## High-level architecture

- `frontend/` (Next.js 15 App Router + TypeScript) drives the Monaco editor UI (`components/editor.tsx`), chat panel, dashboard, and API routes under `app/api/*`.
- `code-agent/` hosts the FastAPI bridge (`main.py`) that proxies chat calls to the LangGraph workflow under `backend/` and exposes `/chat`, `/compile-latex`, and `/format-latex`.
- `code-agent/backend/` contains LangGraph nodes (mode detection, parser, Gemini ask/edit, compiler, formatter, file writer), utility parsers, and an in-process MCP registry for tool calls.
- `latex-api/` is an isolated FastAPI service that shells `pdflatex` and returns either the compiled PDF or diagnostic JSON; both the agent and the frontend `/api/compile` route hit it.
- `docker-compose.yml` wires `postgres`, `latex-api`, `code-agent`, and `frontend`, sharing compiled PDFs through the `uploads` volume mounted at `public/uploads`.

## Request & compile flow

- `frontend/app/api/chat/route.ts` forwards sanitized payloads (message string, last 10 messages, normalized mode, optional LaTeX, `threadId`) to `${FASTAPI_URL}/chat`.
- `components/chat.tsx` maintains a persistent `threadId`, toggles "ask"/"edit", and expects `mode`, `modifiedLatex`, `explanation`, `toolsUsed`, and `compilation_result` fields from the agent.
- `app/editor/editor-content.tsx` applies AI proposals via `onAgentProposal`, highlights changed lines with `computeChangedLineRanges`, auto-compiles through `/api/compile`, and keeps the PDF URL ready for save/update flows.
- `/app/api/compile/route.ts` streams multipart blobs to `LATEX_API_URL/compile`; `/api/save-resume` and `/api/update-resume` persist PDFs to `public/uploads` and Prisma using multipart FormData.

## LangGraph agent rules

- `LangGraphResumeAgent` builds `mode_detector → parser → (gemini_ask | gemini_edit) → compiler → formatter → file_writer`, re-entering `gemini_edit` until compilation succeeds or `AgentConfig.max_iterations` (default 3) is reached.
- `parser.parse_context` uses `utils.latex_parser.analyse_document` to surface packages, sections, and a cursor-centric snippet that seed Gemini system prompts.
- `nodes.llm.edit_with_gemini` enforces a one-line summary followed by a full document inside `latex`; `ensure_complete_document` drops partial drafts and falls back to the prior LaTeX.
- `nodes.compiler` and `nodes.formatter` call MCP tools backed by `backend/tools/*`; every invocation is recorded so the frontend can display `toolsUsed`.
- `nodes.file_writer` writes only when `files_to_modify` targets existing paths with allowed suffixes (`.tex/.bib/.cls/.sty`); otherwise edits stay in memory.

## Frontend conventions

- `EditorContent` tracks `pendingLatex` vs `baseline`, enabling undo/approve flows and Monaco decorations (see `components/editor.tsx`) for visual diffing.
- `components/chat.tsx` trims conversation history to the last 10 messages, retries via `/api/chat`, and surfaces toast notifications keyed to `compilation_result`.
- Server actions in `lib/actions.ts` always call `auth()` and reuse the shared Prisma client from `prisma.ts`; invalidate dashboard data with `revalidatePath("/")` after mutations.
- Dashboard surfaces (`components/dashboard.tsx`, `resume-card.tsx`) expect ISO date strings and wire delete/edit actions through those server functions.

## Data, auth, and storage

- Prisma schema lives in `frontend/prisma/schema.prisma`; run `npx prisma generate` after schema edits so `pnpm build` has the generated client.
- NextAuth (`auth.ts` + `auth.config.ts`) is configured for Google OAuth with JWT sessions—server components gate access by calling `auth()`.
- Resume PDFs land in `public/uploads` with sanitized filenames; updates reuse the existing filename when present to avoid broken links.
- `DATABASE_URL` must point at the same Postgres instance the Prisma client uses (`postgres://admin:admin@postgres:5432/resumes` in Docker).

## Local development loops

- Start infrastructure with `docker compose up -d postgres latex-api`; add `code-agent`/`frontend` or run the full stack once env vars are in place.
- Frontend: from `frontend/`, run `pnpm install`, `npx prisma generate`, then `pnpm dev`; use `pnpm lint` / `pnpm build` before shipping changes.
- Agent: from `code-agent/`, export `GEMINI_API_KEY` (plus optional `GEMINI_MODEL`, `AGENT_MAX_ITERATIONS`, `LATEX_API_URL`) and run `uv run main.py`; add dependencies via `uv sync`/`uv pip install`.
- Outside Docker set `FASTAPI_URL=http://localhost:8001` and `LATEX_API_URL=http://localhost:8000` so frontend API routes reach local services.
- Quick smoke tests hit `/health` on both FastAPI apps and compile a sample resume through `/api/compile`.

## Gotchas & tips

- Edit-mode responses must include the full LaTeX document; partial snippets are discarded and the prior draft is reused.
- Keep `threadId` stable between chat turns so LangGraph’s `MemorySaver` checkpoint maintains context.
- The agent caches compiled PDFs under `AgentConfig.temp_dir` (`/tmp/latex_compile` by default); clean it if disk usage spikes.
- `latex-api` supports `?json=1` for structured logs during debugging; otherwise it streams raw PDFs.
- There’s no automated test suite yet—lean on the compile loop and the two `/health` endpoints for verification before shipping.
