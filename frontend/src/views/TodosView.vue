<template>
  <div>
    <el-card v-if="focusScreenVisible" :class="['running-screen', { 'running-screen-full': isWindowsUi }]">
      <div class="running-exit">
        <el-tooltip content="退出锁屏" placement="left">
          <el-button circle size="small" class="running-exit-btn" @click="exitFocusScreen">
            <el-icon><CloseBold /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
      <div class="running-main">
        <div class="running-badge">当前待办：{{ currentTodoTitle || '无' }}</div>
        <div class="running-time">{{ remainingDisplay }}</div>
      </div>
      <div class="timer-actions-row running-actions">
        <el-tooltip :content="isRunning ? '暂停' : '继续'" placement="top">
          <el-button circle size="large" class="running-btn running-btn-primary" @click="isRunning ? pauseTimer() : startTimer()">
            <el-icon v-if="isRunning"><VideoPause /></el-icon>
            <el-icon v-else><VideoPlay /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="提前完成" placement="top">
          <el-button circle size="large" class="running-btn running-btn-success" @click="completeEarly">
            <el-icon><CircleCheck /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="重置" placement="top">
          <el-button circle size="large" class="running-btn" @click="resetTimer">
            <el-icon><RefreshRight /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
    </el-card>

    <template v-else>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>待办</span>
          <el-tag type="warning">已完成 {{ completedPomodoros }} 个</el-tag>
        </div>
      </template>

      <el-form :inline="true" @submit.prevent>
        <el-form-item>
          <div style="display:flex; align-items:center; gap:12px;"><el-input v-model="title" placeholder="待办标题" style="width: 240px" />
          <el-button type="primary" @click="openCreateDialog">新增</el-button></div>
        </el-form-item>
      </el-form>

      <el-table :data="todos" style="width: 100%">
        <el-table-column prop="title" label="标题" />
        <el-table-column label="操作" width="160" align="center">
          <template #default="scope">
            <div class="todo-action-icons">
              <el-tooltip content="执行" placement="top">
                <el-button circle size="small" type="primary" @click="executeTodo(scope.row)">▶</el-button>
              </el-tooltip>
              <el-tooltip content="修改" placement="top">
                <el-button circle size="small" @click="openEdit(scope.row)">✎</el-button>
              </el-tooltip>
              <el-tooltip content="删除" placement="top">
                <el-button circle size="small" type="danger" @click="onDelete(scope.row.id)">🗑</el-button>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="todoDialogVisible" :title="todoDialogMode === 'create' ? '新增待办' : '修改待办'" width="420">
      <el-form label-width="92px">
        <el-form-item label="标题">
          <el-input v-model="dialogTitle" />
        </el-form-item>
        <el-form-item label="计时模式">
          <el-radio-group v-model="dialogTimerMode">
            <el-radio-button label="countdown">倒计时</el-radio-button>
            <el-radio-button label="countup">正计时</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="dialogTimerMode === 'countdown'" label="专注(分钟)">
          <el-input-number v-model="dialogFocusMinutes" :min="1" :max="180" />
        </el-form-item>
        <el-form-item v-else>
          <el-tag type="info">正计时模式不设时长，手动提前完成</el-tag>
        </el-form-item>
        <el-form-item label="短休息(分钟)">
          <el-tag>5</el-tag>
        </el-form-item>
        <el-form-item label="长休息(分钟)">
          <el-tag>15</el-tag>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="todoDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onDialogSave">保存</el-button>
      </template>
    </el-dialog>
    </template>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { CircleCheck, CloseBold, RefreshRight, VideoPause, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createTodo, deleteTodo, fetchTodos, recordInterrupt, recordPomodoro, updateTodo } from '../api/pomodoro'

const props = defineProps({
  uiMode: {
    type: String,
    default: 'windows'
  }
})

const todos = ref([])
const title = ref('')
const timerMode = ref('countdown')
const focusMinutes = ref(25)
const shortBreakMinutes = 5
const longBreakMinutes = 15
const phase = ref('focus')
const breakKind = ref('short')
const currentSeconds = ref(25 * 60)
const isRunning = ref(false)
const focusScreenVisible = ref(false)
const completedPomodoros = ref(0)
const currentTodoId = ref(null)
const currentTodoTitle = ref('')
const todoDialogVisible = ref(false)
const todoDialogMode = ref('create')
const editId = ref(null)
const dialogTitle = ref('')
const dialogTimerMode = ref('countdown')
const dialogFocusMinutes = ref(25)
let timerRef = null
const isWindowsUi = computed(() => props.uiMode === 'windows')

async function enterFullscreenMode() {
  if (!isWindowsUi.value) {
    return
  }
  const rootEl = document.documentElement
  if (document.fullscreenElement || !rootEl.requestFullscreen) {
    return
  }
  try {
    await rootEl.requestFullscreen()
  } catch {
  }
}

