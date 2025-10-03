import { NextRequest, NextResponse } from "next/server";
import axios from "axios";

export async function POST(req: NextRequest) {
    const body = await req.formData();
    const file = body.get("file");

    if (!file || typeof file === "string") {
        return NextResponse.json({ error: "Missing or invalid file" }, { status: 400 });
    }

    // Create a new FormData instance for the external API call
    const form = new FormData();
    form.append("file", file, "resume.tex");

    try {
        const apiUrl = process.env.LATEX_API_URL || "http://localhost:8000";
        const response = await axios.post(`${apiUrl}/compile`, form, {
            responseType: "arraybuffer",
            headers: {
                "Content-Type": "multipart/form-data",
            },
        });

        const blob = new Blob([response.data], { type: "application/pdf" });
        return new NextResponse(blob, {
            status: 200,
            headers: {
                "Content-Type": "application/pdf",
                "Content-Disposition": "inline; filename=compiled.pdf",
            },
        });
    } catch (error) {
        console.error("Compilation error:", error);
        if (axios.isAxiosError(error) && error.response) {
            return NextResponse.json(
                { error: "LaTeX compilation failed", details: error.message },
                { status: error.response.status }
            );
        }
        return NextResponse.json(
            { error: "LaTeX compilation failed", details: error instanceof Error ? error.message : "Unknown error" },
            { status: 500 }
        );
    }
}
