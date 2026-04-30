"use client";

import { useAppStore } from "../lib/store";
import { useEffect, useRef, useState, Suspense, useCallback } from "react";
import { cn } from "../lib/utils";
import {
  FileText,
  Scroll,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Link2,
  Link2Off,
  Maximize2,
  Minimize2,
  Download,
  Loader2,
} from "lucide-react";
import { PdfViewer } from "./PdfViewer";
import { Column } from "./Column";
import { ParserOutput } from "./ParserOutput";
import { motion } from "framer-motion";
import { downloadParserArtifactsZip } from "../lib/api";

const ACCENT_COLORS = ["cyan", "indigo", "emerald", "amber", "rose"] as const;

export function SyncScrollContainer() {
  const { parseResults, fileId, currentPage, setCurrentPage, parserMeta, setError } =
    useAppStore();
  const pdfRef = useRef<HTMLDivElement>(null);
  const outputRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const [activeScroll, setActiveScroll] = useState<string | null>(null);
  const [numPages, setNumPages] = useState<number>(0);
  const [syncEnabled, setSyncEnabled] = useState(true);
  const [fullViewParser, setFullViewParser] = useState<string | null>(null);
  const [downloadingParser, setDownloadingParser] = useState<string | null>(null);
  const isScrolling = useRef(false);

  const handleDownloadArtifacts = useCallback(
    async (parserName: string) => {
      if (!fileId) return;
      setDownloadingParser(parserName);
      setError(null);
      try {
        const blob = await downloadParserArtifactsZip(fileId, parserName);
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${parserName}_outputs.zip`;
        a.click();
        URL.revokeObjectURL(url);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Download failed");
      } finally {
        setDownloadingParser(null);
      }
    },
    [fileId, setError]
  );

  const parsers = Object.keys(parseResults);
  const effectiveFullViewParser =
    fullViewParser && parsers.includes(fullViewParser) ? fullViewParser : null;
  const visibleParsers = effectiveFullViewParser ? [effectiveFullViewParser] : parsers;
  const inFullView = effectiveFullViewParser !== null;
  
  const getTotalPages = useCallback(() => {
    if (parsers.length === 0) return 0;
    const maxFromResults = Math.max(
      ...Object.values(parseResults).map((pages) =>
        pages.reduce((mx, p) => Math.max(mx, p.page || 0), 0)
      )
    );
    return Math.max(numPages, maxFromResults);
  }, [parsers, parseResults, numPages]);
  
  const totalPages = getTotalPages();

  useEffect(() => {
    if (!syncEnabled) return;
    
    const handleScroll = (sourceId: string) => {
      if (isScrolling.current) return;
      
      const sourceEl = sourceId === "pdf" 
        ? pdfRef.current 
        : outputRefs.current.get(sourceId);
      
      if (!sourceEl) return;
      
      const scrollHeight = sourceEl.scrollHeight - sourceEl.clientHeight;
      if (scrollHeight <= 0) return;
      
      const scrollRatio = sourceEl.scrollTop / scrollHeight;
      if (isNaN(scrollRatio) || !isFinite(scrollRatio)) return;
      
      isScrolling.current = true;
      
      const updateScroll = () => {
        if (sourceId === "pdf") {
          outputRefs.current.forEach((el) => {
            if (el) {
              const targetScroll = scrollRatio * (el.scrollHeight - el.clientHeight);
              el.scrollTop = targetScroll;
            }
          });
        } else {
          if (pdfRef.current) {
            const targetScroll = scrollRatio * (pdfRef.current.scrollHeight - pdfRef.current.clientHeight);
            pdfRef.current.scrollTop = targetScroll;
          }
          outputRefs.current.forEach((el, key) => {
            if (el && key !== sourceId) {
              const targetScroll = scrollRatio * (el.scrollHeight - el.clientHeight);
              el.scrollTop = targetScroll;
            }
          });
        }
        
        setTimeout(() => {
          isScrolling.current = false;
        }, 50);
      };
      
      requestAnimationFrame(updateScroll);
    };

    const pdfContainer = pdfRef.current;
    const handlePdfScroll = () => {
      if (activeScroll !== "pdf") {
        setActiveScroll("pdf");
        handleScroll("pdf");
      }
    };
    
    pdfContainer?.addEventListener("scroll", handlePdfScroll);
    
    const cleanupFns: (() => void)[] = [];
    outputRefs.current.forEach((el, key) => {
      if (!el) return;
      const handleOutputScroll = () => {
        if (activeScroll !== key) {
          setActiveScroll(key);
          handleScroll(key);
        }
      };
      el.addEventListener("scroll", handleOutputScroll);
      cleanupFns.push(() => el.removeEventListener("scroll", handleOutputScroll));
    });

    return () => {
      pdfContainer?.removeEventListener("scroll", handlePdfScroll);
      cleanupFns.forEach(fn => fn());
    };
  }, [syncEnabled, activeScroll]);

  if (parsers.length === 0) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex flex-col items-center justify-center h-[520px] rounded-2xl bg-zinc-900/20 border border-zinc-800/30"
      >
        <div className="p-4 mb-4 rounded-2xl bg-zinc-800/30">
          <Scroll className="w-10 h-10 text-zinc-600" />
        </div>
        <p className="text-zinc-500 font-medium mb-1">No comparison yet</p>
        <p className="text-zinc-600 text-sm">Run parsers to see side-by-side results</p>
      </motion.div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage <= 1}
            className="p-2.5 rounded-xl bg-zinc-800/50 hover:bg-zinc-700/50 disabled:opacity-40 disabled:cursor-not-allowed border border-zinc-700/30 transition-all duration-200"
          >
            <ChevronLeft className="w-4 h-4 text-zinc-300" />
          </motion.button>
          
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-900/60 border border-zinc-800/50">
            <span className="text-sm font-medium text-zinc-400">Page</span>
            <input
              type="number"
              min={1}
              max={totalPages}
              value={currentPage}
              onChange={(e) => {
                const val = parseInt(e.target.value);
                if (val >= 1 && val <= totalPages) {
                  setCurrentPage(val);
                }
              }}
              className="w-12 text-center bg-transparent text-white font-bold focus:outline-none"
            />
            <span className="text-zinc-600">of</span>
            <span className="text-sm font-bold text-zinc-400">{totalPages}</span>
          </div>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage >= totalPages}
            className="p-2.5 rounded-xl bg-zinc-800/50 hover:bg-zinc-700/50 disabled:opacity-40 disabled:cursor-not-allowed border border-zinc-700/30 transition-all duration-200"
          >
            <ChevronRight className="w-4 h-4 text-zinc-300" />
          </motion.button>
        </div>

        <div className="flex items-center gap-2">
          {inFullView && (
            <button
              onClick={() => setFullViewParser(null)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border bg-zinc-800/30 border-zinc-700/30 hover:bg-zinc-700/30 transition-all duration-200"
            >
              <Minimize2 className="w-3.5 h-3.5 text-zinc-300" />
              <span className="text-xs font-medium text-zinc-300">
                Back to comparison
              </span>
            </button>
          )}

          <button
            onClick={() => setSyncEnabled(!syncEnabled)}
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all duration-200",
              syncEnabled
                ? "bg-indigo-500/10 border-indigo-500/20"
                : "bg-zinc-800/30 border-zinc-700/30"
            )}
          >
            {syncEnabled ? (
              <Link2 className="w-3.5 h-3.5 text-indigo-400" />
            ) : (
              <Link2Off className="w-3.5 h-3.5 text-zinc-500" />
            )}
            <span
              className={cn(
                "text-xs font-medium",
                syncEnabled ? "text-indigo-300" : "text-zinc-500"
              )}
            >
              {syncEnabled ? "Sync On" : "Sync Off"}
            </span>
          </button>
        </div>
      </div>

      {inFullView && (
        <div className="text-xs text-zinc-500 px-1">
          Full view: <span className="text-zinc-300 font-medium">{effectiveFullViewParser}</span>
        </div>
      )}

      {totalPages > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin">
          {Array.from({ length: totalPages }, (_, idx) => idx + 1).map((pageNo) => (
            <button
              key={pageNo}
              onClick={() => setCurrentPage(pageNo)}
              className={cn(
                "shrink-0 px-3 py-1.5 text-xs rounded-lg border transition-all duration-200",
                currentPage === pageNo
                  ? "bg-indigo-500/20 text-indigo-300 border-indigo-500/40"
                  : "bg-zinc-900/50 text-zinc-400 border-zinc-800/60 hover:bg-zinc-800/60 hover:text-zinc-300"
              )}
            >
              Page {pageNo}
            </button>
          ))}
        </div>
      )}

      <div
        className="grid gap-4 h-[520px]"
        style={{ gridTemplateColumns: `repeat(${1 + visibleParsers.length}, minmax(0, 1fr))` }}
      >
        <Column
          title="Original PDF"
          pageCount={numPages}
          icon={<FileText className="w-4 h-4" />}
          accentColor="cyan"
        >
          <div className="flex flex-col items-center justify-start pt-4 h-full">
            {fileId ? (
              <Suspense fallback={
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm text-zinc-500 mt-3">Loading PDF...</span>
                </div>
              }>
                <PdfViewer
                  fileId={fileId}
                  currentPage={currentPage}
                  onPageCount={setNumPages}
                />
              </Suspense>
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-zinc-600 text-sm">No PDF uploaded</p>
              </div>
            )}
          </div>
        </Column>

        {visibleParsers.map((parserName, idx) => {
          const pages = parseResults[parserName] || [];
          const accentColor = ACCENT_COLORS[idx % ACCENT_COLORS.length];
          
          return (
            <Column
              key={parserName}
              title={parserName}
              pageCount={pages.length}
              icon={<Sparkles className="w-4 h-4" />}
              accentColor={accentColor}
            >
              <div className="p-2 border-b border-zinc-800/50 flex flex-col gap-2">
                <button
                  onClick={() =>
                    setFullViewParser((prev) => (prev === parserName ? null : parserName))
                  }
                  className={cn(
                    "w-full flex items-center justify-center gap-2 px-3 py-1.5 text-xs rounded-lg border transition-all duration-200",
                    fullViewParser === parserName
                      ? "bg-indigo-500/15 border-indigo-500/30 text-indigo-300"
                      : "bg-zinc-800/30 border-zinc-700/30 text-zinc-300 hover:bg-zinc-700/30"
                  )}
                >
                  {fullViewParser === parserName ? (
                    <>
                      <Minimize2 className="w-3.5 h-3.5" />
                      Exit full view
                    </>
                  ) : (
                    <>
                      <Maximize2 className="w-3.5 h-3.5" />
                      Full view
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => handleDownloadArtifacts(parserName)}
                  disabled={
                    !fileId ||
                    !parserMeta[parserName]?.artifacts_available ||
                    downloadingParser === parserName
                  }
                  className={cn(
                    "w-full flex items-center justify-center gap-2 px-3 py-1.5 text-xs rounded-lg border transition-all duration-200",
                    parserMeta[parserName]?.artifacts_available
                      ? "bg-zinc-800/30 border-zinc-700/30 text-zinc-300 hover:bg-zinc-700/30"
                      : "bg-zinc-900/20 border-zinc-800/40 text-zinc-600 cursor-not-allowed"
                  )}
                  title={
                    parserMeta[parserName]?.artifacts_available
                      ? "Download ZIP of native parser outputs"
                      : "No native output files were saved for this parser"
                  }
                >
                  {downloadingParser === parserName ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Preparing…
                    </>
                  ) : (
                    <>
                      <Download className="w-3.5 h-3.5" />
                      Download outputs
                    </>
                  )}
                </button>
              </div>
              <ParserOutput
                pages={pages}
                currentPage={currentPage}
                fileId={fileId}
                parserName={parserName}
                jsonAvailable={parserMeta[parserName]?.json_available}
              />
            </Column>
          );
        })}
      </div>
    </div>
  );
}