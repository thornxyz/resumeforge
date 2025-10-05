FROM texlive/texlive:latest

# Install Python and pip in a single layer, clean up apt cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install Python packages in one layer with no-cache
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi==0.115.5 \
    uvicorn[standard]==0.32.1 \
    python-multipart==0.0.20

WORKDIR /app

# Create a non-root user for security
RUN groupadd --system --gid 1001 latex \
    && useradd --system --uid 1001 --gid latex latex \
    && chown -R latex:latex /app

# Copy application files
COPY --chown=latex:latex . .

USER latex

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

# Use uvicorn with workers for better performance
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
