# PDF-Parser

A standalone microservice and comparison UI for PDF text extraction.

```
Browser / RAG-Module
       │  POST /upload  +  POST /parse
       ▼
┌─────────────────────────────────────────────────────┐
│                  PDF-Parser API (FastAPI)            │
│  /upload → store PDF, return file_id                │
│  /parse  → run parser subprocess, return pages      │
│  /llm/recommend → Groq ranks best parsers for use   │
└─────────────────────────────────────────────────────┘
       │  subprocess per parser
       ▼
┌──────────────────────────────────────────────────────┐
│  docling │ pdfium │ pdfplumber │ opendataloader │ … │
└──────────────────────────────────────────────────────┘
```

## Parser registry

### Primary parsers (bundled in slim Docker image)

| Name | Library | Output | Speed | Best for |
|------|---------|--------|-------|---------|
| `docling` | docling | Structured Markdown | 1–3 s/page | RAG pipelines, tables, headings |
| `pdfium` | pypdfium2 | Plain text | < 10 ms/page | Large PDFs, speed-critical |
| `pdfplumber` | pdfplumber | Markdown + tables | 0.5–1 s/page | Table-heavy documents |
| `opendataloader` | opendataloader-pdf | Markdown + JSON + HTML | 3–5 s/page | Multi-format output, RAG |

### Additional parsers (require full install or GPU)

| Name | Library | Notes |
|------|---------|-------|
| `marker` | marker-pdf | Best quality markdown; slow; GPU recommended |
| `doctr` | python-doctr | OCR + bounding boxes; GPU recommended |
| `llmsherpha` | llmsherpa | Hierarchical JSON; requires nlm-ingestor service |
| `mineru` | mineru | MinerU CLI; outputs MD + JSON + images |
| `pdfminer` | pdfminer.six | Layout-aware text |
| `unstructured` | unstructured | Element-based extraction |
| `camelot` | camelot-py | Table-focused extraction |
| `grobif` | grobid-client-python | Academic papers (TEI XML); requires GROBID service |
| `tesseract` | pytesseract | OCR via Tesseract binary |
| `paddleocr` | paddleocr | OCR; GPU optional |
| `easyocr` | easyocr | OCR; GPU optional |
| `rapidocr` | rapidocr | Fast OCR |
| `suryaocr` | surya-ocr | High-quality OCR |
| `tabula` | tabula-py | Java-based table extraction |
| `liteparse` | liteparse | Node.js CLI integration |

---

## Repository layout

```
PDF-Parser/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── requirements.txt         # Full dependency list (all parsers)
│   ├── requirements.slim.txt    # Slim list (docling + pdfium only, used in Docker)
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── routes/
│   │   ├── upload.py            # POST /upload
│   │   ├── parse.py             # POST /parse
│   │   ├── llm.py               # POST /llm/recommend
│   │   └── artifacts.py         # GET /artifacts/{file_id}/{parser}/download
│   ├── services/
│   │   ├── parser_service.py    # Subprocess runner + page splitting
│   │   └── llm_service.py       # Groq LLM recommendation logic
│   └── utils/
│       └── file_handler.py      # Upload storage + file_id mapping
├── main_parsers/
│   ├── docling.py               # Docling parser script
│   ├── marker.py                # Marker parser script
│   ├── pdfium.py                # Pdfium parser script
│   ├── doctr.py                 # Doctr parser script
│   ├── llmsherpha.py            # LLMSherpa parser script
│   └── opendataloader.py        # OpenDataLoader parser script
├── Unused-Parsers/              # Legacy parser scripts (14 parsers)
├── parsers/
│   └── paddle_ocr_core.py       # PaddleOCR shared helper
├── web/                         # Next.js comparison UI
│   ├── package.json
│   └── app/
│       ├── page.tsx             # Main comparison page
│       ├── components/          # UploadSection, ParserSelector, PdfViewer, …
│       └── lib/
│           ├── api.ts           # Backend API client
│           └── store.ts         # Zustand state management
├── Dockerfile                   # Slim production image
├── docker-compose.yml           # Standalone service on port 8000
├── docker-compose.parsers.yml   # nlm-ingestor (5010) + GROBID (8070)
├── docker-compose.grobid.yml    # GROBID standalone
└── docker-compose.nlm-ingestor.yml  # nlm-ingestor standalone
```

