"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { motion } from "framer-motion";

const HIGHLIGHTER_URL =
  process.env.NEXT_PUBLIC_HIGHLIGHTER_URL || "http://localhost:4000";

export function HighlighterView() {
  const [loaded, setLoaded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="relative w-full rounded-2xl overflow-hidden border border-zinc-800/50 bg-zinc-900/40"
      style={{ height: "calc(100vh - 160px)", minHeight: "600px" }}
    >
      {!loaded && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-zinc-950">
          <Loader2 className="w-8 h-8 text-zinc-600 animate-spin" />
          <span className="text-sm text-zinc-500">Loading PDF Highlighter…</span>
        </div>
      )}
      <iframe
        src={HIGHLIGHTER_URL}
        onLoad={() => setLoaded(true)}
        className="w-full h-full border-0"
        title="PDF Highlighter"
        allow="downloads"
      />
    </motion.div>
  );
}
