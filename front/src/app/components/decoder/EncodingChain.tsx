import { useRef, useEffect, useState } from 'react';
import { useDrag, useDrop } from 'react-dnd';
import { Binary, Lock, X, GripVertical, Settings2, Hash, Link, Code2, Type, Shield, ShieldCheck, Key, Fingerprint, ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import type { OperationType } from './EncodingTypesList';
import { MiniSelect } from '../CustomSelect';

export interface EncodingOperation {
  id: string;
  type: OperationType;
  params: Record<string, any>;
  enabled: boolean;
}

interface EncodingChainProps {
  chain: EncodingOperation[];
  onRemove: (id: string) => void;
  onUpdateParams: (id: string, params: Record<string, any>) => void;
  onMove: (dragIndex: number, hoverIndex: number) => void;
  onToggle: (id: string) => void;
  sboxNames: string[];
}

const iconMap: Record<string, any> = {
  base64_encode: Binary, base64_decode: Binary,
  base32_encode: Binary, base32_decode: Binary,
  base16_encode: Hash, base16_decode: Hash,
  base85_encode: Binary, base85_decode: Binary,
  url_encode: Link, url_decode: Link,
  html_encode: Code2, html_decode: Code2,
  unicode_encode: Type, unicode_decode: Type,
  md5_hash: Fingerprint,
  rc4_encrypt: Key, rc4_decrypt: Key,
  des_encrypt: Shield, des_decrypt: Shield,
  triple_des_encrypt: ShieldCheck, triple_des_decrypt: ShieldCheck,
  aes_encrypt: Lock, aes_decrypt: Lock,
  sm4_encrypt: Lock, sm4_decrypt: Lock,
};

const colorMap: Record<string, string> = {
  base64_encode: 'from-pink-500 to-rose-500', base64_decode: 'from-pink-500 to-rose-500',
  base32_encode: 'from-pink-500 to-rose-500', base32_decode: 'from-pink-500 to-rose-500',
  base16_encode: 'from-pink-500 to-rose-500', base16_decode: 'from-pink-500 to-rose-500',
  base85_encode: 'from-pink-500 to-rose-500', base85_decode: 'from-pink-500 to-rose-500',
  url_encode: 'from-pink-500 to-rose-500', url_decode: 'from-pink-500 to-rose-500',
  html_encode: 'from-pink-500 to-rose-500', html_decode: 'from-pink-500 to-rose-500',
  unicode_encode: 'from-pink-500 to-rose-500', unicode_decode: 'from-pink-500 to-rose-500',
  md5_hash: 'from-amber-500 to-orange-500',
  rc4_encrypt: 'from-purple-500 to-pink-500', rc4_decrypt: 'from-purple-500 to-pink-500',
  des_encrypt: 'from-purple-500 to-pink-500', des_decrypt: 'from-purple-500 to-pink-500',
  triple_des_encrypt: 'from-purple-500 to-pink-500', triple_des_decrypt: 'from-purple-500 to-pink-500',
  aes_encrypt: 'from-purple-500 to-pink-500', aes_decrypt: 'from-purple-500 to-pink-500',
  sm4_encrypt: 'from-purple-500 to-pink-500', sm4_decrypt: 'from-purple-500 to-pink-500',
};

const labelMap: Record<string, string> = {
  base64_encode: 'Base64 编码', base64_decode: 'Base64 解码',
  base32_encode: 'Base32 编码', base32_decode: 'Base32 解码',
  base16_encode: 'Base16 编码', base16_decode: 'Base16 解码',
  base85_encode: 'Base85 编码', base85_decode: 'Base85 解码',
  url_encode: 'URL 编码', url_decode: 'URL 解码',
  html_encode: 'HTML 编码', html_decode: 'HTML 解码',
  unicode_encode: 'Unicode 编码', unicode_decode: 'Unicode 解码',
  md5_hash: 'MD5 哈希',
  rc4_encrypt: 'RC4 加密', rc4_decrypt: 'RC4 解密',
  des_encrypt: 'DES 加密', des_decrypt: 'DES 解密',
  triple_des_encrypt: '3DES 加密', triple_des_decrypt: '3DES 解密',
  aes_encrypt: 'AES 加密', aes_decrypt: 'AES 解密',
  sm4_encrypt: 'SM4 加密', sm4_decrypt: 'SM4 解密',
};

// Check if operation needs parameters
const hasParams = (type: OperationType) => {
  return type.includes('aes') || type.includes('sm4') || type.includes('des') ||
    type.includes('rc4') || type === 'md5_hash';
};

export function EncodingChain({ chain, onRemove, onUpdateParams, onMove, onToggle, sboxNames }: EncodingChainProps) {
  return (
    <div className="h-full bg-white/50 backdrop-blur-md rounded-3xl p-5 ring-1 ring-purple-200 flex flex-col">
      <h2 className="text-base mb-3 text-gray-700 flex items-center gap-2 flex-shrink-0">
        <div className="w-1 h-5 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full"></div>
        编码链
        <span className="ml-auto text-xs text-gray-400">
          {chain.length} 个操作
        </span>
      </h2>

      <div className="flex-1 space-y-2 overflow-y-auto">
        {chain.length === 0 ? (
          <div className="h-full flex items-center justify-center text-center px-4">
            <div className="text-gray-400 text-sm border-2 border-dashed border-gray-200 rounded-2xl p-6 w-full">
              <div className="mb-2">点击左侧操作</div>
              <div>添加到编码链</div>
            </div>
          </div>
        ) : (
          <AnimatePresence>
            {chain.map((operation, index) => (
              <ChainItem
                key={operation.id}
                operation={operation}
                index={index}
                onRemove={onRemove}
                onUpdateParams={onUpdateParams}
                onMove={onMove}
                onToggle={onToggle}
                sboxNames={sboxNames}
              />
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}

interface ChainItemProps {
  operation: EncodingOperation;
  index: number;
  onRemove: (id: string) => void;
  onUpdateParams: (id: string, params: Record<string, any>) => void;
  onMove: (dragIndex: number, hoverIndex: number) => void;
  onToggle: (id: string) => void;
  sboxNames: string[];
}

function ChainItem({ operation, index, onRemove, onUpdateParams, onMove, onToggle, sboxNames }: ChainItemProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [showParams, setShowParams] = useState(false);

  const [{ isDragging }, drag, preview] = useDrag({
    type: 'CHAIN_ITEM',
    item: { index },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const [, drop] = useDrop({
    accept: 'CHAIN_ITEM',
    hover: (item: { index: number }) => {
      if (!ref.current) return;
      const dragIndex = item.index;
      const hoverIndex = index;
      if (dragIndex === hoverIndex) return;
      onMove(dragIndex, hoverIndex);
      item.index = hoverIndex;
    },
  });

  drag(drop(ref));

  const Icon = iconMap[operation.type] || Binary;
  const color = colorMap[operation.type] || 'from-gray-500 to-gray-600';
  const label = labelMap[operation.type] || operation.type;
  const showSettings = hasParams(operation.type);

  return (
    <motion.div
      ref={ref}
      className={`bg-white/80 rounded-xl ring-1 ring-purple-100 transition-all duration-200 ${isDragging ? 'opacity-50 scale-95' : 'hover:ring-2 hover:ring-purple-300 hover:shadow-md'
        } ${!operation.enabled ? 'opacity-50' : ''}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
    >
      <div className="p-3">
        <div className="flex items-center gap-2">
          {/* Drag Handle */}
          <div className="cursor-move text-gray-400 hover:text-purple-500 transition-colors">
            <GripVertical className="w-4 h-4" />
          </div>

          {/* Icon */}
          <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center flex-shrink-0 shadow-sm`}>
            <Icon className="w-4 h-4 text-white" strokeWidth={2.5} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-gray-800 truncate">{label}</div>
            <div className="text-xs text-gray-400">步骤 {index + 1}</div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1">
            {/* Enable/Disable Switch */}
            <button
              onClick={() => onToggle(operation.id)}
              className={`w-8 h-5 rounded-full transition-colors ${operation.enabled ? 'bg-purple-500' : 'bg-gray-300'}`}
            >
              <div className={`w-4 h-4 rounded-full bg-white shadow transition-transform ${operation.enabled ? 'translate-x-3.5' : 'translate-x-0.5'}`} />
            </button>
            {showSettings && (
              <button
                onClick={() => setShowParams(!showParams)}
                className={`p-1 rounded-lg hover:bg-purple-100 transition-colors ${showParams ? 'text-purple-600 bg-purple-100' : 'text-gray-500'}`}
              >
                <ChevronDown className={`w-4 h-4 transition-transform ${showParams ? 'rotate-180' : ''}`} />
              </button>
            )}
            <button
              onClick={() => onRemove(operation.id)}
              className="p-1 rounded-lg hover:bg-red-100 text-gray-500 hover:text-red-600 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Parameters Panel */}
        <AnimatePresence>
          {showParams && showSettings && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="mt-3 pt-3 border-t border-purple-100 space-y-2">
                <ParamsPanel operation={operation} onUpdateParams={onUpdateParams} sboxNames={sboxNames} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

interface ParamsPanelProps {
  operation: EncodingOperation;
  onUpdateParams: (id: string, params: Record<string, any>) => void;
  sboxNames: string[];
}

function ParamsPanel({ operation, onUpdateParams, sboxNames }: ParamsPanelProps) {
  const { type, params, id } = operation;
  const update = (key: string, value: any) => onUpdateParams(id, { ...params, [key]: value });

  const inputClass = "w-full px-2 py-1.5 text-xs bg-white/60 border border-purple-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-purple-400";
  const labelClass = "text-xs text-gray-600 mb-1";

  const typeOptions = [
    { value: 'utf-8', label: 'UTF-8' },
    { value: 'hex', label: 'HEX' },
  ];

  const outputFormatOptions = [
    { value: 'hex', label: 'HEX' },
    { value: 'base64', label: 'Base64' },
  ];

  const modeOptions = ['ECB', 'CBC', 'CFB', 'OFB', 'CTR'].map(m => ({ value: m, label: m }));
  const paddingOptions = ['pkcs7', 'zeropadding', 'iso10126', 'ansix923', 'nopadding'].map(p => ({ value: p, label: p }));
  const sboxOptions = sboxNames.map(name => ({ value: name, label: name }));

  // MD5
  if (type === 'md5_hash') {
    return (
      <div>
        <label className={labelClass}>输出格式</label>
        <MiniSelect
          value={params.output_format || 'hex'}
          onChange={(v) => update('output_format', v)}
          options={outputFormatOptions}
        />
      </div>
    );
  }

  // RC4
  if (type.includes('rc4')) {
    return (
      <>
        <div className="flex gap-2">
          <div className="flex-1">
            <label className={labelClass}>Key</label>
            <input type="text" value={params.key || ''} onChange={(e) => update('key', e.target.value)} placeholder="密钥" className={inputClass} />
          </div>
          <div className="w-20">
            <label className={labelClass}>类型</label>
            <MiniSelect
              value={params.key_type || 'utf-8'}
              onChange={(v) => update('key_type', v)}
              options={typeOptions}
            />
          </div>
        </div>
        <label className="flex items-center gap-2 text-xs text-gray-600">
          <input type="checkbox" checked={params.swap_bytes || false} onChange={(e) => update('swap_bytes', e.target.checked)} className="rounded" />
          Swap Bytes (Magic KSA)
        </label>
        <div>
          <label className={labelClass}>S-Box</label>
          <MiniSelect
            value={params.sbox_name || 'Standard RC4'}
            onChange={(v) => update('sbox_name', v)}
            options={sboxOptions}
          />
        </div>
      </>
    );
  }

  // DES / 3DES / AES / SM4
  const showIV = params.mode && params.mode !== 'ECB';
  const isSM4OrAES = type.includes('sm4') || type.includes('aes');

  return (
    <>
      <div className="flex gap-2">
        <div className="flex-1">
          <label className={labelClass}>Key</label>
          <input type="text" value={params.key || ''} onChange={(e) => update('key', e.target.value)} placeholder="密钥" className={inputClass} />
        </div>
        <div className="w-20">
          <label className={labelClass}>类型</label>
          <MiniSelect
            value={params.key_type || 'utf-8'}
            onChange={(v) => update('key_type', v)}
            options={typeOptions}
          />
        </div>
      </div>

      {showIV && (
        <div className="flex gap-2">
          <div className="flex-1">
            <label className={labelClass}>IV</label>
            <input type="text" value={params.iv || ''} onChange={(e) => update('iv', e.target.value)} placeholder="初始向量" className={inputClass} />
          </div>
          <div className="w-20">
            <label className={labelClass}>类型</label>
            <MiniSelect
              value={params.iv_type || 'utf-8'}
              onChange={(v) => update('iv_type', v)}
              options={typeOptions}
            />
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <div className="flex-1">
          <label className={labelClass}>Mode</label>
          <MiniSelect
            value={params.mode || 'ECB'}
            onChange={(v) => update('mode', v)}
            options={modeOptions}
          />
        </div>
        <div className="flex-1">
          <label className={labelClass}>Padding</label>
          <MiniSelect
            value={params.padding || 'pkcs7'}
            onChange={(v) => update('padding', v)}
            options={paddingOptions}
          />
        </div>
      </div>

      {isSM4OrAES && (
        <>
          <div>
            <label className={labelClass}>S-Box</label>
            <MiniSelect
              value={params.sbox_name || sboxNames[0] || ''}
              onChange={(v) => update('sbox_name', v)}
              options={sboxOptions}
            />
          </div>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-xs text-gray-600">
              <input type="checkbox" checked={params.swap_key_schedule || false} onChange={(e) => update('swap_key_schedule', e.target.checked)} className="rounded" />
              Swap Key Schedule
            </label>
            <label className="flex items-center gap-2 text-xs text-gray-600">
              <input type="checkbox" checked={params.swap_data_round || false} onChange={(e) => update('swap_data_round', e.target.checked)} className="rounded" />
              Swap Data Round
            </label>
          </div>
        </>
      )}

      {/* DES/3DES Custom S-Box */}
      {(type.includes('des')) && (
        <div>
          <label className={labelClass}>S-Box</label>
          <MiniSelect
            value={params.sbox_name || 'Standard DES'}
            onChange={(v) => update('sbox_name', v)}
            options={sboxOptions}
          />
        </div>
      )}
    </>
  );
}