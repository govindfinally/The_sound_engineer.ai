"""
================================================================================
  the_sound_engineer / backend / main.py
  FastAPI server with WebSocket support for real-time audio recommendations
================================================================================
"""

import asyncio
import json
from fastapi import FastAPI, WebSocket, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from session_manager import SessionManager

# ═══════════════════════════════════════════════════════════════════════════
# INITIALIZE
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="The Sound Engineer API",
    description="Real-time AI sound engineering for bands",
    version="1.0.0"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global session manager
session_manager = SessionManager()

# WebSocket connection tracking: {session_id → set of connected websockets}
active_connections = {}


# ═══════════════════════════════════════════════════════════════════════════
# REST ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "The Sound Engineer API",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/session/create")
async def create_session(band_name: str = Query(..., min_length=1, max_length=100)):
    """
    Create a new session for a band.
    Returns: {session_id, band_code}
    """
    try:
        session_id, band_code = session_manager.create_session(band_name)
        return {
            "success": True,
            "session_id": session_id,
            "band_code": band_code,
            "band_name": band_name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}/info")
async def get_session_info(session_id: str):
    """
    Get full session info including all member details.
    """
    info = session_manager.get_session_info(session_id)
    if not info:
        raise HTTPException(status_code=404, detail="Session not found")
    return info


@app.get("/session/{session_id}/recommendations")
async def get_all_recommendations(session_id: str):
    """
    Get ALL recommendations for the entire band.
    Master dashboard output.
    """
    recs = session_manager.get_all_recommendations(session_id)
    if not recs:
        raise HTTPException(status_code=404, detail="Session not found")
    return recs


@app.post("/session/{session_id}/member/register")
async def register_member(
    session_id: str,
    member_name: str = Query(..., min_length=1, max_length=50),
    instrument: str = Query(...),
    phone_id: str = Query(...),
    position: str = Query(..., regex="^(left|center|right)$")
):
    """
    Register a band member (phone node) in a session.
    """
    node = session_manager.add_node(session_id, member_name, instrument, phone_id, position)
    if not node:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Notify all connected WebSocket clients about new member
    await broadcast_to_session(session_id, {
        "event": "member_joined",
        "member": {
            "name": node.name,
            "instrument": node.instrument,
            "phone_id": node.phoneID,
            "position": node.position,
        }
    })

    return {
        "success": True,
        "member_name": node.name,
        "phone_id": node.phoneID,
    }


@app.delete("/session/{session_id}/member/{phone_id}")
async def remove_member(session_id: str, phone_id: str):
    """Remove a member from the session."""
    success = session_manager.remove_node(session_id, phone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member or session not found")
    
    await broadcast_to_session(session_id, {
        "event": "member_left",
        "phone_id": phone_id,
    })

    return {"success": True}


@app.delete("/session/{session_id}/end")
async def end_session(session_id: str):
    """End a session and clean up."""
    success = session_manager.end_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True}


# ═══════════════════════════════════════════════════════════════════════════
# WebSocket ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.websocket("/ws/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time updates.
    Frontend connects here to receive live band recommendations.
    """
    await websocket.accept()
    
    # Initialize connection tracking for this session
    if session_id not in active_connections:
        active_connections[session_id] = set()
    
    active_connections[session_id].add(websocket)
    print(f"[WS] Client connected to session {session_id[:8]}... Total: {len(active_connections[session_id])}")

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "update_level":
                # Client sends audio level update
                phone_id = message.get("phone_id")
                db_level = message.get("db_level", -60.0)
                
                node = session_manager.get_node(session_id, phone_id)
                if node:
                    node.update_audio_level(db_level)
                    node.receive_feedback(message.get("feedback", {}))
                    
                    # Broadcast updated recommendations to all clients
                    recs = session_manager.get_all_recommendations(session_id)
                    await broadcast_to_session(session_id, {
                        "event": "recommendations_updated",
                        "data": recs,
                    })
            
            elif message.get("type") == "ping":
                # Keep-alive ping
                await websocket.send_json({"type": "pong"})

    except Exception as e:
        print(f"[WS ERROR] {e}")
    finally:
        # Clean up on disconnect
        active_connections[session_id].discard(websocket)
        print(f"[WS] Client disconnected. Remaining: {len(active_connections.get(session_id, set()))}")
        if not active_connections[session_id]:
            del active_connections[session_id]


# ═══════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════

async def broadcast_to_session(session_id: str, message: dict):
    """
    Send a message to all connected WebSocket clients in a session.
    """
    if session_id not in active_connections:
        return
    
    disconnected = set()
    for websocket in active_connections[session_id]:
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"[WS BROADCAST ERROR] {e}")
            disconnected.add(websocket)
    
    # Remove dead connections
    active_connections[session_id] -= disconnected


# ═══════════════════════════════════════════════════════════════════════════
# STARTUP & SHUTDOWN
# ═══════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*70)
    print("  🎵 The Sound Engineer — Backend Started")
    print("  FastAPI + WebSocket Server for Real-time Sound Engineering")
    print("="*70 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    print("\n" + "="*70)
    print("  🎵 The Sound Engineer — Backend Stopped")
    print("="*70 + "\n")


# ═══════════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )