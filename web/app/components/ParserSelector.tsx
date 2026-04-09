"use client";

import { useAppStore } from "../lib/store";
import { getRecommendations } from "../lib/api";
import { cn } from "../lib/utils";
import { Check, Sparkles, Loader2, Wand2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function ParserSelector() {
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
            <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider px-1">
              Recommended parsers
            </p>
            {recommendations.map((parser, idx) => (
              <motion.div
                key={parser.name}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                onClick={() => toggleParser(parser.name)}
                className={cn(
                  "group flex items-center justify-between p-4 rounded-xl border cursor-pointer transition-all duration-200",
                  selectedParsers.includes(parser.name)
                    ? "bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border-indigo-500/40"
                    : "bg-zinc-950/30 border-zinc-800/50 hover:border-zinc-700 hover:bg-zinc-900/30"
                )}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-200",
                      selectedParsers.includes(parser.name)
                        ? "bg-indigo-500/20 text-indigo-400"
                        : "bg-zinc-800/50 text-zinc-500 group-hover:bg-zinc-800 group-hover:text-zinc-400"
                    )}
                  >
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <div className="space-y-0.5">
                    <h4 className="font-semibold text-zinc-200">{parser.name}</h4>
                    <p className="text-xs text-zinc-500 line-clamp-1">{parser.reason}</p>
                  </div>
                </div>
                <div
                  className={cn(
                    "w-6 h-6 rounded-lg flex items-center justify-center transition-all duration-200",
                    selectedParsers.includes(parser.name)
                      ? "bg-indigo-500 text-white"
                      : "bg-zinc-800 border border-zinc-700 group-hover:border-zinc-600"
                  )}
                >
                  {selectedParsers.includes(parser.name) && (
                    <Check className="w-4 h-4" />
                  )}
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}