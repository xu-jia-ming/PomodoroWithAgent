<template>
  <div class="app-wrapper">
    <div class="app-shell" :class="{ 'android-mode': uiMode === 'android', 'windows-mode': uiMode === 'windows' }">
    <header class="app-header">
      <div class="header-main">
        <div class="header-title">
          <h2>PomodoroTable</h2>
          <p>Focus smarter on Windows and Android</p>
        </div>
        <div class="header-controls">
          <el-segmented v-model="uiMode" :options="uiOptions" size="small" />
          <el-switch
            v-model="darkMode"
            class="theme-switch"
            inline-prompt
            :active-icon="MoonNight"
            :inactive-icon="Sunny"
          />
          <el-popover placement="bottom-end" trigger="click" :width="180">
            <template #reference>
              <el-button circle size="small" :icon="Brush" />
            </template>
            <div class="color-options">
              <button
                v-for="option in themeOptions"
                :key="option.value"
                class="color-option-btn"
                type="button"
                @click="themeKey = option.value"
              >
                <span class="color-dot" :style="{ backgroundColor: option.preview }"></span>
                <span class="color-label">{{ option.label }}</span>
                <el-icon v-if="themeKey === option.value" class="color-check"><Check /></el-icon>
              </button>
            </div>
          </el-popover>
        </div>
      </div>
    </header>

    <main class="app-content">
      <TodosView v-if="activeTab === 'todos'" :ui-mode="uiMode" />
      <StatsView v-else-if="activeTab === 'stats'" />
      <ProfileView v-else-if="activeTab === 'profile'" />
      <ReflectionView v-else />
    </main>

    <footer class="tab-footer">
      <el-button text class="nav-btn" :type="activeTab === 'todos' ? 'primary' : ''" @click="activeTab = 'todos'">待办</el-button>
      <el-button text class="nav-btn" :type="activeTab === 'stats' ? 'primary' : ''" @click="activeTab = 'stats'">统计数据</el-button>
      <el-button text class="nav-btn" :type="activeTab === 'reflection' ? 'primary' : ''" @click="activeTab = 'reflection'">心流</el-button>
      <el-button text class="nav-btn" :type="activeTab === 'profile' ? 'primary' : ''" @click="activeTab = 'profile'">我的</el-button>
    </footer>
  </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { Brush, Check, MoonNight, Sunny } from '@element-plus/icons-vue'
import TodosView from './views/TodosView.vue'
import StatsView from './views/StatsView.vue'
import ProfileView from './views/ProfileView.vue'
import ReflectionView from './views/ReflectionView.vue'

const activeTab = ref('todos')
const uiOptions = [
  { label: 'Windows UI', value: 'windows' },
  { label: 'Android UI', value: 'android' }
]
const themeOptions = [
  { label: '雾灰护眼', value: 'calm-gray', preview: '#eef2f7' },
  { label: '浅蓝清爽', value: 'calm-blue', preview: '#eaf2ff' },
  { label: '浅绿自然', value: 'calm-green', preview: '#edf7f1' },
  { label: '暖白柔和', value: 'warm-cream', preview: '#fff8ef' }
]

