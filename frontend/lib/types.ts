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
    createdAt: Date;
    updatedAt: Date;
}

// Page props types
export interface EditorPageProps {
    searchParams: {
        resumeId?: string;
    };
}

// Component props types
export interface EditorContentProps {
    user: User;
    initialResume?: Resume | null;
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
