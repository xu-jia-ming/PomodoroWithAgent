<template>
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
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { fetchMe } from '../api/pomodoro'

const user = ref({ id: 0, nickname: '-' })

onMounted(async () => {
  const res = await fetchMe()
  user.value = res.data
})
</script>
