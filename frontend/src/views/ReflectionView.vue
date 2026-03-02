<template>
  <el-card>
    <template #header>
      <div class="panel-header">
        <span>{{ isReflectionMode ? '心流感悟' : '个人计划安排' }}</span>
        <el-button text type="primary" @click="toggleMode">
          {{ isReflectionMode ? '切换到个人计划' : '切换到心流感悟' }}
        </el-button>
      </div>
    </template>

    <template v-if="isReflectionMode">
      <el-form @submit.prevent>
        <el-form-item>
          <el-input
            v-model="draft"
            type="textarea"
            :rows="4"
            placeholder="记录此刻的感悟..."
          />
        </el-form-item>
        <el-form-item>
          <div class="inline-actions">
            <el-button type="primary" @click="addReflection">保存感悟</el-button>
            <el-button :loading="polishingDraft" @click="polishDraftByAi">AI润色表达</el-button>
          </div>
        </el-form-item>
      </el-form>

      <el-divider>感悟列表</el-divider>

      <el-empty v-if="!records.length" description="还没有记录，写下第一条感悟吧" />

      <div v-else class="records-list">
        <el-card v-for="item in records" :key="item.id" shadow="never" class="record-item">
          <div class="record-head">
            <div class="record-time">{{ item.createdAtText }}</div>
            <div class="record-actions">
              <el-button text type="primary" @click="openEdit(item)">修改</el-button>
              <el-button text type="danger" @click="removeReflection(item)">删除</el-button>
            </div>
          </div>
          <div class="record-content">{{ item.content }}</div>
        </el-card>
      </div>
    </template>

    <template v-else>
      <el-form @submit.prevent>
        <el-form-item label="计划类型">
          <el-radio-group v-model="planKind">
            <el-radio-button label="short">短期计划</el-radio-button>
            <el-radio-button label="long">长期计划</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="卡片名字">
          <el-input v-model="planCardNameDraft" placeholder="输入计划卡片名字（不存在会自动新建）" style="width: 320px;" />
        </el-form-item>

        <template v-if="planKind === 'short'">
          <el-form-item label="日期选择">
            <el-date-picker
              v-model="shortPlanDatesDraft"
              type="dates"
              placeholder="选择若干日期"
              format="YYYY-MM-DD"
              style="width: 100%;"
            />
          </el-form-item>
          <el-form-item label="补充说明">
            <div class="note-wrap">
              <el-button text type="primary" @click="shortNoteExpanded = !shortNoteExpanded">
                {{ shortNoteExpanded ? '收起补充说明' : '展开补充说明' }}
              </el-button>
              <el-input
                v-model="shortPlanNoteDraft"
                type="textarea"
                :rows="shortNoteExpanded ? 10 : 3"
                :class="{ expanded: shortNoteExpanded }"
                placeholder="写具体安排，比如：哪天复习哪一章、哪天模拟考试"
              />
            </div>
          </el-form-item>
          <el-form-item>
            <div class="inline-actions">
              <el-button type="primary" @click="addShortPlan">添加短期计划</el-button>
            </div>
          </el-form-item>
        </template>

        <template v-else>
          <el-form-item>
            <div class="inline-actions">
              <el-button type="primary" @click="openLongPlanCreateDialog">添加长期计划</el-button>
            </div>
          </el-form-item>
          <el-alert
            type="info"
            :closable="false"
            title="长期计划通过弹窗维护：先写计划标题，再添加多个“时间段 + 具体事项”。"
          />
        </template>
      </el-form>
      <el-alert
        v-if="planAdviceText"
        type="info"
        :closable="false"
        title="AI计划建议"
        show-icon
        style="margin-bottom: 10px;"
      />
      <pre v-if="planAdviceText" class="advice-content">{{ planAdviceText }}</pre>
      <div class="plan-list-head">
        <span>计划列表</span>
        <el-button type="primary" plain size="small" @click="openSyncPlansDialog">选择同步到待办</el-button>
      </div>
      <el-divider style="margin-top: 8px;" />

      <el-empty v-if="!plans.length" description="还没有计划，先写一个小目标吧" />

      <div v-else class="records-list">
        <el-card
          v-for="card in planCardGroups"
          :key="card.id"
          shadow="never"
          :class="['record-item', 'plan-card', { 'plan-card-collapsed': !isPlanCardExpanded(card.id) }]"
        >
          <template #header>
            <div class="card-head-row">
              <div class="card-head-title">
                <span>{{ card.name }}</span>
                <el-tag size="small">{{ card.items.length }} 项</el-tag>
              </div>
              <div class="card-head-actions">
                <el-tooltip :content="isPlanCardExpanded(card.id) ? '收起' : '展开'" placement="top">
                  <el-button text type="primary" @click="togglePlanCardExpand(card.id)">
                    <el-icon><ArrowDown v-if="isPlanCardExpanded(card.id)" /><ArrowRight v-else /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="修改卡片名" placement="top">
                  <el-button text type="primary" @click="renamePlanCard(card)">
                    <el-icon><EditPen /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="删除卡片" placement="top">
                  <el-button text type="danger" @click="removePlanCard(card)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-tooltip>
              </div>
            </div>
          </template>
          <template v-if="isPlanCardExpanded(card.id)">
            <el-empty v-if="!card.items.length" description="该计划卡片暂无内容" />
            <div v-else class="records-list">
              <el-card v-for="item in card.items" :key="item.id" shadow="never" class="record-item">
              <div class="record-head">
                <div class="record-time">
                  {{ item.planType === 'long' ? '长期计划' : '短期计划' }}
                </div>
                <div class="record-actions plan-item-actions">
                  <el-tooltip content="修改" placement="top">
                    <el-button text type="primary" @click="openPlanEdit(item)">
                      <el-icon><EditPen /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip v-if="item.planType === 'long'" content="复制" placement="top">
                    <el-button text type="primary" @click="openPlanDuplicate(item)">
                      <el-icon><CopyDocument /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip :content="item.planType === 'long' ? 'AI优化' : 'AI建议'" placement="top">
                    <el-button text type="primary" :loading="planAdviceLoadingId === item.id" @click="generatePlanAdviceForItem(item)">
                      <el-icon><MagicStick /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="删除" placement="top">
                    <el-button text type="danger" @click="removePlan(item)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </el-tooltip>
                </div>
              </div>

              <div v-if="item.planType === 'short'" class="plan-meta">
                <div class="meta-label">日期：</div>
                <div class="date-tags">
                  <el-tag v-for="date in item.shortDates" :key="`${item.id}-${date}`" size="small">{{ date }}</el-tag>
                </div>
              </div>

              <div v-else class="plan-meta">
                <div class="time-grid">
                  <span v-for="segment in getLongPlanSegments(item)" :key="`${item.id}-${segment.id}`">
                    {{ segment.start }} - {{ segment.end }}：{{ segment.task }}
                  </span>
                </div>
              </div>

              <div v-if="item.note" class="record-content">{{ item.note }}</div>
              </el-card>
            </div>
          </template>
        </el-card>
      </div>
    </template>

    <el-dialog v-model="editDialogVisible" title="修改感悟" width="520px">
      <el-input
        v-model="editDraft"
        type="textarea"
        :rows="5"
        placeholder="请输入修改后的内容"
      />
      <template #footer>
        <el-button :loading="polishingEditDraft" @click="polishEditDraftByAi">AI润色表达</el-button>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="planEditDialogVisible"
      :title="planEditMode === 'duplicate'
        ? (planEditKind === 'long' ? '复制长期计划' : '复制短期计划')
        : (planEditKind === 'long' ? '修改长期计划' : '修改短期计划')"
      width="620px"
    >
      <template v-if="planEditKind === 'short'">
        <el-form @submit.prevent>
          <el-form-item label="卡片名字">
            <el-input v-model="editPlanCardName" placeholder="输入计划卡片名字（不存在会自动新建）" style="width: 320px;" />
          </el-form-item>
          <el-form-item label="日期选择">
            <el-date-picker
              v-model="editShortPlanDates"
              type="dates"
              placeholder="选择若干日期"
              format="YYYY-MM-DD"
              style="width: 100%;"
            />
          </el-form-item>
          <el-form-item label="补充说明">
            <el-input
              v-model="editShortPlanNote"
              type="textarea"
              :rows="8"
              placeholder="请输入补充说明"
            />
          </el-form-item>
        </el-form>
      </template>
      <template v-else>
        <el-form @submit.prevent>
          <el-form-item label="卡片名字">
            <el-input v-model="editPlanCardName" placeholder="输入计划卡片名字（不存在会自动新建）" style="width: 320px;" />
          </el-form-item>
          <div class="segment-list">
            <div v-for="(segment, index) in editLongPlanSegments" :key="segment.key" class="segment-row">
              <el-time-picker
                v-model="segment.timeRange"
                is-range
                format="HH:mm"
                value-format="HH:mm"
                range-separator="至"
                start-placeholder="开始"
                end-placeholder="结束"
                style="width: 240px;"
              />
              <el-input
                v-model="segment.task"
                placeholder="这段时间做什么事"
                style="flex: 1; min-width: 180px;"
              />
              <el-button text type="danger" @click="removeEditLongSegment(index)">删除</el-button>
            </div>
            <el-button plain @click="appendEditLongSegment">增加具体计划</el-button>
          </div>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="planEditDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePlanEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="syncDialogVisible" title="选择计划同步到待办" width="680px">
      <el-alert
        type="info"
        :closable="false"
        title="勾选后会在待办页创建任务。短期计划按计划同步；长期计划可按具体事件同步。"
        style="margin-bottom: 12px;"
      />
      <div class="inline-actions" style="margin-bottom: 10px;">
        <el-button size="small" @click="selectAllPlanCardsForSync">全选卡片</el-button>
        <el-button size="small" @click="clearPlanCardsForSync">全不选卡片</el-button>
        <el-button size="small" @click="selectAllSyncItems">全选项目</el-button>
        <el-button size="small" @click="clearAllSyncItems">全不选项目</el-button>
      </div>
      <el-form label-width="110px" style="margin-bottom: 10px;">
        <el-form-item label="同步计划卡片">
          <el-select
            v-model="selectedSyncPlanCardIds"
            multiple
            filterable
            collapse-tags
            collapse-tags-tooltip
            placeholder="下拉选择要同步的计划卡片"
            style="width: 100%;"
          >
            <el-option
              v-for="card in planCardGroups"
              :key="`sync-card-${card.id}`"
              :label="`${getPlanCardDisplayName(card)}（${card.items.length}项）`"
              :value="String(card.id)"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <el-form label-width="110px" style="margin-bottom: 10px;">
        <el-form-item
          v-for="card in getSelectedSyncPlanCards()"
          :key="`map-${card.id}`"
          :label="`${getPlanCardDisplayName(card)} ->`"
        >
          <div class="sync-map-row">
            <el-radio-group v-model="getSyncCardMapping(card.id).targetMode">
              <el-radio-button label="existing">现有卡片</el-radio-button>
              <el-radio-button label="new">新建卡片</el-radio-button>
            </el-radio-group>
            <el-select
              v-if="getSyncCardMapping(card.id).targetMode === 'existing'"
              v-model="getSyncCardMapping(card.id).targetCollectionId"
              placeholder="请选择待办卡片"
              style="width: 200px;"
            >
              <el-option
                v-for="item in syncCollections"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
            <el-input
              v-else
              v-model="getSyncCardMapping(card.id).newCollectionName"
              placeholder="留空自动命名待办卡片N"
              style="width: 200px;"
            />
          </div>
        </el-form-item>
      </el-form>
      <el-checkbox-group v-model="selectedSyncItems" class="sync-checklist">
        <el-card
          v-for="group in getSyncPlanGroups()"
          :key="`sync-group-${group.id}`"
          class="sync-item-card"
          shadow="never"
        >
          <template #header>
            <div class="card-head-row">
              <strong class="sync-group-title">卡片：{{ getSyncGroupDisplayName(group) }}</strong>
              <el-button text type="primary" @click="toggleSyncCardExpand(group.id)">
                {{ isSyncCardExpanded(group.id) ? '收起' : '展开' }}
              </el-button>
            </div>
          </template>
          <div v-if="isSyncCardExpanded(group.id)">
            <el-card
              v-for="item in group.items"
              :key="`sync-${item.id}`"
              class="sync-item-card"
              shadow="never"
              style="margin-bottom: 8px;"
            >
              <div class="sync-item-head">
                <template v-if="item.planType === 'short'">
                  <el-checkbox :value="`short:${item.id}`">
                    [短期] {{ item.title }}
                  </el-checkbox>
                </template>
                <template v-else>
                  <span>[长期] {{ item.title }}</span>
                </template>
              </div>
              <div v-if="item.planType === 'short'" class="sync-item-meta">
                {{ Array.isArray(item.shortDates) ? item.shortDates.join('、') : '' }}
              </div>
              <div v-else class="sync-item-meta">
                <div class="long-segment-checks">
                  <el-checkbox
                    v-for="segment in getLongPlanSegments(item)"
                    :key="`sync-seg-${item.id}-${segment.id}`"
                    :value="`long:${item.id}:${segment.id}`"
                  >
                    {{ segment.start }} - {{ segment.end }}：{{ segment.task }}
                  </el-checkbox>
                </div>
              </div>
            </el-card>
          </div>
        </el-card>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="syncDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="syncingPlans" @click="syncSelectedPlansToTodos">同步到待办</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="longPlanCreateDialogVisible" title="添加长期计划" width="720px">
      <el-form @submit.prevent>
        <el-form-item label="卡片名字">
          <el-input v-model="planCardNameDraft" placeholder="输入计划卡片名字（不存在会自动新建）" style="width: 320px;" />
        </el-form-item>
        <div class="segment-list">
          <div v-for="(segment, index) in longPlanSegmentsDraft" :key="segment.key" class="segment-row">
            <el-time-picker
              v-model="segment.timeRange"
              is-range
              format="HH:mm"
              value-format="HH:mm"
              range-separator="至"
              start-placeholder="开始"
              end-placeholder="结束"
              style="width: 240px;"
            />
            <el-input
              v-model="segment.task"
              placeholder="这段时间做什么事"
              style="flex: 1; min-width: 180px;"
            />
            <el-button text type="danger" @click="removeLongSegmentDraft(index)">删除</el-button>
          </div>
          <el-button plain @click="appendLongSegmentDraft">增加具体计划</el-button>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="longPlanCreateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addLongPlan">保存长期计划</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="longPlanAdviceDialogVisible" title="长期计划 AI 优化建议" width="760px">
      <el-alert
        type="info"
        :closable="false"
        title="勾选你认可的建议后，可一键应用到当前长期计划。"
        style="margin-bottom: 10px;"
      />
      <pre v-if="longPlanAdviceRawText" class="advice-content">{{ longPlanAdviceRawText }}</pre>
      <el-empty v-if="!longPlanAdviceOptions.length" description="暂无可应用的结构化建议，可参考上方文字手动调整。" />
      <el-checkbox-group v-else v-model="selectedLongPlanAdviceIds" class="sync-checklist">
        <el-card
          v-for="option in longPlanAdviceOptions"
          :key="option.id"
          class="sync-item-card"
          shadow="never"
        >
          <div class="sync-item-head">
            <el-checkbox :value="option.id">
              {{ option.before.start }}-{{ option.before.end }} {{ option.before.task }}
              -> {{ option.after.start }}-{{ option.after.end }} {{ option.after.task }}
            </el-checkbox>
          </div>
          <div class="sync-item-meta">{{ option.reason || 'AI建议调整该时间段计划。' }}</div>
        </el-card>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="longPlanAdviceDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!longPlanAdviceOptions.length" @click="applySelectedLongPlanAdvice">应用选中建议</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ArrowDown, ArrowRight, CopyDocument, Delete, EditPen, MagicStick } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createCollection, createTodo, fetchCollections, generateAiAdvice, optimizeAiPlan } from '../api/pomodoro'

