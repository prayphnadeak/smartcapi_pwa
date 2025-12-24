import os
import pickle
import torch
from typing import Optional, Any
from app.core.config import settings
from app.core.logger import ml_logger

# Function to load Random Forest model
def load_rf_model(model_path: str = None) -> Optional[Any]:
    """
    Load Random Forest model from disk
    
    Args:
        model_path: Path to the model file (default: use settings)
        
    Returns:
        Loaded model or None if loading failed
    """
    try:
        if model_path is None:
            model_path = settings.RF_MODEL_PATH
        
        if not os.path.exists(model_path):
            ml_logger.warning(f"Model file not found at {model_path}")
            return None
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        
        # Format path for logging (Request: .\smartcapi_pwa\...)
        log_path = model_path.replace("C:\\xampp\\htdocs", ".")
        ml_logger.info(f"Random Forest model loaded from {log_path}")
        return model
    except Exception as e:
        ml_logger.error(f"Error loading Random Forest model: {str(e)}")
        return None

# Function to save Random Forest model
def save_rf_model(model: Any, model_path: str = None) -> bool:
    """
    Save Random Forest model to disk
    
    Args:
        model: Model to save
        model_path: Path to save the model (default: use settings)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if model_path is None:
            model_path = settings.RF_MODEL_PATH
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        ml_logger.info(f"Random Forest model saved to {model_path}")
        return True
    except Exception as e:
        ml_logger.error(f"Error saving Random Forest model: {str(e)}")
        return False

# Function to load Whisper model
def load_whisper_model(model_name: str = "small", model_path: str = None) -> Optional[Any]:
    """
    Load Whisper model from disk or download if not exists
    
    Args:
        model_name: Name of the Whisper model
        model_path: Path to the model file (default: use settings)
        
    Returns:
        Loaded model or None if loading failed
    """
    try:
        import whisper
        
        if model_path is None:
            model_path = settings.WHISPER_MODEL_PATH
        
        model_dir = os.path.dirname(model_path)
        
        # If model file exists, load it
        if os.path.exists(model_path):
            model = whisper.load_model(model_name, download_root=model_dir)
            ml_logger.info(f"Whisper model loaded from {model_path}")
            return model
        else:
            # Download model
            model = whisper.load_model(model_name)
            # Save model for future use
            torch.save(model.state_dict(), model_path)
            ml_logger.info(f"Whisper model downloaded and saved to {model_path}")
            return model
    except Exception as e:
        ml_logger.error(f"Error loading Whisper model: {str(e)}")
        return None