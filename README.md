# PDF Parser Comparison System

A full-stack application for uploading PDFs, getting **ranked** AI parser recommendations, and comparing extraction results side-by-side.

## Architecture

```
web/              Next.js 16.2.2 frontend (React 19.2.4, Tailwind 4, Zustand)
backend/          FastAPI API (upload, recommend, parse)
main_parsers/     Primary ranked parser scripts (pdfium, marker, docling, doctr, llmsherpha)
Unused-Parsers/   Legacy parser scripts (backward-compatible)
parsers/          Shared helper modules (e.g. paddle_ocr_core.py)
```

The backend runs each parser as a **subprocess** (`python <script>.py` with `cwd` set to a temp directory), discovers `extracted.txt` / `extracted.md` output, and returns:
- page-wise text (`parsers`)
- per-parser run metadata (`parser_meta`) including execution time and output files.

## Parser Registry (runnable names)

Primary/main parsers:
- `pdfium`
- `llmsherpha` (alias supported: `llmsherpa`)
- `marker`
- `docling`
- `doctr`

Legacy/backward-compatible parsers (stored in `Unused-Parsers/`):
- `pdfplumber`, `camelot`, `pdfminer`, `unstructured`, `mineru`, `grobif`, `layoutparser`,
  `paddleocr`, `easyocr`, `tesseract`, `rapidocr`, `suryaocr`, `tabula`, `liteparse`

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
3. The backend calls **Groq** (LLM) to return the **top 3 ranked parsers** with:
   - `rank` (1 = best match)
   - use-case-specific reason (fit + tradeoffs)
4. **Select** parsers (auto-selected from recommendations, or pick manually).
5. Click **Parse** to run selected parsers. Results include:
   - page-wise extraction text
   - per-parser execution time + output file list
6. In Comparison View, each parser column supports **Full view** (2-pane mode: Original PDF + selected parser result).

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | API root with endpoint info |
| `POST` | `/upload` | Upload a PDF, receive a `file_id` |
| `POST` | `/llm/recommend` | Get AI parser recommendations |
| `POST` | `/parse` | Run selected parsers on the uploaded PDF |
| `GET` | `/files/{file_id}` | Serve an uploaded PDF |
| `GET` | `/artifacts/{file_id}/{parser_name}/download` | Download parser output artifacts as ZIP |
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

### Recommend response example

```json
{
  "parsers": [
    { "name": "docling", "reason": "Best semantic fit for RAG...", "rank": 1 },
    { "name": "marker", "reason": "Higher fidelity but slower...", "rank": 2 },
    { "name": "pdfium", "reason": "Fast fallback for plain text...", "rank": 3 }
  ]
}
```

### Parse response example

```json
{
  "parsers": {
    "docling": [
      { "page": 1, "text": "..." }
    ]
  },
  "parser_meta": {
    "docling": {
      "execution_time_ms": 1432,
      "output_files": ["sample_extracted/extracted.md"],
      "artifacts_available": true
    }
  }
}
```

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
| `LLMSHERPA_API_URL` | llmsherpha / llmsherpa | nlm-ingestor URL (default `http://127.0.0.1:5010/api/parseDocument?renderFormat=all`) |
| `MINERU_BACKEND` | mineru | `pipeline` / `hybrid-auto-engine` etc. |
| `MINERU_METHOD` | mineru | `auto` / `txt` / `ocr` |
| `MINERU_SOURCE` | mineru | Path to PDF (auto-set by API) |
| `PADDLEOCR_SOURCE` | paddleocr | Path to PDF (auto-set by API) |
| `PADDLEOCR_LANG` | paddleocr | Language code (default `en`) |
| `PADDLEOCR_USE_GPU` | paddleocr | `1` for GPU |
| `LITEPARSE_OCR` | liteparse | `0` to disable OCR (faster) |
| `LITEPARSE_DPI` | liteparse | Render DPI (default `150`) |
| `PDFIUM_SOURCE` | pdfium | Path to PDF (auto-set by API) |
| `CAMELOT_SOURCE` | camelot | Path to PDF (auto-set by API) |
| `MARKER_SOURCE` | marker | Path to PDF (auto-set by API) |
| `DOCLING_SOURCE` | docling | Path to PDF (auto-set by API) |
| `DOCTR_SOURCE` | doctr | Path to PDF (auto-set by API) |

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
│   │   ├── parse.py               # POST /parse
│   │   └── artifacts.py           # GET /artifacts/download
│   ├── services/
│   │   ├── llm_service.py         # Groq LLM recommendation logic
│   │   └── parser_service.py      # Subprocess runner + output discovery
│   ├── utils/
│   │   └── file_handler.py        # Upload storage
│   ├── uploads/                   # Uploaded PDF files
│   └── tmp-marker-check/          # Temp parser work directories
├── web/
│   ├── package.json               # Next.js 16.2.2 + React 19.2.4 + Tailwind 4
│   ├── next.config.ts             # Next.js configuration
│   └── app/
│       ├── page.tsx               # Main page
│       ├── layout.tsx             # Root layout
│       ├── globals.css            # Global styles
│       ├── components/
│       │   ├── UploadSection.tsx  # PDF upload UI
│       │   ├── ParserSelector.tsx # Parser selection UI
│       │   ├── ParseButton.tsx    # Parse execution button
│       │   ├── PdfViewer.tsx      # PDF rendering component
│       │   ├── Column.tsx         # Parser results column
│       │   ├── ParserOutput.tsx   # Parser text output display
│       │   └── SyncScrollContainer.tsx # Synchronized scroll container
│       └── lib/
│           ├── api.ts             # Backend API client
│           ├── store.ts           # Zustand state management
│           └── utils.ts            # Utility functions
├── parsers/
│   └── paddle_ocr_core.py        # PaddleOCR pipeline helper
├── main_parsers/                  # Primary ranked parser scripts
│   ├── pdfium.py
│   ├── llmsherpha.py
│   ├── marker.py
│   ├── docling.py
│   └── doctr.py
├── Unused-Parsers/                # Legacy parsers (backward-compatible)
│   ├── pdfplumber.py
│   ├── camelot.py
│   ├── pdfminer_runner.py
│   ├── unstructured.py
│   ├── MinorU.py
│   ├── grobif.py
│   ├── layoutparser.py
│   ├── paddle.py
│   ├── easyocr.py
│   ├── tesseract.py
│   ├── rapidocr.py
│   ├── suryaocr.py
│   ├── tabula.py
│   └── liteparse.py
├── marker_image.py               # Standalone marker image script
├── marker_output/                 # Marker parser output directory
├── output files/                  # Sample output files
├── docker-compose.parsers.yml     # nlm-ingestor + GROBID
├── docker-compose.grobid.yml      # GROBID standalone
├── docker-compose.nlm-ingestor.yml # nlm-ingestor standalone
└── README.md
## License

Private project.
