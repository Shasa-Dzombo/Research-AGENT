"""
Test client for the AI Research Agent FastAPI endpoints
Run this script to test all the API endpoints
"""

import requests
import json
from typing import Dict, Any
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_welcome():
    """Test the welcome endpoint"""
    print("=== Testing Welcome Endpoint ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_create_session():
    """Test creating a new session"""
    print("=== Testing Session Creation ===")
    
    project_data = {
        "title": "Maternal Mortality Trends in Rural Kenya",
        "description": "Find main causes of maternal deaths",
        "area_of_study": "Public Health",
        "geography": "Rural Kenya",
        "custom_sub_questions": [
            "What are the training levels of healthcare providers in rural areas?",
            "How does transportation infrastructure affect maternal care access?"
        ]
    }
    
    response = requests.post(f"{BASE_URL}/session", json=project_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Session ID: {result['session_id']}")
        print(f"Expires at: {result['expires_at']}")
        # Return the session ID for use in other tests
        return result['session_id']
    else:
        print(f"Error: {response.text}")
        return None
    print()

def test_generate_main_question(session_id):
    """Test generating the main research question"""
    print("=== Testing Main Question Generation ===")
    
    session_data = {
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/research/main-question", json=session_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("Main Question:")
        print(f"  ID: {result['id']}")
        print(f"  Question: {result['text']}")
        print(f"  Type: {result['question_type']}")
    else:
        print(f"Error: {response.text}")
    print()

def test_generate_sub_questions(session_id):
    """Test generating sub-questions"""
    print("=== Testing Sub-Question Generation ===")
    
    session_data = {
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/research/sub-questions", json=session_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        sub_questions = response.json()
        print(f"Generated {len(sub_questions)} sub-questions:")
        for i, sq in enumerate(sub_questions, 1):
            print(f"  {i}. {sq['text']}")
    else:
        print(f"Error: {response.text}")
    print()

def test_generate_mappings(session_id):
    """Test generating mappings for sub-questions"""
    print("=== Testing Sub-Question Mappings ===")
    
    session_data = {
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/research/mappings", json=session_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        mappings = response.json()
        for i, mapping in enumerate(mappings, 1):
            print(f"\n{i}. {mapping['sub_question']}")
            print(f"   Data Requirements: {mapping['data_requirements'][:100]}...")
            print(f"   Analysis Approach: {mapping['analysis_approach'][:100]}...")
    else:
        print(f"Error: {response.text}")
    print()

def test_identify_data_gaps(session_id):
    """Test identifying data gaps"""
    print("=== Testing Data Gaps Identification ===")
    
    session_data = {
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/research/data-gaps", json=session_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        gaps = response.json()
        for i, gap in enumerate(gaps, 1):
            print(f"\n{i}. Missing Variable: {gap['missing_variable']}")
            print(f"   Description: {gap['gap_description'][:100]}...")
            print(f"   Sources: {gap['suggested_sources'][:100]}...")
    else:
        print(f"Error: {response.text}")
    print()

def test_literature_search(session_id):
    """Test literature search for all sub-questions"""
    print("=== Testing Literature Search for Sub-Questions ===")
    
    session_data = {
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/research/literature", json=session_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        literature = response.json()
        for sq_id, papers in literature.items():
            print(f"\nSub-question ID: {sq_id}")
            print(f"Found {len(papers)} papers:")
            for i, paper in enumerate(papers[:2], 1):  # Show only first 2 papers per question
                print(f"  {i}. {paper['title']}")
                print(f"     Relevance: {paper['relevance']:.3f}")
    else:
        print(f"Error: {response.text}")
    print()

def test_specific_literature_search():
    """Test specific literature search"""
    print("=== Testing Specific Literature Search ===")
    
    search_data = {
        "query": "maternal mortality Kenya",
        "limit": 5
    }
    
    response = requests.post(f"{BASE_URL}/literature/search", json=search_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        papers = response.json()
        print(f"Found {len(papers)} papers:")
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper['title']}")
            print(f"   Authors: {', '.join(paper['authors'][:3])}")
            print(f"   Year: {paper.get('year', 'N/A')}")
            print(f"   Relevance: {paper['relevance']:.3f}")
            print(f"   Source: {paper['source']}")
    else:
        print(f"Error: {response.text}")
    print()

def test_get_complete_research(session_id):
    """Test getting complete research analysis"""
    print("=== Testing Complete Research Analysis ===")
    
    session_data = {
        "session_id": session_id
    }
    
    response = requests.get(f"{BASE_URL}/research/complete", json=session_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print("MAIN QUESTION:")
        print(f"  {result['main_question']['text']}")
        
        print(f"\nSUB-QUESTIONS ({len(result['sub_questions'])}):")
        for i, sq in enumerate(result['sub_questions'], 1):
            print(f"  {i}. {sq['text']}")
        
        print(f"\nDATA REQUIREMENTS & ANALYSIS ({len(result['mappings'])}):")
        for i, mapping in enumerate(result['mappings'], 1):
            print(f"  {i}. {mapping['sub_question'][:50]}...")
        
        print(f"\nDATA GAPS ({len(result['data_gaps'])}):")
        for i, gap in enumerate(result['data_gaps'], 1):
            print(f"  {i}. {gap['missing_variable']}")
        
        print(f"\nLITERATURE:")
        total_papers = sum(len(papers) for papers in result['literature'].values())
        print(f"  Found literature for {len(result['literature'])} sub-questions")
        print(f"  Total papers: {total_papers}")
        
    else:
        print(f"Error: {response.text}")
    print()

def test_run_all_workflow():
    """Test running the complete workflow in one go"""
    print("=== Testing Complete Workflow Run ===")
    
    project_data = {
        "title": "Healthcare Access in Urban Slums",
        "description": "Analyze barriers to healthcare access in urban informal settlements",
        "area_of_study": "Urban Health",
        "geography": "Nairobi, Kenya"
    }
    
    response = requests.post(f"{BASE_URL}/research/run-all", json=project_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Session ID: {result['session_id']}")
        print(f"Expires at: {result['expires_at']}")
        
        workflow_result = result.get('result', {})
        print("\nWorkflow Result:")
        
        if 'main_question' in workflow_result:
            print(f"Main Question: {workflow_result['main_question']['text']}")
        
        if 'sub_questions' in workflow_result:
            print(f"Sub-questions: {len(workflow_result['sub_questions'])}")
        
        if 'mappings' in workflow_result:
            print(f"Mappings: {len(workflow_result['mappings'])}")
        
        if 'data_gaps' in workflow_result:
            print(f"Data Gaps: {len(workflow_result['data_gaps'])}")
        
        if 'literature' in workflow_result:
            lit_count = sum(len(papers) for papers in workflow_result['literature'].values())
            print(f"Literature: {lit_count} papers")
    else:
        print(f"Error: {response.text}")
    print()

def main():
    """Run all tests"""
    print("AI Research Agent API Test Client")
    print("=" * 50)
    
    try:
        # Test each endpoint in sequence
        test_welcome()
        
        # Create a session and use it for subsequent tests
        session_id = test_create_session()
        
        if session_id:
            # Step-by-step workflow
            test_generate_main_question(session_id)
            test_generate_sub_questions(session_id)
            test_generate_mappings(session_id)
            test_identify_data_gaps(session_id)
            test_literature_search(session_id)
            test_get_complete_research(session_id)
        
        # Tests that don't require a session
        test_specific_literature_search()
        test_run_all_workflow()
        
        print("All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server.")
        print("Make sure the FastAPI server is running on http://localhost:8000")
        print("Run: python start_api.py")

if __name__ == "__main__":
    main()
