# Prompt Engineering Guide for Meeting Transcript Analysis with Gemini

## Table of Contents
1. [Core Prompt Engineering Principles](#core-prompt-engineering-principles)
2. [XML vs JSON in Prompts](#xml-vs-json-in-prompts)
3. [Few-Shot Learning Strategies](#few-shot-learning-strategies)
4. [Handling Ambiguous Action Items](#handling-ambiguous-action-items)
5. [Context Window Optimization](#context-window-optimization)
6. [Prompt Templates for Different Meeting Types](#prompt-templates-for-different-meeting-types)

---

## Core Prompt Engineering Principles

### 1. Structure Your Prompts with Clear Delimiters

**Best Practice:** Use XML-like tags or clear section markers to separate different components of your prompt. This helps Gemini understand the boundaries between instructions, context, and data.

```
<system_role>
You are an expert meeting analyst specializing in extracting actionable insights from transcripts.
</system_role>

<task_instructions>
1. Identify all action items, both explicit and implied
2. Determine task owners from context clues
3. Extract deadlines, even if mentioned informally
4. Flag items that need clarification
</task_instructions>

<output_requirements>
Format your response as structured JSON with specific fields for each action item.
</output_requirements>

<transcript>
[Meeting content here]
</transcript>
```

### 2. Be Explicit About Output Format

**Key Insight:** Gemini performs better when you provide exact formatting instructions with examples of the desired output structure.

```
Return your analysis in this EXACT format:
{
  "action_items": [
    {
      "task": "Clear, actionable description",
      "owner": "Person's name or 'Unassigned'",
      "deadline": "YYYY-MM-DD or 'Not specified'",
      "priority": "High|Medium|Low",
      "confidence": "High|Medium|Low",
      "context": "Why this task is needed"
    }
  ],
  "ambiguous_items": [
    {
      "statement": "Original ambiguous statement",
      "clarification_needed": "What needs to be clarified"
    }
  ]
}
```

### 3. Chain-of-Thought Prompting for Complex Analysis

**Strategy:** Break down the analysis into steps to improve accuracy:

```
Analyze this transcript using the following thought process:

Step 1: Read through and identify all statements containing action words (will, should, need to, must, going to)
Step 2: For each action statement, determine if it's a commitment or suggestion
Step 3: Extract the WHO (owner), WHAT (task), WHEN (deadline), and WHY (context)
Step 4: Assess confidence level based on clarity of the statement
Step 5: Group related tasks and identify dependencies

Show your reasoning for each extracted action item.
```

### 4. Role-Based Prompting

**Effectiveness:** Assigning a specific expert role improves task performance by 15-20% based on recent studies.

```
You are a Senior Project Manager with 15 years of experience in extracting and organizing action items from meeting transcripts. You have developed an keen eye for:
- Implicit commitments that aren't directly stated
- Dependencies between tasks
- Realistic vs. aspirational deadlines
- Task ownership based on team dynamics
```

---

## XML vs JSON in Prompts

### When to Use JSON Format

**Recommended for Gemini 2.5 models** - Native support with schema validation

**Advantages:**
- Smaller token footprint (20-30% fewer tokens than XML)
- Direct parsing without post-processing
- Better for nested structures and arrays
- Schema enforcement available

**Example JSON-focused prompt:**
```
Extract action items and return them as a JSON array. Each item must have these exact keys:
- "task": string (imperative sentence starting with a verb)
- "owner": string (full name from transcript)
- "deadline": string (ISO date format or "TBD")
- "dependencies": array of task IDs

Example of expected output:
[
  {
    "task": "Review and approve Q3 budget proposal",
    "owner": "Sarah Johnson",
    "deadline": "2025-02-15",
    "dependencies": []
  }
]
```

### When to Use XML Format

**Use cases:**
- Mixed content (narrative + structured data)
- Document-like hierarchies
- When you need better human readability

**Example XML-focused prompt:**
```
Structure your response using these XML tags:

<analysis>
  <action_items>
    <item priority="high" confidence="certain">
      <task>Complete market analysis report</task>
      <owner>Michael Chen</owner>
      <deadline>2025-02-20</deadline>
      <rationale>Needed for board presentation</rationale>
    </item>
  </action_items>
  
  <decisions>
    <decision impact="major">
      <description>Approved $50K marketing budget</description>
      <made_by>Leadership team</made_by>
    </decision>
  </decisions>
</analysis>
```

---

## Few-Shot Learning Strategies

### 1. Optimal Number of Examples

**Research Finding:** 2-5 examples provide the best balance between performance and token usage. More than 5 examples shows diminishing returns.

### 2. Example Selection Principles

**Diversity Over Quantity:** Choose examples that cover different scenarios:

```
<examples>
<!-- Example 1: Clear, explicit action item -->
<example>
Input: "John will send the report to everyone by 5 PM tomorrow."
Output: {
  "task": "Send report to all team members",
  "owner": "John",
  "deadline": "Tomorrow 5 PM",
  "confidence": "High",
  "extraction_reason": "Explicit commitment with clear owner and deadline"
}
</example>

<!-- Example 2: Implicit action item -->
<example>
Input: "We really need someone to look into why customers are churning."
Output: {
  "task": "Investigate customer churn reasons",
  "owner": "Unassigned",
  "deadline": "Not specified",
  "confidence": "Medium",
  "extraction_reason": "Clear need expressed but no owner assigned",
  "flag_for_followup": true
}
</example>

<!-- Example 3: Conditional/dependent action -->
<example>
Input: "Once Sarah finishes the design, Tom can start development."
Output: [
  {
    "task": "Complete design",
    "owner": "Sarah",
    "deadline": "Not specified",
    "id": "task_1"
  },
  {
    "task": "Start development",
    "owner": "Tom",
    "deadline": "After task_1",
    "dependencies": ["task_1"]
  }
]
</example>

<!-- Example 4: Non-action item (negative example) -->
<example>
Input: "Last quarter's results were better than expected."
Output: {
  "action_items": [],
  "note": "Statement is informational, not actionable"
}
</example>
</examples>
```

### 3. Include Negative Examples

**Critical for accuracy:** Show the model what NOT to extract as action items:

```
These are NOT action items:
- Status updates: "The project is 70% complete"
- Opinions: "I think this approach might work better"
- Questions without commitment: "Should we consider hiring?"
- Past actions: "We completed the audit last week"
```

### 4. Progressive Complexity

Start with simple examples and progress to complex ones:

```
Level 1 (Simple): "Bob will call the client tomorrow"
Level 2 (Moderate): "We need to finalize the proposal by next week"
Level 3 (Complex): "After the legal review, assuming no issues, marketing should prepare the campaign, coordinating with sales on timing"
```

---

## Handling Ambiguous Action Items

### 1. Classification Framework

Train the model to categorize action items by clarity:

```
Classify each potential action item into one of these categories:

CERTAIN: Has clear owner, deadline, and deliverable
Example: "Lisa will submit the report by Friday"

PROBABLE: Missing one element but context makes it likely
Example: "Marketing needs to update the website" (missing deadline)

AMBIGUOUS: Multiple interpretations possible
Example: "Someone should probably look at this"

NOT_ACTIONABLE: Suggestions or observations
Example: "It would be nice if we had better tools"

For PROBABLE and AMBIGUOUS items, specify what clarification is needed.
```

### 2. Context Clues for Owner Inference

```
When the owner isn't explicitly stated, use these context clues:

1. Department mentions: "Engineering needs to fix this" → Assign to Engineering Lead
2. Expertise references: "This needs someone with SQL skills" → Check attendee roles
3. Previous ownership: "The same person who did it last time" → Reference historical context
4. Proximity principle: The person speaking often owns tasks they mention
5. Volunteering patterns: "I can handle that" or "Leave it with me"

If no owner can be inferred, mark as "REQUIRES_ASSIGNMENT" with suggested owner based on task type.
```

### 3. Deadline Interpretation

```
Convert informal time references to specific dates:

Time Reference → Interpretation Rules:
- "ASAP" → Flag as HIGH PRIORITY, suggest 2 business days
- "End of day" → Same day, 5 PM
- "Early next week" → Monday or Tuesday of next week
- "When you get a chance" → LOW PRIORITY, suggest 1 week
- "Before the board meeting" → Check calendar context, subtract 2 days for prep
- "In Q3" → Last day of Q3 as deadline

Always note when a deadline is inferred vs. explicitly stated.
```

### 4. Confidence Scoring

```
Assign confidence scores based on these criteria:

HIGH CONFIDENCE (90-100%):
- Explicit verbal commitment ("I will...")
- Clear owner and deadline stated
- Written in meeting notes/slides
- Confirmed by multiple participants

MEDIUM CONFIDENCE (60-89%):
- Strong action words but missing details
- Owner implied by context
- Deadline approximate
- Single mention without confirmation

LOW CONFIDENCE (30-59%):
- Vague language ("maybe", "should consider")
- No clear owner
- Conditional statements
- Disagreement among participants
```

---

## Context Window Optimization

### 1. Prompt Compression Techniques

**Remove redundancy while preserving meaning:**

```
INSTEAD OF:
"Please analyze the following meeting transcript and extract all action items. An action item is something that someone needs to do. Please identify who needs to do it and when they need to do it by."

USE:
"Extract action items with owner and deadline from this transcript:"
```

### 2. Strategic Information Placement

**Research shows Gemini has best recall for information at the beginning and end of prompts:**

```
[CRITICAL INSTRUCTIONS - Start]
Must extract ALL action items, even implicit ones.
Flag any ambiguous ownership or deadlines.

[CONTEXT/EXAMPLES - Middle]
[Few-shot examples here]

[TRANSCRIPT - Large content block]
[Meeting transcript here]

[REMINDER OF KEY TASK - End]
Remember: Identify implicit commitments and inferred deadlines.
Return structured JSON with all action items found.
```

### 3. Chunking Strategies for Long Transcripts

**Semantic Chunking Prompt:**
```
First pass - Identify topic boundaries:
"Mark where the discussion shifts to a new agenda item or topic."

Second pass - Extract from chunks:
"Extract action items from this segment, maintaining context from the overall meeting about attendees and project background."

Final pass - Consolidate:
"Merge these action items, removing duplicates and resolving any conflicts in ownership or deadlines."
```

### 4. Focus Windows for Different Meeting Phases

```
For long transcripts, use targeted extraction:

MEETING_START_PROMPT = """
Focus on the first 10% of the transcript.
Typically contains: Agenda review, previous action items follow-up
Extract: Carried-over tasks, confirmed deadlines
"""

MEETING_MIDDLE_PROMPT = """
Focus on the main discussion (10-80% of transcript).
Typically contains: Problem-solving, decisions, new assignments
Extract: New action items, dependencies, decision-based tasks
"""

MEETING_END_PROMPT = """
Focus on the last 20% of the transcript.
Typically contains: Summary, next steps, confirmations
Extract: Confirmed action items, final deadlines, follow-up meetings
"""
```

---

## Prompt Templates for Different Meeting Types

### 1. Sprint Planning Meeting

```
You are analyzing a SPRINT PLANNING meeting transcript.

Key patterns to identify:
- Story assignments (who will work on which user story)
- Story point estimates
- Sprint goals and commitments
- Dependencies between stories
- Definition of done for each item

Expected action item format:
- Task: [Story ID] - [Story description]
- Owner: [Developer name]
- Deadline: End of sprint ([date])
- Story Points: [number]
- Acceptance Criteria: [specific criteria mentioned]

Pay special attention to:
- "I'll take..." → ownership commitment
- "This depends on..." → dependency tracking
- "We need to complete... first" → priority ordering
```

### 2. Executive/Leadership Meeting

```
You are analyzing an EXECUTIVE LEADERSHIP meeting transcript.

Focus on:
- Strategic decisions requiring implementation
- Budget approvals and resource allocations
- Policy changes requiring communication
- Compliance/regulatory action items
- Cross-department initiatives

Expected output emphasis:
- Impact level: Organization-wide, Department, Team
- Budget implications if mentioned
- Stakeholders affected
- Communication requirements
- Board reporting requirements

Note: Executive meetings often have implicit delegations. When an executive mentions a need, infer delegation to their direct reports.
```

### 3. Client/Sales Meeting

```
You are analyzing a CLIENT/SALES meeting transcript.

Critical extraction points:
- Client requests and requirements
- Promises made to the client (even tentative)
- Follow-up items mentioned
- Documentation to be shared
- Internal actions needed to fulfill client needs

Special handling:
- Separate internal vs. client-facing action items
- Note any deadlines promised to client (these are HIGH PRIORITY)
- Extract both explicit commits and items where we said "we'll look into"
- Flag any scope changes or feature requests

Format:
{
  "client_facing_actions": [...],
  "internal_actions": [...],
  "tentative_commitments": [items where we said we'd investigate]
}
```

### 4. Daily Standup

```
You are analyzing a DAILY STANDUP meeting transcript.

Expected pattern:
Each person discusses:
1. What they did yesterday
2. What they'll do today
3. Any blockers

Extract only:
- Today's commitments (these become action items)
- Blockers requiring resolution
- Help needed from specific team members

Ignore:
- Yesterday's completed work
- General status updates

Output format:
{
  "person_name": {
    "today_commitment": [...],
    "blockers": [...],
    "needs_from_others": [...]
  }
}
```

### 5. Retrospective Meeting

```
You are analyzing a RETROSPECTIVE meeting transcript.

Focus areas:
- Improvement actions (must extract ALL)
- Process changes agreed upon
- Experiments to try in next sprint
- Tools or training needs identified

Categorize actions as:
- START: New practices to begin
- STOP: Practices to discontinue
- CONTINUE: Practices to maintain (usually not action items)
- IMPROVE: Existing practices to modify

Special note: Retrospective actions are often owned by the Scrum Master or team collectively. If no owner specified, default to "Team" or "Scrum Master" based on context.
```

## Key Prompt Engineering Takeaways

### The 10 Commandments of Meeting Transcript Prompts

1. **Use structured delimiters** (XML tags or markdown sections) to separate prompt components
2. **Provide 2-5 diverse examples** covering edge cases and negative examples
3. **Explicitly define output schema** with field types and formats
4. **Include confidence scoring** for extracted items
5. **Place critical instructions** at the beginning and end of prompts
6. **Use role-based prompting** to invoke expert-level analysis
7. **Break complex analysis into steps** (chain-of-thought)
8. **Define classification frameworks** for ambiguous items
9. **Customize prompts for meeting types** to capture domain-specific patterns
10. **Include negative examples** to prevent over-extraction

### Performance Optimization Tips

- **Token efficiency:** JSON > XML (20-30% fewer tokens)
- **Accuracy boost:** Few-shot examples improve accuracy by 40-60%
- **Role assignment:** Expert role prompts show 15-20% better performance
- **Instruction placement:** Beginning + end reminders improve recall by 25%
- **Explicit formatting:** Exact output examples reduce format errors by 80%

### Common Pitfalls to Avoid

❌ Vague instructions like "extract important stuff"
❌ No examples or only positive examples
❌ Inconsistent formatting between examples
❌ Missing edge case handling
❌ No confidence scoring or ambiguity handling
❌ Overly complex nested structures
❌ Assuming context without providing it
❌ No distinction between meeting types
❌ Ignoring implicit commitments
❌ Not specifying how to handle missing information

This focused approach to prompt engineering ensures consistent, accurate extraction of action items from meeting transcripts while properly handling ambiguity and maintaining context.