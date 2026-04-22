# PDF Parser Comparison

I ran the same 26-page PDF (`meta.pdf`, 1 MB) through six parsers on my
laptop (CPU only). Here is what I found.

---

## Speed

| Parser           | Time                    | vs `pdfium` |
| ---------------- | ----------------------- | ----------: |
| `pdfium`         | **0.40 s**              |          1× |
| `opendataloader` | **3.99 s**              |         10× |
| `llmsherpa`      | **8.22 s**              |         21× |
| `docling`        | **23.83 s**             |         60× |
| `doctr`          | **229.16 s** (3m 49s)   |        573× |
| `marker`         | **1478.50 s** (24m 38s) |     ~3,700× |

`pdfium` is done in less than half a second. `marker` takes almost
25 minutes. Big gap.

---

## Output

| Parser           | Format                                        | Size    | Headings | Tables |
| ---------------- | --------------------------------------------- | ------: | -------: | -----: |
| `pdfium`         | `.txt`                                        | 83.9 KB |        0 |      0 |
| `opendataloader` | `.md` / `.json` / `.html` / `.txt` / PDF / images | 83.4 KB |       28 |      1 |
| `llmsherpa`      | `.json`                                       | 277.9 KB |       — |     17 |
| `docling`        | `.md`                                         | 85.7 KB |       29 |    100 |
| `doctr`          | `.md` (OCR)                                   | 82.4 KB |        0 |      0 |
| `marker`         | `.md`                                         | 91.5 KB |       29 |    100 |

---

## What each one does

| Parser           | Text | Headings | Tables  | Layout | Images | OCR |
| ---------------- | ---- | -------- | ------- | ------ | ------ | --- |
| `pdfium`         | Yes  | No       | No      | No     | No     | No  |
| `opendataloader` | Yes  | Yes      | Partial | Yes    | Yes    | No  |
| `llmsherpa`      | Yes  | Yes      | Yes     | Partial| No     | No  |
| `docling`        | Yes  | Yes      | Yes     | Partial| No     | Partial |
| `doctr`          | Yes  | No       | No      | No     | No     | Yes |
| `marker`         | Yes  | Yes      | Yes     | Partial| No     | Yes |

---

## Notes on each

- **`pdfium`** — Very fast. Raw text only. No headings, no tables.
  Good for search and bulk work.

- **`opendataloader`** — Fast (4 s). Writes 7 output formats in one go,
  including an annotated PDF and 18 images. Tables are weak.

- **`llmsherpa`** — Gives tagged JSON blocks (header, paragraph, table).
  Good for RAG. Needs a Docker service.

- **`docling`** — 25 s. Clean markdown with real tables and 29 headings.
  The best balance of speed and quality.

- **`doctr`** — OCR only. Slow even on a normal PDF. Garbles tables.
  Use it only for scans.

- **`marker`** — Best quality markdown: bold, italic, footnotes, math.
  But 25 minutes on CPU. Use with GPU or for one-off jobs.

---

## Which one to pick

- **Many PDFs, just need text** → `pdfium`
- **Need bounding boxes or multiple formats** → `opendataloader`
- **Building a RAG pipeline** → `llmsherpa`
- **Want a good markdown copy (default choice)** → `docling`
- **PDF is a scan** → `doctr`
- **Need best quality, time is fine** → `marker`

---

_Measured on macOS, CPU only. `meta.pdf`, 26 pages, 1 MB. GPU and warm
model caches would change the numbers, but not the order._
