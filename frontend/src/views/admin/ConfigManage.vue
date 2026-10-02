<template>
  <el-card>
    <h3 class="title">站点配置</h3>
    <el-form label-width="140px" :model="form">
      <el-form-item v-for="field in fields" :key="field.key" :label="field.label">
        <el-input v-if="field.type === 'input'" v-model="form[field.key]" :placeholder="field.placeholder" />
        <el-input
          v-else-if="field.type === 'textarea'"
          v-model="form[field.key]"
          type="textarea"
          :rows="field.rows || 3"
          :placeholder="field.placeholder"
        />
        <el-color-picker v-else-if="field.type === 'color'" v-model="form[field.key]" />
        <el-input v-else-if="field.type === 'json'" v-model="form[field.key]" type="textarea" :rows="6" />
        <el-switch v-else-if="field.type === 'switch'" v-model="form[field.key]" active-text="显示" inactive-text="隐藏" />
      </el-form-item>
      <el-form-item label="主题强调色预览">
        <span class="accent-preview" :style="{ background: form.site_accent_color || '#2563eb' }" />
        <span class="accent-hint">当前强调色：{{ form.site_accent_color || '#2563eb' }}</span>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="handleSave">保存配置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getSiteConfig, updateSiteConfig } from '@/api/site'

const fields = [
  { key: 'site_name', label: '站点名称', type: 'input' },
  { key: 'site_description', label: '站点描述', type: 'textarea', rows: 2 },
  { key: 'site_slogan', label: '首页副标题', type: 'input', placeholder: '显示在首页 Hero 区' },
  { key: 'site_author', label: '站点作者', type: 'input', placeholder: '文章卡片显示的默认作者' },
  { key: 'site_avatar', label: '作者头像 URL', type: 'input', placeholder: '侧边简介卡片头像' },
  { key: 'site_bio', label: '个人简介', type: 'textarea', rows: 3, placeholder: '侧边简介卡片文案' },
  { key: 'profile_links', label: '平台链接(JSON)', type: 'json', placeholder: '[{"platform":"github","url":"https://github.com/you"}]' },
  { key: 'homepage_section_count', label: '首页栏目数', type: 'input', placeholder: '首页 Tab 显示的顶级栏目数量' },
  { key: 'site_accent_color', label: '主题强调色', type: 'color' },
  { key: 'profile_visible', label: '显示简介卡片', type: 'switch' },
  { key: 'sidebar_tags_visible', label: '显示标签云', type: 'switch' },
  { key: 'sidebar_tag_count', label: '标签云数量', type: 'input', placeholder: '侧边标签云最多显示个数，默认 8' },
  { key: 'sidebar_recent_visible', label: '显示最近发布', type: 'switch' },
  { key: 'notice_text', label: '网站公告', type: 'textarea', rows: 2, placeholder: '站点顶部横幅内容' },
  { key: 'notice_enabled', label: '启用公告', type: 'switch' },
  { key: 'notice_version', label: '公告版本号', type: 'input', placeholder: '修改后已关闭用户将重新看到公告' },
  { key: 'site_menus', label: '导航菜单(JSON)', type: 'json', placeholder: '[{"label":"首页","path":"/"},{"label":"文章","path":"/posts"},{"label":"栏目","type":"category"}]' },
  { key: 'site_logo', label: 'Logo 地址', type: 'input' },
  { key: 'icp', label: 'ICP 备案号', type: 'input' },
  { key: 'footer_text', label: '页脚文字', type: 'input' },
]

const form = reactive({})
const saving = ref(false)

onMounted(async () => {
  const res = await getSiteConfig()
  for (const item of res.data) {
    form[item.key] = item.value
  }
})

async function handleSave() {
  saving.value = true
  try {
    const payload = Object.entries(form).map(([key, value]) => {
      if (typeof value === 'boolean') return { key, value: String(value) }
      return { key, value }
    })
    await updateSiteConfig(payload)
    ElMessage.success('配置已保存')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.title {
  margin-bottom: 16px;
}

.accent-preview {
  display: inline-block;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  margin-right: 10px;
  vertical-align: middle;
}

.accent-hint {
  font-size: 13px;
  color: var(--blog-text-secondary);
}
</style>