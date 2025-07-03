import Editor from "@monaco-editor/react";
import latex from "monaco-latex";

export default function LatexEditor({
  value,
  onChange,
}: {
  value: string;
  onChange: (val: string | undefined) => void;
}) {
  const handleEditorWillMount = (monaco: any) => {
    monaco.languages.register({ id: "latex" });
    monaco.languages.setMonarchTokensProvider("latex", latex);
  };

  return (
    <Editor
      height="635px"
      defaultLanguage="latex"
      value={value}
      onChange={onChange}
      theme="light"
      beforeMount={handleEditorWillMount}
      options={{
        fontSize: 12,
        minimap: {
          enabled: false,
        },
        lineNumbersMinChars: 2,
      }}
    />
  );
}
