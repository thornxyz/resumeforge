## Quick map

- `frontend/` is a Next.js 15 App Router UI; live editor state and preview hooks live in `app/editor/editor-content.tsx` and tie into Monaco via `components/editor.tsx`.
- `code-agent/` wraps the LangGraph-powered backend under `backend/`, exposed through FastAPI in `main.py`; Gemini credentials and MCP tooling are wired in `backend/config.py` and `backend/mcp/session.py`.
- `latex-api/` is an isolated FastAPI + `pdflatex` runner with `/compile` and `/health`; keep it running (Docker image includes TeX Live) for both frontend previews and agent validation.
- Data is stored with Prisma models in `frontend/prisma/schema.prisma`; authentication flows through NextAuth helpers in `frontend/auth.ts`.

## Local workflows

- Bring up Postgres + LaTeX first: `docker compose up -d postgres latex-api`. Full stack (`frontend` + services) also runs via `docker compose up -d` if env vars are ready.
- Frontend loop (run from `frontend/`): `pnpm install`, `npx prisma generate`, then `pnpm dev` (Turbopack). Use `pnpm lint` / `pnpm build` before shipping schema or UI changes.
- Agent loop (run from `code-agent/`): ensure `GEMINI_API_KEY` (and optionally `GEMINI_MODEL`, `LATEX_API_URL`) then `uv run main.py`. Install deps with `uv pip install -r requirements.txt` when adding libraries.
- Outside Docker the frontend expects `FASTAPI_URL=http://localhost:8001` and `LATEX_API_URL=http://localhost:8000`; inside Docker it targets `http://host.docker.internal:8001` for the agent.

## LangGraph agent flow

- `/chat` in `code-agent/main.py` normalizes the request and forwards it to `LangGraphResumeAgent.process`; replies must include `modifiedLatex`, `explanation`, and `toolsUsed` for the React chat (`components/chat.tsx`).
- Graph layout (`backend/agent.py`): `mode_detector` → `parser` → branch (`gemini_ask` or `gemini_edit`). Edit mode loops through `compiler` (MCP), optional retry, `formatter`, then `file_writer` for disk edits.
- `parser` summarises packages/sections via `backend/utils/latex_parser.py`; it feeds Gemini extra context and cursor-adjacent snippets.
- `gemini_edit` (in `backend/nodes/llm.py`) must output explanation + ```latex block; `ensure_complete_document`patches missing`\documentclass` so partial snippets are rejected.

## MCP tooling & compilation

- `backend/mcp/session.py` registers in-process MCP tools: `latex_compiler` delegates to `backend/tools/compiler.compile_latex`, `latex_formatter` to `backend/tools/formatter.format_latex`; tool names surface in the UI, so keep them stable.
- Compilation posts the full document to the external `latex-api` service and caches PDFs under `AgentConfig.temp_dir`; failures bubble back as `errors` and `log` used for iteration prompts.
- File writes (`backend/tools/file_writer.py`) whitelist extensions (`.tex/.bib/.cls/.sty`) and require `files_to_modify`; diffs are returned in unified format for audit.

## Frontend ↔ agent contract

- `/app/api/chat/route.ts` forwards the last 10 messages, editor text, mode, and `threadId`; any non-200 from FastAPI is mapped to UX-friendly errors (401, 429, 503).
- `components/chat.tsx` persists `threadId`, updates mode, and applies `modifiedLatex` only when `success` is true; it immediately triggers `/api/compile` so backend responses must stay JSON and `modifiedLatex` must be compile-ready.
- `/app/api/compile/route.ts` streams FormData (`file`) to the LaTeX API; use `axios` with `responseType: "arraybuffer"` and return a PDF `NextResponse`.
- Saving flows (`/api/save-resume`, `/api/update-resume`) expect FormData with `title`, `latexContent`, `pdf`; uploads land in `public/uploads` and Prisma rows connect to the signed-in user.

## Conventions & health

- Always hand back complete LaTeX documents; the agent discards partials and retries with the previous draft.
- Gemini outputs should explain first, then include a ```latex block—mirrors the prompt in `edit_with_gemini` and keeps chat rendering consistent.
- Reuse the shared Prisma client from `frontend/prisma.ts` and gate server actions with `auth()` to avoid session leaks.
- Health checks live at `/health` on both FastAPI apps; hit them during smoke tests because there’s no automated test suite yet.
