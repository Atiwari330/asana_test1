# Gmail API Integration Research for Automated Email-to-Task System (2025)

## Executive Summary

This research provides a comprehensive guide for implementing Gmail API integration in your existing Streamlit application. Based on the latest 2025 documentation and best practices, this report covers setup, authentication, monitoring approaches, and complete implementation patterns.

## 1. Gmail API Setup & Authentication (2025)

### Latest Setup Process

**Step 1: Google Cloud Console Setup**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one (can use same project as Gemini API)
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it

**Step 2: OAuth 2.0 Configuration**
1. Go to "APIs & Services" > "OAuth consent screen"
2. Configure app information:
   - App name: Your application name
   - User support email: Your contact email
   - Developer contact: Your email
3. Add scopes (see scopes section below)
4. Add test users if in testing mode

**Step 3: Create Credentials**
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Choose "Desktop application" for development
4. Download the `credentials.json` file

### OAuth 2.0 vs Service Account Authentication

| Authentication Type | Use Case | Pros | Cons | Recommendation |
|---------------------|----------|------|------|----------------|
| OAuth 2.0 | User consent required | Secure, user-controlled access | Requires user interaction | **Recommended** for your use case |
| Service Account | Domain-wide access | No user interaction | Only for Google Workspace domains | Not suitable for external Gmail |

**For your use case**: OAuth 2.0 is the correct choice since you're accessing external customer Gmail accounts.

### Required Scopes

```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',     # Read emails
    'https://www.googleapis.com/auth/gmail.modify',       # Modify labels (mark as read)
    # Optional: 'https://mail.google.com/'                # Full access if needed
]
```

### Token Storage Best Practices

```python
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def authenticate_gmail():
    """Authenticate and return Gmail service object"""
    creds = None
    token_file = 'token.pickle'
    
    # Load existing token
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)
```

## 2. Email Monitoring Approaches Comparison

| Approach | Pros | Cons | Complexity | Recommended For |
|----------|------|------|------------|-----------------|
| **Push Notifications** | Real-time, efficient, no polling overhead | Complex setup, requires webhook infrastructure | High | Production apps with high email volume |
| **Polling** | Simple to implement, no webhook needed | Higher latency, API quota usage | Low | Development and moderate volume use |

### Push Notifications Setup (Advanced)

**Requirements:**
- Google Cloud Pub/Sub setup
- Webhook endpoint (HTTPS required)
- Domain verification

**Process:**
1. Create Pub/Sub topic and subscription
2. Set up webhook endpoint
3. Grant Gmail API push permissions
4. Create watch request

```python
# Push notification setup (advanced)
def setup_gmail_watch(service, topic_name):
    """Set up Gmail push notifications"""
    request_body = {
        'labelIds': ['INBOX'],
        'topicName': f'projects/{PROJECT_ID}/topics/{topic_name}'
    }
    
    return service.users().watch(userId='me', body=request_body).execute()
```

### Polling Approach (Recommended for Start)

**Advantages for your use case:**
- Simpler implementation
- No webhook infrastructure needed
- Easier to test and debug
- Works well with Streamlit

**Optimal polling intervals:**
- Development: 1-5 minutes
- Production: 30 seconds to 2 minutes
- Consider API quotas (see section 7)

```python
import time
from datetime import datetime, timedelta

def poll_gmail_for_new_emails(service, last_check_time):
    """Poll Gmail for new emails since last check"""
    query = f'after:{last_check_time.strftime("%Y/%m/%d")}'
    
    # Add domain filter
    domain_filter = ' OR '.join([f'from:*@{domain}' for domain in MONITORED_DOMAINS])
    query += f' AND ({domain_filter})'
    
    try:
        results = service.users().messages().list(
            userId='me', 
            q=query,
            maxResults=50
        ).execute()
        
        messages = results.get('messages', [])
        return messages
    except Exception as error:
        print(f'Error polling Gmail: {error}')
        return []
```

## 3. Email Processing Implementation

### Complete Email Retrieval

