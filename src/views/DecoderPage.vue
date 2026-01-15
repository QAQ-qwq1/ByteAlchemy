
<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import draggable from 'vuedraggable'
import { ElMessage } from 'element-plus'

// --- State ---
const inputData = ref('')
const outputData = ref('')
const inputFormat = ref('UTF-8')
const outputFormat = ref('UTF-8')
const hexSeparator = ref('无分隔符')
const isBigEndian = ref(true)

const sboxNames = ref(['Standard AES', 'Standard SM4'])
const recipe = ref([]) // Active operations in the chain

// --- Operation Palette ---
const palette = [
    { category: '编码 / 解码', ops: [
        { id: 'base64_encode', label: 'Base64 编码' }, { id: 'base64_decode', label: 'Base64 解码' },
        { id: 'base32_encode', label: 'Base32 编码' }, { id: 'base32_decode', label: 'Base32 解码' },
        { id: 'base16_encode', label: 'Base16 编码' }, { id: 'base16_decode', label: 'Base16 解码' },
        { id: 'base85_encode', label: 'Base85 编码' }, { id: 'base85_decode', label: 'Base85 解码' },
        { id: 'url_encode', label: 'URL 编码' }, { id: 'url_decode', label: 'URL 解码' },
        { id: 'html_encode', label: 'HTML 编码' }, { id: 'html_decode', label: 'HTML 解码' },
        { id: 'unicode_encode', label: 'Unicode 编码' }, { id: 'unicode_decode', label: 'Unicode 解码' },
    ]},
    { category: '加密 / 解密', ops: [
        { id: 'aes_encrypt', label: 'AES 加密', params: { key: '1234567890123456', iv: '', mode: 'CBC', padding: 'pkcs7', sbox_name: 'Standard AES', key_type: 'utf-8', iv_type: 'utf-8', swap_key_schedule: false, swap_data_round: false } },
        { id: 'aes_decrypt', label: 'AES 解密', params: { key: '1234567890123456', iv: '', mode: 'CBC', padding: 'pkcs7', sbox_name: 'Standard AES', key_type: 'utf-8', iv_type: 'utf-8', swap_key_schedule: false, swap_data_round: false } },
        { id: 'sm4_encrypt', label: 'SM4 加密', params: { key: '1234567890123456', iv: '', mode: 'ECB', padding: 'pkcs7', sbox_name: 'Standard SM4', key_type: 'utf-8', iv_type: 'utf-8', swap_key_schedule: false, swap_data_round: false } },
        { id: 'sm4_decrypt', label: 'SM4 解密', params: { key: '1234567890123456', iv: '', mode: 'ECB', padding: 'pkcs7', sbox_name: 'Standard SM4', key_type: 'utf-8', iv_type: 'utf-8', swap_key_schedule: false, swap_data_round: false } },
    ]}
]

// --- Logic ---
const loadSboxNames = async (retries = 5) => {
    try {
        const response = await axios.get('http://127.0.0.1:3335/api/sbox/names')
        sboxNames.value = response.data.names
    } catch (error) { 
        console.error("Load SBox Names failed, retrying...", error)
        if (retries > 0) {
            setTimeout(() => loadSboxNames(retries - 1), 500)
        }
    }
}

const addToRecipe = (op) => {
    recipe.value.push({
        ...op,
        instanceId: Date.now() + Math.random(),
        enabled: true,
        params: op.params ? JSON.parse(JSON.stringify(op.params)) : {}
    })
}

const removeFromRecipe = (index) => {
    recipe.value.splice(index, 1)
}

