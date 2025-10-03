// User types
export interface User {
    name?: string | null;
    email?: string | null;
    image?: string | null;
}

// Resume types
export interface Resume {
    id: string;
    title: string;
    latexContent: string;
    pdfUrl: string | null;
    createdAt: string;
    updatedAt: string;
}

// Page props types
export interface EditorPageProps {
    searchParams: Promise<{
        resumeId?: string;
    }>;
}

// Component props types
export interface EditorContentProps {
    user: User;
    initialResume?: Resume | null;
}

export interface ChatProps {
    latexContent: string;
    onLatexUpdate: (newLatex: string) => void;
    onCompile: (latexContent?: string) => void;
    messages: Message[];
    onMessagesUpdate: (messages: Message[]) => void;
}

export interface LatexEditorProps {
    value: string;
    onChange: (val: string | undefined) => void;
}

export interface PdfPreviewProps {
    pdfUrl: string;
    zoom?: number;
}

export interface ResumeCardProps {
    resume: Resume;
}

// Chat types
export interface Message {
    id: string;
    content: string;
    role: "user" | "assistant";
    timestamp: Date;
}
