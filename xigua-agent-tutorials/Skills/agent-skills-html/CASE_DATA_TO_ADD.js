// ========== 多案例数据源（添加到 interactive.js 的 S013C hook 开头）==========

// 将现有的 skillTree 重命名为 skillTreeGeneral
const skillTreeGeneral = skillTree; // 保留原有的通用结构数据

// 案例1：frontend-design（最简案例）
const skillTreeFrontendDesign = {
  name: 'frontend-design',
  type: 'root',
  icon: '📦',
  layer: 'root',
  expanded: true,
  description: '最简Skill结构：只有核心文件 SKILL.md',
  why: '展示Skill的最小必需结构，证明其他目录都是可选的',
  example: '真实案例：frontend-design 只有 SKILL.md 和 LICENSE.txt',
  collaboration: [
    '✅ SKILL.md 是唯一必需的文件',
    '✅ 不需要任何其他目录也能正常工作',
    '✅ 适合功能单一、不需要额外资源的Skill'
  ],
  children: [
    {
      name: 'SKILL.md',
      type: 'file',
      icon: '📝',
      layer: 'required',
      description: '✅ 唯一必需的核心文件：包含 frontmatter（YAML）和正文（Markdown）',
      why: 'frontmatter 定义触发条件（什么时候调用），正文定义执行流程（怎么执行）',
      example: `---
name: frontend-design
description: 创建高质量前端界面
---

# Frontend Design

## Goal
生成生产级前端代码，避免通用AI美学

## Workflow
1. 分析设计需求和目标受众
2. 选择合适的技术栈和样式风格
3. 生成组件代码和样式
4. 确保可访问性和响应式设计`,
      collaboration: [
        'frontmatter（--- 之间的 YAML）定义 Skill 的元信息和触发条件',
        '正文（Markdown）定义执行流程、约束和最佳实践',
        '✅ 对于简单Skill，只需要这一个文件就足够了'
      ]
    },
    {
      name: 'LICENSE.txt',
      type: 'file',
      icon: '📄',
      layer: 'optional',
      description: '许可证文件（几乎所有官方Skill都有）',
      why: '声明Skill的使用许可和版权信息',
      example: 'MIT License\n\nCopyright (c) 2024 Anthropic\n\nPermission is hereby granted...',
      collaboration: []
    }
  ]
};