```python
import base64
from email.mime.text import MIMEText
import html
import re

def get_full_email_thread(service, message_id):
    """Retrieve complete email thread with all context"""
    try:
        # Get the message
        message = service.users().messages().get(
            userId='me', 
            id=message_id,
            format='full'
        ).execute()
        
        # Get thread if it exists
        thread_id = message['threadId']
        thread = service.users().threads().get(
            userId='me',
            id=thread_id
        ).execute()
        
        return process_email_thread(thread)
        
    except Exception as error:
        print(f'Error retrieving email: {error}')
        return None

def process_email_thread(thread):
    """Process email thread to extract useful information"""
    emails = []
    
    for message in thread['messages']:
        email_data = extract_email_data(message)
        emails.append(email_data)
    
    return {
        'thread_id': thread['id'],
        'emails': emails,
        'participant_count': len(set(email['sender'] for email in emails)),
        'last_message_date': emails[-1]['date'] if emails else None
    }

def extract_email_data(message):
    """Extract data from individual email message"""
    payload = message['payload']
    headers = payload.get('headers', [])
    
    # Extract headers
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
    recipient = next((h['value'] for h in headers if h['name'] == 'To'), '')
    date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
    
    # Extract body
    body = extract_email_body(payload)
    
    return {
        'id': message['id'],
        'subject': subject,
        'sender': sender,
        'recipient': recipient,
        'date': date,
        'body': body,
        'snippet': message.get('snippet', ''),
        'labels': message.get('labelIds', [])
    }

def extract_email_body(payload):
    """Extract email body from payload"""
    body = ""
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                break
            elif part['mimeType'] == 'text/html':
                data = part['body']['data']
                html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                # Convert HTML to text (basic)
                body = html.unescape(re.sub('<[^<]+?>', '', html_body))
    else:
        if payload['body'].get('data'):
            body = base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8')
    
    return body.strip()
```

### Domain Filtering

```python
def should_process_email(sender_email, monitored_domains):
    """Check if email should be processed based on sender domain"""
    sender_domain = sender_email.split('@')[-1].lower()
    return any(domain.lower() in sender_domain for domain in monitored_domains)

# Configuration
MONITORED_DOMAINS = [
    'customerdomain.com',
    'anotherclient.com',
    'partner.org'
]
```

## 4. Streamlit Integration Patterns

### Session State Management

```python
import streamlit as st
from datetime import datetime, timedelta

# Initialize session state
if 'gmail_service' not in st.session_state:
    st.session_state.gmail_service = None
if 'last_email_check' not in st.session_state:
    st.session_state.last_email_check = datetime.now() - timedelta(days=1)
if 'processed_emails' not in st.session_state:
    st.session_state.processed_emails = set()
```

### OAuth Flow in Streamlit

```python
def streamlit_gmail_auth():
    """Handle Gmail authentication in Streamlit"""
    
    if st.session_state.gmail_service is None:
        st.write("Gmail authentication required")
        
        if st.button("Authenticate Gmail"):
            try:
                service = authenticate_gmail()
                st.session_state.gmail_service = service
                st.success("Gmail authenticated successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Authentication failed: {e}")
    else:
        st.success("Gmail is authenticated")
        
        if st.button("Refresh Authentication"):
            st.session_state.gmail_service = None
            st.rerun()

def main():
    st.title("Email-to-Task Automation")
    
    # Authentication
    streamlit_gmail_auth()
    
    if st.session_state.gmail_service:
        # Show monitoring interface
        show_monitoring_interface()
```

### Background Processing Options

**Option 1: Manual Refresh (Simplest)**
```python
def show_monitoring_interface():
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write(f"Last check: {st.session_state.last_email_check}")
    
    with col2:
        if st.button("Check for New Emails"):
            check_and_process_emails()

def check_and_process_emails():
    """Process new emails and create tasks"""
    service = st.session_state.gmail_service
    
    with st.spinner("Checking for new emails..."):
        new_emails = poll_gmail_for_new_emails(
            service, 
            st.session_state.last_email_check
        )
        
        if new_emails:
            st.write(f"Found {len(new_emails)} new emails")
            for msg_id in [email['id'] for email in new_emails]:
                if msg_id not in st.session_state.processed_emails:
                    process_single_email(service, msg_id)
                    st.session_state.processed_emails.add(msg_id)
        
        st.session_state.last_email_check = datetime.now()
```

