#!/usr/bin/env python3
"""
Streamlit Web Interface for RTM AI Agent
Provides a user-friendly web interface for uploading Excel files and generating RTMs
with dynamic sheet selection and comprehensive analysis
"""

import streamlit as st
import asyncio
import os
import tempfile
from pathlib import Path
import time
from datetime import datetime

from app.services.rtm_orchestrator import RTMOrchestrator

# Page configuration
st.set_page_config(
    page_title="RTM AI Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the orchestrator
@st.cache_resource
def get_orchestrator():
    return RTMOrchestrator()

def main():
    """Main Streamlit application"""
    
    # Header
    st.title("📊 RTM AI Agent - Dynamic Excel Analysis")
    st.markdown("**Automated Requirements Traceability Matrix Generator with AI-Powered Analysis**")
    st.markdown("*Supports any Excel structure - No hardcoded sheet names or columns*")
    st.markdown("---")
    
    # Initialize orchestrator
    orchestrator = get_orchestrator()
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # System status
        st.subheader("🟢 System Status")
        try:
            st.success("✅ Groq AI - Ready")
            st.info("🎯 Dynamic Excel Processing - Active")
            st.info("📊 3-Sheet RTM Output - Enabled")
        except Exception as e:
            st.error(f"❌ System Error: {str(e)}")
        
        st.markdown("---")
        
        # Processing Information
        st.subheader("ℹ️ How It Works")
        st.markdown("""
        **1. Upload** your Excel file
        **2. AI analyzes** all sheets dynamically
        **3. Select** focus sheet for detailed analysis
        **4. Generate** 3-sheet RTM:
        - Detailed focus analysis
        - Complete all-sheets RTM
        - Summary statistics
        """)
        
        with st.expander("🔑 Features"):
            st.markdown("""
            - **Dynamic Sheet Detection** - Works with any Excel structure
            - **Intelligent Column Recognition** - Auto-detects requirements
            - **Smart Chunking** - Respects API token limits
            - **Rate-Limited Processing** - Prevents API overload
            - **Groq AI Analysis** - High-quality requirement classification
            - **Fallback Analysis** - Rule-based backup if AI fails
            - **Original Data Preservation** - Maintains exact descriptions & IDs
            """)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📤 Upload Excel File")
        
        uploaded_file = st.file_uploader(
            "Choose an Excel file (.xlsx, .xls)",
            type=['xlsx', 'xls'],
            help="Upload any Excel file with requirements - sheet names and column structures will be detected automatically"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.info(f"📄 **File:** {uploaded_file.name}")
            st.info(f"📏 **Size:** {uploaded_file.size:,} bytes")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(uploaded_file.read())
                temp_file_path = tmp_file.name
            
            try:
                # Analyze sheets in the uploaded file
                with st.spinner("🔍 Analyzing Excel structure..."):
                    sheet_suggestions = orchestrator.get_available_sheets(temp_file_path)
                
                if sheet_suggestions:
                    st.success(f"✅ Found {len(sheet_suggestions)} sheets with requirements")
                    
                    # Display sheet analysis
                    with st.expander("📋 Sheet Analysis Results", expanded=True):
                        for i, suggestion in enumerate(sheet_suggestions):
                            confidence = suggestion['confidence_score']
                            sheet_name = suggestion['sheet_name']
                            total_rows = suggestion['total_rows']
                            reason = suggestion['recommendation_reason']
                            
                            # Color code by confidence
                            if confidence >= 0.8:
                                confidence_color = "🟢"
                            elif confidence >= 0.5:
                                confidence_color = "🟡"
                            else:
                                confidence_color = "🔴"
                            
                            st.markdown(f"""
                            **{confidence_color} {sheet_name}**  
                            Confidence: {confidence:.2f} | Rows: {total_rows} | {reason}
                            """)
                    
                    # Focus sheet selection
                    st.subheader("🎯 Select Focus Sheet for Detailed Analysis")
                    sheet_names = [s['sheet_name'] for s in sheet_suggestions]
                    
                    # Default to highest confidence sheet
                    default_index = 0  # First sheet (highest confidence due to sorting)
                    
                    focus_sheet = st.selectbox(
                        "Choose the sheet that should receive the most detailed AI analysis:",
                        options=sheet_names,
                        index=default_index,
                        help="This sheet will get deep, comprehensive analysis. Other sheets will get thorough but broader analysis."
                    )
                    
                    # Show focus sheet details
                    focus_sheet_info = next(s for s in sheet_suggestions if s['sheet_name'] == focus_sheet)
                    st.info(f"🎯 **Focus Sheet:** {focus_sheet} (Confidence: {focus_sheet_info['confidence_score']:.2f})")
                    
                    # Processing estimate
                    with st.spinner("⏱️ Calculating processing estimate..."):
                        estimate = orchestrator.get_processing_estimate(temp_file_path, focus_sheet)
                    
                    if 'error' not in estimate:
                        col_est1, col_est2, col_est3 = st.columns(3)
                        
                        with col_est1:
                            st.metric("Total Requirements", estimate['total_requirements'])
                        
                        with col_est2:
                            st.metric("Estimated Time", f"{estimate['estimated_processing_minutes']} min")
                        
                        with col_est3:
                            st.metric("API Calls", estimate['estimated_api_calls'])
                        
                        # Processing feasibility check
                        if estimate['processing_feasible']:
                            st.success("✅ Processing is feasible with current API limits")
                        else:
                            st.error("❌ Processing may exceed daily API limits - consider splitting the file")
                    
                    # Generate RTM button
                    st.markdown("---")
                    if st.button("🚀 Generate RTM with AI Analysis", type="primary", use_container_width=True):
                        process_excel_file(orchestrator, temp_file_path, focus_sheet, uploaded_file.name)
                
                else:
                    st.warning("⚠️ No sheets with identifiable requirements found in this Excel file.")
                    st.markdown("**Possible reasons:**")
                    st.markdown("- File contains only data tables without requirement-like content")
                    st.markdown("- Sheet structure is very different from typical requirements documents")
                    st.markdown("- File is corrupted or not a valid Excel file")
            
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
    
    with col2:
        st.header("ℹ️ About")
        st.markdown("""
        **RTM AI Agent** is a sophisticated system that automatically analyzes Excel requirements documents and generates professional Requirements Traceability Matrices.
        
        **🔥 New Features:**
        - **Universal Compatibility** - Works with any Excel structure
        - **Dynamic Column Detection** - No hardcoded assumptions
        - **Focus Sheet Selection** - You choose what gets priority
        - **3-Sheet Output** - Detailed, Complete, Summary
        - **Smart Rate Limiting** - Respects API constraints
        
        **🛠️ Technical Stack:**
        - Groq AI (llama-3.1-8b-instant)
        - Intelligent chunking with tiktoken
        - Dynamic Excel processing with openpyxl
        - Professional RTM formatting
        """)
        
        with st.expander("📊 Output Structure"):
            st.markdown("""
            **Sheet 1: Detailed Focus Analysis**
            - Deep AI analysis of your selected priority sheet
            - Comprehensive requirement classification
            - Detailed test case suggestions
            - Priority reasoning
            
            **Sheet 2: Complete RTM**
            - All requirements from all sheets
            - Maintains original Excel file order
            - Complete traceability matrix
            - Cross-sheet coverage
            
            **Sheet 3: Summary Statistics**
            - Requirements by type and priority
            - Sheet-by-sheet breakdown
            - Processing statistics
            - Quality metrics
            """)

def process_excel_file(orchestrator, file_path, focus_sheet, original_filename):
    """Process Excel file with real-time progress updates"""
    
    # Create progress containers
    progress_container = st.container()
    results_container = st.container()
    
    with progress_container:
        st.markdown("---")
        st.subheader("🔄 Processing Progress")
        
        overall_progress = st.progress(0)
        status_text = st.empty()
        phase_info = st.empty()
        
    try:
        # Phase 1: Validation
        status_text.text("✅ Validating focus sheet...")
        phase_info.info("🔍 Phase 1: Validation and Setup")
        overall_progress.progress(10)
        
        valid, message = orchestrator.validate_focus_sheet(file_path, focus_sheet)
        if not valid:
            st.error(f"❌ Validation failed: {message}")
            return
        
        st.success(f"✅ {message}")
        
        # Phase 2: Excel Processing
        status_text.text("📊 Loading and analyzing Excel structure...")
        phase_info.info("📋 Phase 2: Excel Structure Analysis")
        overall_progress.progress(20)
        time.sleep(1)  # Brief pause for UI update
        
        # Phase 3: AI Analysis
        status_text.text("🤖 Starting AI analysis with intelligent chunking...")
        phase_info.info("🧠 Phase 3: AI Analysis with Groq")
        overall_progress.progress(30)
        
        # Run the async processing
        start_time = datetime.now()
        
        with st.spinner("🚀 Processing with AI... This may take several minutes depending on file size"):
            rtm_output = asyncio.run(orchestrator.process_excel_to_rtm(file_path, focus_sheet))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Phase 4: RTM Generation
        status_text.text("📈 Generating comprehensive RTM output...")
        phase_info.info("📊 Phase 4: RTM Generation")
        overall_progress.progress(90)
        
        # Complete
        overall_progress.progress(100)
        status_text.text("🎉 Processing completed successfully!")
        phase_info.success("✅ All phases completed")
        
        # Display results
        with results_container:
            st.markdown("---")
            st.subheader("🎉 RTM Generated Successfully!")
            
            col_result1, col_result2, col_result3 = st.columns(3)
            
            with col_result1:
                st.metric("Total Requirements", rtm_output.requirements_count)
            
            with col_result2:
                st.metric("Processing Time", f"{processing_time:.1f}s")
            
            with col_result3:
                st.metric("Sheets Generated", "3")
            
            # File download
            st.markdown("### 📁 Download RTM")
            
            if os.path.exists(rtm_output.file_path):
                with open(rtm_output.file_path, 'rb') as file:
                    st.download_button(
                        label="📥 Download RTM Excel File",
                        data=file.read(),
                        file_name=Path(rtm_output.file_path).name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )
                
                st.success(f"✅ RTM file ready: {Path(rtm_output.file_path).name}")
                
                # Display summary statistics
                if rtm_output.summary_statistics:
                    with st.expander("📊 Summary Statistics", expanded=True):
                        stats = rtm_output.summary_statistics
                        
                        col_stat1, col_stat2 = st.columns(2)
                        
                        with col_stat1:
                            st.markdown("**By Type:**")
                            for req_type, count in stats.get('by_type', {}).items():
                                st.write(f"• {req_type}: {count}")
                        
                        with col_stat2:
                            st.markdown("**By Priority:**")
                            for priority, count in stats.get('by_priority', {}).items():
                                st.write(f"• {priority}: {count}")
                        
                        st.markdown("**Analysis Quality:**")
                        ai_count = stats.get('ai_analysis_count', 0)
                        fallback_count = stats.get('fallback_count', 0)
                        total = ai_count + fallback_count
                        if total > 0:
                            ai_percentage = (ai_count / total) * 100
                            st.write(f"• AI Analysis: {ai_count} ({ai_percentage:.1f}%)")
                            st.write(f"• Rule-based Fallback: {fallback_count} ({100-ai_percentage:.1f}%)")
            else:
                st.error("❌ Generated file not found")
                
    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()
        
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        st.info("Make sure the API server is running: `python main.py`")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def monitor_analysis_progress(file_id, analysis_request, overall_progress, status_text, batch_container):
    """Monitor analysis progress with real-time updates"""
    
    import threading
    import time
    
    # Start analysis in background
    analysis_thread = threading.Thread(
        target=start_analysis, 
        args=(analysis_request,)
    )
    analysis_thread.daemon = True
    analysis_thread.start()
    
    # Monitor progress
    batch_info = {}
    start_time = time.time()
    
    with batch_container.container():
        batch_status = st.empty()
        batch_progress = st.empty()
        batch_details = st.empty()
    
    # Poll for progress updates
    while analysis_thread.is_alive():
        try:
            # Get current status with batch progress
            status_response = requests.get(f"{API_BASE_URL}/status/{file_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                
                # Update overall status
                if status_data.get("status") == "processing":
                    elapsed = time.time() - start_time
                    progress_percent = status_data.get("progress_percent", 30)
                    batch_info = status_data.get("batch_info", {})
                    
                    # Update main status
                    status_text.text(f"🤖 {status_data.get('message', 'Processing...')} ({elapsed:.0f}s elapsed)")
                    overall_progress.progress(progress_percent)
                    
                    # Update batch progress display
                    if batch_info:
                        with batch_container.container():
                            current_batch = batch_info.get('current_batch', 0)
                            total_batches = batch_info.get('total_batches', 0)
                            completed_batches = batch_info.get('completed_batches', 0)
                            
                            if total_batches > 0:
                                batch_status.info(f"""
                                **🔄 Batch Processing Progress**
                                - **Current Batch**: {current_batch}/{total_batches}
                                - **Completed Batches**: {completed_batches}
                                - **Estimated Time Remaining**: {((total_batches - current_batch) * 35):.0f} seconds
                                """)
                                
                                # Batch progress bar
                                batch_progress_percent = (completed_batches / total_batches) * 100 if total_batches > 0 else 0
                                batch_progress.progress(int(batch_progress_percent))
                                
                                # Show batch details with AI service status
                                if current_batch > 0:
                                    batch_details.text(f"📊 Processing ~{(520 // total_batches)} requirements per batch")
                                    
                                    # Show recent batch activity
                                    recent_activity = get_recent_batch_activity(file_id)
                                    if recent_activity:
                                        with st.expander("🔍 Recent Batch Activity", expanded=False):
                                            for activity in recent_activity[-5:]:  # Show last 5 activities
                                                st.text(activity)
                    
                elif status_data.get("status") == "completed":
                    status_text.text("✅ Analysis complete!")
                    overall_progress.progress(100)
                    
                    # Clear batch progress
                    batch_container.empty()
                    break
                    
        except Exception as e:
            # Continue even if status check fails
            pass
            
        time.sleep(3)  # Check every 3 seconds
    
    # Get final results
    try:
        # Wait a moment for analysis to complete
        time.sleep(1)
        
        analysis_response = requests.post(f"{API_BASE_URL}/analyze", json=analysis_request)
        
        if analysis_response.status_code == 200:
            analysis_data = analysis_response.json()
            display_results(analysis_data, file_id)
        else:
            st.error(f"Analysis failed: {analysis_response.text}")
            
    except Exception as e:
        st.error(f"Error getting results: {str(e)}")

def start_analysis(analysis_request):
    """Start analysis in background thread"""
    try:
        requests.post(f"{API_BASE_URL}/analyze", json=analysis_request)
    except:
        pass

def get_recent_batch_activity(file_id):
    """Get recent batch activity from progress tracker"""
    try:
        # Get status from API which includes recent activities
        status_response = requests.get(f"{API_BASE_URL}/status/{file_id}")
        if status_response.status_code == 200:
            status_data = status_response.json()
            batch_info = status_data.get("batch_info", {})
            return batch_info.get("recent_activities", [])
        return []
    except:
        return []

def display_results(analysis_data, file_id):
    """Display analysis results and download options"""
    
    st.markdown("---")
    st.header("📊 Analysis Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Requirements Found", analysis_data["requirements_found"])
    
    with col2:
        processing_time = analysis_data["analysis_summary"]["processing_time_seconds"]
        st.metric("Processing Time", f"{processing_time:.1f}s")
    
    with col3:
        st.metric("Status", analysis_data["status"].title())
    
    with col4:
        output_file = analysis_data["processing_details"]["output_file"]
        st.metric("Output File", output_file)
    
    # Detailed statistics
    if "statistics" in analysis_data["analysis_summary"]:
        stats = analysis_data["analysis_summary"]["statistics"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Requirements by Type")
            if "by_type" in stats:
                type_data = stats["by_type"]
                df_type = pd.DataFrame(list(type_data.items()), columns=["Type", "Count"])
                st.bar_chart(df_type.set_index("Type"))
        
        with col2:
            st.subheader("🎯 Requirements by Priority")
            if "by_priority" in stats:
                priority_data = stats["by_priority"]
                df_priority = pd.DataFrame(list(priority_data.items()), columns=["Priority", "Count"])
                st.bar_chart(df_priority.set_index("Priority"))
    
    # Download button
    st.markdown("---")
    if st.button("📥 Download RTM Excel File", type="primary"):
        download_rtm(file_id, output_file)

def download_rtm(file_id, filename):
    """Download the generated RTM file"""
    
    try:
        download_response = requests.get(f"{API_BASE_URL}/download/{file_id}")
        
        if download_response.status_code == 200:
            st.download_button(
                label="💾 Save RTM File",
                data=download_response.content,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("✅ RTM file ready for download!")
        else:
            st.error("Download failed. Please try again.")
            
    except Exception as e:
        st.error(f"Download error: {str(e)}")

if __name__ == "__main__":
    main()
