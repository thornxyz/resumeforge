# ResumeForge

An AI-powered resume builder that allows you to vibecode your resume in latex.

## Tech Stack

### Frontend

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Monaco Editor** - Code editor for LaTeX editing
- **TailwindCSS** - Utility-first CSS framework
- **Prisma** - Database ORM
- **NextAuth.js** - Authentication
- **React PDF** - PDF rendering

### Backend

- **FastAPI** - Python API framework for the AI agent
- **Google Gemini AI** - LLM for conversational intelligence
- **LangChain** - AI agent orchestration
- **LaTeX API** - PDF compilation service
- **PostgreSQL** - Database

## Prerequisites

- Docker & Docker Compose
- Node.js 20+ & pnpm (for local frontend development)
- Python 3.13+ & uv (for local AI agent development)
- Google Gemini API key

## Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/thornxyz/resumeforge.git
   cd resumeforge
   ```

2. **Set up environment variables**

   Create a `.env` file in the root directory:

   ```env
   # Database
   DATABASE_URL=postgresql://admin:admin@localhost:5432/resumes

   # NextAuth
   AUTH_SECRET=your-secret-key-here

   # Google OAuth (optional)
   AUTH_GOOGLE_ID=your-google-client-id
   AUTH_GOOGLE_SECRET=your-google-client-secret

   # AI Agent
   GEMINI_API_KEY=your-gemini-api-key
   ```

3. **Start Docker services**

   This will set up the frontend, PostgreSQL database, and LaTeX API:

   ```bash
   docker compose up -d
   ```

4. **Start the AI agent**

   ```bash
   cd code-agent
   uv run main.py
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - AI Agent API: http://localhost:8001
   - LaTeX API: http://localhost:8000

## Development

### Start required services (Postgres & LaTeX API)

```bash
docker compose up -d postgres latex-api
```

### Run frontend in development mode

```bash
cd frontend
pnpm install
npx prisma generate
pnpm dev
```

### Run AI agent

```bash
cd code-agent
uv run main.py
```

## Todo

- **Improve LaTeX code generation**: Enhance the coding agent to validate LaTeX syntax and prevent compilation errors. Add error handling and retry logic for malformed LaTeX output.

- **Integrate Language Server Protocol (LSP)**: Add full LSP support to the Monaco editor for real-time LaTeX syntax checking etc. Consider integrating TexLab or Digestif language server.

- **Resume templates library**: Create a collection of professional resume templates (Modern, ATS-friendly, Academic, Creative) with preview functionality and one-click application.

- **Resume builder agent**: Develop an AI assistant to guide users through building resumes from scratch, including:
  - Interactive questionnaire for gathering user information
  - Smart content suggestions based on industry and role
  - Auto-formatting and section organization
  - Export to multiple formats (PDF, LaTeX source, Markdown)
