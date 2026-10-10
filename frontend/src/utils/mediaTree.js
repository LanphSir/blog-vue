export function buildFolderTree(folders) {
  const rootEntry = folders.find((f) => f.dir === 'root')
  const rootCount = rootEntry ? rootEntry.count : 0
  const total = folders.reduce((sum, f) => sum + f.count, 0)

  const years = new Map()
  for (const f of folders) {
    if (f.dir === 'root') continue
    const [year, month, day] = f.dir.split('/')
    if (!years.has(year)) years.set(year, { count: 0, months: new Map() })
    const y = years.get(year)
    y.count += f.count
    if (!month) continue
    if (!y.months.has(month)) y.months.set(month, { count: 0, days: [] })
    const m = y.months.get(month)
    m.count += f.count
    if (day) m.days.push({ dir: f.dir, count: f.count })
  }

  const nodes = [{ key: '', label: `全部（${total}）`, dir: '' }]
  if (rootCount > 0) nodes.push({ key: 'root', label: `未分类·根目录（${rootCount}）`, dir: 'root' })
  for (const [year, y] of [...years.entries()].sort().reverse()) {
    const yearNode = {
      key: year,
      label: `${year}（${y.count}）`,
      dir: year,
      children: [],
    }
    for (const [month, m] of [...y.months.entries()].sort().reverse()) {
      const dir = `${year}-${month}`
      const monthNode = { key: dir, label: `${month}（${m.count}）`, dir, children: [] }
      for (const d of [...m.days].sort((a, b) => b.dir.localeCompare(a.dir))) {
        monthNode.children.push({ key: d.dir, label: `${d.dir.slice(-2)}（${d.count}）`, dir: d.dir })
      }
      if (!monthNode.children.length) delete monthNode.children
      yearNode.children.push(monthNode)
    }
    nodes.push(yearNode)
  }
  return nodes
}

export function toCascaderOptions(folders) {
  const tree = buildFolderTree(folders)
  const strip = (nodes) =>
    nodes
      .filter((n) => n.dir !== '')
      .map((n) => {
        const opt = { value: n.dir, label: n.label.replace(/（\d+）/, '') }
        if (n.children?.length) opt.children = strip(n.children)
        return opt
      })
  return [{ value: '', label: '全部目录' }, ...strip(tree)]
}
