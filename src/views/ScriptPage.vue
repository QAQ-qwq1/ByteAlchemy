<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import 'xterm/css/xterm.css'

// --- State ---
const scripts = ref([])
const loading = ref(false)
const currentRunningScript = ref(null)

// Terminal State
const terminalRef = ref(null)
const isConnected = ref(false)
let terminal = null
let fitAddon = null
let websocket = null

// Upload Dialog State
const uploadDialogVisible = ref(false)
const newScript = ref({
    name: '',
    description: '',
    content: ''
})

// --- API Base ---
const API_BASE = 'http://127.0.0.1:3335'
const WS_BASE = 'ws://127.0.0.1:3336'

// --- Terminal Functions ---
const initTerminal = () => {
    if (terminal) return
    
    terminal = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: "'JetBrains Mono', 'Consolas', 'Courier New', monospace",
        theme: {
            background: '#1e1e1e',
            foreground: '#4af626',
            cursor: '#4af626',
            cursorAccent: '#1e1e1e',
            selection: 'rgba(74, 246, 38, 0.3)',
            black: '#1e1e1e',
            red: '#ff5555',
            green: '#4af626',
            yellow: '#f1fa8c',
            blue: '#6272a4',
            magenta: '#ff79c6',
            cyan: '#8be9fd',
            white: '#f8f8f2',
            brightBlack: '#6272a4',
            brightRed: '#ff6e6e',
            brightGreen: '#69ff94',
            brightYellow: '#ffffa5',
            brightBlue: '#d6acff',
            brightMagenta: '#ff92df',
            brightCyan: '#a4ffff',
            brightWhite: '#ffffff'
        },
        allowTransparency: true,
        scrollback: 1000
    })
    
    fitAddon = new FitAddon()
    terminal.loadAddon(fitAddon)
    terminal.loadAddon(new WebLinksAddon())
    
    nextTick(() => {
        if (terminalRef.value) {
            terminal.open(terminalRef.value)
            fitAddon.fit()
            
            // Handle terminal input
            terminal.onData((data) => {
                if (websocket && isConnected.value) {
                    websocket.send(data)
                }
            })
            
            // Connect to WebSocket
            connectWebSocket()
        }
    })
}

const connectWebSocket = () => {
    if (websocket && isConnected.value) return
    
    try {
        const rows = terminal.rows
        const cols = terminal.cols
        
        websocket = new WebSocket(WS_BASE)
        
        websocket.onopen = () => {
            isConnected.value = true
            websocket.send(`INIT:${rows}:${cols}`)
            ElMessage.success('终端已连接')
        }
        
        websocket.onmessage = (event) => {
            terminal.write(event.data)
        }
        
        websocket.onclose = () => {
            isConnected.value = false
            terminal.write('\r\n\x1b[1;31m[连接已断开]\x1b[0m\r\n')
        }
        
        websocket.onerror = (error) => {
            console.error('WebSocket error:', error)
            isConnected.value = false
        }
    } catch (error) {
        console.error('Failed to connect WebSocket:', error)
        ElMessage.error('终端连接失败')
    }
}

const disconnectWebSocket = () => {
    if (websocket) {
        websocket.close()
        websocket = null
        isConnected.value = false
    }
}

const reconnectTerminal = () => {
    disconnectWebSocket()
    setTimeout(() => {
        connectWebSocket()
    }, 500)
}

const handleResize = () => {
    if (fitAddon && terminal) {
        fitAddon.fit()
        if (websocket && isConnected.value) {
            websocket.send(`RESIZE:${terminal.rows}:${terminal.cols}`)
        }
    }
}

// --- Script Functions ---
const loadScripts = async () => {
    loading.value = true
    try {
        const response = await axios.get(`${API_BASE}/api/scripts`)
        scripts.value = response.data.scripts
    } catch (error) {
        console.error('Failed to load scripts:', error)
        ElMessage.error('加载脚本列表失败')
    } finally {
        loading.value = false
    }
}

const openUploadDialog = () => {
    newScript.value = { name: '', description: '', content: '' }
    uploadDialogVisible.value = true
}

const handleFileUpload = (file) => {
    const reader = new FileReader()
    reader.onload = (e) => {
        newScript.value.content = e.target.result
        if (!newScript.value.name) {
            newScript.value.name = file.name.replace(/\.py$/, '')
        }
    }
    reader.readAsText(file.raw)
    return false
}

