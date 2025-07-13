import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import { prisma } from "@/prisma";
import { writeFile, mkdir } from "fs/promises";
import path from "path";

export async function POST(req: NextRequest) {
    try {
        const session = await auth();

        if (!session?.user?.email) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const formData = await req.formData();
        const title = formData.get("title") as string;
        const latexContent = formData.get("latexContent") as string;
        const pdfFile = formData.get("pdf") as File;

        if (!title || !latexContent || !pdfFile) {
            return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
        }

        // Create uploads directory if it doesn't exist
        const uploadsDir = path.join(process.cwd(), "public", "uploads");
        try {
            await mkdir(uploadsDir, { recursive: true });
        } catch (error) {
            // Directory might already exist
        }

        // Generate filename based on resume title for better organization
        const sanitizedTitle = title.toLowerCase()
            .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
            .replace(/\s+/g, '-') // Replace spaces with hyphens
            .substring(0, 50); // Limit length

        const timestamp = Date.now();
        const fileName = `${sanitizedTitle}_${timestamp}.pdf`;
        const filePath = path.join(uploadsDir, fileName);

        // Save PDF file
        const buffer = Buffer.from(await pdfFile.arrayBuffer());
        await writeFile(filePath, buffer);

        const pdfUrl = `/uploads/${fileName}`;

        // Save to database
        const resume = await prisma.resume.create({
            data: {
                title,
                latexContent,
                pdfUrl,
                user: {
                    connect: {
                        email: session.user.email
                    }
                }
            }
        });

        return NextResponse.json({
            success: true,
            id: resume.id,
            pdfUrl: pdfUrl
        });

    } catch (error) {
        console.error("Error saving resume:", error);
        return NextResponse.json({ error: "Failed to save resume" }, { status: 500 });
    }
}