const REFLECTION_STORAGE_KEY = 'pomodoro-reflections-v1'
const PLAN_STORAGE_KEY = 'pomodoro-plans-v2'
const PLAN_CARD_STORAGE_KEY = 'pomodoro-plan-cards-v1'

const isReflectionMode = ref(true)

const draft = ref('')
const records = ref([])
const editDialogVisible = ref(false)
const editDraft = ref('')
const editingId = ref(null)

const planKind = ref('short')
const planCardNameDraft = ref('')
const shortPlanDatesDraft = ref([])
const shortPlanNoteDraft = ref('')
const shortNoteExpanded = ref(false)

const longPlanSegmentsDraft = ref([])
const longPlanCreateDialogVisible = ref(false)

const plans = ref([])
const planEditDialogVisible = ref(false)
const planEditingId = ref(null)
const planEditKind = ref('short')
const planEditMode = ref('edit')
const editPlanCardName = ref('')
const editShortPlanDates = ref([])
const editShortPlanNote = ref('')
const editLongPlanSegments = ref([])
const polishingDraft = ref(false)
const polishingEditDraft = ref(false)
const planAdviceLoadingId = ref(null)
const planAdviceText = ref('')
const syncDialogVisible = ref(false)
const selectedSyncItems = ref([])
const selectedSyncPlanCardIds = ref([])
const syncExpandedCardIds = ref([])
const syncingPlans = ref(false)
const syncCollections = ref([])
const syncCardMappings = ref([])
const longPlanAdviceDialogVisible = ref(false)
const longPlanAdvicePlanId = ref(null)
const longPlanAdviceRawText = ref('')
const longPlanAdviceOptions = ref([])
const selectedLongPlanAdviceIds = ref([])
const planCards = ref([])
const expandedPlanCardIds = ref([])

