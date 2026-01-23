import Editor from '@monaco-editor/react';

interface CodeEditorProps {
    value: string;
    onChange: (value: string) => void;
    readOnly?: boolean;
    height?: string;
    wordWrap?: 'on' | 'off' | 'wordWrapColumn' | 'bounded';
}

export function CodeEditor({ value, onChange, readOnly = false, height = '600px', wordWrap = 'on' }: CodeEditorProps) {
    return (
        <div className="rounded-lg overflow-hidden border border-cyan-200 bg-white h-full">
            <Editor
                height={height}
                defaultLanguage="python"
                value={value}
                onChange={(val) => onChange(val || '')}
                theme="vs-light"
                options={{
                    readOnly,
                    minimap: { enabled: false },
                    fontSize: 14,
                    fontFamily: "'JetBrains Mono', 'Consolas', 'Courier New', monospace",
                    lineNumbers: 'on',
                    scrollBeyondLastLine: false,
                    wordWrap: wordWrap,
                    automaticLayout: true,
                    tabSize: 4,
                    insertSpaces: true,
                    folding: true,
                    bracketPairColorization: { enabled: true },
                    formatOnPaste: true,
                    formatOnType: true,
                    suggestOnTriggerCharacters: true,
                    quickSuggestions: true,
                    padding: { top: 8, bottom: 8 },
                }}
            />
        </div>
    );
}