**Option 2: Auto-refresh with st.rerun() (Moderate)**
```python
import time

def auto_check_emails():
    """Auto-check emails every 60 seconds"""
    if 'last_auto_check' not in st.session_state:
        st.session_state.last_auto_check = datetime.now()
    
    if datetime.now() - st.session_state.last_auto_check > timedelta(seconds=60):
        check_and_process_emails()
        st.session_state.last_auto_check = datetime.now()
        time.sleep(1)
        st.rerun()
```

### Monitoring Status Display

```python
def show_monitoring_status():
    """Display current monitoring status"""
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Processed Emails", 
            len(st.session_state.processed_emails)
        )
    
    with col2:
        st.metric(
            "Monitored Domains", 
            len(MONITORED_DOMAINS)
        )
    
    with col3:
        minutes_since_check = int(
            (datetime.now() - st.session_state.last_email_check).total_seconds() / 60
        )
        st.metric("Minutes Since Last Check", minutes_since_check)
    
    # Configuration
    st.subheader("Monitoring Configuration")
    
    # Domain management
    new_domain = st.text_input("Add monitored domain:")
    if st.button("Add Domain") and new_domain:
        if new_domain not in MONITORED_DOMAINS:
            MONITORED_DOMAINS.append(new_domain)
            st.success(f"Added {new_domain}")
            st.rerun()
    
    # Display current domains
    for domain in MONITORED_DOMAINS:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(domain)
        with col2:
            if st.button(f"Remove", key=f"remove_{domain}"):
                MONITORED_DOMAINS.remove(domain)
                st.rerun()
```

## 5. Libraries and Dependencies (2025 Versions)

### Requirements.txt

```txt
# Core dependencies
streamlit>=1.40.0
google-api-python-client>=2.140.0
google-auth-httplib2>=0.2.0
google-auth-oauthlib>=1.2.0
google-auth>=2.30.0

# Existing dependencies (your current stack)
google-genai>=0.1.0
asana>=5.1.0

# Email processing
beautifulsoup4>=4.12.0
html2text>=2024.2.26

# Background task scheduling (if using polling)
APScheduler>=3.10.0

# Data handling
python-dotenv>=1.0.0
pandas>=2.2.0

# Optional: For push notifications (advanced)
google-cloud-pubsub>=2.23.0
flask>=3.0.0
```

### Installation Command

```bash
pip install streamlit google-api-python-client google-auth-httplib2 google-auth-oauthlib beautifulsoup4 APScheduler python-dotenv
```

## 6. Complete Working Examples

### Main Application Structure

```python
import streamlit as st
import os
from datetime import datetime, timedelta
import json
import pickle
from gmail_api import GmailMonitor
from asana_integration import create_asana_task
from gemini_analysis import analyze_email_content

# Configuration
CONFIG_FILE = 'email_config.json'
TOKEN_FILE = 'gmail_token.pickle'

def load_config():
    """Load configuration from JSON file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'monitored_domains': [],
        'asana_project_mapping': {},
        'email_processing_rules': []
    }

def save_config(config):
    """Save configuration to JSON file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, indent=2, fp=f)

class EmailToTaskProcessor:
    def __init__(self):
        self.config = load_config()
        self.gmail_monitor = GmailMonitor()
        
    def process_email_to_task(self, email_data):
        """Process email and create Asana task"""
        try:
            # Analyze email content with Gemini
            analysis = analyze_email_content(
                email_data['subject'],
                email_data['body'],
                email_data['sender']
            )
            
            # Determine project based on sender domain
            sender_domain = email_data['sender'].split('@')[-1]
            project_id = self.config['asana_project_mapping'].get(
                sender_domain, 
                'default_project'
            )
            
            # Create Asana task
            task_data = {
                'name': f"Email: {email_data['subject'][:50]}...",
                'notes': f"From: {email_data['sender']}\n\n{analysis['summary']}\n\nAction Items:\n{analysis['action_items']}",
                'projects': [project_id],
                'due_on': analysis.get('suggested_due_date'),
                'assignee': analysis.get('suggested_assignee')
            }
            
            task = create_asana_task(task_data)
            return task
            
        except Exception as e:
            st.error(f"Error processing email to task: {e}")
            return None

def main():
    st.set_page_config(
        page_title="Email-to-Task Automation",
        page_icon="📧",
        layout="wide"
    )
    
    st.title("📧 Email-to-Task Automation System")
    
    # Initialize processor
    if 'processor' not in st.session_state:
        st.session_state.processor = EmailToTaskProcessor()
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard", "Configuration", "Email Monitor", "Task History"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Configuration":
        show_configuration()
    elif page == "Email Monitor":
        show_email_monitor()
    elif page == "Task History":
        show_task_history()

def show_dashboard():
    """Main dashboard view"""
    st.header("📊 Dashboard")
    
    # Authentication status
    auth_status = st.session_state.processor.gmail_monitor.check_authentication()
    
    if not auth_status:
        st.warning("Gmail authentication required")
        if st.button("Authenticate Gmail"):
            st.session_state.processor.gmail_monitor.authenticate()
            st.rerun()
    else:
        st.success("Gmail authenticated ✓")
        
        # Quick stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Emails Processed Today", "12")  # Replace with actual data
        with col2:
            st.metric("Tasks Created", "8")  # Replace with actual data
        with col3:
            st.metric("Active Domains", len(st.session_state.processor.config['monitored_domains']))
        
        # Recent activity
        st.subheader("Recent Activity")
        # Add activity feed here

if __name__ == "__main__":
    main()
```

