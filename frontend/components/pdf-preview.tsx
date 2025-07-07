"use client";

import { useState, useCallback, useMemo, useEffect } from "react";
import { useResizeObserver } from "@wojtekmaj/react-hooks";
import { pdfjs, Document, Page } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { PdfPreviewProps } from "@/lib/types";
import { IoDocumentTextOutline } from "react-icons/io5";

import type { PDFDocumentProxy } from "pdfjs-dist";

// Move worker initialization inside useEffect to handle fast refresh
const resizeObserverOptions = {};
const maxWidth = 800;

export default function PdfPreview({ pdfUrl, zoom = 100 }: PdfPreviewProps) {
  const [numPages, setNumPages] = useState<number>();
  const [containerRef, setContainerRef] = useState<HTMLElement | null>(null);
  const [containerWidth, setContainerWidth] = useState<number>();

  // Initialize PDF.js worker on component mount to handle fast refresh
  useEffect(() => {
    if (typeof window !== "undefined" && !pdfjs.GlobalWorkerOptions.workerSrc) {
      pdfjs.GlobalWorkerOptions.workerSrc = new URL(
        "pdfjs-dist/build/pdf.worker.min.mjs",
        import.meta.url
      ).toString();
    }
  }, []);

  const options = useMemo(
    () => ({
      cMapUrl: "/cmaps/",
      standardFontDataUrl: "/standard_fonts/",
    }),
    []
  );

  const onResize = useCallback<ResizeObserverCallback>((entries) => {
    const [entry] = entries;
    if (entry) {
      setContainerWidth(entry.contentRect.width);
    }
  }, []);

  useResizeObserver(containerRef, resizeObserverOptions, onResize);

  function onDocumentLoadSuccess({
    numPages: nextNumPages,
  }: PDFDocumentProxy): void {
    setNumPages(nextNumPages);
  }

  if (!pdfUrl) {
    return (
      <div className="w-full h-[95%] border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <IoDocumentTextOutline className="mx-auto mb-2" size={80} />
          <p className="text-lg font-medium">PDF Preview</p>
          <p className="text-sm">Compile your LaTeX to see the preview here</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full  overflow-auto" ref={setContainerRef}>
      <Document
        file={pdfUrl}
        onLoadSuccess={onDocumentLoadSuccess}
        options={options}
      >
        {Array.from(new Array(numPages), (_el, index) => (
          <Page
            key={`page_${index + 1}`}
            pageNumber={index + 1}
            width={
              containerWidth
                ? containerWidth * (zoom / 100)
                : maxWidth * (zoom / 100)
            }
            className="mx-auto"
          />
        ))}
      </Document>
    </div>
  );
}
