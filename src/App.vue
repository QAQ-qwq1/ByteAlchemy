
<script setup>
import { ref } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import DecoderPage from '@/views/DecoderPage.vue'
import FormatterPage from '@/views/FormatterPage.vue'
import RegexPage from '@/views/RegexPage.vue'
import ScriptPage from '@/views/ScriptPage.vue'
import SettingsPage from '@/views/SettingsPage.vue'

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