### Gmail Monitor Class

```python
import pickle
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta

class GmailMonitor:
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None
        
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        return True
    
    def check_authentication(self):
        """Check if authentication is valid"""
        try:
            if self.service:
                self.service.users().getProfile(userId='me').execute()
                return True
        except:
            pass
        return False
    
    def get_new_emails(self, domains, since_date=None):
        """Get new emails from specified domains"""
        if not self.service:
            raise Exception("Not authenticated")
        
        if not since_date:
            since_date = datetime.now() - timedelta(hours=24)
        
        # Build query
        date_query = f'after:{since_date.strftime("%Y/%m/%d")}'
        domain_query = ' OR '.join([f'from:*@{domain}' for domain in domains])
        query = f'{date_query} AND ({domain_query})'
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            return [self.get_message_details(msg['id']) for msg in messages]
            
        except Exception as error:
            raise Exception(f'Error fetching emails: {error}')
    
    def get_message_details(self, message_id):
        """Get detailed information about a specific message"""
        message = self.service.users().messages().get(
            userId='me', 
            id=message_id,
            format='full'
        ).execute()
        
        return extract_email_data(message)  # Use function from previous section
```

## 7. API Quotas and Rate Limits (2025)

### Current Gmail API Limits

| Limit Type | Value | Notes |
|------------|-------|-------|
| Per-project rate limit | 1,200,000 quota units/minute | Shared across all users |
| Per-user rate limit | 15,000 quota units/user/minute | Per individual Gmail account |
| Per-user burst limit | 250 quota units/user/second | Short bursts allowed |

### Quota Units per Method

| Method | Quota Units | Usage Notes |
|--------|-------------|-------------|
| `messages.list` | 5 | Listing emails |
| `messages.get` | 5 | Getting email details |
| `history.list` | 2 | Most efficient for polling |
| `messages.send` | 100 | Sending emails |
| `threads.get` | 5 | Getting thread details |

### Rate Limiting Best Practices

```python
import time
import random
from googleapiclient.errors import HttpError

def make_api_request_with_backoff(api_call, max_retries=5):
    """Make API request with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return api_call()
        except HttpError as error:
            if error.resp.status in [403, 429]:  # Rate limit exceeded
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limit hit, waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                raise error
    
    raise Exception(f"Max retries exceeded")

# Usage
def safe_get_messages(service, query):
    return make_api_request_with_backoff(
        lambda: service.users().messages().list(userId='me', q=query).execute()
    )
```

### Monitoring Usage

```python
def track_api_usage():
    """Track API usage for quota monitoring"""
    # You can implement a simple counter
    if 'api_calls_today' not in st.session_state:
        st.session_state.api_calls_today = 0
        st.session_state.last_reset = datetime.now().date()
    
    # Reset counter daily
    if datetime.now().date() > st.session_state.last_reset:
        st.session_state.api_calls_today = 0
        st.session_state.last_reset = datetime.now().date()
    
    st.session_state.api_calls_today += 5  # Adjust based on API call
    
    # Display usage
    st.sidebar.metric("API Calls Today", st.session_state.api_calls_today)
```

## 8. Security & Best Practices

### Secure Token Storage

