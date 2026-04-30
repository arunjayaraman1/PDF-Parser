const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ParserRecommendation {
  name: string;
  reason: string;
  /** 1 = best match; 2–3 = next-best */
  rank: number;
}

export interface UploadResponse {
  file_id: string;
  file_path: string;
  filename: string;
}

export interface PageResult {
  page: number;
  text: string;
}

export interface ParserRunMeta {
  execution_time_ms: number;
  output_files: string[];
  /** True when native outputs were saved under uploads/artifacts and ZIP download is available */
  artifacts_available?: boolean;
  /** True when extracted.json is available for this parser */
  json_available?: boolean;
}

export interface ParseResponse {
  parsers: Record<string, PageResult[]>;
  parser_meta: Record<string, ParserRunMeta>;
}

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || "Upload failed");
  }

  return res.json();
}

export async function getRecommendations(
  description: string
): Promise<{ parsers: ParserRecommendation[] }> {
  const res = await fetch(`${API_BASE}/llm/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || "Recommendation failed");
  }

  return res.json();
}

export type MineruProfile = "fast" | "quality" | "balanced";

export async function parsePdf(
  fileId: string,
  parsers: string[],
  options?: { mineruProfile?: MineruProfile | null }
): Promise<ParseResponse> {
  const body: Record<string, unknown> = { file_id: fileId, parsers };
  if (options?.mineruProfile) {
    body.mineru_profile = options.mineruProfile;
  }
  const res = await fetch(`${API_BASE}/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || "Parse failed");
  }

  return res.json();
}

export async function fetchParserArtifactFile(
  fileId: string,
  parserName: string,
  filename: string
): Promise<string> {
  const url = `${API_BASE}/artifacts/${encodeURIComponent(fileId)}/${encodeURIComponent(parserName)}/file/${encodeURIComponent(filename)}`;
  const res = await fetch(url);
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to fetch file");
  }
  return res.text();
}

export async function downloadParserArtifactsZip(
  fileId: string,
  parserName: string
): Promise<Blob> {
  const url = `${API_BASE}/artifacts/${encodeURIComponent(fileId)}/${encodeURIComponent(
    parserName
  )}/download`;
  const res = await fetch(url);
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    const detail = error.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg ?? "").join("; ")
          : "Download failed";
    throw new Error(msg || "Download failed");
  }
  return res.blob();
}