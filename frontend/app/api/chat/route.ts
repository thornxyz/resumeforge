import { GoogleGenerativeAI } from '@google/generative-ai';
import { NextRequest, NextResponse } from 'next/server';

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);

export async function POST(request: NextRequest) {
    try {
        const { message, conversationHistory, latexContent, mode } = await request.json();

        if (!message || typeof message !== 'string') {
            return NextResponse.json(
                { error: 'Message is required and must be a string' },
                { status: 400 }
            );
        }

        if (!process.env.GEMINI_API_KEY) {
            return NextResponse.json(
                { error: 'Gemini API key is not configured' },
                { status: 500 }
            );
        }

        // Get the model
        const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

        // Build conversation context from history
        let conversationContext = "";
        if (conversationHistory && Array.isArray(conversationHistory)) {
            conversationContext = conversationHistory
                .slice(-10) // Only include last 10 messages for context
                .map((msg: any) => `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`)
                .join('\n');
        }

        let prompt: string;

        if (mode === "agent" && latexContent) {
            // Agent mode: modify LaTeX code based on natural language instructions
            prompt = `You are a LaTeX code assistant that helps users modify their resume code based on natural language instructions.

CURRENT LATEX CODE:
\`\`\`latex
${latexContent}
\`\`\`

USER INSTRUCTION: ${message}

${conversationContext ? `PREVIOUS CONVERSATION:\n${conversationContext}\n` : ''}

CRITICAL REQUIREMENTS:
1. You MUST actually modify the LaTeX code based on the user's request
2. You MUST respond with ONLY a valid JSON object in this EXACT format
3. Do NOT include any explanatory text before or after the JSON
4. Do NOT just explain what you would do - actually DO the modifications
5. ALWAYS include the complete modified LaTeX in the "modifiedLatex" field

REQUIRED JSON FORMAT:
{
  "explanation": "Brief explanation of what you changed",
  "modifiedLatex": "The complete modified LaTeX code with actual changes applied",
  "hasChanges": true
}

IMPORTANT: When you make ANY change (even small ones like changing a name), you MUST:
- Set "hasChanges": true
- Include the COMPLETE modified LaTeX code in "modifiedLatex"
- Do NOT set "hasChanges": false unless you truly cannot fulfill the request

EXAMPLES:
- If user says "make the font bigger", actually change \\fontsize or add \\large commands
- If user says "add a phone number", actually insert the phone number in the contact section
- If user says "change the color to blue", actually modify color commands like \\textcolor{blue}
- If user says "remove education section", actually delete those lines from the code

STRICT GUIDELINES:
- ALWAYS make the actual requested changes to the LaTeX code
- Set hasChanges to true when you make modifications
- Set hasChanges to false ONLY if the request cannot be fulfilled or no changes are truly needed
- Return the COMPLETE modified LaTeX document, not just snippets
- Ensure all LaTeX syntax remains valid after modifications
- Keep explanations brief but specific about what was actually changed

YOU MUST RESPOND WITH ONLY THE JSON OBJECT - NO OTHER TEXT:`;
        } else {
            // Regular chat mode
            prompt = `You are an AI assistant specialized in helping with LaTeX resume writing, formatting, and career advice. You should be helpful, professional, and provide practical guidance.

${conversationContext ? `Previous conversation:\n${conversationContext}\n\n` : ''}Current user message: ${message}

Please provide a helpful response:`;
        }

        // Generate response
        const result = await model.generateContent(prompt);
        const response = await result.response;
        const text = response.text();

        if (mode === "agent" && latexContent) {
            try {
                // Clean the response text and try to parse JSON
                let cleanedText = text.trim();

                // Remove any markdown code block formatting
                cleanedText = cleanedText.replace(/```json\s*/, '').replace(/```\s*$/, '');

                // Try to extract the first valid JSON object
                const jsonStart = cleanedText.indexOf('{');
                const jsonEnd = cleanedText.lastIndexOf('}');
                let jsonString = '';
                if (jsonStart !== -1 && jsonEnd !== -1 && jsonEnd > jsonStart) {
                    jsonString = cleanedText.substring(jsonStart, jsonEnd + 1);
                }

                if (jsonString) {
                    try {
                        // Try parsing directly first
                        const parsedResponse = JSON.parse(jsonString);
                        console.log("Raw AI response:", parsedResponse);
                        
                        if (parsedResponse.explanation) {
                            // Check if AI actually provided modified code
                            const hasActualChanges = parsedResponse.modifiedLatex && 
                                                   parsedResponse.modifiedLatex !== latexContent &&
                                                   parsedResponse.modifiedLatex.trim() !== latexContent.trim();
                            
                            console.log("Change detection:", {
                                aiSaysHasChanges: parsedResponse.hasChanges,
                                actuallyHasChanges: hasActualChanges,
                                explanation: parsedResponse.explanation,
                                modifiedLatexProvided: !!parsedResponse.modifiedLatex
                            });
                            
                            // Override AI's hasChanges if we detect actual changes
                            const finalHasChanges = hasActualChanges || parsedResponse.hasChanges === true;
                            
                            return NextResponse.json({
                                success: true,
                                explanation: parsedResponse.explanation,
                                modifiedLatex: finalHasChanges ? parsedResponse.modifiedLatex : null,
                                response: parsedResponse.explanation
                            });
                        }
                    } catch (jsonParseError) {
                        // Try to fix common issues: unescaped backslashes in string values
                        try {
                            // Only escape backslashes that are not already escaped and are inside string values
                            let safeJson = jsonString.replace(/\\(?![\\"'bnrtfu])/g, "\\\\");
                            const parsedResponse = JSON.parse(safeJson);
                            console.log("Sanitized AI response:", parsedResponse);
                            
                            if (parsedResponse.explanation) {
                                // Check if AI actually provided modified code
                                const hasActualChanges = parsedResponse.modifiedLatex && 
                                                       parsedResponse.modifiedLatex !== latexContent &&
                                                       parsedResponse.modifiedLatex.trim() !== latexContent.trim();
                                
                                // Override AI's hasChanges if we detect actual changes
                                const finalHasChanges = hasActualChanges || parsedResponse.hasChanges === true;
                                
                                return NextResponse.json({
                                    success: true,
                                    explanation: parsedResponse.explanation,
                                    modifiedLatex: finalHasChanges ? parsedResponse.modifiedLatex : null,
                                    response: parsedResponse.explanation
                                });
                            }
                        } catch (secondaryError) {
                            console.log("Failed to parse JSON after sanitization:", jsonString);
                        }
                    }
                }

                // If we can't parse as JSON, try to parse as direct JSON (whole cleanedText)
                try {
                    const directParse = JSON.parse(cleanedText);
                    return NextResponse.json({
                        success: true,
                        explanation: directParse.explanation,
                        modifiedLatex: directParse.hasChanges ? directParse.modifiedLatex : null,
                        response: directParse.explanation
                    });
                } catch (directParseError) {
                    console.log("Failed to parse JSON response (direct):", cleanedText);
                    return NextResponse.json({
                        success: true,
                        response: text,
                        explanation: "I couldn't process that request properly. Please try rephrasing."
                    });
                }
            } catch (parseError) {
                console.log("JSON parsing error (outer catch):", parseError);
                // Fallback to regular response if JSON parsing fails
                return NextResponse.json({
                    success: true,
                    response: text,
                    explanation: text
                });
            }
        } else {
            // Regular chat response
            return NextResponse.json({
                success: true,
                response: text
            });
        }

    } catch (error) {
        console.error('Error calling Gemini API:', error);

        // Handle specific Gemini API errors
        if (error instanceof Error) {
            if (error.message.includes('API_KEY_INVALID')) {
                return NextResponse.json(
                    { error: 'Invalid API key' },
                    { status: 401 }
                );
            }
            if (error.message.includes('QUOTA_EXCEEDED')) {
                return NextResponse.json(
                    { error: 'API quota exceeded' },
                    { status: 429 }
                );
            }
        }

        return NextResponse.json(
            { error: 'Failed to generate response' },
            { status: 500 }
        );
    }
}
