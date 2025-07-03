"use server";

import { signOut } from "@/auth";
import { auth } from "@/auth";
import { prisma } from "@/prisma";
import { revalidatePath } from "next/cache";

export async function handleSignOut() {
    await signOut();
}

export async function saveResume(title: string, latexContent: string, pdfUrl?: string) {
    const session = await auth();

    if (!session?.user?.email) {
        throw new Error("Unauthorized");
    }

    try {
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

        revalidatePath("/");
        return { success: true, id: resume.id };
    } catch (error) {
        console.error("Error saving resume:", error);
        throw new Error("Failed to save resume");
    }
}

export async function updateResume(id: string, title: string, latexContent: string, pdfUrl?: string) {
    const session = await auth();

    if (!session?.user?.email) {
        throw new Error("Unauthorized");
    }

    try {
        const resume = await prisma.resume.update({
            where: {
                id,
                user: {
                    email: session.user.email
                }
            },
            data: {
                title,
                latexContent,
                ...(pdfUrl && { pdfUrl })
            }
        });

        revalidatePath("/");
        return { success: true, id: resume.id };
    } catch (error) {
        console.error("Error updating resume:", error);
        throw new Error("Failed to update resume");
    }
}

export async function getUserResumes() {
    const session = await auth();

    if (!session?.user?.email) {
        return [];
    }

    try {
        const resumes = await prisma.resume.findMany({
            where: {
                user: {
                    email: session.user.email
                }
            },
            orderBy: {
                updatedAt: "desc"
            }
        });

        return resumes;
    } catch (error) {
        console.error("Error fetching resumes:", error);
        return [];
    }
}

export async function getResumeById(id: string) {
    const session = await auth();

    if (!session?.user?.email) {
        return null;
    }

    try {
        const resume = await prisma.resume.findFirst({
            where: {
                id,
                user: {
                    email: session.user.email
                }
            }
        });

        return resume;
    } catch (error) {
        console.error("Error fetching resume:", error);
        return null;
    }
}

export async function deleteResume(id: string) {
    const session = await auth();

    if (!session?.user?.email) {
        throw new Error("Unauthorized");
    }

    try {
        await prisma.resume.delete({
            where: {
                id,
                user: {
                    email: session.user.email
                }
            }
        });

        revalidatePath("/");
        return { success: true };
    } catch (error) {
        console.error("Error deleting resume:", error);
        throw new Error("Failed to delete resume");
    }
}