const lightThemes = {
  'calm-gray': {
    appBg: '#eef2f7',
    surface: '#ffffff',
    surfaceSoft: '#f6f8fb',
    text: '#1f2d3d',
    textMuted: '#5f6b7a',
    border: '#dbe2ea',
    primary: '#4a7cff',
    focusBg: '#1f2a37',
    focusText: '#f8fafc',
    focusBadgeBg: '#111827',
    focusBadgeText: '#93c5fd',
    focusControlBg: '#374151',
    focusControlBorder: '#4b5563',
    focusControlText: '#f9fafb',
    focusPrimary: '#5b8def',
    focusSuccess: '#5fa65f',
    focusExitBg: 'rgba(0, 0, 0, 0.45)',
    focusExitBorder: 'rgba(255, 255, 255, 0.2)'
  },
  'calm-blue': {
    appBg: '#eaf2ff',
    surface: '#ffffff',
    surfaceSoft: '#f3f7ff',
    text: '#1b2a41',
    textMuted: '#4d5f7a',
    border: '#cfdff5',
    primary: '#3f73d8',
    focusBg: '#1c2740',
    focusText: '#f8fbff',
    focusBadgeBg: '#142034',
    focusBadgeText: '#8ec5ff',
    focusControlBg: '#2a3a5c',
    focusControlBorder: '#41598b',
    focusControlText: '#edf4ff',
    focusPrimary: '#5b8def',
    focusSuccess: '#58a87c',
    focusExitBg: 'rgba(20, 32, 52, 0.55)',
    focusExitBorder: 'rgba(255, 255, 255, 0.2)'
  },
  'calm-green': {
    appBg: '#edf7f1',
    surface: '#ffffff',
    surfaceSoft: '#f4fbf7',
    text: '#1f3528',
    textMuted: '#4f6b5a',
    border: '#d2e7da',
    primary: '#3f8f6a',
    focusBg: '#1f3328',
    focusText: '#f6fbf8',
    focusBadgeBg: '#15241c',
    focusBadgeText: '#8fddb4',
    focusControlBg: '#304a3c',
    focusControlBorder: '#476b57',
    focusControlText: '#f2faf5',
    focusPrimary: '#4f9d78',
    focusSuccess: '#67b85e',
    focusExitBg: 'rgba(21, 36, 28, 0.55)',
    focusExitBorder: 'rgba(255, 255, 255, 0.2)'
  },
  'warm-cream': {
    appBg: '#fff8ef',
    surface: '#fffdf9',
    surfaceSoft: '#fff7ed',
    text: '#3b2f24',
    textMuted: '#6d5b49',
    border: '#ebdbc9',
    primary: '#c27a45',
    focusBg: '#342a22',
    focusText: '#fffaf4',
    focusBadgeBg: '#261f19',
    focusBadgeText: '#f8c58a',
    focusControlBg: '#4a3a2e',
    focusControlBorder: '#6b5443',
    focusControlText: '#fff8ef',
    focusPrimary: '#cf8c53',
    focusSuccess: '#8eb364',
    focusExitBg: 'rgba(38, 31, 25, 0.55)',
    focusExitBorder: 'rgba(255, 255, 255, 0.2)'
  }
}

const darkThemes = {
  'calm-gray': {
    appBg: '#131820',
    surface: '#1a2230',
    surfaceSoft: '#222c3d',
    text: '#e6edf6',
    textMuted: '#a5b1c2',
    border: '#2f3b4d',
    primary: '#7ea4ff',
    focusBg: '#0f141d',
    focusText: '#f2f6fc',
    focusBadgeBg: '#1f2a3a',
    focusBadgeText: '#a7c7ff',
    focusControlBg: '#2a3546',
    focusControlBorder: '#3a4a61',
    focusControlText: '#f0f5fb',
    focusPrimary: '#7fa6ff',
    focusSuccess: '#71b88f',
    focusExitBg: 'rgba(12, 18, 28, 0.7)',
    focusExitBorder: 'rgba(166, 182, 204, 0.35)'
  },
  'calm-blue': {
    appBg: '#111a27',
    surface: '#172234',
    surfaceSoft: '#213047',
    text: '#e8f1ff',
    textMuted: '#a9bbd9',
    border: '#2d4260',
    primary: '#82aef8',
    focusBg: '#0d1522',
    focusText: '#eef5ff',
    focusBadgeBg: '#1a2940',
    focusBadgeText: '#9ed0ff',
    focusControlBg: '#253854',
    focusControlBorder: '#3d5a83',
    focusControlText: '#edf4ff',
    focusPrimary: '#84aff8',
    focusSuccess: '#67b397',
    focusExitBg: 'rgba(13, 21, 34, 0.72)',
    focusExitBorder: 'rgba(166, 190, 230, 0.35)'
  },
  'calm-green': {
    appBg: '#121d18',
    surface: '#182520',
    surfaceSoft: '#21342b',
    text: '#e8f5ee',
    textMuted: '#adc6b7',
    border: '#324b3e',
    primary: '#72c39a',
    focusBg: '#101914',
    focusText: '#edf8f2',
    focusBadgeBg: '#1a2b22',
    focusBadgeText: '#9de3bf',
    focusControlBg: '#294137',
    focusControlBorder: '#3e6352',
    focusControlText: '#eef9f3',
    focusPrimary: '#74c79e',
    focusSuccess: '#7ecf6b',
    focusExitBg: 'rgba(16, 25, 20, 0.72)',
    focusExitBorder: 'rgba(170, 206, 186, 0.35)'
  },
  'warm-cream': {
    appBg: '#1d1712',
    surface: '#272018',
    surfaceSoft: '#342a20',
    text: '#f8eee2',
    textMuted: '#cdb9a3',
    border: '#4a3b2d',
    primary: '#e0a772',
    focusBg: '#17110d',
    focusText: '#fff4e8',
    focusBadgeBg: '#2b2118',
    focusBadgeText: '#f3c799',
    focusControlBg: '#3d2f24',
    focusControlBorder: '#5c4736',
    focusControlText: '#fff6ed',
    focusPrimary: '#e3ab75',
    focusSuccess: '#9cc57d',
    focusExitBg: 'rgba(23, 17, 13, 0.72)',
    focusExitBorder: 'rgba(213, 187, 160, 0.35)'
  }
}

