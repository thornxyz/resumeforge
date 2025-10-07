import Editor, { type Monaco } from "@monaco-editor/react";
import { useCallback, useEffect, useRef } from "react";
import latex from "monaco-latex";
import { LatexEditorProps } from "@/lib/types";

type MonacoEditorInstance = ReturnType<Monaco["editor"]["create"]>;

type DecorationsCollection = ReturnType<
  MonacoEditorInstance["createDecorationsCollection"]
>;

export default function LatexEditor({
  value,
  onChange,
  highlightedLineRanges = [],
}: LatexEditorProps) {
  const editorRef = useRef<MonacoEditorInstance | null>(null);
  const monacoRef = useRef<Monaco | null>(null);
  const decorationsRef = useRef<DecorationsCollection | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const styleId = "latex-editor-pending-style";
    if (document.getElementById(styleId)) {
      return;
    }

    const style = document.createElement("style");
    style.id = styleId;
    style.innerHTML = `
      .monaco-editor .pending-line-decoration {
        background-color: rgba(59, 130, 246, 0.18) !important;
      }
      .monaco-editor .pending-line-border {
        border-left: 3px solid rgba(37, 99, 235, 0.8);
      }
      .monaco-editor .pending-line-glyph {
        background-color: rgba(37, 99, 235, 0.85);
        border-radius: 9999px;
        width: 6px !important;
        margin-left: 2px;
      }
    `;
    document.head.appendChild(style);
  }, []);

  const applyHighlights = useCallback(
    (ranges: NonNullable<LatexEditorProps["highlightedLineRanges"]>) => {
      const editorInstance = editorRef.current;
      const monacoInstance = monacoRef.current;
      if (!editorInstance || !monacoInstance) {
        return;
      }

      if (!decorationsRef.current) {
        decorationsRef.current = editorInstance.createDecorationsCollection();
      }

      decorationsRef.current.set(
        ranges.map((range) => ({
          range: new monacoInstance.Range(range.start, 1, range.end, 1),
          options: {
            isWholeLine: true,
            className: "pending-line-decoration",
            linesDecorationsClassName: "pending-line-border",
            glyphMarginClassName: "pending-line-glyph",
            overviewRuler: {
              color: "rgba(37, 99, 235, 0.6)",
              position: monacoInstance.editor.OverviewRulerLane.Full,
            },
          },
        }))
      );
    },
    []
  );

  const handleEditorWillMount = (monaco: Monaco) => {
    monaco.languages.register({ id: "latex" });
    monaco.languages.setMonarchTokensProvider("latex", latex);
  };

  const handleEditorMount = (editor: MonacoEditorInstance, monaco: Monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    decorationsRef.current = editor.createDecorationsCollection();
    applyHighlights(highlightedLineRanges);
  };

  useEffect(() => {
    applyHighlights(highlightedLineRanges);
  }, [applyHighlights, highlightedLineRanges]);

  useEffect(() => {
    return () => {
      decorationsRef.current?.set([]);
      decorationsRef.current = null;
      editorRef.current = null;
      monacoRef.current = null;
    };
  }, []);

  return (
    <Editor
      height={"100%"}
      defaultLanguage="latex"
      value={value}
      onChange={onChange}
      theme="light"
      beforeMount={handleEditorWillMount}
      onMount={handleEditorMount}
      options={{
        fontSize: 13,
        glyphMargin: true,
        minimap: {
          enabled: false,
        },
        lineNumbersMinChars: 2,
        wordWrap: "on",
        // Useful for LaTeX
        formatOnPaste: true,
        formatOnType: true,
      }}
    />
  );
}
