<template>
  <el-card>
    <el-form label-width="90px" :model="form">
      <el-form-item label="标题">
        <el-input v-model="form.title" placeholder="文章标题" />
      </el-form-item>
      <el-form-item label="Slug">
        <el-input v-model="form.slug" placeholder="URL 别名，如 my-first-post" />
      </el-form-item>
      <el-form-item label="封面图">
        <MediaPicker v-model="form.cover_image" tip="支持本地上传或从媒体库选取" :preview-width="220" :preview-height="120" />
      </el-form-item>
      <el-form-item label="摘要">
        <el-input v-model="form.summary" type="textarea" :rows="3" placeholder="文章摘要（可选）" />
      </el-form-item>
      <el-form-item label="分类">
        <el-select v-model="form.category_id" placeholder="选择分类" clearable>
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="标签">
        <el-select v-model="form.tag_ids" multiple placeholder="选择标签" style="width: 100%">
          <el-option v-for="t in tags" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-radio-group v-model="form.status">
          <el-radio value="draft">草稿</el-radio>
          <el-radio value="published">发布</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="置顶/推荐">
        <el-switch v-model="form.is_top" active-text="置顶" />
        <span class="form-gap" />
        <el-switch v-model="form.is_featured" active-text="推荐" />
      </el-form-item>
      <el-form-item label="排序权重">
        <el-input-number v-model="form.sort_weight" :min="0" />
        <span class="form-hint">数值越大越靠前</span>
      </el-form-item>
      <el-form-item label="作者">
        <el-input v-model="form.author" placeholder="留空则使用站点作者" />
      </el-form-item>
      <el-form-item label="正文(Markdown)">
        <MarkdownEditor v-model="form.content" @save="handleSave" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        <el-button @click="$router.back()">返回</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
/* 文章编辑：标题/Slug/封面/摘要/分类/标签/状态/置顶推荐/权重/作者 + Markdown 正文。
 * 封面经 MediaPicker；标签多选；保存后跳回文章列表。
 */
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import MediaPicker from '@/components/admin/MediaPicker.vue'
import { adminCreatePost, adminGetPost, adminUpdatePost } from '@/api/posts'
import { getCategories, getTags } from '@/api/categories'

const route = useRoute()
const router = useRouter()
const postId = route.params.id

const form = ref({
  title: '',
  slug: '',
  cover_image: '',
  summary: '',
  content: '',
  status: 'draft',
  is_top: false,
  is_featured: false,
  sort_weight: 0,
  author: '',
  category_id: null,
  tag_ids: [],
})

const categories = ref([])
const tags = ref([])
const saving = ref(false)

onMounted(async () => {
  const [catRes, tagRes] = await Promise.all([getCategories(), getTags()])
  categories.value = catRes.data
  tags.value = tagRes.data

  if (postId) {
    const res = await adminGetPost(postId)
    form.value = { ...form.value, ...res.data }
  }
})

async function handleSave() {
  if (!form.value.title || !form.value.slug) {
    ElMessage.warning('标题和 Slug 不能为空')
    return
  }
  saving.value = true
  try {
    if (postId) {
      await adminUpdatePost(postId, form.value)
    } else {
      await adminCreatePost(form.value)
    }
    ElMessage.success('保存成功')
    router.push({ name: 'admin-posts' })
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.form-gap {
  width: 24px;
}

.form-hint {
  margin-left: 12px;
  font-size: 12px;
  color: var(--blog-text-secondary);
}
</style>