const legacyColorThemeMap = {
  '#f5f7fa': 'calm-gray',
  '#ecf5ff': 'calm-blue',
  '#f0f9eb': 'calm-green',
  '#fffdf5': 'warm-cream'
}

const uiMode = ref(localStorage.getItem('ui-mode') || 'windows')
const savedTheme = localStorage.getItem('app-theme')
const legacyColor = localStorage.getItem('app-bg-color')
const themeKey = ref(savedTheme || legacyColorThemeMap[legacyColor] || 'calm-gray')
const darkMode = ref(localStorage.getItem('app-dark-mode') === 'true')

function applyTheme(value, isDark) {
  const palette = isDark ? darkThemes : lightThemes
  const theme = palette[value] || palette['calm-gray']
  document.documentElement.style.colorScheme = isDark ? 'dark' : 'light'
  document.documentElement.style.setProperty('--app-bg-color', theme.appBg)
  document.documentElement.style.setProperty('--app-surface-color', theme.surface)
  document.documentElement.style.setProperty('--app-surface-soft-color', theme.surfaceSoft)
  document.documentElement.style.setProperty('--app-text-color', theme.text)
  document.documentElement.style.setProperty('--app-text-muted-color', theme.textMuted)
  document.documentElement.style.setProperty('--app-border-color', theme.border)
  document.documentElement.style.setProperty('--app-primary-color', theme.primary)

  document.documentElement.style.setProperty('--focus-bg-color', theme.focusBg)
  document.documentElement.style.setProperty('--focus-text-color', theme.focusText)
  document.documentElement.style.setProperty('--focus-badge-bg-color', theme.focusBadgeBg)
  document.documentElement.style.setProperty('--focus-badge-text-color', theme.focusBadgeText)
  document.documentElement.style.setProperty('--focus-control-bg-color', theme.focusControlBg)
  document.documentElement.style.setProperty('--focus-control-border-color', theme.focusControlBorder)
  document.documentElement.style.setProperty('--focus-control-text-color', theme.focusControlText)
  document.documentElement.style.setProperty('--focus-primary-color', theme.focusPrimary)
  document.documentElement.style.setProperty('--focus-success-color', theme.focusSuccess)
  document.documentElement.style.setProperty('--focus-exit-bg-color', theme.focusExitBg)
  document.documentElement.style.setProperty('--focus-exit-border-color', theme.focusExitBorder)

  // Keep Element Plus global surfaces in sync to avoid white patches in dark mode (dialogs, popovers, inputs).
  document.documentElement.style.setProperty('--el-bg-color', theme.surface)
  document.documentElement.style.setProperty('--el-bg-color-page', theme.appBg)
  document.documentElement.style.setProperty('--el-bg-color-overlay', theme.surface)
  document.documentElement.style.setProperty('--el-fill-color', theme.surfaceSoft)
  document.documentElement.style.setProperty('--el-fill-color-light', theme.surfaceSoft)
  document.documentElement.style.setProperty('--el-fill-color-lighter', theme.surfaceSoft)
  document.documentElement.style.setProperty('--el-fill-color-extra-light', theme.surfaceSoft)
  document.documentElement.style.setProperty('--el-fill-color-blank', theme.surface)
  document.documentElement.style.setProperty('--el-text-color-primary', theme.text)
  document.documentElement.style.setProperty('--el-text-color-regular', theme.text)
  document.documentElement.style.setProperty('--el-text-color-secondary', theme.textMuted)
  document.documentElement.style.setProperty('--el-text-color-placeholder', theme.textMuted)
  document.documentElement.style.setProperty('--el-border-color', theme.border)
  document.documentElement.style.setProperty('--el-border-color-light', theme.border)
  document.documentElement.style.setProperty('--el-border-color-lighter', theme.border)
  document.documentElement.style.setProperty('--el-border-color-extra-light', theme.border)
  document.documentElement.style.setProperty('--el-overlay-color', isDark ? 'rgba(0, 0, 0, 0.66)' : 'rgba(0, 0, 0, 0.55)')
  document.documentElement.style.setProperty('--el-overlay-color-light', isDark ? 'rgba(0, 0, 0, 0.58)' : 'rgba(0, 0, 0, 0.5)')
  document.documentElement.style.setProperty('--el-overlay-color-lighter', isDark ? 'rgba(0, 0, 0, 0.45)' : 'rgba(0, 0, 0, 0.35)')
  document.documentElement.style.setProperty('--el-mask-color', isDark ? 'rgba(17, 24, 39, 0.76)' : 'rgba(255, 255, 255, 0.88)')
  document.documentElement.style.setProperty('--el-mask-color-extra-light', isDark ? 'rgba(17, 24, 39, 0.45)' : 'rgba(255, 255, 255, 0.35)')

  document.body.style.backgroundColor = theme.appBg
  document.body.style.color = theme.text
  document.body.style.overflow = 'hidden'
}

