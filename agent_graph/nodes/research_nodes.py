"""
Research workflow nodes
"""
import json
import time
from langchain_core.messages import SystemMessage, HumanMessage
from config.llm_factory import get_llm
from state.state import AgentState
from model.models import ResearchQuestion, SubQuestionMap, DataGap, LiteratureReference, ResearchVariable
from utils.parser_utils import parse_main_and_sub_questions, parse_subquestion_mappings, parse_data_gaps
from prompts.research_prompts import PROMPT_STEP2, PROMPT_STEP3, PROMPT_STEP4
from utils.research_utils import search_literature

def generate_questions_node(state: AgentState) -> AgentState:
    """Generate multiple main research questions and sub-questions"""
    llm = get_llm()
    
    # Build system and user prompt strings and call the LLM wrapper
    system_message = PROMPT_STEP2
    user_message = f"Here is the project information: {json.dumps(state['project'], ensure_ascii=False)}. Please generate 3-5 main research questions and 3-5 sub-questions for each main question."

    # Call the LLM wrapper with explicit system prompt and user prompt string
    res = llm.invoke(user_message, system_prompt=system_message)
    content = res.content
    
    # Parse the text response
    parsed = parse_main_and_sub_questions(content)
    
    # Fallback if parsing fails
    if not parsed["main_questions"] or not parsed["sub_questions"]:
        parsed = {
            "main_questions": [
                "What are the factors contributing to maternal mortality in Turkana County?",
                "How do healthcare infrastructure challenges affect maternal health outcomes?",
                "What role do cultural practices play in maternal health decisions?"
            ],
            "sub_questions": [
                {"text": "What are the key healthcare infrastructure challenges in Turkana?", "main_question_index": 0, "main_question_text": "What are the factors contributing to maternal mortality in Turkana County?"},
                {"text": "How do cultural practices affect maternal health outcomes?", "main_question_index": 0, "main_question_text": "What are the factors contributing to maternal mortality in Turkana County?"},
                {"text": "What interventions have been effective in similar contexts?", "main_question_index": 0, "main_question_text": "What are the factors contributing to maternal mortality in Turkana County?"},
                {"text": "What is the current state of health facilities in rural areas?", "main_question_index": 1, "main_question_text": "How do healthcare infrastructure challenges affect maternal health outcomes?"},
                {"text": "How does distance to healthcare facilities affect outcomes?", "main_question_index": 1, "main_question_text": "How do healthcare infrastructure challenges affect maternal health outcomes?"},
                {"text": "What are the traditional birthing practices in the community?", "main_question_index": 2, "main_question_text": "What role do cultural practices play in maternal health decisions?"},
                {"text": "How do community beliefs influence healthcare seeking behavior?", "main_question_index": 2, "main_question_text": "What role do cultural practices play in maternal health decisions?"}
            ],
            "sub_questions_by_main": {
                0: ["What are the key healthcare infrastructure challenges in Turkana?", "How do cultural practices affect maternal health outcomes?", "What interventions have been effective in similar contexts?"],
                1: ["What is the current state of health facilities in rural areas?", "How does distance to healthcare facilities affect outcomes?"],
                2: ["What are the traditional birthing practices in the community?", "How do community beliefs influence healthcare seeking behavior?"]
            }
        }

    # Create main question objects
    main_questions = [
        ResearchQuestion(text=mq, question_type="main")
        for mq in parsed["main_questions"]
    ]
    
    # Create sub-question objects linked to their main questions
    sub_questions = []
    for sub_q_data in parsed["sub_questions"]:
        main_idx = sub_q_data.get("main_question_index", 0)
        if main_idx < len(main_questions):
            parent_id = main_questions[main_idx].id
        else:
            parent_id = main_questions[0].id if main_questions else None
            
        sub_questions.append(
            ResearchQuestion(
                text=sub_q_data["text"], 
                question_type="sub", 
                parent_question_id=parent_id
            )
        )
    
    # Add any custom sub-questions provided by the user
    if "custom_sub_questions" in state and state["custom_sub_questions"]:
        for custom_q in state["custom_sub_questions"]:
            # Link custom questions to the first main question by default
            parent_id = main_questions[0].id if main_questions else None
            sub_questions.append(
                ResearchQuestion(
                    text=custom_q, 
                    question_type="sub", 
                    parent_question_id=parent_id
                )
            )
    
    return {**state, "main_questions": main_questions, "sub_questions": sub_questions}

