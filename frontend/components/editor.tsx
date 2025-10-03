import Editor from "@monaco-editor/react";
import latex from "monaco-latex";
import { LatexEditorProps } from "@/lib/types";

export default function LatexEditor({ value, onChange }: LatexEditorProps) {
  const handleEditorWillMount = (monaco: any) => {
    // Register LaTeX language
    monaco.languages.register({ id: "latex" });

    // Set syntax highlighting
    monaco.languages.setMonarchTokensProvider("latex", latex);

    // Add LaTeX-specific autocomplete suggestions
    monaco.languages.registerCompletionItemProvider("latex", {
      provideCompletionItems: (model: any, position: any) => {
        const suggestions = [
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

        return { suggestions };
      },
    });

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

  return (
    <Editor
      height={"100%"}
      defaultLanguage="latex"
      value={value}
      onChange={onChange}
      theme="light"
      beforeMount={handleEditorWillMount}
      options={{
        fontSize: 13,
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
