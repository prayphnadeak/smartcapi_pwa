
import json
import asyncio
import redis
from datetime import datetime
from app.core.config import settings
from app.core.logger import api_logger
from app.services.llm_service import llm_service
from app.db.database import SessionLocal
from app.db.models import Interview, QuestionnaireQuestion
# We need to access questions to know what to extract
from app.services.question_manager import QuestionManager

class AlignerService:
    """
    Consumes events from Redis (segment.speaker, transcript.partial)
    Merges them to form a coherent Transcript.
    Triggers LLM when a complete answer is detected.
    """
    # Function to initialize AlignerService
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        self.pubsub = self.redis.pubsub()
        self.interview_buffers = {} # {interview_id: {text: [], speakers: [], last_processed: 0}}
        
    # Function to listen to redis events
    async def listen(self):
        """
        Listen to all interview events
        """
        # Subscribe to pattern
        self.pubsub.psubscribe("interview.*.events")
        api_logger.info("AlignerService listening on interview.*.events")
        
        for message in self.pubsub.listen():
            if message['type'] == 'pmessage':
                try:
                    data = json.loads(message['data'])
                    await self.process_event(data)
                except Exception as e:
                    api_logger.error(f"Aligner Error processing message: {e}")

    # Function to process an event
    async def process_event(self, event):
        interview_id = event.get("interview_id")
        event_type = event.get("type")
        
        if not interview_id:
            return

        # Initialize buffer
        if interview_id not in self.interview_buffers:
            self.interview_buffers[interview_id] = {
                "transcript_parts": [],
                "current_speaker": "unknown",
                "accumulated_text": "",
                "last_activity": datetime.now()
            }
        
        buffer = self.interview_buffers[interview_id]
        
        if event_type == "segment.speaker":
            # Update current speaker state
            # We assume audio segments arrive somewhat in order
            speaker = event.get("speaker")
            buffer["current_speaker"] = speaker
            
            # Simple heuristic: If we switch FROM respondent TO enumerator, 
            # and we have accumulated text, it might be the end of an answer.
            # (Logic to be refined)
            
        elif event_type == "transcript.partial":
            text = event.get("text")
            if text:
                # Append text if speaker is valid (Respondent)
                # Or just append everything and filter later?
                # For MVP: Filter "Enumerator" speech if we can. 
                # Issues: Synchronization. Speaker event for time T might arrive after Transcript for time T.
                # Assuming "current_speaker" track is rough approximation.
                
                speaker = buffer["current_speaker"]
                timestamp = event.get("timestamp")
                
                api_logger.info(f"Aligner: [{speaker}] {text}")
                
                if speaker == "respondent" or speaker == "unknown":
                    buffer["accumulated_text"] += " " + text
                    
                    # Publish live update to UI
                    self.redis.publish(f"interview.{interview_id}.ui", json.dumps({
                        "type": "live_transcript",
                        "text": buffer["accumulated_text"],
                        "speaker": speaker
                    }))
                    
                    # Trigger Extraction Heuristic?
                    # E.g. Silence (detected by no events for X ms) or specific keywords
                    # Or handled by "Finalize" command from UI/WS.
                    
                    # For now, let's just push live updates.
                    # Extraction triggering logic needs to be robust. 
                    # Maybe the "Silence" event from AudioWorker triggers it?
                    
        elif event_type == "segment.silence":
             # If silence > threshold, trigger extraction on accumulated text
             pass

