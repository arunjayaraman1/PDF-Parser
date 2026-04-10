"use client";

import { useAppStore } from "../lib/store";
import { getRecommendations } from "../lib/api";
import { cn } from "../lib/utils";
import { Check, Loader2, Wand2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";

export function ParserSelector() {
  const [expandedRecommendations, setExpandedRecommendations] = useState<Record<string, boolean>>({});
  const {
    description,
    file,
    recommendations,
    setRecommendations,
    selectedParsers,
    setSelectedParsers,
    toggleParser,
    setError,
    setIsLoading,
    isLoading,
  } = useAppStore();

  const handleGetRecommendations = async () => {
    if (!description.trim()) {
      setError("Please enter a description");
      return;
    }
    if (!file) {
      setError("Please upload a PDF first");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await getRecommendations(description);
      setRecommendations(response.parsers);
      const topThree = response.parsers.slice(0, 3).map((p) => p.name);
      setSelectedParsers(topThree);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get recommendations");
    } finally {
      setIsLoading(false);
    }
  };

  const isDisabled = isLoading || !file || !description.trim();
  const capabilityNoteByParser: Record<string, string> = {
    unstructured: "Strong capability for layout-aware text and mixed document sections.",
    tabula: "Strong capability for extracting table-focused data cleanly.",
    suryaocr: "Strong capability for OCR on scanned or image-based PDF pages.",
    pdfplumber: "Strong capability for digital PDFs with selectable text.",
    mineru: "Strong capability for structured extraction in complex layouts.",
  };

  const getCapabilityNote = (parserName: string) =>
    capabilityNoteByParser[parserName.toLowerCase()] ??
    "Strong capability for general-purpose PDF extraction.";

  return (
    <div className="space-y-4">
      <motion.button
        whileHover={!isDisabled ? { scale: 1.01 } : {}}
        whileTap={!isDisabled ? { scale: 0.99 } : {}}
        onClick={handleGetRecommendations}
        disabled={isDisabled}
        className={cn(
          "w-full flex items-center justify-center gap-2.5 px-6 py-3.5 text-sm font-semibold rounded-xl transition-all duration-300",
          !isDisabled
            ? "bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-500 text-white shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30"
            : "bg-zinc-800/50 text-zinc-500 cursor-not-allowed border border-zinc-800"
        )}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Analyzing your use case...</span>
          </>
        ) : (
          <>
            <Wand2 className="w-4 h-4" />
            <span>Get AI Recommendations</span>
          </>
        )}
      </motion.button>

      <AnimatePresence>
        {recommendations.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="grid gap-3 pt-2"
          >
            <div className="px-1 space-y-0.5">
              <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider">
                Ranked recommendations
              </p>
              <p className="text-[11px] text-zinc-600 leading-snug">
                1 = best match for your use case (fit, speed, and task)
              </p>
            </div>
            {recommendations.map((parser, idx) => {
              const rank = parser.rank ?? idx + 1;
              const cap = getCapabilityNote(parser.name);
              const isExpanded = Boolean(expandedRecommendations[parser.name]);
              const reasonText = parser.reason.trim();
              const shouldShowToggle = reasonText.length > 200;
              return (
              <motion.div key={`${rank}-${parser.name}`} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: idx * 0.1 }}>
                <div
                  onClick={() => toggleParser(parser.name)}
                  className={cn(
                    "group flex items-center justify-between p-4 rounded-xl border cursor-pointer transition-all duration-200",
                    selectedParsers.includes(parser.name)
                      ? "bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border-indigo-500/40"
                      : "bg-zinc-950/30 border-zinc-800/50 hover:border-zinc-700 hover:bg-zinc-900/30"
                  )}
                >
                  <div className="flex items-start gap-3 flex-1">
                    <div
                      className={cn(
                        "w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-200 shrink-0",
                        selectedParsers.includes(parser.name)
                          ? "bg-indigo-500 text-white shadow-md shadow-indigo-500/20"
                          : "bg-zinc-800 text-zinc-300 border border-zinc-700 group-hover:border-zinc-600"
                      )}
                      aria-label={`Rank ${rank}`}
                    >
                      {rank}
                    </div>
                    <div className="space-y-1 min-w-0">
                      <h4 className="font-semibold text-zinc-200">{parser.name}</h4>
                      <p
                        className={cn(
                          "text-xs text-zinc-400 leading-relaxed",
                          !isExpanded && shouldShowToggle && "line-clamp-3"
                        )}
                      >
                        {reasonText}
                      </p>
                      <p className="text-[11px] text-zinc-600 leading-relaxed">
                        Capability: {cap}
                      </p>
                      {shouldShowToggle && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setExpandedRecommendations((prev) => ({
                              ...prev,
                              [parser.name]: !prev[parser.name],
                            }));
                          }}
                          className="text-xs font-medium text-cyan-400 hover:text-cyan-300 transition-colors"
                        >
                          {isExpanded ? "Show less" : "Show more"}
                        </button>
                      )}
                    </div>
                  </div>

                  <div
                    className={cn(
                      "w-6 h-6 rounded-lg flex items-center justify-center transition-all duration-200 shrink-0 ml-3",
                      selectedParsers.includes(parser.name)
                        ? "bg-indigo-500 text-white"
                        : "bg-zinc-800 border border-zinc-700 group-hover:border-zinc-600"
                    )}
                  >
                    {selectedParsers.includes(parser.name) && (
                      <Check className="w-4 h-4" />
                    )}
                  </div>
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