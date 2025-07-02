import Editor from "@monaco-editor/react";

export default function LatexEditor({
  value,
  onChange,
}: {
  value: string;
  onChange: (val: string | undefined) => void;
}) {
  return (
    <Editor
      height="600px"
      defaultLanguage="latex"
      value={value}
      onChange={onChange}
      theme="light"
      options={{
        fontSize: 16,
        minimap: {
          enabled: false,
        },
      }}
    />
  );
}
