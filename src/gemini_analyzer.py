"""
Gemini AI Analyzer Module
Uses Google Gemini to analyze transcripts and extract action items
"""

import os
import json
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class ActionItem(BaseModel):
    """Model for an action item extracted from transcript"""
    title: str = Field(description="Brief, actionable task description")
    description: str = Field(description="Additional context and details about the task")
    priority: Optional[str] = Field(default="medium", description="Priority level: low, medium, or high")
    mentioned_by: Optional[str] = Field(default=None, description="Person who mentioned or owns this action")
    timestamp: Optional[str] = Field(default=None, description="Timestamp in the recording where this was discussed (format: MM:SS or HH:MM:SS)")
    is_question: bool = Field(default=False, description="Whether this is a customer question that needs answering")


class TranscriptAnalysis(BaseModel):
    """Model for complete transcript analysis"""
    action_items: List[ActionItem] = Field(description="List of action items extracted from the transcript")
    summary: str = Field(description="Brief summary of the meeting")
    participants: List[str] = Field(description="List of participants identified in the transcript")
    key_decisions: List[str] = Field(description="Key decisions made during the meeting")
    meeting_title: str = Field(description="Concise title for the meeting (10-30 characters)")


class GeminiAnalyzer:
    """Analyze transcripts using Google Gemini AI"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-pro"):
        """
        Initialize Gemini analyzer
        
        Args:
            api_key: Gemini API key (if None, will use environment variable)
            model: Model to use ("gemini-2.5-pro", "gemini-2.5-flash", "gemini-1.5-flash", etc.)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable.")
        
        # Initialize client
        self.client = genai.Client(api_key=self.api_key)
        self.model = model
        
        logger.info(f"Initialized Gemini analyzer with model: {model}")
    
    def analyze_transcript(self, 
                          transcript: str, 
                          customer_name: str,
                          additional_context: str = "",
                          meeting_type: str = "sales_call",
                          recording_link: str = "",
                          department: str = "",
                          project: str = "") -> TranscriptAnalysis:
        """
        Analyze transcript and extract structured action items
        
        Args:
            transcript: The transcript text to analyze
            customer_name: Name of the customer/project
            additional_context: Any additional context about the meeting
            meeting_type: Type of meeting ("sales_call", "internal_meeting", or "project_meeting")
            department: Department name for internal meetings
            project: Project name for project meetings
            
        Returns:
            TranscriptAnalysis object with extracted data
        """
        # Create the analysis prompt based on meeting type
        if meeting_type == "internal_meeting":
            # Check for department-specific prompts
            if department.lower() == "onboarding":
                prompt = self._create_onboarding_prompt(transcript, additional_context)
            elif department.lower() == "sales":
                prompt = self._create_sales_dept_prompt(transcript, additional_context)
            elif "support" in department.lower():
                prompt = self._create_support_prompt(transcript, additional_context)
            else:
                prompt = self._create_internal_prompt(transcript, additional_context)
        elif meeting_type == "project_meeting":
            # Check for project-specific prompts
            if "finpay" in project.lower() or "lsq" in project.lower():
                prompt = self._create_finpay_lsq_prompt(transcript, additional_context)
            else:
                # Create a generic project prompt if needed in the future
                prompt = self._create_finpay_lsq_prompt(transcript, additional_context)  # Default to Finpay for now
        elif meeting_type == "existing_customer":
            # Use existing customer escalation prompt
            prompt = self._create_existing_customer_prompt(transcript, customer_name, additional_context)
        else:
            prompt = self._create_sales_prompt(transcript, customer_name, additional_context)
        
        try:
            # Generate response with structured output using manual schema
            # Convert Pydantic model to schema dict for compatibility
            schema = {
                "type": "object",
                "properties": {
                    "action_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "priority": {"type": "string"},
                                "mentioned_by": {"type": "string"},
                                "timestamp": {"type": "string"},
                                "is_question": {"type": "boolean"}
                            },
                            "required": ["title", "description"]
                        }
                    },
                    "summary": {"type": "string"},
                    "participants": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "key_decisions": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "meeting_title": {"type": "string"}
                },
                "required": ["action_items", "summary", "participants", "key_decisions", "meeting_title"]
            }
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.1,  # Low temperature for consistent extraction
                    max_output_tokens=8192  # Increased for Sales Sync meetings with many action items
                )
            )
            
            # Parse the response
            if hasattr(response, 'text') and response.text:
                try:
                    result_json = json.loads(response.text)
                except json.JSONDecodeError as json_error:
                    logger.error(f"JSON parsing error: {json_error}")
                    logger.error(f"Response text (first 500 chars): {response.text[:500]}")
                    logger.error(f"Response text (around error position): {response.text[max(0, json_error.pos-100):min(len(response.text), json_error.pos+100)]}")
                    
                    # Try to clean the response and parse again
                    try:
                        # Remove any trailing commas and fix common JSON issues
                        cleaned_text = response.text.strip()
                        # Try to fix unterminated strings by escaping quotes
                        cleaned_text = cleaned_text.replace('\\"', '\\\"')
                        result_json = json.loads(cleaned_text)
                        logger.info("Successfully parsed after cleaning")
                    except:
                        # If still failing, return partial analysis
                        logger.error("Could not parse JSON even after cleaning")
                        return TranscriptAnalysis(
                            action_items=[],
                            summary="Error parsing AI response - JSON formatting issue",
                            participants=[],
                            key_decisions=[],
                            meeting_title="Sales Sync Meeting"
                        )
                
                # Convert to Pydantic model
                analysis = TranscriptAnalysis(
                    action_items=[ActionItem(**item) for item in result_json.get('action_items', [])],
                    summary=result_json.get('summary', ''),
                    participants=result_json.get('participants', []),
                    key_decisions=result_json.get('key_decisions', []),
                    meeting_title=result_json.get('meeting_title', 'Meeting')
                )
            else:
                # Fallback empty analysis
                analysis = TranscriptAnalysis(
                    action_items=[],
                    summary="Unable to extract content",
                    participants=[],
                    key_decisions=[],
                    meeting_title="Meeting"
                )
            
            logger.info(f"Successfully analyzed transcript. Found {len(analysis.action_items)} action items.")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            # Return empty analysis on error
            return TranscriptAnalysis(
                action_items=[],
                summary="Error analyzing transcript",
                participants=[],
                key_decisions=[],
                meeting_title="Meeting"
            )
    
    def _create_sales_prompt(self, transcript: str, customer_name: str, additional_context: str) -> str:
        """
        Create the prompt for sales call transcripts
        
        Args:
            transcript: The transcript text
            customer_name: Customer/project name
            additional_context: Additional context including customer-specific information
            
        Returns:
            Formatted prompt string for sales calls
        """
        # Build customer context section if provided
        customer_context_section = ""
        if additional_context and additional_context.strip():
            customer_context_section = f"""
Customer-Specific Context:
{additional_context}
"""
        
        prompt = f"""<context>
You are analyzing a sales call transcript for {customer_name}, a prospect/customer of Opus.

About the presenter: Adi Tiwari, VP of Operations and Sales Executive at Opus, a software company specializing in behavioral health software.

Opus Products:
- EHR (Electronic Health Record) - Main product
- CRM (Customer Relationship Management) - White-labeled
- RCM (Revenue Cycle Management) - White-labeled
- Opus Kiosk
- AI Scribe Co-pilot

Typical attendees from prospects:
- Providers/Therapists
- Billers
- Front desk staff
- Admins
- Owners/Operators
{customer_context_section}
</context>

<transcript>
{transcript}
</transcript>

<instructions>
CONTEXT: You are analyzing a sales call where Adi Tiwari is the Opus sales executive/presenter.

Analyze this sales call transcript and extract:
1. Action items - ONLY tasks that Adi Tiwari specifically needs to complete
2. A brief summary of the demo/call
3. List of participants (names and roles if mentioned)
4. Key decisions or buying signals
5. Meeting title - Create a concise descriptive title (10-30 chars) that captures the essence of this call:
   - Examples: "Initial Demo", "Follow-up - Billing", "Technical Deep Dive", "Pricing Discussion", "Implementation Planning"
   - Focus on the main topic or stage of the sales process

For action items, focus on:
- Questions that need answers (technical, pricing, compliance, integration)
- Follow-up materials to send
- Next steps discussed
- Features or modules to demonstrate further
- Implementation or timeline discussions

TIMESTAMP EXTRACTION:
- Look for timestamps in the transcript (format: MM:SS or HH:MM:SS)
- Record the timestamp when each action item or question was discussed
- If multiple timestamps, use the first clear mention
- If no timestamp found, leave as null

CUSTOMER QUESTIONS:
- Mark items as questions (is_question: true) when:
  - Customer explicitly asks "What about...?", "How does...?", "Can you...?"
  - Customer requests information or clarification
  - Topic requires follow-up research or answer
- For questions, format title as: "Customer Question: [brief question]"
- Include full context in description

MANDATORY TASKS FOR SALES CALLS - ALWAYS INCLUDE THESE THREE:
(Use "{customer_name}" as the customer name in the titles below)

1. SUMMARY OF CALL (ALWAYS REQUIRED - MUST BE FIRST):
   - Title: "SUMMARY OF CALL"
   - Priority: low
   - Description: Provide a comprehensive meeting summary including:
     * Meeting stage/type (initial discovery, demo, follow-up, pricing discussion, technical deep dive, etc.)
     * Key topics discussed and main points covered
     * Customer's level of engagement and sentiment (interested, hesitant, excited, concerned, etc.)
     * Primary pain points or challenges the customer mentioned
     * Opus products/features that were demonstrated or discussed
     * Customer's specific use cases and requirements
     * Important questions raised by the customer and how they were addressed
     * Any objections or concerns expressed
     * Buying signals or positive indicators observed
     * Next steps and expected timeline
     * Overall assessment of the call's success and progress in the sales cycle
   - This is NOT an action item - it's purely informational for reference
   - Write in a narrative style that gives context to someone who wasn't on the call

2. SEND FOLLOW-UP EMAIL (ALWAYS REQUIRED):
   - Title: "Send follow-up email to {customer_name}"
   - Priority: high
   - Description should include a HIGH-LEVEL SUMMARY (one paragraph):
     * What was demonstrated/discussed (high-level topics, not technical details)
     * Key points of interest from the customer
     * Main concerns or requirements mentioned
     * Next steps agreed upon
   - Do NOT include technical implementation details or feature specifics
   - Example: "Demonstrated the EHR platform focusing on scheduling and billing modules. Customer expressed interest in insurance verification features and workflow automation. Main concern was integration with existing systems. Agreed to schedule a follow-up call next week to discuss implementation timeline."

3. UPDATE HUBSPOT (ALWAYS REQUIRED):
   - Title: "Update HubSpot for {customer_name}"
   - Priority: high
   - Description MUST include these specific instructions:
     * Update the 'Next Step' field in HubSpot for this deal
     * Set the 'Next Activity Date' based on discussed timeline
     * Create a task in HubSpot for the next action (e.g., "Follow up with client in one week", "Send pricing proposal by Friday")
     * Log this call/meeting as an activity
   - Include what the next action should be based on the conversation

ADDITIONAL ACTION ITEMS:
Then extract any OTHER action items that ADI TIWARI explicitly owns or commits to:
- Look for phrases like "I'll send", "I'll schedule", "I'll follow up", "Let me get you"
- Exclude tasks assigned to prospects/customers (like "Steve will send")
- Exclude general discussion topics that aren't clear assignments
- If unclear who owns it, default to NOT including it as Adi's action

IMPORTANT: Write action items with enough context so someone who didn't attend the meeting can understand:
- What specific question was asked
- What feature/module was discussed
- What the customer's concern or requirement is
- Why this follow-up is needed

OWNERSHIP RULES:
- If someone says "Steve will send..." → That's Steve's task, NOT Adi's
- If David says "I will collect data..." → That's David's task, NOT Adi's  
- If Adi says "I'll send..." or "Let me..." → That IS Adi's task
- General discussions without clear ownership → NOT an action item
- When in doubt about ownership → EXCLUDE it

Prioritize based on:
- High: Blocking decisions, urgent timeline, critical requirements
- Medium: Important but not urgent, standard follow-ups
- Low: Nice-to-have information, future considerations

Return a structured JSON response with all extracted information.
</instructions>"""
        
        return prompt
    
    def _create_internal_prompt(self, transcript: str, additional_context: str) -> str:
        """
        Create the prompt for internal meeting transcripts
        
        Args:
            transcript: The transcript text
            additional_context: Additional context
            
        Returns:
            Formatted prompt string for internal meetings
        """
        prompt = f"""<context>
You are analyzing an internal Opus meeting transcript.

About Opus:
- Software company specializing in behavioral health
- Main product: EHR (Electronic Health Record)
- Other products: CRM, RCM (both white-labeled), Opus Kiosk, AI Scribe Co-pilot

Meeting context:
- Internal operational or strategic meeting
- Attendees are Opus team members
- Adi Tiwari is VP of Operations, handles support, marketing, and cross-functional operations

KEY DEPARTMENT HEADS FOR TASK DELEGATION:
- Marketing: Sean Rickenbacker (Marketing Director)
- Engineering/Development: Hector Fraginals (CTO)
- Onboarding/Training: Janelle Hall (Lead Onboarding Director)
- Support: John (Support Lead)

{additional_context if additional_context else ""}
</context>

<transcript>
{transcript}
</transcript>

<instructions>
Analyze this internal meeting transcript and extract:
1. Action items - specific tasks that need to be completed
2. A brief summary of the meeting
3. List of participants (Opus team members)
4. Key decisions made
5. Meeting title - Create a concise descriptive title (10-30 chars) that captures the meeting type:
   - Examples: "Leadership Sync", "Retrospective", "Sprint Planning", "Training Session", "Strategy Review", "Support Review"
   - Focus on the type or purpose of the meeting

MANDATORY TASK - ALWAYS INCLUDE AS FIRST ACTION ITEM:
1. SUMMARY OF CALL:
   - Title: "SUMMARY OF CALL"
   - Priority: low
   - Description: Comprehensive meeting overview including:
     * Meeting purpose and context
     * Main topics discussed and key points covered
     * Department(s) involved and their perspectives
     * Important decisions made or deferred
     * Process improvements or changes discussed
     * Cross-functional dependencies identified
     * Team dynamics and engagement level
     * Any blockers or challenges raised
     * Action items agreed upon and ownership
     * Next steps and follow-up meetings planned
     * Overall meeting effectiveness and outcomes
   - This is NOT an action item requiring work - it's informational documentation
   - Write as a narrative that provides context for team members who weren't present

For additional action items:
- Extract clear, actionable tasks
- Focus on operational and strategic items
- Include decisions that require follow-up
- Note cross-functional dependencies
- Capture process improvements or changes discussed

IMPORTANT:
- Tasks are rarely assigned to Adi unless explicitly stated
- Most tasks are for team organization and will be assigned later in Asana
- Include enough context for proper task assignment later
- Focus on WHO needs to do WHAT by WHEN (if mentioned)
- Do NOT use the is_question flag - that's only for sales calls with external customers
- Internal meetings generate action items for department heads, NOT customer questions

Prioritize based on:
- High: Critical operational issues, customer-impacting items, urgent deadlines
- Medium: Standard operational tasks, process improvements
- Low: Future considerations, nice-to-have improvements

Return a structured JSON response with all extracted information.
</instructions>"""
        
        return prompt
    
    def _create_onboarding_prompt(self, transcript: str, additional_context: str) -> str:
        """
        Create the prompt for onboarding department meetings
        
        Args:
            transcript: The transcript text
            additional_context: Additional context
            
        Returns:
            Formatted prompt string for onboarding meetings
        """
        prompt = f"""<context>
You are analyzing an internal Opus onboarding department meeting transcript.

CRITICAL LEADERSHIP CONTEXT:
- Humberto Buniotto (CEO) - His instructions SUPERSEDE all others. If Humberto says something needs to be done, it's the highest priority action item.
  - Name variations: May appear as "Humberto", "Buniotto", "CEO"
- Adi Tiwari (VP of Operations) - Second in command, reports to Humberto
  - Name variations: May appear as "Adi", "Aditya", "VP"

About Opus:
- Software company specializing in behavioral health
- Main product: EHR (Electronic Health Record)
- Other products: CRM, RCM (both white-labeled), Opus Kiosk, AI Scribe Co-pilot

Onboarding Department Focus:
- Client implementation and onboarding processes
- Training and setup for new customers
- Integration and technical setup
- Customer success handoffs

{additional_context if additional_context else ""}
</context>

<transcript>
{transcript}
</transcript>

<instructions>
Analyze this onboarding meeting transcript and extract:
1. Action items - specific tasks that need to be completed
2. A brief summary of the meeting
3. List of participants
4. Key decisions made
5. Meeting title - Create a concise descriptive title (10-30 chars)

MANDATORY TASK - ALWAYS INCLUDE AS FIRST ACTION ITEM:
1. SUMMARY OF CALL:
   - Title: "SUMMARY OF CALL"
   - Priority: low
   - Description: Comprehensive onboarding meeting summary including:
     * Meeting purpose (new client onboarding, implementation review, training session, etc.)
     * Client name and their current onboarding stage
     * Key onboarding topics discussed
     * Client requirements and customization needs identified
     * Training topics covered or scheduled
     * Integration points and technical requirements
     * Timeline and milestones discussed
     * Client concerns or questions raised
     * Humberto's (CEO) directives if present
     * Adi's (VP Ops) operational guidance if present
     * Resources needed or blockers identified
     * Next steps in the onboarding process
     * Overall client readiness and engagement assessment
   - This is NOT an action item - it's informational documentation
   - Focus on providing context for the onboarding team's reference

CRITICAL OWNERSHIP RULES FOR ONBOARDING:
1. If HUMBERTO (CEO) says something needs to be done → It's an action item (HIGH PRIORITY)
2. If ADI says something needs to be done → It's an action item (HIGH/MEDIUM PRIORITY)
3. Humberto or Adi MAY assign tasks to themselves - capture these
4. Unless explicitly directed to Humberto or Adi, assume tasks are for the team
5. Watch for name variations and misspellings

For action items:
- Extract ALL directives from Humberto (CEO) - these are non-negotiable
- Extract directives from Adi (VP Operations)
- Include questions that need answers (but do NOT use is_question flag - that's only for sales calls)
- Note if someone specific is assigned (rare, but possible)
- Default assumption: Tasks are for the onboarding team unless specified

TIMESTAMP EXTRACTION:
- Look for timestamps in the transcript (format: MM:SS or HH:MM:SS)
- Record when each action item was discussed

Priority Guidelines:
- Humberto's directives: HIGH priority
- Adi's directives: HIGH or MEDIUM priority based on urgency
- Team questions/follow-ups: MEDIUM priority
- General improvements: LOW priority

Return a structured JSON response with all extracted information.
</instructions>"""
        
        return prompt
    
    def _create_sales_dept_prompt(self, transcript: str, additional_context: str) -> str:
        """
        Create the prompt for Sales Sync department meetings
        
        Args:
            transcript: The transcript text
            additional_context: Additional context
            
        Returns:
            Formatted prompt string for sales sync meetings
        """
        prompt = f"""<context>
You are analyzing a Sales Sync meeting transcript from Opus.

MEETING PURPOSE:
This is a weekly sales team sync where we:
- Review open deals in the pipeline
- Discuss strategies to close specific opportunities
- Assign action items for advancing deals
- Review marketing initiatives and campaigns
- Discuss HubSpot hygiene and process improvements
- Plan next steps for each opportunity

KEY TEAM MEMBERS AND THEIR ROLES:
- Adi Tiwari: VP of Operations, Sales Executive, primary demo person for all deals
- Humberto Buniotto: CEO (highest authority)
- Chris Garraffa: Account Executive
- Nigel Green: Sales Consultant
- Gabriel Lacap: Sales Account Engineer (notes, follow-ups, agreements)
- Shawn Rickenbacker: Marketing Director

IMPORTANT NAME SPELLINGS:
- It's 'Garraffa' not 'Garofa' or 'Garafa'
- It's 'Shawn' not 'Sean' 
- It's 'Buniotto' not 'Buñodo' or other variations
- It's 'Lacap' not 'Lakap'

About Opus:
- Software company specializing in behavioral health
- Main product: EHR (Electronic Health Record)
- Other products: CRM (white-labeled Lead Squared), RCM, Opus Kiosk, AI Scribe Co-pilot
- Sales process involves demos, pricing discussions, and implementation planning

{additional_context if additional_context else ""}
</context>

<transcript>
{transcript}
</transcript>

<instructions>
Analyze this Sales Sync meeting transcript and extract:
1. Action items - specific tasks with clear ownership
2. A brief summary of the meeting
3. List of participants
4. Key decisions made
5. Meeting title - Create a concise descriptive title (10-30 chars)

MANDATORY TASK - ALWAYS INCLUDE AS FIRST ACTION ITEM:
1. SUMMARY OF CALL:
   - Title: "SUMMARY OF CALL"
   - Priority: low
   - Description: Comprehensive sales meeting summary including:
     * Deals reviewed and their current status
     * Key opportunities discussed with next steps
     * Blockers or challenges for specific deals
     * Marketing initiatives or campaigns discussed
     * HubSpot process improvements or hygiene items
     * Win/loss analysis if discussed
     * Competitive intelligence shared
     * Team member updates and capacity
     * Strategic decisions or pivots
     * Pipeline health and forecast
     * Action items by deal owner
   - This is informational documentation for the sales team

CRITICAL OWNERSHIP RULES:
1. CEO directives from Humberto are HIGHEST priority
2. VP directives from Adi are HIGH priority
3. Properly attribute tasks to the right person:
   - Deal-specific tasks → Usually Chris, Nigel, or Adi (whoever owns the deal)
   - Marketing tasks → Shawn Rickenbacker
   - Agreement/documentation tasks → Gabriel Lacap
   - HubSpot hygiene → Often team-wide or specific AE
4. If unclear who owns a deal, look for context clues like "my deal" or "I'll follow up"

For action items, focus on:
- Follow-ups with specific prospects
- Demo scheduling and preparation
- Proposal and pricing tasks
- Contract and agreement preparation
- Marketing collateral needs
- HubSpot updates and data entry
- Competitive research needs
- Internal process improvements

DEAL ATTRIBUTION:
- When action items relate to specific deals, include the company name
- Format: "Follow up with [Company] about [topic]"
- Track which AE owns which deal when mentioned

TIMESTAMP EXTRACTION:
- Look for timestamps in the transcript (format: MM:SS or HH:MM:SS)
- Record when key decisions or commitments were made

Priority Guidelines:
- CEO directives: HIGH
- Deal-closing activities: HIGH
- Time-sensitive proposals: HIGH
- Marketing campaigns: MEDIUM
- HubSpot hygiene: MEDIUM
- Process improvements: LOW

IMPORTANT:
- Do NOT use the is_question flag - that's only for sales calls with external customers
- Sales Sync meetings generate internal action items for the sales team, NOT customer questions
- This is an internal team meeting, not a customer-facing call

Return a structured JSON response with all extracted information.
</instructions>"""
        
        return prompt
    
    def _create_finpay_lsq_prompt(self, transcript: str, additional_context: str) -> str:
        """
        Create the prompt for Finpay <> LSQ Integration project meetings
        
        Args:
            transcript: The transcript text
            additional_context: Additional context
            
        Returns:
            Formatted prompt string for Finpay LSQ integration meetings
        """
        prompt = f"""<context>
You are analyzing a meeting transcript for the Finpay <> LSQ Integration project.

PROJECT CONTEXT:
This is a critical integration project between two companies:
- Finpay: Third-party behavioral health company specializing in estimations and financial services
- LSQ (Lead Squared): CRM platform that Opus white-labels as "Opus CRM"

PROJECT GOAL: Integrate Finpay's services with Lead Squared (Opus CRM) to enable seamless data flow and functionality between the two platforms.

KEY STAKEHOLDERS AND THEIR ROLES:

OPUS TEAM:
- Hector Fraginals - Chief Technology Officer (CTO) at Opus
  - Technical decision maker, oversees integration architecture
  - Name variations: May appear as "Hector", "CTO"
- Adi Tiwari - VP of Operations at Opus
  - Project coordination, operational requirements
  - Name variations: May appear as "Adi", "VP Ops"

FINPAY TEAM:
- Linda Stewart - VP of Operations at Finpay
  - Finpay's operational lead for integration
  - Name variations: May appear as "Linda", "VP"
- Lauren - Finpay team member
  - Integration support and coordination
- Rob - Finpay team member
  - Technical or operational support

ABOUT THE COMPANIES:
- Opus: EHR (Electronic Health Record) company for behavioral health
  - White-labels Lead Squared as "Opus CRM"
  - Integration needs to work within Opus ecosystem
- Finpay: Provides estimation and financial services for behavioral health
- Lead Squared (LSQ): The underlying CRM platform

{additional_context if additional_context else ""}
</context>

<transcript>
{transcript}
</transcript>

<instructions>
Analyze this Finpay <> LSQ Integration meeting transcript and extract:
1. Action items - specific tasks related to the integration project
2. A brief summary of the meeting
3. List of participants (identify company affiliation when possible)
4. Key technical or business decisions made
5. Meeting title - Create a concise descriptive title (10-30 chars) focused on integration progress

MANDATORY TASK - ALWAYS INCLUDE AS FIRST ACTION ITEM:
1. SUMMARY OF CALL:
   - Title: "SUMMARY OF CALL"
   - Priority: low
   - Description: Comprehensive integration meeting summary including:
     * Meeting purpose (technical review, API discussion, timeline sync, testing session, etc.)
     * Current integration status and progress since last meeting
     * Technical topics discussed (APIs, data mapping, authentication, etc.)
     * Business requirements clarified or modified
     * Decisions made by Hector (CTO) or technical leads
     * Operational considerations raised by Adi (VP Ops) or Linda (Finpay VP)
     * Blockers or dependencies identified between teams
     * Testing results or plans discussed
     * Security or compliance topics addressed
     * Timeline updates or commitments made
     * Resource needs from either Opus or Finpay side
     * Next technical milestones
     * Overall integration health and risk assessment
   - This is NOT an action item - it's project documentation for reference
   - Provide technical and business context for both teams

CRITICAL EXTRACTION RULES:
1. Technical decisions from Hector (CTO) are HIGH priority
2. Integration requirements from either side are HIGH priority
3. Timeline commitments are HIGH priority
4. Testing and validation tasks are MEDIUM-HIGH priority
5. Documentation tasks are MEDIUM priority

For action items, focus on:
- Integration requirements and specifications
- API endpoints or data mapping needs
- Testing procedures and timelines
- Blockers or dependencies between teams
- Security or compliance requirements
- Timeline commitments
- Follow-up meetings or demos needed

OWNERSHIP ATTRIBUTION:
- Tasks for Opus team: Usually technical integration on Opus/LSQ side
- Tasks for Finpay team: Usually related to their API/data requirements
- Joint tasks: Testing, validation, documentation
- Unless specified, technical tasks likely belong to the technical team mentioned

TIMESTAMP EXTRACTION:
- Look for timestamps in the transcript (format: MM:SS or HH:MM:SS)
- Record when key decisions or commitments were made

INTEGRATION QUESTIONS:
- For questions needing clarification, format title as: "Integration Question: [specific question]"
- These are NOT customer questions - they are technical/business clarifications between partners
- Include full context in the description
- DO NOT mark these with is_question flag (that's only for sales calls)

Priority Guidelines:
- Blockers to integration: HIGH
- Technical implementation tasks: HIGH
- Testing and validation: MEDIUM-HIGH
- Documentation: MEDIUM
- Future enhancements: LOW

Return a structured JSON response with all extracted information.
</instructions>"""
        
        return prompt
    
    def _create_support_prompt(self, transcript: str, additional_context: str) -> str:
        """
        Create the prompt for Support Leadership department meetings
        
        Args:
            transcript: The transcript text
            additional_context: Additional context
            
        Returns:
            Formatted prompt string for support meetings
        """
        prompt = f"""<context>
You are analyzing a Support Leadership meeting transcript from Opus.

MEETING PURPOSE:
This is a customer support leadership meeting focusing on:
- Bug tracking and resolution
- Vendor/partner management and escalations
- Cross-functional initiatives
- Support ticket priorities and workflows
- Technical escalations and issues
- Customer issue resolution strategies

KEY TEAM MEMBERS AND THEIR ROLES:
- John Catipon: Customer Support Lead, responsible for day-to-day support operations
- Adi Tiwari: VP of Operations, provides oversight for Support Leadership department
- Hector Fraginals: Chief Technology Officer (CTO), handles engineering escalations
- Janelle: Lead Onboarding Director, handles onboarding-related support issues

IMPORTANT CONTEXT ABOUT OPUS:
- We're an EHR (Electronic Health Record) company in the behavioral health space
- We get many bug reports and support tickets that need tracking
- Support often collaborates with Engineering (Hector/CTO) for technical issues
- Support coordinates with Onboarding (Janelle) for implementation issues

VENDOR/PARTNER INFORMATION:
When these vendors are mentioned, use the following context:
- Dosespot: E-prescribing and medication management partner
  * Issues related to medication ordering, prescriptions, controlled substances
  * API integration issues with e-prescribing
- LeadSquared (LSQ): White-labeled CRM solution provider
  * CRM functionality issues
  * Lead management and tracking problems
  * Marketing automation concerns
- Imagine (referred to as "Opus RCM"): Revenue Cycle Management partner
  * Billing and claims issues
  * Insurance verification problems
  * Payment processing concerns

{additional_context if additional_context else ""}
</context>

<transcript>
{transcript}
</transcript>

<instructions>
Analyze this Support Leadership meeting transcript and extract:
1. Action items - specific tasks with clear ownership
2. A brief summary of the meeting
3. List of participants
4. Key decisions made
5. Meeting title - Create a concise descriptive title (10-30 chars)

MANDATORY TASK - ALWAYS INCLUDE AS FIRST ACTION ITEM:
1. SUMMARY OF MEETING:
   - Title: "SUMMARY OF MEETING"
   - Priority: low
   - Description: Comprehensive support meeting overview including:
     * Major bugs or issues discussed and their priority
     * Customer escalations and resolution strategies
     * Vendor/partner issues (Dosespot, LSQ, Opus RCM)
     * Engineering escalations to Hector/CTO
     * Onboarding support issues for Janelle
     * Support workflow improvements or process changes
     * Resource allocation and capacity planning
     * Cross-functional coordination needs
     * Training needs or knowledge gaps identified
     * Key metrics or KPIs discussed
   - This is NOT an action item - it's informational documentation
   - Write as a narrative for team members who weren't present

For additional action items, focus on:
- Bug tickets that need to be created or tracked
- Customer escalations requiring follow-up
- Vendor issues needing escalation (specify which vendor)
- Engineering tasks for Hector's team
- Onboarding support items for Janelle's team
- Process improvements or documentation needs
- Training or knowledge transfer requirements
- Cross-team coordination tasks

OWNERSHIP RULES:
- Support tasks → Usually John Catipon (Customer Support Lead)
- Operations/strategic tasks → Adi (VP of Ops)
- Engineering/technical escalations → Hector (CTO)
- Onboarding-related support → Janelle
- Vendor escalations → Specify the vendor (Dosespot, LSQ, Opus RCM)
- If unclear, default to John Catipon for operational support tasks

IMPORTANT:
- Do NOT use the is_question flag - that's only for sales calls with external customers
- Support meetings generate action items and escalations, NOT customer questions

VENDOR TASK FORMATTING:
When creating tasks related to vendors, always include vendor name:
- "Escalate [issue] to Dosespot team"
- "Follow up with LSQ about [CRM feature]"
- "Contact Opus RCM regarding [billing issue]"

Priority Guidelines:
- Critical customer issues: HIGH
- Bugs affecting multiple customers: HIGH
- Vendor escalations: MEDIUM-HIGH
- Process improvements: MEDIUM
- Documentation updates: LOW-MEDIUM
- Meeting summary: LOW (always)

TIMESTAMP EXTRACTION:
- Look for timestamps in the transcript (format: MM:SS or HH:MM:SS)
- Record when key issues or escalations were raised

Return a structured JSON response with all extracted information.
</instructions>"""
        
        return prompt
    
    def _create_existing_customer_prompt(self, transcript: str, customer_name: str, additional_context: str) -> str:
        """
        Create the prompt for existing customer escalation meetings
        
        Args:
            transcript: The transcript text
            customer_name: Name of the existing customer
            additional_context: Customer-specific context from JSON
            
        Returns:
            Formatted prompt string for existing customer escalations
        """
        prompt = f"""<context>
You are analyzing a meeting transcript for an existing Opus customer who is experiencing issues or escalations during their onboarding phase.

MEETING PURPOSE:
This is an escalation or issue resolution meeting for an existing customer who has already purchased Opus and is currently in the onboarding/implementation phase. The VP of Operations (Adi Tiwari) is handling the escalation as the Account Executive and needs to delegate tasks appropriately.

KEY TEAM MEMBERS AND DEFAULT ASSIGNEES:
- Adi Tiwari: VP of Operations and Account Executive (handles customer escalations and relationships)
- Janelle: Lead Onboarding Director (primary contact for onboarding issues)
- Laura: Onboarding team member (assists with onboarding tasks)
- Hector Fraginals: Chief Technology Officer (for technical/engineering escalations)
- John: Support Lead (for support-related issues)

ESCALATION WORKFLOW:
1. Customer raises issue to their Account Executive (Adi)
2. Adi responds to customer via email/Slack to acknowledge and set expectations
3. Adi creates tasks to delegate the actual work to the appropriate team
4. Team members handle their assigned tasks
5. Adi follows up with customer on resolution

CUSTOMER-SPECIFIC CONTEXT:
Customer: {customer_name}
{additional_context if additional_context else "No additional context provided for this customer."}
</context>

<transcript>
{transcript}
</transcript>

<instructions>
Analyze this existing customer escalation transcript and extract:
1. Action items - specific tasks with clear delegation intent
2. A brief summary of the meeting/escalation
3. List of participants
4. Key decisions made
5. Meeting title - Create a concise descriptive title (10-30 chars)

MANDATORY TASK - ALWAYS INCLUDE AS FIRST ACTION ITEM:
1. ESCALATION SUMMARY:
   - Title: "ESCALATION SUMMARY"
   - Priority: low
   - Description: Comprehensive escalation overview including:
     * Nature of the customer's issue or concern
     * Current status of their onboarding/implementation
     * Specific problems or blockers identified
     * Customer's expectations and timeline requirements
     * Proposed resolution approach
     * Teams that need to be involved (Onboarding, Engineering, Support)
     * Risk assessment (impact on go-live date, customer satisfaction)
     * Follow-up requirements with the customer
   - This is documentation for reference, not an action item requiring work

For additional action items, focus on:
- Onboarding tasks that need to be completed or fixed
- Technical issues requiring engineering attention
- Configuration or setup problems
- Training or documentation needs
- Process improvements identified
- Customer communication and follow-ups
- Internal coordination between teams

DELEGATION GUIDELINES:
- Onboarding issues → Janelle or Laura
- Technical/system issues → Hector (CTO)
- Support process issues → John (Support Lead)
- Customer communication → Usually remains with Adi
- If unclear, note "Assignee: TBD - [suggested team]"

TASK FORMATTING:
- Create clear, actionable tasks that someone can pick up and execute
- Include enough context so the assignee understands the customer situation
- Format: "[Action Required]: [Specific task for customer name]"
- Include any deadlines or urgency mentioned by the customer

CUSTOMER CONTEXT AWARENESS:
- Consider the customer-specific context provided above
- Note any special requirements or sensitivities mentioned
- Flag if the issue relates to promises made during sales
- Identify if this is a recurring issue or new problem

Priority Guidelines:
- Customer-blocking issues: HIGH
- Issues affecting go-live date: HIGH
- Configuration/setup tasks: MEDIUM
- Documentation/training: MEDIUM
- Process improvements: LOW
- Summary: LOW (always)

IMPORTANT NOTES:
- These are existing paying customers, not prospects
- Focus on resolution and maintaining customer satisfaction
- Tasks should enable delegation while Adi maintains customer relationship
- Don't assign tasks directly - leave assignee field empty for manual assignment
- Include customer name in task titles for clarity

Return a structured JSON response with all extracted information.
</instructions>"""
        
        return prompt
    
    def _create_prompt(self, transcript: str, customer_name: str, additional_context: str) -> str:
        """
        Legacy prompt method - defaults to sales prompt
        Kept for backward compatibility
        """
        return self._create_sales_prompt(transcript, customer_name, additional_context)
    
    def analyze_image_for_tasks(self, 
                                image_file,
                                customer_name: str,
                                meeting_type: str,
                                customer_context: str = "") -> str:
        """
        Analyze an image (email screenshot, etc.) and extract tasks
        
        Args:
            image_file: The uploaded image file from Streamlit
            customer_name: Name of the customer/project
            meeting_type: Type of meeting context
            customer_context: Additional context for existing customers
            
        Returns:
            Extracted tasks and context as a string
        """
        import base64
        from io import BytesIO
        
        # Read image data
        image_bytes = image_file.read()
        image_file.seek(0)  # Reset file pointer for potential reuse
        
        # Encode image to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create prompt for image analysis
        if meeting_type == "existing_customer" and customer_context:
            context_prompt = f"""
This is an email or message screenshot related to an existing customer: {customer_name}

CUSTOMER CONTEXT:
{customer_context}

ANALYSIS INSTRUCTIONS:
1. Identify the type of communication (email, Slack, etc.)
2. Extract the sender's name and role
3. Identify the main request or issue being raised
4. Determine what actions need to be taken
5. Consider who should handle each action based on the customer context
6. Format as clear, actionable tasks

Remember this is an existing customer in onboarding, so tasks should typically be delegated to:
- Janelle or Laura for onboarding issues
- Hector for technical problems
- John for support issues
- Adi maintains the relationship but delegates the work
"""
        else:
            context_prompt = f"""
This is an email or message screenshot related to: {customer_name}
Meeting Type: {meeting_type}

ANALYSIS INSTRUCTIONS:
1. Identify the type of communication (email, Slack, etc.)
2. Extract the sender's name and role
3. Identify the main request or issue being raised
4. Determine what actions need to be taken
5. Format as clear, actionable tasks
"""
        
        prompt = f"""{context_prompt}

Based on the image content, extract and format the following:

1. COMMUNICATION SUMMARY:
   - Type (Email/Slack/etc.)
   - From: [Sender name and company]
   - Subject/Topic: [Main topic]
   - Urgency: [Low/Medium/High based on content]

2. KEY REQUEST/ISSUE:
   [Summarize the main ask or problem]

3. ACTIONABLE TASKS:
   [List each task that needs to be done, one per line]
   - Be specific and actionable
   - Include relevant context
   - Note any deadlines mentioned

4. SUGGESTED DELEGATION:
   [Based on the context, suggest who should handle each task]

Format the output as natural language tasks that can be directly used for task creation."""
        
        try:
            # Use Gemini's multimodal capability
            # Combine image and text in the content
            contents = [
                {
                    "role": "user",
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": f"image/{image_file.type.split('/')[-1] if hasattr(image_file, 'type') else 'jpeg'}",
                                "data": base64_image
                            }
                        },
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents
            )
            
            if response and response.text:
                return response.text
            else:
                return "Unable to extract content from the image. Please try again or enter tasks manually."
                
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise Exception(f"Failed to analyze image: {str(e)}")
    
    def analyze_pdf_for_tasks(self,
                              pdf_text: str,
                              customer_name: str,
                              meeting_type: str,
                              customer_context: str = "") -> str:
        """
        Analyze PDF text (email conversation, document) and extract tasks
        
        Args:
            pdf_text: Extracted text from PDF
            customer_name: Name of the customer/project
            meeting_type: Type of meeting context
            customer_context: Additional context for existing customers
            
        Returns:
            Extracted tasks and context as a string
        """
        # Create context-aware prompt based on meeting type
        if meeting_type == "existing_customer" and customer_context:
            context_prompt = f"""
You are analyzing a PDF document (likely an email conversation or thread) related to an existing customer: {customer_name}

CUSTOMER CONTEXT:
{customer_context}

IMPORTANT: This is an existing customer in onboarding. The VP of Operations (Adi) handles escalations but delegates work to:
- Janelle Hall or Laura for onboarding issues
- Hector Fraginals (CTO) for technical problems  
- John for support issues

CONVERSATION ANALYSIS INSTRUCTIONS:
1. Identify the type of document (email thread, single email, document)
2. Understand the full context of the conversation
3. Identify all participants and their roles
4. Track the flow of the conversation and any decisions made
5. Extract the main issues, requests, or concerns raised
6. Determine what specific actions need to be taken
7. Consider who should handle each action based on the customer context
8. Note any deadlines, urgency indicators, or commitments made
"""
        else:
            context_prompt = f"""
You are analyzing a PDF document related to: {customer_name}
Meeting Type: {meeting_type}

CONVERSATION ANALYSIS INSTRUCTIONS:
1. Identify the type of document (email thread, single email, document)
2. Understand the full context of the conversation
3. Identify all participants and their roles
4. Extract the main issues, requests, or concerns raised
5. Determine what specific actions need to be taken
6. Note any deadlines or urgency indicators
"""
        
        prompt = f"""{context_prompt}

PDF CONTENT TO ANALYZE:
{pdf_text[:15000]}  # Limit to first 15000 chars to avoid token limits

Based on the complete conversation/document above, extract and format:

1. CONVERSATION SUMMARY:
   - Document Type: [Email thread/Single email/Document]
   - Main Participants: [List key people involved]
   - Date Range: [If visible in the content]
   - Overall Topic: [Main subject of discussion]
   - Urgency Level: [Low/Medium/High/Critical based on content and tone]

2. KEY ISSUES/REQUESTS IDENTIFIED:
   [List each distinct issue, request, or concern raised in the conversation]
   - Include who raised it and any context
   - Note any responses or resolutions already discussed

3. ACTIONABLE TASKS:
   [Extract clear, specific tasks that need to be done]
   - Be very specific and include relevant context from the conversation
   - Include any commitments made or deadlines mentioned
   - Reference specific requests from the customer
   - Format: "Task: [specific action] - Context: [why this is needed based on conversation]"

4. SUGGESTED DELEGATION:
   [For each task, suggest who should handle it based on the context]
   - Consider the nature of each task and appropriate team member
   - For existing customers, default to Janelle/Laura for onboarding tasks

5. CRITICAL INFORMATION:
   - Any promises or commitments made
   - Deadlines or time-sensitive items
   - Escalation triggers or customer satisfaction concerns
   - Technical requirements or integration needs mentioned

Format the output as clear, actionable tasks that capture the full context of the conversation."""
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            if response and response.text:
                return response.text
            else:
                return "Unable to extract tasks from the PDF. Please try again or enter tasks manually."
                
        except Exception as e:
            logger.error(f"PDF analysis for tasks failed: {e}")
            raise Exception(f"Failed to analyze PDF: {str(e)}")
    
    def interpret_quick_tasks(self, 
                             task_input: str, 
                             context_name: str,
                             context_type: str) -> List[Dict[str, str]]:
        """
        Interpret natural language task descriptions into structured tasks
        Can handle multiple tasks separated by newlines or semicolons
        
        Args:
            task_input: Natural language task description(s)
            context_name: Name of customer/department/project for context
            context_type: Type of context (Sales Call, Internal Meeting, Project Meeting)
            
        Returns:
            List of task dictionaries with title, description, priority
        """
        # First, let AI determine if there are multiple tasks
        detection_prompt = f"""Analyze this input and determine if it contains multiple separate tasks:

Input: "{task_input}"

Instructions:
1. Identify if this contains ONE task or MULTIPLE tasks
2. Multiple tasks might be separated by:
   - New lines
   - Semicolons
   - Words like "and also", "additionally", "plus"
   - Numbered or bulleted lists
3. Each distinct action should be a separate task

Return a JSON with:
{{
  "task_count": <number>,
  "tasks": ["<task 1 text>", "<task 2 text>", ...]
}}

If it's one task, return task_count: 1 with the full text as the single task.
"""
        
        try:
            # Detect multiple tasks
            detection_response = self.client.models.generate_content(
                model=self.model,
                contents=detection_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            detected = json.loads(detection_response.text)
            individual_tasks = detected.get('tasks', [task_input])
            
            # Now process each task
            all_tasks = []
            
            for task_text in individual_tasks:
                if not task_text.strip():
                    continue
                    
                interpretation_prompt = f"""Convert this natural language task instruction into a structured task:

Task instruction: "{task_text}"

Context:
- Organization/Project: {context_name}
- Meeting Type: {context_type}

Extract and structure the following:
1. Title: A clear, concise, action-oriented task title (5-10 words)
2. Description: Detailed explanation including:
   - Any specific details mentioned
   - Timeline or deadline if mentioned
   - People or resources mentioned
   - Context about why this task is needed
3. Priority: Determine based on urgency:
   - "high" if mentions: urgent, ASAP, today, tomorrow, critical
   - "medium" if mentions: this week, soon, next few days
   - "low" if no urgency indicated or mentions: eventually, when possible, later

Return ONLY a JSON object with this structure:
{{
  "title": "<clear action title>",
  "description": "<detailed description>",
  "priority": "<high|medium|low>"
}}
"""
                
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=interpretation_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                
                if response.text:
                    task_data = json.loads(response.text)
                    # Ensure all required fields
                    if 'title' in task_data:
                        all_tasks.append({
                            'title': task_data.get('title', 'Quick Task'),
                            'description': task_data.get('description', task_text),
                            'priority': task_data.get('priority', 'medium')
                        })
            
            return all_tasks
            
        except Exception as e:
            logger.error(f"Error interpreting quick tasks: {str(e)}")
            # Fallback: create a simple task from the input
            return [{
                'title': 'Quick Task',
                'description': task_input,
                'priority': 'medium'
            }]
    
    def extract_simple_action_items(self, transcript: str) -> List[Dict[str, str]]:
        """
        Simple extraction of action items without full analysis
        
        Args:
            transcript: The transcript text
            
        Returns:
            List of action items as dictionaries
        """
        prompt = f"""Extract action items from this transcript. 
        Return ONLY a JSON array of action items.
        Each item should have 'title' and 'description' fields.
        
        Transcript:
        {transcript}
        
        Focus on clear, actionable tasks mentioned in the meeting."""
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            # Parse JSON response
            if response.text:
                items = json.loads(response.text)
                if isinstance(items, list):
                    return items
                elif isinstance(items, dict) and 'action_items' in items:
                    return items['action_items']
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting action items: {str(e)}")
            return []