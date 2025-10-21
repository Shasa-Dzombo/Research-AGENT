"""
Test script for question selection functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_question_selection_workflow():
    """Test the complete question selection workflow"""
    
    print("=== Testing Question Selection Workflow ===\n")
    
    # 1. Create session and generate questions
    print("1. Creating session and generating questions...")
    project_data = {
        "title": "Climate Change Impact on Agricultural Productivity",
        "description": "Investigating how climate change affects crop yields and farming practices",
        "area_of_study": "Environmental Science",
        "geography": "Sub-Saharan Africa",
        "custom_sub_questions": [
            "What are the current climate adaptation strategies used by farmers?",
            "How does rainfall variability affect crop selection?"
        ]
    }
    
    response = requests.post(f"{BASE_URL}/generate-questions", json=project_data)
    if response.status_code != 200:
        print(f"Error generating questions: {response.text}")
        return
    
    result = response.json()
    session_id = result["session_id"]
    main_questions = result["main_questions"]
    
    print(f"Generated {len(main_questions)} main questions:")
    for i, mq in enumerate(main_questions, 1):
        print(f"  {i}. {mq['text']} (ID: {mq['id']})")
        print(f"     Sub-questions: {len(mq['sub_questions'])}")
        for j, sq in enumerate(mq['sub_questions'], 1):
            print(f"       {j}. {sq['text']}")
        print()
    
    # 2. Select specific main questions (let's select the first 2)
    print("2. Selecting first 2 main questions...")
    selected_ids = [mq['id'] for mq in main_questions[:2]]
    
    selection_data = {
        "session_id": session_id,
        "selected_main_question_ids": selected_ids
    }
    
    response = requests.post(f"{BASE_URL}/select-questions", json=selection_data)
    if response.status_code != 200:
        print(f"Error selecting questions: {response.text}")
        return
    
    selection_result = response.json()
    print(f"Selection successful: {selection_result['message']}")
    print(f"Selected {len(selection_result['selected_questions'])} main questions with their sub-questions\n")
    
    # 3. Analyze sub-questions for specific main questions (using IDs)
    print("3. Analyzing sub-questions for selected main questions...")
    analysis_data = {
        "session_id": session_id,
        "main_question_ids": selected_ids
    }
    
    response = requests.post(f"{BASE_URL}/analyze-subquestions", json=analysis_data)
    if response.status_code != 200:
        print(f"Error analyzing sub-questions: {response.text}")
        return
    
    analysis_result = response.json()
    print(f"Analysis completed for {len(analysis_result)} sub-questions:")
    for i, mapping in enumerate(analysis_result, 1):
        print(f"  {i}. Sub-question: {mapping['sub_question']}")
        print(f"     Data Requirements: {mapping['data_requirements'][:100]}...")
        print(f"     Analysis Approach: {mapping['analysis_approach'][:100]}...")
        print()
    
    # 4. Alternative: Analyze previously selected sub-questions
    print("4. Testing analysis of previously selected questions...")
    session_data = {"session_id": session_id}
    
    response = requests.post(f"{BASE_URL}/analyze-selected-subquestions", json=session_data)
    if response.status_code == 200:
        print("✓ Successfully analyzed previously selected sub-questions")
    else:
        print(f"✗ Error with selected analysis: {response.text}")
    
    # 5. Get selected questions list
    print("5. Retrieving selected questions...")
    response = requests.get(f"{BASE_URL}/selected-questions/{session_id}")
    if response.status_code != 200:
        print(f"Error getting selected questions: {response.text}")
        return
    
    selected_result = response.json()
    print(f"Currently selected: {selected_result['total_selected']} main questions")
    
    for i, mq in enumerate(selected_result['selected_main_questions'], 1):
        print(f"  {i}. {mq['text']}")
        print(f"     Sub-questions: {len(mq['sub_questions'])}")
        for j, sq in enumerate(mq['sub_questions'], 1):
            print(f"       {j}. {sq['text']}")
        print()
    
    # 6. Check session status
    print("6. Checking session status...")
    response = requests.get(f"{BASE_URL}/session/{session_id}")
    if response.status_code == 200:
        status = response.json()
        print(f"Session status:")
        print(f"  - Questions generated: {status['workflow_status']['questions_generated']}")
        print(f"  - Questions selected: {status['workflow_status']['questions_selected']}")
        print(f"  - Mappings created: {status['workflow_status']['mappings_created']}")
        print(f"  - Selected questions count: {status['selected_questions_count']}")
        print(f"  - Questions filtered: {status['questions_filtered']}")
    
    print(f"\nSession ID for further testing: {session_id}")
    return session_id, selected_ids

def test_invalid_selection(session_id):
    """Test error handling for invalid question selection"""
    print("\n=== Testing Invalid Selection ===")
    
    # Try to select non-existent question IDs
    invalid_data = {
        "session_id": session_id,
        "selected_main_question_ids": ["invalid-id-1", "invalid-id-2"]
    }
    
    response = requests.post(f"{BASE_URL}/select-questions", json=invalid_data)
    if response.status_code == 400:
        print("✓ Invalid ID handling works correctly")
        print(f"  Error message: {response.json()['detail']}")
    else:
        print("✗ Invalid ID handling failed")

def test_targeted_analysis(session_id, available_main_ids):
    """Test analyzing specific main questions by ID"""
    print("\n=== Testing Targeted Sub-Question Analysis ===")
    
    # Test 1: Analyze only the first main question
    print("1. Analyzing sub-questions for first main question only...")
    analysis_data = {
        "session_id": session_id,
        "main_question_ids": [available_main_ids[0]]
    }
    
    response = requests.post(f"{BASE_URL}/analyze-subquestions", json=analysis_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Successfully analyzed {len(result)} sub-questions for 1 main question")
    else:
        print(f"✗ Failed to analyze: {response.text}")
    
    # Test 2: Analyze multiple specific main questions
    if len(available_main_ids) >= 2:
        print("2. Analyzing sub-questions for multiple specific main questions...")
        analysis_data = {
            "session_id": session_id,
            "main_question_ids": available_main_ids[:2]
        }
        
        response = requests.post(f"{BASE_URL}/analyze-subquestions", json=analysis_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Successfully analyzed {len(result)} sub-questions for 2 main questions")
        else:
            print(f"✗ Failed to analyze: {response.text}")
    
    # Test 3: Try to analyze with invalid main question ID
    print("3. Testing with invalid main question ID...")
    invalid_analysis_data = {
        "session_id": session_id,
        "main_question_ids": ["invalid-main-question-id"]
    }
    
    response = requests.post(f"{BASE_URL}/analyze-subquestions", json=invalid_analysis_data)
    if response.status_code == 400:
        print("✓ Invalid main question ID handling works correctly")
        print(f"  Error message: {response.json()['detail']}")
    else:
        print("✗ Invalid main question ID handling failed")

if __name__ == "__main__":
    try:
        session_id, selected_ids = test_question_selection_workflow()
        if session_id:
            test_invalid_selection(session_id)
            test_targeted_analysis(session_id, selected_ids)
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"Test failed with error: {e}")
