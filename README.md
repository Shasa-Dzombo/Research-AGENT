# AI Research Agent

A sophisticated AI-powered research assistant that provides intelligent research question generation, lite## 🔗 API Endpoints

### New: Conversational Bot API

- **POST** `/api/chatbot/chat/start` - Start new chat session
- **POST** `/api/chatbot/chat/{session_id}/message` - Send message to bot
- **GET** `/api/chatbot/chat/{session_id}/status` - Get conversation status
- **POST** `/api/chatbot/chat/{session_id}/reset` - Reset conversation
- **GET** `/api/chatbot/chat/{session_id}/export` - Export research framework
- **DELETE** `/api/chatbot/chat/{session_id}` - Delete chat session

### Traditional Session-Based Workflow

- **POST** `/api/generate-questions` - Create session and generate research questions
- **POST** `/api/analyze-subquestions` - Map sub-questions to data requirements
- **POST** `/api/identify-data-gaps` - Identify missing data and suggest sources
- **POST** `/api/search-literature` - Search academic literature for sub-questions
- **GET** `/api/session/{session_id}` - Get current session state and progress

### Utility Endpoints

- **GET** `/` - Welcome message and API information
- **GET** `/health` - Health check endpoint
- **POST** `/api/literature/search` - Direct literature search without session
- **POST** `/api/complete-analysis` - Complete workflow in single call
- **GET** `/api/project-templates` - Sample project templatesd data gap analysis through both REST API and conversational chat interfaces.

## 🚀 Features

### Core Research Capabilities
- **Session-Based Workflow**: Maintain research context across multiple API calls
- **Research Question Generation**: Generate main questions and related sub-questions
- **Data Requirements Analysis**: Map sub-questions to specific data needs and analytical approaches
- **Data Gap Identification**: Automatically identify missing variables and suggest data sources
- **Literature Search**: Search across multiple academic databases (Semantic Scholar, CrossRef)

### New: Conversational Bot Interface 🤖
- **5-Stage Guided Workflow**: Interactive chat-based research assistant
- **Natural Language Processing**: Understand and respond to user queries conversationally
- **Real-time Guidance**: Step-by-step assistance through the research process
- **Streamlit Chat Interface**: User-friendly web interface for conversations
- **Export Functionality**: Download complete research frameworks as JSON

### Technical Features
- **Modular Architecture**: Clean, maintainable codebase with separation of concerns
- **Google Gemini LLM Integration**: Advanced AI for research assistance
- **Multiple Interface Options**: REST API, Streamlit dashboard, and conversational chat
- **Docker Support**: Easy deployment and scaling

## 🎯 Quick Start

### Option 1: Conversational Chat Interface (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Launch both API and chatbot
python launch.py
# Choose option 1 for chatbot interface

# Access at http://localhost:8502
```

### Option 2: Traditional Workflow Interface

```bash
# Launch main Streamlit interface
python launch.py
# Choose option 2 for main interface

# Access at http://localhost:8501
```

### Option 3: API Only

```bash
# Start API server
python launch.py
# Choose option 4 for API only

# Access docs at http://localhost:8000/docs
```

## 📁 Project Structure

```
├── main.py                          # Application entry point
├── launch.py                        # Easy launcher for all services
├── streamlit_chatbot.py             # NEW: Conversational chat interface
├── test_chatbot.py                  # NEW: Chatbot testing script
├── app/
│   ├── app.py                      # FastAPI factory with middleware
│   ├── api.py                      # REST endpoints with session management
│   └── chatbot_api.py              # NEW: Chatbot API endpoints
├── agents/
│   ├── research_assistant.py       # High-level orchestration
│   └── conversational_agent.py     # NEW: Conversational bot logic
├── agent_graph/
│   ├── graph.py                    # StateGraph workflow definition
│   └── nodes/
│       └── research_nodes.py       # Individual workflow nodes
├── state/
│   └── state.py                    # AgentState definitions
├── model/
│   └── models.py                   # Pydantic request/response models
├── config/
│   ├── config.py                   # Application settings
│   └── llm_factory.py             # LLM configuration factory
├── prompts/
│   └── research_prompts.py         # LLM prompt templates
├── utils/
│   ├── parser_utils.py             # Response parsing utilities
│   └── research_utils.py           # Literature search utilities
├── tests/
│   ├── start_api.py                # API startup script
│   └── test_api.py                 # Comprehensive API tests
├── docker-compose.yml              # Docker orchestration
├── Dockerfile                      # Container definition
├── CHATBOT_README.md               # NEW: Detailed chatbot documentation
└── requirements.txt                # Python dependencies
```

## 🤖 Conversational Workflow (5 Stages)

The new conversational bot guides users through a structured research workflow:

### Stage 1: Introduction & Project Setup �
- Bot introduces capabilities and workflow
- User provides research title, description, area of study, geographic focus
- Supports both natural language and structured input

### Stage 2: Research Questions ❓
- AI generates 2 main research questions with sub-questions
- User selects most relevant questions
- Option to add custom questions

### Stage 3: Sub-Question Analysis 🔍
- Detailed analysis of data requirements for each sub-question
- Explanation of analysis approaches and methodologies
- Interactive Q&A for clarification

### Stage 4: Data Gaps Identification 📊
- Automatic identification of potential missing data
- Suggested alternative sources and approaches
- Gap-specific explanations and solutions

### Stage 5: Literature Search 📚
- Relevant academic literature and resources
- Curated list of papers and references
- Complete research framework ready for export

## �🔗 API Endpoints

### Traditional Session-Based Workflow

- **POST** `/api/generate-questions` - Create session and generate research questions
- **POST** `/api/analyze-subquestions` - Map sub-questions to data requirements
- **POST** `/api/identify-data-gaps` - Identify missing data and suggest sources
- **POST** `/api/search-literature` - Search academic literature for sub-questions
- **GET** `/api/session/{session_id}` - Get current session state and progress

### Utility Endpoints

- **GET** `/` - Welcome message and API information
- **GET** `/health` - Health check endpoint
- **POST** `/api/literature/search` - Direct literature search without session
- **POST** `/api/complete-analysis` - Complete workflow in single call
- **GET** `/api/project-templates` - Sample project templates

## 🛠️ Quick Start

### Prerequisites

- Python 3.8+
- Google API Key (for Gemini LLM)

### Local Development

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd Research
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   Create a `.env` file:
   ```env
   # Google API Key (required for LLM functionality)
   GOOGLE_API_KEY=your_google_api_key_here

   # Server Configuration
   HOST=localhost
   PORT=8000
   RELOAD=True
   DEBUG=False

   # Session Management
   SESSION_EXPIRY_HOURS=24

   # Literature Search Settings
   DEFAULT_SEARCH_LIMIT=10
   MAX_SEARCH_LIMIT=50
   ```

3. **Start the Server**:
   ```bash
   python main.py
   ```

4. **Access API Documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Development

1. **Environment Setup**:
   Create `.env` file with your Google API key

2. **Build and Run**:
   ```bash
   docker-compose up -d
   ```

3. **Stop Container**:
   ```bash
   docker-compose down
   ```

4. **Access API**: http://localhost:8000/docs

## 📚 Usage Examples

### Session-Based Research Workflow

```python
import requests

