<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const sboxNames = ref([])
const selectedName = ref('')
const currentName = ref('')
const currentContent = ref('')
const isStandard = ref(false)
const isExpanded = ref(true)
const isAppearanceExpanded = ref(true)

// Appearance Settings
const terminalWallpaper = ref('')
const terminalOpacity = ref(0.3)
const wallpaperPreview = ref('')

// Parse currentContent into 16x16 grid
const sboxGrid = computed(() => {
    try {
        let clean = currentContent.value.replace(/[\[\]\s]/g, '')
        if (clean.includes(',')) {
            // JSON format
            return currentContent.value.replace(/[\[\]]/g, '').split(',').map(v => v.trim()).filter(v => v !== '')
        } else {
            // Hex stream
            let bytes = []
            for (let i = 0; i < clean.length; i += 2) {
                bytes.push(clean.substring(i, i + 2))
            }
            return bytes
        }
    } catch (e) { return [] }
})

const loadSboxNames = async (retries = 5) => {
    try {
        const response = await axios.get('http://127.0.0.1:3335/api/sbox/names')
        sboxNames.value = response.data.names
        if (sboxNames.value.length > 0 && !selectedName.value) {
            selectSbox(sboxNames.value[0])
        }
    } catch (error) { 
        console.error("Load SBox Names failed, retrying...", error)
        if (retries > 0) {
            setTimeout(() => loadSboxNames(retries - 1), 500)
        }
    }
}

const selectSbox = async (name) => {
    selectedName.value = name
    try {
        const response = await axios.get(`http://127.0.0.1:3335/api/sbox/get/${encodeURIComponent(name)}`)
        currentName.value = response.data.name
        currentContent.value = response.data.content
        isStandard.value = response.data.is_standard
    } catch (error) {
        ElMessage.error("Failed to load S-box")
    }
}

const newSbox = () => {
    selectedName.value = ''
    currentName.value = 'New S-Box'
    currentContent.value = ''
    isStandard.value = false
}

const cloneSbox = () => {
    const originalName = currentName.value
    selectedName.value = ''
    currentName.value = originalName + '_Copy'
    isStandard.value = false
    ElMessage.success("已克隆配置")
}

const saveSbox = async () => {
    if (!currentName.value) return ElMessage.warning("名称不能为空")
    try {
        await axios.post('http://127.0.0.1:3335/api/sbox/save', {
            name: currentName.value,
            content: currentContent.value
        })
        ElMessage.success("保存成功")
        await loadSboxNames()
        selectSbox(currentName.value)
    } catch (error) {
        ElMessage.error("保存失败: " + (error.response?.data?.detail || error.message))
    }
}

const deleteSbox = async () => {
    if (isStandard.value) return
    
    try {
        await ElMessageBox.confirm(`确定要删除 ${selectedName.value} 吗?`, '警告', {
            confirmButtonText: '确定删除',
            cancelButtonText: '取消',
            type: 'warning'
        })
        
        await axios.delete(`http://127.0.0.1:3335/api/sbox/delete/${encodeURIComponent(selectedName.value)}`)
        ElMessage.success("删除成功")
        await loadSboxNames()
        if (sboxNames.value.length > 0) selectSbox(sboxNames.value[0])
    } catch (error) {
        if (error !== 'cancel') {
             ElMessage.error("删除失败")
        }
    }
}

// --- Appearance Functions ---
const handleWallpaperUpload = (file) => {
    const reader = new FileReader()
    reader.onload = (e) => {
        const result = e.target.result
        // Basic size check (5MB limit)
        if (result.length > 5 * 1024 * 1024 * 1.37) { // Base64 is ~37% larger
             ElMessage.error('图片大小不能超过 5MB')
             return
        }
        terminalWallpaper.value = result
        wallpaperPreview.value = result
        saveAppearanceSettings()
    }
    reader.readAsDataURL(file.raw)
    return false
}

const removeWallpaper = () => {
    terminalWallpaper.value = ''
    wallpaperPreview.value = ''
    saveAppearanceSettings()
}

const saveAppearanceSettings = () => {
    try {
        localStorage.setItem('terminal_bg_image', terminalWallpaper.value)
        localStorage.setItem('terminal_bg_opacity', terminalOpacity.value)
        // Dispatch event for other tabs/components
        window.dispatchEvent(new Event('storage'))
        ElMessage.success('外观设置已保存')
    } catch (e) {
        console.error("Save settings failed:", e)
        if (e.name === 'QuotaExceededError') {
             ElMessage.error('保存失败：图片太大超过了存储限制，请使用更小的图片')
        } else {
             ElMessage.error('保存设置失败')
        }
    }
}

const loadAppearanceSettings = () => {
    const bg = localStorage.getItem('terminal_bg_image')
    const opacity = localStorage.getItem('terminal_bg_opacity')
    
    if (bg) {
        terminalWallpaper.value = bg
        wallpaperPreview.value = bg
    }
    
    if (opacity !== null) {
        terminalOpacity.value = parseFloat(opacity)
    }
}

