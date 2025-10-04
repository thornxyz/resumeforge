import { NextRequest, NextResponse } from 'next/server';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8001';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { message, conversationHistory, latexContent, mode, threadId } = body;
        const normalizedMode = mode === 'edit' ? 'edit' : 'ask';

        if (!message || typeof message !== 'string') {
            return NextResponse.json(
                { error: 'Message is required and must be a string' },
                { status: 400 }
            );
        }

        // Forward the request to the FastAPI server
        try {
            const response = await fetch(`${FASTAPI_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message,
                    conversationHistory: conversationHistory || [],
                    latexContent,
                    mode: normalizedMode,
                    threadId: typeof threadId === 'string' ? threadId : undefined,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                console.error('FastAPI error:', response.status, errorData);

                // Handle specific HTTP status codes
                if (response.status === 401) {
                    return NextResponse.json(
                        { error: 'API authentication failed. Please check the configuration.' },
                        { status: 401 }
                    );
                } else if (response.status === 429) {
                    return NextResponse.json(
                        { error: 'API rate limit exceeded. Please try again later.' },
                        { status: 429 }
                    );
                } else {
                    return NextResponse.json(
                        { error: errorData.detail || 'Failed to get response from AI service' },
                        { status: response.status }
                    );
                }
            }

            const data = await response.json();
            return NextResponse.json(data);

        } catch (fetchError) {
            console.error('Error connecting to FastAPI server:', fetchError);

            // Check if it's a connection error
            if (fetchError instanceof Error && fetchError.message.includes('ECONNREFUSED')) {
                return NextResponse.json(
                    { error: 'AI service is currently unavailable. Please try again later.' },
                    { status: 503 }
                );
            }

            return NextResponse.json(
                { error: 'Failed to connect to AI service' },
                { status: 500 }
            );
        }

    } catch (error) {
        console.error('Error in chat API route:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}