watch(uiMode, (value) => {
  localStorage.setItem('ui-mode', value)
})

watch([themeKey, darkMode], ([themeValue, isDark]) => {
  localStorage.setItem('app-theme', themeValue)
  localStorage.setItem('app-dark-mode', String(isDark))
  applyTheme(themeValue, isDark)
}, { immediate: true })

onMounted(() => {
  document.documentElement.style.height = '100%'
  document.documentElement.style.overflow = 'hidden'
  document.body.style.height = '100%'
  document.body.style.margin = '0'
  document.body.style.overflow = 'hidden'
  const appRoot = document.getElementById('app')
  if (appRoot) {
    appRoot.style.height = '100%'
    appRoot.style.overflow = 'hidden'
  }
})
</script>

<style scoped>
.app-wrapper {
  height: 100%;
  min-height: 100%;
  padding: 12px;
  overflow: hidden;
  display: flex;
  align-items: stretch;
  justify-content: center;
  background:
    radial-gradient(circle at 0% 0%, color-mix(in srgb, var(--app-primary-color, #4a7cff) 22%, transparent), transparent 45%),
    radial-gradient(circle at 100% 100%, color-mix(in srgb, var(--app-primary-color, #4a7cff) 14%, transparent), transparent 55%),
    var(--app-bg-color, #eef2f7);
}

.app-shell {
  width: min(100%, 1280px);
  height: calc(100% - 24px);
  min-height: calc(100% - 24px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: color-mix(in srgb, var(--app-bg-color, #f5f7fa) 86%, var(--app-surface-color, #ffffff));
  color: var(--app-text-color, #1f2d3d);
  --el-color-primary: var(--app-primary-color, #4a7cff);
  --el-text-color-primary: var(--app-text-color, #1f2d3d);
  --el-border-color: var(--app-border-color, #dbe2ea);
}

.app-shell.windows-mode {
  width: 100%;
  height: calc(100% - 24px);
  min-height: 620px;
  max-height: none;
  border: 1px solid var(--app-border-color, #dbe2ea);
  border-radius: 20px;
  overflow: hidden;
  box-shadow:
    0 24px 60px rgba(18, 35, 67, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.36);
}

.app-shell.android-mode {
  width: min(100%, 430px);
  height: calc(100% - 24px);
  max-height: 100%;
  margin: 0 auto;
  border: 1px solid var(--app-border-color, #dbe2ea);
  border-radius: 28px;
  box-shadow:
    0 20px 45px rgba(18, 35, 67, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.app-header {
  padding: 12px 16px 10px;
  background: color-mix(in srgb, var(--app-surface-color, #ffffff) 86%, transparent);
  border-bottom: 1px solid var(--app-border-color, #dbe2ea);
  backdrop-filter: blur(8px);
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.header-title h2 {
  margin: 0;
  font-size: 22px;
  letter-spacing: 0.2px;
}

.header-title p {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--app-text-muted-color, #5f6b7a);
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.theme-switch {
  --el-switch-on-color: var(--app-primary-color, #4a7cff);
}

.color-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.color-option-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  border: none;
  background: transparent;
  padding: 6px;
  border-radius: 8px;
  cursor: pointer;
}

.color-option-btn:hover {
  background: var(--app-surface-soft-color, #f6f8fb);
}

.color-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid var(--app-border-color, #dbe2ea);
}

.color-label {
  flex: 1;
  text-align: left;
  font-size: 13px;
  color: var(--app-text-color, #1f2d3d);
}

.color-check {
  color: var(--app-primary-color, #4a7cff);
}

.app-content {
  flex: 1;
  min-height: 0;
  padding: 16px;
  overflow-y: auto;
  background: linear-gradient(
    165deg,
    color-mix(in srgb, var(--app-surface-color, #ffffff) 94%, transparent),
    color-mix(in srgb, var(--app-surface-soft-color, #f6f8fb) 88%, transparent)
  );
}

.tab-footer {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 10px 10px calc(10px + env(safe-area-inset-bottom, 0px));
  background: color-mix(in srgb, var(--app-surface-color, #ffffff) 92%, transparent);
  border-top: 1px solid var(--app-border-color, #dbe2ea);
  margin-top: auto;
  position: relative;
  z-index: 2;
  flex-shrink: 0;
}

.tab-footer :deep(.el-button) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-width: 0;
  height: 34px;
  padding: 0 8px;
  line-height: 1;
  border-radius: 10px;
}

.tab-footer :deep(.el-button--primary.is-text) {
  background: color-mix(in srgb, var(--app-primary-color, #4a7cff) 14%, transparent);
}

.tab-footer :deep(.el-button > span) {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  line-height: 1.2;
}

@media (max-width: 1024px) {
  .app-wrapper {
    padding: 0;
  }

  .app-shell.windows-mode,
  .app-shell.android-mode,
  .app-shell {
    width: 100%;
    max-width: none;
    height: 100%;
    max-height: none;
    min-height: 100%;
    border-radius: 0;
    box-shadow: none;
  }

  .header-title h2 {
    font-size: 19px;
  }

  .header-title p {
    display: none;
  }

  .app-content {
    padding: 12px;
  }
}

.app-shell :deep(.el-card),
.app-shell :deep(.el-dialog) {
  background: var(--app-surface-color, #ffffff);
  border-color: var(--app-border-color, #dbe2ea);
}

.app-shell :deep(.el-card__header),
.app-shell :deep(.el-dialog__header) {
  border-bottom-color: var(--app-border-color, #dbe2ea);
  color: var(--app-text-color, #1f2d3d);
}

.app-shell :deep(.el-card__body),
.app-shell :deep(.el-table),
.app-shell :deep(.el-form-item__label),
.app-shell :deep(.el-dialog__body),
.app-shell :deep(.el-descriptions__label),
.app-shell :deep(.el-descriptions__content) {
  color: var(--app-text-color, #1f2d3d);
}

.app-shell :deep(.el-table) {
  --el-table-header-bg-color: var(--app-surface-soft-color, #f6f8fb);
  --el-table-tr-bg-color: var(--app-surface-color, #ffffff);
  --el-table-row-hover-bg-color: var(--app-surface-soft-color, #f6f8fb);
  --el-table-border-color: var(--app-border-color, #dbe2ea);
  --el-table-text-color: var(--app-text-color, #1f2d3d);
}
</style>
