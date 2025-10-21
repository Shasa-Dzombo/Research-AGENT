"""
Agent state definitions
"""
from typing import List, Optional, Dict, Any, TypedDict
from model.models import ResearchQuestion, SubQuestionMap, ResearchVariable, DataGap, LiteratureReference

class AgentState(TypedDict):
    """State for the research agent workflow"""
    project: Dict[str, Any]
    main_questions: List[ResearchQuestion]  # Changed from single main_question to multiple
    sub_questions: List[ResearchQuestion]
    mappings: List[SubQuestionMap]
    research_variables: List[ResearchVariable]
    data_gaps: List[DataGap]
    literature: Dict[str, List[LiteratureReference]]  # key: sub_question_id
    selected_main_question_ids: Optional[List[str]]  # IDs of selected main questions
    questions_filtered: Optional[bool]  # Flag to indicate if questions have been filtered
    sub_question_answers: Optional[List[Dict[str, Any]]]  # Answers to sub-questions
