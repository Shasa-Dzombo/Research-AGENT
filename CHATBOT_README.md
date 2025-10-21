# AI Research Agent - Conversational Bot

## Overview

The AI Research Agent now includes a conversational bot interface that guides users through a 5-stage research workflow. The bot provides an intuitive, chat-based experience for research project setup and analysis.

## Features

### 5-Stage Conversational Workflow

1. **Introduction & Capabilities** 🤖
   - Introduces the bot and explains its capabilities
   - Provides overview of the research workflow

2. **Project Setup** 📋
   - Collects research title, description, area of study, and geographic focus
   - Supports both conversational and structured input

3. **Research Questions** ❓
   - Generates main research questions and sub-questions
   - Allows users to select relevant questions and add custom ones
   - User can select 2 main questions from generated options

4. **Sub-Question Analysis** 🔍
   - Provides detailed data requirements for each sub-question
   - Explains analysis approaches and methodologies
   - Allows users to ask for clarification on any requirement

5. **Data Gaps Identification** 📊
   - Identifies potential missing data and variables
   - Suggests alternative sources and approaches
   - Provides explanations for each identified gap

6. **Literature Search** 📚
   - Searches for relevant academic literature and resources
   - Provides curated list of papers and references
   - Completes the research framework

## API Endpoints

### Chat Session Management

```
POST /api/chatbot/chat/start
```
- Starts a new chat session
- Returns session ID and introduction message

```
POST /api/chatbot/chat/{session_id}/message
```
- Sends a message to the conversational agent
- Body: `{"message": "user message", "context": {...}}`
- Returns bot response with stage, options, and data

```
GET /api/chatbot/chat/{session_id}/status
```
- Gets current session status and progress
- Returns stage, user data, and timestamps

```
POST /api/chatbot/chat/{session_id}/reset
```
- Resets the conversation to start over
- Preserves session ID but clears conversation history

```
GET /api/chatbot/chat/{session_id}/export
```
- Exports complete research framework as JSON
- Includes all collected data and conversation history

```
DELETE /api/chatbot/chat/{session_id}
```
- Deletes a chat session and all associated data

### Request/Response Models

**ChatMessage**
```json
{
  "message": "string",
  "context": {
    "structured_input": {...},
    "additional_data": {...}
  }
}
```

**ChatResponse**
```json
{
  "message": "string",
  "stage": "string",
  "options": ["option1", "option2"],
  "data": {...},
  "action": "string",
  "session_id": "string"
}
```

## Streamlit Chat Interface

### Running the Chat Interface

```bash
# Start the API server
uvicorn main:app --reload --port 8000

# In another terminal, start the chat interface
streamlit run streamlit_chatbot.py --server.port 8502
```

Access the chat interface at: `http://localhost:8502`

### Features

- **Real-time conversation** with typing indicators
- **Quick option buttons** for common responses
- **Session management** with progress tracking
- **Structured forms** for project setup
- **Export functionality** for completed research frameworks
- **Stage progress indicator** showing workflow completion
- **Responsive design** for different screen sizes

## Usage Examples

### 1. Starting a Conversation

```python
import requests

# Start chat session
response = requests.post("http://localhost:8000/api/chatbot/chat/start")
session_data = response.json()
session_id = session_data["session_id"]

print(session_data["message"])  # Introduction message
```

### 2. Project Setup

```python
# Send project information
response = requests.post(
    f"http://localhost:8000/api/chatbot/chat/{session_id}/message",
    json={
        "message": "Title: Digital Health in Rural Areas, Description: Studying mobile health adoption in rural Kenya, Area: Public Health, Geography: Kenya"
    }
)

bot_response = response.json()
print(bot_response["message"])
```

### 3. Using Structured Input

```python
# Structured project setup
response = requests.post(
    f"http://localhost:8000/api/chatbot/chat/{session_id}/message",
    json={
        "message": "I'm providing structured information",
        "context": {
            "structured_input": {
                "title": "Digital Health Impact Study",
                "description": "Analyzing mobile health app effectiveness",
                "area_of_study": "Public Health",
                "geography": "Kenya"
            }
        }
    }
)
```

### 4. Question Selection

```python
# Select research questions
response = requests.post(
    f"http://localhost:8000/api/chatbot/chat/{session_id}/message",
    json={"message": "I select questions 1 and 2"}
)
```

### 5. Asking for Clarification

```python
# Ask about data requirements
response = requests.post(
    f"http://localhost:8000/api/chatbot/chat/{session_id}/message",
    json={"message": "What does demographic data mean in this context?"}
)
```

### 6. Exporting Results

```python
# Export completed research framework
response = requests.get(f"http://localhost:8000/api/chatbot/chat/{session_id}/export")
export_data = response.json()

# Save to file
with open("research_framework.json", "w") as f:
    json.dump(export_data, f, indent=2)
```

## Testing

Run the test script to verify functionality:

```bash
python test_chatbot.py
```

Choose option 1 for API endpoint testing or option 2 for full conversation flow testing.

## Integration with Existing System

The conversational bot integrates seamlessly with the existing research agent infrastructure:

- **Uses existing ResearchAssistant** for question generation and analysis
- **Leverages current literature search** utilities
- **Maintains compatibility** with existing API endpoints
- **Extends the workflow** without breaking existing functionality

## Session Management

- **Session persistence** across multiple interactions
- **Automatic session expiry** after 24 hours of inactivity
- **Conversation history** stored for each session
- **State management** for workflow progression
- **Error recovery** with graceful fallbacks

## Error Handling

- **API connection errors** with user-friendly messages
- **Invalid input handling** with guidance for correction
- **Session recovery** for interrupted conversations
- **Graceful degradation** when backend services are unavailable

## Customization

### Adding New Conversation Stages

1. Add new stage to `ConversationStage` enum
2. Implement handler method in `ConversationalAgent`
3. Add routing logic in `process_message`
4. Update API action handlers as needed

### Modifying Response Templates

Responses are generated in the handler methods and can be customized by modifying the message templates in `agents/conversational_agent.py`.

### Extending API Functionality

Add new endpoints to `app/chatbot_api.py` and include them in the router registration.

## Security Considerations

- **Session isolation** prevents cross-session data leakage
- **Input validation** on all user messages
- **Rate limiting** can be added for production use
- **CORS configuration** for web interface security

## Performance

- **Lightweight session storage** in memory (can be extended to Redis/database)
- **Efficient message processing** with minimal overhead
- **Asynchronous API endpoints** for better concurrency
- **Streamlined conversation flow** reduces unnecessary API calls

## Future Enhancements

- **Voice interface** integration
- **Multi-language support**
- **Advanced NLP** for better message understanding
- **Persistent session storage** with database backend
- **Real-time collaboration** features
- **Integration with external research databases**
