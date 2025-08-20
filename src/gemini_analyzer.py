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


class GeminiAnalyzer:
    """Analyze transcripts using Google Gemini AI"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        """
        Initialize Gemini analyzer
        
        Args:
            api_key: Gemini API key (if None, will use environment variable)
            model: Model to use ("gemini-1.5-flash" or "gemini-1.5-pro")
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
                          additional_context: str = "") -> TranscriptAnalysis:
        """
        Analyze transcript and extract structured action items
        
        Args:
            transcript: The transcript text to analyze
            customer_name: Name of the customer/project
            additional_context: Any additional context about the meeting
            
        Returns:
            TranscriptAnalysis object with extracted data
        """
        # Create the analysis prompt
        prompt = self._create_prompt(transcript, customer_name, additional_context)
        
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
                    }
                },
                "required": ["action_items", "summary", "participants", "key_decisions"]
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
                    key_decisions=result_json.get('key_decisions', [])
                )
            else:
                # Fallback empty analysis
                analysis = TranscriptAnalysis(
                    action_items=[],
                    summary="Unable to extract content",
                    participants=[],
                    key_decisions=[]
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
                key_decisions=[]
            )
    
    def _create_prompt(self, transcript: str, customer_name: str, additional_context: str) -> str:
        """
        Create the prompt for Gemini
        
        Args:
            transcript: The transcript text
            customer_name: Customer/project name
            additional_context: Additional context
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""<context>
You are analyzing a meeting transcript for {customer_name}.
{additional_context if additional_context else ""}

Your role: Extract actionable tasks and key information from the meeting transcript.
Focus on: Clear action items that need to be completed, who mentioned them, and any decisions made.
</context>

<transcript>
{transcript}
</transcript>

<instructions>
Analyze the above transcript and extract:
1. Action items - specific tasks that need to be completed
2. A brief summary of the meeting
3. List of participants (names mentioned in the transcript)
4. Key decisions that were made

For action items:
- Make titles brief and actionable (start with a verb when possible)
- Include relevant context in the description
- If someone specific is assigned or mentioned for a task, note them
- Assess priority based on urgency mentioned in the discussion

Return a structured JSON response with all extracted information.
</instructions>"""
        
        return prompt
    
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