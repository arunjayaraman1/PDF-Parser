const API_BASE = "http://localhost:8000";

export interface ParserRecommendation {
  name: string;
  reason: string;
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

export interface ParseResponse {
  parsers: Record<string, PageResult[]>;
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