// 案例2：pdf（中等案例）
const skillTreePdf = {
  name: 'pdf',
  type: 'root',
  icon: '📦',
  layer: 'root',
  expanded: true,
  description: '中等复杂度：混合目录+文件结构',
  why: '展示Skill如何灵活组织资源，既有目录也有根目录下的文件',
  example: '真实案例：pdf 有 scripts/ 目录，但 forms.md 和 reference.md 直接在根目录',
  collaboration: [
    '✅ 有 scripts/ 目录用于执行脚本',
    '✅ 有根目录下的 .md 文件（不在 references/ 目录中）',
    '⚠️ 注意：reference.md 是单数，不是 references/ 目录'
  ],
  children: [
    {
      name: 'SKILL.md',
      type: 'file',
      icon: '📝',
      layer: 'required',
      description: '✅ 核心文件',
      why: 'PDF操作的主流程定义',
      example: `---
name: pdf
description: PDF文件操作工具集
---

# PDF Operations

## Capabilities
- 合并多个PDF
- 提取文本和表格
- 添加水印
- 填写PDF表单`,
      collaboration: [
        '调用 scripts/ 中的Python脚本执行具体操作',
        '引用 forms.md 和 reference.md 获取详细说明'
      ]
    },
    {
      name: 'scripts/',
      type: 'directory',
      icon: '📁',
      layer: 'optional',
      expanded: false,
      description: '🔧 执行脚本目录',
      why: 'PDF操作需要确定性执行，使用Python脚本保证可靠性',
      example: '真实案例：pdf 的 scripts/ 包含多个PDF处理脚本',
      collaboration: [
        '由 SKILL.md 在需要时调用',
        '提供合并、提取、水印等具体功能'
      ],
      children: [
        {
          name: 'merge_pdfs.py',
          type: 'file',
          icon: '🐍',
          layer: 'optional',
          description: '合并多个PDF文件',
          why: '自动化PDF合并操作',
          example: `#!/usr/bin/env python3
import PyPDF2

def merge_pdfs(input_files, output_file):
    merger = PyPDF2.PdfMerger()
    for pdf in input_files:
        merger.append(pdf)
    merger.write(output_file)
    merger.close()`,
          collaboration: []
        },
        {
          name: 'extract_text.py',
          type: 'file',
          icon: '🐍',
          layer: 'optional',
          description: '提取PDF文本内容',
          why: '从PDF中提取可编辑文本',
          example: `#!/usr/bin/env python3
import PyPDF2

def extract_text(pdf_file):
    with open(pdf_file, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text`,
          collaboration: []
        },
        {
          name: 'add_watermark.py',
          type: 'file',
          icon: '🐍',
          layer: 'optional',
          description: '添加水印到PDF',
          why: '为PDF文件添加版权保护',
          example: `#!/usr/bin/env python3
import PyPDF2

def add_watermark(input_pdf, watermark_pdf, output_pdf):
    # 水印添加逻辑
    pass`,
          collaboration: []
        }
      ]
    },
    {
      name: 'forms.md',
      type: 'file',
      icon: '📄',
      layer: 'optional',
      description: '📋 PDF表单填写参考（根目录下的文件）',
      why: '提供PDF表单字段说明和填写指南',
      example: `# PDF表单填写指南

## 常见表单字段
- 文本字段：直接输入文本
- 复选框：true/false
- 单选按钮：选项值

## 示例
\`\`\`python
form_data = {
    'name': 'John Doe',
    'email': 'john@example.com',
    'agree': True
}
\`\`\``,
      collaboration: [
        '⚠️ 注意：这是根目录下的 .md 文件',
        '不在 references/ 目录中',
        '展示了Skill结构的灵活性'
      ]
    },
    {
      name: 'reference.md',
      type: 'file',
      icon: '📄',
      layer: 'optional',
      description: '📚 PDF操作参考文档（根目录下的文件，单数形式）',
      why: '提供PDF操作的详细API说明',
      example: `# PDF操作参考

## PyPDF2 API
- PdfReader: 读取PDF
- PdfWriter: 写入PDF
- PdfMerger: 合并PDF

## 常见问题
- 加密PDF处理
- 图片提取
- OCR文字识别`,
      collaboration: [
        '⚠️ 注意：是 reference.md（单数），不是 references/ 目录',
        '不同Skill的命名习惯不同',
        'skill-creator 用 references/（复数目录）',
        'mcp-builder 用 reference/（单数目录）',
        'pdf 用 reference.md（单数文件）'
      ]
    },
    {
      name: 'LICENSE.txt',
      type: 'file',
      icon: '📄',
      layer: 'optional',
      description: '许可证文件',
      why: '声明使用许可',
      example: 'MIT License...',
      collaboration: []
    }
  ]
};

