import numpy as np
import pickle
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import SentenceTransformer with fallback mechanism
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import sentence_transformers: {e}")
    logger.warning("Vector embeddings will not be available. Using dummy embeddings instead.")
    EMBEDDINGS_AVAILABLE = False

# Load the model once at startup
model = None

async def get_model():
    """Get or initialize the sentence transformer model."""
    global model
    if not EMBEDDINGS_AVAILABLE:
        logger.warning("Embeddings not available. Returning None for model.")
        return None
        
    if model is None:
        try:
            # Using a smaller model for efficiency, can be replaced with a more powerful one
            logger.info("Loading sentence transformer model...")
            model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None
    return model

async def create_embedding(text: str) -> bytes:
    """Create a vector embedding for the given text."""
    model = await get_model()
    
    if model is None:
        # Return a dummy embedding if model is not available
        dummy_embedding = np.zeros(384)  # Standard size for small models
        return pickle.dumps(dummy_embedding)
        
    try:
        # Generate embedding
        embedding = model.encode(text)
        # Convert to bytes for storage
        return pickle.dumps(embedding)
    except Exception as e:
        logger.error(f"Error creating embedding: {e}")
        # Return a dummy embedding on error
        dummy_embedding = np.zeros(384)
        return pickle.dumps(dummy_embedding)

async def get_embedding_from_bytes(embedding_bytes: bytes) -> np.ndarray:
    """Convert stored bytes back to numpy array."""
    return pickle.loads(embedding_bytes)

async def calculate_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Calculate cosine similarity between two embeddings."""
    return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))

async def search_by_text(query_text: str, embeddings_list: list) -> list:
    """Search for similar items based on text query."""
    model = await get_model()
    
    if model is None or not embeddings_list:
        # Return all indices with zero similarity if model is not available
        return [(i, 0.0) for i in range(len(embeddings_list))]
    
    try:
        query_embedding = model.encode(query_text)
        
        results = []
        for i, embedding_bytes in enumerate(embeddings_list):
            embedding = await get_embedding_from_bytes(embedding_bytes)
            similarity = await calculate_similarity(query_embedding, embedding)
            results.append((i, similarity))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    except Exception as e:
        logger.error(f"Error in search_by_text: {e}")
        # Return all indices with zero similarity on error
        return [(i, 0.0) for i in range(len(embeddings_list))]
