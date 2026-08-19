# Agent 上下文管理系统 -- Context Engineering 完整指南 · HTML 交互课件

> 从"会存取记忆"升维到"懂窗口策展"，掌握 Agent 上下文工程的完整分析框架（六模块坐标系 + Anthropic 五策略），并建立场景选型和成本优化的工程师直觉。

## 项目概述

这是一个纯前端的交互式课件，旨在帮助学员：
1. 理解记忆管理与上下文工程的本质差异（供给侧 vs 消费侧）。
2. 掌握上下文窗口的六大功能模块（系统提示词、对话历史、记忆注入、工具上下文、任务状态、外部知识）。
3. 深入理解 Anthropic 五策略框架（Write、Select、Compress、Isolate、Cache）。
4. 通过交互式全景图和场景矩阵，建立上下文策展的工程师直觉。

## 快速启动

本项目为纯静态 HTML/JS，无需编译。

### 方法 1: Python 服务器（推荐）
```bash
cd html-courseware
python -m http.server 8080
# 访问 http://localhost:8080
```

### 方法 2: VS Code Live Server
1. 安装 Live Server 插件。
2. 右键 `index.html` -> "Open with Live Server"。

### 方法 3: 直接打开
```bash
open index.html
# 或在浏览器中直接打开 index.html（部分交互功能可能受限）
```

## 目录结构

```
html-courseware/
├── index.html              # 主入口（幻灯片路由 + 导航框架）
├── css/
│   └── main.css            # 全局样式（梦幻柔光主题 + 响应式布局）
├── js/
│   └── main.js             # 核心逻辑（翻页/进度/菜单/交互）
├── slides/                 # 27 张幻灯片页面（HTML 片段）
│   ├── S001-cover.html
│   ├── S002-supply-demand.html
│   ├── ...
│   └── S027-knowledge-map.html
├── slide_structure.json    # 幻灯片结构定义（章节/页面/布局）
├── style_manifest.json     # 视觉风格配置（配色/字体/动效）
├── courseware-brief.md      # 课件需求简报
└── interaction_architecture.md  # 交互架构设计文档
```

## 课程章节结构（4 章 27 页 / 90 分钟）

### 第一章：认知升维
- S001: 封面
- S002: 供需模型 — 记忆管理 vs 上下文工程
- S003: 三层递进模型 — PE → MM → CE
- S004: Context Rot — 有效窗口的真相
- S005: 分层容器模型 — 上下文窗口全景

### 第二章：六大功能模块
- S006: 六模块全景图（交互式坐标系）
- S007: 系统提示词 — 人格与规则层
- S008: 对话历史 — 短期工作记忆
- S009: 记忆注入 — 长期知识召回
- S010: 工具上下文 — 外部能力接口
- S011: 任务状态 — Scratchpad 与规划
- S012: 外部知识 — RAG 与文档注入

### 第三章：五策略框架
- S013: 五策略全景图（交互式框架）
- S014: 策略总览 — Write / Select / Compress / Isolate / Cache
- S015: Write 策略 — 结构化写入
- S016: Select 策略 — 智能筛选
- S017-S020: Compress 策略 — 工具清理/观测遮蔽/压缩合并
- S021: Isolate 策略 — 多 Agent 隔离
- S022: Cache 策略 — 前缀缓存

### 第四章：决策内化
- S023: 章节过渡
- S024: OpenClaw 诊断实战
- S025: 场景选型矩阵
- S026: Token 经济学
- S027: 知识地图总结

## 快捷键

| 按键 | 功能 |
|------|------|
| `←` `→` | 前后翻页 |
| `F` | 全屏切换 |
| `M` | 课程目录菜单 |
| `T` | 画笔拖尾效果 |

## 设计约束

1. **居中对齐**：使用 `.slide` 类的默认 Flexbox 居中。
2. **80% 填充限制**：内容不应贴边，留有足够呼吸感。
3. **无滚动条**：内容必须适配视口高度（`100vh`），溢出会被裁剪。
4. **响应式字体**：使用 `clamp()` 确保在不同分辨率下可读。

## 视觉风格

- **主题**：P03 梦幻柔光（浅色主题，柔和渐变）
- **配色**：Split-complementary — primary `#2D5A7A` / accent `#c17f59`
- **字体**：Sora / Noto Sans SC
- **动效**：Medium level

## 技术栈

- **前端框架**：纯 Vanilla JS（无依赖）
- **样式**：CSS3（Flexbox + Grid + CSS Variables + clamp()）
- **图标**：Emoji（无需字体库）

## 许可证

本项目仅供教学使用，未经授权不得用于商业用途。

---

**课程时长**：90 分钟
**维护者**：LLM 上下文工程课程组