// 案例3：skill-creator（完整案例）
const skillTreeSkillCreator = {
  name: 'skill-creator',
  type: 'root',
  icon: '📦',
  layer: 'root',
  expanded: true,
  description: '复杂Skill结构：多层目录+子Agent+自定义目录',
  why: '展示Skill的完整能力，包括子Agent协同、评估系统、多层资源组织',
  example: '真实案例：skill-creator 是官方最复杂的Skill之一',
  collaboration: [
    '✅ 有 agents/ 目录定义子Agent（analyzer、comparator、grader）',
    '✅ 有 references/ 目录存放参考资料',
    '✅ 有 scripts/ 目录执行评估和报告生成',
    '✅ 有 assets/ 目录存放HTML模板',
    '✅ 有 eval-viewer/ 自定义目录用于评估可视化'
  ],
  children: [
    {
      name: 'SKILL.md',
      type: 'file',
      icon: '📝',
      layer: 'required',
      description: '✅ 核心文件',
      why: 'Skill创建的主流程定义',
      example: `---
name: skill-creator
description: 设计、创建和改进高质量AI技能
---

# Skill Creator

## Goal
帮助用户创建结构良好、触发准确的Skill

## Workflow
1. 理解用户需求和使用场景
2. 设计Skill结构和触发条件
3. 生成SKILL.md和支撑文件
4. 运行评估和改进`,
      collaboration: [
        '调用 agents/ 中的子Agent进行分析和评估',
        '引用 references/ 中的设计模式',
        '使用 scripts/ 运行自动化评估',
        '使用 assets/ 中的HTML模板生成报告'
      ]
    },
    {
      name: 'agents/',
      type: 'directory',
      icon: '📁',
      layer: 'optional',
      expanded: false,
      description: '🤖 子Agent定义（仅复杂Skill使用）',
      why: '当Skill需要多个专门化的子任务时，使用子Agent协同完成',
      example: '真实案例：skill-creator 有 3 个子Agent协同工作',
      collaboration: [
        '⚠️ 这不是"适配层"，而是子Agent的Markdown定义',
        '每个子Agent有独立的角色和能力定义',
        '由主Skill协调调用'
      ],
      children: [
        {
          name: 'analyzer.md',
          type: 'file',
          icon: '📄',
          layer: 'optional',
          description: '分析器子Agent',
          why: '负责分析Skill设计的质量和完整性',
          example: `# Analyzer Agent

## Role
分析Skill设计的质量和完整性

## Capabilities
- 检查frontmatter完整性
- 评估触发条件准确性
- 识别潜在改进点

## Output Format
- 问题列表
- 改进建议
- 质量评分`,
          collaboration: []
        },
        {
          name: 'comparator.md',
          type: 'file',
          icon: '📄',
          layer: 'optional',
          description: '对比器子Agent',
          why: '对比不同Skill实现方案的优劣',
          example: `# Comparator Agent

## Role
对比不同Skill实现方案

## Capabilities
- 多方案并行分析
- 优劣势对比
- 推荐最佳方案

## Output Format
- 方案A优势/劣势
- 方案B优势/劣势
- 推荐方案及理由`,
          collaboration: []
        },
        {
          name: 'grader.md',
          type: 'file',
          icon: '📄',
          layer: 'optional',
          description: '评分器子Agent',
          why: '给Skill设计打分，提供量化评估',
          example: `# Grader Agent

## Role
给Skill设计打分

## Scoring Criteria
- 触发准确性 (0-10)
- 执行流程清晰度 (0-10)
- 资源组织合理性 (0-10)
- 文档完整性 (0-10)

## Output Format
- 各维度评分
- 总分
- 改进建议`,
          collaboration: []
        }
      ]
    },
    {
      name: 'references/',
      type: 'directory',
      icon: '📁',
      layer: 'optional',
      expanded: false,
      description: '📚 参考资料（复数形式）',
      why: '存放Skill设计模式和最佳实践',
      example: '真实案例：skill-creator 有 references/schemas.md',
      collaboration: [
        '由 SKILL.md 在需要时引用',
        '⚠️ 注意：是 references/（复数），与 pdf 的 reference.md 不同'
      ],
      children: [
        {
          name: 'schemas.md',
          type: 'file',
          icon: '📄',
          layer: 'optional',
          description: 'Skill设计模式参考',
          why: '提供常见Skill设计模式和反模式',
          example: `# Skill设计模式

## 触发模式
- 任务型触发：明确的任务关键词
- 场景型触发：特定工作场景
- 工具型触发：特定工具或框架

## 反模式
- 触发条件过于宽泛
- 执行流程不清晰
- 缺少约束和验证`,
          collaboration: []
        }
      ]
    },
    {
      name: 'scripts/',
      type: 'directory',
      icon: '📁',
      layer: 'optional',
      expanded: false,
      description: '🔧 执行脚本',
      why: '自动化评估和报告生成',
      example: '真实案例：skill-creator 有 3 个Python脚本',
      collaboration: [
        '由 SKILL.md 在需要时调用',
        '提供自动化评估能力'
      ],
      children: [
        {
          name: 'run_eval.py',
          type: 'file',
          icon: '🐍',
          layer: 'optional',
          description: '运行Skill评估',
          why: '自动化评估Skill的执行效果',
          example: `#!/usr/bin/env python3
"""
运行 Skill 评估
"""
import subprocess
import json

def run_evaluation(skill_path):
    # 评估逻辑
    results = {
        'trigger_accuracy': 8.5,
        'workflow_clarity': 9.0,
        'resource_organization': 7.5
    }
    return results

if __name__ == '__main__':
    results = run_evaluation('.')
    print(json.dumps(results, indent=2))`,
          collaboration: []
        },
        {
          name: 'generate_report.py',
          type: 'file',
          icon: '🐍',
          layer: 'optional',
          description: '生成评估报告',
          why: '将评估结果转换为可读报告',
          example: `#!/usr/bin/env python3
"""
生成 Skill 执行报告
"""
def generate_report(results):
    report = f"""
# Skill 评估报告

## 评分结果
- 触发准确性: {results['trigger_accuracy']}/10
- 流程清晰度: {results['workflow_clarity']}/10
- 资源组织: {results['resource_organization']}/10

## 总体评价
{'优秀' if sum(results.values())/len(results) >= 8 else '良好'}
"""
    return report`,
          collaboration: []
        },
        {
          name: 'improve_description.py',
          type: 'file',
          icon: '🐍',
          layer: 'optional',
          description: '改进描述文本',
          why: '优化Skill的描述和文档',
          example: `#!/usr/bin/env python3
"""
改进 Skill 描述
"""
def improve_description(original_desc):
    # 改进逻辑
    improved = original_desc.strip()
    # 添加清晰度、具体性等改进
    return improved`,
          collaboration: []
        }
      ]
    },
    {
      name: 'assets/',
      type: 'directory',
      icon: '📁',
      layer: 'optional',
      expanded: false,
      description: '🎨 输出模板（较少使用）',
      why: '存放HTML报告模板',
      example: '真实案例：skill-creator 有 assets/eval_review.html',
      collaboration: [
        '由 scripts/ 使用生成HTML报告',
        '⚠️ 这是较少使用的目录，大部分Skill没有'
      ],
      children: [
        {
          name: 'eval_review.html',
          type: 'file',
          icon: '📄',
          layer: 'optional',
          description: '评估报告HTML模板',
          why: '提供可视化的评估报告',
          example: `<!DOCTYPE html>
<html>
<head>
  <title>Skill评估报告</title>
  <style>
    body { font-family: sans-serif; }
    .score { font-size: 2em; color: #10b981; }
  </style>
</head>
<body>
  <h1>Skill评估报告</h1>
  <div class="score">{{total_score}}/10</div>
  <div>{{details}}</div>
</body>
</html>`,
          collaboration: []
        }
      ]
    },
    {
      name: 'eval-viewer/',
      type: 'directory',
      icon: '📁',
      layer: 'flexible',
      expanded: false,
      description: '💡 自定义目录：评估结果查看器',
      why: '展示Skill结构的灵活性，可以创建任何符合需求的目录',
      example: '真实案例：skill-creator 特有的目录，用于评估可视化',
      collaboration: [
        '✅ 这是完全自定义的目录',
        '✅ 展示了Skill可以根据需要创建任何目录',
        '✅ 不是标准目录，但完全合法'
      ],
      children: [
        {
          name: '...',
          type: 'note',
          icon: '📝',
          layer: 'flexible',
          description: '包含评估可视化相关文件',
          why: '提供Web界面查看评估结果',
          example: '具体实现细节请参考官方仓库',
          collaboration: []
        }
      ]
    },
    {
      name: 'LICENSE.txt',
      type: 'file',
      icon: '📄',
      layer: 'optional',
      description: '许可证文件',
      why: '声明使用许可',
      example: 'MIT License...',
      collaboration: []
    }
  ]
};

