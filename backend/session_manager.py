import uuid
import random
import string
from instrument_node import InstrumentNode
from feedback_detector import FeedbackDetector
class SessionManager:
    def __init__(self):
        self.sessions = {}
    def create_session(self, session_name: str) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "name": session_name,
            "nodes": {},
            "feedback_detector": FeedbackDetector(),
            "band_code": ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        }
        return session_id, self.sessions[session_id]["band_code"]
    def add_node(self, session_id: str, member_name: str, instrument: str, phoneID: str, position: str) -> bool:
        if session_id in self.sessions:
            node = InstrumentNode(member_name, instrument, phoneID, position)
            self.sessions[session_id]["nodes"][member_name] = node
            return True
        return False
    
    def get_session_info(self, session_id: str) -> dict:
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return {
                "session_name": session["name"],
                "nodes": list(session["nodes"].keys()),
                "band_code": session["band_code"]
            }
        return {}
    def get_node(self, session_id: str, member_name: str, phone_id: str) -> InstrumentNode:
        if session_id in self.sessions and member_name in self.sessions[session_id]["nodes"]:
            node = self.sessions[session_id]["nodes"][member_name]
            if node.phoneID == phone_id:
                return node
        return None
    def get_all_nodes(self, session_id: str) -> list:
        if session_id in self.sessions:
            return list(self.sessions[session_id]["nodes"].values())
    def remove_node(self, session_id: str, member_name: str) -> bool:
        if session_id in self.sessions and member_name in self.sessions[session_id]["nodes"]:
            del self.sessions[session_id]["nodes"][member_name]
            return True
        return False
    def end_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    def get_all_recommendations(self, session_id: str) -> list:
        if session_id in self.sessions:
            session = self.sessions[session_id]
            feedback_detector = session["feedback_detector"]
            recommendations = []
            for node in session["nodes"].values():
                feedback_detector.update(node)
                rec = node.get_recommendation()
                recommendations.append(rec)
            return recommendations
        return []
if __name__ == "__main__":
    manager = SessionManager()
    session_id, band_code = manager.create_session("Jazz Night")
    print(f"Session created: {session_id} with band code {band_code}")
    manager.add_node(session_id, "Alice", "guitar", "phone123", "left")
    manager.add_node(session_id, "Bob", "bass", "phone456", "right")
    info = manager.get_session_info(session_id)
    print(f"Session info: {info}")
    nodes = manager.get_all_nodes(session_id)
    print(f"Nodes in session: {[node.name for node in nodes]}")
        