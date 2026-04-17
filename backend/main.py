"""
================================================================================
  the_sound_engineer / backend / main.py

  FINAL VERSION (Aligned with updated SessionManager)

================================================================================
"""

import json
import numpy as np
from fastapi import FastAPI, WebSocket, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from session_manager import SessionManager

# ═══════════════════════════════════════════════════════════════════════════
# APP INIT
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="The Sound Engineer API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_manager = SessionManager()

# session_id → active WebSocket connections
active_connections: dict[str, set[WebSocket]] = {}

# 🔥 GLOBAL FREQUENCY BINS (REQUIRED FOR FEEDBACK DETECTOR)
FREQ_BINS = np.linspace(20, 20000, 512)


# ═══════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "status": "running",
        "active_sessions": session_manager.active_session_count(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# SESSION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/session/create")
async def create_session(band_name: str = Query(...)):
    session_id, band_code = session_manager.create_session(band_name)

    # 🔥 Attach frequency bins to session
    session = session_manager._sessions.get(session_id)
    if session:
        session.freqs = FREQ_BINS

    return {
        "session_id": session_id,
        "band_code": band_code,
        "band_name": band_name,
    }


@app.get("/session/join/{band_code}")
async def resolve_band_code(band_code: str):
    session_id = session_manager.get_session_id_by_code(band_code)

    if not session_id:
        raise HTTPException(404, "Invalid band code")

    info = session_manager.get_session_info(session_id)

    return {
        "session_id": session_id,
        "band_name": info["band_name"],   # ✅ FIXED
        "member_count": info["member_count"],
    }


@app.get("/session/{session_id}/info")
async def get_session_info(session_id: str):
    info = session_manager.get_session_info(session_id)

    if not info:
        raise HTTPException(404, "Session not found")

    return info


@app.get("/session/{session_id}/recommendations")
async def get_all_recommendations(session_id: str):
    recs = session_manager.get_all_recommendations(session_id)

    if not recs:
        raise HTTPException(404, "Session not found")

    return recs


@app.post("/session/{session_id}/member/register")
async def register_member(
    session_id: str,
    member_name: str = Query(...),
    instrument: str = Query(...),
    phone_id: str = Query(...),
    position: str = Query(...),
):
    node = session_manager.add_node(session_id, member_name, instrument, phone_id, position)

    if not node:
        raise HTTPException(404, "Session not found")

    await _broadcast(session_id, {
        "event": "member_joined",
        "member": {
            "name": node.name,
            "instrument": node.instrument,
            "phone_id": node.phoneID,
            "position": node.position,
        },
    })

    return {"success": True}


@app.delete("/session/{session_id}/member/{phone_id}")
async def remove_member(session_id: str, phone_id: str):
    success = session_manager.remove_node(session_id, phone_id)

    if not success:
        raise HTTPException(404, "Member not found")

    await _broadcast(session_id, {
        "event": "member_left",
        "phone_id": phone_id,
    })

    return {"success": True}


@app.delete("/session/{session_id}/end")
async def end_session(session_id: str):
    success = session_manager.end_session(session_id)

    if not success:
        raise HTTPException(404, "Session not found")

    return {"success": True}


# ═══════════════════════════════════════════════════════════════════════════
# WEBSOCKET
# ═══════════════════════════════════════════════════════════════════════════

@app.websocket("/ws/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):

    await websocket.accept()

    active_connections.setdefault(session_id, set()).add(websocket)

    print(f"[WS] Connected → {session_id[:6]}")

    # Send initial state
    recs = session_manager.get_all_recommendations(session_id)
    if recs:
        await websocket.send_json({
            "event": "recommendations_updated",
            "data": recs,
        })

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                msg = json.loads(raw)
            except:
                continue

            msg_type = msg.get("type")

            if msg_type == "update_level":

                phone_id = msg.get("phone_id")
                db_level = float(msg.get("db_level", -60))

                node = session_manager.get_node(session_id, phone_id)

                if not node:
                    continue

                node.update_audio_level(db_level)
                node.receive_feedback(msg.get("feedback", {}))

                recs = session_manager.get_all_recommendations(session_id)

                await _broadcast(session_id, {
                    "event": "recommendations_updated",
                    "data": recs,
                })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except Exception as e:
        print("[WS ERROR]", e)

    finally:
        active_connections[session_id].discard(websocket)

        if not active_connections[session_id]:
            del active_connections[session_id]

        print(f"[WS] Disconnected → {session_id[:6]}")
#==============================================================================
# joining using the band code
#=============================================================================
@app.post("/session/join")
async def join_with_code(
    band_code: str = Query(...),
    member_name: str = Query(...),
    instrument: str = Query(...),
    phone_id: str = Query(...),
    position: str = Query(...)
):
    session_id = session_manager.get_session_id_by_code(band_code)

    if not session_id:
        raise HTTPException(404, "Invalid band code")

    node = session_manager.add_node(
        session_id,
        member_name,
        instrument,
        phone_id,
        position
    )

    return {
        "success": True,
        "session_id": session_id,
        "member": node.name
    }


# ═══════════════════════════════════════════════════════════════════════════
# BROADCAST
# ═══════════════════════════════════════════════════════════════════════════

async def _broadcast(session_id: str, message: dict):

    if session_id not in active_connections:
        return

    dead = set()

    for ws in active_connections[session_id]:
        try:
            await ws.send_json(message)
        except:
            dead.add(ws)

    active_connections[session_id] -= dead


# ═══════════════════════════════════════════════════════════════════════════
# ENTRY
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)