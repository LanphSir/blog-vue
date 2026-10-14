<template>
  <div class="mlg" v-loading="loading">
    <div class="mlg-bar">
      <el-cascader
        v-model="dirPath"
        :options="cascaderOptions"
        :props="{ checkStrictly: true, expandTrigger: 'hover' }"
        size="small"
        clearable
        :show-all-levels="false"
        placeholder="全部目录"
        style="width: 240px"
        @change="load(1)"
      />
    </div>
    <div class="mlg-grid" :class="{ 'mlg-compact': compact }">
      <button
        v-for="item in items"
        :key="item.id"
        type="button"
        class="mlg-tile"
        :class="{ selected: modelValue === item.url }"
        :title="item.name"
        @click="emit('update:modelValue', item.url)"
      >
        <img v-if="isImage(item)" :src="item.url" class="mlg-img" loading="lazy" alt="" />
        <span v-else class="mlg-ext">{{ item.ext }}</span>
        <span class="mlg-name">{{ item.name }}</span>
      </button>
    </div>
    <el-empty v-if="!loading && !items.length" description="媒体库暂无图片" :image-size="60" />
    <div class="mlg-foot">
      <span class="mlg-total">共 {{ total }} 个文件</span>
      <el-pagination
        v-if="total > pageSize"
        small
        layout="prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="load"
      />
    </div>
  </div>
</template>

<script setup>
/* 媒体库网格：按目录分组的图片选择器，供 MediaPicker 与 MarkdownEditor 复用。
 * 目录用 el-cascader（checkStrictly 支持选中父级目录），目录树来自 mediaTree 聚合。
 * isImage 用 mime 或扩展名兜底判断是否图片，非图片格子显示扩展名占位。
 */
import { computed, onMounted, ref } from 'vue'
import { adminListMedia, adminMediaFolders } from '@/api/upload'
import { toCascaderOptions } from '@/utils/mediaTree'

const props = defineProps({
  modelValue: { type: String, default: '' },
  pageSize: { type: Number, default: 12 },
  compact: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const folders = ref([])
const dirPath = ref([])

const cascaderOptions = computed(() => toCascaderOptions(folders.value))

function currentDir() {
  const path = (dirPath.value || []).filter(Boolean)
  return path.length ? path[path.length - 1] : ''
}

async function loadFolders() {
  try {
    const res = await adminMediaFolders()
    folders.value = res.data
  } catch {
    folders.value = []
  }
}

function isImage(item) {
  return (item.mime || item.ext || '').includes('image') || /\.(png|jpe?g|gif|webp|svg)$/i.test(item.name || '')
}

async function load(toPage = 1) {
  page.value = toPage
  loading.value = true
  try {
    const params = { page: toPage, page_size: props.pageSize }
    const dir = currentDir()
    if (dir) params.dir = dir
    const res = await adminListMedia(params)
    items.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadFolders()
  load()
})

defineExpose({ reload: (p) => load(p ?? 1), loadFolders })
</script>

<style scoped>
.mlg-bar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

.mlg-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
  min-height: 120px;
}

.mlg-compact {
  grid-template-columns: repeat(auto-fill, minmax(88px, 1fr));
}

.mlg-tile {
  display: flex;
  flex-direction: column;
  border: 2px solid var(--blog-border);
  border-radius: 8px;
  background: transparent;
  padding: 0;
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.15s;
}

.mlg-tile:hover,
.mlg-tile.selected {
  border-color: var(--blog-primary);
}

.mlg-img {
  width: 100%;
  height: 84px;
  object-fit: cover;
  display: block;
  background: var(--el-fill-color-lighter);
}

.mlg-ext {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 84px;
  font-size: 12px;
  color: var(--blog-text-secondary);
  background: var(--el-fill-color-lighter);
}

.mlg-name {
  font-size: 11px;
  color: var(--blog-text-secondary);
  padding: 4px 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left;
}

.mlg-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.mlg-total {
  font-size: 12px;
  color: var(--blog-text-secondary);
}
</style>