const planCardGroups = computed(() => {
  return planCards.value.map((card) => ({
    ...card,
    items: plans.value.filter((plan) => String(plan.planCardId) === String(card.id))
  }))
})

function syncExpandedPlanCards() {
  const ids = planCardGroups.value.map((card) => String(card.id))
  if (!ids.length) {
    expandedPlanCardIds.value = []
    return
  }
  if (!expandedPlanCardIds.value.length) {
    expandedPlanCardIds.value = [...ids]
    return
  }
  const known = new Set(expandedPlanCardIds.value.map((id) => String(id)))
  for (const id of ids) {
    known.add(id)
  }
  expandedPlanCardIds.value = ids.filter((id) => known.has(id))
}

function isPlanCardExpanded(cardId) {
  return expandedPlanCardIds.value.includes(String(cardId))
}

function togglePlanCardExpand(cardId) {
  const key = String(cardId)
  if (isPlanCardExpanded(key)) {
    expandedPlanCardIds.value = expandedPlanCardIds.value.filter((item) => item !== key)
    return
  }
  expandedPlanCardIds.value = [...expandedPlanCardIds.value, key]
}

function toggleMode() {
  isReflectionMode.value = !isReflectionMode.value
}

function toDisplayTime(date) {
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

function saveRecords() {
  localStorage.setItem(REFLECTION_STORAGE_KEY, JSON.stringify(records.value))
}

function loadRecords() {
  const raw = localStorage.getItem(REFLECTION_STORAGE_KEY)
  if (!raw) {
    records.value = []
    return
  }
  try {
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) {
      records.value = []
      return
    }
    records.value = parsed
      .filter((item) => item && item.id && item.content && item.createdAtText)
      .sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)))
  } catch {
    records.value = []
  }
}

function addReflection() {
  const content = draft.value.trim()
  if (!content) {
    ElMessage.warning('请输入感悟内容')
    return
  }

  const now = new Date()
  records.value.unshift({
    id: `${now.getTime()}-${Math.random().toString(16).slice(2, 8)}`,
    content,
    createdAt: now.toISOString(),
    createdAtText: toDisplayTime(now)
  })
  saveRecords()
  draft.value = ''
  ElMessage.success('已记录')
}

function openEdit(item) {
  editingId.value = item.id
  editDraft.value = item.content
  editDialogVisible.value = true
}

function saveEdit() {
  const content = editDraft.value.trim()
  if (!content) {
    ElMessage.warning('请输入感悟内容')
    return
  }

  const index = records.value.findIndex((item) => item.id === editingId.value)
  if (index < 0) {
    editDialogVisible.value = false
    return
  }

  records.value[index] = {
    ...records.value[index],
    content
  }
  saveRecords()
  editDialogVisible.value = false
  ElMessage.success('已修改')
}

