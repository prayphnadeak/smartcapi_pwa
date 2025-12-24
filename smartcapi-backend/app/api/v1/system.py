import os
from fastapi import APIRouter, Depends, HTTPException, status
from app.api import deps
from app.db.models import User
from app.core.logger import api_logger
from app.core.redis_client import redis_client, RedisQueue

router = APIRouter()

@router.delete("/logs")
async def clear_system_logs(
    current_user: User = Depends(deps.get_current_admin_user),
):
    """
    Clear system logs (truncate files).
    Requires admin privileges.
    """
    # Define paths relative to the project root (where uvicorn runs)
    log_files = [
        "./app/storage/logs/api.log",
        "./app/storage/logs/ml.log",
        "./app/storage/logs/db.log"
    ]
    
    cleared_files = []
    errors = []
    
    # 1. Flush Redis Queues (Clear "Ghost" Data)
    try:
        if redis_client:
            redis_client.delete(
                RedisQueue.AUDIO_WHISPER,
                RedisQueue.MERGER_SEGMENTS,
                RedisQueue.MERGER_TRANSCRIPTS,
                RedisQueue.LLM_EXTRACTION,
                RedisQueue.AUDIO_PROCESSING
            )
            api_logger.info("System Cleanup: Flushed Redis processing queues.")
        else:
            errors.append("Redis client not available - Queues not flushed")
    except Exception as e:
        error_msg = f"Failed to flush Redis queues: {str(e)}"
        api_logger.error(error_msg)
        errors.append(error_msg)

    # 2. Clear Log Files
    for log_file in log_files:
        # Resolve absolute path just to be safe
        abs_path = os.path.abspath(log_file)
        
        if os.path.exists(abs_path):
            try:
                # Truncate file content to 0 bytes
                # 'w' mode opens for writing and truncates automatically
                with open(abs_path, 'w') as f:
                    pass 
                cleared_files.append(os.path.basename(log_file))
            except Exception as e:
                errors.append(f"{os.path.basename(log_file)}: {str(e)}")
        else:
             # It's not an error if file doesn't exist, just skip
             pass
    
    if errors:
        api_logger.warning(f"Failed to clear some logs: {errors}")
        # We still return 200 OK but with error details, unless all failed
        if not cleared_files and errors:
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clear logs: {', '.join(errors)}"
            )
    
    api_logger.info(f"System logs cleared by user {current_user.email}")
    
    return {
        "message": "System logs cleared successfully",
        "cleared_files": cleared_files,
        "errors": errors
    }
