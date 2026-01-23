import { Play, Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { MiniSelect } from '../CustomSelect';

interface OperationAreaProps {
  input: string;
  output: string;
  inputFormat: string;
  outputFormat: string;
  isProcessing: boolean;
  onInputChange: (value: string) => void;
  onInputFormatChange: (format: string) => void;
  onOutputFormatChange: (format: string) => void;
  onExecute: () => void;
}

const formatOptions = [
  { value: 'UTF-8', label: 'UTF-8' },
  { value: 'HEX', label: 'HEX' },
  { value: 'ASCII', label: 'ASCII' },
];

export function OperationArea({
  input,
  output,
  inputFormat,
  outputFormat,
  isProcessing,
  onInputChange,
  onInputFormatChange,
  onOutputFormatChange,
  onExecute
}: OperationAreaProps) {
  const [copied, setCopied] = useState(false);

  const copyOutput = () => {
    navigator.clipboard.writeText(output);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="h-full bg-white/50 backdrop-blur-md rounded-3xl p-5 ring-1 ring-blue-200 flex flex-col">
      <h2 className="text-base mb-3 text-gray-700 flex items-center gap-2 flex-shrink-0">
        <div className="w-1 h-5 bg-gradient-to-b from-blue-500 to-cyan-500 rounded-full"></div>
        操作区域
      </h2>

      <div className="flex-1 flex flex-col gap-3 min-h-0">
        {/* Input Area */}
        <div className="flex-1 flex flex-col min-h-0">
          <div className="mb-2 flex items-center justify-between">
            <label className="text-sm text-gray-600 font-medium">输入</label>
            <div className="flex items-center gap-2">
              <MiniSelect
                value={inputFormat}
                onChange={onInputFormatChange}
                options={formatOptions}
              />
              <span className="text-xs text-gray-400">{input.length} 字符</span>
            </div>
          </div>
          <textarea
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            placeholder="在此输入需要处理的文本..."
            className="flex-1 w-full px-4 py-3 bg-white/60 border border-blue-200 rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all text-sm font-mono"
          />
        </div>

        {/* Execute Button */}
        <div className="flex-shrink-0 flex items-center justify-center py-1">
          <button
            onClick={onExecute}
            disabled={isProcessing}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ${isProcessing ? 'animate-pulse' : ''}`}
          >
            <Play className="w-4 h-4" fill="currentColor" />
            {isProcessing ? '处理中...' : '执行'}
          </button>
        </div>

        {/* Output Area */}
        <div className="flex-1 flex flex-col min-h-0">
          <div className="mb-2 flex items-center justify-between">
            <label className="text-sm text-gray-600 font-medium">输出</label>
            <div className="flex items-center gap-2">
              <MiniSelect
                value={outputFormat}
                onChange={onOutputFormatChange}
                options={formatOptions}
              />
              <button
                onClick={copyOutput}
                disabled={!output}
                className="p-1.5 rounded-lg hover:bg-blue-100 text-gray-500 hover:text-blue-600 transition-colors disabled:opacity-30"
                title="复制"
              >
                {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
              </button>
              <span className="text-xs text-gray-400">{output.length} 字符</span>
            </div>
          </div>
          <div className="flex-1 w-full px-4 py-3 bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-200 rounded-2xl overflow-auto text-sm font-mono text-gray-700 whitespace-pre-wrap">
            {output || <span className="text-gray-400">输出结果将显示在此处...</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