def map_subquestions_node(state: AgentState) -> AgentState:
    """Map sub-questions to data requirements and analysis approaches"""
    subs = state["sub_questions"]
    llm = get_llm()
    
    # Create message content and call LLM with explicit system prompt
    system_message = PROMPT_STEP3

    sub_questions_text = "\n".join([f"- {s.text}" for s in subs])
    user_message = f"Here are the sub-questions to analyze:\n{sub_questions_text}"

    res = llm.invoke(user_message, system_prompt=system_message)

    # Parse the response using our helper function
    parsed = parse_subquestion_mappings(res.content)

    text_to_id = {s.text: s.id for s in subs}
    mappings = []
    
    for i, item in enumerate(parsed):
        # Try to find exact match first
        sub_question_id = text_to_id.get(item["sub_question"])
        
        # If no exact match, try to find the best match or use the sub-question at the same index
        if not sub_question_id and i < len(subs):
            sub_question_id = subs[i].id
            print(f"Warning: Using fallback ID for sub-question: {item['sub_question']}")
        
        # If still no ID, generate a warning but continue
        if not sub_question_id:
            print(f"Error: Could not find ID for sub-question: {item['sub_question']}")
            continue
            
        mappings.append(SubQuestionMap(
            sub_question_id=sub_question_id,
            sub_question=item["sub_question"],
            data_requirements=item["data_requirements"],
            analysis_approach=item["analysis_approach"],
        ))
    
    return {**state, "mappings": mappings}

def explore_database_node(state: AgentState) -> AgentState:
    """Node to explore the database schema and identify available data before identifying gaps"""
    mappings = state.get("mappings", [])
    
    if not mappings:
        return {**state, "database_exploration": {"available_tables": [], "relevant_info": {}, "exploration_summary": "No analyzed sub-questions found"}}
    
    try:
        from utils.database_utils import parse_database_schema, find_relevant_tables_by_research_context, get_database_summary
        
        # Get database summary
        db_summary = get_database_summary()
        
        # Extract keywords from sub-questions and data requirements
        research_keywords = []
        for mapping in mappings:
            if mapping.sub_question_id:  # Only valid mappings
                # Extract keywords from sub-question text
                sub_q_words = mapping.sub_question.lower().split()
                research_keywords.extend([word.strip('?.,!') for word in sub_q_words if len(word) > 3])
                
                # Extract keywords from data requirements
                data_req_words = mapping.data_requirements.lower().split()
                research_keywords.extend([word.strip('.,!') for word in data_req_words if len(word) > 4])
        
        # Find relevant database elements using actual database vocabulary
        relevance_analysis = find_relevant_tables_by_research_context(research_keywords)
        
        exploration_result = {
            "database_summary": db_summary,
            "research_analysis": {
                "total_research_keywords": len(set(research_keywords)),
                "database_keywords_matched": relevance_analysis["database_keywords_found"],
                "matches_found": relevance_analysis["total_matches"]
            },
            "relevant_tables": relevance_analysis["relevant_tables"],
            "relevant_columns": relevance_analysis["relevant_columns"],
            "exploration_summary": f"Analyzed {len(mappings)} sub-questions, found {relevance_analysis['total_matches']} keyword matches in database vocabulary from {db_summary['statistics']['total_tables']} available tables"
        }
        
        print(f"Database exploration completed: {exploration_result['exploration_summary']}")
        
        return {**state, "database_exploration": exploration_result}
        
    except Exception as e:
        print(f"Error during database exploration: {e}")
        return {**state, "database_exploration": {"error": str(e), "exploration_summary": "Database exploration failed"}}

