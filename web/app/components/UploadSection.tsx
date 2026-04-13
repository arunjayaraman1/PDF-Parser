"use client";

import { useCallback, useState } from "react";
import { Upload, X, FileArchive } from "lucide-react";
import { useAppStore } from "../lib/store";
import { uploadPdf } from "../lib/api";
import { cn } from "../lib/utils";
import { motion, AnimatePresence } from "framer-motion";

const SAMPLE_PDF_URL = "/samples/Meta-Harness.pdf";
const SAMPLE_PDF_NAME = "Meta-Harness.pdf";

const showSamplePdfOption =
  process.env.NODE_ENV === "development" ||
  process.env.NEXT_PUBLIC_SHOW_SAMPLE_PDF === "true";

export function UploadSection() {
  const { description, setDescription, file, setFile, setError, setIsLoading, isLoading } =
    useAppStore();
  const [isDragging, setIsDragging] = useState(false);
  const [isFetchingSample, setIsFetchingSample] = useState(false);

  const handleUpload = useCallback(
    async (uploadedFile: File) => {
      if (!uploadedFile.type.includes("pdf")) {
        setError("Please upload a PDF file");
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const response = await uploadPdf(uploadedFile);
        setFile(uploadedFile, response.file_id, response.file_path);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setIsLoading(false);
      }
    },
    [setFile, setError, setIsLoading]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const files = e.dataTransfer.files;
      if (files.length > 0 && files[0].type.includes("pdf")) {
        handleUpload(files[0]);
      }
    },
    [handleUpload]
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleUpload(files[0]);
      }
    },
    [handleUpload]
  );

  const handleLoadSample = useCallback(async () => {
    if (file || isLoading || isFetchingSample) return;
    setError(null);
    setIsFetchingSample(true);
    try {
      const res = await fetch(SAMPLE_PDF_URL);
      if (!res.ok) {
        setError(
          "Sample PDF not found. Copy Meta-Harness.pdf from the project root to web/public/samples/Meta-Harness.pdf."
        );
        return;
      }
      const blob = await res.blob();
      const sampleFile = new File([blob], SAMPLE_PDF_NAME, {
        type: "application/pdf",
      });
      await handleUpload(sampleFile);
    } catch {
      setError(
        "Could not load sample PDF. Copy Meta-Harness.pdf to web/public/samples/Meta-Harness.pdf."
      );
    } finally {
      setIsFetchingSample(false);
    }
  }, [file, isLoading, isFetchingSample, handleUpload, setError]);

  const uploadBusy = isLoading || isFetchingSample;

  return (
    <div className="space-y-5">
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-zinc-300">
            Use Case Description
          </label>
          <span className="text-xs text-zinc-500">{description.length}/500</span>
        </div>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value.slice(0, 500))}
          placeholder="e.g., I need to extract tables from scanned PDFs for data analysis..."
          className="w-full h-24 px-4 py-3 text-sm text-zinc-100 bg-zinc-950/50 border border-zinc-800 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500/50 placeholder:text-zinc-600 transition-all duration-200"
        />
      </div>

      <div className="relative">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={cn(
            "relative flex flex-col items-center justify-center w-full h-36 border-2 border-dashed rounded-2xl cursor-pointer transition-all duration-300",
            isDragging
              ? "border-indigo-500 bg-indigo-500/10 scale-[1.02]"
              : "border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900/30",
            file && "pointer-events-none opacity-40"
          )}
        >
          <AnimatePresence mode="wait">
            {file ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="flex items-center gap-4"
              >
                <div className="p-3 rounded-xl bg-indigo-500/20">
                  <FileArchive className="w-8 h-8 text-indigo-400" />
                </div>
                <div className="text-left">
                  <p className="font-medium text-zinc-200">{file.name}</p>
                  <p className="text-xs text-zinc-500">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                  className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-zinc-400" />
                </motion.button>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center"
              >
                <div className="inline-flex p-3 mb-3 rounded-xl bg-zinc-900/50">
                  <Upload className="w-6 h-6 text-zinc-500" />
                </div>
                <p className="text-sm text-zinc-400 mb-1">
                  Drag & drop your PDF here
                </p>
                <p className="text-xs text-zinc-600">
                  or{" "}
                  <span className="text-indigo-400 font-medium">browse files</span>
                </p>
              </motion.div>
            )}
          </AnimatePresence>
          
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="absolute inset-0 opacity-0 cursor-pointer"
            disabled={!!file}
          />
        </div>
        
        {uploadBusy && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 flex items-center justify-center bg-zinc-950/80 rounded-2xl backdrop-blur-sm"
          >
            <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-zinc-900 border border-zinc-800">
              <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-zinc-300">
                {isFetchingSample && !isLoading ? "Loading sample…" : "Uploading..."}
              </span>
            </div>
          </motion.div>
        )}
      </div>

      {showSamplePdfOption && (
        <div className="flex justify-center">
          <button
            type="button"
            onClick={handleLoadSample}
            disabled={!!file || uploadBusy}
            className="text-xs text-indigo-400/90 hover:text-indigo-300 disabled:opacity-40 disabled:pointer-events-none underline-offset-2 hover:underline transition-colors"
          >
            Use sample PDF (Meta-Harness)
          </button>
        </div>
      )}
    </div>
  );
}