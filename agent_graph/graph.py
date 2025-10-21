"""
Complete StateGraph with 13-node workflow
"""
from langgraph.graph import StateGraph, END
from state.state import AgentState
from agent_graph.nodes.research_nodes import (
    generate_questions_node,
    map_subquestions_node, 
    identify_data_gaps_node,
    search_literature_node
)

def build_graph():
    """Build and compile the research workflow graph"""
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("generate_questions", generate_questions_node)
    graph.add_node("map_subquestions", map_subquestions_node)
    graph.add_node("identify_data_gaps", identify_data_gaps_node)
    graph.add_node("search_literature", search_literature_node)
    
    # Define workflow edges
    graph.set_entry_point("generate_questions")
    graph.add_edge("generate_questions", "map_subquestions")
    graph.add_edge("map_subquestions", "identify_data_gaps")
    graph.add_edge("identify_data_gaps", "search_literature")
    graph.add_edge("search_literature", END)
    
    return graph.compile()
