"""
Audio processing service for transcribing speech to text.
"""
import os
import tempfile
from typing import Union, Optional

import whisper

def transcribe_audio(audio_data: bytes, model_size: str = "base") -> str:
    """
    Transcribe audio data to text using OpenAI's Whisper model.
    
    Args:
        audio_data: Raw audio data bytes
        model_size: Size of the Whisper model (tiny, base, small, medium, large)
        
    Returns:
        str: Transcribed text
        
    Raises:
        Exception: For any processing errors
    """
    try:
        # Force CPU usage to avoid MPS issues on Mac
        device = "cpu"
        
        # Load the model on CPU
        model = whisper.load_model(model_size, device=device)
        
        # Save audio data to a temporary file with appropriate extension
        # Use .ogg extension if the original was .ogg, otherwise use .wav
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=True) as tmp:
            tmp.write(audio_data)
            tmp.flush()
            
            # Transcribe the audio with additional options
            result = model.transcribe(
                tmp.name, 
                fp16=False,  # Disable half precision
                language=None,  # Auto-detect language
                task="transcribe"  # Transcribe (not translate)
            )
            
            # Return the transcribed text
            return result["text"].strip()
                
    except Exception as e:
        # Re-raise with more context
        raise Exception(f"Error transcribing audio: {str(e)}") from e
