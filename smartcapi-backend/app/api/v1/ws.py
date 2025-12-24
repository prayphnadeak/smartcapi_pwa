"""
Enhanced WebSocket Handler for Real-time Interview Processing
Refactored for Hybrid Worker Architecture (Redis Pub/Sub)
"""

import asyncio
import json
import time
import base64
from typing import Dict, Optional, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import redis.asyncio as aioredis

from app.db.database import get_db
from app.core.logger import api_logger
from app.core.config import settings
from app.services.question_manager import QuestionManager
from app.core.redis_client import async_redis_client, RedisQueue, RedisChannel

router = APIRouter()

class InterviewSession:
    """Manages state for a single interview session (Redis Publisher)"""
    
    def __init__(self, user_id: int, interview_id: int, db: Session):
        self.user_id = user_id
        self.interview_id = interview_id
        self.db = db
        self.question_manager = QuestionManager(db)
        self.chunk_count = 0
        
        api_logger.info(
            f"InterviewSession created: user={user_id}, interview={interview_id}"
        )

    async def process_audio_chunk(self, audio_data: bytes, websocket: WebSocket):
        """
        Publish audio chunk to Redis queues for workers
        
        Args:
            audio_data: Raw audio bytes
            websocket: WebSocket connection (unused for direct response now, but kept for signature)
        """
        try:
            self.chunk_count += 1
            timestamp = time.time()
            
            # Encode audio to base64 for JSON serialization
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            payload = json.dumps({
                "interview_id": self.interview_id,
                "user_id": self.user_id,
                "timestamp": timestamp,
                "audio_data": audio_b64
            })
            
            # Push to both processing queues
            if async_redis_client:
                async with async_redis_client.pipeline() as pipe:
                    pipe.rpush(RedisQueue.AUDIO_PROCESSING, payload)
                    pipe.rpush(RedisQueue.AUDIO_WHISPER, payload)
                    await pipe.execute()
            
            # --- NEW: Save Raw Audio Stream to File ---
            # Append bytes directly to file
            import os
            # Ensure upload directory exists
            os.makedirs(settings.INTERVIEW_STORAGE_DIR, exist_ok=True)
            
            file_path = os.path.join(settings.INTERVIEW_STORAGE_DIR, f"{self.interview_id}.wav")
            
            # If first chunk, ensure dir exists (redundant if mkdir run, but safe)
            # os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Using synchronous write for simplicity in async context (might block slightly, but OS buffering helps)
            with open(file_path, "ab") as f:
                f.write(audio_data)
            
            # --- CRITICAL FIX: Update DB with audio_path ---
            # If this is the first chunk (or periodically), ensure DB has the path
            if self.chunk_count == 1 or self.chunk_count % 50 == 0:
                from app.db.models import Interview
                # Use a fresh session or the existing one? Existing one `self.db` is passed in init.
                # Since we are in async context but using sync DB session, be careful.
                # Ideally, we should check if path is already set.
                
                # We need to use a relative path for the API to serve it via Static mount or Nginx
                # Nginx alias: /storage -> /var/www/smartcapi/backend/storage
                # DB should store relative to storage root? or full URL? 
                # Usually relative: "interviews/1.wav"
                
                relative_path = f"interviews/{self.interview_id}.wav"
                
                # Check directly using SQL or ORM
                interview = self.db.query(Interview).filter(Interview.id == self.interview_id).first()
                if interview and not interview.audio_path:
                    interview.audio_path = relative_path
                    self.db.commit()
                    api_logger.info(f"Updated audio_path for interview {self.interview_id} to {relative_path}")
            # ------------------------------------------
            
        except Exception as e:
            api_logger.error(f"Error publishing audio chunk: {str(e)}")
            # Optional: Notify user of system error?
            # await websocket.send_text(json.dumps({"type": "error", "message": "System busy"}))