async function exitFullscreenMode() {
  if (!isWindowsUi.value) {
    return
  }
  if (!document.fullscreenElement || !document.exitFullscreen) {
    return
  }
  try {
    await document.exitFullscreen()
  } catch {
  }
}

function onFullscreenChange() {
  if (!focusScreenVisible.value || !isWindowsUi.value) {
    return
  }
  if (!document.fullscreenElement) {
    void enterFullscreenMode()
  }
}

const remainingDisplay = computed(() => {
  const min = String(Math.floor(currentSeconds.value / 60)).padStart(2, '0')
  const sec = String(currentSeconds.value % 60).padStart(2, '0')
  return `${min}:${sec}`
})

const shouldCountDown = computed(() => phase.value === 'break' || timerMode.value === 'countdown')

const currentTargetMinutes = computed(() => {
  if (phase.value === 'focus') {
    return focusMinutes.value
  }
  return breakKind.value === 'long' ? longBreakMinutes : shortBreakMinutes
})

function syncPhaseStorage() {
  if (phase.value === 'focus') {
    localStorage.setItem('pomodoro-phase', '专注')
    return
  }
  localStorage.setItem('pomodoro-phase', breakKind.value === 'long' ? '长休息' : '短休息')
}

function resetClockByMode() {
  currentSeconds.value = shouldCountDown.value ? currentTargetMinutes.value * 60 : 0
}

watch(focusMinutes, () => {
  if (!isRunning.value) {
    resetClockByMode()
  }
})

watch(timerMode, () => {
  if (!isRunning.value) {
    resetClockByMode()
  }
})

watch([phase, breakKind], () => {
  syncPhaseStorage()
}, { immediate: true })

watch(focusScreenVisible, (visible) => {
  document.body.style.overflow = visible && isWindowsUi.value ? 'hidden' : ''
  if (visible) {
    void enterFullscreenMode()
    return
  }
  void exitFullscreenMode()
})

async function loadTodos() {
  const res = await fetchTodos()
  todos.value = res.data
}

function resetDialogForm() {
  dialogTitle.value = ''
  dialogTimerMode.value = 'countdown'
  dialogFocusMinutes.value = 25
}

function openCreateDialog() {
  if (!title.value.trim()) {
    ElMessage.warning('请输入待办标题')
    return
  }
  todoDialogMode.value = 'create'
  resetDialogForm()
  dialogTitle.value = title.value.trim()
  todoDialogVisible.value = true
}

function getElapsedMinutes() {
  const elapsedSeconds = shouldCountDown.value
    ? currentTargetMinutes.value * 60 - currentSeconds.value
    : currentSeconds.value
  return Math.max(Math.floor(elapsedSeconds / 60), 0)
}

function getCompletionMinutes() {
  const elapsedSeconds = shouldCountDown.value
    ? currentTargetMinutes.value * 60 - currentSeconds.value
    : currentSeconds.value
  return Math.max(1, Math.ceil(elapsedSeconds / 60))
}

async function finishPomodoro(successMessage) {
  pauseTimer()
  if (phase.value === 'focus') {
    const elapsedSeconds = shouldCountDown.value
      ? currentTargetMinutes.value * 60 - currentSeconds.value
      : currentSeconds.value

    if (elapsedSeconds < 60) {
      focusScreenVisible.value = false
      resetClockByMode()
      ElMessage.warning('专注时间太短，不计入')
      return
    }

    completedPomodoros.value += 1
    await recordPomodoro({
      duration_minutes: getCompletionMinutes(),
      todo_id: currentTodoId.value,
      todo_title: currentTodoTitle.value || null
    })
    await loadTodos()

    breakKind.value = completedPomodoros.value % 4 === 0 ? 'long' : 'short'
    phase.value = 'break'
    resetClockByMode()
    ElMessage.success(successMessage)
    startTimer()
    return
  }

  phase.value = 'focus'
  resetClockByMode()
  focusScreenVisible.value = false
  ElMessage.success('休息结束，进入下一轮专注')
}

async function finishBreakEarly() {
  pauseTimer()
  phase.value = 'focus'
  resetClockByMode()
  focusScreenVisible.value = false
  ElMessage.success('已跳过休息，进入下一轮专注')
}

function startTimer() {
  if (isRunning.value) {
    return
  }

  focusScreenVisible.value = true
  void enterFullscreenMode()

  if (shouldCountDown.value && currentSeconds.value <= 0) {
    currentSeconds.value = currentTargetMinutes.value * 60
  }

  isRunning.value = true
  timerRef = setInterval(async () => {
    if (shouldCountDown.value) {
      if (currentSeconds.value <= 0) {
        await finishPomodoro('番茄钟完成，已记录到统计数据')
        return
      }
      currentSeconds.value -= 1
      return
    }
    currentSeconds.value += 1
  }, 1000)
}

