
<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const inputContent = ref('')
const outputContent = ref('')
const selectedMode = ref('xml')

const formatOptions = [
    { value: 'xml', label: 'XML 格式化' },
    { value: 'json', label: 'JSON 格式化' },
    { value: 'python', label: 'Python 格式化' },
    { value: 'html', label: 'HTML 格式化' },
    { value: 'sql', label: 'SQL 格式化' },
    { value: 'css', label: 'CSS 格式化' }
]

const format = async () => {
    try {
        const response = await axios.post('http://127.0.0.1:3335/api/format', {
            type: selectedMode.value,
            data: inputContent.value
        })
        outputContent.value = response.data.result
        ElMessage.success('格式化完成')
    } catch (error) {
        outputContent.value = "Error: " + (error.response?.data?.detail || error.message)
        ElMessage.error('格式化出错')
    }
}
</script>

<template>
    <div class="page-container">
        <div class="toolbar">
            <el-select v-model="selectedMode" placeholder="选择格式" style="width: 200px">
                <el-option
                    v-for="item in formatOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                />
            </el-select>
            
            <el-button type="primary" @click="format">
                <el-icon class="el-icon--left"><MagicStick /></el-icon>
                执行格式化
            </el-button>
        </div>

        <div class="work-area">
            <div class="panel">
                <div class="panel-header">输入 (Raw)</div>
                <el-input
                    v-model="inputContent"
                    type="textarea"
                    resize="none"
                    class="code-editor"
                    placeholder="在此粘贴需要格式化的代码..."
                />
            </div>
            
            <div class="panel">
                <div class="panel-header">输出 (Formatted)</div>
                <el-input
                    v-model="outputContent"
                    readonly
                    type="textarea"
                    resize="none"
                    class="code-editor"
                    placeholder="格式化结果..."
                />
            </div>
        </div>
    </div>
</template>

<style scoped>
.page-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 20px 0;
}

.toolbar {
    display: flex;
    gap: 16px;
    align-items: center;
    margin-bottom: 20px;
}

.work-area {
    display: flex;
    flex: 1;
    gap: 20px;
    min-height: 0;
}

.panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: var(--panel-bg);
    border-radius: 8px;
    border: 1px solid var(--border-color);
    overflow: hidden;
}

.panel-header {
    padding: 12px 16px;
    background: var(--header-bg);
    font-weight: 600;
    color: var(--text-color);
    font-size: 12px;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border-color);
}

.code-editor {
    flex: 1;
    height: 100%;
}

.code-editor :deep(.el-textarea__inner) {
    height: 100%;
    border: none;
    border-radius: 0;
    background: transparent;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 14px;
    box-shadow: none;
    padding: 16px;
    color: var(--text-color);
}
</style>

