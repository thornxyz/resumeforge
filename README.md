# ResumeForge

An AI-assisted resume editor.

## Features

- Monaco-based LaTeX editor with AI-assisted "ask" and "edit" modes
- Inline diff highlighting and undo/approve flow for agent proposals
- Automatic PDF compilation via a dedicated `latex-api` service
- Resume storage with Prisma/PostgreSQL and Google OAuth via NextAuth
- Dockerized stack with separate services for the frontend, AI agent, and compiler

## Architecture

| Service            | Purpose                                                                                                                                                           | Location                  |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| Frontend           | Next.js 15 App Router app that hosts the editor, chat panel, dashboard, and API routes (`/api/chat`, `/api/compile`, `/api/save-resume`, `/api/update-resume`).   | `frontend/`               |
| AI Agent           | FastAPI bridge exposing `/chat`, `/compile-latex`, `/format-latex`, orchestrating a LangGraph workflow that calls Gemini, formats output, and records tool usage. | `code-agent/`             |
| LangGraph workflow | Nodes for mode detection → parsing → Gemini ask/edit → compile → format → file write, plus MCP tooling that proxies compilation/formatting.                       | `code-agent/backend/`     |
| LaTeX API          | FastAPI wrapper around `pdflatex` running in nonstop mode and returning PDFs or diagnostics.                                                                      | `latex-api/`              |
| Database           | PostgreSQL for user and resume storage.                                                                                                                           | Docker `postgres` service |

Compilation flow:

1. The frontend posts chat payloads (message, last 10 turns, mode, optional LaTeX, `threadId`) to the agent's `/chat` endpoint.
2. The LangGraph agent picks "ask" or "edit", calls Gemini, and—on edit—loops through compilation/formatting until success or `AgentConfig.max_iterations` (default 3).
3. The frontend applies the resulting LaTeX via `onAgentProposal`, highlights diffs with `computeChangedLineRanges`, recompiles through `/api/compile`, and persists PDFs with Prisma.

## Prerequisites

- Docker & Docker Compose
- Node.js 20+ with pnpm (frontend development)
- Python 3.13+ with [uv](https://github.com/astral-sh/uv) (agent development)
- Google Gemini API key (for the agent)
- Google OAuth credentials (for production auth)

## Environment

Create a root `.env` and share it across services:

```env
# Database / Prisma
DATABASE_URL=postgresql://admin:admin@localhost:5432/resumes

# NextAuth
AUTH_SECRET=your-secret-key

# Google OAuth
AUTH_GOOGLE_ID=...
AUTH_GOOGLE_SECRET=...

# Gemini
GEMINI_API_KEY=...

```

## Quick start (Docker)

```bash
git clone https://github.com/thornxyz/resumeforge.git
cd resumeforge
# create and fill .env using the values above
docker compose up -d
```

Now browse to:

- Frontend: <http://localhost:3000>
- AI Agent: <http://localhost:8001/health>
- LaTeX API: <http://localhost:8000/health>

## Local development:

### 1. Start shared services

```bash
docker compose up -d postgres latex-api
```

### 2. Run the frontend

```bash
cd frontend
pnpm install
npx prisma generate
npx --yes prisma migrate deploy
pnpm dev
```

### 3. Run the AI agent

```bash
cd code-agent
uv sync
uv run main.py
```

## Todo

- Improve LaTeX code generation with better system prompt, and prevent generation of wrong syntax.
- Add full LSP support (TexLab or Digestif) inside the Monaco editor.
- Resume template gallery.
- Extend the agent into an onboarding wizard that gathers resume data and exports multiple formats.
