// Lazily load md-editor-v3 and register local extension instances so that
// code highlighting and fullscreen work without relying on a CDN.
// Everything here stays out of the main bundle (only editor/preview routes use it).
let setupPromise = null

export function setupMdEditor() {
  if (!setupPromise) {
    setupPromise = Promise.all([
      import('md-editor-v3'),
      import('highlight.js/lib/common'),
      import('screenfull'),
      import('markdown-it-mark'),
    ]).then(([mdv, hljsMod, screenfullMod, markMod]) => {
      const markdownItMark = markMod.default
      mdv.config({
        editorExtensions: {
          highlight: { instance: hljsMod.default },
          screenfull: { instance: screenfullMod.default },
        },
        // 支持 ==高亮== 语法
        markdownItConfig: (md) => {
          md.use(markdownItMark)
        },
      })
      return {
        MdEditor: mdv.MdEditor,
        MdPreview: mdv.MdPreview,
        MdCatalog: mdv.MdCatalog,
      }
    })
  }
  return setupPromise
}