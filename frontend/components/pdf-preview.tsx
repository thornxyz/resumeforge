export default function PdfPreview({ pdfUrl }: { pdfUrl: string }) {
  if (!pdfUrl) {
    return (
      <div className="w-full h-[600px] border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <svg
            className="w-12 h-12 mx-auto mb-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="text-lg font-medium">PDF Preview</p>
          <p className="text-sm">Compile your LaTeX to see the preview here</p>
        </div>
      </div>
    );
  }

  return <iframe src={pdfUrl} className="w-full h-[600px] border rounded-lg" />;
}
