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
          <el-input v-model="configForm.base_url" placeholder="例如：https://api.deepseek.com" />
        </el-form-item>

        <el-form-item label="模型">
          <el-input v-model="configForm.model" placeholder="例如：deepseek-chat / gpt-4o-mini" />
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

  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchAiConfig, fetchMe, updateAiConfig } from '../api/pomodoro'

const user = ref({ id: 0, nickname: '-' })
const savingConfig = ref(false)

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

const providerDefaults = {
  openai_compatible: { base_url: '', model: 'gpt-4o-mini' },
  openai: { base_url: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  deepseek: { base_url: 'https://api.deepseek.com', model: 'deepseek-chat' },
  moonshot: { base_url: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k' },
  qwen: { base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus' }
}

function onProviderChange(provider) {
  const defaults = providerDefaults[provider]
  if (!defaults) {
    return
  }
  configForm.base_url = defaults.base_url
  configForm.model = defaults.model
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
</style>

