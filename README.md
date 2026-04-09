# PDF Parser Comparison System

A full-stack application for uploading PDFs, getting AI-powered parser recommendations, and comparing extraction results side-by-side across **18 parsers**.

## Architecture

```
web/          Next.js 16 frontend (React 19, Tailwind, Zustand)
backend/      FastAPI API (upload, recommend, parse)
*.py          Root-level parser driver scripts (one per parser)
parsers/      Shared helper modules (e.g. paddle_ocr_core.py)
```

The backend runs each parser as a **subprocess** (`python <script>.py` with `cwd` set to a temp directory), discovers `extracted.txt` / `extracted.md` output, and returns page-wise text to the frontend.

## Supported Parsers

| Parser | OCR | Best for |
|--------|-----|----------|
| **pdfplumber** | No | Simple layout text/tables |
| **pdfminer** | No | Custom pipelines with layout data |
| **docling** | Yes | RAG / gen-AI all-purpose parsing |
| **doctr** | Yes | French/multilingual OCR pipelines |
| **marker** | Yes | LLM-powered markdown conversion |
| **unstructured** | Yes | RAG preprocessing |
| **mineru** | Yes | High-quality scientific/Chinese PDFs |
| **camelot** | No | Table extraction from digital PDFs |
| **tabula** | No | Table extraction (Java-based) |
| **easyocr** | Yes | Multilingual OCR pipelines |
| **paddleocr** | Yes | Asian-language OCR workloads |
| **tesseract** | Yes | CPU OCR baseline |
| **rapidocr** | Yes | Fast Chinese/English OCR |
| **suryaocr** | Yes | Complex OCR + layout workflows |
| **layoutparser** | Via backend | Custom document layout analysis |
| **liteparse** | Optional | LLM layout reasoning workflows |
| **grobif** | No | Academic metadata/citations (GROBID) |
| **llmsherpa** | Backend | Centralized app parsing (nlm-ingestor) |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker (for GROBID and nlm-ingestor services)
- A [Groq API key](https://console.groq.com/) for parser recommendations

### 1. Clone and set up the backend

```bash
cd pdf-auto
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env   # or create manually
```

Add your Groq key:

```
GROQ_API_KEY=gsk_your_key_here
```

### 3. Start external services (optional, for grobif / llmsherpa)

```bash
docker compose -f docker-compose.parsers.yml up -d
```

This starts:
- **nlm-ingestor** on `http://localhost:5010` (for llmsherpa parser)
- **GROBID** on `http://localhost:8070` (for grobif parser)

### 4. Run the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Run the frontend

```bash
cd web
npm install
npm run dev
```

Open **http://localhost:3000** in your browser.

## How It Works

1. **Upload** a PDF through the web UI.
2. **Describe** your use case (e.g. "extract tables from a financial report").
3. The backend calls **Groq** (LLM) to **recommend** the best 3 parsers from the 18 available, based on your description and each parser's strengths.
4. **Select** parsers (auto-selected from recommendations, or pick manually).
5. Click **Parse** to run the selected parsers. Results appear as **side-by-side page-wise text**.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/upload` | Upload a PDF, receive a `file_id` |
| `POST` | `/llm/recommend` | Get AI parser recommendations |
| `POST` | `/parse` | Run selected parsers on the uploaded PDF |
| `GET` | `/files/{file_id}` | Serve an uploaded PDF |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

### Parse request example

```json
{
  "file_id": "abc-123",
  "parsers": ["docling", "mineru", "pdfplumber"],
  "mineru_profile": "fast"
}
```

`mineru_profile` is optional (`fast` / `balanced` / `quality`) and only applies when `mineru` is selected.

## MinerU Run Profiles

When using the **mineru** parser, you can choose a speed/quality trade-off:

| Profile | Backend | Method | Formula | Table | Lang |
|---------|---------|--------|---------|-------|------|
| **fast** | pipeline | txt | off | off | en |
| **balanced** | pipeline | auto | off | on | en |
| **quality** | hybrid-auto-engine | auto | on | on | ch |

Set via the UI dropdown or `mineru_profile` in the API request.

## Docker Compose Files

| File | Services | Ports |
|------|----------|-------|
| `docker-compose.parsers.yml` | nlm-ingestor + GROBID | 5010, 8070 |
| `docker-compose.nlm-ingestor.yml` | nlm-ingestor only | 5010 |
| `docker-compose.grobid.yml` | GROBID only | 8070 |

GROBID is amd64-only; on Apple Silicon it runs under emulation (`platform: linux/amd64` is set).

## Environment Variables

### Backend (`.env` or shell)

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | (required) | Groq API key for LLM recommendations |

### Parser-specific (optional)

| Variable | Parser | Description |
|----------|--------|-------------|
| `GROBID_SERVER` | grobif | GROBID URL (default `http://localhost:8070`) |
| `LLMSHERPA_API_URL` | llmsherpa | nlm-ingestor URL (default `http://127.0.0.1:5010/api/parseDocument?renderFormat=all`) |
| `MINERU_BACKEND` | mineru | `pipeline` / `hybrid-auto-engine` etc. |
| `MINERU_METHOD` | mineru | `auto` / `txt` / `ocr` |
| `MINERU_SOURCE` | mineru | Path to PDF (auto-set by API) |
| `PADDLEOCR_SOURCE` | paddleocr | Path to PDF (auto-set by API) |
| `PADDLEOCR_LANG` | paddleocr | Language code (default `en`) |
| `PADDLEOCR_USE_GPU` | paddleocr | `1` for GPU |
| `LITEPARSE_OCR` | liteparse | `0` to disable OCR (faster) |
| `LITEPARSE_DPI` | liteparse | Render DPI (default `150`) |

## Project Structure

```
pdf-auto/
├── backend/
│   ├── main.py                    # FastAPI app
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # Groq API key (gitignored)
│   ├── models/
│   │   └── schemas.py             # Pydantic models
│   ├── routes/
│   │   ├── upload.py              # POST /upload
│   │   ├── llm.py                 # POST /llm/recommend
│   │   └── parse.py               # POST /parse
│   ├── services/
│   │   ├── llm_service.py         # Groq LLM recommendation logic
│   │   └── parser_service.py      # Subprocess runner + output discovery
│   └── utils/
│       └── file_handler.py        # Upload storage
├── web/
│   ├── package.json               # Next.js 16 + React 19
│   └── app/
│       ├── page.tsx               # Main page
│       ├── components/            # UI components
│       └── lib/
│           ├── api.ts             # Backend API client
│           └── store.ts           # Zustand state
├── parsers/
│   └── paddle_ocr_core.py        # PaddleOCR pipeline helper
├── *.py                           # 18 parser driver scripts
├── docker-compose.parsers.yml     # nlm-ingestor + GROBID
├── docker-compose.grobid.yml      # GROBID standalone
├── docker-compose.nlm-ingestor.yml # nlm-ingestor standalone
└── README.md
```

## License

Private project.
