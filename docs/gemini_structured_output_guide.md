# Google Gemini Structured Output Guide

## Overview

Gemini can generate either JSON or enum values as structured output. To constrain the model to generate JSON, configure a responseSchema. The model will then respond to any prompt with JSON-formatted output. This feature is sometimes called "JSON mode" or "controlled generation."

Controlled Generation for Gemini 1.5 Pro and Flash provides developers with a robust tool to reliably generate responses that adhere to a defined schema, whether it's extracting entities in JSON format for seamless downstream processing or classifying content within your own taxonomy.

**Key Benefits:**
- **Reliable JSON Output**: The model will then respond to any prompt with JSON-formatted output when a response schema is configured
- **Schema Enforcement**: Ensures outputs always conform to your predefined structure
- **Reduced Post-Processing**: This lets you directly extract data from the model's output without post-processing
- **API Economy Integration**: Generate outputs in formats like JSON, making your AI a first-class citizen in the API economy

**Supported Models (2025):**
- Gemini 2.5 Pro and Flash (latest with thinking capabilities)
- Gemini 2.0 Flash and variants
- Gemini 1.5 Pro and Flash

## Setup and Authentication

### API Key Generation

To use the Gemini API, you need an API key. You can create a key for free with a few clicks in Google AI Studio:

1. **Visit Google AI Studio**: Navigate to [ai.google.dev](https://ai.google.dev)
2. **Sign In**: Use your Google account credentials
3. **Create API Key**: Click on the "Get API key" button, then select "Create API key in new project" or use an existing Google Cloud project
4. **Secure Storage**: Copy and store it safely as you will not be able to see this token again

### Environment Setup

**Set Environment Variable:**

```bash
# Linux/macOS
export GEMINI_API_KEY="your_api_key_here"

# Windows
set GEMINI_API_KEY=your_api_key_here
```

**Using .env File:**
```env
GEMINI_API_KEY=your_api_key_here
GOOGLE_CLOUD_PROJECT=your_project_id  # Optional, for Vertex AI
GOOGLE_CLOUD_LOCATION=us-central1     # Optional, for Vertex AI
```

### Installation

**Install the Latest SDK (2025):**
```bash
# Install the new unified Google GenAI SDK
pip install google-genai

# For async support with better performance
pip install google-genai[aiohttp]
```

**Important**: The legacy google-generativeai package is now deprecated. All support will permanently end on November 30, 2025. Use the new unified `google-genai` SDK.

### Basic Client Setup

```python
from google import genai
import os

# Using environment variable (recommended)
client = genai.Client()

# Or explicitly provide API key
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

# For Vertex AI (enterprise)
vertex_client = genai.Client(
    vertexai=True,
    project='your-project-id',
    location='us-central1'
)
```

## Model Selection

### Gemini 1.5 Pro vs Flash for Transcript Analysis

Overall, Gemini 1.5 Pro outperformed Gemini 1.5 Flash on all of the tasks we tested, but the choice depends on your specific requirements:

#### Gemini 1.5 Pro
**Best for Complex Transcript Analysis:**
- Enhanced reasoning and creative abilities, better suited for tasks requiring nuanced understanding, complex problem-solving, and generating high-quality, creative text formats
- Context window of up to 2 million tokens, allowing for extensive data processing without losing context
- **Use Cases**: 
  - Detailed transcript analysis with complex reasoning
  - Multi-speaker identification and sentiment analysis
  - Long-form content summarization with nuanced insights
  - Tasks like time-stamping for podcasts or detailed transcription are more precise, thanks to improved multimodal processing

#### Gemini 1.5 Flash
**Best for High-Speed Processing:**
- Optimized for speed and efficiency, making it well-suited for applications that require quick response times and low latency
- Context window of 1 million tokens, allowing it to handle substantial data inputs efficiently while maintaining speed
- Flash does have a loss of performance in benchmarks traded by his low latency and optimized costs. This loss keeps of a maximum of 15% less compared to the other

**Performance Comparison:**
- **Speed**: Flash provides sub-second response times
- **Cost**: Flash is significantly more cost-effective than 1.5 Pro, especially for processing large volumes of data
- **Quality**: The loss can only be considered relevant under the context of a very complex task and will not make a difference with most usual simple to intermediate tasks

**Recommendation for Transcript Analysis:**
- **Use Gemini 1.5 Pro** if you need detailed analysis, speaker identification, sentiment analysis, or complex reasoning over transcripts
- **Use Gemini 1.5 Flash** for basic transcript processing, simple summarization, or high-volume batch processing where speed and cost matter more than nuanced analysis

### Latest Model Options (2025)

Gemini 2.5 Pro is our state-of-the-art thinking model, capable of reasoning over complex problems in code, math, and STEM, as well as analyzing large datasets, codebases, and documents using long context

Available models:
- `gemini-2.5-pro`: Most advanced thinking model
- `gemini-2.5-flash`: Most cost-efficient model supporting high throughput
- `gemini-2.0-flash`: Next-gen features with superior speed and native tool use
- `gemini-1.5-pro`: Reliable multimodal model for complex reasoning
- `gemini-1.5-flash`: Fast, versatile model for scaling across diverse tasks

## Structured Output Implementation

### Core Concept

Configuring the model for JSON output using responseSchema parameter relies on Schema object to define its structure. This object represents a select subset of the OpenAPI 3.0 Schema object, and also adds a propertyOrdering field.

### Using Pydantic Models (Recommended)

```python
from google import genai
from pydantic import BaseModel
from typing import List, Optional
import enum

class TranscriptSpeaker(BaseModel):
    speaker_id: str
    name: Optional[str] = None
    confidence: float

class TranscriptSegment(BaseModel):
    start_time: float
    end_time: float
    speaker: TranscriptSpeaker
    text: str
    confidence: float

class Sentiment(str, enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class TranscriptAnalysis(BaseModel):
    segments: List[TranscriptSegment]
    summary: str
    overall_sentiment: Sentiment
    key_topics: List[str]
    duration_seconds: float

# Configure client for structured output
client = genai.Client()

response = client.models.generate_content(
    model="gemini-1.5-pro",
    contents="""Analyze this transcript: 
    [00:00] John: Welcome to our quarterly review meeting.
    [00:30] Sarah: Thanks John. Let's start with the sales numbers.
    [01:15] John: Sales increased 15% this quarter, which is fantastic news.
    """,
    config={
        "response_mime_type": "application/json",
        "response_schema": TranscriptAnalysis,
        "temperature": 0.1  # Lower temperature for more consistent structured output
    }
)

# Access parsed response
analysis: TranscriptAnalysis = response.parsed
print(f"Duration: {analysis.duration_seconds}s")
print(f"Sentiment: {analysis.overall_sentiment}")
for segment in analysis.segments:
    print(f"[{segment.start_time}s] {segment.speaker.speaker_id}: {segment.text}")
```

### Advanced Schema Configuration

The response schema feature supports the following schema fields:

**Supported Field Types:**
- `string`, `number`, `integer`, `boolean`
- `array` with specified item types
- `object` with defined properties
- `enum` for classification tasks

**Schema Features:**
- **propertyOrdering**: This field defines the order in which properties are generated
- **Optional Properties**: Fields can be marked as optional
- **Nested Structures**: Support for complex nested objects
- **Array Constraints**: Specify min/max length for arrays

### Using Raw Schema Objects

```python
from google import genai

# Define schema manually
schema = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Title of the transcript"
        },
        "speakers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "speaking_time": {"type": "number"}
                },
                "required": ["name", "speaking_time"]
            }
        },
        "main_topics": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 5
        }
    },
    "required": ["title", "speakers", "main_topics"]
}

client = genai.Client()
response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents="Analyze this meeting transcript for speakers and topics...",
    config={
        "response_mime_type": "application/json",
        "response_schema": schema
    }
)

result = response.parsed
```

### Enum Classification

```python
from google import genai
import enum

class MeetingType(str, enum.Enum):
    STANDUP = "standup"
    PLANNING = "planning"
    RETROSPECTIVE = "retrospective"
    ALL_HANDS = "all_hands"
    ONE_ON_ONE = "one_on_one"

class MeetingClassification(BaseModel):
    meeting_type: MeetingType
    confidence: float
    reasoning: str

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Classify this meeting transcript...",
    config={
        "response_mime_type": "application/json",
        "response_schema": MeetingClassification
    }
)
```

## Example Code

### Complete Transcript Analysis Example

```python
from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional
import json
import os
from datetime import datetime

class Speaker(BaseModel):
    id: str
    name: Optional[str] = None
    role: Optional[str] = None

class TranscriptTimestamp(BaseModel):
    start_time: float = Field(description="Start time in seconds")
    end_time: float = Field(description="End time in seconds")
    text: str = Field(description="Spoken text")
    speaker: Speaker
    confidence: Optional[float] = None

class TopicAnalysis(BaseModel):
    topic: str = Field(description="Main topic discussed")
    relevance_score: float = Field(description="Relevance score from 0-1")
    time_discussed: float = Field(description="Total time discussed in seconds")

class TranscriptSummary(BaseModel):
    title: str = Field(description="Meeting title or topic")
    total_duration: float = Field(description="Total duration in seconds")
    speakers: List[Speaker]
    timestamps: List[TranscriptTimestamp]
    key_topics: List[TopicAnalysis]
    action_items: List[str]
    decisions_made: List[str]
    overall_summary: str = Field(description="2-3 sentence summary")

class TranscriptAnalyzer:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-pro"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
    
    def analyze_transcript(self, transcript_text: str, 
                         meeting_context: str = "") -> TranscriptSummary:
        """
        Analyze a transcript and return structured data
        
        Args:
            transcript_text: The raw transcript text
            meeting_context: Optional context about the meeting
            
        Returns:
            TranscriptSummary: Structured analysis of the transcript
        """
        
        prompt = f"""
        Analyze the following meeting transcript and provide a comprehensive structured analysis.
        
        Context: {meeting_context}
        
        Transcript:
        {transcript_text}
        
        Please provide a detailed analysis including:
        - Identification of all speakers
        - Timestamped segments with speaker attribution
        - Key topics discussed with relevance scores
        - Action items mentioned
        - Decisions made during the meeting
        - Overall summary
        
        Ensure all timestamps are accurate and all speakers are properly identified.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": TranscriptSummary,
                    "temperature": 0.1,
                    "max_output_tokens": 4096
                }
            )
            
            return response.parsed
            
        except Exception as e:
            raise Exception(f"Error analyzing transcript: {str(e)}")
    
    def batch_analyze(self, transcripts: List[tuple]) -> List[TranscriptSummary]:
        """
        Analyze multiple transcripts
        
        Args:
            transcripts: List of (transcript_text, context) tuples
            
        Returns:
            List[TranscriptSummary]: Analysis results for each transcript
        """
        results = []
        for transcript_text, context in transcripts:
            try:
                result = self.analyze_transcript(transcript_text, context)
                results.append(result)
            except Exception as e:
                print(f"Error processing transcript: {e}")
                continue
        return results

# Usage Example
def main():
    # Sample transcript
    sample_transcript = """
    [00:00] John (Project Manager): Good morning everyone, let's start our sprint planning meeting.
    [00:15] Sarah (Developer): Hi John. I've completed the user authentication feature from last sprint.
    [00:30] Mike (Designer): The new UI mockups are ready for review. I think we should prioritize the dashboard redesign.
    [01:00] Sarah: I can take on the dashboard implementation. How much time do we have?
    [01:15] John: We have two weeks for this sprint. Mike, can you share the mockups by tomorrow?
    [01:30] Mike: Absolutely. I'll send them to the team Slack channel.
    [01:45] Sarah: Great. I'll also need to coordinate with the backend team for the API changes.
    [02:00] John: Perfect. Let's make the dashboard our main priority this sprint.
    """
    
    # Initialize analyzer
    analyzer = TranscriptAnalyzer(model="gemini-1.5-pro")
    
    # Analyze transcript
    try:
        result = analyzer.analyze_transcript(
            transcript_text=sample_transcript,
            meeting_context="Sprint planning meeting for a web development team"
        )
        
        # Display results
        print(f"Meeting Title: {result.title}")
        print(f"Duration: {result.total_duration} seconds")
        print(f"\nSpeakers ({len(result.speakers)}):")
        for speaker in result.speakers:
            print(f"  - {speaker.name or speaker.id} ({speaker.role or 'Unknown role'})")
        
        print(f"\nKey Topics ({len(result.key_topics)}):")
        for topic in result.key_topics:
            print(f"  - {topic.topic} (Relevance: {topic.relevance_score:.2f})")
        
        print(f"\nAction Items ({len(result.action_items)}):")
        for item in result.action_items:
            print(f"  - {item}")
        
        print(f"\nDecisions Made ({len(result.decisions_made)}):")
        for decision in result.decisions_made:
            print(f"  - {decision}")
        
        print(f"\nSummary: {result.overall_summary}")
        
        # Save to JSON
        with open(f"transcript_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
            
    except Exception as e:
        print(f"Analysis failed: {e}")

if __name__ == "__main__":
    main()
```

### Streaming Structured Output

```python
from google import genai
from pydantic import BaseModel
from typing import List

class StreamingAnalysis(BaseModel):
    current_speaker: str
    partial_text: str
    confidence: float

def stream_analysis(transcript_chunk: str):
    client = genai.Client()
    
    for chunk in client.models.generate_content_stream(
        model="gemini-2.0-flash",
        contents=f"Analyze this transcript chunk: {transcript_chunk}",
        config={
            "response_mime_type": "application/json",
            "response_schema": StreamingAnalysis
        }
    ):
        if chunk.text:
            # Parse streaming JSON response
            try:
                partial_result = json.loads(chunk.text)
                yield partial_result
            except json.JSONDecodeError:
                continue  # Partial JSON, wait for more
```

## Rate Limits and Pricing

### Current Rate Limits (2025)

Rate limits are tied to the project's usage tier. As your API usage and spending increase, you'll have an option to upgrade to a higher tier with increased rate limits

#### Free Tier
Free Tier Limits: 5 requests per minute (RPM), 25 requests per day
- **Models Available**: All models with limitations
- **Context Window**: 1 million token context window
- **Usage**: Google AI Studio usage is free of charge in all available regions

**Important**: prompts and responses on the free plan will be used to train Google's models. If you plan to use this tier, be sure to never feed sensitive data to the API

#### Paid Tiers

**Tier 1 (Immediate after enabling billing):**
Tier 1 offers 300 RPM with 1 million TPM immediately upon payment, providing more predictable capacity planning

**Tier 2 (Requires $250+ spending + 30 days):**
- Enterprise-level quotas
- Higher rate limits across all dimensions

**Rate Limiting Dimensions:**
The Gemini API enforces rate limits across four distinct dimensions: RPM (Requests Per Minute), TPM (Tokens Per Minute), RPD (Requests Per Day), and IPM (Images Per Minute)

### Pricing Structure (2025)

#### Gemini 2.5 Models
Gemini 2.5 Flash costs $0.30 per million input tokens and $2.50 per million output tokens. Gemini 2.5 Pro costs $1.25 per million input tokens and $10.00 per million output tokens

#### Gemini 1.5 Models
Gemini 1.5 Pro charges $1.25 per million input tokens and $5.00 per million output tokens as of August 2025
- **Gemini 1.5 Flash**: Significantly lower cost, recently had its price decreased by 70%

#### Cost Comparison
This 24x price difference often outweighs rate limit considerations for budget-conscious projects compared to competitors like GPT-4.

**Example Cost Calculation:**
With average English text containing 4 characters per token, a typical 1,000-word prompt costs approximately $0.00031, while a 1,000-word response costs $0.00125

### Cost Optimization Tips

1. **Model Selection**: Implementing intelligent routing based on prompt analysis can maintain quality while reducing costs by 70% or more

2. **Batch Processing**: Batch Mode is designed to process large volumes of requests asynchronously. Requests submitted using this mode are 50% of the price of interactive (non-batch mode) requests

3. **Request Optimization**: Batch them together instead of making multiple small requests

4. **Free Tier Usage**: AI Studio is free and there is a generous free tier on the API as well, which includes 1,500 requests per day with Gemini 1.5 Flash

### Error Handling and Billing

If your request fails with a 400 or 500 error, you won't be charged for the tokens used. However, the request will still count against your quota

**Rate Limit Errors**: When exceeding limits, subsequent requests receive HTTP 429 errors until tokens replenish

### Enterprise Considerations

For enterprise usage:
- **Vertex AI Integration**: Higher quotas and enterprise features
- **Context Caching**: The free plan doesn't include context caching. This means that Google Cloud won't let you store reusable long prompts on their servers
- **Data Handling**: When you enable billing and use the paid tier, your prompts and responses aren't used to improve Google products

This comprehensive guide provides everything needed to implement structured output with Google's Gemini API for transcript analysis and other use cases, with current 2025 pricing and technical specifications.