// 案例数据集合
const skillTreeCases = {
  '通用': skillTreeGeneral,
  'frontend-design': skillTreeFrontendDesign,
  'pdf': skillTreePdf,
  'skill-creator': skillTreeSkillCreator
};

// 当前选中的案例
let currentCase = '通用';
let currentSkillTree = skillTreeCases[currentCase];

// 案例切换函数
window.switchCase = function(caseName) {
  currentCase = caseName;
  currentSkillTree = skillTreeCases[caseName];

  // 更新按钮状态
  document.querySelectorAll('.case-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.case === caseName);
  });

  // 重新渲染树
  renderTree();

  // 默认选中根节点
  setTimeout(() => {
    selectNode(currentSkillTree, [currentSkillTree.name]);
  }, 50);
};

// 修改所有使用 skillTree 的地方为 currentSkillTree
// 在 renderTree() 中：
function renderTree() {
  allNodes = [];
  treeRoot.innerHTML = '';
  treeRoot.appendChild(renderNode(currentSkillTree)); // 改为 currentSkillTree

  // 恢复选中状态
  if (selectedNode) {
    const nodeData = allNodes.find(n => n.node === selectedNode);
    if (nodeData) {
      nodeData.element.classList.add('active');
    }
  }
}

// 在 expandAll() 中：
window.expandAll = function() {
  function expand(node) {
    if (node.type === 'directory') {
      node.expanded = true;
    }
    if (node.children) {
      node.children.forEach(expand);
    }
  }
  expand(currentSkillTree); // 改为 currentSkillTree
  renderTree();
};

