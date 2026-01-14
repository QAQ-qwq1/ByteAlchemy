
<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const activeTab = ref('generate')

// Generate State
const includeDigits = ref(true)
const includeLower = ref(true)
const includeUpper = ref(true)
const customChars = ref('')
const excludeChars = ref('')
const generatedResult = ref('')

// Escape State
const escapeInput = ref('')
const escapeResult = ref('')

const generate = async () => {
    try {
        const response = await axios.post('http://127.0.0.1:3333/api/regex/generate', {
            include_digits: includeDigits.value,
            include_lower: includeLower.value,
            include_upper: includeUpper.value,
            custom_chars: customChars.value,
            exclude_chars: excludeChars.value
        })
        generatedResult.value = response.data.result
        ElMessage.success('生成成功')
    } catch (error) {
         generatedResult.value = "Error generating regex"
         ElMessage.error('生成失败')
    }
}

const escape = async () => {
    try {
        const response = await axios.post('http://127.0.0.1:3333/api/regex/escape', {
            data: escapeInput.value
        })
        escapeResult.value = response.data.result
        ElMessage.success('转义成功')
    } catch (error) {
        escapeResult.value = "Error escaping text"
        ElMessage.error('转义失败')
    }
}
</script>

<template>
    <div class="page-container">
        <el-tabs v-model="activeTab" class="custom-tabs">
            <el-tab-pane label="正则生成" name="generate">
                <div class="content-area">
                    <div class="control-panel">
                        <div class="checkbox-group">
                            <el-checkbox v-model="includeDigits" label="数字 (0-9)" border />
                            <el-checkbox v-model="includeLower" label="小写字母 (a-z)" border />
                            <el-checkbox v-model="includeUpper" label="大写字母 (A-Z)" border />
                        </div>
                        
                        <div class="input-row">
                            <el-input 
                                v-model="customChars" 
                                placeholder="额外包含字符 (Custom Chars)" 
                                clearable
                            >
                                <template #prepend>包含</template>
                            </el-input>
                            <el-input 
                                v-model="excludeChars" 
                                placeholder="排除特定字符 (Exclude Chars)" 
                                clearable
                            >
                                <template #prepend>排除</template>
                            </el-input>
                        </div>

                        <el-button type="primary" @click="generate" size="large" class="action-btn">生成正则表达式</el-button>
                    </div>
                    
                    <div class="result-area">
                        <div class="label-text">结果:</div>
                        <el-input 
                            v-model="generatedResult" 
                            readonly 
                            type="textarea" 
                            :rows="3"
                            resize="none"
                            placeholder="生成的正则将显示在这里..."
                        />
                    </div>
                </div>
            </el-tab-pane>

            <el-tab-pane label="转义工具" name="escape">
                <div class="content-area">
                    <div class="mb-4">
                        <div class="label-text">待转义文本:</div>
                        <el-input 
                            v-model="escapeInput" 
                            type="textarea" 
                            :rows="6" 
                            placeholder="在此输入需要转义的原始文本..."
                        />
                    </div>
                    
                    <el-button type="primary" @click="escape" size="large" class="action-btn">执行转义</el-button>
                    
                    <div class="mt-4">
                        <div class="label-text">转义结果:</div>
                        <el-input 
                            v-model="escapeResult" 
                            readonly 
                            type="textarea" 
                            :rows="6" 
                            placeholder="转义后的结果..."
                        />
                    </div>
                </div>
            </el-tab-pane>
        </el-tabs>
    </div>
</template>

<style scoped>
.page-container {
    padding: 20px 0;
    height: 100%;
}

.custom-tabs :deep(.el-tabs__item) {
    font-size: 16px;
    height: 50px;
    line-height: 50px;
}

.content-area {
    background: var(--panel-bg);
    padding: 24px;
    border-radius: 8px;
    border: 1px solid var(--border-color);
}

.control-panel {
    display: flex;
    flex-direction: column;
    gap: 20px;
    margin-bottom: 24px;
}

.checkbox-group {
    display: flex;
    gap: 16px;
}

.input-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.action-btn {
    width: 200px;
    font-weight: bold;
}

.result-area, .mb-4, .mt-4 {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.mb-4 { margin-bottom: 20px; }
.mt-4 { margin-top: 20px; }

.label-text {
    font-size: 14px;
    color: var(--text-color);
    font-weight: 600;
    margin-bottom: 4px;
}
</style>

