import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import { prisma } from "@/prisma";
import { writeFile, mkdir } from "fs/promises";
import path from "path";

export async function PUT(req: NextRequest) {
    try {
        const session = await auth();

        if (!session?.user?.email) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const formData = await req.formData();
        const resumeId = formData.get("resumeId") as string;
        const title = formData.get("title") as string;
        const latexContent = formData.get("latexContent") as string;
        const pdfFile = formData.get("pdf") as File | null;

        if (!resumeId || !title || !latexContent) {
            return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
        }

        let pdfUrl: string | undefined;

        // If a new PDF file is provided, save it
        if (pdfFile) {
            // Create uploads directory if it doesn't exist
            const uploadsDir = path.join(process.cwd(), "public", "uploads");
            try {
                await mkdir(uploadsDir, { recursive: true });
            } catch (error) {
                // Directory might already exist
            }

            // Get the existing resume to check if it has a PDF URL
            const existingResume = await prisma.resume.findUnique({
                where: {
                    id: resumeId,
                    user: {
                        email: session.user.email
                    }
                }
            });

            let fileName: string;

            if (existingResume?.pdfUrl) {
                // Extract filename from existing URL to reuse it
                fileName = path.basename(existingResume.pdfUrl);
            } else {
                // Generate filename based on resume title for better organization
                const sanitizedTitle = title.toLowerCase()
                    .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
                    .replace(/\s+/g, '-') // Replace spaces with hyphens
                    .substring(0, 50); // Limit length

                const timestamp = Date.now();
                fileName = `${sanitizedTitle}_${timestamp}.pdf`;
            }

            const filePath = path.join(uploadsDir, fileName);

            // Save PDF file (this will overwrite the existing file if it exists)
            const buffer = Buffer.from(await pdfFile.arrayBuffer());
            await writeFile(filePath, buffer);

            pdfUrl = `/uploads/${fileName}`;
        }

        // Update in database
        const updateData: any = {
            title,
            latexContent,
        };

        if (pdfUrl) {
            updateData.pdfUrl = pdfUrl;
        }

        const resume = await prisma.resume.update({
            where: {
                id: resumeId,
                user: {
                    email: session.user.email
                }
            },
            data: updateData
        });

        return NextResponse.json({
            success: true,
            id: resume.id,
            pdfUrl: pdfUrl || resume.pdfUrl
        });

    } catch (error) {
        console.error("Error updating resume:", error);
        return NextResponse.json({ error: "Failed to update resume" }, { status: 500 });
    }
}
