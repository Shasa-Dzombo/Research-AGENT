"""
Gemini-powered Conversational Research Agent
Provides chat-based interface for research assistance
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from config.llm_factory import get_llm
from agents.research_assistant import ResearchAssistant
from utils import database_utils
from utils import research_utils
from state.state import AgentState


class ConversationalAgent:
    """
    Conversational agent that provides research assistance through chat interface.
    Uses Gemini 2.0 Flash for natural language interactions.
    """
    
    def __init__(self):
        self.llm = get_llm()
        self.research_assistant = ResearchAssistant()
        self.db_utils = database_utils  # Module containing database functions
        self.research_utils = research_utils  # Module containing research functions
        self.sessions = {}  # In-memory session storage
        self.session_timeout = timedelta(hours=24)
        
        logging.info("ConversationalAgent initialized with Gemini 2.0 Flash")
    
    def start_chat_session(self, user_id: str = None) -> Dict[str, Any]:
        """
        Start a new chat session for a user.
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            Session information including session_id and welcome message
        """
        session_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id or 'anonymous'}"
        
        # Initialize session state
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "user_id": user_id,
            "conversation_history": [],
            "current_project": None,
            "research_context": {},
            "step": "greeting"
        }
        
        welcome_message = """
🔬 **Welcome to the AI Research Assistant!**

 I'm here to help you with your research project. I can assist you with:

• **Project Setup**: Help define your research objectives and scope
• **Question Generation**: Create comprehensive research questions
• **Literature Search**: Find relevant academic papers and resources  
• **Gap Analysis**: Identify research gaps in your field
• **Framework Export**: Generate structured research frameworks

How can I help you with your research today? You can:
1. Tell me about your research project
2. Ask me to generate research questions
3. Request literature search on a topic
4. Get help with methodology design

What would you like to start with?
        """
        
        response = {
            "session_id": session_id,
            "message": welcome_message.strip(),
            "status": "active",
            "timestamp": datetime.now().isoformat(),
            "available_actions": [
                "setup_project",
                "generate_questions", 
                "search_literature",
                "analyze_gaps",
                "ask_question"
            ]
        }
        
        self._add_to_conversation(session_id, "assistant", welcome_message.strip())
        
        logging.info(f"Started chat session: {session_id}")
        return response
    
    def chat(self, session_id: str, message: str, action: str = "chat") -> Dict[str, Any]:
        """
        Process a chat message and return response.
        
        Args:
            session_id: Session identifier
            message: User's message
            action: Specific action to perform (chat, setup_project, etc.)
            
        Returns:
            Chat response with assistant's reply
        """
        if not self._is_session_valid(session_id):
            return {"error": "Invalid or expired session", "status": "expired"}
        
        session = self.sessions[session_id]
        self._add_to_conversation(session_id, "user", message)
        
        try:
            # Route to specific handlers based on action
            if action == "setup_project":
                response = self._handle_project_setup(session_id, message)
            elif action == "generate_questions":
                response = self._handle_question_generation(session_id, message)
            elif action == "search_literature":
                response = self._handle_literature_search(session_id, message)
            elif action == "analyze_gaps":
                response = self._handle_gap_analysis(session_id, message)
            else:
                # General chat handling
                response = self._handle_general_chat(session_id, message)
            
            self._add_to_conversation(session_id, "assistant", response["message"])
            return response
            
        except Exception as e:
            logging.error(f"Error in chat processing: {e}", exc_info=True)
            error_response = {
                "message": "I apologize, but I encountered an error processing your request. Could you please try again?",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
            return error_response
    
    def _handle_project_setup(self, session_id: str, message: str) -> Dict[str, Any]:
        """Handle project setup conversation"""
        session = self.sessions[session_id]
        
        # Parse project information using LLM
        setup_prompt = f"""
        As a research assistant, analyze the following project description and extract key information:

        Project Description: {message}

        Extract and structure the following information:
        1. Research Topic/Title
        2. Research Objectives
        3. Target Population/Sample
        4. Research Domain/Field
        5. Methodology Preferences (if mentioned)
        6. Timeline (if mentioned)

        Provide a structured response in JSON format and also a natural language summary.
        """
        
        llm_response = self.llm.invoke(setup_prompt)
        
        # Store project information
        session["current_project"] = {
            "description": message,
            "extracted_info": llm_response.content,
            "setup_timestamp": datetime.now().isoformat()
        }
        session["step"] = "project_configured"
        
        response_message = f"""
