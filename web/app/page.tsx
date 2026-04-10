"use client";

import { useAppStore } from "./lib/store";
import { UploadSection } from "./components/UploadSection";
import { ParserSelector } from "./components/ParserSelector";
import { ParseButton } from "./components/ParseButton";
import { SyncScrollContainer } from "./components/SyncScrollContainer";
import {
  Sparkles,
  AlertCircle,
  RotateCcw,
  Hexagon,
} from "lucide-react";
import { motion } from "framer-motion";

export default function Home() {
  const { error, setError, isLoading, reset, parseResults } = useAppStore();

  return (
    <main className="min-h-screen bg-zinc-950 relative">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900/40 via-zinc-950/60 to-zinc-950" />
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-indigo-500/8 blur-[120px] rounded-full" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-cyan-500/6 blur-[100px] rounded-full" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-gradient-radial from-transparent to-zinc-950/80" />
      </div>
      
      <div className="relative z-10">
        <div className="max-w-[1600px] mx-auto px-6 py-8">
          <motion.header 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-between mb-10"
          >
            <div className="flex items-center gap-4">
              <motion.div 
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 200, damping: 15 }}
                className="relative"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-2xl blur-lg opacity-50" />
                <div className="relative p-3 rounded-2xl bg-gradient-to-br from-indigo-500 to-cyan-600 shadow-xl">
                  <Hexagon className="w-8 h-8 text-white" strokeWidth={1.5} />
                </div>
              </motion.div>
              <div>
                <h1 className="text-3xl font-bold tracking-tight">
                  <span className="bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
                    PDF Parser
                  </span>
                </h1>
                <p className="text-zinc-500 mt-1">
                  Compare and find the best parser for your documents
                </p>
              </div>
            </div>
            
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={reset}
              className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-zinc-400 hover:text-zinc-200 bg-zinc-900/60 hover:bg-zinc-800/80 border border-zinc-800/60 rounded-xl transition-all duration-200"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </motion.button>
          </motion.header>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex items-center gap-3 px-5 py-4 mb-8 rounded-2xl bg-red-500/10 border border-red-500/20 backdrop-blur-xl"
            >
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
              <p className="text-sm text-red-300">{error}</p>
              <button
                onClick={() => setError(null)}
                className="ml-auto text-zinc-400 hover:text-zinc-200 transition-colors"
              >
                ×
              </button>
            </motion.div>
          )}

          <div className="space-y-6">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800/50 backdrop-blur-xl shadow-2xl"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-500/20">
                  <span className="text-sm font-semibold text-indigo-400">1</span>
                </div>
                <h2 className="text-lg font-semibold text-zinc-100">
                  Upload & Describe
                </h2>
              </div>
              <UploadSection />
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800/50 backdrop-blur-xl shadow-2xl"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-cyan-500/20">
                  <span className="text-sm font-semibold text-cyan-400">2</span>
                </div>
                <h2 className="text-lg font-semibold text-zinc-100">
                  Select Parsers
                </h2>
              </div>
              <ParserSelector />
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800/50 backdrop-blur-xl shadow-2xl"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500/20">
                  <span className="text-sm font-semibold text-emerald-400">3</span>
                </div>
                <h2 className="text-lg font-semibold text-zinc-100">
                  Run Comparison
                </h2>
              </div>
              <ParseButton />
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800/50 backdrop-blur-xl shadow-2xl"
            >
              <div className="flex items-center gap-3 mb-6">
                <Sparkles className="w-5 h-5 text-amber-400" />
                <h2 className="text-lg font-semibold text-zinc-100">
                  Comparison View
                </h2>
              </div>
              <SyncScrollContainer />
            </motion.div>
          </div>

          <motion.footer 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-16 pt-8 border-t border-zinc-800/50"
          >
            <div className="flex items-center justify-between text-sm text-zinc-600">
              <p>PDF Parser Comparison System v1.0</p>
              <p className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Backend Ready
              </p>
            </div>
          </motion.footer>
        </div>
      </div>
    </main>
  );
}