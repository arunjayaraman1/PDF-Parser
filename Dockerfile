# ── PDF-Parser backend (slim — docling + pdfium + pdfplumber) ────────────────
FROM python:3.11-slim

# System deps needed by docling / PyMuPDF / Pillow / opendataloader-pdf (Java 17)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        poppler-utils \
        openjdk-21-jre-headless \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies in stages (each layer is cached independently).
# Stage 1: fast core packages
RUN pip install --no-cache-dir --timeout 120 \
        fastapi>=0.115.0 \
        "uvicorn[standard]>=0.30.0" \
        python-multipart>=0.0.9 \
        aiofiles>=23.2.1 \
        "pydantic>=2.9.0" \
        python-dotenv>=1.0.0 \
        requests>=2.32.0 \
        "groq>=0.4.0" \
        "pypdfium2>=4.0.0" \
        "pypdf>=4.0.0" \
        "PyMuPDF>=1.24.0" \
        "pdfplumber>=0.11.0" \
        "Pillow>=10.0.0" \
        "pandas>=2.0.0" \
        "psutil>=5.9.0"

# Stage 2: docling (large, downloaded separately so a timeout only retries this layer)
RUN pip install --no-cache-dir --timeout 300 "docling>=2.0.0"

# Stage 3: opendataloader-pdf (requires Java 17)
RUN pip install --no-cache-dir --timeout 300 "opendataloader-pdf>=2.0.0"

# Copy the full project (backend code + parser scripts)
COPY backend/   ./backend/
COPY main_parsers/ ./main_parsers/
COPY parsers/   ./parsers/

# The backend's main.py uses relative imports from the backend/ directory
WORKDIR /app/backend

# Uploads directory (mounted as a volume in docker-compose for persistence)
RUN mkdir -p uploads/artifacts

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
