<template>
  <div>
    <el-card v-if="focusScreenVisible" :class="['running-screen', 'running-screen-full']">
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
    <el-card class="todo-summary-card">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div class="todo-main-head">
            <span>待办</span>
            <el-button circle type="primary" @click="openCreateDialog()">
              <el-icon><Plus /></el-icon>
            </el-button>
          </div>
          <el-tag type="warning">已完成 {{ completedPomodoros }} 个</el-tag>
        </div>
      </template>
    </el-card>

    <el-empty v-if="!cardGroups.length" description="暂无待办卡片，先新增一个卡片吧" />

    <div v-else class="cards-wrap">
      <el-card
        v-for="card in cardGroups"
        :key="card.key"
        :class="['todo-group-card', { 'todo-group-card-collapsed': !isCardExpanded(card.key) }]"
      >
        <template #header>
          <div class="card-head-row">
            <div class="card-head-title">{{ card.name }}</div>
            <div class="card-head-actions">
              <el-button text type="primary" @click="toggleCardExpand(card.key)">
                {{ isCardExpanded(card.key) ? '收起' : '展开' }}
              </el-button>
              <el-button text type="primary" @click="openCreateDialog(card.id)">新增</el-button>
              <template v-if="card.id !== null">
                <el-button text type="primary" @click="openEditCard(card)">改名</el-button>
                <el-button text type="primary" @click="openCardAiDialog(card)">AI</el-button>
                <el-button text type="danger" @click="onDeleteCard(card)">删除</el-button>
              </template>
              <template v-else>
                <el-button text type="danger" @click="onDeleteCard(card)">删除</el-button>
              </template>
            </div>
          </div>
        </template>

        <template v-if="isCardExpanded(card.key)">
          <el-empty v-if="!card.items.length" description="该卡片暂无待办" />

          <el-table v-else :data="card.items" style="width: 100%">
            <el-table-column prop="title" label="标题" />
            <el-table-column label="计时提示" width="180">
              <template #default="scope">
                <span>{{ formatTimerHint(scope.row) }}</span>
              </template>
            </el-table-column>
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
        </template>
      </el-card>
    </div>

    <el-dialog
      v-model="todoDialogVisible"
      :title="todoDialogMode === 'create' ? '新增待办' : '修改待办'"
      width="min(420px, 92vw)"
      custom-class="todo-edit-dialog"
      top="4vh"
    >
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
        <el-form-item label="所属卡片">
          <el-autocomplete
            v-model="dialogCollectionName"
            clearable
            :fetch-suggestions="queryCollectionSuggestions"
            placeholder="输入或选择待办卡片名"
            style="width: 220px;"
          />
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

    <el-dialog
      v-model="cardDialogVisible"
      title="修改待办卡片"
      width="min(360px, 92vw)"
      custom-class="card-edit-dialog"
      top="4vh"
    >
      <el-form label-width="72px">
        <el-form-item label="名称">
          <el-input v-model="cardDialogName" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cardDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onCardDialogSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="aiAdviceDialogVisible" :title="`AI 专注建议 · ${aiTargetCardName || '未分配卡片'}`" width="760">
      <el-form label-width="96px">
        <el-form-item label="统计范围">
          <el-segmented v-model="adviceDays" :options="adviceRangeOptions" />
        </el-form-item>
        <el-form-item label="补充需求">
          <el-input
            v-model="advicePrompt"
            type="textarea"
            :rows="3"
            placeholder="例如：我最近下午容易分心，请给具体调整方案"
          />
        </el-form-item>
      </el-form>
      <div class="inline-actions" style="margin-bottom: 10px;">
        <el-button type="primary" :loading="generatingAdvice" @click="onGenerateAdvice">生成建议</el-button>
      </div>
      <el-alert v-if="adviceMeta.reason" :title="adviceMeta.reason" :type="adviceMeta.used_ai ? 'success' : 'warning'" :closable="false" />
      <el-alert v-if="adviceHeadline" :title="adviceHeadline" type="info" :closable="false" style="margin-top: 12px;" />

      <div v-if="adviceSections.length" class="advice-sections">
        <el-card v-for="section in adviceSections" :key="section.title" class="advice-section-card" shadow="never">
          <template #header>
            <strong>{{ section.title }}</strong>
          </template>
          <ul class="advice-list">
            <li v-for="(item, index) in section.bullets" :key="`${section.title}-${index}`">{{ item }}</li>
          </ul>
        </el-card>
      </div>

      <el-card v-if="tuningSuggestions.length" class="advice-section-card" shadow="never" style="margin-top: 12px;">
        <template #header>
          <div class="card-head-row">
            <strong>任务调参建议（名称 + 时长）</strong>
            <el-button type="primary" plain size="small" @click="openConvertDialog">转换为待办卡片</el-button>
          </div>
        </template>
        <el-table :data="tuningSuggestions" size="small" style="width: 100%">
          <el-table-column prop="current_title" label="当前待办" min-width="150" />
          <el-table-column prop="suggested_title" label="推荐待办名" min-width="160" />
          <el-table-column label="时长建议" width="170">
            <template #default="scope">
              <span>{{ scope.row.current_focus_minutes }} -> {{ scope.row.suggested_focus_minutes }} 分钟</span>
            </template>
          </el-table-column>
          <el-table-column prop="reason" label="原因" min-width="200" />
        </el-table>
      </el-card>

      <pre v-if="!adviceSections.length && !tuningSuggestions.length && adviceText" class="advice-content">{{ adviceText }}</pre>
      <template #footer>
        <el-button @click="aiAdviceDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="convertDialogVisible" title="转换建议到待办卡片" width="640px">
      <el-alert
        type="info"
        :closable="false"
        title="勾选要采纳的建议，确认后会自动创建一个 AI 建议待办卡片，并写入对应任务与推荐时长。"
        style="margin-bottom: 12px;"
      />

      <el-checkbox-group v-model="selectedSuggestionIndexes" class="suggestion-checklist">
        <el-card
          v-for="(item, index) in tuningSuggestions"
          :key="`${item.current_title}-${index}`"
          class="suggestion-item-card"
          shadow="never"
        >
          <div class="sync-item-head">
            <el-checkbox :value="String(index)">
              {{ item.current_title }} -> {{ item.suggested_title }}
            </el-checkbox>
          </div>
          <div class="sync-item-meta">
            <span>{{ item.current_focus_minutes }} -> {{ item.suggested_focus_minutes }} 分钟</span>
            <span>{{ item.reason }}</span>
          </div>
        </el-card>
      </el-checkbox-group>

      <template #footer>
        <el-button @click="convertDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="convertingSuggestions" @click="onConvertSuggestions">确认转换</el-button>
      </template>
    </el-dialog>
    </template>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { CircleCheck, CloseBold, Plus, RefreshRight, VideoPause, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createCollection, createTodo, deleteCollection, deleteTodo, fetchCollections, fetchTodos, generateAiAdvice, recordInterrupt, recordPomodoro, updateCollection, updateTodo } from '../api/pomodoro'

