"use client";

import { useState, useEffect, useCallback } from "react";
import { Loader2, FileX } from "lucide-react";

interface PdfViewerProps {
  fileId: string;
  currentPage: number;
  onPageCount?: (count: number) => void;
}

export function PdfViewer({ fileId, currentPage, onPageCount }: PdfViewerProps) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return (
      <div className="flex items-center gap-2 text-zinc-500">
        <Loader2 className="w-5 h-5 animate-spin" />
        <span className="text-sm">Loading viewer...</span>
      </div>
    );
  }

  return (
    <ClientPdfViewer
      fileId={fileId}
      currentPage={currentPage}
      onPageCount={onPageCount}
    />
  );
}

function ClientPdfViewer({ fileId, currentPage, onPageCount }: PdfViewerProps) {
  const [PdfComponent, setPdfComponent] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    import("react-pdf").then((mod) => {
      const pdfjs = (mod as any).pdfjs;
      if (pdfjs) {
        pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;
      }
      setPdfComponent(mod);
      setLoading(false);
    }).catch((err) => {
      setError("Failed to load PDF library");
      setLoading(false);
    });
  }, []);

  if (loading || !PdfComponent) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-zinc-600 animate-spin mb-3" />
        <span className="text-sm text-zinc-500">Loading PDF...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <FileX className="w-8 h-8 text-red-500 mb-3" />
        <span className="text-sm text-red-400">{error}</span>
      </div>
    );
  }

  const { Document, Page } = PdfComponent;

  return (
    <div className="pdf-container w-full">
      <Document
        file={`http://localhost:8000/files/${fileId}`}
        onLoadSuccess={(info: { numPages: number }) => {
          onPageCount?.(info.numPages);
        }}
        loading={
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-zinc-600 animate-spin mb-3" />
            <span className="text-sm text-zinc-500">Loading page...</span>
          </div>
        }
        error={
          <div className="flex flex-col items-center justify-center py-12">
            <FileX className="w-8 h-8 text-red-500 mb-3" />
            <span className="text-sm text-red-400">Failed to load PDF</span>
          </div>
        }
      >
        <Page
          pageNumber={currentPage}
          renderTextLayer={false}
          renderAnnotationLayer={false}
          scale={1.0}
          className="pdf-page"
          width={380}
        />
      </Document>
    </div>
  );
}