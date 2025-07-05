import Editor from "@monaco-editor/react";
import latex from "monaco-latex";
import { LatexEditorProps } from "@/lib/types";

export default function LatexEditor({ value, onChange }: LatexEditorProps) {
  const handleEditorWillMount = (monaco: any) => {
    monaco.languages.register({ id: "latex" });
    monaco.languages.setMonarchTokensProvider("latex", latex);
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
      }}
    />
  );
}