def identify_data_gaps_node(state: AgentState) -> AgentState:
    """Node to identify missing data variables and suggest sources."""
    mappings = state.get("mappings", [])
    
    if not mappings:
        return {**state, "data_gaps": [], "research_variables": []}
    
    llm = get_llm()
    
    # We'll start with an empty list of known variables
    # In a real implementation, you might load this from a database
    known_variables = []
    
    # Format the data requirements from each sub-question (only analyzed ones)
    sub_questions_with_requirements = []
    for mapping in mappings:
        # Only process mappings that have valid sub_question_ids
        if mapping.sub_question_id:
            sub_questions_with_requirements.append(
                f"SUB-QUESTION: {mapping.sub_question}\n"
                f"DATA REQUIREMENTS: {mapping.data_requirements}"
            )
    
    if not sub_questions_with_requirements:
        print("Warning: No valid sub-questions found for data gap analysis")
        return {**state, "data_gaps": [], "research_variables": []}
    
    # Create message content and call LLM with explicit system prompt
    system_message = PROMPT_STEP4

    known_vars_text = "\n".join([f"- {var}" for var in known_variables]) if known_variables else "None yet identified."
    reqs_text = "\n\n".join(sub_questions_with_requirements)

    user_message = (
        f"Here are the known variables we already have:\n{known_vars_text}\n\n"
        f"Here are the sub-questions with their data requirements:\n{reqs_text}\n\n"
        f"Please identify what data variables are missing for each sub-question."
    )

    res = llm.invoke(user_message, system_prompt=system_message)
    
    # Create example gaps based on the actual analyzed sub-questions
    example_gaps = []
    for i, mapping in enumerate(mappings):
        if mapping.sub_question_id:  # Only for valid mappings
            example_gaps.extend([
                {
                    "missing_variable": f"data_variable_{i+1}_geographic",
                    "gap_description": f"Geographic and spatial data needed to answer: {mapping.sub_question}",
                    "suggested_sources": "Geographic Information Systems, Census data, Survey databases",
                    "sub_question": mapping.sub_question
                },
                {
                    "missing_variable": f"data_variable_{i+1}_demographic",
                    "gap_description": f"Demographic and socioeconomic data required for: {mapping.sub_question}",
                    "suggested_sources": "Demographic Health Surveys, National statistics, Community surveys",
                    "sub_question": mapping.sub_question
                }
            ])
    
    # Try to parse the model's response, but use examples if parsing fails
    parsed_gaps = parse_data_gaps(res.content)
    if not parsed_gaps or all(gap.get("missing_variable") == "variable" for gap in parsed_gaps):
        parsed_gaps = example_gaps
    
    # Convert to DataGap objects
    text_to_id = {m.sub_question: m.sub_question_id for m in mappings}
    data_gaps = [
        DataGap(
            missing_variable=gap["missing_variable"],
            gap_description=gap["gap_description"],
            suggested_sources=gap["suggested_sources"],
            sub_question_id=text_to_id.get(gap["sub_question"], "")
        ) for gap in parsed_gaps
    ]
    
    # Also extract research variables from the data requirements
    research_variables = []
    for mapping in mappings:
        # Extract keywords from data requirements
        # This is a simple implementation - in a real app you might use NLP
        keywords = [w.strip() for w in mapping.data_requirements.split(',')]
        for keyword in keywords:
            if keyword and len(keyword) > 3:  # Skip short words
                research_variables.append(
                    ResearchVariable(
                        name=keyword,
                        description=f"Variable from {mapping.sub_question}",
                        sub_question_id=mapping.sub_question_id
                    )
                )
    
    return {**state, "data_gaps": data_gaps, "research_variables": research_variables}

def search_literature_node(state: AgentState) -> AgentState:
    """Node to search for relevant literature for analyzed sub-questions only."""
    # Get mappings to identify which sub-questions were analyzed
    mappings = state.get("mappings", [])
    all_sub_questions = state.get("sub_questions", [])
    
    if not mappings:
        print("Warning: No mappings found, skipping literature search")
        return {**state, "literature": {}}
    
    # Filter to only search literature for analyzed sub-questions
    analyzed_sub_question_ids = {m.sub_question_id for m in mappings if m.sub_question_id}
    analyzed_sub_questions = [sq for sq in all_sub_questions if sq.id in analyzed_sub_question_ids]
    
    if not analyzed_sub_questions:
        print("Warning: No analyzed sub-questions found for literature search")
        return {**state, "literature": {}}
    
    print(f"Searching literature for {len(analyzed_sub_questions)} analyzed sub-questions...")
    
    literature = {}
    total_start_time = time.time()
    
    # Limit to maximum 10 sub-questions for faster processing
    max_subquestions = 10
    if len(analyzed_sub_questions) > max_subquestions:
        print(f"Limiting literature search to first {max_subquestions} sub-questions for faster processing")
        analyzed_sub_questions = analyzed_sub_questions[:max_subquestions]
    
    for i, sq in enumerate(analyzed_sub_questions):
        print(f"Searching literature for sub-question {i+1}/{len(analyzed_sub_questions)}")
        
        # Search for literature relevant to this sub-question
        query = sq.text
        papers = search_literature(query, limit=2)  # Limit to 2 papers per sub-question
        
        # Convert to LiteratureReference objects (only if we got results)
        references = []
        for paper in papers:
            references.append(
                LiteratureReference(
                    title=paper.get("title", ""),
                    authors=paper.get("authors", []) if paper.get("authors") is not None else [],
                    abstract=paper.get("abstract", "") if paper.get("abstract") is not None else "",
                    year=paper.get("year"),
                    venue=paper.get("venue", "") if paper.get("venue") is not None else "",
                    url=paper.get("url", "") if paper.get("url") is not None else "",
                    relevance=paper.get("relevance", 0.0) if paper.get("relevance") is not None else 0.0,
                    source=paper.get("source", "") if paper.get("source") is not None else "",
                    sub_question_id=sq.id
                )
            )
        
        literature[sq.id] = references
    
    total_end_time = time.time()
    print(f"Total literature search completed in {total_end_time - total_start_time:.2f} seconds")
    
    return {**state, "literature": literature}

