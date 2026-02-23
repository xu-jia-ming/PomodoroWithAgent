<template>
  <el-card>
    <template #header>
      <span>锁机</span>
    </template>

    <el-form :inline="true" @submit.prevent>
      <el-form-item label="专注时长(分钟)">
        <el-input-number v-model="durationMinutes" :min="1" :max="180" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :disabled="status.active" @click="onStart">开始</el-button>
        <el-button :disabled="!status.active" @click="onStop">停止</el-button>
      </el-form-item>
    </el-form>

    <el-descriptions :column="1" border>
      <el-descriptions-item label="当前阶段">
        <el-tag type="info">{{ currentPhase }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="当前状态">
        <el-tag :type="status.active ? 'warning' : 'success'">
          {{ status.active ? '锁机中' : '未锁机' }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="剩余时间">
        {{ remainText }}
      </el-descriptions-item>
    </el-descriptions>
  </el-card>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { fetchFocusStatus, startFocus, stopFocus } from '../api/pomodoro'

const durationMinutes = ref(25)
const status = ref({ active: false, end_time: null })
const currentPhase = ref('专注')
const nowTs = ref(Date.now())
let timer = null

const remainText = computed(() => {
  if (!status.value.active || !status.value.end_time) {
    return '00:00'
  }
  const remainMs = Math.max(new Date(status.value.end_time).getTime() - nowTs.value, 0)
  const totalSeconds = Math.floor(remainMs / 1000)
  const m = String(Math.floor(totalSeconds / 60)).padStart(2, '0')
  const s = String(totalSeconds % 60).padStart(2, '0')
  return `${m}:${s}`
})

async function refreshStatus() {
  const res = await fetchFocusStatus()
  status.value = res.data
}

function refreshPhase() {
  currentPhase.value = localStorage.getItem('pomodoro-phase') || '专注'
}

async function onStart() {
  await startFocus({ duration_minutes: durationMinutes.value })
  await refreshStatus()
}

async function onStop() {
  await stopFocus()
  await refreshStatus()
}

onMounted(async () => {
  refreshPhase()
  await refreshStatus()
  timer = setInterval(async () => {
    nowTs.value = Date.now()
    refreshPhase()
    if (status.value.active && status.value.end_time && new Date(status.value.end_time).getTime() <= nowTs.value) {
      await refreshStatus()
    }
  }, 1000)
})

onBeforeUnmount(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>