async function removeReflection(item) {
  try {
    await ElMessageBox.confirm('确认删除这条感悟吗？', '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }

  records.value = records.value.filter((entry) => entry.id !== item.id)
  saveRecords()
  ElMessage.success('已删除')
}

function savePlans() {
  localStorage.setItem(PLAN_STORAGE_KEY, JSON.stringify(plans.value))
}

function savePlanCards() {
  localStorage.setItem(PLAN_CARD_STORAGE_KEY, JSON.stringify(planCards.value))
}

function nextDefaultPlanCardName() {
  let maxIndex = 0
  for (const item of planCards.value) {
    const match = /^计划卡片(\d+)$/.exec(String(item?.name || '').trim())
    if (!match) {
      continue
    }
    maxIndex = Math.max(maxIndex, Number(match[1]))
  }
  return `计划卡片${maxIndex + 1}`
}

function createPlanCard(name = '') {
  const card = {
    id: `pc-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
    name: String(name || '').trim() || nextDefaultPlanCardName()
  }
  planCards.value.push(card)
  savePlanCards()
  return card
}

function ensureDefaultPlanCard() {
  if (planCards.value.length > 0) {
    return
  }
  createPlanCard(nextDefaultPlanCardName())
}

function findPlanCardByName(name) {
  const target = String(name || '').trim()
  if (!target) {
    return null
  }
  return planCards.value.find((item) => String(item.name || '').trim() === target) || null
}

function ensurePlanCardIdByName(name) {
  const target = String(name || '').trim()
  if (!target) {
    return null
  }
  const found = findPlanCardByName(target)
  if (found) {
    return found.id
  }
  const created = createPlanCard(target)
  return created.id
}

function getPlanCardNameById(planCardId) {
  return planCards.value.find((item) => String(item.id) === String(planCardId))?.name || ''
}

function getPlanCardDisplayName(card) {
  const name = String(card?.name || '').trim()
  if (name) {
    return name
  }
  return '未命名卡片'
}

function getSyncGroupDisplayName(group) {
  const byId = planCardGroups.value.find((card) => String(card.id) === String(group?.id))
  if (byId) {
    return getPlanCardDisplayName(byId)
  }
  return getPlanCardDisplayName(group)
}

function createSegmentId() {
  return `seg-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`
}

function createPlanSegment(start = '', end = '', task = '', id = '') {
  return {
    key: `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
    id: id || createSegmentId(),
    timeRange: start && end ? [start, end] : [],
    task
  }
}

function normalizePlanSegments(segments) {
  if (!Array.isArray(segments)) {
    return []
  }
  return segments
    .map((item) => {
      const start = typeof item?.start === 'string' ? item.start.slice(0, 5) : ''
      const end = typeof item?.end === 'string' ? item.end.slice(0, 5) : ''
      const task = String(item?.task || '').trim()
      const id = typeof item?.id === 'string' && item.id ? item.id : createSegmentId()
      if (!start || !end || !task) {
        return null
      }
      return { id, start, end, task }
    })
    .filter(Boolean)
}

function convertLegacyRoutineToSegments(routine) {
  if (!routine || typeof routine !== 'object') {
    return []
  }
  const segments = []
  if (routine.wakeTime) {
    segments.push({ start: routine.wakeTime, end: routine.wakeTime, task: '起床' })
  }
  if (Array.isArray(routine.breakfastRange) && routine.breakfastRange.length === 2) {
    segments.push({ start: routine.breakfastRange[0], end: routine.breakfastRange[1], task: '早餐' })
  }
  if (Array.isArray(routine.lunchRange) && routine.lunchRange.length === 2) {
    segments.push({ start: routine.lunchRange[0], end: routine.lunchRange[1], task: '午餐' })
  }
  if (Array.isArray(routine.dinnerRange) && routine.dinnerRange.length === 2) {
    segments.push({ start: routine.dinnerRange[0], end: routine.dinnerRange[1], task: '晚餐' })
  }
  return normalizePlanSegments(segments)
}

function getLongPlanSegments(item) {
  const routine = item?.longRoutine
  if (!routine || typeof routine !== 'object') {
    return []
  }
  const modernSegments = normalizePlanSegments(routine.segments)
  if (modernSegments.length) {
    return modernSegments
  }
  return convertLegacyRoutineToSegments(routine)
}

function clampTodoTitle(input) {
  const text = String(input || '').trim()
  if (!text) {
    return ''
  }
  return text.length <= 100 ? text : `${text.slice(0, 97)}...`
}

function diffMinutesFromRange(startText, endText) {
  const [sh, sm] = String(startText || '').split(':').map((item) => Number(item))
  const [eh, em] = String(endText || '').split(':').map((item) => Number(item))
  if (![sh, sm, eh, em].every(Number.isFinite)) {
    return 25
  }
  let delta = (eh * 60 + em) - (sh * 60 + sm)
  if (delta <= 0) {
    delta += 24 * 60
  }
  return Math.max(1, Math.min(180, delta))
}

async function polishTextWithAi(rawText) {
  const input = String(rawText || '').trim()
  if (!input) {
    return ''
  }
  const res = await generateAiAdvice({
    days: 30,
    prompt: `请把下面这段感悟润色成更清晰、完整、自然的中文表达。保持原意，不要编造信息。只输出润色后的正文，不要标题和解释。\n\n${input}`
  })
  const output = String(res?.data?.advice || '').trim()
  return output || input
}

async function polishDraftByAi() {
  const input = draft.value.trim()
  if (!input) {
    ElMessage.warning('请先输入感悟内容')
    return
  }
  polishingDraft.value = true
  try {
    draft.value = await polishTextWithAi(input)
    ElMessage.success('AI 已润色当前感悟')
  } finally {
    polishingDraft.value = false
  }
}

async function polishEditDraftByAi() {
  const input = editDraft.value.trim()
  if (!input) {
    ElMessage.warning('请先输入感悟内容')
    return
  }
  polishingEditDraft.value = true
  try {
    editDraft.value = await polishTextWithAi(input)
    ElMessage.success('AI 已润色当前感悟')
  } finally {
    polishingEditDraft.value = false
  }
}

function buildPlanDraftSummary() {
  if (planKind.value === 'short') {
    const dates = Array.isArray(shortPlanDatesDraft.value)
      ? shortPlanDatesDraft.value.map((item) => normalizeDateValue(item)).filter(Boolean)
      : []
    return [
      '计划类型：短期计划',
      `标题：${shortPlanTitleDraft.value || '(未填写)'}`,
      `日期：${dates.length ? dates.join('、') : '(未选择)'}`,
      `补充说明：${shortPlanNoteDraft.value || '(无)'}`
    ].join('\n')
  }
  const segments = normalizePlanSegments(
    longPlanSegmentsDraft.value.map((item) => {
      const start = Array.isArray(item.timeRange) && item.timeRange.length === 2 ? item.timeRange[0] : ''
      const end = Array.isArray(item.timeRange) && item.timeRange.length === 2 ? item.timeRange[1] : ''
      return {
        id: item.id,
        start,
        end,
        task: item.task
      }
    })
  )
  return [
    '计划类型：长期计划',
    `卡片名字：${planCardNameDraft.value || '(未填写)'}`,
    `具体计划：${segments.length ? segments.map((segment) => `${segment.start}-${segment.end} ${segment.task}`).join('；') : '(未填写)'}`
  ].join('\n')
}

function buildPlanItemSummary(item) {
  if (item.planType === 'short') {
    const dates = Array.isArray(item.shortDates) ? item.shortDates : []
    return [
      '计划类型：短期计划',
      `标题：${item.title || ''}`,
      `日期：${dates.length ? dates.join('、') : '(未设置)'}`,
      `补充说明：${item.note || '(无)'}`
    ].join('\n')
  }
  const segments = getLongPlanSegments(item)
  return [
    '计划类型：长期计划',
    `标题：${item.title || ''}`,
    `具体计划：${segments.length ? segments.map((segment) => `${segment.start}-${segment.end} ${segment.task}`).join('；') : '(未设置)'}`,
    `补充说明：${item.note || '(无)'}`
  ].join('\n')
}

async function generatePlanAdviceFromDraft() {
  if (planKind.value === 'long') {
    const cardName = planCardNameDraft.value.trim()
    const segments = normalizePlanSegments(
      longPlanSegmentsDraft.value.map((item) => {
        const start = Array.isArray(item.timeRange) && item.timeRange.length === 2 ? item.timeRange[0] : ''
        const end = Array.isArray(item.timeRange) && item.timeRange.length === 2 ? item.timeRange[1] : ''
        return { start, end, task: item.task }
      })
    )
    if (!cardName || !segments.length) {
      ElMessage.warning('请先填写卡片名字和至少一条具体计划')
      return
    }
  }
  planAdviceText.value = '请使用每条计划右侧的 AI建议/AI优化。'
}

async function generatePlanAdviceForItem(item) {
  if (item.planType === 'long') {
    await generateLongPlanAdvice(item)
    return
  }
  planAdviceLoadingId.value = item.id
  try {
    const res = await generateAiAdvice({
      days: 30,
      prompt: `你是时间管理教练。请针对下面这条计划给出优化建议，重点包含：\n1) 需要补充的任务\n2) 时间安排调整建议\n3) 可落地的执行步骤\n请用中文给出条目化建议。\n\n${buildPlanItemSummary(item)}`
    })
    planAdviceText.value = String(res?.data?.advice || '').trim()
    if (!planAdviceText.value) {
      planAdviceText.value = '暂未生成建议，请稍后重试。'
    }
  } finally {
    planAdviceLoadingId.value = null
  }
}

function buildLongPlanAdviceOptions(suggestions, plan) {
  const segments = getLongPlanSegments(plan)
  const options = []
  ;(Array.isArray(suggestions) ? suggestions : []).forEach((item, index) => {
    const segmentId = String(item?.segment_id || '')
    const before = segments.find((segment) => segment.id === segmentId)
    if (!before) {
      return
    }
    const nextStart = typeof item?.suggested_start === 'string' ? item.suggested_start.slice(0, 5) : ''
    const nextEnd = typeof item?.suggested_end === 'string' ? item.suggested_end.slice(0, 5) : ''
    const nextTask = String(item?.suggested_task || '').trim()
    if (!nextStart || !nextEnd || !nextTask) {
      return
    }
    options.push({
      id: `advice-${index}-${segmentId}`,
      segmentId,
      before,
      after: {
        id: segmentId,
        start: nextStart,
        end: nextEnd,
        task: nextTask
      },
      reason: String(item?.reason || '').trim() || 'AI建议优化该事件安排。'
    })
  })
  return options
}

async function generateLongPlanAdvice(plan) {
  const segments = getLongPlanSegments(plan)
  if (!segments.length) {
    ElMessage.warning('该长期计划还没有具体事件')
    return
  }

  planAdviceLoadingId.value = plan.id
  try {
    const res = await optimizeAiPlan({
      title: plan.title,
      segments: segments.map((segment) => ({
        id: segment.id,
        start: segment.start,
        end: segment.end,
        task: segment.task
      }))
    })
    const data = res?.data || {}
    const options = buildLongPlanAdviceOptions(data.suggestions, plan)

    longPlanAdvicePlanId.value = plan.id
    longPlanAdviceRawText.value = String(data.raw_advice || data.reason || '').trim()
    longPlanAdviceOptions.value = options
    selectedLongPlanAdviceIds.value = options.map((item) => item.id)
    longPlanAdviceDialogVisible.value = true
  } finally {
    planAdviceLoadingId.value = null
  }
}

function applySelectedLongPlanAdvice() {
  const planIndex = plans.value.findIndex((item) => item.id === longPlanAdvicePlanId.value)
  if (planIndex < 0) {
    longPlanAdviceDialogVisible.value = false
    return
  }
  const selected = longPlanAdviceOptions.value.filter((item) => selectedLongPlanAdviceIds.value.includes(item.id))
  if (!selected.length) {
    ElMessage.warning('请至少勾选一条建议')
    return
  }

  const currentSegments = getLongPlanSegments(plans.value[planIndex])
  const nextSegments = currentSegments.map((segment) => {
    const found = selected.find((item) => item.segmentId === segment.id)
    return found ? found.after : segment
  })

  plans.value[planIndex] = {
    ...plans.value[planIndex],
    longRoutine: {
      segments: normalizePlanSegments(nextSegments)
    }
  }
  savePlans()
  longPlanAdviceDialogVisible.value = false
  ElMessage.success(`已应用 ${selected.length} 条 AI 建议`)
}

function openSyncPlansDialog() {
  if (!plans.value.length) {
    ElMessage.warning('当前没有可同步的计划')
    return
  }
  void prepareSyncDialog()
}

async function loadSyncCollections() {
  const res = await fetchCollections()
  syncCollections.value = Array.isArray(res.data) ? res.data : []
}

function nextDefaultCardNameForSync() {
  let maxIndex = 0
  for (const item of syncCollections.value) {
    const match = /^待办卡片(\d+)$/.exec(String(item.name || '').trim())
    if (!match) {
      continue
    }
    maxIndex = Math.max(maxIndex, Number(match[1]))
  }
  return `待办卡片${maxIndex + 1}`
}

async function prepareSyncDialog() {
  await loadSyncCollections()
  if (!syncCollections.value.length) {
    await createCollection({ name: nextDefaultCardNameForSync() })
    await loadSyncCollections()
  }
  selectAllPlanCardsForSync()
  syncCardMappings.value = planCardGroups.value.map((card) => ({
    planCardId: String(card.id),
    targetMode: 'existing',
    targetCollectionId: syncCollections.value[0]?.id ?? null,
    newCollectionName: ''
  }))
  selectAllSyncItems()
  syncDialogVisible.value = true
}

function selectAllPlanCardsForSync() {
  selectedSyncPlanCardIds.value = planCardGroups.value.map((card) => String(card.id))
}

function clearPlanCardsForSync() {
  selectedSyncPlanCardIds.value = []
}

function getSelectedSyncPlanCards() {
  return planCardGroups.value.filter((card) => selectedSyncPlanCardIds.value.includes(String(card.id)))
}

function getSyncPlansBySelectedCards() {
  return plans.value.filter((item) => selectedSyncPlanCardIds.value.includes(String(item.planCardId)))
}

function getSyncPlanGroups() {
  return planCardGroups.value
    .filter((card) => selectedSyncPlanCardIds.value.includes(String(card.id)))
    .map((card) => ({
      id: String(card.id),
      name: getPlanCardDisplayName(card),
      items: card.items
    }))
}

function isSyncCardExpanded(cardId) {
  return syncExpandedCardIds.value.includes(String(cardId))
}

function toggleSyncCardExpand(cardId) {
  const key = String(cardId)
  if (isSyncCardExpanded(key)) {
    syncExpandedCardIds.value = syncExpandedCardIds.value.filter((item) => item !== key)
    return
  }
  syncExpandedCardIds.value = [...syncExpandedCardIds.value, key]
}

function syncSyncExpandedCards() {
  const selected = selectedSyncPlanCardIds.value.map((id) => String(id))
  if (!selected.length) {
    syncExpandedCardIds.value = []
    return
  }
  if (!syncExpandedCardIds.value.length) {
    syncExpandedCardIds.value = [...selected]
    return
  }
  const keep = new Set(syncExpandedCardIds.value.map((id) => String(id)))
  syncExpandedCardIds.value = selected.filter((id) => keep.has(id))
}

function getSyncCardMapping(planCardId) {
  const key = String(planCardId)
  let found = syncCardMappings.value.find((item) => String(item.planCardId) === key)
  if (!found) {
    found = {
      planCardId: key,
      targetMode: 'existing',
      targetCollectionId: syncCollections.value[0]?.id ?? null,
      newCollectionName: ''
    }
    syncCardMappings.value.push(found)
  }
  return found
}

function selectAllSyncItems() {
  const defaults = []
  for (const item of getSyncPlansBySelectedCards()) {
    if (item.planType === 'short') {
      defaults.push(`short:${item.id}`)
    } else {
      for (const segment of getLongPlanSegments(item)) {
        defaults.push(`long:${item.id}:${segment.id}`)
      }
    }
  }
  selectedSyncItems.value = defaults
}

function clearAllSyncItems() {
  selectedSyncItems.value = []
}

async function ensureSyncTargetCollectionIdByPlanCard(planCardId) {
  const mapping = getSyncCardMapping(planCardId)
  if (mapping.targetMode === 'existing') {
    if (mapping.targetCollectionId == null) {
      ElMessage.warning('请为每个计划卡片选择目标待办卡片')
      return null
    }
    return mapping.targetCollectionId
  }
  const rawName = String(mapping.newCollectionName || '').trim()
  const name = rawName || nextDefaultCardNameForSync()
  const res = await createCollection({ name })
  const nextId = res?.data?.id ?? null
  await loadSyncCollections()
  mapping.targetCollectionId = nextId
  mapping.targetMode = 'existing'
  mapping.newCollectionName = ''
  return nextId
}

function buildTodoFromPlan(item) {
  const defaultPayload = {
    estimated_pomodoros: 1,
    timer_mode: 'countdown',
    focus_minutes: 25,
    collection_id: null
  }

  if (item.planType === 'short') {
    const dates = Array.isArray(item.shortDates) ? item.shortDates.slice(0, 4) : []
    const dateText = dates.length ? `（${dates.join('、')}）` : ''
    return {
      ...defaultPayload,
      title: clampTodoTitle(`${item.title}${dateText}`),
      estimated_pomodoros: Math.max(1, Math.min(20, (Array.isArray(item.shortDates) ? item.shortDates.length : 1) || 1)),
      focus_minutes: 35
    }
  }

  const segments = getLongPlanSegments(item)
  const suffix = segments.length
    ? `（${segments.slice(0, 3).map((segment) => `${segment.start}-${segment.end} ${segment.task}`).join('，')}）`
    : ''
  return {
    ...defaultPayload,
    title: clampTodoTitle(`${item.title}${suffix}`),
    estimated_pomodoros: 2,
    focus_minutes: 30
  }
}

async function syncSelectedPlansToTodos() {
  if (!selectedSyncPlanCardIds.value.length) {
    ElMessage.warning('请至少勾选一个计划卡片')
    return
  }
  if (!selectedSyncItems.value.length) {
    ElMessage.warning('请至少勾选一条计划或事件')
    return
  }

  const todoPayloads = []
  for (const token of selectedSyncItems.value) {
    const parts = String(token).split(':')
    if (parts[0] === 'short' && parts.length === 2) {
      const planId = parts[1]
      const plan = plans.value.find((item) => String(item.id) === planId && item.planType === 'short')
      if (plan && selectedSyncPlanCardIds.value.includes(String(plan.planCardId))) {
        todoPayloads.push({ payload: buildTodoFromPlan(plan), planCardId: String(plan.planCardId) })
      }
      continue
    }
    if (parts[0] === 'long' && parts.length === 3) {
      const planId = parts[1]
      const segmentId = parts[2]
      const plan = plans.value.find((item) => String(item.id) === planId && item.planType === 'long')
      if (!plan) {
        continue
      }
      const segment = getLongPlanSegments(plan).find((item) => item.id === segmentId)
      if (!segment) {
        continue
      }
      if (!selectedSyncPlanCardIds.value.includes(String(plan.planCardId))) {
        continue
      }
      todoPayloads.push({
        payload: {
          estimated_pomodoros: 1,
          timer_mode: 'countdown',
          focus_minutes: diffMinutesFromRange(segment.start, segment.end),
          collection_id: null,
          title: clampTodoTitle(`${segment.task}（${segment.start}-${segment.end}）`)
        },
        planCardId: String(plan.planCardId)
      })
    }
  }

  if (!todoPayloads.length) {
    ElMessage.warning('未找到可同步的计划或事件，请重试')
    return
  }

  syncingPlans.value = true
  try {
    const collectionIdByPlanCard = {}
    for (const planCardId of selectedSyncPlanCardIds.value) {
      const collectionId = await ensureSyncTargetCollectionIdByPlanCard(planCardId)
      if (collectionId == null) {
        syncingPlans.value = false
        return
      }
      collectionIdByPlanCard[String(planCardId)] = collectionId
    }

    await Promise.all(
      todoPayloads.map((entry) =>
        createTodo({
          ...entry.payload,
          collection_id: collectionIdByPlanCard[String(entry.planCardId)] ?? null
        })
      )
    )
    syncDialogVisible.value = false
    ElMessage.success(`已同步 ${todoPayloads.length} 条待办`)
  } finally {
    syncingPlans.value = false
  }
}

function normalizeDateValue(value) {
  if (!value) {
    return ''
  }
  if (typeof value === 'string') {
    return value.slice(0, 10)
  }
  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    return value.toISOString().slice(0, 10)
  }
  return ''
}

function addShortPlan() {
  const cardName = planCardNameDraft.value.trim()
  const planCardId = ensurePlanCardIdByName(cardName)
  const selectedDates = Array.isArray(shortPlanDatesDraft.value)
    ? shortPlanDatesDraft.value.map((item) => normalizeDateValue(item)).filter(Boolean)
    : []

  if (!cardName || !planCardId) {
    ElMessage.warning('请输入计划卡片名字')
    return
  }
  if (!selectedDates.length) {
    ElMessage.warning('请至少选择一个日期')
    return
  }

  const now = new Date()
  plans.value.unshift({
    id: `${now.getTime()}-${Math.random().toString(16).slice(2, 8)}`,
    planType: 'short',
    planCardId,
    title: cardName,
    note: shortPlanNoteDraft.value.trim(),
    shortDates: [...new Set(selectedDates)].sort(),
    longRoutine: {},
    done: false,
    createdAt: now.toISOString()
  })
  savePlans()
  shortPlanTitleDraft.value = ''
  shortPlanDatesDraft.value = []
  shortPlanNoteDraft.value = ''
  shortNoteExpanded.value = false
  ElMessage.success('短期计划已添加')
}

function hasLongSegments(segments) {
  return Array.isArray(segments) && segments.length > 0
}

function appendLongSegmentDraft() {
  longPlanSegmentsDraft.value.push(createPlanSegment())
}

function removeLongSegmentDraft(index) {
  longPlanSegmentsDraft.value.splice(index, 1)
}

function appendEditLongSegment() {
  editLongPlanSegments.value.push(createPlanSegment())
}

function removeEditLongSegment(index) {
  editLongPlanSegments.value.splice(index, 1)
}

function openLongPlanCreateDialog() {
  if (!planCardNameDraft.value && planCards.value.length) {
    planCardNameDraft.value = planCards.value[0].name
  }
  longPlanSegmentsDraft.value = [createPlanSegment()]
  longPlanCreateDialogVisible.value = true
}

function addLongPlan() {
  const cardName = planCardNameDraft.value.trim()
  const planCardId = ensurePlanCardIdByName(cardName)
  const segments = normalizePlanSegments(
    longPlanSegmentsDraft.value.map((item) => {
      const start = Array.isArray(item.timeRange) && item.timeRange.length === 2 ? item.timeRange[0] : ''
      const end = Array.isArray(item.timeRange) && item.timeRange.length === 2 ? item.timeRange[1] : ''
      return {
        start,
        end,
        task: item.task
      }
    })
  )

  if (!cardName || !planCardId) {
    ElMessage.warning('请输入计划卡片名字')
    return
  }
  if (!hasLongSegments(segments)) {
    ElMessage.warning('请至少添加一条“时间段 + 事项”')
    return
  }

  const now = new Date()
  plans.value.unshift({
    id: `${now.getTime()}-${Math.random().toString(16).slice(2, 8)}`,
    planType: 'long',
    planCardId,
    title: cardName,
    note: '',
    shortDates: [],
    longRoutine: {
      segments
    },
    done: false,
    createdAt: now.toISOString()
  })
  savePlans()
  longPlanSegmentsDraft.value = []
  longPlanCreateDialogVisible.value = false
  ElMessage.success('长期计划已添加')
}

function normalizePlanItem(item) {
  if (!item || !item.id || !item.title) {
    return null
  }

  const planType = item.planType === 'long' ? 'long' : 'short'
  const shortDates = Array.isArray(item.shortDates)
    ? item.shortDates.map((date) => normalizeDateValue(date)).filter(Boolean)
    : (item.targetDate ? [normalizeDateValue(item.targetDate)].filter(Boolean) : [])
  const longRoutine = item.longRoutine && typeof item.longRoutine === 'object'
    ? {
      segments: (() => {
        const modern = normalizePlanSegments(item.longRoutine.segments)
        if (modern.length) {
          return modern
        }
        return convertLegacyRoutineToSegments(item.longRoutine)
      })()
    }
    : { segments: [] }

  return {
    id: item.id,
    planType,
    planCardId: item.planCardId || item.plan_card_id || null,
    title: item.title,
    note: item.note || '',
    shortDates,
    longRoutine,
    done: Boolean(item.done),
    createdAt: item.createdAt || new Date().toISOString()
  }
}

function loadPlanCards() {
  const raw = localStorage.getItem(PLAN_CARD_STORAGE_KEY)
  if (!raw) {
    planCards.value = []
    return
  }
  try {
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) {
      planCards.value = []
      return
    }
    planCards.value = parsed
      .map((item) => {
        if (!item || !item.id || !item.name) {
          return null
        }
        return {
          id: String(item.id),
          name: String(item.name)
        }
      })
      .filter(Boolean)
  } catch {
    planCards.value = []
  }
}

