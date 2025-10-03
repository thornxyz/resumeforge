# Bug Fix: Partial Resume Replacement Issue

## Problem

When users asked the agent to edit a specific part of their resume (e.g., "update my experience section"), the agent would sometimes replace the entire resume with only the modified section, losing all other content.

## Root Cause

The issue had two main causes:

1. **Insufficient LLM Instruction**: The system prompt didn't explicitly instruct the LLM to always return complete documents when making partial edits.

2. **No Snippet Detection**: The code extracted any LaTeX block from the response without validating whether it was a complete document or just a snippet.

## Solution

Applied a multi-layered fix:

### 1. Enhanced System Prompt (`_get_system_prompt`)

Added a new section **"CRITICAL RULE FOR LATEX OUTPUT"** that explicitly instructs the LLM:

- Always return the COMPLETE document when providing LaTeX code
- Never return only the modified section
- Include everything from `\documentclass` to `\end{document}`
- Provides clear examples of correct vs. incorrect behavior

### 2. Snippet Detection (`_extract_latex_from_response`)

Added validation to check if extracted LaTeX is a complete document:

- Checks for presence of `\documentclass`, `\begin{document}`, and `\end{document}`
- If any are missing and it looks like a section snippet, returns `None` instead of the snippet
- Prevents accidental replacement of full document with partial content

### 3. Contextual Prompting (`_create_comprehensive_prompt`)

Added special emphasis when the intent is to modify/enhance/format:

- Adds an extra warning section to the prompt
- Reinforces the requirement to return the complete document
- Only activates when there's an existing resume being modified

## Files Modified

- `/home/thorn/files/resumeforge/code-agent/agent.py`

## Testing Recommendations

Test the following scenarios:

1. **Partial Edit**: "Change my job title in the experience section"
   - Expected: Full document with only job title changed
2. **Add Content**: "Add Python to my skills"
   - Expected: Full document with Python added to skills section
3. **Remove Content**: "Remove the summary section"
   - Expected: Full document without summary section
4. **Full Replace**: "Here's my new resume: [complete LaTeX]"
   - Expected: Replace with the new complete document

## Benefits

- Users won't lose resume content when making small edits
- More reliable and predictable editing behavior
- Better user experience with incremental resume building
- Maintains document integrity throughout the conversation
