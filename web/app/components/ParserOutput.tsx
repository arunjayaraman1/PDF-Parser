"use client";

import { useState, useCallback } from "react";
import { FileText, FileJson, Loader2 } from "lucide-react";
import { PageResult, fetchParserArtifactFile } from "../lib/api";
import { cn } from "../lib/utils";

interface ParserOutputProps {
  pages: PageResult[];
  currentPage: number;
  fileId?: string | null;
  parserName?: string;
  jsonAvailable?: boolean;
}

export function ParserOutput({
  pages,
  currentPage,
  fileId,
  parserName,
  jsonAvailable,
}: ParserOutputProps) {
  const [outputFormat, setOutputFormat] = useState<"md" | "json">("md");
  const [jsonContent, setJsonContent] = useState<string | null>(null);
  const [jsonLoading, setJsonLoading] = useState(false);
  const [jsonError, setJsonError] = useState<string | null>(null);

  const handleJsonClick = useCallback(async () => {
    setOutputFormat("json");
    if (jsonContent !== null || !fileId || !parserName) return;
    setJsonLoading(true);
    setJsonError(null);
    try {
      const raw = await fetchParserArtifactFile(fileId, parserName, "extracted.json");
      try {
        setJsonContent(JSON.stringify(JSON.parse(raw), null, 2));
      } catch {
        setJsonContent(raw);
      }
    } catch (e) {
      setJsonError(e instanceof Error ? e.message : "Failed to load JSON");
    } finally {
      setJsonLoading(false);
    }
  }, [fileId, parserName, jsonContent]);

  if (!pages || pages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-12">
        <p className="text-sm text-zinc-500">No content available</p>
      </div>
    );
  }

  const allPages = [...pages].sort((a, b) => a.page - b.page);
  const currentPageContent = allPages.find((p) => p.page === currentPage);

  return (
    <div className="flex flex-col h-full">
      {jsonAvailable && (
        <div className="flex items-center gap-1 px-3 py-2 border-b border-zinc-800/50 shrink-0">
          <button
            onClick={() => setOutputFormat("md")}
            className={cn(
              "flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg transition-all duration-200",
              outputFormat === "md"
                ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                : "text-zinc-500 hover:text-zinc-300 border border-transparent hover:border-zinc-700/50"
            )}
          >
            <FileText className="w-3 h-3" />
            Markdown
          </button>
          <button
            onClick={handleJsonClick}
            className={cn(
              "flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg transition-all duration-200",
              outputFormat === "json"
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                : "text-zinc-500 hover:text-zinc-300 border border-transparent hover:border-zinc-700/50"
            )}
          >
            <FileJson className="w-3 h-3" />
            JSON
          </button>
        </div>
      )}

      <div className="p-4 flex-1 overflow-auto">
        {outputFormat === "json" ? (
          jsonLoading ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <Loader2 className="w-6 h-6 text-zinc-600 animate-spin" />
              <span className="text-xs text-zinc-500">Loading JSON...</span>
            </div>
          ) : jsonError ? (
            <div className="p-3 rounded-xl border border-red-500/20 bg-red-500/10">
              <p className="text-xs text-red-400">{jsonError}</p>
            </div>
          ) : jsonContent ? (
            <pre className="text-xs whitespace-pre-wrap font-mono leading-relaxed text-zinc-300">
              {jsonContent}
            </pre>
          ) : null
        ) : currentPageContent ? (
          <div className="page-section">
            <div className="flex items-center gap-2 mb-2 text-zinc-300">
              <div className="px-2 py-0.5 text-xs font-semibold rounded bg-zinc-700 text-zinc-200">
                Page {currentPageContent.page}
              </div>
              <span className="text-xs text-indigo-400">(current)</span>
            </div>

            <div className="p-4 rounded-xl border transition-all duration-200 bg-zinc-800/30 border-zinc-700/50">
              <pre className="text-sm whitespace-pre-wrap font-mono leading-relaxed text-zinc-300">
                {currentPageContent.text?.trim() || (
                  <span className="text-zinc-600 italic">No text on this page</span>
                )}
              </pre>
            </div>
          </div>
        ) : (
          <div className="p-4 rounded-xl border bg-zinc-900/20 border-zinc-800/30">
            <p className="text-sm text-zinc-500">
              No extracted content mapped for page {currentPage}.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