---

## Option A — Docker (recommended)

The Docker image uses `requirements.slim.txt` — it bundles **docling**, **pdfium**, **pdfplumber**, and **opendataloader**. This keeps the image at ~2.1 GB instead of 15+ GB. For `marker`, `doctr`, or GPU parsers use Option B.

### Prerequisites

| Tool | Notes |
|------|-------|
| Docker Desktop 4.x+ | https://www.docker.com/products/docker-desktop |
| Groq API key | https://console.groq.com/ — used for `/llm/recommend` only (not required for parsing) |

### 1. Enter the directory

```bash
cd PDF-Parser
```

### 2. Build and start

```bash
# Basic start (Groq key optional — only needed for parser recommendations)
GROQ_API_KEY=gsk_... docker compose up --build
```

Or set it in a `.env` file next to `docker-compose.yml`:

```bash
echo "GROQ_API_KEY=gsk_..." > .env
docker compose up --build
```

### 3. Verify

```bash
curl http://localhost:8000/health
# → {"status":"ok","service":"pdf-parser-comparison"}

curl http://localhost:8000/
# → {"message":"PDF Parser Comparison System API","docs":"/docs",...}
```

Swagger UI: http://localhost:8000/docs

### 4. Optional — start nlm-ingestor and GROBID

Required only if you want to use the `llmsherpha` or `grobif` parsers:

```bash
docker compose -f docker-compose.parsers.yml up -d
# nlm-ingestor → http://localhost:5010
# GROBID       → http://localhost:8070 (runs under emulation on Apple Silicon)
```

### 5. Stopping

```bash
docker compose down          # stop, keep uploads volume
docker compose down -v       # stop and delete uploads
```

### Docker rebuild rules

| What changed | Command needed |
|---|---|
| Python source / `requirements.slim.txt` | `docker compose build && docker compose up -d` |
| `GROQ_API_KEY` or other env var only | `docker compose up -d` (no rebuild) |

---

## Option B — Local (without Docker)

Use this when you need parsers not in the slim image (`marker`, `doctr`, GPU parsers) or want to develop the service itself.

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | 3.12 recommended |
| Node.js | 18+ | Only if running the comparison UI |
| Java | 11+ | Required by `opendataloader-pdf` |
| Java | 8+ | optional | Required by `tabula-py` |
| Tesseract | optional | Required by `tesseract` parser — `brew install tesseract` |
| Docker | optional | For GROBID and nlm-ingestor sidecar services |

### 1. Create virtual environment

```bash
cd PDF-Parser
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

**Slim install** (docling + pdfium + pdfplumber + opendataloader — enough for RAG-Module integration):

```bash
pip install -r backend/requirements.slim.txt
```

**Full install** (all parsers — takes 10–20 min, downloads large models):

```bash
pip install -r backend/requirements.txt
```

> Some packages in `requirements.txt` (`paddleocr`, `easyocr`, `surya-ocr`) download model weights on first use and require several GB of disk space.

### 3. Configure environment

Create `backend/.env`:

```bash
cp backend/.env.example backend/.env    # if .env.example exists
# or create manually:
echo "GROQ_API_KEY=gsk_..." > backend/.env
```

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | Groq API key — only used by `POST /llm/recommend` |
| `GROBID_SERVER` | `http://localhost:8070` | GROBID URL (for `grobif` parser) |
| `LLMSHERPA_API_URL` | `http://127.0.0.1:5010/api/parseDocument?renderFormat=all` | nlm-ingestor URL (for `llmsherpha` parser) |

### 4. Start the API

```bash
cd backend
uvicorn main:app --reload --port 8000
```

API available at http://localhost:8000 — Swagger UI at http://localhost:8000/docs.

### 5. Start the comparison UI (optional)

In a separate terminal:

```bash
cd web
npm install
npm run dev
```

UI available at http://localhost:3000.

### 6. Optional sidecar services

```bash
# Both nlm-ingestor + GROBID
docker compose -f docker-compose.parsers.yml up -d

# nlm-ingestor only (for llmsherpha parser)
docker compose -f docker-compose.nlm-ingestor.yml up -d

# GROBID only (for grobif parser)
docker compose -f docker-compose.grobid.yml up -d
```

