import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
    const body = await req.formData();
    const file = body.get("file");

    if (!file || typeof file === "string") {
        return NextResponse.json({ error: "Missing or invalid file" }, { status: 400 });
    }

    // Create a new FormData instance for the external API call
    const form = new FormData();
    form.append("file", file, "resume.tex");

    const response = await fetch("http://localhost:8000/compile", {
        method: "POST",
        body: form,
    });

    if (!response.ok) {
        return NextResponse.json(
            { error: "LaTeX compilation failed" },
            { status: response.status }
        );
    }

    const blob = await response.blob();
    return new NextResponse(blob, {
        status: 200,
        headers: {
            "Content-Type": "application/pdf",
            "Content-Disposition": "inline; filename=compiled.pdf",
        },
    });
}
