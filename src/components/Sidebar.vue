<script setup>
import { ref, defineEmits, onMounted } from 'vue'

const props = defineProps({
  currentPage: String
})

const emit = defineEmits(['change-page'])

const menuItems = [
  { id: 'decoder', label: '编码解码', icon: 'M12 4V20M4 12H20' }, 
  { id: 'formatter', label: '格式化', icon: 'M4 6h16M4 12h16M4 18h16' },
  { id: 'regex', label: '正则工具', icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4' },
  { id: 'settings', label: '设置', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' }
]

const isDark = ref(true)

const toggleTheme = () => {
    isDark.value = !isDark.value
    const html = document.documentElement
    if (isDark.value) {
        html.setAttribute('data-theme', 'dark')
        html.classList.add('dark')
    } else {
        html.setAttribute('data-theme', 'light')
        html.classList.remove('dark')
    }
}

onMounted(() => {
    // Initialize theme
    const html = document.documentElement
    html.setAttribute('data-theme', 'dark')
    html.classList.add('dark')
})

const selectPage = (id) => {
  emit('change-page', id)
}

onMounted(() => {
    // Check system preference or saved state (omitted for simplicity, default dark)
})
</script>

<template>
  <div class="sidebar">
    <div class="logo-area lighting-effect">
      <h2>奇怪小工具QAQ</h2>
    </div>
    <nav>
      <div 
        v-for="(item, index) in menuItems" 
        :key="item.id"
        class="menu-item"
        :class="{ active: currentPage === item.id }"
        :style="{ animationDelay: `${index * 0.1}s` }"
        @click="selectPage(item.id)"
      >
        <svg class="icon" viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2">
            <path :d="item.icon" />
        </svg>
        <span>{{ item.label }}</span>
      </div>
    </nav>

    <div class="footer-actions">
        <button class="theme-toggle" @click="toggleTheme" title="Switch Theme">
            {{ isDark ? '🌙' : '☀️' }}
        </button>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  width: 260px;
  background-color: var(--panel-bg);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: background-color 0.3s, border-color 0.3s;
}

.logo-area {
  padding: 24px;
  border-bottom: 1px solid var(--border-color);
}

.logo-area h2 {
  margin: 0;
  font-size: 18px;
  color: var(--accent-color);
  font-weight: 600;
  letter-spacing: 0.5px;
}

nav {
  flex: 1;
  padding: 16px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  cursor: pointer;
  transition: all 0.2s;
  color: #9CA3AF;
  font-weight: 500;
  
  /* Staggered Animation */
  opacity: 0;
  animation: slideIn 0.5s ease forwards;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

.menu-item:hover {
  background-color: rgba(255, 255, 255, 0.05); /* Will adjust for light mode via vars if needed, but simple opacity works */
  color: var(--text-color);
  padding-left: 28px; /* Flow effect */
}

/* Light mode hover fix */
[data-theme="light"] .menu-item:hover {
    background-color: rgba(0, 0, 0, 0.05);
}

.menu-item.active {
  background-color: rgba(216, 125, 255, 0.1); 
  color: var(--accent-color);
  border-right: 3px solid var(--accent-color);
}

/* Light mode active override */
:global([data-theme="light"]) .menu-item.active {
    background-color: rgba(52, 152, 219, 0.1);
}

.icon {
    width: 20px;
    height: 20px;
    margin-right: 12px;
}

.footer-actions {
    padding: 16px;
    border-top: 1px solid var(--border-color);
    display: flex;
    justify-content: flex-end;
}

.theme-toggle {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-color);
    width: 32px;
    height: 32px;
    border-radius: 4px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.theme-toggle:hover {
    border-color: var(--accent-color);
    color: var(--accent-color);
}
</style>
