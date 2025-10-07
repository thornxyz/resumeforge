FROM python:3.13-slim

# Install runtime dependencies and download Texlab release binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    tar \
    && rm -rf /var/lib/apt/lists/* && \
    curl -fsSL "https://github.com/latex-lsp/texlab/releases/download/v5.23.1/texlab-aarch64-linux.tar.gz" \
    | tar -xz -C /usr/local/bin texlab && \
    chmod +x /usr/local/bin/texlab

# Create virtual environment and install Python dependencies
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi==0.115.5 \
    uvicorn[standard]==0.32.1 \
    websockets==14.1

# Create a non-root user
RUN groupadd --system --gid 1001 texlab \
    && useradd --system --uid 1001 --gid texlab texlab

WORKDIR /app

# Copy application files
COPY --chown=texlab:texlab . .

# Change ownership
RUN chown -R texlab:texlab /app

USER texlab

EXPOSE 8002

ENV PYTHONUNBUFFERED=1

# Run the WebSocket server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8002"]
