"use client";

import { useAppStore } from "../lib/store";
import { parsePdf } from "../lib/api";
import { cn } from "../lib/utils";
import { Loader2, Zap, Sparkles } from "lucide-react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export function ParseButton() {
  const {
    fileId,
    file,
    selectedParsers,
    recommendations,
    mineruProfile,
    setMineruProfile,
    setParseResults,
    setParserMeta,
    setError,
    setIsLoading,
    parseResults,
    parserMeta,
    isLoading,
  } = useAppStore();
  const [expandedReasons, setExpandedReasons] = useState<Record<string, boolean>>({});

  const handleParse = async () => {
    if (!fileId) {
      setError("Please upload a PDF first");
      return;
    }
    if (selectedParsers.length === 0) {
      setError("Please select at least one parser");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await parsePdf(fileId, selectedParsers, {
        mineruProfile: selectedParsers.includes("mineru")
          ? mineruProfile ?? undefined
          : undefined,
      });
      setParseResults(response.parsers);
      setParserMeta(response.parser_meta ?? {});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Parse failed");
    } finally {
      setIsLoading(false);
    }
  };

  const hasResults = Object.keys(parseResults).length > 0;
  const isDisabled = isLoading || !fileId || selectedParsers.length === 0;

  const showMineruProfile = selectedParsers.includes("mineru");
  const reasonByParser = new Map(
    recommendations.map((rec) => [rec.name.toLowerCase(), rec.reason])
  );
  const rankByParser = new Map(
    recommendations.map((rec) => [rec.name.toLowerCase(), rec.rank])
  );
  const sourceName = file?.name ?? "Not reported";

  const capabilityNoteByParser: Record<string, string> = {
    unstructured: "Strong for layout-aware extraction from mixed documents.",
    tabula: "Best when you need table-heavy extraction and CSV-friendly output.",
    suryaocr: "Strong OCR capability for scanned pages and image-based text.",
    pdfplumber: "Reliable for digital PDFs with selectable text layers.",
    mineru: "Balanced parser for structured extraction across complex layouts.",
  };

  const outputFilesByParser: Record<string, string> = {
    unstructured: "document_text.txt, elements.json, extracted.txt",
    tabula: "document_text.txt, tables/table-*.csv, extracted.txt",
    suryaocr: "document_text.txt, results.json, extracted.txt",
  };

  const getStrongReason = (parserName: string, pages: number): string => {
    const recommendedReason = reasonByParser.get(parserName.toLowerCase());
    if (recommendedReason?.trim()) {
      return recommendedReason.trim();
    }
    return `This parser successfully extracted structured content from ${pages} ${
      pages === 1 ? "page" : "pages"
    }, showing reliable document coverage for this file.`;
  };

  const getKeyExtractionMetric = (parserName: string, pages: { page: number; text: string }[]) => {
    const parserKey = parserName.toLowerCase();
    const combinedText = pages.map((p) => p.text).join("\n");

    if (parserKey === "tabula") {
      const tableMatches = combinedText.match(/\btable\b/gi)?.length ?? 0;
      return tableMatches > 0
        ? `Table references: ${tableMatches}`
        : `Tables: ${pages.length} page result${pages.length === 1 ? "" : "s"}`;
    }

    if (parserKey === "unstructured") {
      const elementMarkers = combinedText.match(/\belement\b/gi)?.length ?? 0;
      return elementMarkers > 0
        ? `Element mentions: ${elementMarkers}`
        : `Elements: not reported`;
    }

    if (parserKey === "suryaocr") {
      const nonEmptyLines = combinedText
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean).length;
      return `Text lines: ${nonEmptyLines}`;
    }

    return `Extracted pages: ${pages.length}`;
  };

  const getCapabilityNote = (parserName: string) =>
    capabilityNoteByParser[parserName.toLowerCase()] ??
    "General-purpose extraction capability for mixed PDF content.";

  const getOutputFiles = (parserName: string) =>
    outputFilesByParser[parserName.toLowerCase()] ?? "Not reported";

  const getExecutionTime = (parserName: string) => {
    const ms = parserMeta[parserName]?.execution_time_ms;
    if (typeof ms !== "number" || Number.isNaN(ms)) {
      return "Not reported";
    }
    if (ms < 1000) {
      return `${ms} ms`;
    }
    return `${(ms / 1000).toFixed(2)} s`;
  };

  const getOutputFilesDisplay = (parserName: string) => {
    const files = parserMeta[parserName]?.output_files;
    if (Array.isArray(files) && files.length > 0) {
      return files.join(", ");
    }
    return getOutputFiles(parserName);
  };

  return (
    <div className="space-y-4">
      {showMineruProfile && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider px-1">
            MinerU profile
          </label>
          <select
            value={mineruProfile ?? ""}
            onChange={(e) =>
              setMineruProfile(
                e.target.value === ""
                  ? null
                  : (e.target.value as "fast" | "quality" | "balanced")
              )
            }
            className="w-full px-3 py-2 text-sm rounded-xl bg-zinc-950/50 border border-zinc-800 text-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
          >
            <option value="">Server / env default</option>
            <option value="fast">Fast (pipeline + txt, no formula/table)</option>
            <option value="balanced">Balanced (pipeline + auto, tables on)</option>
            <option value="quality">Quality (hybrid-auto-engine, slower)</option>
          </select>
        </div>
      )}
      <motion.button
        whileHover={!isDisabled ? { scale: 1.01 } : {}}
        whileTap={!isDisabled ? { scale: 0.99 } : {}}
        onClick={handleParse}
        disabled={isDisabled}
        className={cn(
          "w-full flex items-center justify-center gap-2.5 px-6 py-3.5 text-sm font-semibold rounded-xl transition-all duration-300",
          !isDisabled
            ? "bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 text-white shadow-lg shadow-emerald-500/25 hover:shadow-xl hover:shadow-emerald-500/30"
            : "bg-zinc-800/50 text-zinc-500 cursor-not-allowed border border-zinc-800"
        )}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Processing documents...</span>
          </>
        ) : (
          <>
            <Zap className="w-4 h-4" />
            <span>Run Parsers</span>
          </>
        )}
      </motion.button>

      <AnimatePresence>
        {hasResults && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-3 pt-2"
          >
            <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider px-1">
              Summary Data
            </p>
            {Object.entries(parseResults).map(([parserName, pages], idx) => {
              const reason = getStrongReason(parserName, pages.length);
              const isExpanded = Boolean(expandedReasons[parserName]);
              const shouldShowToggle = reason.length > 120;
              const keyMetric = getKeyExtractionMetric(parserName, pages);
              const capabilityNote = getCapabilityNote(parserName);
              const outputFiles = getOutputFilesDisplay(parserName);
              const executionTime = getExecutionTime(parserName);

              return (
                <motion.div
                  key={parserName}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="p-4 rounded-xl bg-zinc-950/50 border border-zinc-800/50 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 flex-wrap">
                      <div className="p-1.5 rounded-md bg-zinc-800">
                        <Sparkles className="w-4 h-4 text-emerald-400" />
                      </div>
                      <h4 className="font-semibold text-zinc-200 capitalize">{parserName}</h4>
                      {rankByParser.get(parserName.toLowerCase()) != null && (
                        <span
                          className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-emerald-500/15 text-emerald-400 border border-emerald-500/25"
                          title="AI recommendation rank for this use case"
                        >
                          Rank {rankByParser.get(parserName.toLowerCase())}
                        </span>
                      )}
                      <span className="text-xs text-zinc-600">
                        ({pages.length} {pages.length === 1 ? "page" : "pages"})
                      </span>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-zinc-900/30 border border-zinc-800/30">
                    <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">
                      Strong reason
                    </p>
                    <p
                      className={cn(
                        "text-sm text-zinc-300 leading-relaxed",
                        !isExpanded && "line-clamp-2"
                      )}
                    >
                      {reason}
                    </p>
                    {shouldShowToggle && (
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedReasons((prev) => ({
                            ...prev,
                            [parserName]: !prev[parserName],
                          }))
                        }
                        className="mt-2 text-xs font-medium text-cyan-400 hover:text-cyan-300 transition-colors"
                      >
                        {isExpanded ? "Show less" : "Show more"}
                      </button>
                    )}
                  </div>

                  <div className="grid gap-2 p-3 rounded-lg bg-zinc-900/20 border border-zinc-800/30 text-sm">
                    <p className="text-zinc-300">
                      <span className="text-zinc-500">Source:</span> {sourceName}
                    </p>
                    <p className="text-zinc-300">
                      <span className="text-zinc-500">Pages:</span> {pages.length}
                    </p>
                    <p className="text-zinc-300">
                      <span className="text-zinc-500">Key extraction:</span> {keyMetric}
                    </p>
                    <p className="text-zinc-300">
                      <span className="text-zinc-500">Execution time:</span> {executionTime}
                    </p>
                    <p className="text-zinc-300">
                      <span className="text-zinc-500">Output files:</span> {outputFiles}
                    </p>
                    <p className="text-zinc-300">
                      <span className="text-zinc-500">Capability:</span> {capabilityNote}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}