# Streamlit Application Setup and Deployment - Complete Guide

## Table of Contents
1. [Latest Streamlit Best Practices (2025)](#latest-streamlit-best-practices-2025)
2. [File Upload Configuration](#file-upload-configuration)
3. [Session State Management](#session-state-management)
4. [Error Handling and User Feedback](#error-handling-and-user-feedback)
5. [Local Development Setup](#local-development-setup)
6. [Security Considerations](#security-considerations)

---

## Latest Streamlit Best Practices (2025)

### Core Application Structure

```python
# app.py - Main application structure
import streamlit as st
import pandas as pd
from io import BytesIO
import time

# Page configuration (must be first Streamlit command)
st.set_page_config(
    page_title="Meeting Transcript Processor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def init_session_state():
    """Initialize all session state variables at app startup"""
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = 'idle'
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'processed_results' not in st.session_state:
        st.session_state.processed_results = None
    if 'error_messages' not in st.session_state:
        st.session_state.error_messages = []

# Call initialization at app start
init_session_state()
```

### Performance Optimization Strategies

**1. Caching for Heavy Operations**
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def process_large_file(file_content):
    """Cache expensive file processing operations"""
    # Process file
    return processed_data

@st.cache_resource  # Cache connections/models
def load_ml_model():
    """Load and cache ML models or database connections"""
    return model
```

**2. Fragment Decorators for Partial Reruns (2025 Feature)**
```python
@st.fragment
def update_specific_section():
    """Only this section reruns when its inputs change"""
    # Isolated rerun logic
    pass
```

---

## File Upload Configuration

### Basic File Upload Implementation

```python
def setup_file_uploader():
    """Configure and handle file uploads with proper validation"""
    
    # File upload widget with configuration
    uploaded_file = st.file_uploader(
        label="Upload Meeting Transcript",
        type=['pdf', 'txt', 'docx'],  # Allowed file types
        accept_multiple_files=False,   # Single file only
        help="Upload a PDF or text file containing the meeting transcript",
        key="transcript_uploader",     # Unique key for session state
        disabled=st.session_state.processing_status == 'processing'
    )
    
    if uploaded_file is not None:
        # File validation
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        # Check file size (default limit is 200MB, configurable)
        if file_size_mb > 200:
            st.error(f"File too large: {file_size_mb:.2f}MB. Maximum allowed: 200MB")
            return None
        
        # Store file details in session state
        st.session_state.uploaded_file = {
            'name': uploaded_file.name,
            'type': uploaded_file.type,
            'size': uploaded_file.size,
            'data': uploaded_file.read()  # Read into memory
        }
        
        # Reset file pointer after reading
        uploaded_file.seek(0)
        
        return uploaded_file
    
    return None
```

### Advanced File Upload Configuration

**config.toml Settings:**
```toml
# .streamlit/config.toml
[server]
# Maximum file upload size (in MB)
maxUploadSize = 500

# Maximum message size (affects file uploads)
maxMessageSize = 500

# Enable file watching for development
fileWatcherType = "auto"
```

### File Processing Best Practices

```python
def process_uploaded_file(uploaded_file):
    """Process uploaded file with proper error handling"""
    
    try:
        # Display file information
        with st.expander("File Details", expanded=False):
            st.write(f"Filename: {uploaded_file.name}")
            st.write(f"File type: {uploaded_file.type}")
            st.write(f"File size: {uploaded_file.size:,} bytes")
        
        # Process based on file type
        if uploaded_file.type == "application/pdf":
            # PDF processing
            file_content = process_pdf(uploaded_file)
        elif uploaded_file.type == "text/plain":
            # Text file processing
            file_content = uploaded_file.read().decode('utf-8')
        else:
            # Other file types
            file_content = handle_other_formats(uploaded_file)
        
        return file_content
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.session_state.error_messages.append(str(e))
        return None

def process_pdf(pdf_file):
    """Handle PDF files specifically"""
    # PDF files are processed as BytesIO objects in memory
    pdf_bytes = BytesIO(pdf_file.read())
    # Process PDF bytes...
    return extracted_text
```

### Security Considerations for File Uploads

```python
def validate_uploaded_file(file):
    """Comprehensive file validation for security"""
    
    # 1. Validate file extension (case-insensitive)
    allowed_extensions = {'.pdf', '.txt', '.docx'}
    file_ext = os.path.splitext(file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise ValueError(f"Invalid file type: {file_ext}")
    
    # 2. Validate MIME type
    allowed_mime_types = {
        'application/pdf',
        'text/plain',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    if file.type not in allowed_mime_types:
        raise ValueError(f"Invalid MIME type: {file.type}")
    
    # 3. Check for malicious content patterns
    file_header = file.read(1024)
    file.seek(0)  # Reset pointer
    
    # Check for suspicious patterns
    if contains_suspicious_patterns(file_header):
        raise ValueError("File contains suspicious content")
    
    return True
```

---

## Session State Management

### Comprehensive Session State Pattern

```python
class SessionStateManager:
    """Centralized session state management"""
    
    @staticmethod
    def initialize():
        """Initialize all session state variables"""
        defaults = {
            'user_inputs': {},
            'processing_status': 'idle',
            'results': None,
            'error_log': [],
            'ui_state': {
                'current_tab': 0,
                'sidebar_expanded': True,
                'show_advanced': False
            },
            'cache': {
                'last_processed': None,
                'timestamp': None
            }
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @staticmethod
    def get(key, default=None):
        """Safe getter with default value"""
        return st.session_state.get(key, default)
    
    @staticmethod
    def set(key, value):
        """Set session state value"""
        st.session_state[key] = value
    
    @staticmethod
    def update_nested(path, value):
        """Update nested dictionary values"""
        keys = path.split('.')
        target = st.session_state
        
        for key in keys[:-1]:
            target = target.setdefault(key, {})
        
        target[keys[-1]] = value
    
    @staticmethod
    def clear_all():
        """Clear all session state"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
```

### Widget State Management

```python
def create_stateful_form():
    """Example of form with persistent state"""
    
    with st.form("config_form"):
        # Text input with session state
        workspace_id = st.text_input(
            "Workspace ID",
            value=st.session_state.get('workspace_id', ''),
            key='workspace_id'
        )
        
        # Selectbox with session state
        priority = st.selectbox(
            "Default Priority",
            options=['Low', 'Medium', 'High'],
            index=['Low', 'Medium', 'High'].index(
                st.session_state.get('priority', 'Medium')
            ),
            key='priority'
        )
        
        # Checkbox with session state
        auto_process = st.checkbox(
            "Auto-process on upload",
            value=st.session_state.get('auto_process', False),
            key='auto_process'
        )
        
        # Form submission
        submitted = st.form_submit_button("Save Configuration")
        
        if submitted:
            st.success("Configuration saved!")
            # State is automatically saved through widget keys
```

### Callback Functions with Session State

```python
def handle_file_upload():
    """Callback function for file upload"""
    if st.session_state.file_uploader is not None:
        st.session_state.processing_status = 'uploaded'
        st.session_state.upload_timestamp = time.time()

def handle_process_click():
    """Callback for process button"""
    st.session_state.processing_status = 'processing'
    # Trigger processing logic

# Using callbacks
uploaded_file = st.file_uploader(
    "Choose a file",
    key='file_uploader',
    on_change=handle_file_upload
)

st.button(
    "Process File",
    on_click=handle_process_click,
    disabled=st.session_state.processing_status != 'uploaded'
)
```

### Multi-Page State Management

```python
# pages/page1.py
def page1():
    """First page of multi-page app"""
    st.title("Page 1: Upload")
    
    # Access shared state
    if 'shared_data' not in st.session_state:
        st.session_state.shared_data = {}
    
    file = st.file_uploader("Upload file")
    if file:
        st.session_state.shared_data['file'] = file
        st.success("File uploaded! Go to Page 2 to process.")

# pages/page2.py
def page2():
    """Second page accessing shared state"""
    st.title("Page 2: Process")
    
    if 'shared_data' in st.session_state and 'file' in st.session_state.shared_data:
        file = st.session_state.shared_data['file']
        st.write(f"Processing: {file.name}")
    else:
        st.warning("Please upload a file on Page 1 first")
```

---

## Error Handling and User Feedback

### Comprehensive Error Handling Pattern

```python
class ErrorHandler:
    """Centralized error handling for Streamlit app"""
    
    @staticmethod
    def handle_error(error, context=""):
        """Handle errors with appropriate user feedback"""
        
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Log to session state
        if 'error_log' not in st.session_state:
            st.session_state.error_log = []
        
        st.session_state.error_log.append({
            'timestamp': time.time(),
            'type': error_type,
            'message': error_msg,
            'context': context
        })
        
        # Display user-friendly error message
        if isinstance(error, ValueError):
            st.error(f"⚠️ Invalid input: {error_msg}")
        elif isinstance(error, FileNotFoundError):
            st.error(f"📁 File not found: {error_msg}")
        elif isinstance(error, PermissionError):
            st.error(f"🔒 Permission denied: {error_msg}")
        elif isinstance(error, ConnectionError):
            st.error(f"🌐 Connection error: {error_msg}")
            st.info("Please check your internet connection and try again.")
        else:
            st.error(f"❌ An error occurred: {error_msg}")
            
            # Show debug info in expander for development
            if st.secrets.get("debug_mode", False):
                with st.expander("Debug Information"):
                    st.code(f"Error Type: {error_type}\n"
                           f"Context: {context}\n"
                           f"Full Error: {error}")
    
    @staticmethod
    def safe_execute(func, *args, **kwargs):
        """Execute function with error handling"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.handle_error(e, context=func.__name__)
            return None
```

### Progress Indicators and Status Feedback

```python
def process_with_progress():
    """Demonstrate various progress indicators"""
    
    # 1. Progress Bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(100):
        progress_bar.progress(i + 1)
        status_text.text(f'Processing... {i+1}%')
        time.sleep(0.01)
    
    progress_bar.empty()
    status_text.empty()
    
    # 2. Spinner
    with st.spinner('Analyzing transcript...'):
        time.sleep(2)
        result = perform_analysis()
    
    # 3. Status Messages
    st.success('✅ Analysis complete!')
    st.info('ℹ️ Found 5 action items')
    st.warning('⚠️ 2 items need clarification')
    
    # 4. Toast Notifications (2025 feature)
    st.toast('Processing complete!', icon='🎉')
    
    return result
```

### Advanced Progress Tracking

```python
class ProgressTracker:
    """Track multi-step process progress"""
    
    def __init__(self, steps):
        self.steps = steps
        self.current_step = 0
        self.progress_bar = st.progress(0)
        self.status_container = st.container()
        
    def update(self, step_name, message=""):
        """Update progress for current step"""
        self.current_step += 1
        progress = self.current_step / len(self.steps)
        
        self.progress_bar.progress(progress)
        
        with self.status_container:
            st.write(f"**Step {self.current_step}/{len(self.steps)}:** {step_name}")
            if message:
                st.caption(message)
    
    def complete(self):
        """Mark process as complete"""
        self.progress_bar.progress(1.0)
        with self.status_container:
            st.success("✅ All steps completed successfully!")
        time.sleep(1)
        self.progress_bar.empty()

# Usage
def process_transcript():
    steps = ['Upload', 'Validate', 'Extract', 'Analyze', 'Create Tasks']
    tracker = ProgressTracker(steps)
    
    tracker.update('Upload', 'File received')
    # ... processing logic
    
    tracker.update('Validate', 'File format verified')
    # ... processing logic
    
    tracker.complete()
```

### User Feedback Components

```python
def create_feedback_ui():
    """Create comprehensive feedback UI"""
    
    # Status indicator
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Files Processed", "12", "+3")
    
    with col2:
        st.metric("Success Rate", "95%", "+2%")
    
    with col3:
        st.metric("Avg. Processing Time", "2.3s", "-0.5s")
    
    # Activity log
    with st.expander("Activity Log", expanded=False):
        if 'activity_log' in st.session_state:
            for entry in st.session_state.activity_log[-10:]:  # Last 10 entries
                st.text(f"[{entry['time']}] {entry['action']}: {entry['status']}")
    
    # Error display
    if st.session_state.get('error_messages'):
        with st.expander("⚠️ Errors", expanded=True):
            for error in st.session_state.error_messages:
                st.error(error)
            if st.button("Clear Errors"):
                st.session_state.error_messages = []
                st.rerun()
```

---

## Local Development Setup

### Project Structure

```
meeting-processor/
├── .streamlit/
│   ├── config.toml          # App configuration
│   └── secrets.toml         # Secret keys (git-ignored)
├── pages/                   # Multi-page app pages
│   ├── 1_📤_Upload.py
│   └── 2_📊_Results.py
├── src/
│   ├── __init__.py
│   ├── processor.py        # Core processing logic
│   ├── api_clients.py      # API integrations
│   └── utils.py            # Utility functions
├── requirements.txt         # Python dependencies
├── .env                    # Environment variables (git-ignored)
├── .gitignore
├── README.md
└── app.py                  # Main Streamlit app
```

### Configuration Files

**.streamlit/config.toml:**
```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
address = "localhost"
baseUrlPath = ""
enableCORS = true
enableXsrfProtection = true
maxUploadSize = 200
enableWebsocketCompression = false
headless = false

[browser]
gatherUsageStats = false
serverAddress = "localhost"
serverPort = 8501

[runner]
magicEnabled = true
installTracer = false
fixMatplotlib = true
postScriptGC = true
fastReruns = true

[client]
showErrorDetails = true
toolbarMode = "developer"  # "viewer", "minimal", or "developer"

[logger]
level = "info"
messageFormat = "%(asctime)s %(message)s"
```

**.streamlit/secrets.toml:**
```toml
# DO NOT COMMIT THIS FILE
[api_keys]
gemini_api_key = "your-gemini-api-key"
asana_token = "your-asana-token"

[database]
host = "localhost"
port = 5432
database = "meeting_db"
user = "db_user"
password = "db_password"

[app_settings]
debug_mode = true
max_retries = 3
timeout = 30
```

### Running Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up configuration
mkdir .streamlit
touch .streamlit/config.toml
touch .streamlit/secrets.toml

# 3. Run the app
streamlit run app.py

# Alternative run commands:
# Specify port
streamlit run app.py --server.port 8080

# Specify config file location
streamlit run app.py --config .streamlit/config.toml

# Run without opening browser
streamlit run app.py --server.headless true

# Development mode with auto-reload
streamlit run app.py --server.runOnSave true

# With environment variables
STREAMLIT_SERVER_PORT=8080 streamlit run app.py
```

### Environment Variables

**.env file:**
```bash
# Development environment
ENVIRONMENT=development
DEBUG=true

# API Configuration
API_TIMEOUT=30
MAX_RETRIES=3
RATE_LIMIT=100

# Feature Flags
ENABLE_CACHING=true
ENABLE_ANALYTICS=false
```

**Loading environment variables:**
```python
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Access environment variables
DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'
API_TIMEOUT = int(os.getenv('API_TIMEOUT', 30))

# Or use Streamlit secrets
DEBUG_MODE = st.secrets.get("app_settings", {}).get("debug_mode", False)
```

---

## Security Considerations

### API Key Management

```python
class SecureAPIManager:
    """Secure API key management"""
    
    @staticmethod
    def get_api_key(service_name):
        """Retrieve API key securely"""
        
        # Priority order for API keys:
        # 1. Streamlit secrets (production)
        # 2. Environment variables (development)
        # 3. Error if not found
        
        # Check Streamlit secrets first
        try:
            return st.secrets["api_keys"][service_name]
        except (KeyError, FileNotFoundError):
            pass
        
        # Check environment variables
        env_key = f"{service_name.upper()}_API_KEY"
        if env_key in os.environ:
            return os.environ[env_key]
        
        # No key found
        raise ValueError(f"API key for {service_name} not found. "
                        "Please configure in secrets.toml or environment variables.")
    
    @staticmethod
    def validate_api_key(api_key):
        """Validate API key format"""
        if not api_key or len(api_key) < 20:
            raise ValueError("Invalid API key format")
        
        # Check for common mistakes
        if api_key.startswith('your-') or api_key == 'xxx':
            raise ValueError("Please replace placeholder API key with actual key")
        
        return True
```

### Input Sanitization

```python
def sanitize_user_input(text):
    """Sanitize user input to prevent injection attacks"""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    # Limit length
    max_length = 10000
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove non-printable characters
    import string
    printable = set(string.printable)
    text = ''.join(filter(lambda x: x in printable, text))
    
    return text.strip()
```

### Secure File Handling

```python
class SecureFileHandler:
    """Handle file uploads securely"""
    
    ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.docx'}
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
    
    @classmethod
    def validate_file(cls, uploaded_file):
        """Comprehensive file validation"""
        
        # Check file size
        if uploaded_file.size > cls.MAX_FILE_SIZE:
            raise ValueError(f"File too large: {uploaded_file.size / 1024 / 1024:.2f}MB")
        
        # Check extension
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            raise ValueError(f"File type not allowed: {file_ext}")
        
        # Check MIME type matches extension
        expected_mime = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        if uploaded_file.type != expected_mime.get(file_ext):
            raise ValueError("File type mismatch detected")
        
        return True
    
    @staticmethod
    def scan_for_malware(file_content):
        """Basic malware pattern detection"""
        
        # Check for common malware signatures
        suspicious_patterns = [
            b'<%eval',  # PHP eval
            b'<script',  # JavaScript
            b'system(',  # System calls
            b'exec(',    # Exec calls
        ]
        
        file_header = file_content[:1024] if len(file_content) > 1024 else file_content
        
        for pattern in suspicious_patterns:
            if pattern in file_header:
                raise ValueError("Suspicious content detected in file")
        
        return True
```

### Session Security

```python
def implement_session_security():
    """Implement session-level security measures"""
    
    # Session timeout
    if 'last_activity' in st.session_state:
        inactive_time = time.time() - st.session_state.last_activity
        timeout_seconds = 3600  # 1 hour
        
        if inactive_time > timeout_seconds:
            st.warning("Session expired due to inactivity")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.session_state.last_activity = time.time()
    
    # Rate limiting
    if 'request_count' not in st.session_state:
        st.session_state.request_count = 0
        st.session_state.request_timestamp = time.time()
    
    # Reset counter every minute
    if time.time() - st.session_state.request_timestamp > 60:
        st.session_state.request_count = 0
        st.session_state.request_timestamp = time.time()
    
    # Check rate limit
    st.session_state.request_count += 1
    if st.session_state.request_count > 100:  # 100 requests per minute
        st.error("Rate limit exceeded. Please wait before trying again.")
        time.sleep(5)
```

### Deployment Security Checklist

```python
def security_checklist():
    """Verify security configurations before deployment"""
    
    checks = {
        "API keys in secrets": check_api_keys_secure(),
        "Debug mode disabled": not st.secrets.get("debug_mode", False),
        "HTTPS enabled": check_https_enabled(),
        "File upload limits set": check_upload_limits(),
        "Input validation active": True,  # Should always be true
        "Error details hidden": check_error_details_hidden(),
        "Telemetry disabled": check_telemetry_disabled(),
    }
    
    # Display security status
    st.sidebar.header("🔒 Security Status")
    for check, passed in checks.items():
        if passed:
            st.sidebar.success(f"✅ {check}")
        else:
            st.sidebar.error(f"❌ {check}")
    
    return all(checks.values())

def check_api_keys_secure():
    """Verify API keys are not hardcoded"""
    # Check that keys are in secrets, not in code
    try:
        st.secrets["api_keys"]
        return True
    except:
        return False

def check_error_details_hidden():
    """Check if error details are hidden in production"""
    import streamlit.config as config
    return config.get_option("client.showErrorDetails") != "stacktrace"
```

## Best Practices Summary

### Do's ✅
1. **Initialize session state** at app startup
2. **Use secrets.toml** for all sensitive data
3. **Implement proper error handling** with user-friendly messages
4. **Validate all file uploads** thoroughly
5. **Use caching** for expensive operations
6. **Provide clear progress indicators** for long-running tasks
7. **Implement rate limiting** for API calls
8. **Use callbacks** for complex state management
9. **Structure code modularly** with separate concern areas
10. **Test locally** with various file types and sizes

### Don'ts ❌
1. **Never hardcode API keys** in source code
2. **Don't store sensitive data** in session state permanently
3. **Avoid processing large files** without progress indicators
4. **Don't trust user input** without sanitization
5. **Never commit secrets.toml** to version control
6. **Don't use global variables** instead of session state
7. **Avoid blocking operations** without user feedback
8. **Don't skip file validation** for uploads
9. **Never expose debug information** in production
10. **Don't ignore error handling** for edge cases

## Deployment Checklist

- [ ] All API keys moved to secrets.toml
- [ ] Debug mode disabled in config.toml
- [ ] File upload limits configured appropriately
- [ ] Error handling implemented for all user interactions
- [ ] Session state properly initialized
- [ ] Progress indicators for all long-running operations
- [ ] Input validation and sanitization active
- [ ] Security headers configured
- [ ] Logging configured appropriately
- [ ] Performance optimization (caching) implemented
- [ ] Multi-user session handling tested
- [ ] Rate limiting implemented for API calls
- [ ] Graceful error messages for all failure modes
- [ ] Documentation updated with setup instructions
- [ ] Requirements.txt up to date with all dependencies