"""
REST API endpoints with session management
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import uuid
from datetime import datetime, timedelta
import json

from model.models import (
    ProjectRequest, SessionRequest, ResearchQuestionResponse, 
    SubQuestionMappingResponse, DataGapResponse, LiteratureResponse,
    ResearchAnalysisResponse, LiteratureSearchRequest, ProjectInfo,
    QuestionSelectionRequest, QuestionSelectionResponse, SelectedQuestionsListResponse,
    SubQuestionAnalysisRequest, SubQuestionAnswer, SubQuestionAnswersResponse,
    DatabaseSchemaResponse, TableDetailsResponse
)
from agents.research_assistant import ResearchAssistant
from agent_graph.graph import build_graph
from utils.research_utils import search_literature

router = APIRouter()

# Session management for research workflow
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.expiry: Dict[str, datetime] = {}
        # Session expiry in hours
        self.expiry_time = 24

    def create_session(self, project_info: Dict[str, Any], custom_sub_questions: List[str] = None) -> str:
        """Create a new session and return the session ID"""
        session_id = str(uuid.uuid4())
        
        # Initialize session state
        self.sessions[session_id] = {
            "project": project_info,
            "main_questions": [],
            "sub_questions": [],
            "mappings": [],
            "research_variables": [],
            "data_gaps": [],
            "literature": {},
            "custom_sub_questions": custom_sub_questions or [],
            "selected_main_question_ids": [],
            "questions_filtered": False,
            "sub_question_answers": [],
            "created_at": datetime.now().isoformat(),
        }
        
        # Set expiry
        self.expiry[session_id] = datetime.now() + timedelta(hours=self.expiry_time)
        return session_id

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session data if it exists and is not expired"""
        self.clean_expired_sessions()
        return self.sessions.get(session_id)

    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session with new data"""
        if session_id in self.sessions:
            self.sessions[session_id].update(data)
            # Refresh expiry time
            self.expiry[session_id] = datetime.now() + timedelta(hours=self.expiry_time)
            return True
        return False

    def clean_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = [sid for sid, expiry in self.expiry.items() if expiry < now]
        
        for sid in expired:
            if sid in self.sessions:
                del self.sessions[sid]
            if sid in self.expiry:
                del self.expiry[sid]

# Initialize session manager
session_manager = SessionManager()

# 1. Main question and sub-questions generation
@router.post("/generate-questions", response_model=Dict[str, Any])
async def generate_questions(project: ProjectRequest):
    """
    Generate main research question and sub-questions based on project information.
    Creates a new session for subsequent API calls.
    """
    try:
        # Create ProjectInfo object
        project_info = ProjectInfo(
            title=project.title,
            description=project.description,
            area_of_study=project.area_of_study,
            geography=project.geography
        )
        
        # Create a new session
        session_id = session_manager.create_session(
            json.loads(project_info.model_dump_json()),
            project.custom_sub_questions or []
        )
        
        # Get state from the new session
        state = session_manager.get_session(session_id)
        
        # Run only the question generation step
        from agent_graph.nodes.research_nodes import generate_questions_node
        result = generate_questions_node(state)
        
        # Update session with results
        session_manager.update_session(session_id, result)
        
        # Format response
        main_questions = [
            ResearchQuestionResponse(
                id=mq.id,
                text=mq.text,
                question_type=mq.question_type,
                parent_question_id=mq.parent_question_id,
                sub_questions=[
                    ResearchQuestionResponse(
                        id=sq.id,
                        text=sq.text,
                        question_type=sq.question_type,
                        parent_question_id=sq.parent_question_id
                    )
                    for sq in result["sub_questions"] if sq.parent_question_id == mq.id
                ]
            )
            for mq in result["main_questions"]
        ]
        
        return {
            "session_id": session_id,
            "main_questions": main_questions,
            "expires_at": session_manager.expiry[session_id].isoformat(),
            "message": "Questions generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

# 2. Data requirements and analysis approach for sub-questions
@router.post("/analyze-subquestions", response_model=List[SubQuestionMappingResponse])
async def analyze_subquestions(request: SubQuestionAnalysisRequest):
    """
    Generate data requirements and analysis approaches for sub-questions of specified main questions
    """
    try:
        # Get session data
        state = session_manager.get_session(request.session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Check if we have questions generated
        if not state.get("main_questions") or not state.get("sub_questions"):
            raise HTTPException(
                status_code=400, 
                detail="No questions found in session. Please run generate-questions endpoint first."
            )
        
        # Validate main question IDs
        available_main_ids = [mq.id for mq in state.get("main_questions", [])]
        invalid_ids = [qid for qid in request.main_question_ids if qid not in available_main_ids]
        
        if invalid_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid main question IDs: {invalid_ids}"
            )
        
        # Filter sub-questions to only include those linked to specified main questions
        filtered_sub_questions = [
            sq for sq in state.get("sub_questions", [])
            if sq.parent_question_id in request.main_question_ids
        ]
        
        if not filtered_sub_questions:
            raise HTTPException(
                status_code=400,
                detail="No sub-questions found for the specified main question IDs"
            )
        
        # Create a temporary state with only the selected sub-questions
        filtered_state = {**state, "sub_questions": filtered_sub_questions}
        
        # Run the mapping step with filtered questions
        from agent_graph.nodes.research_nodes import map_subquestions_node
        result = map_subquestions_node(filtered_state)
        
        # Update the session state with:
        # 1. The new mappings
        # 2. The analyzed main question IDs (so user can continue with same session)
        update_data = {
            **result,
            "selected_main_question_ids": request.main_question_ids,  # Track what was analyzed
            "questions_filtered": True  # Mark that questions have been processed
        }
        
        # Update session with results
        session_manager.update_session(request.session_id, update_data)
        
        # Format response
        mappings = [
            SubQuestionMappingResponse(
                sub_question_id=mapping.sub_question_id,
                sub_question=mapping.sub_question,
                data_requirements=mapping.data_requirements,
                analysis_approach=mapping.analysis_approach
            )
            for mapping in result["mappings"]
        ]
        
        return mappings
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing sub-questions: {str(e)}")

# 2b. Answer sub-questions from previous analysis
@router.post("/analyze-selected-subquestions", response_model=SubQuestionAnswersResponse)
async def analyze_selected_subquestions(session: SessionRequest):
    """
    Generate comprehensive answers for sub-questions from the previous analysis step.
    This creates a loop that processes each sub-question text and provides detailed answers.
    """
    try:
        # Get session data
        state = session_manager.get_session(session.session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Check if we have mappings from previous analysis
        existing_mappings = state.get("mappings", [])
        if not existing_mappings:
            raise HTTPException(
                status_code=400,
                detail="No sub-question analysis found. Please run /analyze-subquestions first to analyze sub-questions."
            )
        
        print(f"Processing {len(existing_mappings)} sub-questions from previous analysis...")
        
        # Use the new answering node to generate answers
        from agent_graph.nodes.research_nodes import answer_subquestions_node
        result = answer_subquestions_node(state)
        
        # Update session with the answers
        session_manager.update_session(session.session_id, result)
        
        # Format response with comprehensive answer information
        answers = result.get("sub_question_answers", [])
        formatted_answers = [
            SubQuestionAnswer(
                sub_question_id=answer["sub_question_id"],
                sub_question_text=answer["sub_question_text"],
                answer=answer["answer"],
                confidence_score=answer.get("confidence_score", 0.8),
                sources_used=answer.get("sources_used", [])
            )
            for answer in answers
        ]
        
        # Calculate average confidence and analyze answer quality
        avg_confidence = sum(ans.confidence_score or 0 for ans in formatted_answers) / len(formatted_answers) if formatted_answers else 0
        high_quality_answers = sum(1 for ans in formatted_answers if (ans.confidence_score or 0) >= 0.8)
        
        processing_summary = f"Generated {len(formatted_answers)} comprehensive answers (avg. confidence: {avg_confidence:.2f}). "
        processing_summary += f"{high_quality_answers} high-quality answers were produced based on detailed data requirements and analysis approaches. "
        processing_summary += f"Each answer incorporates the specific data variables and analytical methods identified in the previous mapping step."
        
        return SubQuestionAnswersResponse(
            session_id=session.session_id,
            answers=formatted_answers,
            total_answered=len(formatted_answers),
            processing_summary=processing_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sub-question answers: {str(e)}")

# 2c. Get current analysis status
@router.get("/analysis-status/{session_id}")
async def get_analysis_status(session_id: str):
    """
    Get the current analysis status for a session including what questions have been analyzed
    """
    try:
        # Get session data
        state = session_manager.get_session(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Get analysis information
        selected_main_ids = state.get("selected_main_question_ids", [])
        mappings = state.get("mappings", [])
        answers = state.get("sub_question_answers", [])
        main_questions = state.get("main_questions", [])
        
        # Find which main questions have been analyzed
        analyzed_main_questions = []
        if selected_main_ids:
            analyzed_main_questions = [
                {
                    "id": mq.id,
                    "text": mq.text,
                    "analyzed": True
                }
                for mq in main_questions
                if mq.id in selected_main_ids
            ]
        
        unanalyzed_main_questions = [
            {
                "id": mq.id,
                "text": mq.text,
                "analyzed": False
            }
            for mq in main_questions
            if mq.id not in selected_main_ids
        ]
        
        return {
            "session_id": session_id,
            "total_main_questions": len(main_questions),
            "analyzed_main_questions_count": len(analyzed_main_questions),
            "unanalyzed_main_questions_count": len(unanalyzed_main_questions),
            "mappings_count": len(mappings),
            "answers_count": len(answers),
            "can_continue_workflow": len(mappings) > 0,
            "has_answers": len(answers) > 0,
            "analyzed_main_questions": analyzed_main_questions,
            "unanalyzed_main_questions": unanalyzed_main_questions,
            "workflow_status": {
                "questions_generated": len(main_questions) > 0,
                "questions_analyzed": len(mappings) > 0,
                "questions_answered": len(answers) > 0,
                "ready_for_next_step": len(mappings) > 0 or len(answers) > 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting analysis status: {str(e)}")

# 2d. Database Schema Exploration (before data gaps identification)
@router.get("/database-tables", response_model=List[str])
async def get_database_tables():
    """
    Get a list of all available table names in the database
    """
    try:
        from utils.database_utils import get_available_table_names
        tables = get_available_table_names()
        return tables
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting table names: {str(e)}")

@router.get("/database-table/{table_name}", response_model=TableDetailsResponse)
async def get_table_details(table_name: str):
    """
    Get detailed information about a specific table including all its columns
    """
    try:
        from utils.database_utils import get_table_details
        table_details = get_table_details(table_name)
        return table_details
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting table details: {str(e)}")

@router.post("/explore-relevant-data")
async def explore_relevant_data(session: SessionRequest):
    """
    Explore database using keywords found in actual database vocabulary.
    This endpoint finds relevant tables/columns based on research context using database-native terms.
    """
    try:
        # Get session data
        state = session_manager.get_session(session.session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Check if we have analyzed sub-questions
        mappings = state.get("mappings", [])
        if not mappings:
            raise HTTPException(
                status_code=400,
                detail="No analyzed sub-questions found. Please run analyze-subquestions first."
            )
        
        # Run the improved database exploration
        from agent_graph.nodes.research_nodes import explore_database_node
        result = explore_database_node(state)
        
        # Update session with exploration results
        session_manager.update_session(session.session_id, result)
        
        # Return the exploration results
        exploration = result.get("database_exploration", {})
        
        return {
            "session_id": session.session_id,
            "database_exploration": exploration,
            "message": "Database exploration completed using database vocabulary matching",
            "next_steps": ["Use /identify-data-gaps to identify missing variables based on available data"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exploring relevant data: {str(e)}")

@router.get("/database-keywords")
async def get_database_keywords():
    """
    Get available keywords extracted from the database schema (table names, column names, descriptions)
    """
    try:
        from utils.database_utils import extract_database_keywords, get_database_summary
        
        keywords = extract_database_keywords()
        summary = get_database_summary()
        
        return {
            "database_summary": summary,
            "available_keywords": keywords,
            "usage": "These are the actual words found in the database. Use them to understand what data is available."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting database keywords: {str(e)}")

# 3. Data gaps identification
@router.post("/identify-data-gaps", response_model=List[DataGapResponse])
async def identify_data_gaps(session: SessionRequest):
    """
    Identify data gaps and suggest sources for the analyzed sub-questions using session ID
    """
    try:
        # Get session data
        state = session_manager.get_session(session.session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Check if we have mappings from analyzed sub-questions
        mappings = state.get("mappings", [])
        if not mappings:
            raise HTTPException(
                status_code=400, 
                detail="No mappings found in session. Please run analyze-subquestions endpoint first."
            )
        
        # Filter mappings to only include those with valid sub_question_ids
        valid_mappings = [m for m in mappings if m.sub_question_id]
        if not valid_mappings:
            raise HTTPException(
                status_code=400,
                detail="No valid sub-question mappings found. Please check the analyze-subquestions step."
            )
        
        print(f"Identifying data gaps for {len(valid_mappings)} analyzed sub-questions...")
        
        # Run the data gaps identification step
        from agent_graph.nodes.research_nodes import identify_data_gaps_node
        result = identify_data_gaps_node(state)
        
        # Update session with results
        session_manager.update_session(session.session_id, result)
        
        # Format response
        data_gaps = [
            DataGapResponse(
                id=gap.id,
                missing_variable=gap.missing_variable,
                gap_description=gap.gap_description,
                suggested_sources=gap.suggested_sources,
                sub_question_id=gap.sub_question_id
            )
            for gap in result["data_gaps"]
        ]
        
        return data_gaps
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error identifying data gaps: {str(e)}")

# 4. Literature search for analyzed sub-questions
@router.post("/search-literature-analyzed")
async def search_literature_for_analyzed_subquestions(session: SessionRequest):
    """
    Search for relevant literature for analyzed sub-questions using session ID
    """
    try:
        # Get session data
        state = session_manager.get_session(session.session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Check if we have analyzed sub-questions (mappings)
        mappings = state.get("mappings", [])
        if not mappings:
            raise HTTPException(
                status_code=400,
                detail="No analyzed sub-questions found. Please run analyze-subquestions first."
            )
        
        # Run literature search for analyzed questions only
        from agent_graph.nodes.research_nodes import search_literature_node
        result = search_literature_node(state)
        
        # Update session with literature results
        session_manager.update_session(session.session_id, result)
        
        # Format literature response properly
        literature_response = {}
        for sub_question_id, papers in result.get("literature", {}).items():
            literature_response[sub_question_id] = [
                {
                    "id": paper.id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "abstract": paper.abstract,
                    "year": paper.year,
                    "venue": paper.venue,
                    "url": paper.url,
                    "relevance": paper.relevance,
                    "source": paper.source,
                    "sub_question_id": paper.sub_question_id
                }
                for paper in papers
            ]
        
        # Return literature results
        return {
            "session_id": session.session_id,
            "literature": literature_response,
            "message": f"Literature search completed for {len(mappings)} analyzed sub-questions"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching literature: {str(e)}")

# 5. Direct literature search endpoint
@router.post("/literature/search", response_model=List[Dict[str, Any]])
async def search_literature_direct(request: LiteratureSearchRequest):
    """
    Direct literature search for a specific query
    """
    try:
        papers = search_literature(request.query, limit=request.limit)
        
        # Format response
        formatted_papers = []
        for paper in papers:
            formatted_papers.append({
                "title": paper.get("title", ""),
                "authors": paper.get("authors", []),
                "abstract": paper.get("abstract", ""),
                "year": paper.get("year"),
                "venue": paper.get("venue", ""),
                "url": paper.get("url", ""),
                "relevance": paper.get("relevance", 0.0),
                "source": paper.get("source", ""),
                "citations": paper.get("citations", 0)
            })
        
        return formatted_papers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching literature: {str(e)}")

# Question selection endpoints
@router.post("/select-questions", response_model=QuestionSelectionResponse)
async def select_questions(request: QuestionSelectionRequest):
    """
    Select specific main questions and their sub-questions to continue with in the workflow
    """
    try:
        # Get session data
        state = session_manager.get_session(request.session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Validate that questions have been generated
        if not state.get("main_questions"):
            raise HTTPException(
                status_code=400, 
                detail="No main questions found. Please run generate-questions endpoint first."
            )
        
        # Validate selected question IDs
        available_main_ids = [mq.id for mq in state.get("main_questions", [])]
        invalid_ids = [qid for qid in request.selected_main_question_ids if qid not in available_main_ids]
        
        if invalid_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid main question IDs: {invalid_ids}"
            )
        
        # Update state with selected question IDs
        state["selected_main_question_ids"] = request.selected_main_question_ids
        
        # Filter questions using the selection node
        from agent_graph.nodes.research_nodes import select_questions_node
        filtered_state = select_questions_node(state)
        
        # Update session with filtered results
        session_manager.update_session(request.session_id, filtered_state)
        
        # Format response with selected questions and their sub-questions
        selected_questions = []
        for main_q in filtered_state["main_questions"]:
            # Get sub-questions for this main question
            sub_questions = [
                ResearchQuestionResponse(
                    id=sq.id,
                    text=sq.text,
                    question_type=sq.question_type,
                    parent_question_id=sq.parent_question_id
                )
                for sq in filtered_state["sub_questions"]
                if sq.parent_question_id == main_q.id
            ]
            
            selected_questions.append(
                ResearchQuestionResponse(
                    id=main_q.id,
                    text=main_q.text,
                    question_type=main_q.question_type,
                    parent_question_id=main_q.parent_question_id,
                    sub_questions=sub_questions
                )
            )
        
        return QuestionSelectionResponse(
            session_id=request.session_id,
            selected_questions=selected_questions,
            message=f"Successfully selected {len(request.selected_main_question_ids)} main questions with their sub-questions"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting questions: {str(e)}")

@router.get("/selected-questions/{session_id}", response_model=SelectedQuestionsListResponse)
async def get_selected_questions(session_id: str):
    """
    Get the list of currently selected main questions and their sub-questions for a session
    """
    try:
        # Get session data
        state = session_manager.get_session(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Check if questions have been filtered/selected
        selected_main_questions = state.get("main_questions", [])
        
        if not selected_main_questions:
            return SelectedQuestionsListResponse(
                session_id=session_id,
                selected_main_questions=[],
                total_selected=0
            )
        
        # Format response with selected questions and their sub-questions
        formatted_questions = []
        for main_q in selected_main_questions:
            # Get sub-questions for this main question
            sub_questions = [
                ResearchQuestionResponse(
                    id=sq.id,
                    text=sq.text,
                    question_type=sq.question_type,
                    parent_question_id=sq.parent_question_id
                )
                for sq in state.get("sub_questions", [])
                if sq.parent_question_id == main_q.id
            ]
            
            formatted_questions.append(
                ResearchQuestionResponse(
                    id=main_q.id,
                    text=main_q.text,
                    question_type=main_q.question_type,
                    parent_question_id=main_q.parent_question_id,
                    sub_questions=sub_questions
                )
            )
        
        return SelectedQuestionsListResponse(
            session_id=session_id,
            selected_main_questions=formatted_questions,
            total_selected=len(formatted_questions)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting selected questions: {str(e)}")

# Complete research analysis endpoint (runs all steps)
@router.post("/complete-analysis", response_model=ResearchAnalysisResponse)
async def complete_research_analysis(project: ProjectRequest):
    """
    Run the complete research analysis workflow including all steps:
    1. Generate questions
    2. Analyze sub-questions
    3. Identify data gaps
    4. Search literature
    """
    try:
        # Create ProjectInfo object
        project_info = ProjectInfo(
            title=project.title,
            description=project.description,
            area_of_study=project.area_of_study,
            geography=project.geography
        )
        
        # Build the workflow graph
        graph = build_graph()
        
        # Initialize state
        state = {
            "project": json.loads(project_info.model_dump_json()),
            "main_questions": [],
            "sub_questions": [],
            "mappings": [],
            "research_variables": [],
            "data_gaps": [],
            "literature": {},
            "custom_sub_questions": project.custom_sub_questions or [],
            "selected_main_question_ids": [],
            "questions_filtered": False,
            "sub_question_answers": []
        }
        
        # Run the complete workflow
        result = graph.invoke(state)
        
        # Format response
        main_questions = [
            ResearchQuestionResponse(
                id=mq.id,
                text=mq.text,
                question_type=mq.question_type,
                parent_question_id=mq.parent_question_id
            )
            for mq in result["main_questions"]
        ]
        
        sub_questions = [
            ResearchQuestionResponse(
                id=sq.id,
                text=sq.text,
                question_type=sq.question_type,
                parent_question_id=sq.parent_question_id
            )
            for sq in result["sub_questions"]
        ]
        
        mappings = [
            SubQuestionMappingResponse(
                sub_question_id=mapping.sub_question_id,
                sub_question=mapping.sub_question,
                data_requirements=mapping.data_requirements,
                analysis_approach=mapping.analysis_approach
            )
            for mapping in result["mappings"]
        ]
        
        data_gaps = [
            DataGapResponse(
                id=gap.id,
                missing_variable=gap.missing_variable,
                gap_description=gap.gap_description,
                suggested_sources=gap.suggested_sources,
                sub_question_id=gap.sub_question_id
            )
            for gap in result["data_gaps"]
        ]
        
        literature = {}
        for sub_question_id, papers in result["literature"].items():
            literature[sub_question_id] = [
                LiteratureResponse(
                    id=paper.id,
                    title=paper.title,
                    authors=paper.authors,
                    abstract=paper.abstract,
                    year=paper.year,
                    venue=paper.venue,
                    url=paper.url,
                    relevance=paper.relevance,
                    source=paper.source,
                    sub_question_id=paper.sub_question_id
                )
                for paper in papers
            ]
        
        return ResearchAnalysisResponse(
            main_questions=main_questions,
            sub_questions=sub_questions,
            mappings=mappings,
            data_gaps=data_gaps,
            literature=literature
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running complete analysis: {str(e)}")

# Session management endpoints
@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Get current session state
    """
    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Convert complex objects to serializable format
    response = {
        "session_id": session_id,
        "created_at": state.get("created_at"),
        "expires_at": session_manager.expiry[session_id].isoformat(),
        "project": state.get("project", {}),
        "has_main_questions": len(state.get("main_questions", [])) > 0,
        "main_questions_count": len(state.get("main_questions", [])),
        "sub_questions_count": len(state.get("sub_questions", [])),
        "selected_questions_count": len(state.get("selected_main_question_ids", [])),
        "questions_filtered": state.get("questions_filtered", False),
        "mappings_count": len(state.get("mappings", [])),
        "data_gaps_count": len(state.get("data_gaps", [])),
        "literature_count": sum(len(papers) for papers in state.get("literature", {}).values()),
        "workflow_status": {
            "questions_generated": len(state.get("main_questions", [])) > 0,
            "questions_selected": len(state.get("selected_main_question_ids", [])) > 0,
            "mappings_created": len(state.get("mappings", [])) > 0,
            "data_gaps_identified": len(state.get("data_gaps", [])) > 0,
            "literature_searched": len(state.get("literature", {})) > 0
        }
    }
    
    return response

# Additional utility endpoints
@router.get("/project-templates")
async def get_project_templates():
    """
    Get sample project templates for different research areas
    """
    templates = {
        "maternal_health": {
            "title": "Maternal Mortality Trends in Rural Kenya",
            "description": "Investigate the main causes of maternal deaths in rural healthcare settings",
            "area_of_study": "Public Health",
            "geography": "Rural Kenya"
        },
        "urban_health": {
            "title": "Healthcare Access in Urban Slums",
            "description": "Analyze barriers to healthcare access in urban informal settlements",
            "area_of_study": "Urban Health",
            "geography": "Nairobi, Kenya"
        },
        "infectious_disease": {
            "title": "TB Treatment Outcomes",
            "description": "Evaluate factors affecting tuberculosis treatment success rates",
            "area_of_study": "Infectious Diseases",
            "geography": "Sub-Saharan Africa"
        }
    }
    return templates