```python
import os
import json
from cryptography.fernet import Fernet

class SecureTokenStorage:
    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self):
        """Get encryption key from environment or create new one"""
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            print(f"Generated new encryption key: {key.decode()}")
            print("Store this in your environment variables as ENCRYPTION_KEY")
        return key if isinstance(key, bytes) else key.encode()
    
    def save_token(self, token_data, filename):
        """Save encrypted token"""
        encrypted_data = self.cipher.encrypt(json.dumps(token_data).encode())
        with open(filename, 'wb') as f:
            f.write(encrypted_data)
    
    def load_token(self, filename):
        """Load and decrypt token"""
        try:
            with open(filename, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except:
            return None
```

### Environment Configuration

```python
# .env file
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.pickle
ENCRYPTION_KEY=your_encryption_key_here
ASANA_ACCESS_TOKEN=your_asana_token
GOOGLE_GEMINI_API_KEY=your_gemini_key

# Monitored domains (JSON format)
MONITORED_DOMAINS=["customerdomain.com", "partnerdomain.com"]

# Asana project mappings
ASANA_PROJECT_MAPPING={"customerdomain.com": "project_id_1", "partnerdomain.com": "project_id_2"}
```

### GDPR/Privacy Considerations

```python
def privacy_compliant_processing():
    """Ensure privacy-compliant email processing"""
    
    privacy_settings = {
        'data_retention_days': 30,  # Delete processed emails after 30 days
        'anonymize_sender': True,   # Hash sender emails
        'log_minimal_data': True,   # Only log essential information
        'user_consent_required': True
    }
    
    return privacy_settings

def anonymize_email_data(email_data):
    """Anonymize sensitive email data"""
    import hashlib
    
    # Hash sender email
    email_data['sender_hash'] = hashlib.sha256(
        email_data['sender'].encode()
    ).hexdigest()[:16]
    
    # Remove full sender email
    del email_data['sender']
    
    return email_data
```

## 9. Architecture Recommendations

### Recommended Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │  Gmail API       │    │  Background     │
│   Frontend      │◄──►│  Integration     │◄──►│  Scheduler      │
│                 │    │                  │    │  (APScheduler)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         ▼                        ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Session       │    │  Email           │    │  Task Queue     │
│   Management    │    │  Processing      │    │  (JSON/SQLite)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         └────────────────────────┼───────────────────────┘
                                  ▼
                      ┌──────────────────┐
                      │  Gemini AI       │
                      │  Analysis        │
                      └──────────────────┘
                                  │
                                  ▼
                      ┌──────────────────┐
                      │  Asana API       │
                      │  Task Creation   │
                      └──────────────────┘
```

### Background Task Scheduling (Production)

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import threading

class EmailMonitorService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.gmail_monitor = GmailMonitor()
        self.processor = EmailToTaskProcessor()
        
    def start_monitoring(self, interval_minutes=2):
        """Start background email monitoring"""
        self.scheduler.add_job(
            func=self._check_emails_job,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='email_check_job',
            name='Check Gmail for new emails',
            replace_existing=True
        )
        
        self.scheduler.start()
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        if self.scheduler.running:
            self.scheduler.shutdown()
    
    def _check_emails_job(self):
        """Background job to check for new emails"""
        try:
            # Get configuration
            config = load_config()
            domains = config.get('monitored_domains', [])
            
            if not domains:
                return
            
            # Check for new emails
            new_emails = self.gmail_monitor.get_new_emails(
                domains, 
                since_date=datetime.now() - timedelta(minutes=5)
            )
            
            # Process each email
            for email in new_emails:
                self.processor.process_email_to_task(email)
                
        except Exception as e:
            print(f"Background email check failed: {e}")

# Streamlit integration
if 'monitor_service' not in st.session_state:
    st.session_state.monitor_service = EmailMonitorService()

# Control buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("Start Monitoring"):
        st.session_state.monitor_service.start_monitoring()
        st.success("Background monitoring started")

with col2:
    if st.button("Stop Monitoring"):
        st.session_state.monitor_service.stop_monitoring()
        st.success("Background monitoring stopped")
```

## 10. Error Handling & Monitoring

### Comprehensive Error Handling