class ConnectionManager:
    """Manages WebSocket connections and interview sessions"""
    
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.interview_sessions: Dict[int, InterviewSession] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        self.active_connections[user_id] = websocket
        api_logger.info(f"User {user_id} connected")
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.interview_sessions:
            del self.interview_sessions[user_id]
        api_logger.info(f"User {user_id} disconnected")
    
    def start_interview_session(self, user_id: int, interview_id: int, db: Session) -> InterviewSession:
        session = InterviewSession(user_id, interview_id, db)
        self.interview_sessions[user_id] = session
        return session
    
    def get_interview_session(self, user_id: int) -> Optional[InterviewSession]:
        return self.interview_sessions.get(user_id)

manager = ConnectionManager()

async def redis_subscription_loop(websocket: WebSocket, interview_id: int):
    """
    Listen to Redis PubSub and forward messages to WebSocket
    """
    pubsub = async_redis_client.pubsub()
    channel = RedisChannel.interview_updates(interview_id)
    await pubsub.subscribe(channel)
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                # Forward the message content directly to the frontend
                # We expect the workers to publish valid JSON strings
                data = message["data"]
                # If data is bytes, decode it
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                
                await websocket.send_text(data)
    except Exception as e:
        api_logger.error(f"Redis subscription error for interview {interview_id}: {e}")
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()

@router.websocket("/interview")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    user_id = None
    redis_task = None
    
    try:
        await websocket.accept()
        await manager.connect(websocket, 0) # Temp ID
        
        # init handshake
        init_data = await websocket.receive_text()
        init_message = json.loads(init_data)
        
        if init_message.get("type") != "start_interview":
            await websocket.send_text(json.dumps({"type": "error", "message": "Expected start_interview"}))
            return
            
        user_id = init_message.get("user_id")
        interview_id = init_message.get("interview_id")
        
        if not user_id or not interview_id:
            await websocket.send_text(json.dumps({"type": "error", "message": "Missing ID"}))
            return
            
        # Switch to real ID
        manager.disconnect(0)
        await manager.connect(websocket, user_id)
        session = manager.start_interview_session(user_id, interview_id, db)
        
        # Send current question info immediately
        current_question = session.question_manager.get_current_question()
        if current_question:
            await websocket.send_text(json.dumps({
                "type": "current_question",
                "question_id": current_question.id,
                "question_text": current_question.question_text,
                "question_number": current_question.question_number,
                "variable_name": current_question.variable_name
            }))
            
        # Start Redis subscription in background
        redis_task = asyncio.create_task(redis_subscription_loop(websocket, interview_id))
        
        # Main Audio Loop
        while True:
            # Receive message (text or bytes)
            # We use receive() to handle both types genericly, or check type
            message = await websocket.receive()
            
            if "text" in message:
                try:
                    text_data = message["text"]
                    data_json = json.loads(text_data)
                    msg_type = data_json.get("type")
                    
                    if msg_type == "set_question":
                        q_id = data_json.get("question_id")
                        var_name = data_json.get("variable_name")
                        
                        question = None
                        if q_id:
                            # Try to get by ID to confirm validity? Or just trust it.
                            # Better to validate if possible, but for speed just trusting ID is ok if direct.
                            pass
                        elif var_name:
                            # Lookup by variable name
                            question = session.question_manager.get_question_by_variable_name(var_name)
                            if question:
                                q_id = question.id
                        
                        if q_id and async_redis_client:
                            # Update current question in Redis for workers to see
                            redis_key = f"interview:{interview_id}:current_question"
                            await async_redis_client.set(redis_key, str(q_id))
                            api_logger.info(f"Set current question for interview {interview_id} to {q_id}")
                            
                            # Update DB
                            from app.db.models import Interview
                            interview = session.db.query(Interview).filter(Interview.id == interview_id).first()
                            if interview:
                                interview.current_question_id = q_id
                                session.db.commit()
                            
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    api_logger.error(f"Error handling text message: {e}")

            elif "bytes" in message:
                await session.process_audio_chunk(message["bytes"], websocket)
            
    except WebSocketDisconnect:
        api_logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        api_logger.error(f"WebSocket error: {str(e)}")
    finally:
        if redis_task:
            redis_task.cancel()
        if user_id:
            manager.disconnect(user_id)