const executeRecipe = async () => {
    try {
        // 1. Convert Input Format if needed
        let currentInput = inputData.value
        let skipConversion = false
        
        // Smart Input Handling for Crypto Ops (Pass Hex directly)
        if (inputFormat.value === 'HEX' && recipe.value.length > 0) {
            const firstOpId = recipe.value[0].id
            const cryptoOps = ['aes_encrypt', 'aes_decrypt', 'sm4_encrypt', 'sm4_decrypt']
            if (cryptoOps.includes(firstOpId)) {
                skipConversion = true
                // Do not convert, pass raw Hex string
            }
        }

        if (!skipConversion && (inputFormat.value !== 'UTF-8' || hexSeparator.value !== '无分隔符')) {
             const conv = await axios.post('http://127.0.0.1:3335/api/utils/convert_format', {
                 data: currentInput,
                 from_fmt: inputFormat.value,
                 to_fmt: 'UTF-8',
                 separator: hexSeparator.value === '无分隔符' ? '' : (hexSeparator.value === '空格' ? ' ' : hexSeparator.value)
             })
             currentInput = conv.data.result
        }

        // 2. Run Pipeline
        const activeRecipe = recipe.value.filter(r => r.enabled !== false)
        const operations = activeRecipe.map((r, index) => {
            const op = { name: r.id, params: { ...r.params } }
            // Inject data_type for first op if using Hex Mode
            if (index === 0 && skipConversion && inputFormat.value === 'HEX') {
                op.params.data_type = 'hex'
            }
            return op
        })

        const response = await axios.post('http://127.0.0.1:3335/api/pipeline/run', {
            data: currentInput,
            operations: operations
        })
        let result = response.data.result

        // 3. Convert Output Format
        if (outputFormat.value !== 'UTF-8') {
            const conv = await axios.post('http://127.0.0.1:3335/api/utils/convert_format', {
                 data: result,
                 from_fmt: 'UTF-8',
                 to_fmt: outputFormat.value
             })
             result = conv.data.result
        }

        outputData.value = result
        ElMessage.success('执行成功')
    } catch (error) {
        console.error("Execute Recipe Error:", error)
        outputData.value = `[Error] ${error.response?.data?.detail || error.message}`
        if (error.message === 'Network Error') {
            outputData.value += " (Check if Python backend is running on 127.0.0.1:3335)"
        }
        ElMessage.error('执行出错')
    }
}

const toggleEndian = async () => {
    try {
        isBigEndian.value = !isBigEndian.value
        const response = await axios.post('http://127.0.0.1:3335/api/utils/endian_swap', {
            data: inputData.value,
            from_fmt: inputFormat.value,
            to_fmt: '', // ignored for swap
            separator: hexSeparator.value === '无分隔符' ? '' : (hexSeparator.value === '空格' ? ' ' : hexSeparator.value)
        })
        inputData.value = response.data.result
        ElMessage.success(`切换为 ${isBigEndian.value ? 'Big Endian' : 'Little Endian'}`)
    } catch (error) { console.error(error) }
}

onMounted(() => {
    loadSboxNames()
})
</script>

