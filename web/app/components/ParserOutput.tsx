"use client";

import { PageResult } from "../lib/api";
import { cn } from "../lib/utils";

interface ParserOutputProps {
  pages: PageResult[];
  currentPage: number;
}

export function ParserOutput({ pages, currentPage }: ParserOutputProps) {
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
    <div className="p-4">
      {currentPageContent ? (
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
  );
}