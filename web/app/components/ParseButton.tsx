"use client";

import { useAppStore } from "../lib/store";
import { parsePdf } from "../lib/api";
import { cn } from "../lib/utils";
import { Play, Loader2, Copy, Check, Zap, Terminal } from "lucide-react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export function ParseButton() {
  const {
    fileId,
    selectedParsers,
    mineruProfile,
    setMineruProfile,
    setParseResults,
    setError,
    setIsLoading,
    isLoading,
  } = useAppStore();
  const [copied, setCopied] = useState<string | null>(null);

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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Parse failed");
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async (text: string, parserName: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(parserName);
    setTimeout(() => setCopied(null), 2000);
  };

  const { parseResults } = useAppStore();
  const hasResults = Object.keys(parseResults).length > 0;
  const isDisabled = isLoading || !fileId || selectedParsers.length === 0;

  const showMineruProfile = selectedParsers.includes("mineru");

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
              Extracted Results
            </p>
            {Object.entries(parseResults).map(([parserName, pages], idx) => {
              const allText = pages.map((p) => p.text).join("\n\n");
              return (
                <motion.div
                  key={parserName}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="p-4 rounded-xl bg-zinc-950/50 border border-zinc-800/50"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 rounded-md bg-zinc-800">
                        <Terminal className="w-4 h-4 text-zinc-400" />
                      </div>
                      <h4 className="font-semibold text-zinc-200 capitalize">{parserName}</h4>
                      <span className="text-xs text-zinc-600">
                        ({pages.length} {pages.length === 1 ? "page" : "pages"})
                      </span>
                    </div>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => copyToClipboard(allText, parserName)}
                      className={cn(
                        "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200",
                        copied === parserName
                          ? "bg-emerald-500/20 text-emerald-400"
                          : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                      )}
                    >
                      {copied === parserName ? (
                        <Check className="w-3.5 h-3.5" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                      {copied === parserName ? "Copied" : "Copy"}
                    </motion.button>
                  </div>
                  <div className="space-y-2 max-h-40 overflow-y-auto pr-2 scrollbar-thin">
                    {pages.map((page, pageIdx) => (
                      <div 
                        key={pageIdx} 
                        className="p-3 rounded-lg bg-zinc-900/30 border border-zinc-800/30"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-medium text-zinc-600 bg-zinc-800/50 px-2 py-0.5 rounded">
                            Page {page.page}
                          </span>
                        </div>
                        <pre className="text-xs text-zinc-400 whitespace-pre-wrap font-mono leading-relaxed">
                          {page.text.slice(0, 400)}
                          {page.text.length > 400 && "..."}
                        </pre>
                      </div>
                    ))}
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