Great! I've analyzed your project information. Here's what I understand:

{llm_response.content}

Now I can help you with:
• **Generate Research Questions**: Create comprehensive research questions based on your project
• **Literature Search**: Find relevant papers and resources for your topic
• **Methodology Guidance**: Suggest appropriate research methods
• **Gap Analysis**: Identify research gaps in your field

What would you like to do next?
        """
        
        return {
            "message": response_message.strip(),
            "status": "project_setup_complete",
            "timestamp": datetime.now().isoformat(),
            "project_info": session["current_project"],
            "next_actions": ["generate_questions", "search_literature", "methodology_help"]
        }
    
    def _handle_question_generation(self, session_id: str, message: str) -> Dict[str, Any]:
        """Handle research question generation"""
        session = self.sessions[session_id]
        
        if not session.get("current_project"):
            return {
                "message": "Please set up your project first by describing your research topic and objectives.",
                "status": "project_required",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Use the research assistant to generate questions
            project_info = {
                "title": "User Project",
                "description": session["current_project"]["description"],
                "objectives": message
            }
            
            # Generate questions using research workflow
            result = self.research_assistant.run_complete_workflow(project_info)
            
            # Format the response
            questions_text = "## Generated Research Questions\n\n"
            if result.get("sub_questions"):
                for i, question in enumerate(result["sub_questions"], 1):
                    questions_text += f"{i}. {question}\n"
            
            response_message = f"""
Based on your project, I've generated the following research questions:

{questions_text}

These questions are designed to be:
- **Specific**: Clearly defined and focused
- **Measurable**: Can be answered with data
- **Relevant**: Aligned with your research objectives
- **Achievable**: Realistic within typical research constraints

Would you like me to:
• Refine any of these questions?
• Generate additional questions for specific aspects?
• Help you prioritize these questions?
• Search for literature related to these questions?
            """
            
            session["research_context"]["generated_questions"] = result.get("sub_questions", [])
            
            return {
                "message": response_message.strip(),
                "status": "questions_generated", 
                "timestamp": datetime.now().isoformat(),
                "research_questions": result.get("sub_questions", []),
                "next_actions": ["refine_questions", "search_literature", "prioritize_questions"]
            }
            
        except Exception as e:
            logging.error(f"Error generating questions: {e}")
            return {
                "message": "I encountered an issue generating research questions. Could you provide more details about your research objectives?",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    def _handle_literature_search(self, session_id: str, message: str) -> Dict[str, Any]:
        """Handle literature search requests"""
        session = self.sessions[session_id]
        
        search_prompt = f"""
        Based on the search query: "{message}"
        
        I'll search for relevant academic literature. Let me analyze your query and provide relevant resources.
        """
        
        try:
            # Use database utils for literature search if available
            search_results = []
            
            # Simulate literature search (integrate with actual database later)
            llm_response = self.llm.invoke(f"""
            As a research librarian, provide a literature search response for: {message}
            
            Suggest:
            1. Key search terms and keywords
            2. Relevant databases to search
            3. Suggested paper types (reviews, empirical studies, etc.)
            4. Related research areas to explore
            
            Format as a helpful guide.
            """)
            
            response_message = f"""
## Literature Search Results

**Search Query**: {message}

{llm_response.content}

### Next Steps:
• Would you like me to refine the search terms?
• Should I search for papers on specific sub-topics?
• Do you need help accessing academic databases?
• Would you like citation formatting help?
            """
            
            return {
                "message": response_message.strip(),
                "status": "literature_search_complete",
                "timestamp": datetime.now().isoformat(),
                "search_query": message,
                "suggestions": llm_response.content
            }
            
        except Exception as e:
            logging.error(f"Error in literature search: {e}")
            return {
                "message": "I encountered an issue with the literature search. Please try rephrasing your search terms.",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    def _handle_gap_analysis(self, session_id: str, message: str) -> Dict[str, Any]:
        """Handle research gap analysis"""
        session = self.sessions[session_id]
        
        gap_analysis_prompt = f"""
        As a research expert, analyze the following research area for potential gaps:
        
        Research Area: {message}
        
        Identify:
        1. Methodological gaps
        2. Theoretical gaps  
        3. Empirical gaps
        4. Population/demographic gaps
        5. Temporal gaps (outdated research)
        6. Geographic/cultural gaps
        
        Provide specific, actionable gap analysis.
        """
        
        llm_response = self.llm.invoke(gap_analysis_prompt)
        
        response_message = f"""
