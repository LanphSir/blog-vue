<template>
  <teleport to="body">
    <transition name="search">
      <div v-if="visible" class="search-overlay" @click.self="close">
        <div class="search-panel">
          <div class="search-input-row">
            <el-icon class="search-icon"><Search /></el-icon>
            <input
              ref="inputRef"
              v-model="keyword"
              class="search-input"
              placeholder="搜索文章标题或内容…"
              @input="onInput"
              @keydown.down.prevent="move(1)"
              @keydown.up.prevent="move(-1)"
              @keydown.enter.prevent="goFirst"
            />
            <kbd class="search-esc">ESC</kbd>
          </div>

          <div ref="resultsWrap" class="search-results">
            <div v-if="loading" class="search-status">搜索中…</div>
            <template v-else-if="!keyword">
              <div v-if="history.length" class="search-history">
                <div class="history-head">
                  <span class="history-title">搜索历史</span>
                  <button class="history-clear" @click="history = clearHistory()">清空</button>
                </div>
                <div class="history-chips">
                  <span v-for="item in history" :key="item" class="history-chip" @click="useHistory(item)">
                    <el-icon class="chip-icon"><Clock /></el-icon>
                    <span class="chip-text">{{ item }}</span>
                    <el-icon class="chip-del" title="删除" @click.stop="history = removeHistory(item)"
                      ><Close
                    /></el-icon>
                  </span>
                </div>
              </div>
              <div v-else class="search-status">输入关键词开始搜索，支持 Ctrl/Cmd + K 唤起</div>
            </template>
            <div v-else-if="!results.length" class="search-status">未找到相关文章</div>
            <button
              v-for="(post, i) in results"
              :key="post.id"
              class="result-item"
              :class="{ active: i === activeIndex }"
              @mouseenter="activeIndex = i"
              @click="goDetail(post)"
            >
              <div class="result-line">
                <div class="result-title" v-html="highlight(post.title)" />
                <kbd v-if="i === activeIndex" class="result-enter">↵</kbd>
              </div>
              <div class="result-summary" v-html="highlight(post.summary || '')" />
              <div class="result-meta">
                <span v-if="post.category?.name" class="result-cat">{{ post.category.name }}</span>
                <span>{{ formatDate(post.published_at) }}</span>
                <span>{{ post.view_count }} 阅读</span>
              </div>
            </button>
            <button v-if="results.length >= 8" class="result-more" @click="goSearchPage">
              查看全部结果 →
            </button>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
/* 全局搜索浮层：Ctrl/Cmd+K 唤起，teleport 到 body，带搜索历史与键盘上下选择。
 * 注意结果高亮用 highlight() 把关键词包 <mark>，其中对 HTML 特殊字符先做转义、
 * 正则元字符做 escape，避免用户输入被当正则/破坏页面结构。
 * 历史复用 searchHistory（上限 10 条、localStorage 容错）。
 */
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Clock, Close, Search } from '@element-plus/icons-vue'
import { getPosts } from '@/api/posts'
import { addHistory, clearHistory, loadHistory, removeHistory } from '@/utils/searchHistory'

const router = useRouter()
const visible = ref(false)
const keyword = ref('')
const results = ref([])
const loading = ref(false)
const inputRef = ref(null)
const history = ref(loadHistory())
const resultsWrap = ref(null)
const activeIndex = ref(0)
let debounceTimer = null

watch(results, () => {
  activeIndex.value = 0
})

function move(step) {
  const n = results.value.length
  if (!n) return
  activeIndex.value = (activeIndex.value + step + n) % n
  nextTick(() => {
    resultsWrap.value?.querySelectorAll('.result-item')[activeIndex.value]?.scrollIntoView({ block: 'nearest' })
  })
}

function useHistory(word) {
  keyword.value = word
  history.value = addHistory(word)
  search()
  inputRef.value?.focus()
}

function recordHistory() {
  const kw = keyword.value.trim()
  if (kw) history.value = addHistory(kw)
}

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString('zh-CN') : ''
}

function highlight(text) {
  if (!text || !keyword.value) return text
  const escaped = text.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c])
  const kw = keyword.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return escaped.replace(new RegExp(`(${kw})`, 'gi'), '<mark>$1</mark>')
}

async function search() {
  if (!keyword.value.trim()) {
    results.value = []
    return
  }
  loading.value = true
  try {
    const res = await getPosts({ page: 1, page_size: 8, keyword: keyword.value.trim() })
    results.value = res.data.items
  } catch {
    results.value = []
  } finally {
    loading.value = false
  }
}