def select_questions_node(state: AgentState) -> AgentState:
    """Node to filter selected main questions and their sub-questions"""
    selected_main_ids = state.get("selected_main_question_ids", [])
    all_main_questions = state.get("main_questions", [])
    all_sub_questions = state.get("sub_questions", [])
    
    if not selected_main_ids:
        # If no selection made, keep all questions
        return state
    
    # Filter main questions based on selection
    selected_main_questions = [
        mq for mq in all_main_questions 
        if mq.id in selected_main_ids
    ]
    
    # Filter sub-questions to only include those linked to selected main questions
    selected_sub_questions = [
        sq for sq in all_sub_questions 
        if sq.parent_question_id in selected_main_ids
    ]
    
    return {
        **state, 
        "main_questions": selected_main_questions,
        "sub_questions": selected_sub_questions,
        "questions_filtered": True
    }

def answer_subquestions_node(state: AgentState) -> AgentState:
    """Node to generate comprehensive answers for sub-questions based on their data requirements and analysis approach"""
    mappings = state.get("mappings", [])
    
    if not mappings:
        return {**state, "sub_question_answers": []}
    
    llm = get_llm()
    answers = []
    
    # Import the enhanced answer generation prompt
    from prompts.research_prompts import PROMPT_ANSWER_GENERATION
    
    # Process each sub-question mapping to generate a comprehensive answer
    for mapping in mappings:
        try:
            # Create detailed context for answer generation
            user_message = f"""Please provide a comprehensive answer for the following research sub-question:

SUB-QUESTION: {mapping.sub_question}

DATA REQUIREMENTS IDENTIFIED:
{mapping.data_requirements}

ANALYSIS APPROACH SPECIFIED:
{mapping.analysis_approach}

CONTEXT: This sub-question is part of a larger research study. Your answer should be comprehensive, evidence-based, and directly incorporate the data requirements and analysis approach identified above."""

            # Use the LLM to generate a comprehensive answer
            # Call the LLM wrapper with the explicit answer-generation system prompt
            response = llm.invoke(user_message, system_prompt=PROMPT_ANSWER_GENERATION)
            answer_text = response.content
            
            # Calculate confidence score based on the completeness of mapping information
            confidence_score = 0.7  # Base confidence
            if len(mapping.data_requirements) > 100:  # Good data requirements
                confidence_score += 0.1
            if len(mapping.analysis_approach) > 100:  # Good analysis approach
                confidence_score += 0.1
            if mapping.sub_question_id:  # Has proper ID mapping
                confidence_score += 0.1
            
            # Create comprehensive answer object
            answer = {
                "sub_question_id": mapping.sub_question_id,
                "sub_question_text": mapping.sub_question,
                "answer": answer_text,
                "confidence_score": min(confidence_score, 1.0),  # Cap at 1.0
                "sources_used": [
                    "Research methodology analysis",
                    "Evidence-based synthesis",
                    f"Data requirements: {len(mapping.data_requirements.split())} words",
                    f"Analysis approach: {len(mapping.analysis_approach.split())} words"
                ]
            }
            
            answers.append(answer)
            
        except Exception as e:
            # If individual answer generation fails, create a detailed placeholder
            print(f"Error generating answer for sub-question {mapping.sub_question}: {e}")
            answer = {
                "sub_question_id": mapping.sub_question_id,
                "sub_question_text": mapping.sub_question,
                "answer": f"""**PROCESSING ERROR ENCOUNTERED**

The system encountered an error while generating a comprehensive answer for this sub-question. However, based on the analysis framework:

**DATA REQUIREMENTS IDENTIFIED:**
{mapping.data_requirements}

**RECOMMENDED ANALYSIS APPROACH:**
{mapping.analysis_approach}

**SUGGESTED NEXT STEPS:**
1. Review the data requirements to ensure all necessary variables are available
2. Apply the specified analysis approach once data is collected
3. Consider alternative analytical methods if primary approach is not feasible

Please retry the analysis or consult with a research methodologist for manual review.""",
                "confidence_score": 0.2,
                "sources_used": ["Error in processing - manual review required"]
            }
            answers.append(answer)
    
    print(f"Generated {len(answers)} comprehensive answers for sub-questions")
    return {**state, "sub_question_answers": answers}
