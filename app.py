"""
Asana Opus - AI-Powered Meeting Transcript to Task Converter
Main Streamlit Application
"""

import streamlit as st
import json
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Optional
from datetime import datetime

# Import custom modules
from src.pdf_processor import PDFProcessor
from src.gemini_analyzer import GeminiAnalyzer
from src.asana_client import AsanaTaskCreator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Asana Opus - Transcript to Tasks",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = 'idle'
    if 'extracted_text' not in st.session_state:
        st.session_state.extracted_text = None
    if 'action_items' not in st.session_state:
        st.session_state.action_items = []
    if 'created_tasks' not in st.session_state:
        st.session_state.created_tasks = []
    if 'error_messages' not in st.session_state:
        st.session_state.error_messages = []
    if 'meeting_type' not in st.session_state:
        st.session_state.meeting_type = 'sales_call'
    if 'meeting_title' not in st.session_state:
        st.session_state.meeting_title = 'Meeting'

init_session_state()

def load_customers() -> Dict:
    """Load customer configuration from JSON file"""
    try:
        with open('customers.json', 'r') as f:
            data = json.load(f)
            return data.get('customers', {})
    except FileNotFoundError:
        st.error("customers.json file not found. Please create it from the template.")
        return {}
    except json.JSONDecodeError:
        st.error("Invalid JSON in customers.json file.")
        return {}

def check_api_keys() -> tuple:
    """Check if required API keys are configured"""
    asana_token = os.getenv('ASANA_ACCESS_TOKEN')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    missing_keys = []
    if not asana_token:
        missing_keys.append("ASANA_ACCESS_TOKEN")
    if not gemini_key:
        missing_keys.append("GEMINI_API_KEY")
    
    return len(missing_keys) == 0, missing_keys

