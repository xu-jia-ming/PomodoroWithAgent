<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span>统计数据</span>
        <el-segmented v-model="rangeDays" :options="rangeOptions" size="small" />
      </div>
    </template>

    <el-row :gutter="12">
      <el-col :span="6">
        <el-statistic title="今日番茄" :value="stats.today_pomodoros" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="本周番茄" :value="stats.week_pomodoros" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="专注分钟" :value="stats.total_focus_minutes" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="打断次数" :value="stats.interrupt_count" />
      </el-col>
    </el-row>

    <el-row :gutter="12" style="margin-top: 12px;">
      <el-col :span="8">
        <el-statistic title="待办总数" :value="stats.total_todos" />
      </el-col>
      <el-col :span="8">
        <el-statistic title="待办完成数" :value="stats.completed_todos" />
      </el-col>
      <el-col :span="8">
        <el-statistic title="待办完成率(%)" :value="stats.todo_completion_rate" />
      </el-col>
    </el-row>

    <el-divider content-position="center">最近专注会话</el-divider>
    <el-table :data="recentSessions" size="small" style="width: 100%" class="compact-table">
      <el-table-column prop="todo_title" label="待办" />
      <el-table-column prop="duration_minutes" label="分钟" width="90" />
      <el-table-column label="状态" width="90">
        <template #default="scope">
          {{ scope.row.status === 'completed' ? '完成' : '中断' }}
        </template>
      </el-table-column>
      <el-table-column label="结束时间" width="120">
        <template #default="scope">
          {{ formatDateTime(scope.row.end_time) }}
        </template>
      </el-table-column>
    </el-table>

    <el-divider content-position="center">历史完成曲线</el-divider>
    <div ref="trendRef" style="width: 92%; height: 280px; margin: 0 auto;"></div>
  </el-card>
</template>

<script setup>
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { fetchStats } from '../api/pomodoro'

const rangeDays = ref(null)
const rangeOptions = [
  { label: '近7天', value: 7 },
  { label: '近30天', value: 30 },
  { label: '全部', value: null }
]

const stats = ref({
  today_pomodoros: 0,
  week_pomodoros: 0,
  total_focus_minutes: 0,
  interrupt_count: 0,
  total_todos: 0,
  completed_todos: 0,
  todo_completion_rate: 0,
  recent_sessions: [],
  completion_trend: []
})

const trendRef = ref(null)
let chartInstance = null

const recentSessions = computed(() => (stats.value.recent_sessions || []).slice(0, 5))

function formatDateTime(value) {
  if (!value) {
    return '-'
  }
  const text = String(value)
  const datePart = text.slice(5, 10)
  const timePart = text.slice(11, 16)
  return `${datePart} ${timePart}`
}

function renderTrend() {
  if (!trendRef.value) {
    return
  }
  if (!chartInstance) {
    chartInstance = echarts.init(trendRef.value)
  }
  const xData = stats.value.completion_trend.map((item) => item.date)
  const yData = stats.value.completion_trend.map((item) => item.count)
  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: xData,
      boundaryGap: false,
      axisLabel: {
        formatter: (value) => value.slice(5),
        hideOverlap: true
      }
    },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        type: 'line',
        smooth: true,
        data: yData,
        areaStyle: {}
      }
    ],
    grid: { left: 36, right: 16, top: 20, bottom: 28, containLabel: true }
  })
}

function onResize() {
  if (chartInstance) {
    chartInstance.resize()
  }
}

async function loadStats() {
  const res = await fetchStats(rangeDays.value)
  stats.value = res.data
  await nextTick()
  renderTrend()
}

onMounted(async () => {
  await loadStats()
  window.addEventListener('resize', onResize)
})

watch(rangeDays, async () => {
  await loadStats()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.compact-table :deep(.el-table__cell) {
  padding-top: 6px;
  padding-bottom: 6px;
}
</style>
