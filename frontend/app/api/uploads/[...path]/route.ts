import { NextRequest, NextResponse } from "next/server";
import path from "path";
import { readFile, stat } from "fs/promises";

export const runtime = "nodejs";

export async function GET(
    _request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> },
) {
    const { path: segments } = await params;

    if (!segments || segments.length === 0) {
        return NextResponse.json({ error: "File path is required" }, { status: 400 });
    }

    // Prevent directory traversal or nested path injection
    if (segments.some((segment) => segment.includes("..") || segment.includes("/"))) {
        return NextResponse.json({ error: "Invalid path" }, { status: 400 });
    }

    const fileName = segments[segments.length - 1];
    if (!fileName || !fileName.toLowerCase().endsWith(".pdf")) {
        return NextResponse.json({ error: "Unsupported file type" }, { status: 400 });
    }

    // Resolve file location in /public/uploads
    const filePath = path.join(process.cwd(), "public", "uploads", ...segments);

    try {
        const fileStat = await stat(filePath);
        if (!fileStat.isFile()) {
            return NextResponse.json({ error: "File not found" }, { status: 404 });
        }

        const fileBuffer = await readFile(filePath);
        const body = Uint8Array.from(fileBuffer);

        return new NextResponse(body, {
            headers: {
                "Content-Type": "application/pdf",
                "Content-Disposition": `inline; filename="${fileName}"`,
                "Cache-Control": "public, max-age=31536000, immutable",
            },
        });
    } catch (error) {
        if ((error as NodeJS.ErrnoException)?.code === "ENOENT") {
            return NextResponse.json({ error: "File not found" }, { status: 404 });
        }
        console.error("Error serving uploaded PDF:", error);
        return NextResponse.json({ error: "Failed to load file" }, { status: 500 });
    }
}