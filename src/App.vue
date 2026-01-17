
<script setup>
import { ref, defineAsyncComponent } from 'vue'
import Sidebar from '@/components/Sidebar.vue'

// Lazy load views
const DecoderPage = defineAsyncComponent(() => import('@/views/DecoderPage.vue'))
const FormatterPage = defineAsyncComponent(() => import('@/views/FormatterPage.vue'))
const RegexPage = defineAsyncComponent(() => import('@/views/RegexPage.vue'))
const ScriptPage = defineAsyncComponent(() => import('@/views/ScriptPage.vue'))
const SettingsPage = defineAsyncComponent(() => import('@/views/SettingsPage.vue'))

const currentPage = ref('decoder')

const renderPage = {
    'decoder': DecoderPage,
    'formatter': FormatterPage,
    'regex': RegexPage,
    'script': ScriptPage,
    'settings': SettingsPage
}
</script>

<template>
  <div class="app-container">
    <Sidebar :currentPage="currentPage" @change-page="(id) => currentPage = id" />
    <div class="content-area">
        <component :is="renderPage[currentPage]" />
    </div>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: var(--bg-color);
  color: var(--text-color);
}

.content-area {
    flex: 1;
    padding: 0 32px;
    overflow-y: auto;
}
</style>