<template>
    <div class="decoder-container">
        <!-- Triple Column Layout -->
        
        <!-- Left: Palette -->
        <div class="palette-col">
            <div class="col-header lighting-effect">操作列表</div>
            <div class="palette-content">
                <el-scrollbar>
                    <div v-for="cat in palette" :key="cat.category" class="category-group">
                        <div class="category-label">{{ cat.category }}</div>
                        <div v-for="op in cat.ops" :key="op.id" class="op-item" @click="addToRecipe(op)">
                            {{ op.label }}
                            <el-icon class="plus"><Plus /></el-icon>
                        </div>
                    </div>
                </el-scrollbar>
            </div>
        </div>

        <!-- Center: Recipe -->
        <div class="recipe-col">
            <div class="col-header lighting-effect">
                编码链 (Operation Chain)
                <el-button type="primary" size="small" @click="executeRecipe" round>
                    执行 <el-icon class="el-icon--right"><VideoPlay /></el-icon>
                </el-button>
            </div>
            <div class="recipe-content">
                <el-scrollbar>
                    <div v-if="recipe.length === 0" class="empty-recipe">
                        点击左侧操作以添加到链中
                    </div>
                    <draggable 
                        v-model="recipe" 
                        item-key="instanceId" 
                        handle=".drag-handle"
                        class="drag-list"
                    >
                        <template #item="{ element, index }">
                            <el-card class="recipe-item" :class="{ 'disabled': element.enabled === false }" :body-style="{ padding: '0px' }">
                                <div class="recipe-item-header">
                                    <div class="header-left">
                                        <el-icon class="drag-handle"><Grid /></el-icon>
                                        <span class="item-label">{{ element.label }}</span>
                                    </div>
                                    <div class="item-actions">
                                        <el-switch v-model="element.enabled" size="small" style="margin-right: 8px" />
                                        <el-button link type="danger" size="small" @click="removeFromRecipe(index)">
                                            <el-icon><Close /></el-icon>
                                        </el-button>
                                    </div>
                                </div>
                                <!-- Params -->
                                <div v-if="element.params && element.enabled !== false" class="item-params">
                                    <div v-if="element.params.key !== undefined" class="param-row">
                                        <span class="param-label">Key:</span>
                                        <el-input v-model="element.params.key" size="small" placeholder="Key" style="flex: 1" />
                                        <el-select v-if="element.params.key_type !== undefined" v-model="element.params.key_type" size="small" style="width: 85px">
                                             <el-option label="UTF-8" value="utf-8"/>
                                             <el-option label="HEX" value="hex"/>
                                        </el-select>
                                    </div>
                                    <div v-if="element.params.iv !== undefined" class="param-row">
                                        <span class="param-label">IV:</span>
                                        <el-input v-model="element.params.iv" size="small" placeholder="IV" style="flex: 1" />
                                        <el-select v-if="element.params.iv_type !== undefined" v-model="element.params.iv_type" size="small" style="width: 85px">
                                             <el-option label="UTF-8" value="utf-8"/>
                                             <el-option label="HEX" value="hex"/>
                                        </el-select>
                                    </div>
                                    <div v-if="element.params.mode !== undefined" class="param-row">
                                        <span class="param-label">Mode:</span>
                                        <el-select v-model="element.params.mode" size="small" style="width: 100%">
                                            <el-option v-for="m in ['ECB', 'CBC', 'CFB', 'OFB', 'CTR']" :key="m" :label="m" :value="m" />
                                        </el-select>
                                    </div>
                                    <div v-if="element.params.padding !== undefined" class="param-row">
                                        <span class="param-label">Padding:</span>
                                        <el-select v-model="element.params.padding" size="small" style="width: 100%">
                                            <el-option v-for="p in ['pkcs7', 'zeropadding', 'iso10126', 'ansix923', 'nopadding']" :key="p" :label="p" :value="p" />
                                        </el-select>
                                    </div>
                                    <div v-if="element.params.sbox_name !== undefined" class="param-row">
                                        <span class="param-label">S-Box:</span>
                                        <el-select v-model="element.params.sbox_name" size="small" style="width: 100%">
                                            <el-option v-for="name in sboxNames" :key="name" :label="name" :value="name" />
                                        </el-select>
                                    </div>
                                    <div v-if="element.params.swap_key_schedule !== undefined" class="param-row">
                                        <el-checkbox v-model="element.params.swap_key_schedule" label="Swap Key Schedule (Magic)" size="small" />
                                    </div>
                                    <div v-if="element.params.swap_data_round !== undefined" class="param-row">
                                        <el-checkbox v-model="element.params.swap_data_round" label="Swap Data Round (Magic)" size="small" />
                                    </div>
                                    <div v-if="element.id.startsWith('sm4') || element.id.startsWith('aes')" class="hint-text" style="font-size: 11px; color: #909399; margin-top: 4px; line-height: 1.4;">
                                        <div v-if="element.params.swap_key_schedule">ℹ️ Swap Key: 在密钥扩展阶段交换S盒输出 (字节序翻转)</div>
                                        <div v-if="element.params.swap_data_round">ℹ️ Swap Data: 在加密轮函数中交换S盒输出/列 (字节序翻转)</div>
                                    </div>
                                </div>
                            </el-card>
                        </template>

                    </draggable>
                </el-scrollbar>
            </div>
        </div>

        <!-- Right: Work Area -->
        <div class="work-col">
            <!-- Input -->
            <div class="section input-section">
                <div class="section-header lighting-effect">
                    <span>输入 (Input)</span>
                    <div class="controls">
                        <el-select v-model="inputFormat" size="small" style="width: 90px">
                            <el-option label="UTF-8" value="UTF-8" />
                            <el-option label="HEX" value="HEX" />
                            <el-option label="ASCII" value="ASCII" />
                        </el-select>
                        <el-select v-if="inputFormat === 'HEX'" v-model="hexSeparator" size="small" style="width: 100px">
                            <el-option label="无分隔符" value="无分隔符" />
                            <el-option label="空格" value="空格" />
                            <el-option label="0x" value="0x" />
                            <el-option label="\x" value="\x" />
                        </el-select>
                        <el-button 
                            size="small" 
                            class="endian-btn"
                            :class="{ 'be': isBigEndian, 'le': !isBigEndian }"
                            @click="toggleEndian"
                        >
                            {{ isBigEndian ? 'BE' : 'LE' }}
                        </el-button>
                    </div>
                </div>
                <el-input
                    v-model="inputData"
                    type="textarea"
                    placeholder="在此输入数据..."
                    resize="none"
                    class="io-textarea"
                />
            </div>

            <!-- Output -->
            <div class="section output-section">
                <div class="section-header lighting-effect">
                    <span>输出 (Output)</span>
                    <div class="controls">
                        <el-select v-model="outputFormat" size="small" style="width: 90px">
                            <el-option label="UTF-8" value="UTF-8" />
                            <el-option label="HEX" value="HEX" />
                            <el-option label="ASCII" value="ASCII" />
                        </el-select>
                    </div>
                </div>
                <el-input
                    v-model="outputData"
                    type="textarea"
                    readonly
                    placeholder="处理结果..."
                    resize="none"
                    class="io-textarea"
                />
            </div>
        </div>
    </div>