// 在 collapseAll() 中：
window.collapseAll = function() {
  function collapse(node) {
    if (node.type === 'directory' && node.name !== currentSkillTree.name) { // 改为 currentSkillTree.name
      node.expanded = false;
    }
    if (node.children) {
      node.children.forEach(collapse);
    }
  }
  collapse(currentSkillTree); // 改为 currentSkillTree
  currentSkillTree.expanded = true; // 保持根目录展开
  renderTree();
};

// 在 jumpToNode() 中：
window.jumpToNode = function(nodeName) {
  function findAndExpand(node, target, path = []) {
    if (node.name === target) {
      return { node, path: [...path, node.name] };
    }
    if (node.children) {
      for (let child of node.children) {
        const result = findAndExpand(child, target, [...path, node.name]);
        if (result) {
          node.expanded = true;
          return result;
        }
      }
    }
    return null;
  }

  const result = findAndExpand(currentSkillTree, nodeName); // 改为 currentSkillTree
  if (result) {
    renderTree();
    setTimeout(() => {
      selectNode(result.node, result.path);
      const targetEl = document.querySelector(`[data-node-name="${nodeName}"]`);
      if (targetEl) {
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 50);
  }
};

// 在 jumpToNodeByPath() 中：
window.jumpToNodeByPath = function(targetPath) {
  function findByPath(node, path, currentPath = []) {
    const newPath = [...currentPath, node.name];
    if (JSON.stringify(newPath) === JSON.stringify(path)) {
      return { node, path: newPath };
    }
    if (node.children && path.length > newPath.length) {
      for (let child of node.children) {
        const result = findByPath(child, path, newPath);
        if (result) {
          node.expanded = true;
          return result;
        }
      }
    }
    return null;
  }

  const result = findByPath(currentSkillTree, targetPath); // 改为 currentSkillTree
  if (result) {
    renderTree();
    setTimeout(() => {
      selectNode(result.node, result.path);
    }, 50);
  }
};
