import Editor, { type Monaco } from "@monaco-editor/react";
import { useCallback, useEffect, useRef } from "react";
import latex from "monaco-latex";
import { LatexEditorProps } from "@/lib/types";

export default function LatexEditor({
  value,
  onChange,
  highlightedLineRanges = [],
}: LatexEditorProps) {
  const editorRef = useRef<ReturnType<Monaco["editor"]["create"]> | null>(null);
  const monacoRef = useRef<Monaco | null>(null);
  const decorationsRef = useRef<string[]>([]);

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

      decorationsRef.current = editorInstance.deltaDecorations(
        decorationsRef.current,
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
    // Register LaTeX language
    monaco.languages.register({ id: "latex" });

    // Set syntax highlighting
    monaco.languages.setMonarchTokensProvider("latex", latex);

    // Add LaTeX-specific autocomplete suggestions
    type CompletionProvider = Parameters<
      Monaco["languages"]["registerCompletionItemProvider"]
    >[1];

    const completionProvider: CompletionProvider = {
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position);
        const range = new monaco.Range(
          position.lineNumber,
          word.startColumn,
          position.lineNumber,
          word.endColumn
        );

        const baseSuggestions = [
          // Document structure
          {
            label: "\\documentclass",
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: "\\documentclass{${1:article}}",
            insertTextRules:
              monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: "Define document class",
          },
          {
            label: "\\begin",
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText:
              "\\begin{${1:environment}}\n\t$0\n\\end{${1:environment}}",
            insertTextRules:
              monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: "Begin an environment",
          },
          {
            label: "\\section",
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: "\\section{$1}",
            insertTextRules:
              monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: "Section heading",
          },
          {
            label: "\\subsection",
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: "\\subsection{$1}",
            insertTextRules:
              monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: "Subsection heading",
          },
          // Text formatting
          {
            label: "\\textbf",
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: "\\textbf{$1}",
            insertTextRules:
              monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: "Bold text",
          },
          {
            label: "\\textit",
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: "\\textit{$1}",
            insertTextRules:
              monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: "Italic text",
          },
          {
            label: "\\emph",
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: "\\emph{$1}",
            insertTextRules:
              monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: "Emphasized text",
          },
          // Lists
          {
            label: "itemize",
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: "\\begin{itemize}\n\t\\item $0\n\\end{itemize}",
            insertTextRules:
              monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: "Bulleted list",
          },
          {
            label: "enumerate",
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: "\\begin{enumerate}\n\t\\item $0\n\\end{enumerate}",
            insertTextRules:
              monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: "Numbered list",
          },
          {
            label: "\\item",
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: "\\item ",
            documentation: "List item",
          },
          // Resume-specific commands
          {
            label: "\\href",
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: "\\href{${1:url}}{${2:text}}",
            insertTextRules:
              monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: "Hyperlink",
          },
          {
            label: "\\usepackage",
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: "\\usepackage{$1}",
            insertTextRules:
              monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: "Include a package",
          },
        ];

        const suggestions = baseSuggestions.map((suggestion) => ({
          ...suggestion,
          range,
        }));

        return { suggestions };
      },
    };

    monaco.languages.registerCompletionItemProvider(
      "latex",
      completionProvider
    );

    // Add bracket matching
    monaco.languages.setLanguageConfiguration("latex", {
      brackets: [
        ["{", "}"],
        ["[", "]"],
        ["(", ")"],
      ],
      autoClosingPairs: [
        { open: "{", close: "}" },
        { open: "[", close: "]" },
        { open: "(", close: ")" },
        { open: "$", close: "$" },
        { open: "\\begin{", close: "}" },
      ],
      surroundingPairs: [
        { open: "{", close: "}" },
        { open: "[", close: "]" },
        { open: "(", close: ")" },
        { open: "$", close: "$" },
      ],
    });
  };

  const handleEditorMount = (
    editor: ReturnType<Monaco["editor"]["create"]>,
    monaco: Monaco
  ) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    applyHighlights(highlightedLineRanges);
  };

  useEffect(() => {
    applyHighlights(highlightedLineRanges);
  }, [applyHighlights, highlightedLineRanges]);

  useEffect(() => {
    return () => {
      if (editorRef.current) {
        editorRef.current.deltaDecorations(decorationsRef.current, []);
      }
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
        // Enhanced editor options for LaTeX
        suggest: {
          snippetsPreventQuickSuggestions: false,
        },
        quickSuggestions: {
          other: true,
          comments: false,
          strings: false,
        },
        acceptSuggestionOnCommitCharacter: true,
        acceptSuggestionOnEnter: "on",
        tabCompletion: "on",
        // Bracket matching
        matchBrackets: "always",
        autoClosingBrackets: "always",
        autoClosingQuotes: "always",
        // Useful for LaTeX
        formatOnPaste: true,
        formatOnType: true,
      }}
    />
  );
}
