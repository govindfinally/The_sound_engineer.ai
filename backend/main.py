from fastapi import FastAPI
from pydantic import BaseModel
from session_manager import SessionManager

session_manager = SessionManager()

app = FastAPI()
@app.get("/")
def read_root():
    return {"message": "Welcome to The Sound Engineer API!"}


class CreateSessionRequest(BaseModel):
    session_name: str
    band_name: str
    
    


@app.post("/create_session")
def create_session(request: CreateSessionRequest):
    session_id, band_code = session_manager.create_session(request.session_name)
    return {"session_id": session_id, "band_code": band_code}
class AddNodeRequest(BaseModel):
    session_id: str
    member_name: str
    instrument: str
    phoneID: str
    position: str
@app.post("/add_node")
def add_node(request: AddNodeRequest):
    success = session_manager.add_node(
        request.session_id,
        request.member_name,
        request.instrument,
        request.phoneID,
        request.position
    )
    return {"success": success}
class GetSessionInfoRequest(BaseModel):
    session_id: str
@app.post("/get_session_info")
def get_session_info(request: GetSessionInfoRequest):
    info = session_manager.get_session_info(request.session_id)
    return info 
class GetRecommendationsRequest(BaseModel):
    session_id: str
@app.post("/get_recommendations")
def get_recommendations(request: GetRecommendationsRequest):
    recommendations = session_manager.get_all_recommendations(request.session_id)
    return {"recommendations": recommendations}

    