const submitScript = async () => {
    if (!newScript.value.name || !newScript.value.content) {
        ElMessage.warning('请输入脚本名称和内容')
        return
    }
    
    try {
        await axios.post(`${API_BASE}/api/scripts`, newScript.value)
        ElMessage.success('脚本上传成功')
        uploadDialogVisible.value = false
        loadScripts()
    } catch (error) {
        console.error('Failed to upload script:', error)
        ElMessage.error('上传脚本失败: ' + (error.response?.data?.detail || error.message))
    }
}

const deleteScript = async (script) => {
    try {
        await ElMessageBox.confirm(
            `确定要删除脚本 "${script.name}" 吗？`,
            '确认删除',
            { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
        )
        
        await axios.delete(`${API_BASE}/api/scripts/${script.id}`)
        ElMessage.success('脚本已删除')
        loadScripts()
    } catch (error) {
        if (error !== 'cancel') {
            ElMessage.error('删除失败')
        }
    }
}

const runScript = (script) => {
    if (!websocket || !isConnected.value) {
        ElMessage.warning('终端未连接，正在重连...')
        reconnectTerminal()
        return
    }
    
    // 获取脚本完整路径并在终端中执行
    currentRunningScript.value = script.id
    
    // 使用相对路径执行脚本 (core/script/user_scripts/)
    // 在终端的当前工作目录下执行
    const cmd = `python core/script/user_scripts/${script.id}.py`
    websocket.send(`CMD:${cmd}`)
    
    setTimeout(() => {
        currentRunningScript.value = null
    }, 1000)
}

const clearTerminal = () => {
    if (terminal) {
        terminal.clear()
    }
}

// --- Lifecycle ---
onMounted(() => {
    loadScripts()
    initTerminal()
    window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
    disconnectWebSocket()
    if (terminal) {
        terminal.dispose()
    }
    window.removeEventListener('resize', handleResize)
})
</script>

<template>
    <div class="script-container">
        <!-- Header Section -->
        <div class="header-section">
            <div class="page-header lighting-effect">
                <h2>📜 脚本库</h2>
                <span class="subtitle">Script Library</span>
            </div>
            <div class="header-actions">
                <el-button type="primary" @click="openUploadDialog" round>
                    <el-icon><Plus /></el-icon>
                    上传脚本
                </el-button>
                <el-button @click="loadScripts" :loading="loading" circle>
                    <el-icon><Refresh /></el-icon>
                </el-button>
            </div>
        </div>
        
        <!-- Scripts Grid -->
        <div class="scripts-section">
            <div v-if="scripts.length === 0 && !loading" class="empty-state">
                <el-icon class="empty-icon"><Document /></el-icon>
                <p>还没有脚本</p>
                <p class="hint">点击上方"上传脚本"按钮添加你的第一个脚本</p>
            </div>
            
            <div class="scripts-grid" v-else>
                <div 
                    v-for="script in scripts" 
                    :key="script.id"
                    class="script-card"
                    :class="{ 'running': currentRunningScript === script.id }"
                >
                    <div class="script-main" @click="runScript(script)">
                        <div class="script-icon">
                            <el-icon v-if="currentRunningScript === script.id" class="is-loading">
                                <Loading />
                            </el-icon>
                            <el-icon v-else><DocumentCopy /></el-icon>
                        </div>
                        <div class="script-info">
                            <div class="script-name">{{ script.name }}</div>
                            <div class="script-desc" v-if="script.description">{{ script.description }}</div>
                        </div>
                    </div>
                    <div class="script-actions">
                        <el-button 
                            link 
                            type="danger" 
                            size="small"
                            @click.stop="deleteScript(script)"
                        >
                            <el-icon><Delete /></el-icon>
                        </el-button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Interactive Terminal Section -->
        <div class="terminal-section">
            <div class="terminal-header">
                <span>🖥️ 交互式终端 (Interactive Terminal)</span>
                <div class="terminal-controls">
                    <el-tag :type="isConnected ? 'success' : 'danger'" size="small">
                        {{ isConnected ? '已连接' : '未连接' }}
                    </el-tag>
                    <el-button link size="small" @click="reconnectTerminal">
                        <el-icon><Refresh /></el-icon> 重连
                    </el-button>
                    <el-button link size="small" @click="clearTerminal">
                        <el-icon><Delete /></el-icon> 清屏
                    </el-button>
                </div>
            </div>
            <div class="terminal-body" ref="terminalRef"></div>
        </div>
        
        <!-- Upload Dialog -->
        <el-dialog
            v-model="uploadDialogVisible"
            title="上传脚本"
            width="600px"
            class="upload-dialog"
        >
            <el-form label-position="top">
                <el-form-item label="脚本名称">
                    <el-input v-model="newScript.name" placeholder="例如：数据处理脚本" />
                </el-form-item>
                
                <el-form-item label="描述 (可选)">
                    <el-input v-model="newScript.description" placeholder="脚本功能描述..." />
                </el-form-item>
                
                <el-form-item label="脚本内容">
                    <el-upload
                        drag
                        :auto-upload="false"
                        :on-change="handleFileUpload"
                        accept=".py"
                        :show-file-list="false"
                        style="width: 100%; margin-bottom: 12px;"
                    >
                        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                        <div class="el-upload__text">
                            拖拽 .py 文件到此处，或 <em>点击上传</em>
                        </div>
                    </el-upload>
                    
                    <el-input
                        v-model="newScript.content"
                        type="textarea"
                        :rows="10"
                        placeholder="# 在此粘贴或编写 Python 代码..."
                        style="font-family: 'JetBrains Mono', monospace;"
                    />
                </el-form-item>
            </el-form>
            
            <template #footer>
                <el-button @click="uploadDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="submitScript">上传</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<style scoped>
.script-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 16px;
    gap: 16px;
    background: var(--bg-color);
    color: var(--text-color);
    overflow: hidden;
}