## Research Gap Analysis

**Analysis for**: {message}

{llm_response.content}

### Recommendations:
These gaps represent opportunities for original research contribution. Would you like me to:
• Help you focus on specific gaps?
• Generate research questions targeting these gaps?
• Suggest methodologies to address these gaps?
• Search for recent work in these gap areas?
        """
        
        return {
            "message": response_message.strip(),
            "status": "gap_analysis_complete", 
            "timestamp": datetime.now().isoformat(),
            "analysis_topic": message,
            "gaps_identified": llm_response.content
        }
    
    def _handle_general_chat(self, session_id: str, message: str) -> Dict[str, Any]:
        """Handle general research assistance chat"""
        session = self.sessions[session_id]
        
        # Build context from conversation history
        context = self._build_conversation_context(session_id)
        
        general_prompt = f"""
        You are an expert research assistant powered by Gemini 2.0. You help researchers with:
        - Research methodology and design
        - Literature review strategies
        - Data collection and analysis
        - Academic writing and publishing
        - Research ethics and best practices
        
        Conversation context: {context}
        
        User message: {message}
        
        Provide helpful, specific, and actionable research guidance. Be encouraging and professional.
        """
        
        llm_response = self.llm.invoke(general_prompt)
        
        return {
            "message": llm_response.content,
            "status": "chat_response",
            "timestamp": datetime.now().isoformat(),
            "context_used": True
        }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current session status and information"""
        if not self._is_session_valid(session_id):
            return {"error": "Invalid or expired session", "status": "expired"}
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "status": "active",
            "created_at": session["created_at"].isoformat(),
            "user_id": session.get("user_id"),
            "current_step": session.get("step", "greeting"),
            "has_project": bool(session.get("current_project")),
            "conversation_length": len(session["conversation_history"]),
            "research_context": session.get("research_context", {})
        }
    
    def export_research_framework(self, session_id: str) -> Dict[str, Any]:
        """Export current research framework and session data"""
        if not self._is_session_valid(session_id):
            return {"error": "Invalid or expired session", "status": "expired"}
        
        session = self.sessions[session_id]
        
        framework = {
            "session_info": {
                "session_id": session_id,
                "created_at": session["created_at"].isoformat(),
                "exported_at": datetime.now().isoformat()
            },
            "project": session.get("current_project"),
            "research_context": session.get("research_context", {}),
            "conversation_summary": self._summarize_conversation(session_id)
        }
        
        return {
            "framework": framework,
            "status": "exported",
            "timestamp": datetime.now().isoformat()
        }
    
    # Helper methods
    def _is_session_valid(self, session_id: str) -> bool:
        """Check if session exists and is not expired"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        if datetime.now() - session["created_at"] > self.session_timeout:
            # Clean up expired session
            del self.sessions[session_id]
            return False
        
        return True
    
    def _add_to_conversation(self, session_id: str, role: str, message: str):
        """Add message to conversation history"""
        if session_id in self.sessions:
            self.sessions[session_id]["conversation_history"].append({
                "role": role,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
    
    def _build_conversation_context(self, session_id: str) -> str:
        """Build context string from recent conversation"""
        session = self.sessions.get(session_id, {})
        history = session.get("conversation_history", [])
        
        # Get last 4 messages for context
        recent_messages = history[-4:] if len(history) > 4 else history
        
        context_lines = []
        for msg in recent_messages:
            role = msg["role"].title()
            context_lines.append(f"{role}: {msg['message'][:200]}...")
        
        return "\n".join(context_lines)
    
    def _summarize_conversation(self, session_id: str) -> str:
        """Generate conversation summary using LLM"""
        context = self._build_conversation_context(session_id)
        
        if not context:
            return "No conversation to summarize."
        
        summary_prompt = f"""
        Summarize this research consultation conversation in 2-3 sentences:
        
        {context}
        
        Focus on: research topic, key questions asked, main assistance provided.
        """
        
        try:
            summary_response = self.llm.invoke(summary_prompt)
            return summary_response.content
        except Exception as e:
            logging.error(f"Error summarizing conversation: {e}")
            return "Conversation summary unavailable."