async function completeEarly() {
  if (phase.value === 'focus') {
    await finishPomodoro('已提前完成，已记录到统计数据')
    return
  }
  await finishBreakEarly()
}

function exitFocusScreen() {
  resetTimer()
  focusScreenVisible.value = false
}

function pauseTimer() {
  if (timerRef) {
    clearInterval(timerRef)
    timerRef = null
  }
  isRunning.value = false
}

function resetTimer() {
  if (isRunning.value) {
    const elapsedMinutes = getElapsedMinutes()
    if (elapsedMinutes > 0) {
      if (phase.value === 'focus') {
        recordInterrupt({
          duration_minutes: elapsedMinutes,
          todo_id: currentTodoId.value,
          todo_title: currentTodoTitle.value || null
        })
      }
    }
  }
  pauseTimer()
  resetClockByMode()
}

function executeTodo(todo) {
  currentTodoId.value = todo.id
  currentTodoTitle.value = todo.title
  timerMode.value = todo.timer_mode || 'countdown'
  focusMinutes.value = todo.focus_minutes || 25
  phase.value = 'focus'
  focusScreenVisible.value = true
  resetTimer()
  startTimer()
}

function openEdit(todo) {
  todoDialogMode.value = 'edit'
  editId.value = todo.id
  dialogTitle.value = todo.title
  dialogTimerMode.value = todo.timer_mode || 'countdown'
  dialogFocusMinutes.value = todo.focus_minutes || 25
  todoDialogVisible.value = true
}

async function onDialogSave() {
  if (!dialogTitle.value.trim()) {
    ElMessage.warning('请输入待办标题')
    return
  }

  const payload = {
    title: dialogTitle.value.trim(),
    estimated_pomodoros: 1,
    timer_mode: dialogTimerMode.value,
    focus_minutes: dialogFocusMinutes.value,
    collection_id: null
  }

  if (todoDialogMode.value === 'create') {
    await createTodo(payload)
    title.value = ''
  } else {
    await updateTodo(editId.value, payload)
  }

  todoDialogVisible.value = false
  await loadTodos()
}

async function onDelete(id) {
  try {
    await ElMessageBox.confirm('确认删除该待办吗？', '删除确认', {
      type: 'warning',
      confirmButtonText: '确认',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }

  await deleteTodo(id)
  if (currentTodoId.value === id) {
    currentTodoId.value = null
    currentTodoTitle.value = ''
    resetTimer()
  }
  await loadTodos()
}

onMounted(async () => {
  phase.value = 'focus'
  resetClockByMode()
  document.addEventListener('fullscreenchange', onFullscreenChange)
  await loadTodos()
})

onBeforeUnmount(() => {
  if (timerRef) {
    clearInterval(timerRef)
  }
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  document.body.style.overflow = ''
  void exitFullscreenMode()
})
</script>

<style scoped>
.timer-actions-item {
  width: 100%;
}

.timer-actions-row {
  display: flex;
  flex-wrap: nowrap;
  gap: 16px;
}

.running-screen {
  min-height: 72vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 20px;
  border: none;
}

.running-screen-full {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  z-index: 3000;
  margin: 0;
  border-radius: 0;
}

.running-time {
  font-size: 96px;
  line-height: 1;
  font-weight: 700;
  color: var(--focus-text-color, #ffffff);
}

.running-exit {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 2;
}

.running-exit-btn {
  background: var(--focus-exit-bg-color, rgba(0, 0, 0, 0.45));
  border-color: var(--focus-exit-border-color, rgba(255, 255, 255, 0.2));
  color: var(--focus-text-color, #ffffff);
}

.running-actions {
  justify-content: center;
  margin-top: auto;
  margin-bottom: 22px;
}

.running-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  margin-top: 90px;
}

.running-btn {
  width: 56px;
  height: 56px;
  background: var(--focus-control-bg-color, #374151);
  border-color: var(--focus-control-border-color, #4b5563);
  color: var(--focus-control-text-color, #f9fafb);
}

.running-btn :deep(.el-icon) {
  font-size: 18px;
}

.running-btn-primary {
  background: var(--focus-primary-color, #5b8def);
  border-color: var(--focus-primary-color, #5b8def);
  color: #fff;
}

.running-btn-success {
  background: var(--focus-success-color, #67b85e);
  border-color: var(--focus-success-color, #67b85e);
  color: #fff;
}

.running-badge {
  background: var(--focus-badge-bg-color, #1f1f1f);
  border: none;
  color: var(--focus-badge-text-color, #67c23a);
  padding: 6px 12px;
  border-radius: 16px;
}

.running-screen :deep(.el-card__body) {
  width: 100%;
  height: 100%;
  background: var(--focus-bg-color, #1f2937);
  border-radius: 0;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
}

.todo-action-icons {
  display: flex;
  gap: 6px;
  justify-content: center;
}
</style>