const props = defineProps({
  uiMode: {
    type: String,
    default: 'windows'
  }
})

const todos = ref([])
const collections = ref([])
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
const dialogCollectionName = ref('')
const aiAdviceDialogVisible = ref(false)
const generatingAdvice = ref(false)
const adviceDays = ref(30)
const adviceRangeOptions = [
  { label: '7天', value: 7 },
  { label: '30天', value: 30 },
  { label: '90天', value: 90 }
]
const advicePrompt = ref('')
const adviceText = ref('')
const adviceHeadline = ref('')
const adviceSections = ref([])
const tuningSuggestions = ref([])
const aiTargetCardId = ref(null)
const adviceMeta = ref({
  used_ai: false,
  provider: '',
  generated_at: '',
  reason: ''
})
const convertDialogVisible = ref(false)
const convertingSuggestions = ref(false)
const selectedSuggestionIndexes = ref([])
const cardDialogVisible = ref(false)
const cardDialogId = ref(null)
const cardDialogName = ref('')
const expandedCardKeys = ref([])
let timerRef = null
let timerStartedAtMs = null
let timerStartSeconds = 0
let finishingByTimer = false
const isWindowsUi = computed(() => props.uiMode === 'windows')

const cardGroups = computed(() => {
  const grouped = collections.value.map((collection) => ({
    key: `card-${collection.id}`,
    id: collection.id,
    name: collection.name,
    items: todos.value.filter((todo) => todo.collection_id === collection.id)
  }))
  const ungrouped = todos.value.filter((todo) => todo.collection_id == null)
  if (ungrouped.length) {
    grouped.push({
      key: 'card-ungrouped',
      id: null,
      name: '未分配卡片',
      items: ungrouped
    })
  }
  return grouped
})

