# Scripts Usage Guide

本目录包含用于自动化验证和辅助工具的脚本。

---

## validate_learning_path.py

### 功能
自动验证生成的学习路径文档是否符合质量标准和模板结构。

### 验证项目

#### 1. 基础结构检查
- ✓ 文档必须以标题开头
- ✓ 必须有且仅有一个 H1 标题
- ✓ 文档长度合理（100-1000 行）

#### 2. 必需章节检查
- ✓ 学习目标与边界
- ✓ 学习路径总览
- ✓ 阶段一：基础入门
- ✓ 阶段二：进阶案例
- ✓ 阶段三：项目实战
- ✓ 学习资源推荐

#### 3. 推荐章节检查
- ⚠️ 常见问题与解决方案
- ⚠️ 进阶方向

#### 4. 子章节检查（在"学习目标与边界"下）
- ✓ 核心目标
- ✓ 学习边界
- ✓ 前置知识
- ✓ 预计时间

#### 5. 内容质量检查
- ✓ 检查空章节
- ✓ 检查占位符（[待补充]、TODO、TBD）
- ✓ 检查章节内容长度

#### 6. 学习路径图检查
- ✓ 必须有代码块（路径图）
- ✓ 必须包含"阶段1"、"阶段2"、"阶段3"
- ⚠️ 建议包含"关键路径"

#### 7. 检查点检查
- ✓ 每个阶段必须有检查点章节
- ✓ 每个检查点章节必须有 ✓ 标记
- ⚠️ 建议每个阶段有 3-5 个检查点

#### 8. 时间估算检查
- ✓ 必须有"预计时间"部分
- ⚠️ 建议有具体的时间估算（X小时/天/周）

#### 9. 依赖关系检查
- ⚠️ 建议在学习路径图中标注依赖关系

#### 10. 统计信息
- 总行数
- 总字符数
- H1/H2/H3 章节数
- 代码块数量
- 检查点数量

---

### 使用方法

#### 基本用法
```bash
python3 scripts/validate_learning_path.py <path_to_learning_path.md>
```

#### 严格模式（警告也视为错误）
```bash
python3 scripts/validate_learning_path.py <path_to_learning_path.md> --strict
```

---

### 使用示例

#### 示例 1: 验证一个学习路径文档
```bash
python3 scripts/validate_learning_path.py /path/to/agent-skills-learning-path.md
```

**输出示例**:
```
🔍 Validating learning path: /path/to/agent-skills-learning-path.md

============================================================
📋 Learning Path Validation Report
============================================================

📊 Statistics:
  - Total lines: 450
  - Total characters: 15234
  - H1 sections: 1
  - H2 sections: 8
  - H3 sections: 15
  - Code blocks: 3
  - Checkpoints: 12

⚠️  Warnings (2):
  ⚠️  WARNING: Missing recommended section: 进阶方向
  ⚠️  WARNING: 阶段一 has only 2 checkpoints (recommended: 3-5)

============================================================
⚠️  Validation PASSED with warnings
============================================================
```

#### 示例 2: 严格模式验证
```bash
python3 scripts/validate_learning_path.py /path/to/rag-learning-path.md --strict
```

**输出示例**:
```
🔍 Validating learning path: /path/to/rag-learning-path.md
   Mode: STRICT (warnings treated as errors)

============================================================
📋 Learning Path Validation Report
============================================================

📊 Statistics:
  - Total lines: 520
  - Total characters: 18456
  - H1 sections: 1
  - H2 sections: 9
  - H3 sections: 18
  - Code blocks: 4
  - Checkpoints: 15

============================================================
✅ Validation PASSED - All checks successful!
============================================================
```

#### 示例 3: 验证失败的情况
```bash
python3 scripts/validate_learning_path.py /path/to/incomplete-learning-path.md
```

**输出示例**:
```
🔍 Validating learning path: /path/to/incomplete-learning-path.md

============================================================
📋 Learning Path Validation Report
============================================================

📊 Statistics:
  - Total lines: 120
  - Total characters: 4500
  - H1 sections: 1
  - H2 sections: 4
  - H3 sections: 6
  - Code blocks: 0
  - Checkpoints: 3

❌ Errors (4):
  ❌ ERROR: Missing required section: 阶段二：进阶案例
  ❌ ERROR: Missing required section: 阶段三：项目实战
  ❌ ERROR: Learning path diagram missing '阶段1'
  ❌ ERROR: 阶段一 missing checkpoint section

⚠️  Warnings (3):
  ⚠️  WARNING: Document is very short (120 lines)
  ⚠️  WARNING: No code blocks found (learning path diagram missing?)
  ⚠️  WARNING: Missing recommended section: 常见问题与解决方案

============================================================
❌ Validation FAILED
============================================================
```

---

### 集成到 Workflow

#### 在 SKILL.md 中引用
在 `SKILL.md` 的 Validation 章节中添加：

```markdown
## Validation
Before declaring completion, verify:
- ✓ Learning boundary is explicitly stated
- ✓ All three perspectives are covered (or justified omission)
- ✓ Knowledge points have clear dependencies and sequencing
- ✓ Each stage has validation checkpoints
- ✓ Time estimates are provided for each phase
- ✓ Resources are stage-specific and accessible
- ✓ Output follows template structure in `assets/learning-path-template.md`
- ✓ Run validation script: `python3 scripts/validate_learning_path.py <output_file>`
```

#### 在生成学习路径后自动验证
```markdown
## Workflow
1. Confirm knowledge boundary and learning goals.
2. Classify request type: quick-start, systematic-mastery, or project-driven.
3. Route to three-perspective analysis framework.
4. Sequence knowledge points with dependency mapping.
5. Design validation checkpoints for each stage.
6. Recommend stage-specific resources.
7. Generate complete learning path document.
8. **Run validation script to verify output quality.**
9. If validation fails, fix issues and re-validate.
```

---

### 退出码

- `0`: 验证通过
- `1`: 验证失败（有错误，或严格模式下有警告）

可以在 CI/CD 流程中使用：
```bash
python3 scripts/validate_learning_path.py output.md || exit 1
```

---

### 扩展建议

未来可以添加的验证项：

1. **链接有效性检查**: 验证文档中的所有链接是否有效
2. **代码示例语法检查**: 验证代码块中的代码是否有语法错误
3. **术语一致性检查**: 验证术语使用是否一致
4. **难度等级检查**: 验证难度标记（⭐）是否合理递增
5. **时间估算合理性检查**: 验证时间估算是否合理（如基础入门不应超过1天）

---

### 常见问题

**Q: 为什么需要自动化验证？**
A: 自动化验证可以确保生成的学习路径文档符合质量标准，避免遗漏关键章节或内容，提高输出的一致性和可靠性。

**Q: 验证脚本会修改文档吗？**
A: 不会。验证脚本只读取文档并生成验证报告，不会修改原文档。

**Q: 如何处理验证失败？**
A: 根据验证报告中的错误和警告信息，修改文档后重新验证，直到通过为止。

**Q: 严格模式和普通模式有什么区别？**
A: 普通模式下，只有错误会导致验证失败；严格模式下，警告也会导致验证失败。建议在正式发布前使用严格模式。
