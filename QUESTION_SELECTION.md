# Question Selection Feature

This document explains the new question selection functionality that allows users to choose specific main questions with their sub-questions after generation.

## Overview

After generating multiple main questions (3-5) with their respective sub-questions, users can now:
1. Select which main questions they want to proceed with
2. Automatically include all sub-questions associated with selected main questions
3. Continue the workflow with only the selected questions

## API Endpoints

### 1. Generate Questions
**POST** `/generate-questions`

Generates 3-5 main research questions with 3-5 sub-questions each.

```json
{
  "title": "Your research title",
  "description": "Research description",
  "area_of_study": "Field of study",
  "geography": "Geographic scope",
  "custom_sub_questions": ["Optional custom questions"]
}
```

**Response includes:**
- `session_id`: For subsequent API calls
- `main_questions`: Array of main questions with their sub-questions
- Each main question includes its `id` for selection

### 2. Select Questions
**POST** `/select-questions`

Select specific main questions to continue with in the workflow.

```json
{
  "session_id": "your-session-id",
  "selected_main_question_ids": ["main-q-id-1", "main-q-id-2"]
}
```

**Response includes:**
- Selected main questions with their associated sub-questions
- Confirmation message

### 3. Analyze Sub-questions
**POST** `/analyze-subquestions`

Analyze sub-questions for specific main questions by their IDs.

```json
{
  "session_id": "your-session-id",
  "main_question_ids": ["main-q-id-1", "main-q-id-2"]
}
```

**Response includes:**
- Array of sub-question mappings with data requirements and analysis approaches
- Only for sub-questions linked to the specified main question IDs

### 4. Analyze Selected Sub-questions
**POST** `/analyze-selected-subquestions`

Analyze sub-questions for previously selected main questions.

```json
{
  "session_id": "your-session-id"
}
```

**Response includes:**
- Analysis for all sub-questions of previously selected main questions

### 5. Get Selected Questions
**GET** `/selected-questions/{session_id}`

Retrieve the current list of selected main questions and their sub-questions.

**Response includes:**
- `selected_main_questions`: Array of selected questions with sub-questions
- `total_selected`: Count of selected main questions

## Workflow Integration

### Standard Workflow
1. **Generate Questions** → Multiple main questions with sub-questions
2. **Select Questions** → Choose specific main questions by ID
3. **Analyze Sub-questions** → Analyze sub-questions for chosen main questions by ID
4. **Identify Data Gaps** → For analyzed sub-questions only
5. **Search Literature** → For analyzed sub-questions only

### Alternative Workflow
1. **Generate Questions** → Multiple main questions with sub-questions
2. **Analyze Sub-questions** → Directly analyze specific main questions by ID (skip selection step)
3. **Continue with workflow** → Process only the analyzed questions

### Supabase Integration

The system integrates with Supabase to:
- Persist research sessions
- Store question selections
- Enable session recovery

**Configuration:**
- Set `SUPABASE_URL` in your `.env` file
- Set `SUPABASE_CLIENT_KEY` in your `.env` file

### Database Schema

**research_sessions table:**
```sql
CREATE TABLE research_sessions (
  id SERIAL PRIMARY KEY,
  session_id TEXT UNIQUE NOT NULL,
  project_data JSONB,
  main_questions JSONB,
  sub_questions JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**question_selections table:**
```sql
CREATE TABLE question_selections (
  id SERIAL PRIMARY KEY,
  session_id TEXT NOT NULL,
  selected_main_question_ids TEXT[],
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (session_id) REFERENCES research_sessions(session_id)
);
```

## Example Usage

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Generate questions
project_data = {
    "title": "Climate Change Impact on Agriculture",
    "description": "Study agricultural impacts",
    "area_of_study": "Environmental Science",
    "geography": "Sub-Saharan Africa"
}

response = requests.post(f"{BASE_URL}/generate-questions", json=project_data)
result = response.json()
session_id = result["session_id"]
main_questions = result["main_questions"]

# 2. Select first 2 main questions
selected_ids = [mq["id"] for mq in main_questions[:2]]
selection_data = {
    "session_id": session_id,
    "selected_main_question_ids": selected_ids
}

response = requests.post(f"{BASE_URL}/select-questions", json=selection_data)
selection_result = response.json()

# 3. Continue with workflow using selected questions
# The subsequent endpoints will now work with only the selected questions
```

## Error Handling

- **404**: Session not found or expired
- **400**: Invalid main question IDs provided
- **400**: No questions generated yet
- **500**: Server error during selection process

## Session Management

The session now tracks:
- `questions_filtered`: Boolean indicating if selection was made
- `selected_main_question_ids`: Array of selected question IDs
- `selected_questions_count`: Count for quick reference

Use `/session/{session_id}` to check the current state and workflow progress.