const aiTargetCard = computed(() => cardGroups.value.find((card) => card.id === aiTargetCardId.value) || null)
const aiTargetCardName = computed(() => aiTargetCard.value?.name || '')

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
  document.body.style.overflow = visible ? 'hidden' : ''
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

async function loadCollections() {
  const res = await fetchCollections()
  collections.value = Array.isArray(res.data) ? res.data : []
}

function nextDefaultCardName() {
  let maxIndex = 0
  for (const item of collections.value) {
    const match = /^待办卡片(\d+)$/.exec(String(item.name || '').trim())
    if (!match) {
      continue
    }
    maxIndex = Math.max(maxIndex, Number(match[1]))
  }
  return `待办卡片${maxIndex + 1}`
}

async function ensureAtLeastOneCard() {
  if (collections.value.length > 0) {
    return
  }
  await createCollection({ name: nextDefaultCardName() })
  await loadCollections()
}

async function loadData() {
  await Promise.all([loadTodos(), loadCollections()])
  await ensureAtLeastOneCard()
}

function resetDialogForm() {
  dialogTitle.value = ''
  dialogTimerMode.value = 'countdown'
  dialogFocusMinutes.value = 25
  dialogCollectionName.value = ''
}

function isCardExpanded(cardKey) {
  return expandedCardKeys.value.includes(cardKey)
}

function toggleCardExpand(cardKey) {
  if (isCardExpanded(cardKey)) {
    expandedCardKeys.value = expandedCardKeys.value.filter((item) => item !== cardKey)
    return
  }
  expandedCardKeys.value = [...expandedCardKeys.value, cardKey]
}

function openCreateDialog(collectionId) {
  todoDialogMode.value = 'create'
  resetDialogForm()
  if (collectionId !== undefined) {
    const found = collections.value.find((item) => item.id === collectionId)
    dialogCollectionName.value = found?.name || ''
  }
  todoDialogVisible.value = true
}

function queryCollectionSuggestions(queryString, cb) {
  const keyword = String(queryString || '').trim().toLowerCase()
  const options = collections.value
    .map((item) => String(item?.name || '').trim())
    .filter(Boolean)
    .filter((name, index, arr) => arr.indexOf(name) === index)
    .filter((name) => !keyword || name.toLowerCase().includes(keyword))
    .map((name) => ({ value: name }))
  cb(options)
}

function formatDurationLabel(minutes) {
  const safeMinutes = Math.max(Number(minutes) || 0, 0)
  if (safeMinutes < 60) {
    return `${safeMinutes}min`
  }
  const hour = Math.floor(safeMinutes / 60)
  const minute = safeMinutes % 60
  if (minute === 0) {
    return `${hour}h`
  }
  return `${hour}h${minute}min`
}

