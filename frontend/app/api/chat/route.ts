import { GoogleGenerativeAI } from '@google/generative-ai';
import { NextRequest, NextResponse } from 'next/server';

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);

export async function POST(request: NextRequest) {
    try {
        const { message, conversationHistory } = await request.json();

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
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

        // Build conversation context from history
        let conversationContext = "";
        if (conversationHistory && Array.isArray(conversationHistory)) {
            conversationContext = conversationHistory
                .slice(-10) // Only include last 10 messages for context
                .map((msg: any) => `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`)
                .join('\n');
        }

        // Create the prompt with context
        const prompt = `You are an AI assistant specialized in helping with LaTeX resume writing, formatting, and career advice. You should be helpful, professional, and provide practical guidance.

${conversationContext ? `Previous conversation:\n${conversationContext}\n\n` : ''}Current user message: ${message}

Please provide a helpful response:`;

        // Generate response
        const result = await model.generateContent(prompt);
        const response = await result.response;
        const text = response.text();

        return NextResponse.json({
            success: true,
            response: text
        });

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