```python
import logging
from functools import wraps

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_automation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def handle_gmail_errors(func):
    """Decorator for handling Gmail API errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HttpError as error:
            if error.resp.status == 401:
                logger.error("Authentication error - token expired")
                st.error("Authentication expired. Please re-authenticate.")
            elif error.resp.status == 403:
                logger.error("Rate limit exceeded")
                st.warning("Rate limit exceeded. Please wait before trying again.")
            elif error.resp.status == 429:
                logger.error("Too many requests")
                st.warning("Too many requests. Implement exponential backoff.")
            else:
                logger.error(f"Gmail API error: {error}")
                st.error(f"API error: {error}")
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            st.error(f"Unexpected error: {e}")
        return None
    return wrapper

@handle_gmail_errors
def safe_gmail_operation(operation):
    """Safely execute Gmail operations"""
    return operation()
```

### Health Monitoring

```python
def system_health_check():
    """Perform system health checks"""
    health_status = {
        'gmail_auth': False,
        'asana_auth': False,
        'gemini_auth': False,
        'last_email_check': None,
        'errors_last_hour': 0
    }
    
    try:
        # Check Gmail authentication
        if st.session_state.gmail_service:
            st.session_state.gmail_service.users().getProfile(userId='me').execute()
            health_status['gmail_auth'] = True
    except:
        pass
    
    # Display health status
    st.subheader("System Health")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "🟢" if health_status['gmail_auth'] else "🔴"
        st.write(f"{status} Gmail API")
    
    with col2:
        status = "🟢" if health_status['asana_auth'] else "🔴"
        st.write(f"{status} Asana API")
    
    with col3:
        status = "🟢" if health_status['gemini_auth'] else "🔴"
        st.write(f"{status} Gemini API")
    
    return health_status
```

## 11. Deployment Considerations

### Environment Setup

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Gmail API
    GMAIL_CREDENTIALS_FILE = os.getenv('GMAIL_CREDENTIALS_FILE', 'credentials.json')
    GMAIL_TOKEN_FILE = os.getenv('GMAIL_TOKEN_FILE', 'token.pickle')
    
    # Asana
    ASANA_ACCESS_TOKEN = os.getenv('ASANA_ACCESS_TOKEN')
    
    # Gemini
    GOOGLE_GEMINI_API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')
    
    # Email monitoring
    MONITORING_INTERVAL_MINUTES = int(os.getenv('MONITORING_INTERVAL_MINUTES', '2'))
    MAX_EMAILS_PER_CHECK = int(os.getenv('MAX_EMAILS_PER_CHECK', '50'))
    
    # Security
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    
    @classmethod
    def validate(cls):
        """Validate all required environment variables"""
        required_vars = [
            'ASANA_ACCESS_TOKEN',
            'GOOGLE_GEMINI_API_KEY'
        ]
        
        missing = [var for var in required_vars if not getattr(cls, var)]
        
        if missing:
            raise Exception(f"Missing required environment variables: {', '.join(missing)}")
```

### Docker Deployment (Optional)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Summary & Next Steps

### Implementation Timeline

**Phase 1 (Week 1): Basic Setup**
- Set up Google Cloud project and Gmail API
- Implement basic authentication
- Create simple email polling mechanism

**Phase 2 (Week 2): Core Features**
- Implement email processing and filtering
- Add Gemini AI integration for email analysis
- Create basic Asana task creation

**Phase 3 (Week 3): Streamlit Integration**
- Build Streamlit interface
- Add configuration management
- Implement session state handling

**Phase 4 (Week 4): Production Features**
- Add error handling and logging
- Implement background monitoring
- Add security features

### Key Recommendations

1. **Start with polling approach** - simpler to implement and debug
2. **Use the same Google Cloud project** as your Gemini API for consistency
3. **Implement proper error handling** from the beginning
4. **Store sensitive data securely** using environment variables
5. **Monitor API quotas** to avoid hitting limits
6. **Test with a small number of domains** initially

### Estimated Costs

- **Gmail API**: Free (within quotas)
- **Google Cloud Project**: Free tier available
- **Additional quota**: Contact Google for pricing if needed

### Support Resources

- [Gmail API Documentation](https://developers.google.com/workspace/gmail/api)
- [Google API Python Client](https://googleapis.github.io/google-api-python-client/)
- [Streamlit Documentation](https://docs.streamlit.io/)

This research provides a comprehensive foundation for implementing your Gmail API integration. The polling approach is recommended for initial implementation, with the option to upgrade to push notifications for production use.