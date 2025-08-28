# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered Streamlit application for Opus Behavioral Health that converts meeting transcripts into Asana tasks using Google Gemini AI. The system processes PDFs from tools like Gong, Grain, or Otter.ai and intelligently creates actionable tasks in appropriate Asana projects based on meeting type and context.

## Common Development Commands

### Running the Application
```bash
streamlit run app.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Testing Connections
The app has built-in connection testing in the UI sidebar. API connections can be programmatically tested:
```python
# Asana connection test
asana_client.test_connection()
```

### Running Tests
```bash
python -m pytest tests/
```
Note: Test directory structure needs to be created as tests are not yet implemented.

## Architecture & Key Components

### Core Flow
1. **app.py** - Main Streamlit interface that orchestrates the workflow:
   - Loads configurations from JSON files (customers, departments, projects)
   - Handles meeting type selection (sales_call, internal_meeting, project_meeting)
   - Routes to appropriate Asana project based on selection
   - Manages session state for multi-step workflow

2. **src/pdf_processor.py** - Robust PDF text extraction with fallback methods:
   - Primary: PyMuPDF (fastest)
   - Fallback 1: pdfplumber (better for complex layouts)
   - Fallback 2: PyPDF2 (most compatible)
   - Returns extracted text with page markers

3. **src/gemini_analyzer.py** - AI analysis with department/context-specific prompts:
   - Routes to different prompt methods based on meeting type and department
   - Department-specific prompts: Sales, Onboarding, Support Leadership and Ops
   - Project-specific prompts: Finpay/LSQ integration meetings
   - Returns structured JSON with action items, participants, decisions, and summary

4. **src/asana_client.py** - Asana API integration:
   - Creates tasks with enhanced descriptions including meeting context
   - Supports section creation for meeting organization
   - Handles timestamps and recording links
   - Batch task creation with error handling

### Configuration Files

- **customers.json** - Maps customer names to Asana project IDs for sales calls
- **departments.json** - Maps internal departments to Asana projects:
  - Onboarding: 1211116494194833
  - Operations: 1211106531309164
  - Sales: 1211124207848026
  - Support Leadership and Ops: 1211163265698003
- **projects.json** - Maps special projects (Finpay, LSQ) to Asana projects
- **existing_customers.json** - Maps existing customers to their escalation projects with custom context

### Meeting Type and Prompt Routing

The system uses intelligent routing in `gemini_analyzer.py` based on meeting type:

**Internal Meetings** - Checks department name (case-insensitive):
- "onboarding" → `_create_onboarding_prompt()`
- "sales" → `_create_sales_dept_prompt()`
- Contains "support" → `_create_support_prompt()`
- Default → `_create_internal_prompt()`

**Project Meetings**:
- Contains "finpay" or "lsq" → `_create_finpay_lsq_prompt()`

**Existing Customers**:
- Routes to `_create_existing_customer_prompt()`
- Injects customer-specific context from `existing_customers.json`
- Focuses on escalation handling and task delegation

### Key Context for Support Department

When working with Support Leadership and Ops:
- John: Support Lead
- Adi Tiwari: VP of Operations (oversees department)
- Hector Fraginals: CTO (engineering escalations)
- Janelle: Lead Onboarding Director
- Vendors:
  - Dosespot: E-prescribing/medication management
  - LeadSquared (LSQ): CRM provider
  - Imagine/Opus RCM: Revenue cycle management

### Key Context for Existing Customers

For existing customer escalations:
- Default contacts: Janelle or Laura (onboarding team)
- Adi Tiwari: VP of Ops/Account Executive handling escalations
- Focus: Delegation of resolution tasks while maintaining customer relationship
- Customer-specific context stored in `existing_customers.json`

### Environment Variables

Required in `.env`:
- `ASANA_ACCESS_TOKEN` - Asana Personal Access Token
- `GEMINI_API_KEY` - Google Gemini API key

Optional:
- `DEBUG_MODE` - Set to "true" for verbose logging
- `MAX_FILE_SIZE_MB` - Maximum PDF size (default: 50)

### Adding New Departments or Customers

1. Edit the appropriate JSON config file
2. For departments with custom prompts, add a new method in `gemini_analyzer.py`:
   - Follow pattern: `_create_[department]_prompt(self, transcript: str, additional_context: str)`
   - Update routing logic in `analyze_transcript()` method
3. Restart the application to load new configurations

### Quick Task Feature

The app supports "Quick Tasks" mode for creating tasks without transcript processing:
- Interprets natural language task descriptions
- Can handle multiple tasks separated by newlines or semicolons
- Uses AI to structure tasks appropriately

### Session State Management

The app uses Streamlit session state to track:
- `meeting_type`: sales_call, internal_meeting, or project_meeting
- `extracted_text`: PDF text content
- `action_items`: AI-extracted tasks
- `recording_link`: Optional meeting recording URL
- `quick_task_mode`: Toggle for quick task creation

### Error Handling Patterns

- PDF extraction uses sequential fallback methods
- API calls wrapped in try-except with detailed logging
- User-friendly error messages in UI
- Connection testing before operations