function loadPlans() {
  const raw = localStorage.getItem(PLAN_STORAGE_KEY) || localStorage.getItem('pomodoro-plans-v1')
  if (!raw) {
    plans.value = []
    return
  }
  try {
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) {
      plans.value = []
      return
    }
    plans.value = parsed
      .map((item) => normalizePlanItem(item))
      .filter(Boolean)
      .sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)))
    const fallbackCardId = planCards.value[0]?.id || null
    plans.value = plans.value.map((item) => ({
      ...item,
      planCardId: item.planCardId || fallbackCardId
    }))
  } catch {
    plans.value = []
  }
}

async function removePlanCard(card) {
  const relatedCount = plans.value.filter((item) => String(item.planCardId) === String(card.id)).length
  try {
    await ElMessageBox.confirm(
      `确认删除卡片“${card.name}”吗？该卡片下 ${relatedCount} 条计划会一起删除。`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )
  } catch {
    return
  }

  planCards.value = planCards.value.filter((item) => String(item.id) !== String(card.id))
  plans.value = plans.value.filter((item) => String(item.planCardId) !== String(card.id))
  savePlanCards()
  savePlans()
  ensureDefaultPlanCard()
  syncExpandedPlanCards()
  if (!findPlanCardByName(planCardNameDraft.value)) {
    planCardNameDraft.value = planCards.value[0]?.name || ''
  }
  ElMessage.success('计划卡片已删除')
}

