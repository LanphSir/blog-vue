// 导航/菜单可用的图标注册表。后端只存图标名字符串，前端在这里映射到实际组件。
// 关键约束：resolveIcon 对未知名字必须返回 null（渲染处已按 null 跳过），绝不能在找不到时抛错，
// 否则一个脏图标名会让整个导航挂掉。
import {
  Bell,
  Collection,
  Camera,
  ChatDotRound,
  Cloudy,
  Coffee,
  Compass,
  Connection,
  Cpu,
  Document,
  Film,
  Folder,
  FolderOpened,
  Grid,
  Headset,
  HomeFilled,
  InfoFilled,
  Link,
  Location,
  Memo,
  Message,
  Notebook,
  Picture,
  PriceTag,
  Present,
  Reading,
  Star,
  Sunny,
  Trophy,
  User,
  UserFilled,
  VideoCamera,
} from '@element-plus/icons-vue'

export const NAV_ICONS = {
  HomeFilled,
  Document,
  Folder,
  FolderOpened,
  Grid,
  PriceTag,
  Star,
  Link,
  Connection,
  InfoFilled,
  User,
  UserFilled,
  Camera,
  Picture,
  Film,
  VideoCamera,
  Headset,
  Coffee,
  Collection,
  Notebook,
  Reading,
  Memo,
  Cloudy,
  Sunny,
  Bell,
  ChatDotRound,
  Message,
  Location,
  Compass,
  Trophy,
  Present,
  Cpu,
}

export const ICON_NAMES = Object.keys(NAV_ICONS)

export function resolveIcon(name) {
  if (!name) return null
  return NAV_ICONS[name] || null
}
