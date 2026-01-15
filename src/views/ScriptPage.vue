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

// Theme & Wallpaper State
const terminalBgImage = ref('')
const terminalBgOpacity = ref(0.3)
const terminalStyle = ref({})

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

// Run Dialog State
const runDialogVisible = ref(false)
const runningScriptInfo = ref(null)
const scriptInputs = ref('')
const scriptParams = ref([])
const loadingScriptContent = ref(false)

// --- API Base ---
const API_BASE = 'http://127.0.0.1:3335'
const WS_BASE = 'ws://127.0.0.1:3336'

// --- Terminal Themes ---
const darkTheme = {
    background: 'transparent', // Important for wallpaper visibility
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
}

const lightTheme = {
    background: 'transparent', // Important for wallpaper visibility
    foreground: '#2c3e50',
    cursor: '#2c3e50',
    cursorAccent: '#ffffff',
    selection: 'rgba(44, 62, 80, 0.2)',
    black: '#000000',
    red: '#e74c3c',
    green: '#27ae60',
    yellow: '#f1c40f',
    blue: '#2980b9',
    magenta: '#8e44ad',
    cyan: '#16a085',
    white: '#ecf0f1',
    brightBlack: '#7f8c8d',
    brightRed: '#c0392b',
    brightGreen: '#2ecc71',
    brightYellow: '#f39c12',
    brightBlue: '#3498db',
    brightMagenta: '#9b59b6',
    brightCyan: '#1abc9c',
    brightWhite: '#ffffff'
}

const getPreferredTheme = () => {
    const isDark = document.documentElement.classList.contains('dark') || 
                   document.documentElement.getAttribute('data-theme') === 'dark'
    return isDark ? darkTheme : lightTheme
}

// --- Terminal Functions ---
const initTerminal = () => {
    if (terminal) return
    
    terminal = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: "'JetBrains Mono', 'Consolas', 'Courier New', monospace",
        theme: getPreferredTheme(),
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

const runScript = async (script) => {
    if (!websocket || !isConnected.value) {
        ElMessage.warning('终端未连接，正在重连...')
        reconnectTerminal()
        return
    }
    
    // 显示运行对话框
    runningScriptInfo.value = script
    scriptInputs.value = ''
    scriptParams.value = []
    runDialogVisible.value = true
    loadingScriptContent.value = true
    
    try {
        // 获取脚本内容以分析参数
        const res = await axios.get(`${API_BASE}/api/scripts/${script.id}`)
        const content = res.data.script.content
        
        // 解析 input() 调用
        // 匹配 input("prompt") 或 input('prompt')
        const inputRegex = /input\s*\(\s*['"](.*?)['"]\s*\)/g
        let match
        const params = []
        while ((match = inputRegex.exec(content)) !== null) {
            params.push({
                label: match[1] || `参数 ${params.length + 1}`,
                value: ''
            })
        }
        
        scriptParams.value = params
    } catch (e) {
        console.error('Failed to analyze script inputs:', e)
        ElMessage.warning('无法自动分析脚本参数，请手动输入')
    } finally {
        loadingScriptContent.value = false
    }
}

const executeScript = () => {
    if (!runningScriptInfo.value) return
    
    const script = runningScriptInfo.value
    
    // 聚焦终端
    if (terminal) {
        terminal.focus()
    }
    terminal.write('\r\n\x1b[1;36m▶ 运行: ' + script.name + '\x1b[0m\r\n\r\n')
    
    // 发送运行命令
    currentRunningScript.value = script.id
    const scriptPath = `core/script/user_scripts/${script.id}.py`
    
    // 构造输入内容
    let inputsToSend = ''
    if (scriptParams.value.length > 0) {
        // 如果有动态参数，拼接它们
        inputsToSend = scriptParams.value.map(p => p.value).join('\n')
    } else if (scriptInputs.value.trim()) {
        // 否则使用手动输入框的内容
        inputsToSend = scriptInputs.value.trim()
    }
    
    let cmd
    if (inputsToSend) {
        // 使用 echo 管道传递输入，确保输入及时到达
        // 处理单引号转义
        const escapedInput = inputsToSend.replace(/'/g, "'\\''")
        // 如果有多行输入，echo -e 并使用 \n
        if (inputsToSend.includes('\n')) {
             const multilines = inputsToSend.replace(/\n/g, '\\n')
             cmd = `echo -e '${multilines}' | python ${scriptPath}`
        } else {
             cmd = `echo '${escapedInput}' | python ${scriptPath}`
        }
    } else {
        cmd = `python ${scriptPath}`
    }
    
    websocket.send(`CMD:${cmd}`)
    runDialogVisible.value = false
}

const clearTerminal = () => {
    if (terminal) {
        terminal.clear()
    }
}

// --- Lifecycle ---
let themeObserver = null

const loadWallpaperSettings = () => {
    const bg = localStorage.getItem('terminal_bg_image')
    const opacity = localStorage.getItem('terminal_bg_opacity')
    
    terminalBgImage.value = bg || ''
    terminalBgOpacity.value = opacity !== null ? parseFloat(opacity) : 0.3
    
    // Update CSS variables
    if (bg) {
        document.documentElement.style.setProperty('--terminal-bg-image', `url(${bg})`)
        document.documentElement.style.setProperty('--terminal-opacity', terminalBgOpacity.value)
    } else {
        document.documentElement.style.removeProperty('--terminal-bg-image')
    }
}

onMounted(() => {
    loadScripts()
    initTerminal()
    loadWallpaperSettings()
    window.addEventListener('resize', handleResize)
    
    // Listen for storage changes (settings updates)
    window.addEventListener('storage', loadWallpaperSettings)
    
    // Watch for theme changes
    themeObserver = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && 
                (mutation.attributeName === 'class' || mutation.attributeName === 'data-theme')) {
                if (terminal) {
                    terminal.options.theme = getPreferredTheme()
                }
            }
        })
    })
    
    themeObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['class', 'data-theme']
    })
})

