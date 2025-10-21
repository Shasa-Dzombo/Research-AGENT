"""
Agent orchestration and response normalization
"""
from typing import Dict, Any
from agent_graph.graph import build_graph
from state.state import AgentState

class ResearchAssistant:
    """Research agent orchestrator"""
    
    def __init__(self):
        self.graph = build_graph()
    
    def run_complete_workflow(self, project_info: Dict[str, Any], custom_sub_questions: list = None) -> Dict[str, Any]:
        """
        Run the complete research workflow and normalize the response
        """
        # Initialize state
        initial_state: AgentState = {
            "project": project_info,
            "main_question": None,
            "sub_questions": [],
            "mappings": [],
            "research_variables": [],
            "data_gaps": [],
            "literature": {},
            "custom_sub_questions": custom_sub_questions or []
        }
        
        # Run the workflow
        result = self.graph.invoke(initial_state)
        
        # Normalize and return the response
        return self._normalize_response(result)
    
    def _normalize_response(self, result: AgentState) -> Dict[str, Any]:
        """
        Normalize the response to a consistent format
        """
        return {
            "main_question": result.get("main_question"),
            "sub_questions": result.get("sub_questions", []),
            "mappings": result.get("mappings", []),
            "research_variables": result.get("research_variables", []),
            "data_gaps": result.get("data_gaps", []),
            "literature": result.get("literature", {}),
            "project": result.get("project", {})
        }
