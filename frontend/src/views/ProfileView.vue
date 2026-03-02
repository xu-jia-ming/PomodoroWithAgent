<template>
  <div class="profile-page">
    <el-card>
      <template #header>
        <span>我的</span>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户ID">{{ user.id }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ user.nickname }}</el-descriptions-item>
        <el-descriptions-item label="版本">v0.1.0</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>AI 助手配置</span>
          <el-tag :type="configForm.enabled ? 'success' : 'info'">{{ configForm.enabled ? '已启用' : '未启用' }}</el-tag>
        </div>
      </template>

      <el-alert
        v-if="aiMeta.api_key_set"
        type="success"
        :closable="false"
        :title="`API Key 已配置：${aiMeta.api_key_hint || ''}`"
        style="margin-bottom: 12px;"
      />
      <el-alert
        v-else
        type="warning"
        :closable="false"
        title="尚未配置 API Key，建议先配置，否则会降级为规则建议。"
        style="margin-bottom: 12px;"
      />

      <el-form label-width="128px">
        <el-form-item label="AI厂商">
          <el-select v-model="configForm.provider" style="width: 280px" @change="onProviderChange">
            <el-option label="OpenAI兼容" value="openai_compatible" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="Moonshot" value="moonshot" />
            <el-option label="Qwen" value="qwen" />
          </el-select>
        </el-form-item>

        <el-form-item label="Base URL">
          <el-input v-model="configForm.base_url" placeholder="例如：https://api.deepseek.com/v1" />
        </el-form-item>

        <el-form-item label="模型">
          <el-input v-model="configForm.model" placeholder="例如：gpt-4o-mini / deepseek-chat" />
        </el-form-item>

        <el-form-item label="Temperature">
          <el-input-number v-model="configForm.temperature" :min="0" :max="1.5" :step="0.1" />
        </el-form-item>

        <el-form-item label="Max Tokens">
          <el-input-number v-model="configForm.max_tokens" :min="64" :max="8192" :step="64" />
        </el-form-item>

        <el-form-item label="启用AI建议">
          <el-switch v-model="configForm.enabled" />
        </el-form-item>

        <el-form-item label="API Key">
          <el-input
            v-model="newApiKey"
            show-password
            placeholder="留空表示不更新；输入后将覆盖旧 Key"
          />
        </el-form-item>
      </el-form>

      <div class="actions">
        <el-button type="primary" :loading="savingConfig" @click="saveConfig(false)">保存配置</el-button>
        <el-button type="danger" plain :loading="savingConfig" @click="saveConfig(true)">清空 API Key</el-button>
      </div>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>AI 专注建议</span>
          <el-button type="primary" :loading="generatingAdvice" @click="onGenerateAdvice">生成建议</el-button>
        </div>
      </template>

      <el-form label-width="128px">
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
          <div class="card-header">
            <strong>任务调参建议（名称 + 时长）</strong>
            <el-button type="primary" plain size="small" @click="openConvertDialog">转换为未来待办集</el-button>
          </div>
        </template>
        <el-table :data="tuningSuggestions" size="small" style="width: 100%">
          <el-table-column prop="current_title" label="当前待办" min-width="160" />
          <el-table-column label="推荐待办名" min-width="180">
            <template #default="scope">
              <span>{{ scope.row.suggested_title }}</span>
            </template>
          </el-table-column>
          <el-table-column label="时长建议" width="180">
            <template #default="scope">
              <span>{{ scope.row.current_focus_minutes }} -> {{ scope.row.suggested_focus_minutes }} 分钟</span>
            </template>
          </el-table-column>
          <el-table-column prop="reason" label="原因" min-width="220" />
        </el-table>
      </el-card>

      <pre v-if="!adviceSections.length && !tuningSuggestions.length && adviceText" class="advice-content">{{ adviceText }}</pre>

      <el-descriptions v-if="adviceMeta.generated_at" :column="1" border style="margin-top: 12px;">
        <el-descriptions-item label="生成方式">{{ adviceMeta.used_ai ? 'AI模型' : '规则引擎' }}</el-descriptions-item>
        <el-descriptions-item label="厂商">{{ adviceMeta.provider || '-' }}</el-descriptions-item>
        <el-descriptions-item label="生成时间">{{ adviceMeta.generated_at }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-dialog v-model="convertDialogVisible" title="转换建议到未来待办集" width="640px">
      <el-alert
        type="info"
        :closable="false"
        title="勾选要采纳的建议，确认后会自动创建一个 AI 建议待办集，并写入对应任务与推荐时长。"
        style="margin-bottom: 12px;"
      />

      <el-checkbox-group v-model="selectedSuggestionIndexes" class="suggestion-checklist">
        <el-card
          v-for="(item, index) in tuningSuggestions"
          :key="`${item.current_title}-${index}`"
          class="suggestion-item-card"
          shadow="never"
        >
          <div class="suggestion-item-head">
            <el-checkbox :value="String(index)">
              {{ item.current_title }} -> {{ item.suggested_title }}
            </el-checkbox>
          </div>
          <div class="suggestion-item-meta">
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
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createCollection, createTodo, fetchAiConfig, fetchMe, generateAiAdvice, updateAiConfig } from '../api/pomodoro'

