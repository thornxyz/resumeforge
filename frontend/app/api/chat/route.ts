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
        const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash-exp" });

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

CRITICAL: You MUST respond with ONLY a valid JSON object in this EXACT format. Do not include any other text before or after the JSON:

{
  "explanation": "Brief explanation of what you changed",
  "modifiedLatex": "The complete modified LaTeX code here",
  "hasChanges": true
}

Guidelines:
- Make precise modifications based on the user's request
- If no changes are needed, set hasChanges to false and leave modifiedLatex as the original code
- Always return the complete LaTeX document, not just the changed parts
- Keep the explanation concise and specific
- Ensure the JSON is valid and properly escaped

RESPOND WITH ONLY THE JSON OBJECT:`;
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

                // Try to find JSON object
                const jsonMatch = cleanedText.match(/\{[\s\S]*\}/);
                if (jsonMatch) {
                    const parsedResponse = JSON.parse(jsonMatch[0]);

                    // Validate the response has required fields
                    if (parsedResponse.explanation && typeof parsedResponse.hasChanges === 'boolean') {
                        return NextResponse.json({
                            success: true,
                            explanation: parsedResponse.explanation,
                            modifiedLatex: parsedResponse.hasChanges ? parsedResponse.modifiedLatex : null,
                            response: parsedResponse.explanation
                        });
                    }
                }

                // If we can't parse as JSON, try to parse as direct JSON
                try {
                    const directParse = JSON.parse(cleanedText);
                    return NextResponse.json({
                        success: true,
                        explanation: directParse.explanation,
                        modifiedLatex: directParse.hasChanges ? directParse.modifiedLatex : null,
                        response: directParse.explanation
                    });
                } catch (directParseError) {
                    // Final fallback - treat as regular response
                    console.log("Failed to parse JSON response:", cleanedText);
                    return NextResponse.json({
                        success: true,
                        response: text,
                        explanation: "I couldn't process that request properly. Please try rephrasing."
                    });
                }
            } catch (parseError) {
                console.log("JSON parsing error:", parseError);
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
