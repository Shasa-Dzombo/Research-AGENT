"""
Streamlit Interface for AI Research Agent
A user-friendly web interface to interact with the research workflow
"""

import streamlit as st
import requests
import json
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api"

# Initialize session state for systematic workflow
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 0
if 'project_created' not in st.session_state:
    st.session_state.project_created = False
if 'questions_generated' not in st.session_state:
    st.session_state.questions_generated = False
if 'questions_analyzed' not in st.session_state:
    st.session_state.questions_analyzed = False
if 'data_gaps_identified' not in st.session_state:
    st.session_state.data_gaps_identified = False
if 'literature_searched' not in st.session_state:
    st.session_state.literature_searched = False
if 'main_question_ids' not in st.session_state:
    st.session_state.main_question_ids = []
if 'questions_data' not in st.session_state:
    st.session_state.questions_data = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'data_gaps_results' not in st.session_state:
    st.session_state.data_gaps_results = None
if 'literature_results' not in st.session_state:
    st.session_state.literature_results = None

def make_api_request(endpoint: str, method: str = "POST", data: Dict = None) -> Dict:
    """Make API request with error handling"""
    try:
        url = f"{API_BASE_URL}/{endpoint}"
        
        if method == "POST":
            response = requests.post(url, json=data)
        else:
            response = requests.get(url)
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        if hasattr(e, 'response') and e.response:
            st.error(f"Response: {e.response.text}")
        return None

def navigate_to_tab(tab_index: int):
    """Navigate to a specific tab"""
    st.session_state.current_tab = tab_index
    st.rerun()