/* Header */
.header-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.page-header {
    display: flex;
    align-items: baseline;
    gap: 12px;
}

.page-header h2 {
    margin: 0;
    font-size: 20px;
    color: var(--accent-color);
}

.subtitle {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    text-transform: uppercase;
    letter-spacing: 1px;
}

.header-actions {
    display: flex;
    gap: 8px;
}

/* Scripts Section */
.scripts-section {
    flex: 0 0 auto;
    min-height: 120px;
    max-height: 35%;
    background: var(--panel-bg);
    border-radius: 12px;
    border: 1px solid var(--border-color);
    padding: 16px;
    overflow-y: auto;
}

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--el-text-color-secondary);
}

.empty-icon {
    font-size: 48px;
    margin-bottom: 12px;
}

.empty-state .hint {
    font-size: 12px;
    margin-top: 4px;
}

.scripts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 12px;
}

.script-card {
    background: var(--item-bg);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    transition: all 0.2s ease;
}

.script-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    border-color: var(--el-color-primary);
}

.script-card.running {
    border-color: var(--el-color-success);
    background: rgba(103, 194, 58, 0.1);
}

.script-main {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 0;
}

.script-icon {
    font-size: 24px;
    color: var(--el-color-primary);
    flex-shrink: 0;
}

.script-info {
    min-width: 0;
}

.script-name {
    font-weight: 600;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.script-desc {
    font-size: 11px;
    color: var(--el-text-color-secondary);
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.script-actions {
    flex-shrink: 0;
    opacity: 0;
    transition: opacity 0.2s;
}

.script-card:hover .script-actions {
    opacity: 1;
}

/* Terminal Section */
.terminal-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #1e1e1e;
    border-radius: 12px;
    border: 1px solid var(--border-color);
    overflow: hidden;
    min-height: 250px;
}

.terminal-header {
    background: #2d2d2d;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: bold;
    color: #ccc;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #3c3c3c;
}

.terminal-controls {
    display: flex;
    align-items: center;
    gap: 12px;
}

.terminal-body {
    flex: 1;
    padding: 8px;
    overflow: hidden;
}

/* Upload Dialog Styles */
:deep(.upload-dialog .el-dialog__body) {
    padding-top: 8px;
}

/* Fix xterm.js sizing */
.terminal-body :deep(.xterm) {
    height: 100%;
}

.terminal-body :deep(.xterm-viewport) {
    overflow-y: auto !important;
}
</style>