onMounted(() => {
    loadSboxNames()
    loadAppearanceSettings()
})
</script>

<template>
    <div class="page-container">
        <h1>设置</h1>
        
        <el-card class="section-card" :body-style="{ padding: '0px' }">
            <template #header>
                <div class="section-header" @click="isExpanded = !isExpanded">
                    <div class="header-left">
                        <h2>配置 S盒 (S-Box Configuration)</h2>
                        <el-tag v-if="isStandard" type="success" size="small" effect="dark" round>标准 (Static)</el-tag>
                        <el-tag v-else type="primary" size="small" effect="dark" round>自定义 (Custom)</el-tag>
                    </div>
                    <el-icon class="expand-icon" :style="{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }">
                         <ArrowDown />
                    </el-icon>
                </div>
            </template>

            <div class="sbox-editor-wrapper" :class="{ collapsed: !isExpanded }">
                <div class="sbox-editor">
                    <!-- Sidebar -->
                    <div class="side-list">
                        <div class="list-container">
                            <div 
                                v-for="name in sboxNames" 
                                :key="name" 
                                class="list-item"
                                :class="{ active: selectedName === name, is_standard: name.startsWith('Standard') }"
                                @click="selectSbox(name)"
                            >
                                <span class="dot"></span>
                                {{ name }}
                            </div>
                        </div>
                        <el-button class="add-btn" @click="newSbox" plain type="primary" size="small" style="width: 100%; margin-top: 10px;">
                            <el-icon><Plus /></el-icon> 新建 S盒
                        </el-button>
                    </div>

                    <!-- Main Panel -->
                    <div class="editor-main">
                        <div class="form-header">
                            <div class="form-group name-group">
                                <span class="input-label">配置名称:</span>
                                <el-input v-model="currentName" :readonly="isStandard" placeholder="输入S盒名称">
                                    <template #append v-if="!isStandard">
                                        <el-button @click="saveSbox">保存</el-button>
                                    </template>
                                </el-input>
                            </div>
                             <el-button @click="cloneSbox" size="small">
                                <el-icon><CopyDocument /></el-icon> 克隆
                            </el-button>
                        </div>

                        <!-- Visualization Grid -->
                        <div class="visualization">
                            <span class="input-label">矩阵视图 (16x16 Grid):</span>
                            <div class="grid-container">
                                <div v-for="(val, idx) in sboxGrid" :key="idx" class="grid-cell" :title="`Index: ${idx}`">
                                    {{ val.length === 2 ? val : ('0' + val).slice(-2) }}
                                </div>
                            </div>
                        </div>

                        <div class="form-group flex-grow">
                             <span class="input-label">原始数据 (Hex Stream):</span>
                             <el-input 
                                v-model="currentContent" 
                                :readonly="isStandard" 
                                type="textarea" 
                                :rows="4"
                                resize="none"
                                placeholder="例如: d690e9fe..."
                             />
                        </div>

                        <div class="actions">
                             <el-alert
                                v-if="isStandard"
                                title="标准S盒不可直接修改，请克隆后编辑"
                                type="warning"
                                show-icon
                                :closable="false"
                                style="width: 100%"
                            />
                            <div v-else style="display: flex; gap: 10px; width: 100%;">
                                <el-button type="primary" @click="saveSbox" style="flex: 1">保存配置</el-button>
                                <el-button type="danger" plain @click="deleteSbox">删除此配置</el-button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </el-card>



        <el-card class="section-card" :body-style="{ padding: '0px' }">
            <template #header>
                <div class="section-header" @click="isAppearanceExpanded = !isAppearanceExpanded">
                    <div class="header-left">
                        <h2>终端外观 (Terminal Appearance)</h2>
                    </div>
                    <el-icon class="expand-icon" :style="{ transform: isAppearanceExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }">
                         <ArrowDown />
                    </el-icon>
                </div>
            </template>

            <div class="sbox-editor-wrapper" :class="{ collapsed: !isAppearanceExpanded }">
                <div class="appearance-editor">
                    <div class="setting-item">
                        <div class="setting-label">背景图片 (Wallpaper)</div>
                        <div class="wallpaper-upload">
                             <el-upload
                                class="avatar-uploader"
                                :show-file-list="false"
                                :auto-upload="false"
                                :on-change="handleWallpaperUpload"
                                accept="image/*"
                            >
                                <img v-if="wallpaperPreview" :src="wallpaperPreview" class="avatar" />
                                <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
                            </el-upload>
                            <div class="upload-hint">
                                <p>点击上传图片 (最大 5MB)</p>
                                <el-button v-if="wallpaperPreview" type="danger" link @click.stop="removeWallpaper">清除壁纸</el-button>
                            </div>
                        </div>
                    </div>

                    <div class="setting-item">
                        <div class="setting-label">
                            背景不透明度 (Opacity)
                            <span class="value-text">{{ Math.round(terminalOpacity * 100) }}%</span>
                        </div>
                        <div class="slider-container">
                             <el-slider 
                                v-model="terminalOpacity" 
                                :min="0" 
                                :max="1" 
                                :step="0.05" 
                                show-input
                                @change="saveAppearanceSettings"
                             />
                        </div>
                    </div>
                </div>
            </div>
        </el-card>

        <div class="about-section">
            <el-card class="about-card">
                <template #header>
                    <div class="about-header">
                         <h2>关于 Descrypt Pro</h2>
                    </div>
                </template>
                <p>由于不会写解密脚本于是用AI搓了一个奇怪小玩意。受 CyberChef 启发，基于 Electron 和 FastAPI 构建。</p>
                <el-descriptions :column="3" border>
                    <el-descriptions-item label="版本">0.0.1</el-descriptions-item>
                    <el-descriptions-item label="驱动">QAQ</el-descriptions-item>
                    <el-descriptions-item label="状态">
                         <el-tag type="success">运行中</el-tag>
                    </el-descriptions-item>
                </el-descriptions>
            </el-card>
        </div>
    </div>
