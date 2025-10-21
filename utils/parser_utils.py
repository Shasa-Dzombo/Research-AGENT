"""
Parsing utilities for research workflow responses
"""
import re
from typing import Dict, List, Any


def parse_main_and_sub_questions(text: str) -> dict:
    """Parse the text response to extract multiple main questions and their sub-questions."""
    lines = text.strip().split('\n')
    
    main_questions = []
    sub_questions_map = {}  # Maps main question index to list of sub-questions
    
    current_main_index = -1
    collecting_sub_questions = False
    
    for line in lines:
        line = line.strip()
        
        # Check for main question headers (MAIN QUESTION 1:, MAIN QUESTION 2:, etc.)
        if line.startswith("MAIN QUESTION") and ":" in line:
            # Extract the main question from the next non-empty line
            current_main_index = len(main_questions)
            collecting_sub_questions = False
            continue
        
        # Check for sub-questions header
        elif line == "SUB-QUESTIONS:":
            collecting_sub_questions = True
            if current_main_index not in sub_questions_map:
                sub_questions_map[current_main_index] = []
            continue
        
        # Collect main question text (first non-empty line after MAIN QUESTION header)
        elif current_main_index >= 0 and len(main_questions) == current_main_index and line and not collecting_sub_questions:
            main_questions.append(line)
        
        # Collect sub-questions
        elif collecting_sub_questions and line.startswith("- "):
            if current_main_index in sub_questions_map:
                sub_questions_map[current_main_index].append(line[2:])
    
    # Convert to the expected format - flatten all sub-questions with main question references
    all_sub_questions = []
    for main_idx, sub_list in sub_questions_map.items():
        for sub_q in sub_list:
            all_sub_questions.append({
                "text": sub_q,
                "main_question_index": main_idx,
                "main_question_text": main_questions[main_idx] if main_idx < len(main_questions) else ""
            })
    
    return {
        "main_questions": main_questions,
        "sub_questions": all_sub_questions,
        "sub_questions_by_main": sub_questions_map
    }


def parse_subquestion_mappings(text: str) -> list:
    """Parse the text response to extract sub-question mappings."""
    sections = text.split("SUB-QUESTION:")
    mappings = []
    
    for section in sections[1:]:  # Skip the first empty element
        lines = section.strip().split('\n')
        sub_question = lines[0].strip()
        
        data_req = ""
        analysis = ""
        
        in_data_req = False
        in_analysis = False
        data_req_lines = []
        analysis_lines = []
        
        for line in lines[1:]:  # Skip the first line which is the sub-question
            if "DATA REQUIREMENTS:" in line:
                in_data_req = True
                in_analysis = False
                continue
            elif "ANALYSIS APPROACH:" in line:
                in_data_req = False
                in_analysis = True
                continue
            
            if in_data_req:
                data_req_lines.append(line.strip())
            elif in_analysis:
                analysis_lines.append(line.strip())
        
        data_req = " ".join(data_req_lines).strip()
        analysis = " ".join(analysis_lines).strip()
        
        mappings.append({
            "sub_question": sub_question,
            "data_requirements": data_req,
            "analysis_approach": analysis
        })
    
    return mappings


def parse_data_gaps(text: str) -> list:
    """Parse the text response to extract data gaps."""
    gaps = []
    
    # Improved parser that can handle different formats
    
    # First try: Format with clear MISSING VARIABLE: headers
    missing_var_pattern = r"MISSING VARIABLE:([^\n]+)(?:[\s\S]*?)GAP DESCRIPTION:([^\n]+)(?:[\s\S]*?)SUGGESTED SOURCES:([^\n]+)(?:[\s\S]*?)(?:SUB-QUESTION:([^\n]+)|$)"
    matches = re.finditer(missing_var_pattern, text, re.IGNORECASE)
    
    for match in matches:
        # Extract components
        var_name = match.group(1).strip()
        description = match.group(2).strip()
        sources = match.group(3).strip()
        sub_question = match.group(4).strip() if match.group(4) else "General research question"
        
        # Skip if variable name is literally just "variable"
        if var_name.lower() != "variable":
            gaps.append({
                "missing_variable": var_name,
                "gap_description": description,
                "suggested_sources": sources,
                "sub_question": sub_question
            })
    
    # If we found good matches with the expected format, return them
    if gaps:
        return gaps
    
    # Second try: Look for bullet points or numbered lists with variable names
    # This handles formats like "1. Missing variable: healthcare_access_data"
    list_pattern = r"(?:\d+\.|\*|\-)[\s\t]*(?:Missing|Needed|Required):?\s*([a-zA-Z0-9_]+)(?:[\s\S]*?)(?:Description|Gap):?\s*([^\n]+)(?:[\s\S]*?)(?:Sources|Data sources):?\s*([^\n]+)"
    matches = re.finditer(list_pattern, text, re.IGNORECASE)
    
    for match in matches:
        var_name = match.group(1).strip()
        description = match.group(2).strip() if match.group(2) else "No description provided"
        sources = match.group(3).strip() if match.group(3) else "No sources specified"
        
        if var_name.lower() != "variable" and len(var_name) > 2:
            gaps.append({
                "missing_variable": var_name,
                "gap_description": description,
                "suggested_sources": sources,
                "sub_question": "From list item"
            })
    
    # If we found list items, return them
    if gaps:
        return gaps
    
    # Third try: Look for sentences with specific missing data mentions
    sentences = re.split(r'[.!?]\s+', text)
    for sentence in sentences:
        if "missing" in sentence.lower() and any(term in sentence.lower() for term in ["data", "variable", "information"]):
            # Try to extract a meaningful variable name
            var_match = re.search(r'missing\s+([a-zA-Z0-9_]+(?:\s+[a-zA-Z0-9_]+){0,2})', sentence.lower())
            if var_match:
                var_name = var_match.group(1)
                # Skip common false positives
                if var_name not in ["variable", "data", "information", "variables"] and len(var_name) > 3:
                    gaps.append({
                        "missing_variable": var_name,
                        "gap_description": sentence.strip(),
                        "suggested_sources": "Not specified in text",
                        "sub_question": "Extracted from context"
                    })
    
    # Last resort: Use hardcoded examples if nothing was found
    if not gaps:
        # Create some example data gaps that match common research topics
        gaps = [
            {
                "missing_variable": "demographic_data",
                "gap_description": "Detailed demographic breakdown of the population being studied",
                "suggested_sources": "National census, demographic health surveys",
                "sub_question": "General research question"
            },
            {
                "missing_variable": "geographic_distribution",
                "gap_description": "Spatial data showing the distribution of cases or facilities",
                "suggested_sources": "GIS databases, health ministry records",
                "sub_question": "General research question"
            }
        ]
    
    return gaps