const user = ref({ id: 0, nickname: '-' })
const savingConfig = ref(false)
const generatingAdvice = ref(false)

const configForm = reactive({
  provider: 'openai_compatible',
  base_url: '',
  model: 'gpt-4o-mini',
  temperature: 0.3,
  max_tokens: 700,
  enabled: false
})

const aiMeta = reactive({
  api_key_set: false,
  api_key_hint: '',
  updated_at: null
})

const newApiKey = ref('')

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
const convertDialogVisible = ref(false)
const convertingSuggestions = ref(false)
const selectedSuggestionIndexes = ref([])
const adviceMeta = reactive({
  used_ai: false,
  provider: '',
  generated_at: '',
  reason: ''
})

const providerDefaults = {
  openai_compatible: { base_url: '', model: 'gpt-4o-mini' },
  openai: { base_url: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  deepseek: { base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  moonshot: { base_url: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k' },
  qwen: { base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus' }
}

function onProviderChange(provider) {
  const defaults = providerDefaults[provider]
  if (!defaults) {
    return
  }
  if (!configForm.base_url) {
    configForm.base_url = defaults.base_url
  }
  if (!configForm.model) {
    configForm.model = defaults.model
  }
}

async function loadUserAndConfig() {
  const [userRes, configRes] = await Promise.all([fetchMe(), fetchAiConfig()])
  user.value = userRes.data

  const config = configRes.data || {}
  configForm.provider = config.provider || 'openai_compatible'
  configForm.base_url = config.base_url || ''
  configForm.model = config.model || 'gpt-4o-mini'
  configForm.temperature = config.temperature ?? 0.3
  configForm.max_tokens = config.max_tokens ?? 700
  configForm.enabled = !!config.enabled

  aiMeta.api_key_set = !!config.api_key_set
  aiMeta.api_key_hint = config.api_key_hint || ''
  aiMeta.updated_at = config.updated_at
}

async function saveConfig(clearKey) {
  savingConfig.value = true
  try {
    const trimmedKey = newApiKey.value.trim()
    const payload = {
      provider: configForm.provider,
      base_url: configForm.base_url?.trim() || null,
      model: configForm.model?.trim() || 'gpt-4o-mini',
      temperature: configForm.temperature,
      max_tokens: configForm.max_tokens,
      enabled: configForm.enabled,
      api_key: trimmedKey || null,
      replace_api_key: !clearKey && !!trimmedKey,
      clear_api_key: !!clearKey
    }
    const res = await updateAiConfig(payload)
    const config = res.data || {}
    aiMeta.api_key_set = !!config.api_key_set
    aiMeta.api_key_hint = config.api_key_hint || ''
    aiMeta.updated_at = config.updated_at
    newApiKey.value = ''
    ElMessage.success(clearKey ? 'API Key 已清空' : 'AI 配置已保存')
  } finally {
    savingConfig.value = false
  }
}

async function onGenerateAdvice() {
  generatingAdvice.value = true
  try {
    const res = await generateAiAdvice({
      days: adviceDays.value,
      prompt: advicePrompt.value?.trim() || null
    })
    const data = res.data || {}
    adviceText.value = data.advice || ''
    adviceHeadline.value = data.advice_structured?.headline || ''
    adviceSections.value = Array.isArray(data.advice_structured?.sections) ? data.advice_structured.sections : []
    tuningSuggestions.value = Array.isArray(data.advice_structured?.task_tuning_suggestions)
      ? data.advice_structured.task_tuning_suggestions
      : []
    selectedSuggestionIndexes.value = tuningSuggestions.value.map((_, index) => String(index))
    adviceMeta.used_ai = !!data.used_ai
    adviceMeta.provider = data.provider || ''
    adviceMeta.generated_at = data.generated_at || ''
    adviceMeta.reason = data.reason || ''
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
      throw new Error('创建未来待办集失败')
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
    ElMessage.success(`已转换 ${selected.length} 条建议到未来待办集`)
  } finally {
    convertingSuggestions.value = false
  }
}

onMounted(async () => {
  await loadUserAndConfig()
})
</script>

<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.actions {
  display: flex;
  gap: 10px;
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

.suggestion-item-head {
  font-weight: 600;
}

.suggestion-item-head :deep(.el-checkbox) {
  align-items: flex-start;
}

.suggestion-item-head :deep(.el-checkbox__label) {
  display: block;
  line-height: 1.5;
  white-space: normal;
  word-break: break-word;
}

.suggestion-item-meta {
  margin-top: 8px;
  font-size: 13px;
  color: var(--app-text-muted-color, #5f6b7a);
  display: grid;
  grid-template-columns: 1fr;
  row-gap: 6px;
  padding-left: 28px;
  line-height: 1.5;
}

.suggestion-item-meta span {
  display: block;
  line-height: 1.5;
  white-space: normal;
  word-break: break-word;
}
</style>
