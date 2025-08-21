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
                          meeting_type: str = "sales_call") -> TranscriptAnalysis:
        """
        Analyze transcript and extract structured action items
        
        Args:
            transcript: The transcript text to analyze
            customer_name: Name of the customer/project
            additional_context: Any additional context about the meeting
            meeting_type: Type of meeting ("sales_call" or "internal_meeting")
            
        Returns:
            TranscriptAnalysis object with extracted data
        """
        # Create the analysis prompt based on meeting type
        if meeting_type == "internal_meeting":
            prompt = self._create_internal_prompt(transcript, additional_context)
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
                                "mentioned_by": {"type": "string"}
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
                    max_output_tokens=4096
                )
            )
            
            # Parse the response
            if hasattr(response, 'text') and response.text:
                result_json = json.loads(response.text)
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
            additional_context: Additional context
            
        Returns:
            Formatted prompt string for sales calls
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

{additional_context if additional_context else ""}
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

CRITICAL: Only extract action items that ADI TIWARI (the presenter/sales executive) explicitly owns or commits to:
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

For action items:
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

Prioritize based on:
- High: Critical operational issues, customer-impacting items, urgent deadlines
- Medium: Standard operational tasks, process improvements
- Low: Future considerations, nice-to-have improvements

Return a structured JSON response with all extracted information.
</instructions>"""
        
        return prompt
    
    def _create_prompt(self, transcript: str, customer_name: str, additional_context: str) -> str:
        """
        Legacy prompt method - defaults to sales prompt
        Kept for backward compatibility
        """
        return self._create_sales_prompt(transcript, customer_name, additional_context)
    
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