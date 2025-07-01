FROM texlive/texlive:latest

RUN apt-get update && apt-get install -y python3 python3-pip python3-venv

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python packages in virtual environment
RUN pip install fastapi uvicorn python-multipart

WORKDIR /app
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]