async function renamePlanCard(card) {
  const cardId = String(card?.id || '')
  const oldName = String(card?.name || '').trim()
  let promptResult
  try {
    promptResult = await ElMessageBox.prompt('请输入新的计划卡片名称', '修改卡片名', {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputValue: oldName,
      inputValidator: (value) => {
        const nextName = String(value || '').trim()
        if (!nextName) {
          return '请输入计划卡片名字'
        }
        const existed = planCards.value.find(
          (item) => String(item.id) !== cardId && String(item.name || '').trim() === nextName
        )
        if (existed) {
          return '该卡片名已存在'
        }
        return true
      }
    })
  } catch {
    return
  }

  const nextName = String(promptResult?.value || '').trim()
  if (!nextName || nextName === oldName) {
    return
  }

  const index = planCards.value.findIndex((item) => String(item.id) === cardId)
  if (index < 0) {
    return
  }

  planCards.value[index] = {
    ...planCards.value[index],
    name: nextName
  }
  savePlanCards()
  if (String(planCardNameDraft.value || '').trim() === oldName) {
    planCardNameDraft.value = nextName
  }
  ElMessage.success('计划卡片名已修改')
}

function openPlanEdit(item) {
  planEditMode.value = 'edit'
  planEditingId.value = item.id
  planEditKind.value = item.planType === 'long' ? 'long' : 'short'
  editPlanCardName.value = getPlanCardNameById(item.planCardId) || item.title || ''

  if (planEditKind.value === 'short') {
    editShortPlanDates.value = Array.isArray(item.shortDates) ? [...item.shortDates] : []
    editShortPlanNote.value = item.note || ''
  } else {
    editLongPlanSegments.value = getLongPlanSegments(item).map((segment) =>
      createPlanSegment(segment.start, segment.end, segment.task, segment.id)
    )
    if (!editLongPlanSegments.value.length) {
      editLongPlanSegments.value = [createPlanSegment()]
    }
  }

  planEditDialogVisible.value = true
}