function formatTimerHint(todo) {
  if ((todo.timer_mode || 'countdown') === 'countup') {
    return '正计时'
  }
  return `倒计时(${formatDurationLabel(todo.focus_minutes || 25)})`
}

function openCardAiDialog(card) {
  aiTargetCardId.value = card.id
  aiAdviceDialogVisible.value = true
}

async function onGenerateAdvice() {
  generatingAdvice.value = true
  try {
    const aiCardTodos = (aiTargetCard.value?.items || []).map((item) => ({
      title: item.title,
      timer_mode: item.timer_mode || 'countdown',
      focus_minutes: item.focus_minutes || 25
    }))
    const cardSummary = aiCardTodos.length
      ? aiCardTodos.map((item, index) => `${index + 1}. ${item.title}（${item.timer_mode === 'countup' ? '正计时' : `倒计时${item.focus_minutes}分钟`}）`).join('\n')
      : '当前卡片暂无待办'
    const mergedPrompt = [
      `请基于以下待办卡片生成专注建议。卡片名：${aiTargetCardName.value || '未分配卡片'}`,
      '重点给出：任务拆分、时长调整、执行顺序建议。',
      `待办列表：\n${cardSummary}`,
      advicePrompt.value?.trim() ? `补充需求：${advicePrompt.value.trim()}` : ''
    ].filter(Boolean).join('\n\n')
    const res = await generateAiAdvice({
      days: adviceDays.value,
      prompt: mergedPrompt
    })
    const data = res.data || {}
    adviceText.value = data.advice || ''
    adviceHeadline.value = data.advice_structured?.headline || ''
    adviceSections.value = Array.isArray(data.advice_structured?.sections) ? data.advice_structured.sections : []
    tuningSuggestions.value = Array.isArray(data.advice_structured?.task_tuning_suggestions)
      ? data.advice_structured.task_tuning_suggestions
      : []
    selectedSuggestionIndexes.value = tuningSuggestions.value.map((_, index) => String(index))
    adviceMeta.value = {
      used_ai: !!data.used_ai,
      provider: data.provider || '',
      generated_at: data.generated_at || '',
      reason: data.reason || ''
    }
  } finally {
    generatingAdvice.value = false
  }
}

function openConvertDialog() {
  if (!tuningSuggestions.value.length) {
    ElMessage.warning('暂无可转换的任务调参建议')
    return
  }
  selectedSuggestionIndexes.value = tuningSuggestions.value.map((_, index) => String(index))
  convertDialogVisible.value = true
}

function buildAiCollectionName() {
  const now = new Date()
  const yyyy = now.getFullYear()
  const mm = String(now.getMonth() + 1).padStart(2, '0')
  const dd = String(now.getDate()).padStart(2, '0')
  const hh = String(now.getHours()).padStart(2, '0')
  const mi = String(now.getMinutes()).padStart(2, '0')
  return `AI建议-${yyyy}${mm}${dd}-${hh}${mi}`
}

