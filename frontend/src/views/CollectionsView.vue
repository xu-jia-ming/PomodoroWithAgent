<template>
  <div>
    <el-card>
      <template #header>
        <span>未来待办集</span>
      </template>

      <el-form :inline="true" @submit.prevent>
        <el-form-item>
          <div style="display:flex; align-items:center; gap:12px;">
            <el-input v-model="name" placeholder="未来待办集名称" style="width: 240px" />
            <el-button type="primary" @click="onCreate">新增</el-button>
          </div>
        </el-form-item>
      </el-form>

      <el-table :data="collections" style="width: 100%">
        <el-table-column prop="name" label="名称" />
        <el-table-column label="操作" width="170" align="center">
          <template #default="scope">
            <div class="collection-action-icons">
              <el-tooltip content="转入待办" placement="top">
                <el-button circle size="small" type="primary" @click="transferToTodo(scope.row)">↪</el-button>
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

    <el-dialog v-model="editDialogVisible" title="修改未来待办集" width="360">
      <el-form label-width="72px">
        <el-form-item label="名称">
          <el-input v-model="editName" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onEditSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createCollection, createTodo, deleteCollection, fetchCollections, updateCollection } from '../api/pomodoro'

const name = ref('')
const collections = ref([])
const editDialogVisible = ref(false)
const editId = ref(null)
const editName = ref('')

async function loadCollections() {
  const res = await fetchCollections()
  collections.value = res.data
}

async function onCreate() {
  if (!name.value.trim()) {
    ElMessage.warning('请输入未来待办集名称')
    return
  }

  await createCollection({ name: name.value.trim() })
  name.value = ''
  await loadCollections()
}

function openEdit(row) {
  editId.value = row.id
  editName.value = row.name
  editDialogVisible.value = true
}

async function onEditSave() {
  if (!editName.value.trim()) {
    ElMessage.warning('请输入未来待办集名称')
    return
  }
  await updateCollection(editId.value, { name: editName.value.trim() })
  editDialogVisible.value = false
  await loadCollections()
}

async function onDelete(id) {
  try {
    await ElMessageBox.confirm('确认删除该未来待办集吗？', '删除确认', {
      type: 'warning',
      confirmButtonText: '确认',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }

  await deleteCollection(id)
  await loadCollections()
}

async function transferToTodo(row) {
  await createTodo({
    title: row.name,
    estimated_pomodoros: 1,
    collection_id: row.id
  })
  await deleteCollection(row.id)
  ElMessage.success('已转入待办')
  await loadCollections()
}

onMounted(loadCollections)
</script>

<style scoped>
.collection-action-icons {
  display: flex;
  gap: 6px;
  justify-content: center;
}
</style>
