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
    if 'recording_link' not in st.session_state:
        st.session_state.recording_link = ''

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

def load_departments() -> Dict:
    """Load department configuration from JSON file"""
    try:
        with open('departments.json', 'r') as f:
            data = json.load(f)
            return data.get('departments', {})
    except FileNotFoundError:
        st.error("departments.json file not found. Please create it from the template.")
        return {}
    except json.JSONDecodeError:
        st.error("Invalid JSON in departments.json file.")
        return {}

def load_projects() -> Dict:
    """Load projects configuration from JSON file"""
    try:
        with open('projects.json', 'r') as f:
            data = json.load(f)
            return data.get('projects', {})
    except FileNotFoundError:
        st.error("projects.json file not found. Please create it from the template.")
        return {}
    except json.JSONDecodeError:
        st.error("Invalid JSON in projects.json file.")
        return {}

def load_existing_customers() -> Dict:
    """Load existing customers configuration from JSON file"""
    try:
        with open('existing_customers.json', 'r') as f:
            data = json.load(f)
            return data.get('existing_customers', {})
    except FileNotFoundError:
        st.error("existing_customers.json file not found. Please create it from the template.")
        return {}
    except json.JSONDecodeError:
        st.error("Invalid JSON in existing_customers.json file.")
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
    
    # Load customers, departments, projects, and existing customers
    customers = load_customers()
    departments = load_departments()
    projects = load_projects()
    existing_customers = load_existing_customers()
    if not customers or not departments:
        st.stop()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Meeting type selection
        meeting_type = st.radio(
            "Meeting Type",
            ["Sales Call", "Internal Meeting", "Project Meeting", "Existing Customer"],
            help="Select the type of meeting transcript"
        )
        st.session_state.meeting_type = meeting_type.lower().replace(" ", "_")
        
        # Customer/Department/Project selection based on meeting type
        if st.session_state.meeting_type == "sales_call":
            customer_names = list(customers.keys())
            selected_customer = st.selectbox(
                "Select Customer",
                customer_names,
                help="Choose the customer for task creation"
            )
            
            if selected_customer:
                customer_info = customers[selected_customer]
                project_id = customer_info.get('asana_project_id', '')
                
                if project_id == 'YOUR_ASANA_PROJECT_ID_HERE':
                    st.warning("Please configure the Asana project ID in customers.json")
                else:
                    st.success(f"Customer: {selected_customer} | Project ID: {project_id[:8]}...")
                    
        elif st.session_state.meeting_type == "internal_meeting":
            # Internal meeting - select department
            department_names = list(departments.keys())
            selected_department = st.selectbox(
                "Select Department",
                department_names,
                help="Choose the department for task creation"
            )
            
            if selected_department:
                department_info = departments[selected_department]
                project_id = department_info.get('asana_project_id', '')
                selected_customer = selected_department  # Use department name as customer for consistency
                
                if project_id.startswith('YOUR_'):
                    st.warning(f"Please configure the Asana project ID for {selected_department} in departments.json")
                else:
                    st.success(f"Department: {selected_department} | Project ID: {project_id[:8]}...")
                    
        elif st.session_state.meeting_type == "project_meeting":
            # Project meeting - select project
            project_names = list(projects.keys())
            selected_project = st.selectbox(
                "Select Project",
                project_names,
                help="Choose the project for task creation"
            )
            
            if selected_project:
                project_info = projects[selected_project]
                project_id = project_info.get('asana_project_id', '')
                selected_customer = selected_project  # Use project name as customer for consistency
                
                if project_id.startswith('YOUR_'):
                    st.warning(f"Please configure the Asana project ID for {selected_project} in projects.json")
                else:
                    st.success(f"Project: {selected_project} | Project ID: {project_id[:8]}...")
                    
        else:  # existing_customer
            # Existing customer - select from existing customers
            existing_customer_names = list(existing_customers.keys())
            selected_existing_customer = st.selectbox(
                "Select Existing Customer",
                existing_customer_names,
                help="Choose the existing customer for escalation/task creation"
            )
            
            if selected_existing_customer:
                existing_customer_info = existing_customers[selected_existing_customer]
                project_id = existing_customer_info.get('asana_project_id', '')
                selected_customer = selected_existing_customer  # Use existing customer name for consistency
                
                if project_id == 'YOUR_ASANA_PROJECT_ID_HERE':
                    st.warning(f"Please configure the Asana project ID for {selected_existing_customer} in existing_customers.json")
                else:
                    st.success(f"Existing Customer: {selected_existing_customer} | Project ID: {project_id[:8]}...")
        
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
        
        # Recording link input
        recording_link = st.text_input(
            "Recording Link",
            placeholder="https://grain.com/share/recording/...",
            help="Paste the link to the meeting recording (Grain, Gong, Zoom, etc.)"
        )
        
        if uploaded_file is not None:
            # Display file info
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.info(f"📎 {uploaded_file.name} ({file_size_mb:.2f} MB)")
            
            # Validate recording link
            if not recording_link:
                st.warning("⚠️ Please provide a recording link for reference")
            
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
                        # Store recording link in session state
                        st.session_state.recording_link = recording_link
                        
                        # Analyze transcript
                        analyzer = GeminiAnalyzer()
                        # Pass department for internal meetings, project for project meetings, context for existing customers
                        if st.session_state.meeting_type == "internal_meeting":
                            department = selected_customer
                            project = ""
                            additional_context = ""
                        elif st.session_state.meeting_type == "project_meeting":
                            department = ""
                            project = selected_customer
                            additional_context = ""
                        elif st.session_state.meeting_type == "existing_customer":
                            department = ""
                            project = ""
                            # Get customer-specific context from existing_customers.json
                            existing_customer_info = existing_customers.get(selected_customer, {})
                            additional_context = existing_customer_info.get('context', '')
                        else:
                            department = ""
                            project = ""
                            additional_context = ""
                        
                        analysis = analyzer.analyze_transcript(
                            st.session_state.extracted_text,
                            selected_customer,
                            additional_context if additional_context else f"Meeting transcript for {selected_customer}",
                            meeting_type=st.session_state.meeting_type,
                            recording_link=recording_link,
                            department=department,
                            project=project
                        )
                        
                        # Store action items
                        st.session_state.action_items = [
                            {
                                'title': item.title,
                                'description': item.description,
                                'priority': item.priority or 'medium',
                                'timestamp': getattr(item, 'timestamp', None),
                                'is_question': getattr(item, 'is_question', False)
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
            if project_id and not project_id.startswith('YOUR_'):
                with st.spinner("Creating tasks in Asana..."):
                    try:
                        # Get current date for section naming
                        from datetime import datetime
                        current_date = datetime.now().strftime("%m/%d")
                        
                        # Create section name based on meeting type and title
                        meeting_title = getattr(st.session_state, 'meeting_title', 'Meeting')
                        section_name = f"{current_date} - {meeting_title}"
                        
                        # Create meeting context for task descriptions
                        # Create appropriate context based on meeting type
                        meeting_context = f"{current_date} - {selected_customer}: {meeting_title}"
                        
                        # Create tasks with section
                        asana_client = AsanaTaskCreator()
                        created_tasks = asana_client.create_tasks(
                            st.session_state.action_items,
                            project_id,
                            section_name=section_name,
                            meeting_context=meeting_context,
                            recording_link=st.session_state.recording_link
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
                if st.session_state.meeting_type == "internal_meeting":
                    st.error("Please configure the Asana project ID for this department in departments.json")
                elif st.session_state.meeting_type == "project_meeting":
                    st.error("Please configure the Asana project ID for this project in projects.json")
                else:
                    st.error("Please configure the Asana project ID for this customer in customers.json")
    
    # Quick Task Section
    st.divider()
    st.header("⚡ Quick Task Creation")
    st.info("Create tasks directly from text, upload email screenshots, or upload PDF conversations for automatic task extraction")
    
    # Add tabs for different input methods
    quick_task_tab1, quick_task_tab2, quick_task_tab3 = st.tabs(["📝 Text Input", "📸 Image Upload", "📄 PDF Upload"])
    
    with quick_task_tab1:
        quick_task_col1, quick_task_col2 = st.columns([2, 1])
        
        with quick_task_col1:
            quick_task_text_input = st.text_area(
                "Describe your task(s)",
                placeholder="Examples:\n"
                           "• Send follow-up email to John about pricing tomorrow\n"
                           "• Schedule demo with Sarah for next Tuesday\n"
                           "• Review contract and provide feedback by Friday\n\n"
                           "Tip: Enter multiple tasks on separate lines or separated by semicolons",
                height=120,
                help="Enter one or more tasks. The AI will interpret your natural language and create structured tasks.",
                key="quick_task_input"  # Add key for state management
            )
    
    with quick_task_tab2:
        st.write("Upload a screenshot of an email or message to automatically extract tasks")
        uploaded_image = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
            help="Upload a screenshot of an email, Slack message, or other communication",
            key="quick_task_image_upload"
        )
        
        quick_task_text_image = ""
        
        if uploaded_image is not None:
            # Display the uploaded image
            st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
            
            # Extract text from image button
            if st.button("🔍 Extract Tasks from Image", type="secondary"):
                with st.spinner("Analyzing image..."):
                    try:
                        analyzer = GeminiAnalyzer()
                        
                        # Get the appropriate context based on meeting type
                        if st.session_state.meeting_type == "existing_customer" and 'selected_customer' in locals():
                            existing_customer_info = existing_customers.get(selected_customer, {})
                            customer_context = existing_customer_info.get('context', '')
                        else:
                            customer_context = ""
                        
                        # Analyze the image
                        image_analysis = analyzer.analyze_image_for_tasks(
                            uploaded_image,
                            selected_customer if 'selected_customer' in locals() else "Unknown Customer",
                            st.session_state.meeting_type,
                            customer_context
                        )
                        
                        # Store the extracted text in session state
                        st.session_state['image_extracted_text'] = image_analysis
                        st.success("✅ Successfully analyzed image!")
                        quick_task_text_image = st.text_area(
                            "Extracted Context and Tasks", 
                            image_analysis, 
                            height=200, 
                            help="Review and edit the extracted tasks if needed"
                        )
                    except Exception as e:
                        st.error(f"Error analyzing image: {str(e)}")
        
        # Use extracted text if available
        if 'image_extracted_text' in st.session_state and not quick_task_text_image:
            quick_task_text_image = st.session_state.get('image_extracted_text', '')
            if quick_task_text_image:
                st.text_area(
                    "Previously Extracted Tasks", 
                    quick_task_text_image, 
                    height=200,
                    help="These tasks were extracted from your last image upload"
                )
    
    with quick_task_tab3:
        st.write("Upload a PDF of an email conversation or document to extract tasks")
        uploaded_pdf = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload a PDF of an email thread or conversation for task extraction",
            key="quick_task_pdf_upload"
        )
        
        quick_task_text_pdf = ""
        
        if uploaded_pdf is not None:
            # Display PDF info
            file_size_mb = uploaded_pdf.size / (1024 * 1024)
            st.info(f"📄 {uploaded_pdf.name} ({file_size_mb:.2f} MB)")
            
            # Extract tasks from PDF button
            if st.button("🔍 Extract Tasks from PDF", type="secondary"):
                with st.spinner("Processing PDF and analyzing conversation..."):
                    try:
                        # First extract text from PDF
                        from src.pdf_processor import PDFProcessor
                        pdf_processor = PDFProcessor()
                        # Convert UploadedFile to bytes
                        pdf_bytes = uploaded_pdf.read()
                        uploaded_pdf.seek(0)  # Reset file pointer
                        # extract_text returns tuple (text, method_used)
                        pdf_text, extraction_method = pdf_processor.extract_text(pdf_bytes)
                        
                        if not pdf_text or pdf_text.strip() == "":
                            st.error("Could not extract text from PDF. Please try a different file.")
                        else:
                            # Show extracted text preview
                            with st.expander("📋 View Extracted Text", expanded=False):
                                st.text_area("PDF Content", pdf_text[:3000] + "..." if len(pdf_text) > 3000 else pdf_text, height=200, disabled=True)
                            
                            # Analyze with Gemini
                            analyzer = GeminiAnalyzer()
                            
                            # Get the appropriate context based on meeting type
                            if st.session_state.meeting_type == "existing_customer" and 'selected_customer' in locals():
                                existing_customer_info = existing_customers.get(selected_customer, {})
                                customer_context = existing_customer_info.get('context', '')
                            else:
                                customer_context = ""
                            
                            # Analyze the PDF conversation
                            pdf_analysis = analyzer.analyze_pdf_for_tasks(
                                pdf_text,
                                selected_customer if 'selected_customer' in locals() else "Unknown Customer",
                                st.session_state.meeting_type,
                                customer_context
                            )
                            
                            # Store the extracted tasks in session state
                            st.session_state['pdf_extracted_text'] = pdf_analysis
                            st.success("✅ Successfully analyzed PDF conversation!")
                            quick_task_text_pdf = st.text_area(
                                "Extracted Tasks from Conversation", 
                                pdf_analysis, 
                                height=250, 
                                help="Review and edit the extracted tasks if needed"
                            )
                    except Exception as e:
                        st.error(f"Error processing PDF: {str(e)}")
        
        # Use extracted text if available
        if 'pdf_extracted_text' in st.session_state and not quick_task_text_pdf:
            quick_task_text_pdf = st.session_state.get('pdf_extracted_text', '')
            if quick_task_text_pdf:
                st.text_area(
                    "Previously Extracted Tasks", 
                    quick_task_text_pdf, 
                    height=250,
                    help="These tasks were extracted from your last PDF upload"
                )
    
    # Determine which text to use based on active tab
    if 'quick_task_text_pdf' in locals() and quick_task_text_pdf:
        quick_task_text = quick_task_text_pdf
    elif 'quick_task_text_image' in locals() and quick_task_text_image:
        quick_task_text = quick_task_text_image
    else:
        quick_task_text = quick_task_text_input if 'quick_task_text_input' in locals() else ""
    
    # Create columns for info display
    quick_task_col1, quick_task_col2 = st.columns([2, 1])
    
    with quick_task_col2:
        st.write("**Current Selection:**")
        if 'meeting_type' in st.session_state:
            if st.session_state.meeting_type == "sales_call":
                st.write(f"📊 Customer: {selected_customer if 'selected_customer' in locals() else 'None'}")
            elif st.session_state.meeting_type == "internal_meeting":
                st.write(f"🏢 Department: {selected_customer if 'selected_customer' in locals() else 'None'}")
            elif st.session_state.meeting_type == "existing_customer":
                st.write(f"🔄 Existing: {selected_customer if 'selected_customer' in locals() else 'None'}")
            else:
                st.write(f"📁 Project: {selected_customer if 'selected_customer' in locals() else 'None'}")
            
            if 'project_id' in locals() and project_id and not project_id.startswith('YOUR_'):
                st.write(f"✅ Ready to create tasks")
            else:
                st.write(f"⚠️ Configure project ID first")
    
    if st.button("🚀 Create Quick Task(s)", type="secondary", use_container_width=True):
        if not quick_task_text.strip():
            st.warning("Please enter a task description")
        elif 'project_id' not in locals() or not project_id or project_id.startswith('YOUR_'):
            st.error("Please select a valid customer/department/project with configured Asana ID")
        else:
            with st.spinner("Processing your request with AI..."):
                try:
                    from datetime import datetime
                    
                    # Get current date for section
                    current_date = datetime.now().strftime("%m/%d")
                    section_name = f"Quick Tasks - {current_date}"
                    
                    # Process with AI
                    analyzer = GeminiAnalyzer()
                    
                    # Determine context based on meeting type
                    context_type = st.session_state.meeting_type.replace("_", " ").title()
                    context_name = selected_customer if 'selected_customer' in locals() else "General"
                    
                    # Interpret the quick task(s)
                    interpreted_tasks = analyzer.interpret_quick_tasks(
                        quick_task_text,
                        context_name,
                        context_type
                    )
                    
                    if interpreted_tasks:
                        # Create tasks in Asana
                        asana_client = AsanaTaskCreator()
                        
                        # Check if section exists, create if not
                        created_tasks = asana_client.create_tasks(
                            interpreted_tasks,
                            project_id,
                            section_name=section_name,
                            meeting_context=f"Quick Task - {context_name}"
                        )
                        
                        if created_tasks:
                            st.success(f"✅ Successfully created {len(created_tasks)} task(s) in Asana!")
                            
                            # Show created tasks
                            st.subheader("Created Tasks:")
                            for task in created_tasks:
                                if task.get('permalink_url'):
                                    st.markdown(f"• [{task['name']}]({task['permalink_url']})")
                                else:
                                    st.write(f"• {task['name']}")
                            
                            # Clear the text area for next use by deleting the key
                            if 'quick_task_input' in st.session_state:
                                del st.session_state.quick_task_input
                        else:
                            st.error("Failed to create tasks in Asana")
                    else:
                        st.error("Could not interpret the task description")
                        
                except Exception as e:
                    st.error(f"Error processing quick task: {str(e)}")
    
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