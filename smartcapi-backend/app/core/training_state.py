from typing import Dict, Any

# Global dictionary to store training status
# Format: { user_id: { "progress": int, "status": str, "message": str } }
training_status: Dict[int, Dict[str, Any]] = {}

def get_training_status(user_id: int) -> Dict[str, Any]:
    return training_status.get(user_id, {"progress": 0, "status": "idle", "message": "Waiting to start..."})

def update_training_status(user_id: int, progress: int, status: str, message: str):
    training_status[user_id] = {
        "progress": progress,
        "status": status,
        "message": message
    }

def clear_training_status(user_id: int):
    if user_id in training_status:
        del training_status[user_id]