---

## API reference

### `POST /upload`

Upload a PDF and receive a `file_id` to use in subsequent calls.

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@report.pdf"
```

Response:
```json
{"file_id": "a1b2c3d4-...", "file_path": "...", "filename": "report.pdf"}
```

### `POST /parse`

Run one or more parsers on an uploaded PDF.

```bash
curl -X POST http://localhost:8000/parse \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "a1b2c3d4-...",
    "parsers": ["docling", "pdfium"]
  }'
```

Request body:

| Field | Type | Description |
|-------|------|-------------|
| `file_id` | string | ID returned by `/upload` |
| `parsers` | string[] | List of parser names to run |
| `mineru_profile` | string | `fast` / `balanced` / `quality` — only applies to `mineru` parser |

Response:
```json
{
  "parsers": {
    "docling": [
      {"page": 1, "text": "# Document Title\n\nIntroduction..."},
      {"page": 2, "text": "## Section 2\n\nContent..."}
    ]
  },
  "parser_meta": {
    "docling": {
      "execution_time_ms": 1432,
      "output_files": ["report_extracted/extracted.md"],
      "artifacts_available": true
    }
  }
}
```

### `POST /llm/recommend`

Get AI-ranked parser recommendations for your use case.

```bash
curl -X POST http://localhost:8000/llm/recommend \
  -H "Content-Type: application/json" \
  -d '{"description": "extract tables from a financial report for RAG"}'
```

Response:
```json
{
  "parsers": [
    {"name": "docling", "reason": "Best semantic fit for RAG...", "rank": 1},
    {"name": "marker",  "reason": "Higher fidelity tables...",   "rank": 2},
    {"name": "pdfium",  "reason": "Fast fallback for plain text", "rank": 3}
  ]
}
```

Requires `GROQ_API_KEY`. Falls back to `[pdfium, docling, marker]` if the key is missing.

### `GET /artifacts/{file_id}/{parser_name}/download`

Download the raw parser output (markdown, JSON, images) as a ZIP archive.

```bash
curl -O http://localhost:8000/artifacts/a1b2c3d4-.../docling/download
```

### `GET /health`

```bash
curl http://localhost:8000/health
# → {"status":"ok","service":"pdf-parser-comparison"}
```

---

## Integration with RAG-Module

RAG-Module can delegate PDF parsing to this service automatically. Configure RAG-Module's `.env`:

```env
DEFAULT_PDF_PARSER=pdf_service
PDF_PARSER_SERVICE_URL=http://localhost:8000
PDF_PARSER_SERVICE_PARSER=docling
```

When RAG-Module runs in Docker and PDF-Parser runs on the host:

```env
PDF_PARSER_SERVICE_URL=http://host.docker.internal:8000
```

RAG-Module will then call:
1. `POST /upload` — send the PDF bytes, receive `file_id`
2. `POST /parse` — run `docling` (or whichever `PDF_PARSER_SERVICE_PARSER` is set to), receive page text
3. Concatenate pages → chunk → embed → store in pgvector

---

## MinerU profiles

When `mineru` is selected, pass `mineru_profile` to control the speed/quality tradeoff:

| Profile | Backend | Method | Formula | Tables | Use when |
|---------|---------|--------|---------|--------|---------|
| `fast` | pipeline | txt | off | off | Quick extraction, large files |
| `balanced` | pipeline | auto | off | on | General use (default) |
| `quality` | hybrid-auto-engine | auto | on | on | Research papers, complex layouts |

---

## Adding a new parser

1. Create `main_parsers/myparser.py`. The script must:
   - Read the PDF path from the `MYPARSER_SOURCE` env var
   - Write output to `{stem}_extracted/extracted.md` (or `extracted.txt`) in the current working directory
   - Use `--- Page N / Total ---` headers to separate pages (optional but recommended)
   - Exit with code 0 on success

2. Register it in `backend/services/parser_service.py`:
   ```python
   PARSER_FILES = {
       ...
       "myparser": "main_parsers/myparser.py",
   }
   ```

3. Install the required library in your virtual environment (or add to `requirements.slim.txt` for Docker).

That's it — the API automatically discovers and runs the script.