base_url = "http://localhost:8000"

# Step 1: Generate research questions and create session
response = requests.post(f"{base_url}/api/generate-questions", json={
    "title": "Climate Change Impact on Health in East Africa",
    "description": "Researching climate change effects on public health",
    "area_of_study": "Public Health",
    "geography": "East Africa",
    "custom_sub_questions": [
        "How do heat waves affect maternal health outcomes?"
    ]
})
data = response.json()
session_id = data["session_id"]

# Step 2: Analyze sub-questions for data requirements
response = requests.post(f"{base_url}/api/analyze-subquestions", 
                        json={"session_id": session_id})
mappings = response.json()

# Step 3: Identify data gaps
response = requests.post(f"{base_url}/api/identify-data-gaps", 
                        json={"session_id": session_id})
gaps = response.json()

# Step 4: Search relevant literature
response = requests.post(f"{base_url}/api/search-literature", 
                        json={"session_id": session_id})
literature = response.json()

# Check session status
response = requests.get(f"{base_url}/api/session/{session_id}")
status = response.json()
```

### Complete Analysis (Single Call)

```python
response = requests.post(f"{base_url}/api/complete-analysis", json={
    "title": "Urban Air Quality and Respiratory Health",
    "description": "Impact of air pollution on respiratory diseases",
    "area_of_study": "Environmental Health",
    "geography": "Sub-Saharan Africa"
})
complete_analysis = response.json()
```

### Direct Literature Search

```python
response = requests.post(f"{base_url}/api/literature/search", json={
    "query": "climate change health africa",
    "limit": 10
})
literature_results = response.json()
```

## 🏗️ Architecture

### Core Components

- **FastAPI Application**: Modern, fast web framework with automatic API documentation
- **LangGraph Workflow**: Stateful multi-step research process using StateGraph
- **Gemini LLM Integration**: Advanced language model for intelligent question generation
- **Multi-Database Search**: Semantic Scholar and CrossRef integration
- **Session Management**: Persistent workflow state across API calls

### Key Features

- **Modular Design**: Clean separation of concerns across modules
- **Type Safety**: Full Pydantic model validation throughout
- **Error Handling**: Comprehensive error responses and logging
- **Scalable**: Docker-ready with configurable settings
- **Testable**: Comprehensive test suite included

## 🔧 Configuration

### Environment Variables

All configuration is managed through environment variables. Create a `.env` file with:

```env
# Google API Key (required for LLM functionality)
GOOGLE_API_KEY=your_google_api_key_here

# Server Configuration
HOST=localhost                    # Server host (use 0.0.0.0 for Docker)
PORT=8000                        # Server port
RELOAD=True                      # Enable auto-reload for development
DEBUG=False                      # Enable debug mode

# Session Management
SESSION_EXPIRY_HOURS=24          # Session expiration time in hours

# Literature Search Settings
DEFAULT_SEARCH_LIMIT=10          # Default number of papers to return
MAX_SEARCH_LIMIT=50             # Maximum allowed search limit
```

**Docker Configuration**: When running with Docker, the following environment variables are automatically set:
- `HOST=0.0.0.0` (for container networking)
- `RELOAD=False` (disabled in production containers)

### Application Settings

Configure in `config/config.py`:
- Session expiry time
- Search result limits
- API timeouts
- Logging levels

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run API tests
python tests/test_api.py

# Start test server
python tests/start_api.py
```

## 📄 Documentation

- **API Documentation**: Available at `/docs` (Swagger UI) and `/redoc`
- **Architecture Guide**: See `REFACTORING_SUMMARY.md`
- **Cleanup Guide**: See `CLEANUP_SUMMARY.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📜 License

This project is part of the APHRC AI Models repository for research assistance and analysis.