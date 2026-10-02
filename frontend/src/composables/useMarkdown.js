import { ref, watch } from 'vue'

let marked = null
let hljs = null
let loadPromise = null

async function ensureMarked() {
  if (!loadPromise) {
    loadPromise = Promise.all([import('marked'), import('highlight.js')]).then(
      ([markedMod, hljsMod]) => {
        marked = markedMod.marked
        hljs = hljsMod.default
        marked.setOptions({ gfm: true, breaks: true })
      },
    )
  }
  return loadPromise
}

export async function renderMarkdownAsync(source) {
  await ensureMarked()
  const tokens = marked.lexer(source || '')
  for (const token of tokens) {
    if (token.type === 'code') {
      token.text = hljs.getLanguage(token.lang)
        ? hljs.highlight(token.text, { language: token.lang }).value
        : hljs.highlightAuto(token.text).value
      token.escaped = true
    }
  }
  return marked.parser(tokens)
}

export async function extractHeadingsAsync(source) {
  await ensureMarked()
  const tokens = marked.lexer(source || '')
  const items = []
  const seen = new Set()
  for (const token of tokens) {
    if (token.type === 'heading' && token.depth <= 3) {
      const base = slugify(token.text)
      let id = base
      let n = 2
      while (seen.has(id)) id = `${base}-${n++}`
      seen.add(id)
      items.push({ id, text: token.text, depth: token.depth })
    }
  }
  return items
}

function slugify(text) {
  return text
    .trim()
    .toLowerCase()
    .replace(/[^\w\u4e00-\u9fa5]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export function useMarkdown(source) {
  const html = ref('')
  watch(
    source,
    async (val) => {
      html.value = await renderMarkdownAsync(val)
    },
    { immediate: true },
  )
  return { html }
}