function onInput() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(search, 250)
}

function goFirst() {
  if (results.value.length) goDetail(results.value[activeIndex.value] ?? results.value[0])
  else if (keyword.value.trim()) goSearchPage()
}

function goDetail(post) {
  recordHistory()
  close()
  router.push({ name: 'post-detail', params: { slug: post.slug } })
}

function goSearchPage() {
  recordHistory()
  close()
  router.push({ name: 'posts', query: { keyword: keyword.value.trim() } })
}

function open() {
  visible.value = true
  nextTick(() => inputRef.value?.focus())
}

function close() {
  visible.value = false
  keyword.value = ''
  results.value = []
}

function onKeydown(e) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    visible.value ? close() : open()
  } else if (e.key === 'Escape' && visible.value) {
    close()
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  clearTimeout(debounceTimer)
})

defineExpose({ open, close })
</script>

<style scoped>
.search-history {
  padding: 12px 14px 16px;
}

.history-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.history-title {
  font-size: 12px;
  color: var(--blog-text-secondary);
}

.history-clear {
  border: none;
  background: transparent;
  color: var(--blog-text-secondary);
  font-size: 12px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
}

.history-clear:hover {
  color: var(--blog-primary);
}

.history-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.history-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  max-width: 100%;
  padding: 5px 10px;
  border: 1px solid var(--blog-border);
  border-radius: 999px;
  font-size: 13px;
  color: var(--blog-text);
  cursor: pointer;
  transition:
    color 0.15s,
    border-color 0.15s;
}

.history-chip:hover {
  color: var(--blog-primary);
  border-color: var(--blog-primary);
}

.chip-icon {
  font-size: 12px;
  color: var(--blog-text-secondary);
}

.chip-text {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chip-del {
  font-size: 12px;
  color: var(--blog-text-secondary);
  border-radius: 50%;
}

.chip-del:hover {
  color: #f56c6c;
}

.search-overlay {
  position: fixed;
  inset: 0;
  /* 高于 md-editor-v3（10002/20000）与 medium-zoom（100001）等页内一切浮层 */
  z-index: 110000;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 12vh 16px 0;
}

.search-panel {
  width: min(640px, 100%);
  background: var(--blog-card);
  border: 1px solid var(--blog-border);
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.search-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--blog-border);
}

.search-icon {
  font-size: 18px;
  color: var(--blog-text-secondary);
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 16px;
  color: var(--blog-text);
}

.search-esc {
  font-size: 11px;
  padding: 2px 8px;
  border: 1px solid var(--blog-border);
  border-radius: 4px;
  color: var(--blog-text-secondary);
  background: var(--blog-bg);
}

.search-results {
  max-height: 48vh;
  overflow-y: auto;
  padding: 8px;
}

.search-status {
  padding: 24px 16px;
  text-align: center;
  color: var(--blog-text-secondary);
  font-size: 13px;
}

.result-item {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  padding: 12px 14px;
  border-radius: 8px;
  cursor: pointer;
}

.result-item:hover,
.result-item.active {
  background: color-mix(in srgb, var(--blog-primary) 8%, transparent);
}

.result-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 4px;
}

.result-enter {
  flex-shrink: 0;
  font-size: 11px;
  padding: 1px 7px;
  border: 1px solid var(--blog-border);
  border-radius: 4px;
  color: var(--blog-text-secondary);
  background: var(--blog-bg);
}

.result-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--blog-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-summary {
  font-size: 13px;
  color: var(--blog-text-secondary);
  line-height: 1.6;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-meta {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: var(--blog-text-secondary);
}

.result-cat {
  color: var(--blog-primary);
}

.result-more {
  display: block;
  width: 100%;
  text-align: center;
  border: none;
  background: transparent;
  color: var(--blog-primary);
  font-size: 13px;
  padding: 10px;
  cursor: pointer;
}

.result-more:hover {
  text-decoration: underline;
}

:deep(mark) {
  background: color-mix(in srgb, var(--blog-primary) 30%, transparent);
  color: inherit;
  border-radius: 2px;
  padding: 0 1px;
}

.search-enter-active,
.search-leave-active {
  transition: opacity 0.2s;
}

.search-enter-active .search-panel,
.search-leave-active .search-panel {
  transition: transform 0.2s;
}

.search-enter-from,
.search-leave-to {
  opacity: 0;
}

.search-enter-from .search-panel,
.search-leave-to .search-panel {
  transform: translateY(-16px);
}
</style>