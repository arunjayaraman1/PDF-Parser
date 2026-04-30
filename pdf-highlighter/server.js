import express from 'express';
import multer from 'multer';
import { PDFDocument, PDFName, PDFArray, StandardFonts, rgb } from 'pdf-lib';
import dotenv from 'dotenv';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: resolve(__dirname, '../.env') });

const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY ?? '';
const OPENROUTER_MODEL = process.env.OPENROUTER_MODEL ?? 'openai/gpt-3.5-turbo';
const PORT = process.env.PORT ?? 4000;

// ---------------------------------------------------------------------------
// LLM prompt
// ---------------------------------------------------------------------------

const COLOR_PALETTE = [
  '#ef4444', '#f97316', '#eab308', '#22c55e',
  '#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899',
  '#84cc16', '#14b8a6', '#f59e0b', '#d946ef',
];

const PARSE_INPUT_SYSTEM_PROMPT = `You are a PDF highlight extraction assistant.

The user will provide input in ANY format — structured JSON, partial JSON, natural language, or a mix.
Your job is to extract one or more highlight regions from it.

Return ONLY a JSON array where each element has:
- "page_number": integer, 0-based (convert 1-based if needed, default 0 if absent).
- "bounding_box": [x0, y0, x1, y1] floats in PDF coordinates (bottom-left origin, y increases upward). null if unknown.
- "coord_system": "pdf" (default) or "top-left".
- "content": text content string, or null.
- "confidence": "high", "medium", or "low".
- "color": 6-digit hex color string (e.g. "#3b82f6") used for this highlight. Choose from this palette: ${COLOR_PALETTE.join(', ')}.
  - EVERY item MUST have a UNIQUE color. Never reuse the same color across items in the same response.
  - If you have more items than palette entries, generate additional distinct hex colors that contrast well with the others.

Natural language examples:
- "highlight the abstract on page 1" → page_number=0, bounding_box=null, content="abstract", confidence="low", color="#3b82f6"
- "page 3, coordinates 100,200 to 400,300" → page_number=2, bounding_box=[100,200,400,300], confidence="high", color="#22c55e"

Output raw JSON array only — no explanation text.`;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function stripCodeFence(s) {
  if (s.startsWith('```')) {
    s = s.split('```')[1];
    if (s.startsWith('json')) s = s.slice(4);
  }
  return s.trim();
}

async function callOpenRouter(systemPrompt, userPrompt) {
  if (!OPENROUTER_API_KEY) {
    throw new Error('OPENROUTER_API_KEY is not set in .env');
  }
  const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: OPENROUTER_MODEL,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
      temperature: 0,
    }),
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`OpenRouter ${response.status}: ${body}`);
  }
  const data = await response.json();
  return data.choices[0].message.content.trim();
}

async function parseInputWithLLM(rawInput, pageHeight, totalPages) {
  const prompt =
    `PDF metadata: page_height=${pageHeight.toFixed(1)}pt, total_pages=${totalPages}\n\n` +
    `User input:\n${rawInput}`;

  const raw = await callOpenRouter(PARSE_INPUT_SYSTEM_PROMPT, prompt);
  const parsed = JSON.parse(stripCodeFence(raw));
  return Array.isArray(parsed) ? parsed : [parsed];
}

const LABEL_FONT_SIZE = 10;
const LABEL_GAP = 4;

function hexToRgb01(hex) {
  if (typeof hex !== 'string') return null;
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m) return null;
  const n = parseInt(m[1], 16);
  return [((n >> 16) & 0xff) / 255, ((n >> 8) & 0xff) / 255, (n & 0xff) / 255];
}

function pickUnusedFallback(used) {
  for (const hex of COLOR_PALETTE) {
    if (!used.has(hex)) return hex;
  }
  // Palette exhausted — generate a deterministic distinct color from the index.
  const i = used.size;
  const hue = (i * 137.508) % 360; // golden-angle hue rotation
  const { r, g, b } = hslToRgb(hue, 0.65, 0.5);
  return `#${[r, g, b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('')}`;
}

function hslToRgb(h, s, l) {
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = l - c / 2;
  let r = 0, g = 0, b = 0;
  if      (h <  60) [r, g, b] = [c, x, 0];
  else if (h < 120) [r, g, b] = [x, c, 0];
  else if (h < 180) [r, g, b] = [0, c, x];
  else if (h < 240) [r, g, b] = [0, x, c];
  else if (h < 300) [r, g, b] = [x, 0, c];
  else              [r, g, b] = [c, 0, x];
  return { r: r + m, g: g + m, b: b + m };
}