onUnmounted(() => {
    disconnectWebSocket()
    if (terminal) {
        terminal.dispose()
    }
    if (themeObserver) {
        themeObserver.disconnect()
    }
    window.removeEventListener('storage', loadWallpaperSettings)
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
                    <el-tag 
                        :class="['status-tag', isConnected ? 'status-connected' : 'status-disconnected']" 
                        size="small"
                        effect="dark"
                    >
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
        
        <!-- Run Script Dialog -->
        <el-dialog
            v-model="runDialogVisible"
            title="运行脚本"
            width="500px"
            class="run-dialog"
        >
            <div class="run-dialog-content" v-loading="loadingScriptContent">
                <!-- Header Card -->
                <div class="script-header">
                    <div class="header-icon">
                        <el-icon><VideoPlay /></el-icon>
                    </div>
                    <div class="header-text">
                        <div class="header-title">{{ runningScriptInfo?.name }}</div>
                        <div class="header-desc">配置运行参数</div>
                    </div>
                </div>
                
                <!-- Dynamic Inputs -->
                <div v-if="scriptParams.length > 0" class="params-container">
                    <div 
                        v-for="(param, index) in scriptParams" 
                        :key="index" 
                        class="param-item"
                    >
                        <div class="param-label">
                            <el-icon><Key /></el-icon> {{ param.label }}
                        </div>
                        <el-input 
                            v-model="param.value" 
                            :placeholder="'请输入 ' + param.label"
                            type="textarea"
                            :rows="2"
                            style="font-family: 'JetBrains Mono', monospace;"
                        />
                    </div>
                    
                    <el-alert
                        title="参数将自动传递给脚本"
                        type="info"
                        show-icon
                        :closable="false"
                        class="info-alert"
                    />
                </div>
                
                <!-- Fallback Input -->
                <div v-else class="manual-input">
                    <div class="param-item">
                        <div class="param-label">输入参数 (可选)</div>
                        <el-input
                            v-model="scriptInputs"
                            type="textarea"
                            :rows="3"
                            placeholder="脚本未检测到 input() 调用，如果需要输入请在此手动键入...&#10;输入后将自动发送到终端"
                            style="font-family: 'JetBrains Mono', monospace;"
                        />
                    </div>
                    <el-alert
                        title="留空则直接运行，可在终端中交互"
                        type="warning"
                        show-icon
                        :closable="false"
                        class="info-alert"
                    />
                </div>
            </div>
            <template #footer>
                <el-button @click="runDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="executeScript">
                    <el-icon><VideoPlay /></el-icon>
                    运行
                </el-button>
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
    background: var(--terminal-bg, #1e1e1e);
    border-radius: 12px;
    border: 1px solid var(--border-color);
    overflow: hidden;
    min-height: 250px;
    transition: background-color 0.3s;
}

.terminal-header {
    background: var(--terminal-header-bg, #2d2d2d);
    padding: 8px 16px;
    font-size: 12px;
    font-weight: bold;
    color: var(--el-text-color-secondary);
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    transition: background-color 0.3s;
}

:global([data-theme="light"]) .terminal-section {
    --terminal-bg: #ffffff;
    --terminal-header-bg: #f8f9fa;
}

:global(.dark) .terminal-section {
    --terminal-bg: #1e1e1e;
    --terminal-header-bg: #2d2d2d;
}

.terminal-controls {
    display: flex;
    align-items: center;
    gap: 12px;
}

.status-tag {
    border: none !important;
    font-weight: bold !important;
    color: #fff !important;
}

.status-connected {
    background-color: #67c23a !important;
    box-shadow: 0 0 8px rgba(103, 194, 58, 0.6), 0 0 15px rgba(103, 194, 58, 0.4) !important;
    animation: glow-green 2s infinite alternate;
}

.status-disconnected {
    background-color: #f56c6c !important;
    box-shadow: 0 0 8px rgba(245, 108, 108, 0.6), 0 0 15px rgba(245, 108, 108, 0.4) !important;
    animation: glow-red 2s infinite alternate;
}

@keyframes glow-green {
    from { box-shadow: 0 0 4px rgba(103, 194, 58, 0.6), 0 0 8px rgba(103, 194, 58, 0.4); }
    to { box-shadow: 0 0 10px rgba(103, 194, 58, 0.8), 0 0 20px rgba(103, 194, 58, 0.6); }
}

@keyframes glow-red {
    from { box-shadow: 0 0 4px rgba(245, 108, 108, 0.6), 0 0 8px rgba(245, 108, 108, 0.4); }
    to { box-shadow: 0 0 10px rgba(245, 108, 108, 0.8), 0 0 20px rgba(245, 108, 108, 0.6); }
}

.terminal-body {
    flex: 1;
    padding: 8px;
    overflow: hidden;
    position: relative;
    z-index: 1;
}

/* Background Image Overlay */
.terminal-body::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: var(--terminal-bg-image, none);
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    opacity: var(--terminal-opacity, 0.3);
    z-index: -1;
    pointer-events: none;
    transition: opacity 0.3s ease;
}

/* Ensure xterm background is transparent so image shows through */
.terminal-body :deep(.xterm),
.terminal-body :deep(.xterm-viewport) {
    background-color: transparent !important;
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

/* Run Dialog Styles */
/* Run Dialog Styles */
.run-dialog-content {
    padding: 4px 0;
}

.script-header {
    background: var(--el-fill-color-light);
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    border: 1px solid var(--border-color);
}

.header-icon {
    width: 40px;
    height: 40px;
    background: var(--el-color-primary-light-9);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: var(--el-color-primary);
}

.header-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
}

.header-desc {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: 2px;
}

.video-play-icon {
    font-size: 24px;
    color: var(--el-color-primary);
}

.params-container, .manual-input {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.param-item {
    background: var(--el-bg-color-overlay);
    padding: 12px;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    transition: all 0.3s;
}

.param-item:focus-within {
    border-color: var(--el-color-primary);
    box-shadow: 0 0 0 2px var(--el-color-primary-light-8);
}

.param-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-bottom: 8px;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
}

.info-alert {
    margin-top: 8px;
}

:deep(.run-dialog .el-dialog__body) {
    padding-top: 10px;
}
</style>