</template>

<style scoped>
.page-container {
    padding: 24px 0;
}

h1 {
    margin-bottom: 24px;
    font-size: 24px;
    color: var(--text-color);
}

.section-card {
    background-color: var(--panel-bg);
    border-color: var(--border-color);
    margin-bottom: 24px;
    transition: all 0.3s ease;
}

.section-card:hover {
    box-shadow: 0 0 15px var(--accent-color);
    border-color: var(--accent-color);
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.section-header h2 {
    margin: 0;
    font-size: 16px;
    color: var(--text-color);
}

.expand-icon {
    font-size: 16px;
    color: var(--text-color);
    transition: transform 0.3s;
}

.sbox-editor-wrapper {
    overflow: hidden;
    max-height: 800px;
    transition: max-height 0.4s cubic-bezier(0.645, 0.045, 0.355, 1);
}

.sbox-editor-wrapper.collapsed {
    max-height: 0;
}

.sbox-editor {
    display: flex;
    height: 600px;
}

.side-list {
    width: 220px;
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    padding: 12px;
    background: var(--input-bg);
}

.list-container {
    flex: 1;
    overflow-y: auto;
}

.list-item {
    padding: 10px 12px;
    border-radius: 4px;
    cursor: pointer;
    margin-bottom: 4px;
    color: var(--text-color);
    transition: all 0.2s;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.list-item .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #666;
}

.list-item.is_standard .dot {
    background: var(--el-color-success);
}

.list-item:hover {
    background: var(--hover-bg);
}

.list-item.active {
    background: var(--el-color-primary-light-9);
    color: var(--el-color-primary);
}

.list-item.active .dot {
    background: var(--el-color-primary);
}

:global(.dark) .list-item.active {
    background: var(--el-color-primary-dark-2);
}

.editor-main {
    flex: 1;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.form-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 20px;
}

.name-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.input-label {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    font-weight: bold;
}

.visualization {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1;
    min-height: 0;
}

.grid-container {
    display: grid;
    grid-template-columns: repeat(16, 1fr);
    gap: 2px;
    background: var(--el-fill-color-dark);
    padding: 4px;
    border-radius: 4px;
    border: 1px solid var(--border-color);
    overflow-y: auto;
    max-height: 300px;
}

:global(.dark) .grid-container {
    background: #151217; /* Darker shade of bg #1C191F */
    border-color: var(--border-color);
}

.grid-cell {
    aspect-ratio: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    background: var(--el-bg-color);
    color: var(--text-color);
    cursor: default;
}

:global(.dark) .grid-cell {
    background: #2B2530; /* panel-bg */
    color: var(--text-color);
}

.grid-cell:hover {
    background: var(--el-color-primary);
    color: #fff;
}

.form-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.flex-grow {
    flex: 1;
}

.about-card {
    background: var(--panel-bg);
    border-color: var(--border-color);
}

.appearance-editor {
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 32px;
}

.setting-item {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.setting-label {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-color);
    display: flex;
    justify-content: space-between;
}

.value-text {
    color: var(--el-color-primary);
}

.wallpaper-upload {
    display: flex;
    gap: 20px;
    align-items: center;
}

.avatar-uploader {
    border: 1px dashed var(--border-color);
    border-radius: 6px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: var(--el-transition-duration-fast);
    width: 120px;
    height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.avatar-uploader:hover {
    border-color: var(--el-color-primary);
}

.avatar-uploader-icon {
    font-size: 28px;
    color: #8c939d;
    width: 120px;
    height: 120px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
}

.avatar {
    width: 120px;
    height: 120px;
    display: block;
    object-fit: cover;
}

.upload-hint {
    font-size: 12px;
    color: var(--el-text-color-secondary);
}

.slider-container {
    padding: 0 12px;
}
</style>