function openPlanDuplicate(item) {
  if (item.planType !== 'long') {
    return
  }
  planEditMode.value = 'duplicate'
  planEditingId.value = item.id
  planEditKind.value = 'long'
  editPlanCardName.value = `${getPlanCardNameById(item.planCardId) || item.title || '计划卡片'}（副本）`
  editLongPlanSegments.value = getLongPlanSegments(item).map((segment) =>
    createPlanSegment(segment.start, segment.end, segment.task, createSegmentId())
  )
  if (!editLongPlanSegments.value.length) {
    editLongPlanSegments.value = [createPlanSegment()]
  }
  planEditDialogVisible.value = true
}

function savePlanEdit() {
  const index = plans.value.findIndex((entry) => entry.id === planEditingId.value)
  if (planEditMode.value === 'edit' && index < 0) {
    planEditDialogVisible.value = false
    return
  }
  const cardName = editPlanCardName.value.trim()
  const planCardId = ensurePlanCardIdByName(cardName)
  if (!cardName || !planCardId) {
    ElMessage.warning('请输入计划卡片名字')
    return
  }

  if (planEditKind.value === 'short') {
    const selectedDates = Array.isArray(editShortPlanDates.value)
      ? editShortPlanDates.value.map((item) => normalizeDateValue(item)).filter(Boolean)
      : []

    if (!selectedDates.length) {
      ElMessage.warning('请至少选择一个日期')
      return
    }

    if (planEditMode.value === 'duplicate') {
      const now = new Date()
      plans.value.unshift({
        id: `${now.getTime()}-${Math.random().toString(16).slice(2, 8)}`,
        planType: 'short',
        planCardId,
        title: cardName,
        note: editShortPlanNote.value.trim(),
        shortDates: [...new Set(selectedDates)].sort(),
        longRoutine: {},
        done: false,
        createdAt: now.toISOString()
      })
    } else {
      plans.value[index] = {
        ...plans.value[index],
        planType: 'short',
        planCardId,
        title: cardName,
        note: editShortPlanNote.value.trim(),
        shortDates: [...new Set(selectedDates)].sort(),
        longRoutine: {}
      }
    }
  } else {
    const segments = normalizePlanSegments(
      editLongPlanSegments.value.map((item) => {
        const start = Array.isArray(item.timeRange) && item.timeRange.length === 2 ? item.timeRange[0] : ''
        const end = Array.isArray(item.timeRange) && item.timeRange.length === 2 ? item.timeRange[1] : ''
        return {
          id: item.id,
          start,
          end,
          task: item.task
        }
      })
    )

    if (!hasLongSegments(segments)) {
      ElMessage.warning('请至少添加一条“时间段 + 事项”')
      return
    }

    if (planEditMode.value === 'duplicate') {
      const now = new Date()
      plans.value.unshift({
        id: `${now.getTime()}-${Math.random().toString(16).slice(2, 8)}`,
        planType: 'long',
        planCardId,
        title: cardName,
        note: '',
        shortDates: [],
        longRoutine: {
          segments
        },
        done: false,
        createdAt: now.toISOString()
      })
    } else {
      plans.value[index] = {
        ...plans.value[index],
        planType: 'long',
        planCardId,
        title: cardName,
        note: plans.value[index].note || '',
        shortDates: [],
        longRoutine: {
          segments
        }
      }
    }
  }

  savePlans()
  planEditDialogVisible.value = false
  ElMessage.success(planEditMode.value === 'duplicate' ? '已复制并保存计划' : '计划已修改')
}

