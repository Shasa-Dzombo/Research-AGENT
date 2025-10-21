"""
Chatbot API endpoints for frontend integration
Provides REST API interface for the Gemini-powered conversational agent
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from agents.conversational_agent import ConversationalAgent

# Initialize router and conversational agent
chatbot_router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])
conversational_agent = ConversationalAgent()

# Pydantic models for request/response validation
class ChatStartRequest(BaseModel):
    user_id: Optional[str] = None

class ChatStartResponse(BaseModel):
    session_id: str
    message: str
    status: str
    timestamp: str
    available_actions: List[str]

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str
    action: str = "chat"

class ChatMessageResponse(BaseModel):
    message: str
    status: str
    timestamp: str
    session_id: Optional[str] = None
    context_info: Optional[Dict[str, Any]] = None

class ProjectSetupRequest(BaseModel):
    session_id: str
    project_description: str

class QuestionGenerationRequest(BaseModel):
    session_id: str
    research_objectives: str

class LiteratureSearchRequest(BaseModel):
    session_id: str
    search_query: str

class GapAnalysisRequest(BaseModel):
    session_id: str
    research_area: str

class SessionStatusResponse(BaseModel):
    session_id: str
    status: str
    created_at: str
    user_id: Optional[str]
    current_step: str
    has_project: bool
    conversation_length: int
    research_context: Dict[str, Any]

class FrameworkExportResponse(BaseModel):
    framework: Dict[str, Any]
    status: str
    timestamp: str

# API Endpoints

@chatbot_router.post("/chat/start", response_model=ChatStartResponse)
async def start_chat_session(request: ChatStartRequest):
    """
    Start a new chat session with the research assistant.
    
    Returns:
        Session information and welcome message
    """
    try:
        result = conversational_agent.start_chat_session(request.user_id)
        
        return ChatStartResponse(
            session_id=result["session_id"],
            message=result["message"],
            status=result["status"],
            timestamp=result["timestamp"],
            available_actions=result["available_actions"]
        )
    except Exception as e:
        logging.error(f"Error starting chat session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start chat session")

@chatbot_router.post("/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(request: ChatMessageRequest):
    """
    Send a message to the chatbot and get a response.
    
    Args:
        request: Chat message request with session_id, message, and optional action
        
    Returns:
        Chatbot response message
    """
    try:
        result = conversational_agent.chat(
            session_id=request.session_id,
            message=request.message,
            action=request.action
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return ChatMessageResponse(
            message=result["message"],
            status=result["status"],
            timestamp=result["timestamp"],
            session_id=request.session_id,
            context_info=result.get("context_info")
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process chat message")

@chatbot_router.post("/chat/setup-project")
async def setup_project(request: ProjectSetupRequest):
    """
    Set up a research project for the current session.
    
    Args:
        request: Project setup request with session_id and project description
        
    Returns:
        Project setup confirmation and extracted information
    """
    try:
        result = conversational_agent.chat(
            session_id=request.session_id,
            message=request.project_description,
            action="setup_project"
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error setting up project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to setup project")

@chatbot_router.post("/chat/generate-questions")
async def generate_research_questions(request: QuestionGenerationRequest):
    """
    Generate research questions based on project and objectives.
    
    Args:
        request: Question generation request with session_id and research objectives
        
    Returns:
        Generated research questions
    """
    try:
        result = conversational_agent.chat(
            session_id=request.session_id,
            message=request.research_objectives,
            action="generate_questions"
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error generating questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate research questions")

@chatbot_router.post("/chat/search-literature")
async def search_literature(request: LiteratureSearchRequest):
    """
    Search for relevant literature based on the query.
    
    Args:
        request: Literature search request with session_id and search query
        
    Returns:
        Literature search results and suggestions
    """
    try:
        result = conversational_agent.chat(
            session_id=request.session_id,
            message=request.search_query,
            action="search_literature"
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error searching literature: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to search literature")

@chatbot_router.post("/chat/analyze-gaps")
async def analyze_research_gaps(request: GapAnalysisRequest):
    """
    Analyze research gaps in the specified area.
    
    Args:
        request: Gap analysis request with session_id and research area
        
    Returns:
        Research gap analysis
    """
    try:
        result = conversational_agent.chat(
            session_id=request.session_id,
            message=request.research_area,
            action="analyze_gaps"
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error analyzing gaps: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze research gaps")

@chatbot_router.get("/chat/status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    Get current status and information for a chat session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Current session status and context
    """
    try:
        result = conversational_agent.get_session_status(session_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return SessionStatusResponse(
            session_id=result["session_id"],
            status=result["status"],
            created_at=result["created_at"],
            user_id=result["user_id"],
            current_step=result["current_step"],
            has_project=result["has_project"],
            conversation_length=result["conversation_length"],
            research_context=result["research_context"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting session status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get session status")

@chatbot_router.get("/chat/export/{session_id}", response_model=FrameworkExportResponse)
async def export_research_framework(session_id: str):
    """
    Export the research framework and session data.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Complete research framework with session data
    """
    try:
        result = conversational_agent.export_research_framework(session_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return FrameworkExportResponse(
            framework=result["framework"],
            status=result["status"],
            timestamp=result["timestamp"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error exporting framework: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export research framework")

# Health check for chatbot system
@chatbot_router.get("/health")
async def chatbot_health_check():
    """
    Health check for chatbot system.
    
    Returns:
        System health status and information
    """
    try:
        # Test LLM connection
        test_llm = conversational_agent.llm
        test_response = test_llm.invoke("Test connection - respond with 'OK'")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "llm_model": "gemini-2.0-flash-exp",
            "llm_status": "connected" if test_response else "disconnected",
            "active_sessions": len(conversational_agent.sessions),
            "service": "Conversational Research Agent"
        }
    except Exception as e:
        logging.error(f"Chatbot health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "service": "Conversational Research Agent"
        }

# Session management endpoints
@chatbot_router.delete("/chat/session/{session_id}")
async def end_chat_session(session_id: str):
    """
    End and clean up a chat session.
    
    Args:
        session_id: Session identifier to terminate
        
    Returns:
        Session termination confirmation
    """
    try:
        if session_id in conversational_agent.sessions:
            del conversational_agent.sessions[session_id]
            return {
                "message": "Session ended successfully",
                "session_id": session_id,
                "status": "terminated",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error ending session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to end session")

@chatbot_router.get("/chat/sessions")
async def list_active_sessions():
    """
    List all active chat sessions (for admin/debugging purposes).
    
    Returns:
        List of active session information
    """
    try:
        sessions_info = []
        for session_id, session_data in conversational_agent.sessions.items():
            sessions_info.append({
                "session_id": session_id,
                "created_at": session_data["created_at"].isoformat(),
                "user_id": session_data.get("user_id"),
                "step": session_data.get("step", "unknown"),
                "conversation_length": len(session_data.get("conversation_history", []))
            })
        
        return {
            "active_sessions": sessions_info,
            "total_count": len(sessions_info),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Error listing sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list sessions")

# Function to include chatbot routes in main app
def include_chatbot_routes(app):
    """
    Include chatbot routes in the main FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.include_router(chatbot_router)
    logging.info("✅ Chatbot API routes included successfully")