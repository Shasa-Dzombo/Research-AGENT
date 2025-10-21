"""
Simple test to demonstrate the fixed workflow
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_simple_workflow():
    """Test the simplified workflow without confusion"""
    
    print("=== Testing Simple Analysis Workflow ===\n")
    
    # 1. Generate questions
    print("1. Generating questions...")
    project_data = {
        "title": "Climate Change and Agriculture",
        "description": "Study climate impacts on farming",
        "area_of_study": "Environmental Science",
        "geography": "East Africa"
    }
    
    response = requests.post(f"{BASE_URL}/generate-questions", json=project_data)
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    result = response.json()
    session_id = result["session_id"]
    main_questions = result["main_questions"]
    
    print(f"✓ Generated {len(main_questions)} main questions")
    print(f"Session ID: {session_id}\n")
    
    # Show the main questions
    print("Available main questions:")
    for i, mq in enumerate(main_questions, 1):
        print(f"  {i}. {mq['text']}")
        print(f"     ID: {mq['id']}")
        print(f"     Sub-questions: {len(mq['sub_questions'])}")
        print()
    
    # 2. Analyze specific main questions (choose first 2)
    print("2. Analyzing first 2 main questions...")
    selected_ids = [mq['id'] for mq in main_questions[:2]]
    
    analysis_data = {
        "session_id": session_id,
        "main_question_ids": selected_ids
    }
    
    response = requests.post(f"{BASE_URL}/analyze-subquestions", json=analysis_data)
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    analysis_result = response.json()
    print(f"✓ Analyzed {len(analysis_result)} sub-questions")
    print(f"Analysis completed for main questions: {selected_ids[:2]}...\n")
    
    # 3. Check analysis status
    print("3. Checking analysis status...")
    response = requests.get(f"{BASE_URL}/analysis-status/{session_id}")
    if response.status_code == 200:
        status = response.json()
        print(f"✓ Analysis Status:")
        print(f"  - Total main questions: {status['total_main_questions']}")
        print(f"  - Analyzed: {status['analyzed_main_questions_count']}")
        print(f"  - Can continue workflow: {status['can_continue_workflow']}")
        print(f"  - Ready for next step: {status['workflow_status']['ready_for_next_step']}")
    else:
        print(f"Error getting status: {response.text}")
        return
    
    # 4. Now generate answers for the analyzed sub-questions
    print("\n4. Generating answers for analyzed sub-questions...")
    session_data = {"session_id": session_id}
    
    response = requests.post(f"{BASE_URL}/analyze-selected-subquestions", json=session_data)
    if response.status_code == 200:
        answers_result = response.json()
        print(f"✓ Generated answers for {answers_result['total_answered']} sub-questions!")
        print(f"Processing summary: {answers_result['processing_summary']}")
        
        # Show first few answers
        print("\nSample answers generated:")
        for i, answer in enumerate(answers_result['answers'][:2], 1):  # Show first 2
            print(f"  {i}. Question: {answer['sub_question_text']}")
            print(f"     Answer: {answer['answer'][:150]}...")
            print(f"     Confidence: {answer['confidence_score']}")
            print()
    else:
        print(f"✗ Error generating answers: {response.text}")
        return
    
    # 5. Check updated analysis status
    print("5. Checking updated analysis status...")
    response = requests.get(f"{BASE_URL}/analysis-status/{session_id}")
    if response.status_code == 200:
        status = response.json()
        print(f"✓ Updated Analysis Status:")
        print(f"  - Total main questions: {status['total_main_questions']}")
        print(f"  - Analyzed: {status['analyzed_main_questions_count']}")
        print(f"  - Sub-questions answered: {status['answers_count']}")
        print(f"  - Has answers: {status['has_answers']}")
        print(f"  - Questions answered: {status['workflow_status']['questions_answered']}")
    else:
        print(f"Error getting status: {response.text}")
        return
    
    # 6. Continue to next step (identify data gaps)
    print("\n6. Continuing to identify data gaps...")
    response = requests.post(f"{BASE_URL}/identify-data-gaps", json=session_data)
    if response.status_code == 200:
        gaps = response.json()
        print(f"✓ Identified {len(gaps)} data gaps")
        print("✓ Workflow continues smoothly with same session ID!")
    else:
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    
    print(f"\n🎉 Complete! Session {session_id} now includes:")
    print("  ✓ Generated questions")
    print("  ✓ Analyzed sub-questions") 
    print("  ✓ Generated comprehensive answers")
    print("  ✓ Ready for all next steps")
    return session_id

if __name__ == "__main__":
    try:
        test_simple_workflow()
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"Test failed with error: {e}")
