## Architecture snapshot

- `frontend/` is a Next.js 15 App Router app that shells the Monaco editor (`components/editor.tsx`) and chat/workflow UI (`app/editor/editor-content.tsx`).
- `code-agent/` exposes FastAPI endpoints in `main.py` and orchestrates the LangGraph workflow defined under `backend/`.
- `latex-api/` is a FastAPI wrapper over `pdflatex`; compile requests come from both the agent and the frontend compile endpoint.
- `docker-compose.yml` wires the four services (`postgres`, `latex-api`, `code-agent`, `frontend`) and shares uploaded PDFs via the `uploads` volume.

## Conversational pipeline

- `/app/api/chat/route.ts` forwards sanitized chat payloads (last 10 messages, current doc, mode, `threadId`) to `FastAPI_URL`.
- `LangGraphResumeAgent` (`backend/agent.py`) runs `mode_detector → parser → gemini_ask|gemini_edit`. The edit branch loops through `compiler → formatter → file_writer` until compile succeeds or `AgentConfig.max_iterations` is reached.
- `parser` derives package/section summaries near the cursor for the system prompt, while `gemini_edit` enforces "explanation first, then `latex`" and rejects partial docs via `ensure_complete_document`.
- `backend/mcp/session.py` exposes `latex_compiler`/`latex_formatter`; every invocation is recorded so the chat UI can show `toolsUsed` badges.

## Local workflows

- Bring up data + TeX first: `docker compose up -d postgres latex-api`. Add `code-agent`/`frontend` once env vars are in place or run the whole stack with `docker compose up -d`.
- Frontend loop (from `frontend/`): `pnpm install` → `npx prisma generate` → `pnpm dev`. Run `pnpm lint` / `pnpm build` before shipping schema or UI changes.
- Agent loop (from `code-agent/`): export `GEMINI_API_KEY` (optionally `GEMINI_MODEL`, `LATEX_API_URL`) then `uv run main.py`. Add deps with `uv pip install -r requirements.txt` or edit `pyproject.toml` and re-lock.
- Outside Docker set `FASTAPI_URL=http://localhost:8001` and `LATEX_API_URL=http://localhost:8000`; compose sets internal hostnames (`code-agent`, `latex-api`).

## Frontend conventions

- `components/chat.tsx` expects responses with `mode`, `modifiedLatex`, `explanation`, and `toolsUsed`; when `mode === "edit"` and `success` it auto-applies the LaTeX and triggers `/api/compile`.
- `app/editor/editor-content.tsx` keeps LaTeX + PDF state in sync, auto-updating saved resumes after a successful compile.
- Server actions (`frontend/lib/actions.ts`) must call `auth()` and use the singleton Prisma client from `frontend/prisma.ts`; revalidate dashboard data with `revalidatePath("/")` after mutations.
- Follow the existing Tailwind + shadcn style primitives in `frontend/components/ui/*` when extending UI.

## Agent & tooling notes

- `AgentConfig` (env-driven) caps edit retries, points to the LaTeX API, and restricts writes to `.tex/.bib/.cls/.sty` via `backend/tools/file_writer.py`.
- `compile_document` posts the full document to `/compile`; failures feed the next Gemini turn with aggregated errors + log tail.
- `format_document` normalizes whitespace and list indentation so diffs stay minimal—leave it in the loop when adding nodes.
- `latex-api/main.py` runs `pdflatex` in nonstop mode and returns PDFs directly; pass `?json=1` only if you need structured logs.

## Data, auth, and storage

- Prisma schema lives in `frontend/prisma/schema.prisma`; run `npx prisma generate` after edits and keep migrations under `frontend/prisma/migrations`.
- NextAuth is configured in `frontend/auth.ts`/`auth.config.ts` with Google OAuth; JWT sessions are default, so server actions rely on `auth()` for identity.
- Upload endpoints store PDFs under `public/uploads` (mounted in Docker); `app/api/save-resume` and `/update-resume` require multipart FormData with `title`, `latexContent`, and `pdf`.

## Gotchas

- Always return a full LaTeX document in edit mode—partial snippets are discarded and the prior draft is reused.
- Keep `threadId` intact between chat turns so LangGraph’s MemorySaver can thread conversation state.
- Health checks live at `/health` on both FastAPI apps; there’s no automated test suite, so hit them during smoke tests.
- Prefer incremental diffs when touching LaTeX helpers—`apply_changes` writes directly to the target path once validation passes.
