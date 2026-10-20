<template>
  <section class="card comment-section">
    <h3 class="section-title">
      <el-icon><ChatDotSquare /></el-icon>
      评论 <span class="count">{{ totalComments }}</span>
    </h3>

    <CommentForm :post-slug="slug" @created="onCreated" />

    <el-skeleton v-if="loading" :rows="3" animated />
    <el-empty v-else-if="!threads.length" description="还没有评论，来抢沙发吧" :image-size="72" />

    <ul v-else class="thread-list">
      <li v-for="thread in threads" :key="thread.comment.id" class="thread">
        <CommentItem :comment="thread.comment" @reply="openReply(thread.comment.id, $event)" />
        <div class="replies" v-if="thread.replies.length || thread.reply_count > thread.replies.length">
          <CommentItem
            v-for="reply in visibleReplies(thread)"
            :key="reply.id"
            :comment="reply"
            :size="32"
            readonly
            @reply="openReply(thread.comment.id, $event)"
          />
          <button
            v-if="!isExpanded(thread) && thread.reply_count > thread.replies.length"
            class="expand-btn"
            @click="expand(thread)"
          >
            查看全部 {{ thread.reply_count }} 条回复
          </button>
          <template v-if="isExpanded(thread) && thread._nextPage">
            <div class="pager">
              <el-pagination
                small
                layout="prev, pager, next"
                :total="thread._total"
                :page-size="REPLY_PAGE_SIZE"
                :current-page="thread._page"
                @current-change="(p) => loadMore(thread, p)"
              />
            </div>
          </template>
        </div>

        <div v-if="replyTarget[thread.comment.id]" class="reply-form">
          <CommentForm
            compact
            :post-slug="slug"
            :parent-id="replyTarget[thread.comment.id].id"
            :placeholder="`回复 @${replyTarget[thread.comment.id].nickname}：`"
            submit-text="回复"
            @created="onReplyCreated(thread.comment.id)"
            @cancel="replyTarget[thread.comment.id] = null"
          />
        </div>
      </li>
    </ul>

    <div v-if="total > PAGE_SIZE" class="pager top-pager">
      <el-pagination
        layout="prev, pager, next"
        :total="total"
        :page-size="PAGE_SIZE"
        :current-page="page"
        @current-change="loadThreads"
      />
    </div>
  </section>
</template>

<script setup>
// 文章评论区：顶级线程分页 + 楼内「查看全部回复」按楼展开分页；发表/回复成功
// 后刷新当前页。threads 上的 _page/_total/_nextPage 是展开态私有字段（下划线
// 约定）；回复列表走 /comments/{root}/replies 接口。
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotSquare } from '@element-plus/icons-vue'
import { getCommentCount, getCommentReplies, getCommentThreads } from '@/api/comments'
import CommentForm from './CommentForm.vue'
import CommentItem from './CommentItem.vue'

const props = defineProps({
  slug: { type: String, required: true },
})

const PAGE_SIZE = 10
const REPLY_PAGE_SIZE = 20

const threads = ref([])
const total = ref(0)
const totalComments = ref(0)
const page = ref(1)
const loading = ref(false)
// 楼 id -> {id, nickname} 当前正在回复的评论
const replyTarget = reactive({})
// 楼 id -> 展开后的全部回复
const expanded = reactive({})

async function refreshCount() {
  try {
    const res = await getCommentCount(props.slug)
    totalComments.value = res.data ?? 0
  } catch {
    /* 计数不是关键路径，失败保持旧值 */
  }
}

async function loadThreads(p = 1) {
  loading.value = true
  try {
    const res = await getCommentThreads({ slug: props.slug, page: p, page_size: PAGE_SIZE })
    threads.value = res.data.items.map((t) => ({ ...t, _page: 1, _total: 0, _nextPage: false }))
    total.value = res.data.total
    page.value = p
    Object.keys(replyTarget).forEach((k) => delete replyTarget[k])
    Object.keys(expanded).forEach((k) => delete expanded[k])
    refreshCount()
  } finally {
    loading.value = false
  }
}

function isExpanded(thread) {
  return expanded[thread.comment.id] !== undefined
}

function visibleReplies(thread) {
  return isExpanded(thread) ? expanded[thread.comment.id] : thread.replies
}

async function expand(thread) {
  const res = await getCommentReplies(thread.comment.id, { page: 1, page_size: REPLY_PAGE_SIZE })
  expanded[thread.comment.id] = res.data.items
  thread._total = res.data.total
  thread._page = 1
  thread._nextPage = total_pages(res.data) > 1
}

function total_pages(data) {
  return Math.max(1, Math.ceil(data.total / data.page_size))
}

async function loadMore(thread, p) {
  const res = await getCommentReplies(thread.comment.id, { page: p, page_size: REPLY_PAGE_SIZE })
  thread._page = p
  const merged = [...expanded[thread.comment.id]]
  merged.splice((p - 1) * REPLY_PAGE_SIZE, res.data.items.length, ...res.data.items)
  expanded[thread.comment.id] = merged
}

function openReply(rootId, comment) {
  replyTarget[rootId] = { id: comment.id, nickname: comment.nickname }
}

function refreshThread(rootId) {
  // 新评论可能插入分页：重拉当前线程页；该楼若已展开则同步重拉回复
  const thread = threads.value.find((t) => t.comment.id === rootId)
  if (thread && expanded[rootId] !== undefined) expand(thread)
  loadThreads(page.value)
}

function onCreated() {
  ElMessage.success('发表成功，若博主开启了评论审核将通过后显示')
  loadThreads(page.value)
}

function onReplyCreated(rootId) {
  ElMessage.success('回复成功，若博主开启了评论审核将通过后显示')
  delete replyTarget[rootId]
  refreshThread(rootId)
}

watch(() => props.slug, (s) => s && loadThreads(1))
onMounted(() => loadThreads(1))
</script>

<style scoped>
.comment-section {
  margin-top: 24px;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px;
  font-size: 18px;
  color: var(--blog-text);
}
.count {
  color: var(--blog-primary);
}
.thread-list {
  list-style: none;
  margin: 18px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 22px;
}
.thread {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.replies {
  margin-left: 44px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  border-left: 2px solid var(--blog-border);
  padding-left: 14px;
}
.expand-btn {
  align-self: flex-start;
  background: none;
  border: none;
  color: var(--blog-primary);
  font-size: 13px;
  cursor: pointer;
  padding: 0;
}
.expand-btn:hover {
  text-decoration: underline;
}
.reply-form {
  margin-left: 44px;
}
.pager {
  display: flex;
  justify-content: center;
}
.top-pager {
  margin-top: 22px;
}</style>