function normalizeColor(value, used) {
  const rgb01 = hexToRgb01(value);
  if (rgb01) {
    const hex = (value.startsWith('#') ? value : `#${value}`).toLowerCase();
    if (!used.has(hex)) {
      used.add(hex);
      return { hex, rgb01 };
    }
    // LLM repeated a color — fall through to the unused-color picker.
  }
  const fallback = pickUnusedFallback(used);
  used.add(fallback);
  return { hex: fallback, rgb01: hexToRgb01(fallback) };
}

function addHighlightAnnotation(page, pdfDoc, x0, y0, x1, y1, colorRgb01) {
  const annotDict = pdfDoc.context.obj({
    Type: PDFName.of('Annot'),
    Subtype: PDFName.of('Highlight'),
    Rect: [x0, y0, x1, y1],
    QuadPoints: [x0, y1, x1, y1, x0, y0, x1, y0],
    C: colorRgb01,
    CA: 0.5,
    F: 4,
  });
  const annotRef = pdfDoc.context.register(annotDict);

  const annotsKey = PDFName.of('Annots');
  const existing = page.node.get(annotsKey);
  if (existing instanceof PDFArray) {
    existing.push(annotRef);
  } else {
    page.node.set(annotsKey, pdfDoc.context.obj([annotRef]));
  }
}

function drawHighlightLabel(page, font, index, x0, y0, x1, y1, colorRgb01) {
  const label = `[${index}]`;
  const labelWidth = font.widthOfTextAtSize(label, LABEL_FONT_SIZE);

  let labelX = x0 - labelWidth - LABEL_GAP;
  if (labelX < 2) labelX = x0 + 2;

  const labelY = y1 - LABEL_FONT_SIZE;

  page.drawText(label, {
    x: labelX,
    y: labelY,
    size: LABEL_FONT_SIZE,
    font,
    color: rgb(colorRgb01[0], colorRgb01[1], colorRgb01[2]),
  });
}

// ---------------------------------------------------------------------------
// Express app
// ---------------------------------------------------------------------------

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

app.use(express.static(resolve(__dirname, 'public')));

app.post('/api/highlight', upload.single('pdf'), async (req, res) => {
  try {
    const userInput = req.body?.input?.trim();
    if (!userInput) return res.status(400).json({ error: 'No input provided.' });
    if (!req.file)  return res.status(400).json({ error: 'No PDF uploaded.' });

    const pdfDoc = await PDFDocument.load(req.file.buffer, { ignoreEncryption: true });
    const pages = pdfDoc.getPages();
    const { height: pageHeight } = pages[0].getSize();
    const totalPages = pages.length;
    const labelFont = await pdfDoc.embedFont(StandardFonts.HelveticaBold);

    let items;
    try {
      items = await parseInputWithLLM(userInput, pageHeight, totalPages);
    } catch (err) {
      return res.status(502).json({ error: `LLM error: ${err.message}` });
    }

    let highlighted = 0;
    const skipped = [];
    const citations = [];
    const usedColors = new Set();

    for (const item of items) {
      const bbox = item.bounding_box;

      if (!bbox || !Array.isArray(bbox) || bbox.some(v => v == null || typeof v !== 'number')) {
        skipped.push({ reason: 'no bounding box', content: item.content });
        continue;
      }

      const pageNum = item.page_number ?? 0;
      if (pageNum < 0 || pageNum >= totalPages) {
        skipped.push({ reason: `page ${pageNum} out of range`, content: item.content });
        continue;
      }

      let [x0, y0, x1, y1] = bbox;
      if (item.coord_system === 'top-left') {
        [y0, y1] = [pageHeight - y1, pageHeight - y0];
      }

      const { hex: colorHex, rgb01: colorRgb } = normalizeColor(item.color, usedColors);

      addHighlightAnnotation(pages[pageNum], pdfDoc, x0, y0, x1, y1, colorRgb);
      highlighted++;
      drawHighlightLabel(pages[pageNum], labelFont, highlighted, x0, y0, x1, y1, colorRgb);

      citations.push({
        index: highlighted,
        page: pageNum,
        bbox_pdf: [x0, y0, x1, y1],
        content: item.content ?? null,
        confidence: item.confidence ?? 'unknown',
        color: colorHex,
      });
    }

    if (highlighted === 0) {
      return res.status(422).json({
        error: 'No regions could be highlighted.',
        skipped,
      });
    }

    const bytes = await pdfDoc.save();
    res.json({
      highlighted_count: highlighted,
      total_items: items.length,
      pdf_base64: Buffer.from(bytes).toString('base64'),
      citations,
      skipped,
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`PDF Highlighter → http://localhost:${PORT}`);
});
