## Architecture Overview

ResumeForge is a microservices stack with 4 containers orchestrated via `docker-compose.yml`:

- **`frontend/`** (Next.js 15 App Router + TypeScript) – Monaco editor UI (`components/editor.tsx`), chat panel, dashboard, API routes under `app/api/*`
- **`code-agent/`** (FastAPI + LangGraph) – `/chat`, `/compile-latex`, `/format-latex` endpoints; orchestrates Gemini-powered workflow in `backend/`
- **`latex-api/`** (FastAPI + pdflatex) – Isolated LaTeX compiler returning PDFs or JSON diagnostics
- **`postgres`** – User auth (NextAuth) and resume storage (Prisma)

PDFs are shared via the `uploads` volume mounted at `frontend/public/uploads`.

## Critical Data Flow

### Chat Request Pipeline

1. Frontend POST to `/api/chat/route.ts` → sanitizes payload (message, last 10 messages, mode, latexContent, threadId)
2. Forwards to `${FASTAPI_URL}/chat` → `code-agent/main.py` receives ChatRequest
3. LangGraph workflow executes: `mode_detector → parser → gemini_{ask|edit} → compiler → formatter → file_writer`
4. Returns ChatResponse with `mode`, `modifiedLatex`, `explanation`, `toolsUsed`, `compilation_result`
5. Frontend applies via `onAgentProposal`, highlights diffs with `computeChangedLineRanges`, auto-compiles through `/api/compile`

### LangGraph State Machine (`backend/agent.py`)

- **AgentState** (TypedDict in `state.py`) is the shared graph state—nodes incrementally populate fields like `generated_code`, `compilation_result`, `iteration_count`
- **Retry logic**: `_route_compilation` re-enters `gemini_edit` on error until `max_iterations` (default 3) or success
- **Conditional routing**: `_route_mode` branches to `gemini_ask` (conversational) or `gemini_edit` (code generation) based on detected mode

### LLM Response Contract (`nodes/llm.py`)

- **Ask mode**: Conversational response, no full document generation
- **Edit mode**: MUST return ` one-line summary + ```latex full_document````. Enforced by  `ensure_complete_document`which validates presence of`\documentclass`, `\begin{document}`, `\end{document}`
- **Fallback**: If incomplete, `llm.py` reuses `state["current_document"]` and logs warning

## MCP Tooling (`backend/mcp/session.py`)

Custom in-process MCP implementation (`InProcessMCPSession`) exposes tools without transport layer:

- **`latex_compiler`**: Delegates to `tools/compiler.py` → POSTs to `latex-api:8000/compile`
- **`latex_formatter`**: Runs `tools/formatter.py` for whitespace normalization
- Tool invocations tracked in `MCPRegistry._invocations`, drained after execution to populate `state["tools_used"]`

## Frontend Patterns

### Editor State Management (`app/editor/editor-content.tsx`)

- **Dual state**: `latex` (current) vs `pendingLatex` (AI proposal) vs `baselineLatex` (before proposal)
- **Diff highlights**: `computeChangedLineRanges` compares old/new, Monaco decorations applied in `components/editor.tsx`
- **Suppress loop**: `suppressNextEditorChangeRef` prevents re-triggers during programmatic updates

### Chat Conversation (`components/chat.tsx`)

- **ThreadId persistence**: `threadIdRef.current` generated once with `crypto.randomUUID()`, stable across turns for LangGraph's `MemorySaver` checkpointer
- **History trimming**: `.slice(-10)` keeps only last 10 messages when POSTing to `/api/chat`
- **Tools display**: Appends `_Tools used: {tools}_` markdown footer if `toolsUsed` array present

### Server Actions (`lib/actions.ts`)

- ALL actions MUST `await auth()` first—throws if unauthorized
- ALL use shared Prisma client from `prisma.ts` (NOT `new PrismaClient()`)
- MUST `revalidatePath("/")` after mutations to update dashboard cache
- Date serialization: `.map(r => ({ ...r, createdAt: r.createdAt.toISOString() }))` to avoid Next.js hydration mismatches

## Development Commands

### Local Setup (Incremental)

```bash
# Infrastructure only
docker compose up -d postgres latex-api

# Frontend (separate terminal)
cd frontend
pnpm install
npx prisma generate
npx prisma migrate deploy  # Apply migrations
pnpm dev  # http://localhost:3000

# Agent (separate terminal)
cd code-agent
export GEMINI_API_KEY=...
export FASTAPI_URL=http://localhost:8001  # For frontend in .env.local
export LATEX_API_URL=http://localhost:8000
uv sync
uv run main.py  # http://localhost:8001
```

### Full Docker Stack

```bash
# Requires .env with GEMINI_API_KEY, AUTH_GOOGLE_ID, AUTH_GOOGLE_SECRET, AUTH_SECRET
docker compose up -d
```

### Smoke Tests

- GET `http://localhost:8001/health` → `{"status": "healthy", ...}`
- GET `http://localhost:8000/health` → `{"status": "ok"}`
- POST `/api/compile` with sample LaTeX → should return PDF or JSON error

## Configuration (`code-agent/backend/config.py`)

`AgentConfig` (frozen dataclass) loaded via `load_config()`:

- **Required**: `GEMINI_API_KEY`
- **Optional**: `GEMINI_MODEL` (default: `gemini-2.0-flash-exp`), `GEMINI_TEMPERATURE` (0.2), `AGENT_MAX_ITERATIONS` (3), `LATEX_API_URL`, `LATEX_API_TIMEOUT`
- Cached with `@lru_cache(maxsize=1)` for singleton behavior

## Critical Gotchas

1. **Edit mode completeness**: Partial LaTeX snippets are REJECTED—`ensure_complete_document` checks for `\documentclass`, `\begin{document}`, `\end{document}`. Fallback to prior state if missing.
2. **ThreadId stability**: Must persist `threadId` across chat turns (see `chat.tsx` `threadIdRef`) or LangGraph loses conversation context.
3. **Prisma regeneration**: Run `npx prisma generate` after any `schema.prisma` change, BEFORE `pnpm build`.
4. **PDF caching**: Agent stores PDFs in `AgentConfig.temp_dir` (`/tmp/latex_compile`)—clean manually if disk fills.
5. **LaTeX API modes**: Default streams PDF bytes; add `?json=1` for JSON diagnostics (see `latex-api/main.py`).
6. **Docker vs local URLs**: In Docker, services use internal DNS (`http://latex-api:8000`); outside Docker use `localhost` ports.
7. **No test suite**: Verify via compile loop + health endpoints. Future: Add pytest for agent, Playwright for frontend.