</template>


<style scoped>
.decoder-container {
    display: flex;
    height: 100%;
    gap: 16px;
    padding: 16px;
    background: var(--bg-color);
    color: var(--text-color);
    overflow: hidden;
}

.col-header {
    font-size: 13px;
    font-weight: 700;
    color: var(--accent-color);
    margin-bottom: 12px;
    text-transform: uppercase;
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 32px;
}

/* Palette */
.palette-col {
    width: 240px;
    display: flex;
    flex-direction: column;
}

.palette-content {
    flex: 1;
    background: var(--panel-bg);
    border-radius: 8px;
    padding: 12px;
    border: 1px solid var(--border-color);
    overflow: hidden; 
}

.category-group {
    margin-bottom: 20px;
}

.category-label {
    font-size: 11px;
    color: var(--el-text-color-secondary);
    margin-bottom: 8px;
    padding-left: 4px;
    font-weight: bold;
}

.op-item {
    padding: 8px 12px;
    background: var(--item-bg);
    border-radius: 6px;
    margin-bottom: 6px;
    font-size: 13px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.2s;
    border: 1px solid transparent;
}

.op-item:hover {
    background: var(--hover-bg);
    transform: translateX(4px);
    border-color: var(--el-color-primary);
    color: var(--el-color-primary);
}

.op-item .plus {
    font-size: 12px;
}

/* Recipe */
.recipe-col {
    width: 320px;
    display: flex;
    flex-direction: column;
}

.recipe-content {
    flex: 1;
    background: var(--panel-bg);
    border-radius: 8px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    border: 1px solid var(--border-color);
    overflow: hidden;
}

.empty-recipe {
    text-align: center;
    color: var(--el-text-color-secondary);
    font-size: 13px;
    margin-top: 40px;
    border: 2px dashed var(--border-color);
    padding: 24px;
    border-radius: 12px;
}

.recipe-item {
    margin-bottom: 12px;
    border: 1px solid var(--border-color);
    background: var(--item-bg);
    transition: opacity 0.3s;
    --el-card-bg-color: var(--item-bg);
    --el-card-border-color: var(--border-color);
}

.recipe-item.disabled {
    opacity: 0.6;
}

.recipe-item-header {
    background: var(--header-bg);
    padding: 8px 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 13px;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 8px;
}

.drag-handle {
    cursor: grab;
    color: var(--el-text-color-secondary);
    font-size: 16px;
}

.drag-handle:active {
    cursor: grabbing;
}

.item-label {
    font-weight: 500;
}

.item-params {
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.param-row {
    display: flex;
    align-items: center;
    gap: 8px;
}

.param-label {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    width: 60px;
}

/* Work Area */
.work-col {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.section {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: var(--panel-bg);
    border-radius: 12px;
    border: 1px solid var(--border-color);
    overflow: hidden;
}

.section-header {
    background: var(--header-bg);
    padding: 8px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    font-weight: bold;
    color: var(--text-color);
    height: 48px;
}

.controls {
    display: flex;
    align-items: center;
    gap: 8px;
}

.io-textarea {
    flex: 1;
    height: 100%;
}

.io-textarea :deep(.el-textarea__inner) {
    height: 100%;
    border: none;
    border-radius: 0;
    resize: none;
    padding: 16px;
    background: transparent;
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    box-shadow: none;
    color: var(--text-color);
}
</style>


