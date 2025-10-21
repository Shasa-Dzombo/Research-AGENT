"""
Streamlit Chatbot Interface for AI Research Agent
A conversational interface for the research workflow
"""

import streamlit as st
import requests
import json
from typing import Dict, Any, List
from datetime import datetime
import time

# Configure Streamlit page
st.set_page_config(
    page_title="AI Research Agent - Chat Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/chatbot"  

# Custom CSS for chat interface
st.markdown("""
<style>
.chat-container {
    max-height: 600px;
    overflow-y: auto;
    padding: 1rem;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    background-color: #f9f9f9;
}

.user-message {
    background-color: #007bff;
    color: white;
    padding: 10px 15px;
    border-radius: 18px;
    margin: 5px 0;
    margin-left: 20%;
    text-align: right;
}

.bot-message {
    background-color: #e9ecef;
    color: #333;
    padding: 10px 15px;
    border-radius: 18px;
    margin: 5px 0;
    margin-right: 20%;
}

.stage-indicator {
    background-color: #28a745;
    color: white;
    padding: 5px 10px;
    border-radius: 15px;
    font-size: 0.8em;
    margin-bottom: 10px;
    display: inline-block;
}

.quick-options {
    margin: 10px 0;
}

.quick-options button {
    margin: 2px;
    padding: 5px 10px;
    border: 1px solid #007bff;
    background-color: white;
    color: #007bff;
    border-radius: 15px;
    cursor: pointer;
}

.quick-options button:hover {
    background-color: #007bff;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_session_id' not in st.session_state:
    st.session_state.chat_session_id = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_stage' not in st.session_state:
    st.session_state.current_stage = "introduction"
if 'is_typing' not in st.session_state:
    st.session_state.is_typing = False

def make_chat_request(endpoint: str, method: str = "POST", data: Dict = None) -> Dict:
    """Make API request to chatbot endpoints"""
    try:
        url = f"{API_BASE_URL}/{endpoint}"
        
        if method == "POST":
            response = requests.post(url, json=data)
        elif method == "GET":
            response = requests.get(url)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            response = requests.get(url)
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        if hasattr(e, 'response') and e.response:
            st.error(f"Response: {e.response.text}")
        return None

def start_chat_session():
    """Start a new chat session"""
    # Send proper request body structure expected by the API
    data = {"user_id": None}  # Optional field, can be None
    response = make_chat_request("chat/start", data=data)
    if response:
        st.session_state.chat_session_id = response["session_id"]
        st.session_state.chat_history = []
        add_message_to_history("bot", response["message"], response.get("stage", ""), response.get("options", []))
        return True
    return False

def send_message(message: str, context: Dict = None):
    """Send a message to the chatbot"""
    if not st.session_state.chat_session_id:
        if not start_chat_session():
            return False
    
    # Add user message to history
    add_message_to_history("user", message)
    
    # Show typing indicator
    st.session_state.is_typing = True
    
    # Send message to API
    data = {
        "session_id": st.session_state.chat_session_id,
        "message": message,
        "action": "chat"  # Default action
    }
    if context:
        data["context"] = context
    
    response = make_chat_request("chat/message", data=data)
    
    # Hide typing indicator
    st.session_state.is_typing = False
    
    if response:
        st.session_state.current_stage = response.get("stage", "")
        add_message_to_history("bot", response["message"], response.get("stage", ""), response.get("options", []))
        
        # Handle special actions
        if response.get("action") == "export":
            st.session_state.export_ready = True
        
        return True
    return False

def add_message_to_history(sender: str, message: str, stage: str = "", options: List[str] = None):
    """Add a message to chat history"""
    st.session_state.chat_history.append({
        "sender": sender,
        "message": message,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "stage": stage,
        "options": options or []
    })

def display_chat_history():
    """Display the chat history"""
    chat_container = st.container()
    
    with chat_container:
        for i, msg in enumerate(st.session_state.chat_history):
            if msg["sender"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    {msg["message"]}
                    <br><small>{msg["timestamp"]}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Show stage indicator for bot messages
                if msg.get("stage"):
                    stage_display = msg["stage"].replace("_", " ").title()
                    st.markdown(f"""
                    <div class="stage-indicator">
                        Stage: {stage_display}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="bot-message">
                    {msg["message"]}
                    <br><small>{msg["timestamp"]}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Show quick option buttons for the latest bot message
                if i == len(st.session_state.chat_history) - 1 and msg.get("options"):
                    st.markdown("**Quick options:**")
                    cols = st.columns(min(len(msg["options"]), 3))
                    for j, option in enumerate(msg["options"][:3]):
                        with cols[j % 3]:
                            if st.button(option, key=f"option_{i}_{j}"):
                                send_message(option)
                                st.rerun()
        
        # Show typing indicator
        if st.session_state.is_typing:
            st.markdown("""
            <div class="bot-message">
                <i>🤖 Typing...</i>
            </div>
            """, unsafe_allow_html=True)

def get_chat_status():
    """Get current chat session status"""
    if st.session_state.chat_session_id:
        response = make_chat_request(f"chat/status/{st.session_state.chat_session_id}", method="GET")
        return response
    return None

def export_results():
    """Export chat results"""
    if st.session_state.chat_session_id:
        response = make_chat_request(f"chat/export/{st.session_state.chat_session_id}", method="GET")
        return response
    return None

def reset_chat():
    """Reset the chat session"""
    # Reset session state locally since there's no API reset endpoint
    st.session_state.chat_session_id = None
    st.session_state.chat_history = []
    st.session_state.current_stage = "introduction"
    st.session_state.is_typing = False

# Main Interface
def main():
    st.title("🤖 AI Research Agent - Chat Interface")
    st.markdown("*Your conversational guide through the research workflow*")
    
    # Sidebar with session info and controls
    with st.sidebar:
        st.header("Chat Session")
        
        # Session controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆕 New Chat", help="Start a new chat session"):
                if start_chat_session():
                    st.rerun()
        
        with col2:
            if st.button("🔄 Reset", help="Reset current chat"):
                reset_chat()
                st.rerun()
        
        # Session status
        if st.session_state.chat_session_id:
            status = get_chat_status()
            if status:
                st.markdown("### Session Info")
                st.write(f"**Session ID:** `{st.session_state.chat_session_id[:8]}...`")
                st.write(f"**Current Stage:** {status['stage'].replace('_', ' ').title()}")
                st.write(f"**Messages:** {len(st.session_state.chat_history)}")
                
                # Progress indicator
                stages = ["introduction", "project_setup", "research_questions", "sub_question_analysis", "data_gaps", "literature_search", "completed"]
                current_index = stages.index(status['stage']) if status['stage'] in stages else 0
                progress = (current_index + 1) / len(stages)
                st.progress(progress)
                st.caption(f"Step {current_index + 1} of {len(stages)}")
        
        # Export option
        if st.session_state.current_stage == "completed":
            st.markdown("### Export Results")
            if st.button("📥 Export Research Framework"):
                export_data = export_results()
                if export_data:
                    st.download_button(
                        label="Download JSON",
                        data=json.dumps(export_data, indent=2),
                        file_name=f"research_framework_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
        
        # Help section
        st.markdown("### Help")
        with st.expander("How to use"):
            st.markdown("""
            1. **Start** by clicking "New Chat" if this is your first time
            2. **Follow** the bot's guidance through each stage
            3. **Use** the quick option buttons or type your own responses
            4. **Ask questions** at any time for clarification
            5. **Export** your results when completed
            """)
        
        with st.expander("Stage Overview"):
            st.markdown("""
            **Stage 1:** Project Setup
            - Define your research topic
            
            **Stage 2:** Research Questions
            - Select main questions
            
            **Stage 3:** Sub-Question Analysis
            - Review data requirements
            
            **Stage 4:** Data Gaps
            - Identify missing data
            
            **Stage 5:** Literature Search
            - Find relevant sources
            """)
    
    # Main chat interface
    st.markdown("### Conversation")
    
    # Initialize chat if needed
    if not st.session_state.chat_session_id and not st.session_state.chat_history:
        st.info("👋 Welcome! Click 'New Chat' in the sidebar to start your research journey.")
        if st.button("🚀 Start Research Assistant"):
            if start_chat_session():
                st.rerun()
    else:
        # Display chat history
        chat_placeholder = st.empty()
        with chat_placeholder.container():
            display_chat_history()
        
        # Message input
        st.markdown("---")
        message_container = st.container()
        
        with message_container:
            # Use form to handle Enter key
            with st.form("chat_form", clear_on_submit=True):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    user_input = st.text_input(
                        "Type your message...",
                        placeholder="Ask a question or provide information...",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    send_button = st.form_submit_button("Send", use_container_width=True)
                
                if send_button and user_input.strip():
                    send_message(user_input.strip())
                    st.rerun()
        
        # Quick actions for different stages
        if st.session_state.current_stage == "project_setup":
            st.markdown("### Quick Setup")
            with st.expander("Use structured form"):
                with st.form("project_form"):
                    title = st.text_input("Research Title")
                    description = st.text_area("Description")
                    area_of_study = st.text_input("Area of Study (optional)")
                    geography = st.text_input("Geographic Focus (optional)")
                    
                    if st.form_submit_button("Submit Project Info"):
                        context = {
                            "structured_input": {
                                "title": title,
                                "description": description,
                                "area_of_study": area_of_study,
                                "geography": geography
                            }
                        }
                        send_message("I'm providing structured project information", context)
                        st.rerun()

if __name__ == "__main__":
    main()
