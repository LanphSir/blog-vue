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

        <div v-if="thread.reply_count > 0" class="reply-area">
          <button v-if="!isOpen(thread)" class="toggle-btn" @click="toggle(thread)">
            <el-icon><ArrowDown /></el-icon>
            {{ thread.reply_count }} 条回复
          </button>
          <template v-else>
            <div class="replies">
              <CommentItem
                v-for="reply in thread._replies || thread.replies"
                :key="reply.id"
                :comment="reply"
                :size="32"
                @reply="openReply(thread.comment.id, $event)"
              />
              <div v-if="thread._nextPage" class="pager">
                <el-pagination
                  small
                  layout="prev, pager, next"
                  :total="thread._total"
                  :page-size="REPLY_PAGE_SIZE"
                :current-page="thread._page"
                  @current-change="(p) => loadMore(thread, p)"
                />
              </div>
            </div>
            <button class="toggle-btn collapse" @click="toggle(thread)">
              <el-icon><ArrowUp /></el-icon>
              收起回复
            </button>
          </template>
        </div>

        <div v-if="replyTarget[thread.comment.id]" class="reply-form">
          <CommentForm
            compact
            :post-slug="slug"
            :parent-id="replyTarget[thread.comment.id].id"
            :placeholder="`回复 @${replyTarget[thread.comment.id].nickname}（支持 Markdown）：`"
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
// 文章评论区：顶级线程分页（置顶楼由后端排最前）+ 楼内回复区「默认折叠、点开才列」，
// 展开时若超过预载条数走 /comments/{root}/replies 分页拉取；任何评论（含楼内回复）
// 都可回复，新回复仍归同一楼层平铺。回复成功后自动展开该楼。openIds 是纯前端
// 展开态（下划线字段是线程上的私有渲染态），刷新页面回到默认折叠。
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowDown, ArrowUp, ChatDotSquare } from '@element-plus/icons-vue'
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
// 楼 id -> true：回复区已展开（默认不在其中 = 折叠）
const openIds = reactive({})

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
    threads.value = res.data.items.map((t) => ({ ...t, _replies: null, _page: 1, _total: 0, _nextPage: false }))
    total.value = res.data.total
    page.value = p
    Object.keys(replyTarget).forEach((k) => delete replyTarget[k])
    // 展开态跨刷新保留：重拉后同步各展开楼的数据
    threads.value.forEach((t) => {
      if (openIds[t.comment.id]) fillReplies(t)
    })
    refreshCount()
  } finally {
    loading.value = false
  }
}

function isOpen(thread) {
  return !!openIds[thread.comment.id]
}

async function toggle(thread) {
  const id = thread.comment.id
  if (openIds[id]) {
    delete openIds[id]
    return
  }
  openIds[id] = true
  await fillReplies(thread)
}

// 展开时填充回复：预载已含全部回复就不必再请求，否则拉第一页（分页）
async function fillReplies(thread) {
  const id = thread.comment.id
  if (thread.replies.length >= thread.reply_count) {
    thread._replies = thread.replies
    thread._total = thread.reply_count
    thread._page = 1
    thread._nextPage = false
    return
  }
  const res = await getCommentReplies(id, { page: 1, page_size: REPLY_PAGE_SIZE })
  // 请求期间线程列表可能已重拉（对象被替换），仅在楼仍展开时写回
  if (openIds[id]) {
    thread._replies = res.data.items
    thread._total = res.data.total
    thread._page = 1
    thread._nextPage = Math.max(1, Math.ceil(res.data.total / res.data.page_size)) > 1
  }
}

async function loadMore(thread, p) {
  const res = await getCommentReplies(thread.comment.id, { page: p, page_size: REPLY_PAGE_SIZE })
  thread._page = p
  const merged = [...(thread._replies || thread.replies)]
  merged.splice((p - 1) * REPLY_PAGE_SIZE, res.data.items.length, ...res.data.items)
  thread._replies = merged
}

// rootId = 所在楼层（回复表单永远挂在楼下），comment = 被回复的那条（可以是楼或楼内回复）
function openReply(rootId, comment) {
  replyTarget[rootId] = { id: comment.id, nickname: comment.nickname }
}

async function refreshThread(rootId, forceOpen = false) {
  if (forceOpen) openIds[rootId] = true
  await loadThreads(page.value)
}

function onCreated() {
  ElMessage.success('发表成功，若博主开启了评论审核将通过后显示')
  loadThreads(page.value)
}

function onReplyCreated(rootId) {
  ElMessage.success('回复成功，若博主开启了评论审核将通过后显示')
  delete replyTarget[rootId]
  // 自动展开该楼，让回复者立刻看到自己的回复
  refreshThread(rootId, true)
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
.reply-area {
  margin-left: 44px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.replies {
  display: flex;
  flex-direction: column;
  gap: 14px;
  border-left: 2px solid var(--blog-border);
  padding-left: 14px;
}
.toggle-btn {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--blog-primary);
  font-size: 13px;
  cursor: pointer;
  padding: 0;
}
.toggle-btn:hover {
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
}
</style>
