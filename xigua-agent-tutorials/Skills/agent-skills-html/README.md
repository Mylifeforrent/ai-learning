# Agent Skills 解释型主课 v2

这一版是独立新目录输出的新版课件，目标不是在旧版 11 页上修补，而是重做成一节更完整的 `explorable` 主课。

## 定位

- 单节主课
- 28 页
- 保持原有白灰青视觉方向
- 强化解释型交互，而不是单纯“加动画”

## 课件结构

1. 动机建立：S001-S008
2. 核心机制：S009-S016A
3. 生态与判断：S017-S022
4. 视角切换与收束：S023-S025

## 重点交互页

- `S004-two-worlds.html`
- `S006-skill-not-prompt.html`
- `S010-routing-demo.html`
- `S013-semantic-zoom.html`
- `S013A-skill-directory-map.html`
- `S013B-skill-collaboration-map.html`
- `S017-ecosystem-map.html`
- `S016A-skills-vs-tools.html`
- `S020-task-quiz.html`
- `S021-boundary-counterfactual.html`
- `S024-learning-roadmap.html`

## 启动方式

```bash
cd agent-skills-html
python3 -m http.server 8043
```

然后打开 `http://127.0.0.1:8043`

## 当前状态

- 已完成独立目录输出
- 已完成 25 页 slide inventory
- 已完成核心交互脚本重写
- 仍建议做一轮浏览器级人工验收
