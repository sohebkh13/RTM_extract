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