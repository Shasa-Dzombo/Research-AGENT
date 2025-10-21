"""
LLM configuration (Gemini 2.0 Flash and Gemini 2.5)
"""
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import logging

# Available Gemini models
AVAILABLE_MODELS = {
    "gemini-2.0-flash-exp": "Gemini 2.0 Flash (Experimental) - Latest and fastest model",
    "gemini-1.5-pro": "Gemini 1.5 Pro - Balanced performance and capability", 
    "gemini-1.5-flash": "Gemini 1.5 Flash - Fast and efficient",
    "gemini-pro": "Gemini Pro - Standard model"
}

def get_llm(model: str = "gemini-2.0-flash-exp", temperature: float = 0.1, max_tokens: int = 8192):
    """
    Returns a Gemini LLM instance with the given settings.
    
    Args:
        model: Model name (default: gemini-2.0-flash-exp for latest capabilities)
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens in response
    """
    # Load .env and set API key
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set in .env file")
    
    # Validate model
    if model not in AVAILABLE_MODELS:
        logging.warning(f"Model {model} not in available models. Using gemini-2.0-flash-exp")
        model = "gemini-2.0-flash-exp"
    
    logging.info(f"Initializing {AVAILABLE_MODELS.get(model, model)} with temperature={temperature}")
    
    return ChatGoogleGenerativeAI(
        model=model, 
        temperature=temperature,
        max_tokens=max_tokens,
        google_api_key=api_key
    )

def get_chatbot_llm():
    """
    Get a Gemini LLM specifically configured for chatbot interactions.
    Uses Gemini 2.0 Flash for optimal performance and responsiveness.
    """
    return get_llm(
        model="gemini-2.0-flash-exp",
        temperature=0.3,  # Slightly more creative for conversations
        max_tokens=4096   # Reasonable response length
    )