async function removePlan(item) {
  try {
    await ElMessageBox.confirm('确认删除这条计划吗？', '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }

  plans.value = plans.value.filter((entry) => entry.id !== item.id)
  savePlans()
  ElMessage.success('计划已删除')
}

watch(selectedSyncPlanCardIds, () => {
  const allowed = new Set()
  for (const item of getSyncPlansBySelectedCards()) {
    if (item.planType === 'short') {
      allowed.add(`short:${item.id}`)
      continue
    }
    for (const segment of getLongPlanSegments(item)) {
      allowed.add(`long:${item.id}:${segment.id}`)
    }
  }
  selectedSyncItems.value = selectedSyncItems.value.filter((token) => allowed.has(token))
  syncSyncExpandedCards()
})

watch(planCardGroups, () => {
  syncExpandedPlanCards()
}, { deep: true })

onMounted(() => {
  loadRecords()
  loadPlanCards()
  ensureDefaultPlanCard()
  loadPlans()
  syncExpandedPlanCards()
  if (!planCardNameDraft.value && planCards.value.length) {
    planCardNameDraft.value = planCards.value[0].name
  }
})
</script>

<style scoped>
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.record-item :deep(.el-card__body) {
  padding: 10px 12px;
}

.record-time {
  font-size: 12px;
  color: var(--app-text-muted-color, #5f6b7a);
  margin-bottom: 6px;
}

.record-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.record-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

.plan-item-actions {
  gap: 0;
}

.record-content {
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.inline-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.advice-content {
  margin: 0 0 10px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  padding: 10px;
  border: 1px solid var(--app-border-color, #dbe2ea);
  border-radius: 8px;
  background: var(--app-surface-soft-color, #f6f8fb);
}

.plan-list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.plan-list-head > span {
  font-size: 14px;
  font-weight: 600;
}

.card-head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.card-head-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-head-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

.plan-card.plan-card-collapsed :deep(.el-card__body) {
  display: none;
}

.sync-card-selector {
  margin-bottom: 10px;
}

.sync-card-selector :deep(.el-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
}

.sync-map-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.segment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.segment-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.note-wrap {
  width: 100%;
}

.note-wrap :deep(.el-textarea__inner) {
  transition: min-height 0.2s ease;
}

.note-wrap :deep(.el-textarea.expanded .el-textarea__inner) {
  min-height: 210px;
}

.plan-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 6px;
}

.plan-meta {
  margin-bottom: 8px;
  color: var(--app-text-muted-color, #5f6b7a);
  font-size: 13px;
}

.meta-label {
  margin-bottom: 4px;
}

.date-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.time-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 3px;
}

.sync-checklist {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 420px;
  overflow: auto;
}

.sync-item-card :deep(.el-card__body) {
  padding: 10px 12px;
}

.sync-item-head {
  font-weight: 600;
}

.sync-item-head :deep(.el-checkbox) {
  align-items: flex-start;
}

.sync-item-head :deep(.el-checkbox__label) {
  display: block;
  line-height: 1.5;
  white-space: normal;
  word-break: break-word;
}

.sync-group-title {
  display: block;
  color: var(--app-text-color, #1f2d3d);
}

.sync-item-meta {
  margin-top: 8px;
  font-size: 13px;
  color: var(--app-text-muted-color, #5f6b7a);
  line-height: 1.5;
  padding-left: 28px;
  white-space: normal;
  word-break: break-word;
}

.long-segment-checks {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.long-segment-checks :deep(.el-checkbox) {
  align-items: flex-start;
}

.long-segment-checks :deep(.el-checkbox__label) {
  line-height: 1.5;
  white-space: normal;
  word-break: break-word;
}
</style>