def create_navigation_buttons(current_step: int, total_steps: int = 5):
    """Create navigation buttons for workflow steps"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if current_step > 0:
            if st.button("⬅️ Previous Step", key=f"prev_{current_step}"):
                navigate_to_tab(current_step - 1)
    
    with col2:
        # Progress indicator
        progress = (current_step + 1) / total_steps
        st.progress(progress)
        st.caption(f"Step {current_step + 1} of {total_steps}")
    
    with col3:
        if current_step < total_steps - 1:
            # Check if current step is completed before allowing next
            can_proceed = False
            if current_step == 0 and st.session_state.project_created:
                can_proceed = True
            elif current_step == 1 and st.session_state.questions_analyzed:
                can_proceed = True
            elif current_step == 2 and st.session_state.data_gaps_identified:
                can_proceed = True
            elif current_step == 3 and st.session_state.literature_searched:
                can_proceed = True
            elif current_step == 4:
                can_proceed = True
            
            if can_proceed:
                if st.button("Next Step ➡️", key=f"next_{current_step}", type="primary"):
                    navigate_to_tab(current_step + 1)
            else:
                st.button("Complete Current Step First", key=f"next_disabled_{current_step}", disabled=True)

# Main App Layout
st.title("🔬 AI Research Agent")
st.markdown("*Systematic research workflow with complete API integration*")

# Sidebar - Workflow Status
with st.sidebar:
    st.header("📋 Systematic Workflow")
    
    # Status indicators
    if st.session_state.session_id:
        st.success(f"✅ Session: {st.session_state.session_id[:8]}...")
    else:
        st.warning("⏳ No Active Session")
    
    st.markdown("---")
    
    # Workflow steps
    steps = [
        ("🎯 Project Setup", st.session_state.project_created),
        ("❓ Generate Questions", st.session_state.questions_generated),
        ("📋 Analyze Sub-questions", st.session_state.questions_analyzed),
        ("⚠️ Identify Data Gaps", st.session_state.data_gaps_identified),
        ("📚 Search Literature", st.session_state.literature_searched)
    ]
    
    for step_name, completed in steps:
        if completed:
            st.success(f"{step_name} ✅")
        else:
            st.info(f"{step_name} ⏳")
    
    st.markdown("---")
    
    # Quick actions
    if st.button("🔄 Reset Workflow"):
        for key in ['session_id', 'project_created', 'questions_generated', 'questions_analyzed', 'data_gaps_identified', 'literature_searched', 'main_question_ids', 'questions_data', 'analysis_results', 'data_gaps_results', 'literature_results']:
            if key == 'session_id':
                st.session_state[key] = None
            elif key in ['main_question_ids']:
                st.session_state[key] = []
            elif key in ['questions_data', 'analysis_results', 'data_gaps_results', 'literature_results']:
                st.session_state[key] = None
            else:
                st.session_state[key] = False
        st.rerun()

# Main Content Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Project Setup", "❓ Research Questions", "📋 Sub-question Analysis", "⚠️ Data Gaps", "📚 Literature Search"])

# Tab 1: Project Setup
with tab1:
    st.header("🎯 Project Information")
    st.markdown("**Step 1:** Define your research project to start the systematic workflow")
    
    with st.form("project_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("📝 Project Title *", 
                                placeholder="e.g., Climate Change Impact on Agriculture")
            description = st.text_area("📋 Project Description *", 
                                     placeholder="Detailed description of your research focus...")
        
        with col2:
            area_of_study = st.text_input("🎓 Area of Study", 
                                        placeholder="e.g., Environmental Science")
            geography = st.text_input("🌍 Geographic Focus", 
                                    placeholder="e.g., Sub-Saharan Africa")
        
        submitted = st.form_submit_button("🚀 Start Research Workflow", type="primary")
        
        if submitted:
            if not title or not description:
                st.error("Please fill in all required fields (*)")
            else:
                with st.spinner("Creating research project and generating questions..."):
                    project_data = {
                        "title": title,
                        "description": description,
                        "area_of_study": area_of_study,
                        "geography": geography
                    }
                    
                    result = make_api_request("generate-questions", data=project_data)
                    
                    if result:
                        st.session_state.session_id = result.get("session_id")
                        st.session_state.project_created = True
                        st.session_state.questions_generated = True
                        st.session_state.questions_data = result
                        
                        # Extract main question IDs for later use
                        main_questions = result.get("main_questions", [])
                        st.session_state.main_question_ids = [q.get("id") for q in main_questions if q.get("id")]
                        
                        st.success("✅ Project created and questions generated!")
                        st.info("**Next Step:** Go to Research Questions tab")
                        st.rerun()

# Tab 2: Research Questions  
with tab2:
    st.header("❓ Research Questions")
    st.markdown("**Step 2:** Select main questions (max 2) and analyze sub-questions")
    
    if not st.session_state.session_id:
        st.warning("⚠️ Please create a project first in the Project Setup tab")
    else:
        st.success("✅ Questions generated! Select up to 2 main questions to analyze.")
        
        # Display generated questions for selection
        if st.session_state.questions_data:
            st.subheader("🎯 Select Main Questions to Analyze")
            st.info("💡 **Select maximum 2 questions** for focused, high-quality analysis")
            
            main_questions = st.session_state.questions_data.get("main_questions", [])
            selected_question_ids = []
            
            # Create checkboxes for each main question
            for i, mq in enumerate(main_questions, 1):
                question_text = mq.get('text', 'Unknown')
                question_id = mq.get('id', 'Unknown')
                
                # Display question with preview of sub-questions
                with st.container():
                    col1, col2 = st.columns([1, 4])
                    
                    with col1:
                        selected = st.checkbox(
                            f"Q{i}",
                            key=f"select_main_{question_id}",
                            help=f"Select Question {i}"
                        )
                        if selected:
                            selected_question_ids.append(question_id)
                    
                    with col2:
                        st.write(f"**Question {i}:** {question_text}")
                        
                        # Show sub-questions preview
                        sub_questions = mq.get("sub_questions", [])
                        if sub_questions:
                            with st.expander(f"📋 View {len(sub_questions)} sub-questions"):
                                for j, sq in enumerate(sub_questions, 1):
                                    st.write(f"  {i}.{j}) {sq.get('text', 'Unknown')}")
                
                st.divider()
            
            # Validation and analysis
            if len(selected_question_ids) > 2:
                st.error("❌ **Error: You can select maximum 2 questions.** Please uncheck some questions.")
                st.warning(f"Currently selected: {len(selected_question_ids)} questions")
            elif len(selected_question_ids) == 0:
                st.info("👆 Please select at least 1 main question to proceed with analysis.")
            else:
                st.success(f"✅ Selected {len(selected_question_ids)} question(s) for analysis")
                
                # Show selected questions summary
                with st.expander("📝 Selected Questions Summary", expanded=True):
                    for q_id in selected_question_ids:
                        selected_q = next((q for q in main_questions if q.get('id') == q_id), None)
                        if selected_q:
                            st.write(f"✓ **{selected_q.get('text', 'Unknown')}**")
                
                # Analysis button (only enabled when 1-2 questions selected)
                if st.button("🔍 Analyze Selected Sub-Questions", type="primary", help="Analyze sub-questions for selected main questions"):
                    with st.spinner("Analyzing sub-questions and mapping data requirements..."):
                        analyze_data = {
                            "session_id": st.session_state.session_id,
                            "main_question_ids": selected_question_ids
                        }
                        result = make_api_request("analyze-subquestions", data=analyze_data)
                        
                        if result:
                            st.session_state.questions_analyzed = True
                            st.session_state.analysis_results = result  # Store the results
                            st.success("✅ Sub-questions analyzed successfully!")
                            
                            # Display analysis results preview
                            st.subheader("📋 Analysis Results Preview")
                            st.info(f"✅ Successfully analyzed {len(result)} sub-questions")
                            
                            for i, mapping in enumerate(result[:3], 1):  # Show first 3 as preview
                                with st.expander(f"📝 Sub-question {i}: {mapping.get('sub_question', 'Unknown')[:50]}...", expanded=False):
                                    st.write(f"**Data Requirements:** {mapping.get('data_requirements', 'None specified')[:100]}...")
                                    st.write(f"**Analysis Approach:** {mapping.get('analysis_approach', 'None specified')[:100]}...")
                            
                            if len(result) > 3:
                                st.info(f"+ {len(result) - 3} more sub-questions analyzed. View full details in the Sub-question Analysis tab.")
                            
                            st.info("**Next Step:** Go to Sub-question Analysis tab to see complete results")
                            st.rerun()
        else:
            st.warning("No questions data found. Please regenerate questions in Project Setup.")

# Tab 3: Sub-question Analysis
with tab3:
    st.header("📋 Sub-question Analysis")
    st.markdown("**Step 3:** Review analysis results and identify data gaps")
    
    if not st.session_state.questions_analyzed:
        st.warning("⚠️ Please analyze sub-questions first in the Research Questions tab")
    else:
        st.success("✅ Sub-questions analyzed! Review the analysis below.")
        
        # Display stored analysis results
        if st.session_state.analysis_results:
            st.subheader("📊 Analysis Results Overview")
            st.info(f"📈 **Total Sub-questions Analyzed:** {len(st.session_state.analysis_results)}")
            
            for i, mapping in enumerate(st.session_state.analysis_results, 1):
                with st.expander(f"📝 Sub-question {i}: {mapping.get('sub_question', 'Unknown')}", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📋 Data Requirements:**")
                        st.write(mapping.get('data_requirements', 'None specified'))
                    
                    with col2:
                        st.markdown("**🔬 Analysis Approach:**")
                        st.write(mapping.get('analysis_approach', 'None specified'))
                    
                    # Add mapping ID if available
                    if mapping.get('sub_question_id'):
                        st.caption(f"Sub-question ID: {mapping.get('sub_question_id')}")
        
        st.divider()
        
        if st.button("⚠️ Identify Data Gaps", type="primary"):
            with st.spinner("Identifying data gaps and missing requirements..."):
                gap_data = {"session_id": st.session_state.session_id}
                result = make_api_request("identify-data-gaps", data=gap_data)
                
                if result:
                    st.session_state.data_gaps_identified = True
                    st.session_state.data_gaps_results = result  # Store the results
                    st.success("✅ Data gaps identified!")
                    
                    # Display data gaps
                    st.subheader("⚠️ Identified Data Gaps")
                    if isinstance(result, list) and result:
                        for gap in result:
                            with st.container():
                                st.warning(f"**Missing Variable:** {gap.get('missing_variable', 'Unknown')}")
                                st.write(f"**Description:** {gap.get('gap_description', 'No description')}")
                                st.write(f"**Suggested Sources:** {gap.get('suggested_sources', 'No suggestions')}")
                                st.divider()
                    else:
                        st.info("No significant data gaps identified.")
                    
                    st.info("**Next Step:** Go to Data Gaps tab")
                    st.rerun()

# Tab 4: Data Gaps
with tab4:
    st.header("⚠️ Data Gap Analysis")
    st.markdown("**Step 4:** Review data gaps and search academic literature")
    
    if not st.session_state.data_gaps_identified:
        st.warning("⚠️ Please identify data gaps first in the Sub-question Analysis tab")
    else:
        st.success("✅ Data gaps identified! Review the gaps below.")
        
        # Display stored data gaps results
        if st.session_state.data_gaps_results:
            st.subheader("📊 Data Gaps Overview")
            
            if isinstance(st.session_state.data_gaps_results, list) and st.session_state.data_gaps_results:
                st.error(f"⚠️ **Total Data Gaps Found:** {len(st.session_state.data_gaps_results)}")
                
                for i, gap in enumerate(st.session_state.data_gaps_results, 1):
                    with st.expander(f"⚠️ Data Gap {i}: {gap.get('missing_variable', 'Unknown')}", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**📝 Gap Description:**")
                            st.write(gap.get('gap_description', 'No description'))
                        
                        with col2:
                            st.markdown("**💡 Suggested Sources:**")
                            st.write(gap.get('suggested_sources', 'No suggestions'))
                        
                        # Add gap metadata if available
                        if gap.get('sub_question_id'):
                            st.caption(f"Related to sub-question: {gap.get('sub_question_id')}")
                        
                        # Severity indicator
                        if 'critical' in gap.get('gap_description', '').lower():
                            st.error("🚨 Critical Gap")
                        elif 'important' in gap.get('gap_description', '').lower():
                            st.warning("⚠️ Important Gap")
                        else:
                            st.info("ℹ️ Minor Gap")
            else:
                st.success("✅ **No significant data gaps identified!**")
                st.info("Your research project has comprehensive data coverage.")
        
        st.divider()
        
        if st.button("📚 Search Academic Literature", type="primary"):
            with st.spinner("Searching academic literature with hierarchical ranking... This may take a moment."):
                search_data = {"session_id": st.session_state.session_id}
                result = make_api_request("search-literature-analyzed", data=search_data)
                
                if result:
                    st.session_state.literature_searched = True
                    st.session_state.literature_results = result  # Store the results
                    st.success("✅ Literature search completed with hierarchical confidence ranking!")
                    st.info("**Next Step:** Go to Literature Search tab to view results")
                    st.rerun()

# Tab 5: Literature Search
with tab5:
    st.header("📚 Academic Literature Search")
    st.markdown("**Step 5:** Review hierarchically ranked literature results")
    
    if not st.session_state.literature_searched:
        st.warning("⚠️ Please complete literature search first in the Data Gaps tab")
    else:
        st.success("✅ Literature search completed with hierarchical ranking!")
        
        # Display stored literature results
        if st.session_state.literature_results:
            st.subheader("📊 Literature Search Results")
            
            # Check if results contain literature data
            if isinstance(st.session_state.literature_results, dict):
                literature_data = st.session_state.literature_results.get('literature', {})
                
                if literature_data:
                    st.info(f"📈 **Literature found for {len(literature_data)} sub-questions**")
                    
                    for sub_q_id, papers in literature_data.items():
                        if papers:
                            st.markdown(f"### 📖 Literature for Sub-question: {sub_q_id}")
                            
                            # Sort papers by relevance to create hierarchy
                            sorted_papers = sorted(papers, key=lambda x: x.get('relevance', 0), reverse=True)
                            
                            # Display primary paper (highest relevance)
                            if sorted_papers:
                                primary_paper = sorted_papers[0]
                                
                                st.markdown("#### 🥇 Primary Reference (Highest Confidence)")
                                with st.container():
                                    col1, col2 = st.columns([3, 1])
                                    
                                    with col1:
                                        st.markdown(f"**{primary_paper.get('title', 'Unknown Title')}**")
                                        
                                        authors = primary_paper.get('authors', [])
                                        if authors:
                                            st.write(f"*Authors: {', '.join(authors)}*")
                                        
                                        year = primary_paper.get('year', 'Unknown')
                                        venue = primary_paper.get('venue', 'Unknown')
                                        st.write(f"*Year: {year} | Venue: {venue}*")
                                        
                                        abstract = primary_paper.get('abstract', '')
                                        if abstract:
                                            with st.expander("📄 Abstract"):
                                                st.write(abstract)
                                    
                                    with col2:
                                        relevance = primary_paper.get('relevance', 0)
                                        st.metric("Relevance Score", f"{relevance:.3f}")
                                        
                                        confidence_tier = primary_paper.get('confidence_tier', 'Unknown')
                                        st.metric("Confidence", confidence_tier.title())
                                        
                                        url = primary_paper.get('url', '')
                                        if url:
                                            st.link_button("🔗 Read Paper", url)
                                
                                # Display secondary papers
                                if len(sorted_papers) > 1:
                                    st.markdown("#### 🥈 Secondary References")
                                    
                                    for i, paper in enumerate(sorted_papers[1:], 1):
                                        with st.expander(f"Reference #{i}: {paper.get('title', 'Unknown')[:60]}..."):
                                            col1, col2 = st.columns([3, 1])
                                            
                                            with col1:
                                                authors = paper.get('authors', [])
                                                if authors:
                                                    st.write(f"**Authors:** {', '.join(authors)}")
                                                
                                                year = paper.get('year', 'Unknown')
                                                venue = paper.get('venue', 'Unknown')
                                                st.write(f"**Year:** {year} | **Venue:** {venue}")
                                                
                                                abstract = paper.get('abstract', '')
                                                if abstract:
                                                    st.write(f"**Abstract:** {abstract[:200]}...")
                                            
                                            with col2:
                                                relevance = paper.get('relevance', 0)
                                                st.metric("Score", f"{relevance:.3f}")
                                                
                                                confidence_tier = paper.get('confidence_tier', 'Unknown')
                                                st.write(f"**Tier:** {confidence_tier.title()}")
                                                
                                                url = paper.get('url', '')
                                                if url:
                                                    st.link_button("🔗 View", url)
                            
                            st.divider()
                else:
                    st.info("No literature results found in the session data.")
            else:
                st.info("Literature results are not in the expected format.")
        
        # Literature Hierarchy Information
        st.markdown("### � Literature Hierarchy System")
        st.info("Papers are ranked by confidence using our enhanced scoring algorithm:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🥇 Primary References**")
            st.markdown("- Highest confidence scores (≥0.8)")
            st.markdown("- Most relevant to research questions")
            st.markdown("- Best semantic similarity match")
            
        with col2:
            st.markdown("**🥈 Secondary References**")
            st.markdown("- Supporting evidence papers")
            st.markdown("- Ranked by descending relevance")
            st.markdown("- Citation impact weighted")
        
        # Export options
        st.markdown("### 💾 Export Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Export JSON Results"):
                export_data = {
                    "session_id": st.session_state.session_id,
                    "workflow_completed": True,
                    "timestamp": datetime.now().isoformat(),
                    "analysis_results": st.session_state.analysis_results,
                    "data_gaps": st.session_state.data_gaps_results,
                    "literature": st.session_state.literature_results
                }
                st.download_button(
                    label="⬇️ Download JSON",
                    data=json.dumps(export_data, indent=2, default=str),
                    file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📊 Export CSV Summary"):
                # Create comprehensive summary
                summary_data = {
                    "Session_ID": [st.session_state.session_id],
                    "Timestamp": [datetime.now().isoformat()],
                    "Status": ["Completed"],
                    "Sub_Questions_Analyzed": [len(st.session_state.analysis_results) if st.session_state.analysis_results else 0],
                    "Data_Gaps_Found": [len(st.session_state.data_gaps_results) if st.session_state.data_gaps_results else 0],
                    "Literature_Sources": [len(st.session_state.literature_results.get('literature', {})) if st.session_state.literature_results else 0]
                }
                df = pd.DataFrame(summary_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv,
                    file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col3:
            if st.button("📋 Generate Report"):
                st.markdown("#### 📋 Complete Workflow Summary")
                st.markdown(f"**Session:** `{st.session_state.session_id}`")
                st.markdown(f"**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown("**Status:** ✅ All 5 systematic steps completed")
                
                # Summary statistics
                if st.session_state.analysis_results:
                    st.markdown(f"- **Sub-questions Analyzed:** {len(st.session_state.analysis_results)}")
                if st.session_state.data_gaps_results:
                    st.markdown(f"- **Data Gaps Identified:** {len(st.session_state.data_gaps_results)}")
                if st.session_state.literature_results:
                    lit_count = len(st.session_state.literature_results.get('literature', {}))
                    st.markdown(f"- **Literature Sources Found:** {lit_count}")
                
                st.markdown("**Workflow Quality:** ✅ Real academic sources with hierarchical ranking")

# Footer
st.markdown("---")
st.markdown("**🔬 Systematic Research Workflow:** *generate-questions → analyze-subquestions → identify-data-gaps → search-literature-analyzed*")
st.markdown("*✅ Complete API Integration | 📊 Hierarchical Literature Ranking | 🎯 Real Academic Sources*")