async function onConvertSuggestions() {
  if (!selectedSuggestionIndexes.value.length) {
    ElMessage.warning('请至少勾选一条建议')
    return
  }

  const selected = selectedSuggestionIndexes.value
    .map((value) => Number(value))
    .filter((index) => Number.isInteger(index) && index >= 0 && index < tuningSuggestions.value.length)
    .map((index) => tuningSuggestions.value[index])

  if (!selected.length) {
    ElMessage.warning('没有可转换的建议，请重新选择')
    return
  }

  convertingSuggestions.value = true
  try {
    const collectionRes = await createCollection({ name: buildAiCollectionName() })
    const collectionId = collectionRes.data?.id

    if (!collectionId) {
      throw new Error('创建待办卡片失败')
    }

    await Promise.all(
      selected.map((item) =>
        createTodo({
          title: item.suggested_title || item.current_title,
          estimated_pomodoros: 1,
          timer_mode: 'countdown',
          focus_minutes: Math.max(1, Math.min(180, Number(item.suggested_focus_minutes) || 25)),
          collection_id: collectionId
        })
      )
    )

    convertDialogVisible.value = false
    ElMessage.success(`已转换 ${selected.length} 条建议到待办卡片`)
    await loadData()
  } finally {
    convertingSuggestions.value = false
  }
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

function syncTimerByRealElapsed() {
  if (!isRunning.value || timerStartedAtMs == null) {
    return false
  }
  const elapsedSeconds = Math.max(0, Math.floor((Date.now() - timerStartedAtMs) / 1000))
  if (shouldCountDown.value) {
    currentSeconds.value = Math.max(timerStartSeconds - elapsedSeconds, 0)
    return currentSeconds.value <= 0
  }
  currentSeconds.value = timerStartSeconds + elapsedSeconds
  return false
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
  timerStartedAtMs = Date.now()
  timerStartSeconds = currentSeconds.value
  timerRef = setInterval(async () => {
    const finished = syncTimerByRealElapsed()
    if (finished) {
      if (finishingByTimer) {
        return
      }
      finishingByTimer = true
      try {
        await finishPomodoro('番茄钟完成，已记录到统计数据')
      } finally {
        finishingByTimer = false
      }
      return
    }
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
  syncTimerByRealElapsed()
  if (timerRef) {
    clearInterval(timerRef)
    timerRef = null
  }
  timerStartedAtMs = null
  timerStartSeconds = currentSeconds.value
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

async function onTodosSynced(event) {
  await loadData()
  const todoIds = Array.isArray(event?.detail?.todoIds) ? event.detail.todoIds : []
  if (!todoIds.length) {
    return
  }
  const found = todos.value.find((item) => todoIds.includes(item.id))
  if (!found) {
    return
  }
  currentTodoId.value = found.id
  currentTodoTitle.value = found.title
}

function openEdit(todo) {
  todoDialogMode.value = 'edit'
  editId.value = todo.id
  dialogTitle.value = todo.title
  dialogTimerMode.value = todo.timer_mode || 'countdown'
  dialogFocusMinutes.value = todo.focus_minutes || 25
  const found = collections.value.find((item) => item.id === (todo.collection_id ?? null))
  dialogCollectionName.value = found?.name || ''
  todoDialogVisible.value = true
}

async function onDialogSave() {
  if (!dialogTitle.value.trim()) {
    ElMessage.warning('请输入待办标题')
    return
  }

  let targetCollectionId = null
  const targetCollectionName = String(dialogCollectionName.value || '').trim()
  if (targetCollectionName) {
    const existed = collections.value.find((item) => String(item.name || '').trim() === targetCollectionName)
    if (existed) {
      targetCollectionId = existed.id
    } else {
      const created = await createCollection({ name: targetCollectionName })
      targetCollectionId = created?.data?.id ?? null
      await loadCollections()
      if (targetCollectionId == null) {
        const fallback = collections.value.find((item) => String(item.name || '').trim() === targetCollectionName)
        targetCollectionId = fallback?.id ?? null
      }
    }
  }

  const payload = {
    title: dialogTitle.value.trim(),
    estimated_pomodoros: 1,
    timer_mode: dialogTimerMode.value,
    focus_minutes: dialogFocusMinutes.value,
    collection_id: targetCollectionId
  }

  if (todoDialogMode.value === 'create') {
    await createTodo(payload)
  } else {
    await updateTodo(editId.value, payload)
  }

  todoDialogVisible.value = false
  await loadData()
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
  await loadData()
}

function openEditCard(card) {
  cardDialogId.value = card.id
  cardDialogName.value = card.name
  cardDialogVisible.value = true
}

async function onCardDialogSave() {
  if (!cardDialogName.value.trim()) {
    ElMessage.warning('请输入待办卡片名称')
    return
  }
  await updateCollection(cardDialogId.value, { name: cardDialogName.value.trim() })
  cardDialogVisible.value = false
  await loadCollections()
}

async function onDeleteCard(card) {
  if (card.id == null) {
    if (!Array.isArray(card.items) || !card.items.length) {
      ElMessage.info('未分配卡片暂无待办可删除')
      return
    }

    try {
      await ElMessageBox.confirm(
        `确认删除未分配卡片下全部待办吗？共 ${card.items.length} 条，该操作不可恢复。`,
        '删除确认',
        {
          type: 'warning',
          confirmButtonText: '确认',
          cancelButtonText: '取消'
        }
      )
    } catch {
      return
    }

    const idSet = new Set(card.items.map((item) => item.id))
    await Promise.all(card.items.map((item) => deleteTodo(item.id)))

    if (currentTodoId.value != null && idSet.has(currentTodoId.value)) {
      currentTodoId.value = null
      currentTodoTitle.value = ''
      resetTimer()
    }

    await loadData()
    ElMessage.success(`已删除未分配卡片中的 ${card.items.length} 条待办`)
    return
  }

  try {
    await ElMessageBox.confirm('确认删除该待办卡片吗？卡片中的待办会变为未分配。', '删除确认', {
      type: 'warning',
      confirmButtonText: '确认',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  await deleteCollection(card.id)
  await loadData()
}

onMounted(async () => {
  phase.value = 'focus'
  resetClockByMode()
  document.addEventListener('fullscreenchange', onFullscreenChange)
  window.addEventListener('pomodoro:todos-synced', onTodosSynced)
  await loadData()
})

onBeforeUnmount(() => {
  if (timerRef) {
    clearInterval(timerRef)
  }
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  window.removeEventListener('pomodoro:todos-synced', onTodosSynced)
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
  min-height: 100%;
  height: 100%;
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
  font-size: clamp(58px, 12vw, 96px);
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

.cards-wrap {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}

.inline-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.advice-content {
  margin: 12px 0 0;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  padding: 10px;
  border: 1px solid var(--app-border-color, #dbe2ea);
  border-radius: 8px;
  background: var(--app-surface-soft-color, #f6f8fb);
}

.advice-sections {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.advice-section-card :deep(.el-card__header) {
  padding: 10px 14px;
}

.advice-section-card :deep(.el-card__body) {
  padding: 10px 14px 12px;
}

.advice-list {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.suggestion-checklist {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 420px;
  overflow: auto;
}

.suggestion-item-card :deep(.el-card__body) {
  padding: 10px 12px;
}

.card-head-row {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}

.card-head-title {
  width: 100%;
  line-height: 1.3;
}

.card-head-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  flex-wrap: nowrap;
  overflow-x: auto;
}

.card-head-actions :deep(.el-button) {
  flex: 0 0 auto;
}

.todo-main-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.todo-summary-card :deep(.el-card__header) {
  border-bottom: none;
}

.todo-summary-card :deep(.el-card__body) {
  display: none;
}

.todo-group-card.todo-group-card-collapsed :deep(.el-card__header) {
  border-bottom: none;
}

.todo-group-card.todo-group-card-collapsed :deep(.el-card__body) {
  display: none;
}

:deep(.todo-edit-dialog) {
  width: min(420px, calc(100vw - 24px)) !important;
}

:deep(.card-edit-dialog) {
  width: min(360px, calc(100vw - 24px)) !important;
}

@media (max-width: 768px) {
  :deep(.todo-edit-dialog) {
    margin: 0 auto !important;
    max-height: calc(100vh - 16px);
    display: flex;
    flex-direction: column;
  }

  :deep(.todo-edit-dialog .el-dialog__body) {
    overflow-y: auto;
  }

  :deep(.card-edit-dialog) {
    margin: 0 auto !important;
    max-height: calc(100vh - 16px);
    display: flex;
    flex-direction: column;
  }

  :deep(.card-edit-dialog .el-dialog__body) {
    overflow-y: auto;
  }
}
</style>