def main():
    """Main application logic"""
    
    # Header
    st.title("📄 Asana Opus")
    st.subheader("AI-Powered Meeting Transcript to Task Converter")
    
    # Check API keys
    keys_valid, missing_keys = check_api_keys()
    if not keys_valid:
        st.error(f"Missing API keys in .env file: {', '.join(missing_keys)}")
        st.info("Please copy .env.example to .env and add your API keys.")
        st.stop()
    
    # Load customers
    customers = load_customers()
    if not customers:
        st.stop()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Meeting type selection
        meeting_type = st.radio(
            "Meeting Type",
            ["Sales Call", "Internal Meeting"],
            help="Select the type of meeting transcript"
        )
        st.session_state.meeting_type = meeting_type.lower().replace(" ", "_")
        
        # Customer selection (only for sales calls)
        if st.session_state.meeting_type == "sales_call":
            customer_names = list(customers.keys())
            selected_customer = st.selectbox(
                "Select Customer/Project",
                customer_names,
                help="Choose the customer/project for task creation"
            )
            
            if selected_customer:
                customer_info = customers[selected_customer]
                project_id = customer_info.get('asana_project_id', '')
                
                if project_id == 'YOUR_ASANA_PROJECT_ID_HERE':
                    st.warning("Please configure the Asana project ID in customers.json")
                else:
                    st.success(f"Project ID: {project_id[:8]}...")
        else:
            # Internal meeting - use fixed project
            selected_customer = "Internal Meeting"
            project_id = "1211106531309164"  # Fixed internal meetings project
            st.info("Internal meetings will be added to the Ops Board")
        
        st.divider()
        
        # Processing options
        st.subheader("Options")
        auto_process = st.checkbox(
            "Auto-process on upload",
            value=True,
            help="Automatically analyze transcript when uploaded"
        )
        
        show_extracted_text = st.checkbox(
            "Show extracted text",
            value=False,
            help="Display the raw extracted text from PDF"
        )
        
        st.divider()
        
        # Connection test
        if st.button("Test Connections"):
            with st.spinner("Testing connections..."):
                try:
                    # Test Asana
                    asana_client = AsanaTaskCreator()
                    if asana_client.test_connection():
                        st.success("✅ Asana connection successful")
                    else:
                        st.error("❌ Asana connection failed")
                    
                    # Test Gemini
                    gemini_client = GeminiAnalyzer()
                    st.success("✅ Gemini API key configured")
                    
                except Exception as e:
                    st.error(f"Connection test failed: {str(e)}")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("1️⃣ Upload Transcript")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload a meeting transcript PDF from Grain, Gong, or similar tools"
        )
        
        if uploaded_file is not None:
            # Display file info
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.info(f"📎 {uploaded_file.name} ({file_size_mb:.2f} MB)")
            
            # Process button or auto-process
            if auto_process or st.button("Process Transcript", type="primary"):
                st.session_state.processing_status = 'processing'
                
                # Process the PDF
                with st.spinner("Extracting text from PDF..."):
                    try:
                        # Read file content
                        file_content = uploaded_file.read()
                        
                        # Extract text
                        processor = PDFProcessor()
                        is_valid, error_msg = processor.validate_file(file_content, uploaded_file.name)
                        
                        if not is_valid:
                            st.error(f"Invalid file: {error_msg}")
                            st.session_state.processing_status = 'error'
                        else:
                            extracted_text, method = processor.extract_text(file_content)
                            
                            if extracted_text:
                                st.session_state.extracted_text = extracted_text
                                st.success(f"✅ Text extracted successfully using {method}")
                                
                                if show_extracted_text:
                                    with st.expander("View Extracted Text"):
                                        st.text(extracted_text[:2000] + "..." if len(extracted_text) > 2000 else extracted_text)
                            else:
                                st.error("Failed to extract text from PDF")
                                st.session_state.processing_status = 'error'
                    
                    except Exception as e:
                        st.error(f"Error processing PDF: {str(e)}")
                        st.session_state.processing_status = 'error'
    
    with col2:
        st.header("2️⃣ AI Analysis")
        
        if st.session_state.extracted_text:
            if st.button("Analyze with AI", type="primary") or (auto_process and st.session_state.processing_status == 'processing'):
                with st.spinner("Analyzing transcript with Gemini AI..."):
                    try:
                        # Analyze transcript
                        analyzer = GeminiAnalyzer()
                        analysis = analyzer.analyze_transcript(
                            st.session_state.extracted_text,
                            selected_customer,
                            f"Meeting transcript for {selected_customer}",
                            meeting_type=st.session_state.meeting_type
                        )
                        
                        # Store action items
                        st.session_state.action_items = [
                            {
                                'title': item.title,
                                'description': item.description,
                                'priority': item.priority or 'medium'
                            }
                            for item in analysis.action_items
                        ]
                        
                        # Display results
                        st.success(f"✅ Found {len(analysis.action_items)} action items")
                        
                        # Show meeting title
                        if hasattr(analysis, 'meeting_title'):
                            st.subheader("Meeting Title")
                            st.write(analysis.meeting_title)
                            st.session_state.meeting_title = analysis.meeting_title
                        
                        # Show summary
                        if analysis.summary:
                            st.subheader("Meeting Summary")
                            st.write(analysis.summary)
                        
                        # Show participants
                        if analysis.participants:
                            st.subheader("Participants")
                            st.write(", ".join(analysis.participants))
                        
                        # Show key decisions
                        if analysis.key_decisions:
                            st.subheader("Key Decisions")
                            for decision in analysis.key_decisions:
                                st.write(f"• {decision}")
                        
                        st.session_state.processing_status = 'analyzed'
                        
                    except Exception as e:
                        st.error(f"Error analyzing transcript: {str(e)}")
                        st.session_state.processing_status = 'error'
        else:
            st.info("Upload and process a PDF first")
    
    # Action Items Section
    if st.session_state.action_items:
        st.divider()
        st.header("3️⃣ Action Items")
        
        # Display action items in a table-like format
        for i, item in enumerate(st.session_state.action_items, 1):
            with st.expander(f"{i}. {item['title']}", expanded=True):
                st.write(f"**Description:** {item['description']}")
                st.write(f"**Priority:** {item['priority']}")
        
        # Create tasks button
        if st.button("Create Tasks in Asana", type="primary", use_container_width=True):
            if project_id and project_id != 'YOUR_ASANA_PROJECT_ID_HERE':
                with st.spinner("Creating tasks in Asana..."):
                    try:
                        # Get current date for section naming
                        current_date = datetime.now().strftime("%m/%d")
                        
                        # Create section name based on meeting type and title
                        meeting_title = getattr(st.session_state, 'meeting_title', 'Meeting')
                        section_name = f"{current_date} - {meeting_title}"
                        
                        # Create meeting context for task descriptions
                        if st.session_state.meeting_type == "internal_meeting":
                            meeting_context = f"{current_date} - Internal: {meeting_title}"
                        else:
                            meeting_context = f"{current_date} - {selected_customer}: {meeting_title}"
                        
                        # Create tasks with section
                        asana_client = AsanaTaskCreator()
                        created_tasks = asana_client.create_tasks(
                            st.session_state.action_items,
                            project_id,
                            section_name=section_name,
                            meeting_context=meeting_context
                        )
                        
                        st.session_state.created_tasks = created_tasks
                        
                        if created_tasks:
                            st.success(f"✅ Successfully created {len(created_tasks)} tasks in Asana!")
                            
                            # Show created tasks with links
                            st.subheader("Created Tasks")
                            for task in created_tasks:
                                if task.get('permalink_url'):
                                    st.markdown(f"• [{task['name']}]({task['permalink_url']})")
                                else:
                                    st.write(f"• {task['name']}")
                        else:
                            st.error("No tasks were created. Please check the logs.")
                        
                    except Exception as e:
                        st.error(f"Error creating tasks: {str(e)}")
            else:
                st.error("Please configure the Asana project ID for this customer in customers.json")
    
    # Status indicator in footer
    st.divider()
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        if st.session_state.extracted_text:
            st.metric("Text Extracted", "✅ Yes")
        else:
            st.metric("Text Extracted", "❌ No")
    
    with status_col2:
        st.metric("Action Items", len(st.session_state.action_items))
    
    with status_col3:
        st.metric("Tasks Created", len(st.session_state.created_tasks))

if __name__ == "__main__":
    main()