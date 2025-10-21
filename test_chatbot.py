"""
Test script for the conversational research agent
"""
import requests
import json
import time

API_BASE_URL = "http://localhost:8000/api/chatbot"

def test_chatbot_conversation():
    """Test a complete conversation flow with the chatbot"""
    
    print("🤖 Testing Conversational Research Agent")
    print("=" * 50)
    
    # Start a new chat session
    print("1. Starting new chat session...")
    response = requests.post(f"{API_BASE_URL}/chat/start")
    
    if response.status_code != 200:
        print(f"❌ Failed to start chat session: {response.text}")
        return
    
    session_data = response.json()
    session_id = session_data["session_id"]
    print(f"✅ Chat session started: {session_id}")
    print(f"Bot: {session_data['message'][:100]}...")
    print()
    
    # Test conversation flow
    conversation_steps = [
        "I'm ready to start my research project",
        """My research title is: Impact of Digital Health Technologies on Rural Healthcare Access
        Description: This study examines how mobile health apps and telemedicine services affect healthcare accessibility in rural communities
        Area of Study: Public Health
        Geographic Focus: Kenya""",
        "I select questions 1 and 2",
        "Continue to next stage",
        "Start literature search",
        "Export my research framework"
    ]
    
    for i, message in enumerate(conversation_steps, 2):
        print(f"{i}. Sending message: '{message[:50]}...'")
        
        response = requests.post(
            f"{API_BASE_URL}/chat/{session_id}/message",
            json={"message": message}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to send message: {response.text}")
            continue
        
        bot_response = response.json()
        print(f"Bot stage: {bot_response.get('stage', 'unknown')}")
        print(f"Bot: {bot_response['message'][:100]}...")
        
        if bot_response.get("options"):
            print(f"Options: {bot_response['options'][:3]}...")
        
        print()
        
        # Add delay to simulate natural conversation
        time.sleep(1)
    
    # Test session status
    print("Final session status:")
    response = requests.get(f"{API_BASE_URL}/chat/{session_id}/status")
    if response.status_code == 200:
        status = response.json()
        print(f"✅ Final stage: {status['stage']}")
        print(f"✅ User data keys: {list(status['user_data'].keys())}")
    
    # Test export
    print("\nTesting export...")
    response = requests.get(f"{API_BASE_URL}/chat/{session_id}/export")
    if response.status_code == 200:
        export_data = response.json()
        print(f"✅ Export successful: {len(export_data['export_data'])} keys")
        
        # Save to file
        with open("test_export.json", "w") as f:
            json.dump(export_data, f, indent=2)
        print("✅ Export saved to test_export.json")
    
    print("\n🎉 Chatbot test completed!")

def test_api_endpoints():
    """Test individual API endpoints"""
    print("🔧 Testing API Endpoints")
    print("=" * 30)
    
    # Test health check
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
    except:
        print("❌ Cannot connect to API server")
        return
    
    # Test chat start
    try:
        response = requests.post(f"{API_BASE_URL}/chat/start")
        if response.status_code == 200:
            print("✅ Chat start endpoint working")
            session_id = response.json()["session_id"]
            
            # Test message endpoint
            response = requests.post(
                f"{API_BASE_URL}/chat/{session_id}/message",
                json={"message": "Hello"}
            )
            if response.status_code == 200:
                print("✅ Chat message endpoint working")
            else:
                print("❌ Chat message endpoint failed")
                
        else:
            print("❌ Chat start endpoint failed")
    except Exception as e:
        print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Test API endpoints only")
    print("2. Test full conversation flow")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_api_endpoints()
    elif choice == "2":
        test_chatbot_conversation()
    else:
        print("Invalid choice. Running API endpoints test...")
        test_api_endpoints()
