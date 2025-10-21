"""
Startup script for the AI Research Agent FastAPI server
"""

import uvicorn
import os

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if GOOGLE_API_KEY is set
    if not os.getenv("GOOGLE_API_KEY"):
        print("WARNING: GOOGLE_API_KEY environment variable is not set!")
        print("Please create a .env file with your Google API key:")
        print("GOOGLE_API_KEY=your_api_key_here")
        print()
    
    print("Starting AI Research Agent FastAPI server...")
    print("API Documentation will be available at: http://localhost:8000/docs")
    print("API Base URL: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print()
    
    # Run the server
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
