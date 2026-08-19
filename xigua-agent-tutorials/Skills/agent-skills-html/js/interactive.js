/* ========== Agent Skills Explorable Main Lesson v2 - Interaction Hooks ========== */
window.slideHooks = window.slideHooks || {};

/* ========== S003A: Three Architecture Pains - Progressive Card Switch ========== */
window.slideHooks['slides/S003A-three-architecture-pains.html'] = function() {
    const painCards = [
        document.getElementById('pain-1'),
        document.getElementById('pain-2'),
        document.getElementById('pain-3')
    ];
    const navDots = document.querySelectorAll('.pain-nav-dot');
    const keyInsight = document.getElementById('key-insight');
    const tokenOldBar = document.getElementById('token-old');
    const tokenNewBar = document.getElementById('token-new');

    if (!painCards[0] || navDots.length === 0) return;

    let currentPain = 1;
    let viewedPains = new Set([1]);

    // 清理旧动画
    gsap.killTweensOf([tokenOldBar, tokenNewBar]);

    // 初始化Token动画（使用 set+to 安全模式）
    function playTokenAnimation() {
        if (!tokenOldBar || !tokenNewBar) return;

        // 先设置初始状态
        gsap.set([tokenOldBar, tokenNewBar], { width: '0%' });

        // 再执行动画
        gsap.to(tokenOldBar, {
            width: '100%',
            duration: 1.2,
            ease: 'power2.out'
        });
        gsap.to(tokenNewBar, {
            width: '10%',
            duration: 1.2,
            ease: 'power2.out',
            delay: 0.3
        });
    }

    // 首次进入延迟播放
    setTimeout(playTokenAnimation, 500);

    // 切换痛点函数
    window.switchPain = function(painNum) {
        if (painNum === currentPain) return;

        // 更新导航点状态
        navDots.forEach((dot, idx) => {
            if (idx + 1 === painNum) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });

        // 切换卡片
        painCards.forEach((card, idx) => {
            if (!card) return;
            if (idx + 1 === currentPain) {
                // 淡出当前卡片
                gsap.to(card, {
                    opacity: 0,
                    y: -20,
                    duration: 0.3,
                    ease: 'power2.in',
                    onComplete: () => {
                        card.style.display = 'none';
                    }
                });
            }
            if (idx + 1 === painNum) {
                // 淡入新卡片
                card.style.display = 'block';
                gsap.set(card, { opacity: 0, y: 20 });
                gsap.to(card, {
                    opacity: 1,
                    y: 0,
                    duration: 0.4,
                    ease: 'power2.out',
                    delay: 0.2
                });
            }
        });

        currentPain = painNum;
        viewedPains.add(painNum);

        // 如果切换回痛点一，重新播放Token动画
        if (painNum === 1) {
            setTimeout(playTokenAnimation, 400);
        }

        // 如果三个痛点都看过了，显示关键洞察
        if (viewedPains.size === 3 && keyInsight) {
            gsap.to(keyInsight, {
                opacity: 1,
                duration: 0.6,
                ease: 'power2.out',
                delay: 0.5
            });
        }
    };

    // 返回清理函数
    return function cleanup() {
        gsap.killTweensOf([tokenOldBar, tokenNewBar, ...painCards, keyInsight]);
        delete window.switchPain;
    };
};

/* ========== S008B: Skill Structure Comparison - Three Column Comparison ========== */
window.slideHooks['slides/S008B-skill-structure-comparison.html'] = function() {
    const contentSimple = document.getElementById('content-simple');
    const contentWorkflow = document.getElementById('content-workflow');
    const contentResource = document.getElementById('content-resource');
    const exampleDetail = document.getElementById('example-detail');
    const exampleTitle = document.getElementById('example-title');
    const exampleContent = document.getElementById('example-content');
    const dimensionBtns = document.querySelectorAll('.dimension-btn');

    if (!contentSimple || !contentWorkflow || !contentResource) return;

    let currentDimension = 'structure';
    let currentExample = null;

    // 维度数据
    const dimensionData = {
        structure: {
            simple: ['📄 单个 SKILL.md 文件', '无额外目录', '总大小 < 5KB'],
            workflow: ['📄 单个 SKILL.md 文件', '包含多步骤 Workflow', '总大小 5-15KB'],
            resource: ['📁 SKILL.md + resources/', '包含脚本/模板/参考文档', '总大小 > 50KB']
        },
        complexity: {
            simple: ['3-5 个线性步骤', '无分支逻辑', '5 分钟可完成'],
            workflow: ['5-10 个步骤', '包含条件分支', '15-30 分钟可完成'],
            resource: ['10+ 个步骤', '多层嵌套逻辑', '1-2 小时可完成']
        },
        dependency: {
            simple: ['无外部依赖', '仅依赖 Claude 内置能力', '开箱即用'],
            workflow: ['无外部依赖', '可能调用多个工具', '需要工具权限'],
            resource: ['依赖外部脚本/模板', '需要特定文件结构', '需要环境配置']
        },
        scenario: {
            simple: ['单一明确任务', '如：生成 commit 信息', '如：格式化代码'],
            workflow: ['多步骤流程任务', '如：TDD 开发流程', '如：代码审查流程'],
            resource: ['复杂领域任务', '如：课件生成系统', '如：交互架构设计']
        },
        cost: {
            simple: ['创建成本：5 分钟', '维护成本：几乎为 0', '学习成本：极低'],
            workflow: ['创建成本：15-30 分钟', '维护成本：偶尔调整', '学习成本：低'],
            resource: ['创建成本：1-2 小时', '维护成本：需持续优化', '学习成本：中等']
        },
        value: {
            simple: ['快速解决高频小任务', '提升日常效率', '适合个人使用'],
            workflow: ['标准化复杂流程', '保证质量一致性', '适合团队协作'],
            resource: ['构建领域专家系统', '沉淀专业知识', '适合企业级应用']
        }
    };

    // 示例数据
    const exampleData = {
        simple: {
            title: '简单技能示例：commit-message-generator',
            yaml: `---
name: commit-message-generator
description: 生成符合规范的 Git 提交信息
version: 1.0
---`,
            structure: `commit-message-generator/
└── SKILL.md`,
            scenarios: [
                '✓ 单一明确任务：生成 commit 信息',
                '✓ 5 分钟快速创建',
                '✓ 无需额外配置',
                '✓ 适合个人日常使用'
            ]
        },
        workflow: {
            title: '多步骤工作流示例：test-driven-development',
            yaml: `---
name: test-driven-development
description: TDD 开发流程自动化
version: 1.0
workflow:
  - 分析需求
  - 编写测试用例
  - 实现功能代码
  - 运行测试验证
  - 重构优化
---`,
            structure: `test-driven-development/
└── SKILL.md`,
            scenarios: [
                '✓ 多步骤流程：5-10 个步骤',
                '✓ 包含条件分支判断',
                '✓ 15-30 分钟创建',
                '✓ 适合团队标准化开发'
            ]
        },
        resource: {
            title: '资源依赖型示例：lesson-interaction-architect',
            yaml: `---
name: lesson-interaction-architect
description: 课程交互架构设计系统
version: 1.0
resources:
  - references/interaction-lenses.md
  - references/pattern-catalog.md
  - references/output-contracts.md
---`,
            structure: `lesson-interaction-architect/
├── SKILL.md
└── references/
    ├── interaction-lenses.md
    ├── pattern-catalog.md
    ├── pattern-stack-recipes.md
    └── output-contracts.md`,
            scenarios: [
                '✓ 复杂领域任务：10+ 步骤',
                '✓ 依赖外部参考文档',
                '✓ 1-2 小时创建',
                '✓ 适合企业级专业系统'
            ]
        }
    };

    // 更新内容函数
    function updateContent(dimension) {
        const data = dimensionData[dimension];
        if (!data) {
            console.warn('Invalid dimension:', dimension);
            return;
        }

        // 先清理旧动画
        gsap.killTweensOf([contentSimple, contentWorkflow, contentResource]);

        // 使用 requestAnimationFrame 批量更新 DOM
        requestAnimationFrame(() => {
            // 批量更新三栏内容
            contentSimple.innerHTML = data.simple.map(item =>
                `<div class="content-item">${item}</div>`
            ).join('');

            contentWorkflow.innerHTML = data.workflow.map(item =>
                `<div class="content-item">${item}</div>`
            ).join('');

            contentResource.innerHTML = data.resource.map(item =>
                `<div class="content-item">${item}</div>`
            ).join('');

            // GSAP 安全模式：set + to
            gsap.set([contentSimple, contentWorkflow, contentResource], { opacity: 0, y: 10 });
            gsap.to([contentSimple, contentWorkflow, contentResource], {
                opacity: 1,
                y: 0,
                duration: 0.4,
                stagger: 0.1,
                ease: 'power2.out'
            });
        });
    }

    // 切换维度
    window.switchDimension = function(dimension) {
        if (dimension === currentDimension) return;

        currentDimension = dimension;

        // 更新按钮状态
        dimensionBtns.forEach(btn => {
            if (btn.dataset.dimension === dimension) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // 更新内容
        updateContent(dimension);
    };

    // 显示示例
    window.showExample = function(type) {
        const data = exampleData[type];
        if (!data) return;

        currentExample = type;
        exampleTitle.textContent = data.title;

        // 预构建场景列表 HTML
        const scenariosHTML = data.scenarios
            .map(s => `<div class="scenario-item">${s}</div>`)
            .join('');

        exampleContent.innerHTML = `
            <div class="example-section">
                <h4>YAML Frontmatter</h4>
                <div class="code-block">${data.yaml}</div>
            </div>
            <div class="example-section">
                <h4>目录结构</h4>
                <div class="file-tree">${data.structure}</div>
            </div>
            <div class="example-section">
                <h4>适用场景</h4>
                <div class="scenario-list">${scenariosHTML}</div>
            </div>
        `;

        // 清理旧动画
        gsap.killTweensOf(exampleDetail);

        // 显示展开区（GSAP 安全模式：set + to）
        exampleDetail.style.display = 'block';
        gsap.set(exampleDetail, { opacity: 0, y: 20 });
        gsap.to(exampleDetail, {
            opacity: 1,
            y: 0,
            duration: 0.5,
            ease: 'power2.out'
        });
    };

    // 关闭示例
    window.closeExample = function() {
        gsap.killTweensOf(exampleDetail);
        gsap.to(exampleDetail, {
            opacity: 0,
            y: 20,
            duration: 0.3,
            ease: 'power2.in',
            onComplete: () => {
                exampleDetail.style.display = 'none';
                currentExample = null;
            }
        });
    };

    // 初始化
    updateContent('structure');

    // 返回清理函数
    return function cleanup() {
        gsap.killTweensOf([contentSimple, contentWorkflow, contentResource, exampleDetail]);
        if (window.switchDimension) delete window.switchDimension;
        if (window.showExample) delete window.showExample;
        if (window.closeExample) delete window.closeExample;
    };
};

// ========== S010B: Token经济学原理（简化版）==========
window.slideHooks['slides/S010B-token-economics.html'] = function() {
    // 场景数据
    const scenarioData = {
        test: {
            traditional: { tokens: 5000, cost: 0.025 },
            skill: { system: 200, skillPart: 300, total: 500, cost: 0.0025 }
        },
        review: {
            traditional: { tokens: 4500, cost: 0.0225 },
            skill: { system: 200, skillPart: 250, total: 450, cost: 0.00225 }
        },
        docs: {
            traditional: { tokens: 4000, cost: 0.020 },
            skill: { system: 200, skillPart: 200, total: 400, cost: 0.002 }
        }
    };

    // 获取元素
    const buttons = document.querySelectorAll('.scenario-btn');
    const traditionalTokens = document.getElementById('traditional-tokens');
    const traditionalTotal = document.getElementById('traditional-total');
    const traditionalCost = document.getElementById('traditional-cost');

    const skillSystemTokens = document.getElementById('skill-system-tokens');
    const skillSkillTokens = document.getElementById('skill-skill-tokens');
    const skillTotal = document.getElementById('skill-total');
    const skillCost = document.getElementById('skill-cost');

    const savingsPercent = document.getElementById('savings-percent');
    const savingsPercent2 = document.getElementById('savings-percent-2');

    // 检查元素是否存在
    if (!buttons.length || !traditionalTokens || !skillSystemTokens || !skillSkillTokens) {
        console.warn('S010B: Required elements not found');
        return;
    }

    let currentScenario = 'test';

    // 切换场景函数（简化版，直接更新数字）
    function switchScenario(scenario) {
        if (currentScenario === scenario) return;

        const data = scenarioData[scenario];
        if (!data) {
            console.warn('Invalid scenario:', scenario);
            return;
        }

        currentScenario = scenario;

        // 更新按钮状态
        buttons.forEach(btn => {
            if (btn.dataset.scenario === scenario) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // 计算节省百分比
        const savings = Math.round((1 - data.skill.total / data.traditional.tokens) * 100);

        // 直接更新数字（无动画）
        traditionalTokens.textContent = data.traditional.tokens;
        traditionalTotal.textContent = data.traditional.tokens;
        traditionalCost.textContent = '$' + data.traditional.cost.toFixed(4);

        skillSystemTokens.textContent = data.skill.system;
        skillSkillTokens.textContent = data.skill.skillPart;
        skillTotal.textContent = data.skill.total;
        skillCost.textContent = '$' + data.skill.cost.toFixed(4);

        savingsPercent.textContent = savings;
        savingsPercent2.textContent = savings;
    }

    // 绑定按钮点击事件
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            switchScenario(btn.dataset.scenario);
        });
    });

    // 初始化显示第一个场景
    switchScenario('test');

    // 返回清理函数
    return function cleanup() {
        buttons.forEach(btn => {
            btn.removeEventListener('click', switchScenario);
        });
    };
};

// ========== S022B: Skill在技术生态中的定位 ==========
window.slideHooks['S022B-skill-ecosystem-relations.html'] = function() {
    // 关系数据
    const relationData = {
        skill: {
            title: 'Skill：可插拔的领域专家大脑',
            content: `
                <div style="display:flex;flex-direction:column;gap:16px;">
                    <div>
                        <div style="font-weight:bold;color:var(--primary);margin-bottom:8px;">核心定位</div>
                        <div style="color:var(--text-secondary);line-height:1.6;">
                            Skill 是 Agent 的"可插拔领域专家大脑"，提供结构化的思考流程和专业判断标准，让 Agent 能够像领域专家一样处理复杂任务。
                        </div>
                    </div>
                    <div>
                        <div style="font-weight:bold;color:var(--primary);margin-bottom:8px;">与其他技术的关系</div>
                        <div style="color:var(--text-secondary);line-height:1.6;">
                            • 依赖 Tool 执行具体操作<br>
                            • 从 MCP Server 获取外部资源<br>
                            • 是 Prompt Template 的高级形态<br>
                            • 与 System Prompt 互补分工<br>
                            • 可替代或组合 Workflow
                        </div>
                    </div>
                </div>
            `
        },
        tool: {
            title: 'Skill vs Tool',
            content: `
                <div style="display:flex;flex-direction:column;gap:16px;">
                    <div style="display:inline-block;padding:6px 12px;background:rgba(var(--primary-rgb),0.15);border-radius:8px;color:var(--primary);font-size:0.9em;font-weight:600;width:fit-content;">依赖与互补</div>
                    <div>
                        <div style="font-weight:bold;color:var(--primary);margin-bottom:8px;">核心区别</div>
                        <div style="color:var(--text-secondary);line-height:1.6;">
                            • <strong>Skill</strong>: 指导"如何思考"——提供决策流程和判断标准<br>
                            • <strong>Tool</strong>: 提供"如何执行"——完成具体的操作任务
                        </div>
                    </div>
                    <div>
                        <div style="font-weight:bold;color:var(--primary);margin-bottom:8px;">典型场景</div>
                        <div style="color:var(--text-secondary);line-height:1.6;">
                            Skill 调用 Tool 完成具体操作。例如 <code>test-driven-development</code> Skill 会调用文件读取 Tool 和代码分析 Tool。
                        </div>
                    </div>
                </div>
            `
        },
        mcp: {
            title: 'Skill vs MCP Server',
            content: `
                <div style="display:flex;flex-direction:column;gap:16px;">
                    <div style="display:inline-block;padding:6px 12px;background:rgba(var(--primary-rgb),0.15);border-radius:8px;color:var(--primary);font-size:0.9em;font-weight:600;width:fit-content;">资源供给</div>
                    <div>
                        <div style="font-weight:bold;color:var(--primary);margin-bottom:8px;">核心区别</div>
                        <div style="color:var(--text-secondary);line-height:1.6;">
                            • <strong>MCP Server</strong>: 提供数据通道——连接外部服务和资源<br>
                            • <strong>Skill</strong>: 提供使用流程——如何利用这些资源完成任务
                        </div>
                    </div>
                    <div>
                        <div style="font-weight:bold;color:var(--primary);margin-bottom:8px;">典型场景</div>
                        <div style="color:var(--text-secondary);line-height:1.6;">
                            MCP Server 提供 GitHub API 访问能力，Skill 定义如何系统化地进行代码审查。
                        </div>
                    </div>
                </div>
            `
        },
        prompt: {
            title: 'Skill vs Prompt Template',
            content: `
                <div style="display:flex;flex-direction:column;gap:16px;">
                    <div style="display:inline-block;padding:6px 12px;background:rgba(var(--primary-rgb),0.15);border-radius:8px;color:var(--primary);font-size:0.9em;font-weight:600;width:fit-content;">包含与进化</div>
                    <div>
                        <div style="font-weight:bold;color:var(--primary);margin-bottom:8px;">核心区别</div>
                        <div style="color:var(--text-secondary);line-height:1.6;">
                            • <strong>Prompt Template</strong>: 静态文本模板——固定的提示词结构<br>
                            • <strong>Skill</strong>: 系统化、可路由的高级 Prompt——支持动态加载和流程控制
                        </div>
                    </div>
                    <div>
                        <div style="font-weight:bold;color:var(--primary);margin-bottom:8px;">演进关系</div>
                        <div style="color:var(--text-secondary);line-height:1.6;">
                            Skill 是 Prompt Template 的进化形态，增加了 frontmatter 元数据、Workflow 流程控制和资源依赖管理。
                        </div>
                    </div>
                </div>
            `
        },
        'system-prompt': {
            title: 'Skill vs System Prompt',
            content: `
                <div style="display:flex;flex-direction:column;gap:16px;">
                    <div style="display:inline-block;padding:6px 12px;background:rgba(var(--primary-rgb),0.15);border-radius:8px;color:var(--primary);font-size:0.9em;font-weight:600;width:fit-content;">互补与分离</div>
                    <div>
                        <div style="font-weight:bold;color:var(--primary);margin-bottom:8px;">核心区别</div>
                        <div style="color:var(--text-secondary);line-height:1.6;">
                            • <strong>System Prompt</strong>: 设定基础身份和红线——全局生效<br>
                            • <strong>Skill</strong>: 处理复杂业务逻辑——按需加载
                        </div>
                    </div>
                    <div>
                        <div style="font-weight:bold;color:var(--primary);margin-bottom:8px;">分工原则</div>
                        <div style="color:var(--text-secondary);line-height:1.6;">
                            System Prompt 保持精简（200-500 tokens），复杂的领域知识和流程控制交给 Skill 按需加载。
                        </div>
                    </div>
                </div>
            `
        },
        workflow: {
            title: 'Skill vs Workflow',
            content: `
                <div style="display:flex;flex-direction:column;gap:16px;">
                    <div style="display:inline-block;padding:6px 12px;background:rgba(var(--primary-rgb),0.15);border-radius:8px;color:var(--primary);font-size:0.9em;font-weight:600;width:fit-content;">替代或组合</div>
                    <div>
                        <div style="font-weight:bold;color:var(--primary);margin-bottom:8px;">核心区别</div>
                        <div style="color:var(--text-secondary);line-height:1.6;">
                            • <strong>Workflow</strong>: 刚性流程——固定的步骤序列<br>
                            • <strong>Skill</strong>: 保留灵活性——Agent 可根据情况调整执行路径
                        </div>
                    </div>
                    <div>
                        <div style="font-weight:bold;color:var(--primary);margin-bottom:8px;">选择建议</div>
                        <div style="color:var(--text-secondary);line-height:1.6;">
                            确定性强的任务用 Workflow，需要判断和灵活性的任务用 Skill。也可以组合使用：Workflow 触发 Skill。
                        </div>
                    </div>
                </div>
            `
        }
    };

    // 获取元素
    const viewButtons = document.querySelectorAll('.view-btn');
    const mapView = document.getElementById('map-view');
    const caseView = document.getElementById('case-view');
    const relationDetail = document.getElementById('relation-detail');
    const relationTitle = document.getElementById('relation-title');
    const relationContent = document.getElementById('relation-content');
    const nodes = document.querySelectorAll('.node');
    const connections = document.querySelectorAll('.connection-line');

    // 检查元素是否存在
    if (!mapView || !caseView || !relationDetail) {
        console.warn('S022B: Required elements not found');
        return;
    }

    let currentView = 'map';
    let currentNode = null;

    // 切换视图函数
    window.switchView = function(view) {
        if (currentView === view) return;
        currentView = view;

        // 更新按钮状态
        viewButtons.forEach(btn => {
            if (btn.dataset.view === view) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // 清理动画
        gsap.killTweensOf([mapView, caseView]);

        // 切换视图（修复：提前 set 初始状态）
        if (view === 'map') {
            // 先设置目标视图的初始状态
            mapView.style.display = 'block';
            gsap.set(mapView, { opacity: 0 });

            // 淡出当前视图
            gsap.set(caseView, { opacity: 1 });
            gsap.to(caseView, {
                opacity: 0,
                duration: 0.3,
                ease: 'power2.in',
                onComplete: () => {
                    caseView.style.display = 'none';
                }
            });

            // 淡入目标视图
            gsap.to(mapView, {
                opacity: 1,
                duration: 0.3,
                delay: 0.3,
                ease: 'power2.out'
            });
        } else {
            // 先设置目标视图的初始状态
            caseView.style.display = 'block';
            gsap.set(caseView, { opacity: 0 });

            // 淡出当前视图
            gsap.set(mapView, { opacity: 1 });
            gsap.to(mapView, {
                opacity: 0,
                duration: 0.3,
                ease: 'power2.in',
                onComplete: () => {
                    mapView.style.display = 'none';
                }
            });

            // 淡入目标视图
            gsap.to(caseView, {
                opacity: 1,
                duration: 0.3,
                delay: 0.3,
                ease: 'power2.out'
            });
        }
    };

    // 显示关系详情
    window.showRelation = function(node) {
        // 防止重复点击
        if (currentNode === node && relationDetail.style.display !== 'none') return;

        const data = relationData[node];
        if (!data) {
            console.warn('Invalid node:', node);
            return;
        }

        currentNode = node;

        // 更新节点高亮
        nodes.forEach(n => {
            if (n.dataset.node === node) {
                n.classList.add('active');
            } else {
                n.classList.remove('active');
            }
        });

        // 更新连接线高亮
        connections.forEach(line => {
            if (line.dataset.relation === node) {
                line.classList.add('active');
            } else {
                line.classList.remove('active');
            }
        });

        // 更新内容
        relationTitle.textContent = data.title;
        relationContent.innerHTML = data.content;

        // 显示详情卡片
        gsap.killTweensOf(relationDetail);
        relationDetail.style.display = 'block';
        gsap.set(relationDetail, { opacity: 0, y: 20 });
        gsap.to(relationDetail, {
            opacity: 1,
            y: 0,
            duration: 0.4,
            ease: 'power2.out'
        });
    };

    // 关闭关系详情
    window.closeRelation = function() {
        gsap.killTweensOf(relationDetail);
        gsap.to(relationDetail, {
            opacity: 0,
            y: 20,
            duration: 0.3,
            ease: 'power2.in',
            onComplete: () => {
                relationDetail.style.display = 'none';
                currentNode = null;

                // 清除高亮
                nodes.forEach(n => n.classList.remove('active'));
                connections.forEach(line => line.classList.remove('active'));
            }
        });
    };

    // 初始化：默认显示 Skill 节点信息
    setTimeout(() => {
        window.showRelation('skill');
    }, 500);

    // 返回清理函数
    return function cleanup() {
        gsap.killTweensOf([mapView, caseView, relationDetail]);

        // 清理节点和连接线状态
        nodes.forEach(n => n.classList.remove('active'));
        connections.forEach(line => line.classList.remove('active'));

        // 清理全局函数
        if (window.switchView) delete window.switchView;
        if (window.showRelation) delete window.showRelation;
        if (window.closeRelation) delete window.closeRelation;

        // 重置状态变量
        currentView = null;
        currentNode = null;
    };
};

function setActiveButton(buttons, activeButton, activeClass = 'active') {
    buttons.forEach((button) => {
        button.classList.remove(activeClass);
        button.classList.remove('btn-primary'); // 强制移除 btn-primary 类
        button.style.background = 'var(--bg-white)';
        button.style.color = 'var(--text-primary)';
        button.style.border = '1px solid var(--border)';
    });
    if (!activeButton) return;
    activeButton.classList.add(activeClass);
    activeButton.classList.add('btn-primary'); // 给选中按钮添加 btn-primary 类
    activeButton.style.background = 'var(--teal)';
    activeButton.style.color = 'var(--text-white)';
    activeButton.style.border = '1px solid var(--teal)';
}

function makeTag(text, tone) {
    const palette = {
        bad: ['rgba(220,38,38,0.08)', '#DC2626'],
        good: ['var(--teal-pale)', 'var(--teal)'],
        neutral: ['var(--bg-cool)', 'var(--text-secondary)'],
        warm: ['var(--amber-pale)', 'var(--amber)']
    };
    const [bg, fg] = palette[tone] || palette.neutral;
    return '<span style="padding:6px 12px;background:' + bg + ';color:' + fg + ';border-radius:var(--radius-sm);font-size:0.82rem;">' + text + '</span>';
}

/* ========== S001B: Wall Street Impact - Stock Crash Animation (Vertical Bars) ========== */
window.slideHooks['slides/S001B-wall-street-impact.html'] = function() {
  const playBtn = document.getElementById('play-btn');
  const stockBars = document.querySelectorAll('.stock-bar');
  const lossNumber = document.getElementById('loss-number');
  const currentTime = document.getElementById('current-time');
  const chartArea = document.getElementById('stock-chart-area');

  if (!playBtn || stockBars.length === 0) return;

  let isPlaying = false;
  let hasPlayedOnce = false;

  function playAnimation() {
    if (isPlaying) return;
    isPlaying = true;

    // 禁用播放按钮
    playBtn.disabled = true;
    playBtn.style.opacity = '0.5';

    // 重置所有股票柱状图到初始状态
    stockBars.forEach((bar) => {
      const percent = bar.parentElement.parentElement.querySelector('.stock-percent');
      const value = bar.querySelector('.stock-value');
      if (window.gsap) {
        window.gsap.set(bar, { height: '0%' });
      }
      if (percent) percent.textContent = '0%';
      if (value) value.style.opacity = '0';
    });

    // 阶段1：时间推进到发布时刻（10:30）
    if (window.gsap) {
      window.gsap.to({}, {
        duration: 1,
        onUpdate: function() {
          const progress = this.progress();
          const hour = 9 + Math.floor(progress * 1.5);
          const minute = Math.floor((progress * 1.5 - Math.floor(progress * 1.5)) * 60);
          currentTime.textContent = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
        },
        onComplete: () => {
          currentTime.textContent = '10:30';

          // 阶段2：柱状图先升起到满高度（显示初始市值）
          stockBars.forEach((bar, index) => {
            const value = bar.querySelector('.stock-value');

            window.gsap.to(bar, {
              height: '100%',
              duration: 0.8,
              delay: index * 0.1,
              ease: 'power2.out',
              onComplete: () => {
                if (value) {
                  window.gsap.to(value, { opacity: 1, duration: 0.3 });
                }
              }
            });
          });

          // 阶段3：暴跌动画（柱状图垂直收缩）
          window.gsap.to({}, {
            duration: 0.5,
            delay: 1.5,
            onComplete: () => {
              stockBars.forEach((bar, index) => {
                const drop = parseFloat(bar.dataset.drop);
                const initialValue = parseFloat(bar.dataset.initialValue);
                const percent = bar.parentElement.parentElement.querySelector('.stock-percent');
                const value = bar.querySelector('.stock-value');

                // 计算跌后高度（100% - drop%）
                const finalHeight = 100 - drop;

                // 垂直暴跌动画
                window.gsap.to(bar, {
                  height: finalHeight + '%',
                  duration: 1.5,
                  delay: index * 0.08,
                  ease: 'power4.in', // 加速下跌
                  onStart: () => {
                    // 添加崩塌效果
                    bar.classList.add('collapse-effect');
                    setTimeout(() => {
                      bar.classList.remove('collapse-effect');
                    }, 300);
                  },
                  onUpdate: function() {
                    const progress = this.progress();
                    const currentDrop = drop * progress;
                    const currentValue = initialValue * (1 - currentDrop / 100);

                    if (percent) {
                      percent.textContent = `-${currentDrop.toFixed(1)}%`;
                    }
                    if (value) {
                      value.textContent = `$${Math.round(currentValue)}亿`;
                    }
                  },
                  onComplete: () => {
                    // 添加震动效果
                    if (chartArea && index === stockBars.length - 1) {
                      chartArea.classList.add('shake-effect');
                      setTimeout(() => {
                        chartArea.classList.remove('shake-effect');
                      }, 400);
                    }
                  }
                });
              });
            }
          });

          // 阶段4：时间推进到收盘（16:00）
          window.gsap.to({}, {
            duration: 2,
            delay: 2.5,
            onUpdate: function() {
              const progress = this.progress();
              const hour = 10 + Math.floor(progress * 5.5);
              const minute = 30 + Math.floor((progress * 5.5 - Math.floor(progress * 5.5)) * 60);
              const displayHour = minute >= 60 ? hour + 1 : hour;
              const displayMinute = minute >= 60 ? minute - 60 : minute;
              currentTime.textContent = `${displayHour.toString().padStart(2, '0')}:${displayMinute.toString().padStart(2, '0')}`;
            },
            onComplete: () => {
              currentTime.textContent = '16:00';
            }
          });

          // 阶段5：市值蒸发数字滚动
          window.gsap.to({ value: 0 }, {
            value: 2850,
            duration: 2.5,
            delay: 2.8,
            ease: 'power2.out',
            onUpdate: function() {
              if (lossNumber) {
                lossNumber.textContent = Math.floor(this.targets()[0].value);
              }
            },
            onComplete: () => {
              if (lossNumber) {
                lossNumber.textContent = '2850';
              }
            }
          });

          // 背景颜色渐变（恐慌氛围）
          window.gsap.to(chartArea, {
            backgroundColor: 'rgba(220, 38, 38, 0.03)',
            duration: 2,
            delay: 2
          });

          // 动画结束后恢复播放按钮
          setTimeout(() => {
            isPlaying = false;
            playBtn.disabled = false;
            playBtn.style.opacity = '1';
            playBtn.innerHTML = '<span>↻</span><span>重新播放</span>';
          }, 5500);
        }
      });
    }
  }

  // 自动播放（首次进入页面）
  if (!hasPlayedOnce) {
    setTimeout(() => {
      playAnimation();
      hasPlayedOnce = true;
    }, 1000);
  }

  // 手动播放
  playBtn.addEventListener('click', playAnimation);

  // 清理函数
  return () => {
    playBtn.removeEventListener('click', playAnimation);
  };
};

/* ========== S001A: AI Coding Evolution Timeline ========== */
window.slideHooks['slides/S001A-ai-coding-evolution.html'] = function() {
  const container = document.getElementById('timeline-container');
  const nodes = document.querySelectorAll('.timeline-node');

  if (!container || nodes.length === 0) return;

  let isDragging = false;
  let startX = 0;
  let scrollLeft = 0;
  let activeNode = null;

  // 拖动功能
  container.addEventListener('mousedown', (e) => {
    // 如果点击的是节点圆点，不触发拖动
    if (e.target.classList.contains('node-dot')) return;

    isDragging = true;
    container.classList.add('dragging');
    startX = e.pageX - container.offsetLeft;
    scrollLeft = container.scrollLeft;
  });

  container.addEventListener('mouseleave', () => {
    isDragging = false;
    container.classList.remove('dragging');
  });

  container.addEventListener('mouseup', () => {
    isDragging = false;
    container.classList.remove('dragging');
  });

  container.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    e.preventDefault();
    const x = e.pageX - container.offsetLeft;
    const walk = (x - startX) * 1.5;
    container.scrollLeft = scrollLeft - walk;
  });

  // 点击节点展开/收起卡片
  nodes.forEach((node) => {
    const dot = node.querySelector('.node-dot');

    dot.addEventListener('click', (e) => {
      e.stopPropagation();

      // 如果点击的是当前激活节点，则收起
      if (activeNode === node) {
        node.classList.remove('active');
        activeNode = null;
      } else {
        // 收起其他节点
        nodes.forEach(n => n.classList.remove('active'));
        // 展开当前节点
        node.classList.add('active');
        activeNode = node;
      }
    });
  });

  // 默认展开 2025 节点（高亮节点）
  const highlightNode = document.querySelector('.timeline-node.highlight');
  if (highlightNode) {
    setTimeout(() => {
      highlightNode.classList.add('active');
      activeNode = highlightNode;
    }, 800);
  }

  // 清理函数
  return () => {
    container.removeEventListener('mousedown', () => {});
    container.removeEventListener('mouseleave', () => {});
    container.removeEventListener('mouseup', () => {});
    container.removeEventListener('mousemove', () => {});
  };
};

window.slideHooks['slides/S004-two-worlds.html'] = function() {
    const tasks = {
        tests: {
            beforeHtml: '<p style="font-size:1rem;line-height:1.8;margin:0 0 12px 0;color:var(--text-secondary);">模型可以解释怎么写测试，也能给一个大致模板，但它不知道你项目里的测试框架、目录约定、边界策略和下一步验证流程。</p><p style="font-size:0.92rem;line-height:1.7;margin:0;color:var(--text-tertiary);">结果通常停在“建议层”。</p>',
            afterHtml: '<p style="font-size:1rem;line-height:1.8;margin:0 0 12px 0;color:var(--text-primary);">Agent 先识别这是测试生成任务，再调用测试相关 Skill，输出更接近完成态的结果：测试骨架、边界案例、执行建议、验证路径。</p><p style="font-size:0.92rem;line-height:1.7;margin:0;color:var(--text-secondary);">结果从“会说”变成“能推进任务”。</p>',
            beforeTags: ['只会建议', '上下文补齐靠人', '不稳定'],
            afterTags: ['结构化结果', '更接近执行', '可复用'],
            takeaway: 'Skill 的价值，不是让 AI 更会解释，而是让它更有可能完成工作链。'
        },
        repo: {
            beforeHtml: '<p style="font-size:1rem;line-height:1.8;margin:0 0 12px 0;color:var(--text-secondary);">模型会建议你自己去搜目录、翻 README、找关键词，但“发现哪个 Skill 适合当前任务”这一步仍然大量依赖手工判断。</p><p style="font-size:0.92rem;line-height:1.7;margin:0;color:var(--text-tertiary);">结果停在“方向建议”。</p>',
            afterHtml: '<p style="font-size:1rem;line-height:1.8;margin:0 0 12px 0;color:var(--text-primary);">Agent 可以调起技能发现类 Skill，扫描候选能力、比对描述、返回更接近可执行的推荐路径。</p><p style="font-size:0.92rem;line-height:1.7;margin:0;color:var(--text-secondary);">连“找能力”本身都变成能力。</p>',
            beforeTags: ['搜索成本高', '筛选靠经验', '容易漏掉'],
            afterTags: ['快速定位', '推荐有依据', '更接近完成'],
            takeaway: 'Skill 不只解决业务任务，也能解决“发现合适能力”这种上游任务。'
        },
        markdown: {
            beforeHtml: '<p style="font-size:1rem;line-height:1.8;margin:0 0 12px 0;color:var(--text-secondary);">模型会告诉你如何整理文档，但批处理、统一结构、保持一致性仍然需要你自己反复操作。</p><p style="font-size:0.92rem;line-height:1.7;margin:0;color:var(--text-tertiary);">结果停在“方法建议”。</p>',
            afterHtml: '<p style="font-size:1rem;line-height:1.8;margin:0 0 12px 0;color:var(--text-primary);">Agent 识别出批处理文档任务后，调用文档整理 Skill，可以统一章节结构、提炼摘要，并产出标准化结果。</p><p style="font-size:0.92rem;line-height:1.7;margin:0;color:var(--text-secondary);">高频重复动作开始被模块化。</p>',
            beforeTags: ['批处理弱', '重复劳动多', '一致性差'],
            afterTags: ['统一 schema', '节省重复操作', '更易复用'],
            takeaway: '当任务有稳定输入输出结构时，Skill 很适合把它变成可复用能力。'
        }
    };

    const buttons = Array.from(document.querySelectorAll('.world-task-btn'));
    const before = document.getElementById('world-before');
    const after = document.getElementById('world-after');
    const beforeTags = document.getElementById('world-before-tags');
    const afterTags = document.getElementById('world-after-tags');
    const takeaway = document.getElementById('world-takeaway');
    if (!buttons.length || !before || !after || !beforeTags || !afterTags || !takeaway) return;

    const render = (key, button) => {
        const task = tasks[key];
        setActiveButton(buttons, button);
        before.innerHTML = task.beforeHtml;
        after.innerHTML = task.afterHtml;
        beforeTags.innerHTML = task.beforeTags.map((tag) => makeTag(tag, 'bad')).join('');
        afterTags.innerHTML = task.afterTags.map((tag) => makeTag(tag, 'good')).join('');
        takeaway.textContent = task.takeaway;
    };

    const onClick = (event) => render(event.currentTarget.dataset.task, event.currentTarget);
    buttons.forEach((button) => button.addEventListener('click', onClick));
    render('tests', buttons[0]);

    return function cleanup() {
        buttons.forEach((button) => button.removeEventListener('click', onClick));
    };
};

window.slideHooks['slides/S006-skill-not-prompt.html'] = function() {
    const explainers = {
        discover: '可发现：Agent 不只是知道“有这个能力”，而是更容易知道“什么时候该调用它”。',
        reuse: '可复用：同一份能力封装可以跨任务复用，而不是每次重写长指令。',
        compose: '可组合：多个 Skill 可以串起来形成更完整的工作链。',
        govern: '可治理：描述、流程、资源能被分层管理和持续优化。'
    };
    const buttons = Array.from(document.querySelectorAll('.lens-btn'));
    const explainer = document.getElementById('lens-explainer');
    if (!buttons.length || !explainer) return;

    const render = (lens, button) => {
        setActiveButton(buttons, button);
        explainer.innerHTML = '<p style="margin:0;color:var(--text-primary);">' + explainers[lens] + '</p>';
    };

    const onClick = (event) => render(event.currentTarget.dataset.lens, event.currentTarget);
    buttons.forEach((button) => button.addEventListener('click', onClick));
    render('discover', buttons[0]);
    return function cleanup() {
        buttons.forEach((button) => button.removeEventListener('click', onClick));
    };
};

window.slideHooks['slides/S010-routing-demo.html'] = function() {
    const requests = {
        tests: {
            query: '帮我给这个函数补单元测试',
            steps: [
                { title: '识别任务', desc: 'Agent 先判断这不是普通问答，而是一个代码任务。', payload: { intent: 'generate_unit_tests', confidence: 0.95 } },
                { title: '判断能力边界', desc: '仅靠聊天不够，需要更稳定的测试生成能力。', payload: { needs_skill: true, reason: '需要结构化生成与后续验证建议' } },
                { title: '匹配 Skill', desc: '在候选能力里挑最匹配的测试相关 Skill。', payload: { candidates: ['test-driven-development', 'bugfix-loop'], selected: 'test-driven-development' } },
                { title: '执行', desc: 'Skill 使用上下文生成测试骨架与边界案例。', payload: { outputs: ['test skeleton', 'edge cases', 'run notes'] } },
                { title: '整合输出', desc: 'Agent 把执行结果整理成用户可直接推进的输出。', payload: { response_shape: 'structured', includes: ['code', 'notes', 'next step'] } }
            ]
        },
        markdown: {
            query: '帮我整理这批 Markdown，统一成课程笔记结构',
            steps: [
                { title: '识别任务', desc: 'Agent 识别为批量文档规范化任务。', payload: { intent: 'normalize_markdown_notes', batch_mode: true } },
                { title: '判断能力边界', desc: '这个任务需要稳定 schema 和批处理能力。', payload: { needs_skill: true, reason: '涉及多文件处理与统一输出格式' } },
                { title: '匹配 Skill', desc: '选择更适合整理和结构化输出的 Skill。', payload: { candidates: ['doc-coauthoring', 'copy-editing'], selected: 'doc-coauthoring' } },
                { title: '执行', desc: 'Skill 对输入做清洗、归类、统一结构。', payload: { schema: ['title', 'summary', 'key points', 'next steps'] } },
                { title: '整合输出', desc: 'Agent 返回整理后的结果，并可继续路由到课件或发布工作流。', payload: { response_shape: 'batch_summary', next_handoff: 'optional' } }
            ]
        },
        findskill: {
            query: '帮我找适合做 PDF 处理的 Skill',
            steps: [
                { title: '识别任务', desc: '这不是直接做 PDF，而是先发现合适能力。', payload: { intent: 'discover_skill', target: 'pdf_processing' } },
                { title: '判断能力边界', desc: '需要先扫描技能目录和候选能力。', payload: { needs_skill: true, reason: '需要能力发现与推荐' } },
                { title: '匹配 Skill', desc: 'Agent 匹配到发现类 Skill，而不是直接执行 PDF 工作。', payload: { candidates: ['find-skills', 'pdf'], selected: 'find-skills' } },
                { title: '执行', desc: 'Skill 扫描生态或本地技能，寻找 PDF 相关候选。', payload: { action: 'scan_catalog', likely_match: 'pdf' } },
                { title: '整合输出', desc: '输出的是推荐能力和下一步，而不是最终 PDF 结果。', payload: { output_type: 'recommendation' } }
            ]
        }
    };

    const requestButtons = Array.from(document.querySelectorAll('.route-request-btn'));
    const stepCards = Array.from(document.querySelectorAll('.route-step-card'));
    const userQuery = document.getElementById('route-user-query');
    const stageTitle = document.getElementById('route-stage-title');
    const stageDesc = document.getElementById('route-stage-desc');
    const routeJson = document.getElementById('route-json');
    const nextBtn = document.getElementById('route-next-btn');
    const resetBtn = document.getElementById('route-reset-btn');
    const status = document.getElementById('route-status');

    if (!requestButtons.length || !stepCards.length || !userQuery || !stageTitle || !stageDesc || !routeJson || !nextBtn || !resetBtn || !status) return;

    let currentRequest = 'tests';
    let currentStep = -1;

    const resetSteps = () => {
        currentStep = -1;
        stepCards.forEach((card) => card.classList.remove('active', 'done'));
        stageTitle.textContent = '准备开始';
        stageDesc.textContent = '点击“开始演示”，逐步观察 Agent 如何判断是否要调用 Skill。';
        routeJson.textContent = JSON.stringify({ status: 'idle', next: 'start_demo' }, null, 2);
        status.textContent = '准备就绪：点击开始，逐步观察 Agent 如何做能力判断。';
        nextBtn.textContent = '开始演示';
    };

    const renderRequest = (key, button) => {
        currentRequest = key;
        userQuery.textContent = requests[key].query;
        setActiveButton(requestButtons, button);
        resetSteps();
    };

    const advanceStep = () => {
        const steps = requests[currentRequest].steps;
        if (currentStep >= steps.length - 1) return;
        currentStep += 1;

        stepCards.forEach((card, idx) => {
            card.classList.toggle('active', idx === currentStep);
            card.classList.toggle('done', idx < currentStep);
        });

        const step = steps[currentStep];
        stageTitle.textContent = step.title;
        stageDesc.textContent = step.desc;
        routeJson.textContent = JSON.stringify(step.payload, null, 2);
        status.textContent = '当前阶段：' + step.title;
        if (currentStep === steps.length - 1) nextBtn.textContent = '已完成';
    };

    const onRequestClick = (event) => renderRequest(event.currentTarget.dataset.request, event.currentTarget);
    requestButtons.forEach((button) => button.addEventListener('click', onRequestClick));
    nextBtn.addEventListener('click', advanceStep);
    resetBtn.addEventListener('click', resetSteps);

    renderRequest('tests', requestButtons[0]);

    return function cleanup() {
        requestButtons.forEach((button) => button.removeEventListener('click', onRequestClick));
        nextBtn.removeEventListener('click', advanceStep);
        resetBtn.removeEventListener('click', resetSteps);
    };
};

window.slideHooks['slides/S013-semantic-zoom.html'] = function() {
    const explainers = {
        overview: '先从最外层看：对使用者来说，Skill 是 Agent 在需要时会拿来解决问题的能力模块。',
        folder: '再往里看：它不是一个神秘黑盒，而是可以被组织、描述和调用的文件结构。',
        skillmd: 'SKILL.md 是核心文件。它包含 frontmatter（路由层）和 body（控制层），决定 Skill 何时被触发、如何执行。',
        references: 'references/ 存放深入知识和参考文档，让 Skill 保持简洁的同时能够处理复杂场景。',
        scripts: 'scripts/ 存放可执行脚本，把重复且脆弱的操作变成确定性执行。',
        assets: 'assets/ 存放模板和输出材料，提供可复用的结构化资源。'
    };
    const detailMap = {
        skillmd: {
            title: 'SKILL.md：唯一必需的核心文件',
            items: [
                'frontmatter（--- 之间）：定义 name、description，决定何时触发',
                'body（Markdown 正文）：定义 Goal、Workflow、约束和验证规则',
                '这两部分在同一个文件中，不是分开的'
            ]
        },
        references: {
            title: 'references/：深入知识和变体规则',
            items: [
                '📄 示例文件：api-reference.md',
                '存放不适合塞进 SKILL.md 的长知识、细分分支、案例和补充说明',
                '由 SKILL.md 在特定分支中读取，帮助 Skill 保持短而强'
            ]
        },
        scripts: {
            title: 'scripts/：重复且脆弱的动作脚本化',
            items: [
                '📄 示例文件：test-runner.py',
                '当某个操作高频、容易错、最好确定性执行时，就应该进入 scripts',
                '由 SKILL.md 在需要时调用，把不稳定的人工步骤变成稳定的执行步骤'
            ]
        },
        assets: {
            title: 'assets/：模板、输出材料和复用结构',
            items: [
                '📄 示例文件：report-template.json',
                '存放可复用的模板、配置文件、输出格式定义',
                '让 Skill 输出保持一致性和专业性'
            ]
        }
    };

    const overview = document.getElementById('zoom-view-overview');
    const folder = document.getElementById('zoom-view-folder');
    const detail = document.getElementById('zoom-view-detail');
    const explainer = document.getElementById('zoom-explainer');
    const detailTitle = document.getElementById('zoom-detail-title');
    const detailBody = document.getElementById('zoom-detail-body');
    const focusBtn = document.querySelector('.zoom-focus');
    const folderButtons = Array.from(document.querySelectorAll('.zoom-folder-item[data-view]'));
    const backBtn = document.getElementById('zoom-back-btn');
    const overviewBtn = document.getElementById('zoom-overview-btn');
    if (!overview || !folder || !detail || !explainer || !detailTitle || !detailBody || !focusBtn || !backBtn || !overviewBtn) return;

    let currentLevel = 'overview';

    const showLevel = (level) => {
        currentLevel = level;
        overview.style.display = level === 'overview' ? 'block' : 'none';
        folder.style.display = level === 'folder' ? 'block' : 'none';
        detail.style.display = ['skillmd', 'references', 'scripts', 'assets'].includes(level) ? 'block' : 'none';

        if (level === 'overview') {
            explainer.textContent = explainers.overview;
        } else if (level === 'folder') {
            explainer.textContent = explainers.folder;
        } else {
            const block = detailMap[level];
            detailTitle.textContent = block.title;
            detailBody.innerHTML = block.items.map((item) => '<div style="padding:14px 16px;border-radius:var(--radius-md);background:var(--bg-cool);color:var(--text-primary);">' + item + '</div>').join('');
            explainer.textContent = explainers[level];
        }
    };

    const toFolder = () => showLevel('folder');
    const toOverview = () => showLevel('overview');
    const onFolderClick = (event) => showLevel(event.currentTarget.dataset.view);
    const onBack = () => showLevel(currentLevel === 'folder' ? 'overview' : 'folder');

    focusBtn.addEventListener('click', toFolder);
    folderButtons.forEach((button) => button.addEventListener('click', onFolderClick));
    backBtn.addEventListener('click', onBack);
    overviewBtn.addEventListener('click', toOverview);
    showLevel('overview');

    return function cleanup() {
        focusBtn.removeEventListener('click', toFolder);
        folderButtons.forEach((button) => button.removeEventListener('click', onFolderClick));
        backBtn.removeEventListener('click', onBack);
        overviewBtn.removeEventListener('click', toOverview);
    };
};

window.slideHooks['slides/S013A-skill-directory-map.html'] = function() {
    const data = {
        frontmatter: {
            title: 'frontmatter：先被发现，能力才有机会被用到',
            desc: '它是 Skill 的最前置入口，决定 Agent 是否容易理解这份能力适合什么任务、不适合什么任务。',
            tags: ['路由层', '触发边界', '先被发现'],
            coop: ['和 `SKILL.md` 协同，决定”进来之后做什么”', '定义触发条件和元信息，让 Agent 知道何时调用']
        },
        skillmd: {
            title: 'SKILL.md：把能力真正组织起来',
            desc: '这是控制层。它告诉模型目标、步骤、分支、约束和验证方式，决定 Skill 是”会说”还是”能稳定执行”。',
            tags: ['控制层', '执行路径', '分支与约束'],
            coop: ['读取 `references/` 深入知识', '调用 `scripts/` 执行重复动作', '使用 `assets/` 提供模板与输出材料']
        },
        references: {
            title: 'references/：深入知识和变体规则',
            desc: '把不适合塞进 `SKILL.md` 的长知识、细分分支、案例和补充说明放在这里。',
            tags: ['支撑层', '知识细节'],
            coop: ['由 `SKILL.md` 在特定分支中读取', '帮助 Skill 保持短而强，不被细节淹没']
        },
        scripts: {
            title: 'scripts/：重复且脆弱的动作最好脚本化',
            desc: '当某个操作高频、容易错、最好确定性执行时，就应该进入 scripts，而不是每次让模型口头推理。',
            tags: ['支撑层', '确定性执行'],
            coop: ['由 `SKILL.md` 在需要时调用', '把不稳定的人工步骤变成稳定的执行步骤']
        },
        assets: {
            title: 'assets/：输出模板和复用材料',
            desc: '模板、骨架、样例、标准输出材料通常应该放在这里，而不是分散在正文里。',
            tags: ['支撑层', '复用产物'],
            coop: ['由 `SKILL.md` 选择合适资产', '让 Skill 的输出更快进入可交付状态']
        }
    };

    const buttons = Array.from(document.querySelectorAll('.skill-dir-btn'));
    const title = document.getElementById('dir-role-title');
    const desc = document.getElementById('dir-role-desc');
    const tags = document.getElementById('dir-role-tags');
    const coop = document.getElementById('dir-role-coop');
    if (!buttons.length || !title || !desc || !tags || !coop) return;

    const render = (key, button) => {
        const node = data[key];
        setActiveButton(buttons, button);
        title.textContent = node.title;
        desc.textContent = node.desc;
        tags.innerHTML = node.tags.map((tag) => makeTag(tag, 'good')).join('');
        coop.innerHTML = node.coop.map((item) => '<div style="padding:12px 14px;border-radius:var(--radius-md);background:var(--bg-cool);color:var(--text-primary);">' + item + '</div>').join('');
    };

    const onClick = (event) => render(event.currentTarget.dataset.node, event.currentTarget);
    buttons.forEach((button) => button.addEventListener('click', onClick));
    render('frontmatter', buttons[0]);

    return function cleanup() {
        buttons.forEach((button) => button.removeEventListener('click', onClick));
    };
};

window.slideHooks['slides/S013B-skill-collaboration-map.html'] = function() {
    const flows = {
        discover: {
            route: 'frontmatter 先告诉 Agent：这份能力适合什么请求、什么时候该触发。',
            control: 'SKILL.md 再决定进入后应该走哪条工作流，而不是自由发挥。',
            support: 'references 提供判断细节，assets 提供标准输出结构。',
            summary: '能力发现的关键不是“存在这个 Skill”，而是 Agent 能否读懂它的触发语义。'
        },
        execute: {
            route: 'frontmatter 帮 Agent 判断“现在是不是 Skill 问题”。',
            control: 'SKILL.md 把任务拆成步骤、分支、约束和验证。',
            support: 'scripts 负责重复且脆弱的执行动作，references 补深知识，assets 提供模板。',
            summary: '执行任务时，三层的关系是：先路由，后控制，再调用支撑资源把结果做实。'
        },
        maintain: {
            route: 'frontmatter 决定这份能力是否仍然保持清晰边界。',
            control: 'SKILL.md 是最常见的优化点：流程、分支、验证是否清楚。',
            support: 'references、scripts、assets 会随着经验积累被不断补强。',
            summary: '持续维护本质上是在同步优化三层，而不是只改一个文案。'
        }
    };

    const buttons = Array.from(document.querySelectorAll('.skill-flow-btn'));
    const route = document.getElementById('flow-route');
    const control = document.getElementById('flow-control');
    const support = document.getElementById('flow-support');
    const summary = document.getElementById('flow-summary');
    if (!buttons.length || !route || !control || !support || !summary) return;

    const render = (key, button) => {
        const flow = flows[key];
        setActiveButton(buttons, button);
        route.textContent = flow.route;
        control.textContent = flow.control;
        support.textContent = flow.support;
        summary.textContent = flow.summary;
    };

    const onClick = (event) => render(event.currentTarget.dataset.flow, event.currentTarget);
    buttons.forEach((button) => button.addEventListener('click', onClick));
    render('discover', buttons[0]);

    return function cleanup() {
        buttons.forEach((button) => button.removeEventListener('click', onClick));
    };
};

window.slideHooks['slides/S017-ecosystem-map.html'] = function() {
    const data = {
        public: {
            title: '公开生态：skills.sh / 社区能力库',
            desc: '适合快速发现、体验和借鉴模式。你可以把它理解为 Agent Skills 的公开能力市场。',
            points: ['适合先体验和学习范式', '安装速度快，适合验证方向', '质量差异较大，需要判断边界']
        },
        local: {
            title: '本地私有 Skills',
            desc: '这是团队最容易积累竞争力的地方。它们通常贴着你的真实工作流、生长在你的项目里。',
            points: ['和团队语境最贴合', '可逐步沉淀为内部资产', '更适合长期优化']
        },
        platform: {
            title: '平台专属 Skills',
            desc: '某些能力只有在特定 Agent 平台里才真正成立，因为它依赖平台工具、目录或运行时。',
            points: ['能力边界更明确', '对平台依赖更强', '迁移成本通常更高']
        },
        finder: {
            title: '能力发现工具',
            desc: '找 Skill 本身也可以被 Skill 化。它帮助 Agent 更快地扫描、筛选和推荐能力。',
            points: ['适合作为上游入口能力', '降低技能搜索成本', '让生态更容易被真正使用']
        }
    };

    const buttons = Array.from(document.querySelectorAll('.ecosystem-node'));
    const title = document.getElementById('ecosystem-title');
    const desc = document.getElementById('ecosystem-desc');
    const points = document.getElementById('ecosystem-points');
    if (!buttons.length || !title || !desc || !points) return;

    const render = (key, button) => {
        const block = data[key];
        setActiveButton(buttons, button);
        title.textContent = block.title;
        desc.textContent = block.desc;
        points.innerHTML = block.points.map((item) => '<div style="padding:12px 14px;border-radius:var(--radius-md);background:var(--bg-cool);color:var(--text-primary);">' + item + '</div>').join('');
    };

    const onClick = (event) => render(event.currentTarget.dataset.node, event.currentTarget);
    buttons.forEach((button) => button.addEventListener('click', onClick));
    render('public', buttons[0]);
    return function cleanup() {
        buttons.forEach((button) => button.removeEventListener('click', onClick));
    };
};

window.slideHooks['slides/S020-task-quiz.html'] = function() {
    const questions = [
        {
            task: '我已经知道要怎么做，只是想让 AI 帮我把这个函数写成中文解释。',
            answer: 'none',
            title: '不一定需要 Skill',
            desc: '这更像普通语言表达或总结任务，直接对话往往就够了。',
            tags: ['普通语言任务', '无需外部能力']
        },
        {
            task: '帮我找出当前环境里已经安装的 PDF 处理能力，并告诉我下一步怎么用。',
            answer: 'general',
            title: '更像通用发现类 Skill',
            desc: '这里需要的是能力发现与推荐，而不是直接执行 PDF 处理本身。',
            tags: ['发现能力', '推荐路径']
        },
        {
            task: '帮我读取这个项目目录里的私有 Skill 定义，然后判断哪个最适合当前平台。',
            answer: 'platform',
            title: '需要平台特定 Skill',
            desc: '这个任务强依赖当前平台目录、上下文和运行环境，不是完全通用的能力。',
            tags: ['平台依赖', '环境相关']
        },
        {
            task: '把一批 Markdown 整理成课程大纲，再转换成 HTML 课件结构。',
            answer: 'combo',
            title: '需要多个 Skill 组合',
            desc: '这类任务天然跨越多个阶段：整理、结构化、课件化，通常不止一个 Skill。',
            tags: ['多阶段', '组合能力']
        }
    ];

    const taskBox = document.getElementById('quiz-task');
    const optionButtons = Array.from(document.querySelectorAll('.quiz-option'));
    const nextBtn = document.getElementById('quiz-next-btn');
    const revealBtn = document.getElementById('quiz-reveal-btn');
    const title = document.getElementById('quiz-result-title');
    const desc = document.getElementById('quiz-result-desc');
    const tags = document.getElementById('quiz-result-tags');
    if (!taskBox || !optionButtons.length || !nextBtn || !revealBtn || !title || !desc || !tags) return;

    let index = 0;
    let chosen = null;

    const renderQuestion = () => {
        const q = questions[index];
        chosen = null;
        taskBox.textContent = q.task;
        title.textContent = '准备判断';
        desc.textContent = '先选一个答案，再点击“揭示答案”看推荐路径。';
        tags.innerHTML = '';
        optionButtons.forEach((button) => {
            button.classList.remove('active');
            button.style.background = 'var(--bg-white)';
            button.style.color = 'var(--text-primary)';
            button.style.border = '1px solid var(--border)';
        });
    };

    const onChoose = (event) => {
        chosen = event.currentTarget.dataset.answer;
        setActiveButton(optionButtons, event.currentTarget);
    };

    const reveal = () => {
        const q = questions[index];
        const right = chosen === q.answer;
        title.textContent = right ? '判断正确' : '更推荐的答案是：' + q.title;
        desc.textContent = q.desc;
        tags.innerHTML = q.tags.map((tag) => makeTag(tag, right ? 'good' : 'warm')).join('');
    };

    const next = () => {
        index = (index + 1) % questions.length;
        renderQuestion();
    };

    optionButtons.forEach((button) => button.addEventListener('click', onChoose));
    revealBtn.addEventListener('click', reveal);
    nextBtn.addEventListener('click', next);
    renderQuestion();

    return function cleanup() {
        optionButtons.forEach((button) => button.removeEventListener('click', onChoose));
        revealBtn.removeEventListener('click', reveal);
        nextBtn.removeEventListener('click', next);
    };
};

window.slideHooks['slides/S021-boundary-counterfactual.html'] = function() {
    const scenes = {
        vague: {
            badTitle: '设计错了：触发描述模糊',
            badDesc: 'Agent 不知道什么时候该调用这个 Skill，结果要么触发不到，要么误触发。',
            goodTitle: '设计对了：触发条件清晰',
            goodDesc: 'Skill 明确告诉 Agent 适用场景、非适用场景和典型对象，命中率明显更高。',
            takeaway: '再强的能力，如果找不到正确入口，也很难发挥价值。'
        },
        shallow: {
            badTitle: '设计错了：只有一句笼统说明',
            badDesc: 'SKILL.md 没有工作流和约束，模型进来之后只能自由发挥。',
            goodTitle: '设计对了：流程与约束明确',
            goodDesc: 'Skill 把目标、步骤、限制和验证都交代清楚，输出稳定性明显更高。',
            takeaway: 'Skill 不是一句口号，它需要一套可执行的控制层。'
        },
        missing: {
            badTitle: '设计错了：支撑资源缺失',
            badDesc: '需要参考知识、模板或脚本时，模型没有抓手，只能回退到泛化回答。',
            goodTitle: '设计对了：资源层补齐',
            goodDesc: 'references、scripts、assets 到位后，Skill 才更像真正可复用能力。',
            takeaway: '资源层不是装饰，而是把能力做实的关键。'
        }
    };

    const buttons = Array.from(document.querySelectorAll('.boundary-mode-btn'));
    const badTitle = document.getElementById('bf-bad-title');
    const badDesc = document.getElementById('bf-bad-desc');
    const goodTitle = document.getElementById('bf-good-title');
    const goodDesc = document.getElementById('bf-good-desc');
    const takeaway = document.getElementById('bf-takeaway');
    if (!buttons.length || !badTitle || !badDesc || !goodTitle || !goodDesc || !takeaway) return;

    const render = (key, button) => {
        const scene = scenes[key];
        setActiveButton(buttons, button);
        badTitle.textContent = scene.badTitle;
        badDesc.textContent = scene.badDesc;
        goodTitle.textContent = scene.goodTitle;
        goodDesc.textContent = scene.goodDesc;
        takeaway.textContent = scene.takeaway;
    };

    const onClick = (event) => render(event.currentTarget.dataset.scene, event.currentTarget);
    buttons.forEach((button) => button.addEventListener('click', onClick));
    render('vague', buttons[0]);
    return function cleanup() {
        buttons.forEach((button) => button.removeEventListener('click', onClick));
    };
};

window.slideHooks['slides/S024-learning-roadmap.html'] = function() {
    const phases = [
        {
            title: '阶段 1：体验',
            desc: '先跑起来，感受到 Skill 的价值差异，建立“为什么需要它”的直觉认知。',
            check: '验证点：你能说出 Skill 解决的不是“不会回答”，而是“能力边界”。'
        },
        {
            title: '阶段 2：理解',
            desc: '开始看懂分类、路由、生态和结构，能判断一个任务是不是 Skill 问题。',
            check: '验证点：你能对新任务做出初步的能力判断。'
        },
        {
            title: '阶段 3：设计',
            desc: '开始站在创建者视角，理解 frontmatter、SKILL.md 和资源层如何协同工作。',
            check: '验证点：你能拆解一个 Skill 的三层结构。'
        },
        {
            title: '阶段 4：创造',
            desc: '独立创建、测试、优化 Skill，并持续打磨触发、流程和质量。',
            check: '验证点：你能从需求出发设计一份可用 Skill。'
        }
    ];

    const cards = Array.from(document.querySelectorAll('.roadmap-card'));
    const title = document.getElementById('roadmap-detail-title');
    const desc = document.getElementById('roadmap-detail-desc');
    const check = document.getElementById('roadmap-detail-check');
    if (!cards.length || !title || !desc || !check) return;

    const render = (idx) => {
        cards.forEach((card, cardIdx) => card.classList.toggle('active', cardIdx === idx));
        title.textContent = phases[idx].title;
        desc.textContent = phases[idx].desc;
        check.textContent = phases[idx].check;
    };

    const onClick = (event) => render(Number(event.currentTarget.dataset.phase));
    cards.forEach((card) => card.addEventListener('click', onClick));
    render(0);

    return function cleanup() {
        cards.forEach((card) => card.removeEventListener('click', onClick));
    };
};

window.slideHooks['slides/S013C-skill-tree-explorer.html'] = function() {
  // 数据结构（通用版 - 原有数据）
  const skillTreeGeneral = {
    name: 'my-skill',
    type: 'root',
    icon: '📦',
    layer: 'root',
    expanded: true,
    description: 'Skill 根目录，包含核心文件和可选的支撑目录',
    why: '所有 Skill 必须有一个根目录作为命名空间，避免与其他 Skill 冲突',
    example: '通常以 kebab-case 命名，如：test-driven-development、bugfix-loop、pdf、frontend-design',
    collaboration: [
      '必须包含 SKILL.md 核心文件',
      '可选地添加 references/、scripts/、assets/ 等支撑目录',
      '⚠️ 目录结构非常灵活，没有固定模板，根据需要自定义'
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
name: test-driven-development
description: 为代码生成单元测试
---

# Test Driven Development

## Goal
生成高质量单元测试

## Workflow
1. 分析函数签名和参数
2. 识别边界条件
3. 生成测试骨架
4. 补充断言逻辑`,
        collaboration: [
          'frontmatter（--- 之间的 YAML）定义 Skill 的元信息和触发条件',
          '正文（Markdown）定义执行流程、约束和最佳实践',
          '可以引用 references/ 中的深入知识',
          '可以调用 scripts/ 中的执行脚本',
          '可以使用 assets/ 中的输出模板'
        ]
      },
      {
        name: 'references/',
        type: 'directory',
        icon: '📁',
        layer: 'optional',
        expanded: false,
        description: '📚 可选目录：深入知识、细分规则和补充说明（也可能叫 reference/ 或 reference.md）',
        why: '避免 SKILL.md 被细节淹没，保持主流程清晰；当 Skill 需要大量背景知识时使用',
        example: '真实案例：skill-creator 有 references/schemas.md；pdf 有 reference.md（文件）；mcp-builder 有 reference/（单数）',
        collaboration: [
          '由 SKILL.md 在需要时引用',
          '帮助 Skill 保持简洁，不被细节淹没',
          '⚠️ 命名不统一：references/（复数）、reference/（单数）、reference.md（文件）都存在'
        ],
        children: [
          {
            name: 'deep-dive.md',
            type: 'file',
            icon: '📄',
            layer: 'optional',
            description: '深入知识文档（示例）',
            why: '提供超出主流程的详细说明和背景知识',
            example: `## 测试框架对比
### Jest vs Mocha
- Jest: 零配置，内置断言库
- Mocha: 灵活，需要额外配置

### 最佳实践
- 使用描述性的测试名称
- 每个测试只验证一个行为
- 避免测试实现细节`,
            collaboration: []
          },
          {
            name: 'api-reference.md',
            type: 'file',
            icon: '📄',
            layer: 'optional',
            description: 'API 参考文档（示例）',
            why: '提供完整的 API 说明和参数列表',
            example: `## generateTest(functionCode, options)

### 参数
- functionCode (string): 要测试的函数代码
- options.framework (string): 测试框架（jest/mocha/vitest）
- options.coverage (boolean): 是否生成覆盖率报告

### 返回值
- testCode (string): 生成的测试代码`,
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
        description: '🔧 可选目录：执行脚本（通常是 Python 脚本，也可能是 Shell 脚本）',
        why: '重复且脆弱的操作应该脚本化，而不是每次让模型口头推理；提高执行的确定性和可靠性',
        example: '真实案例：skill-creator 有 run_eval.py、generate_report.py；pdf 有 scripts/ 目录',
        collaboration: [
          '由 SKILL.md 在需要时调用',
          '把不稳定的人工步骤变成稳定的执行步骤',
          '⚠️ 官方 skills 中通常是 Python 脚本（.py），而非 Shell 脚本（.sh）'
        ],
        children: [
          {
            name: 'run_eval.py',
            type: 'file',
            icon: '🐍',
            layer: 'optional',
            description: '评估脚本（示例，参考 skill-creator）',
            why: '自动化评估 Skill 的执行效果，提供量化指标',
            example: `#!/usr/bin/env python3
"""
运行 Skill 评估
"""
import subprocess
import json

def run_tests():
    result = subprocess.run(['npm', 'test'], capture_output=True)
    return result.returncode == 0

if __name__ == '__main__':
    success = run_tests()
    print(json.dumps({'success': success}))`,
            collaboration: []
          },
          {
            name: 'generate_report.py',
            type: 'file',
            icon: '🐍',
            layer: 'optional',
            description: '报告生成脚本（示例，参考 skill-creator）',
            why: '自动生成执行报告，便于分析和改进',
            example: `#!/usr/bin/env python3
"""
生成 Skill 执行报告
"""
def generate_report(results):
    report = f"""
# Skill 执行报告

## 测试结果
- 通过: {results['passed']}
- 失败: {results['failed']}
- 覆盖率: {results['coverage']}%
"""
    return report`,
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
        description: '🎨 可选目录：输出模板和复用材料（较少使用，只有少数 Skill 有此目录）',
        why: '标准化输出格式，提高复用性，让 Skill 的输出更快进入可交付状态',
        example: '真实案例：skill-creator 有 assets/eval_review.html；大部分 Skill 没有此目录',
        collaboration: [
          '由 SKILL.md 选择合适模板',
          '让 Skill 的输出更快进入可交付状态',
          '⚠️ 这是较少使用的目录，不是必需的'
        ],
        children: [
          {
            name: 'test-template.js',
            type: 'file',
            icon: '📄',
            layer: 'optional',
            description: '测试文件模板（示例）',
            why: '提供标准化的测试文件结构',
            example: `describe('{{functionName}}', () => {
  it('should {{behavior}}', () => {
    // 测试代码
  });
});`,
            collaboration: []
          },
          {
            name: 'report-template.md',
            type: 'file',
            icon: '📄',
            layer: 'optional',
            description: '报告模板（示例）',
            why: '提供标准化的报告格式',
            example: `# 测试报告

## 概述
- 测试数量: {{testCount}}
- 通过率: {{passRate}}%

## 详细结果
{{results}}`,
            collaboration: []
          }
        ]
      },
      {
        name: '⚠️ 其他自定义目录',
        type: 'note',
        icon: '💡',
        layer: 'flexible',
        expanded: false,
        description: '目录结构完全灵活，可以根据 Skill 的特点自定义',
        why: '官方 Skill 的目录结构非常多样化，没有固定模板',
        example: `真实案例：
- claude-api: 按编程语言组织（python/, typescript/, java/, go/...）
- skill-creator: 有 eval-viewer/ 目录用于评估可视化
- pdf: 直接有 forms.md 和 reference.md 文件
- frontend-design: 只有 SKILL.md，没有任何其他目录`,
        collaboration: [
          '✅ 唯一必需的是 SKILL.md',
          '✅ 其他目录都是可选的，根据需要添加',
          '✅ 可以创建任何符合你需求的目录结构',
          '✅ 参考官方 Skill 的组织方式，但不必完全照搬'
        ]
      }
    ]
  };

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

  // S013C: Skill 目录树浏览器的渲染逻辑
  // DOM 元素
  const treeRoot = document.getElementById('tree-root');
  const detailTitle = document.getElementById('detail-title');
  const detailMeta = document.getElementById('detail-meta');
  const detailContent = document.getElementById('detail-content');
  const detailQuickJump = document.getElementById('detail-quick-jump');
  const detailBreadcrumb = document.getElementById('detail-breadcrumb');

  let selectedNode = null;
  let allNodes = [];

  // 渲染树形节点
  function renderNode(node, level = 0, path = []) {
    const nodeEl = document.createElement('div');
    nodeEl.className = 'tree-node';
    nodeEl.dataset.nodeName = node.name;
    nodeEl.dataset.nodePath = JSON.stringify([...path, node.name]);

    const labelEl = document.createElement('div');
    labelEl.className = 'tree-node-label';

    const expandIcon = node.type === 'directory'
      ? `<span class="tree-expand-icon">${node.expanded ? '▼' : '▶'}</span>`
      : '';

    labelEl.innerHTML = `
      ${expandIcon}
      <span class="tree-icon">${node.icon}</span>
      <span class="tree-name">${node.name}</span>
    `;

    nodeEl.appendChild(labelEl);

    // 点击事件
    labelEl.addEventListener('click', () => {
      if (node.type === 'directory') {
        node.expanded = !node.expanded;
        renderTree();
      }
      selectNode(node, [...path, node.name]);
    });

    // 存储节点引用
    allNodes.push({ node, element: labelEl, path: [...path, node.name] });

    // 子节点
    if (node.children && node.expanded) {
      const childrenEl = document.createElement('div');
      childrenEl.className = 'tree-children';
      node.children.forEach(child => {
        childrenEl.appendChild(renderNode(child, level + 1, [...path, node.name]));
      });
      nodeEl.appendChild(childrenEl);
    }

    return nodeEl;
  }

  // 渲染整棵树
  function renderTree() {
    allNodes = [];
    treeRoot.innerHTML = '';
    treeRoot.appendChild(renderNode(currentSkillTree));

    // 恢复选中状态
    if (selectedNode) {
      const nodeData = allNodes.find(n => n.node === selectedNode);
      if (nodeData) {
        nodeData.element.classList.add('active');
      }
    }
  }

  // 选中节点
  function selectNode(node, path) {
    // 更新选中状态
    document.querySelectorAll('.tree-node-label').forEach(el => {
      el.classList.remove('active');
    });

    const nodeData = allNodes.find(n => n.node === node);
    if (nodeData) {
      nodeData.element.classList.add('active');
    }

    selectedNode = node;
    renderDetail(node, path);
  }

  // 渲染详情面板
  function renderDetail(node, path) {
    // 面包屑
    detailBreadcrumb.innerHTML = `
      <div class="breadcrumb">
        ${path.map((name, idx) => {
          const isLast = idx === path.length - 1;
          return `
            <span class="breadcrumb-item ${isLast ? 'active' : ''}"
                  ${isLast ? '' : `style="cursor:pointer;" onclick="jumpToNodeByPath(${JSON.stringify(path.slice(0, idx + 1))})"`}>
              ${name}
            </span>
            ${isLast ? '' : '<span class="breadcrumb-sep">/</span>'}
          `;
        }).join('')}
      </div>
    `;

    // 标题
    detailTitle.textContent = node.name;

    // 元信息标签
    const layerInfo = {
      root: { label: '根目录', color: 'var(--purple)' },
      required: { label: '✅ 必需', color: 'var(--teal)' },
      optional: { label: '📦 可选', color: 'var(--purple)' },
      flexible: { label: '💡 灵活', color: 'var(--amber)' }
    }[node.layer];

    detailMeta.innerHTML = `
      <span class="badge">${node.type === 'directory' ? '📁 目录' : node.type === 'note' ? '💡 说明' : '📄 文件'}</span>
      ${layerInfo ? `<span class="badge" style="background:${layerInfo.color}20;color:${layerInfo.color};border:1px solid ${layerInfo.color}40;">${layerInfo.icon || ''} ${layerInfo.label}</span>` : ''}
    `;

    // 详细内容
    detailContent.innerHTML = `
      <div class="detail-section">
        <h4>📝 这是什么</h4>
        <p>${node.description}</p>
      </div>
      <div class="detail-section">
        <h4>💡 为什么需要它</h4>
        <p>${node.why}</p>
      </div>
      <div class="detail-section">
        <h4>📋 典型内容示例</h4>
        <pre><code>${escapeHtml(node.example)}</code></pre>
      </div>
      ${node.collaboration && node.collaboration.length > 0 ? `
        <div class="detail-section">
          <h4>🔗 协同关系</h4>
          ${node.collaboration.map(item => `<div class="collab-item">${item}</div>`).join('')}
        </div>
      ` : ''}
    `;

    // 快速跳转按钮
    const quickJumpButtons = [
      { label: '📝 必需文件', target: 'SKILL.md', color: 'var(--teal)' },
      { label: '📚 参考资料', target: 'references/', color: 'var(--purple)' },
      { label: '🔧 执行脚本', target: 'scripts/', color: 'var(--amber)' },
      { label: '🎨 输出模板', target: 'assets/', color: 'var(--orange)' }
    ];

    detailQuickJump.innerHTML = `
      <div style="font-size:0.88rem;color:var(--text-tertiary);margin-bottom:10px;">快速跳转</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;">
        ${quickJumpButtons.map(btn => `
          <button class="btn" onclick="jumpToNode('${btn.target}')"
                  style="font-size:0.85rem;padding:8px 14px;background:${btn.color}10;color:${btn.color};border:1px solid ${btn.color}40;">
            ${btn.label}
          </button>
        `).join('')}
      </div>
    `;
  }

  // HTML 转义
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // 跳转到指定节点（通过名称）
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

    const result = findAndExpand(currentSkillTree, nodeName);
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

  // 跳转到指定节点（通过路径）
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

    const result = findByPath(currentSkillTree, targetPath);
    if (result) {
      renderTree();
      setTimeout(() => {
        selectNode(result.node, result.path);
      }, 50);
    }
  };

  // 全部展开
  window.expandAll = function() {
    function expand(node) {
      if (node.type === 'directory') {
        node.expanded = true;
      }
      if (node.children) {
        node.children.forEach(expand);
      }
    }
    expand(currentSkillTree);
    renderTree();
  };

  // 全部折叠
  window.collapseAll = function() {
    function collapse(node) {
      if (node.type === 'directory' && node.name !== 'my-skill') {
        node.expanded = false;
      }
      if (node.children) {
        node.children.forEach(collapse);
      }
    }
    collapse(currentSkillTree);
    currentSkillTree.expanded = true; // 保持根目录展开
    renderTree();
  };

  // 初始化
  renderTree();

  // 默认选中 SKILL.md
  setTimeout(() => {
    jumpToNode('SKILL.md');
  }, 100);

  // 清理函数
  return function cleanup() {
    window.jumpToNode = null;
    window.jumpToNodeByPath = null;
    window.expandAll = null;
    window.collapseAll = null;
  };
};

// S015: SKILL.md 深入解析
window.slideHooks['slides/S015-skillmd-deep-dive.html'] = function() {
  // 数据结构
  const skillCreatorData = {
    full: {
      code: `---
name: skill-creator
description: 设计、创建和改进高质量AI技能
---

# Skill Creator

## Goal
帮助用户创建结构良好、触发准确的 Skill

## Workflow
1. 理解用户需求和使用场景
2. 设计 Skill 结构和触发条件
3. 生成 SKILL.md 和支撑文件
4. 运行评估和改进

## Decision Tree
- 如果用户想创建新 Skill → 走创建流程
- 如果用户想改进现有 Skill → 走改进流程

## Constraints
- 不要跳过触发条件设计
- 不要把 SKILL.md 写成纯文档

## Validation
- frontmatter 是否清晰
- workflow 是否可执行

## Resources
- references/schemas.md
- scripts/run_eval.py`,
      explanation: `<p style="margin:0 0 12px 0;"><strong>SKILL.md 的双层结构</strong></p>
<p style="margin:0 0 8px 0;">SKILL.md 由两部分组成：</p>
<p style="margin:0 0 6px 0;">1️⃣ <strong>frontmatter（YAML）</strong>：定义触发条件和元信息</p>
<p style="margin:0 0 6px 0;">2️⃣ <strong>body（Markdown）</strong>：定义执行流程和约束</p>
<p style="margin:12px 0 0 0;color:var(--text-tertiary);">点击上方按钮，分别查看两层的作用</p>`
    },
    frontmatter: {
      code: `---
name: skill-creator
description: 设计、创建和改进高质量AI技能
---`,
      explanation: `<p style="margin:0 0 12px 0;"><strong>frontmatter：路由层</strong></p>
<p style="margin:0 0 12px 0;"><strong>作用</strong>：决定这个 Skill 会不会被 Agent 发现和调用</p>
<p style="margin:0 0 8px 0;"><strong>关键字段</strong>：</p>
<ul style="margin:0 0 12px 0;padding-left:20px;">
  <li style="margin-bottom:6px;"><code>name</code>：Skill 的唯一标识符</li>
  <li style="margin-bottom:6px;"><code>description</code>：告诉 Agent 这个 Skill 适合什么任务</li>
</ul>
<p style="margin:0;color:var(--teal);"><strong>最佳实践</strong>：description 要清晰说明适用场景和边界</p>`
    },
    body: {
      code: `# Skill Creator

## Goal
帮助用户创建结构良好、触发准确的 Skill

## Workflow
1. 理解用户需求和使用场景
2. 设计 Skill 结构和触发条件
3. 生成 SKILL.md 和支撑文件
4. 运行评估和改进

## Decision Tree
- 如果用户想创建新 Skill → 走创建流程
- 如果用户想改进现有 Skill → 走改进流程

## Constraints
- 不要跳过触发条件设计
- 不要把 SKILL.md 写成纯文档

## Validation
- frontmatter 是否清晰
- workflow 是否可执行

## Resources
- references/schemas.md
- scripts/run_eval.py`,
      explanation: `<p style="margin:0 0 12px 0;"><strong>body：控制层</strong></p>
<p style="margin:0 0 12px 0;"><strong>作用</strong>：决定 Agent 进入 Skill 后如何执行</p>
<p style="margin:0 0 8px 0;"><strong>核心章节</strong>：</p>
<ul style="margin:0 0 12px 0;padding-left:20px;">
  <li style="margin-bottom:6px;"><code>Goal</code>：说明解决什么问题</li>
  <li style="margin-bottom:6px;"><code>Workflow</code>：定义执行步骤</li>
  <li style="margin-bottom:6px;"><code>Decision Tree</code>：定义分支逻辑</li>
  <li style="margin-bottom:6px;"><code>Constraints</code>：定义约束和禁止事项</li>
  <li style="margin-bottom:6px;"><code>Validation</code>：定义成功标准</li>
  <li style="margin-bottom:6px;"><code>Resources</code>：引用支撑文件</li>
</ul>
<p style="margin:0;color:var(--teal);"><strong>最佳实践</strong>：Workflow 要具体可执行，不要模糊建议</p>`
    }
  };

  // 获取 DOM 元素
  const buttons = Array.from(document.querySelectorAll('.skillmd-view-btn'));
  const codeArea = document.getElementById('skillmd-code-area');
  const explanationArea = document.getElementById('skillmd-explanation-area');

  if (!buttons.length || !codeArea || !explanationArea) return;

  // 渲染函数
  const render = (view, button) => {
    const data = skillCreatorData[view];
    setActiveButton(buttons, button);
    codeArea.innerHTML = '<pre style="margin:0;white-space:pre-wrap;word-wrap:break-word;">' + data.code + '</pre>';
    explanationArea.innerHTML = data.explanation;
  };

  // 事件处理
  const onClick = (event) => render(event.currentTarget.dataset.view, event.currentTarget);
  buttons.forEach(button => button.addEventListener('click', onClick));

  // 初始化为完整视图
  render('full', buttons[0]);

  // 清理函数
  return function cleanup() {
    buttons.forEach(button => button.removeEventListener('click', onClick));
  };
};

// S022A: Skills vs Function Calling vs MCP 对比
window.slideHooks['slides/S022A-skills-vs-fc-mcp.html'] = function() {
  // 对比数据结构
  const comparisonData = {
    definition: {
      fc: { content: '代码级接口（JSON Schema）', detail: '通过 JSON Schema 定义函数签名，模型生成参数后调用代码', icon: '⚙️' },
      mcp: { content: '通讯协议标准', detail: 'Model Context Protocol，定义 AI 与外部工具的标准通讯方式', icon: '🔌' },
      skills: { content: '业务逻辑封装 (SOP)', detail: '用 Markdown 描述工作流程，模型自动理解和执行', icon: '📋', highlight: '无需编程' }
    },
    essence: {
      fc: { content: '可调用函数接口', detail: '本质是一个可被模型调用的函数，通过 JSON Schema 定义输入输出，模型生成参数后执行代码逻辑', icon: '🔧' },
      mcp: { content: '通过协议暴露的外部能力', detail: '本质是通过 MCP 协议暴露的外部系统能力，更像"能力源"，提供标准化的工具和资源访问接口', icon: '🔌', tag: '能力源' },
      skills: { content: '能力模块（路由+控制+支撑）', detail: '本质是完整的能力模块，包含路由层（何时触发）、控制层（如何执行）、支撑层（资源与脚本），封装完整工作流', icon: '📦', highlight: '完整模块' }
    },
    strength: {
      fc: { content: '擅长：单点执行、精确动作', detail: '适合明确的单步操作，如查询数据库、调用 API、执行计算。局限：不负责完整策略，只是"执行层"', icon: '🎯', tag: '执行层' },
      mcp: { content: '擅长：稳定接入外部系统', detail: '适合把外部系统能力（如文件系统、数据库、第三方服务）稳定接入 Agent。局限：更像"能力源"，不包含业务逻辑', icon: '🔗', tag: '接入层' },
      skills: { content: '擅长：组织工作流、封装判断', detail: '适合复杂多步骤任务，封装决策树、分支逻辑、验证规则。局限：不一定直接拥有底层执行接口，需配合 Tools 或 MCP', icon: '🧩', highlight: '策略层' }
    },
    language: {
      fc: { content: 'JSON Schema + Python/Node.js', detail: '需要编写代码实现函数逻辑', icon: '💻', tag: '需要编程' },
      mcp: { content: 'TypeScript/Python SDK', detail: '使用官方 SDK 开发 MCP 服务器', icon: '🛠️', tag: '需要编程' },
      skills: { content: 'Markdown / 自然语言', detail: '无需编程，用自然语言描述即可', icon: '📝', highlight: '零代码' }
    },
    difficulty: {
      fc: { content: '高', detail: '需要精确定义 Schema，处理参数验证和错误', icon: '🔴', tag: '复杂' },
      mcp: { content: '中', detail: '需要理解协议规范，搭建服务器', icon: '🟡', tag: '中等' },
      skills: { content: '极低', detail: '写 Markdown 文档即可，无需编程基础', icon: '🟢', highlight: '简单' }
    },
    flexibility: {
      fc: { content: '僵化（参数严格匹配）', detail: '参数必须完全匹配 Schema，否则调用失败', icon: '🔒', tag: '严格' },
      mcp: { content: '较强', detail: '支持动态资源和工具发现', icon: '🔓', tag: '灵活' },
      skills: { content: '极强（大模型自动补全）', detail: '模型可以根据上下文自动补全缺失信息', icon: '✨', highlight: '智能' }
    },
    audience: {
      fc: { content: '后端工程师', detail: '需要编程能力和 API 设计经验', icon: '👨‍💻', tag: '专业' },
      mcp: { content: '全栈工程师', detail: '需要理解前后端通讯和协议设计', icon: '👩‍💻', tag: '专业' },
      skills: { content: '所有人', detail: '产品经理、运营、非技术人员都可以创建', icon: '👥', highlight: '人人可用' }
    }
  };

  const scenarios = {
    prototype: { name: '快速原型验证', recommended: 'skills', reason: 'Agent Skills 无需编程，可以快速迭代验证想法', color: 'var(--teal)' },
    production: { name: '生产级系统', recommended: 'mcp', reason: 'MCP 提供标准化协议，适合构建稳定的生产系统', color: 'rgba(59,130,246,1)' },
    nonTech: { name: '非技术人员使用', recommended: 'skills', reason: 'Agent Skills 使用 Markdown，非技术人员也能创建和维护', color: 'var(--teal)' },
    complex: { name: '复杂工作流', recommended: 'skills', reason: 'Agent Skills 支持复杂的决策树和分支逻辑', color: 'var(--teal)' },
    precise: { name: '精确参数控制', recommended: 'fc', reason: 'Function Calling 提供严格的参数验证和类型检查', color: 'rgba(100,116,139,1)' }
  };

  // 获取 DOM 元素
  const dimButtons = Array.from(document.querySelectorAll('.tech-dim-btn'));
  const scenarioButtons = Array.from(document.querySelectorAll('.tech-scenario-btn'));
  const fcContent = document.getElementById('fc-content');
  const mcpContent = document.getElementById('mcp-content');
  const skillsContent = document.getElementById('skills-content');
  const recommendationResult = document.getElementById('tech-recommendation-result');

  if (!dimButtons.length || !fcContent || !mcpContent || !skillsContent) return;

  // 渲染维度对比
  const renderDimension = (dim, button) => {
    const data = comparisonData[dim];
    setActiveButton(dimButtons, button);

    // Function Calling
    fcContent.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
        <span style="font-size:1.5rem;">${data.fc.icon}</span>
        <strong style="font-size:1.05rem;color:rgba(100,116,139,1);">${data.fc.content}</strong>
      </div>
      <p style="margin:0;font-size:0.9rem;color:var(--text-secondary);line-height:1.6;">${data.fc.detail}</p>
      ${data.fc.tag ? `<div style="margin-top:10px;padding:4px 10px;background:rgba(220,38,38,0.1);color:rgba(220,38,38,1);border-radius:var(--radius-sm);font-size:0.8rem;display:inline-block;">${data.fc.tag}</div>` : ''}
    `;

    // MCP
    mcpContent.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
        <span style="font-size:1.5rem;">${data.mcp.icon}</span>
        <strong style="font-size:1.05rem;color:rgba(59,130,246,1);">${data.mcp.content}</strong>
      </div>
      <p style="margin:0;font-size:0.9rem;color:var(--text-secondary);line-height:1.6;">${data.mcp.detail}</p>
      ${data.mcp.tag ? `<div style="margin-top:10px;padding:4px 10px;background:rgba(251,191,36,0.2);color:rgba(180,83,9,1);border-radius:var(--radius-sm);font-size:0.8rem;display:inline-block;">${data.mcp.tag}</div>` : ''}
    `;

    // Agent Skills
    skillsContent.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
        <span style="font-size:1.5rem;">${data.skills.icon}</span>
        <strong style="font-size:1.05rem;color:var(--teal);">${data.skills.content}</strong>
      </div>
      <p style="margin:0;font-size:0.9rem;color:var(--text-secondary);line-height:1.6;">${data.skills.detail}</p>
      ${data.skills.highlight ? `<div style="margin-top:10px;padding:4px 10px;background:var(--teal);color:white;border-radius:var(--radius-sm);font-size:0.8rem;display:inline-block;font-weight:600;">✨ ${data.skills.highlight}</div>` : ''}
    `;
  };

  // 渲染场景推荐
  const renderScenario = (scenario, button) => {
    const data = scenarios[scenario];
    setActiveButton(scenarioButtons, button);

    const techName = data.recommended === 'skills' ? 'Agent Skills' : data.recommended === 'mcp' ? 'MCP' : 'Function Calling';

    recommendationResult.innerHTML = `
      <div style="padding:14px;background:${data.color}15;border-left:4px solid ${data.color};border-radius:var(--radius-md);">
        <p style="margin:0 0 6px 0;font-size:0.95rem;color:var(--text-primary);">
          <strong style="color:${data.color};">推荐：${techName}</strong>
        </p>
        <p style="margin:0;font-size:0.88rem;color:var(--text-secondary);">${data.reason}</p>
      </div>
    `;
  };

  // 事件绑定
  const onDimClick = (event) => renderDimension(event.currentTarget.dataset.dim, event.currentTarget);
  const onScenarioClick = (event) => renderScenario(event.currentTarget.dataset.scenario, event.currentTarget);

  dimButtons.forEach(btn => btn.addEventListener('click', onDimClick));
  scenarioButtons.forEach(btn => btn.addEventListener('click', onScenarioClick));

  // 初始化
  renderDimension('definition', dimButtons[0]);

  // 清理函数
  return function cleanup() {
    dimButtons.forEach(btn => btn.removeEventListener('click', onDimClick));
    scenarioButtons.forEach(btn => btn.removeEventListener('click', onScenarioClick));
  };
};

// S010A: Agent Skills 完整运行逻辑 - 深度演示
window.slideHooks['slides/S010A-skill-execution-flow.html'] = function() {
  // test-driven-development Skill 数据
  const skillData = {
    name: 'test-driven-development',
    frontmatter: {
      description: '在实现任何功能或修复 bug 前，先编写测试用例',
      trigger: ['写测试', 'test', 'TDD', '单元测试'],
      tokens: 80
    },
    workflow: [
      '读取目标代码文件',
      '分析代码结构和功能',
      '设计测试用例（正常/边界/异常）',
      '生成测试代码',
      '验证测试覆盖率'
    ],
    resources: {
      scripts: ['test-runner.sh', 'coverage-check.py'],
      templates: ['test-template.js']
    },
    fullTokens: 450
  };

  // 状态管理
  let currentStage = 0;
  let isAutoPlaying = false;
  let autoPlayInterval = null;

  // DOM 元素
  const stageIndicators = Array.from(document.querySelectorAll('.stage-indicator'));
  const stageContent = document.getElementById('stage-content');
  const prevBtn = document.getElementById('prev-btn');
  const nextBtn = document.getElementById('next-btn');
  const autoBtn = document.getElementById('auto-btn');
  const resetBtn = document.getElementById('reset-btn');

  if (!stageIndicators.length || !stageContent || !prevBtn || !nextBtn || !autoBtn || !resetBtn) return;

  // 清理函数
  const cleanup = () => {
    if (autoPlayInterval) {
      clearInterval(autoPlayInterval);
      autoPlayInterval = null;
    }
    isAutoPlaying = false;
  };

  // 渲染阶段内容
  const renderStage = (stage) => {
    currentStage = stage;

    // 更新阶段指示器
    stageIndicators.forEach((indicator, idx) => {
      const stageNum = idx + 1;
      indicator.classList.remove('active', 'completed');
      if (stageNum === stage) {
        indicator.classList.add('active');
      } else if (stageNum < stage) {
        indicator.classList.add('completed');
      }
    });

    // 更新按钮状态
    prevBtn.disabled = stage <= 1;
    nextBtn.disabled = stage >= 5;
    autoBtn.disabled = false;
    resetBtn.disabled = false;

    prevBtn.style.opacity = stage <= 1 ? '0.5' : '1';
    nextBtn.style.opacity = stage >= 5 ? '0.5' : '1';
    autoBtn.style.opacity = '1';
    resetBtn.style.opacity = '1';

    prevBtn.style.cursor = stage <= 1 ? 'not-allowed' : 'pointer';
    nextBtn.style.cursor = stage >= 5 ? 'not-allowed' : 'pointer';
    autoBtn.style.cursor = 'pointer';
    resetBtn.style.cursor = 'pointer';

    // 更新按钮文字
    if (stage === 0) {
      nextBtn.textContent = '开始演示 ▶';
      nextBtn.style.background = 'var(--teal)';
      nextBtn.style.color = 'var(--text-white)';
      nextBtn.style.border = 'none';
    } else {
      nextBtn.textContent = '下一步 ▶';
      nextBtn.style.background = 'var(--bg-white)';
      nextBtn.style.color = 'var(--text-primary)';
      nextBtn.style.border = '1px solid var(--border)';
    }

    // 渲染对应阶段的内容
    switch(stage) {
      case 1:
        renderStage1();
        break;
      case 2:
        renderStage2();
        break;
      case 3:
        renderStage3();
        break;
      case 4:
        renderStage4();
        break;
      case 5:
        renderStage5();
        break;
    }
  };

  // 阶段1：触发匹配
  const renderStage1 = () => {
    stageContent.innerHTML = `
      <div>
        <div style="font-size:0.95rem;font-weight:600;color:var(--text-primary);margin-bottom:10px;text-align:center;">
          🎯 阶段1：触发匹配
        </div>
        <p style="margin-bottom:12px;color:var(--text-secondary);font-size:0.8rem;text-align:center;">
          用户输入关键词，Agent 匹配 Skill 的 trigger 规则
        </p>

        <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:12px;align-items:center;max-width:900px;margin:0 auto;">
          <!-- 左侧：用户输入 -->
          <div>
            <div style="text-align:center;font-weight:600;color:var(--text-secondary);margin-bottom:6px;font-size:0.8rem;">
              用户输入
            </div>
            <div style="background:var(--bg-cool);border:1px solid var(--border);padding:12px;border-radius:var(--radius-md);text-align:center;">
              <div style="font-size:0.95rem;font-weight:600;color:var(--text-primary);">
                "帮我写测试用例"
              </div>
            </div>
          </div>

          <!-- 中间：箭头 -->
          <div style="font-size:1.5rem;color:var(--teal);">→</div>

          <!-- 右侧：Skill trigger 规则 -->
          <div>
            <div style="text-align:center;font-weight:600;color:var(--teal);margin-bottom:6px;font-size:0.8rem;">
              Skill Trigger 规则
            </div>
            <div style="background:var(--teal-pale);border:2px solid var(--teal);padding:10px;border-radius:var(--radius-md);">
              <div style="font-size:0.75rem;color:var(--text-secondary);margin-bottom:4px;">
                test-driven-development
              </div>
              <div style="font-size:0.8rem;color:var(--text-primary);line-height:1.4;">
                <div style="margin-bottom:2px;">✓ "写测试" <span style="color:var(--teal);font-weight:600;">← 匹配</span></div>
                <div style="margin-bottom:2px;">✓ "test"</div>
                <div style="margin-bottom:2px;">✓ "TDD"</div>
                <div>✓ "单元测试"</div>
              </div>
            </div>
          </div>
        </div>

        <div style="margin-top:12px;text-align:center;padding:8px;background:var(--teal-pale);border-left:4px solid var(--teal);border-radius:var(--radius-sm);max-width:700px;margin:12px auto 0;font-size:0.8rem;">
          <strong>✅ 匹配成功：</strong> 用户输入包含"写测试"关键词，触发 test-driven-development Skill
        </div>
      </div>
    `;
  };

  // 阶段2：加载解析
  const renderStage2 = () => {
    stageContent.innerHTML = `
      <div>
        <div style="font-size:0.95rem;font-weight:600;color:var(--text-primary);margin-bottom:10px;text-align:center;">
          📂 阶段2：加载解析 .skill 文件
        </div>
        <p style="margin-bottom:10px;color:var(--text-secondary);font-size:0.8rem;text-align:center;">
          读取 test-driven-development.skill 文件，解析 frontmatter、workflow、resources
        </p>

        <div style="max-width:900px;margin:0 auto;">
          <!-- 进度条 -->
          <div style="margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
              <span style="font-size:0.75rem;color:var(--text-secondary);">加载进度</span>
              <span style="font-size:0.75rem;color:var(--teal);font-weight:600;" id="load-progress">0%</span>
            </div>
            <div style="height:5px;background:var(--bg-cool);border-radius:var(--radius-full);overflow:hidden;">
              <div id="load-bar" style="height:100%;width:0%;background:linear-gradient(90deg, var(--teal), var(--teal-light));transition:width 1s ease-out;"></div>
            </div>
          </div>

          <!-- 三栏解析结果 -->
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
            <!-- Frontmatter -->
            <div class="card" style="padding:10px;">
              <div style="font-weight:600;color:var(--purple);margin-bottom:6px;font-size:0.8rem;">
                📋 Frontmatter
              </div>
              <div style="font-size:0.7rem;line-height:1.4;color:var(--text-secondary);">
                <div><strong>name:</strong> ${skillData.name}</div>
                <div style="margin-top:3px;"><strong>description:</strong> ${skillData.frontmatter.description.substring(0, 30)}...</div>
                <div style="margin-top:3px;"><strong>tokens:</strong> ${skillData.frontmatter.tokens}</div>
              </div>
            </div>

            <!-- Workflow -->
            <div class="card" style="padding:10px;">
              <div style="font-weight:600;color:var(--teal);margin-bottom:6px;font-size:0.8rem;">
                ⚙️ Workflow
              </div>
              <div style="font-size:0.7rem;line-height:1.4;color:var(--text-secondary);">
                ${skillData.workflow.slice(0, 3).map((step, idx) => `<div style="margin-bottom:2px;">${idx + 1}. ${step.substring(0, 18)}...</div>`).join('')}
                <div style="color:var(--text-tertiary);margin-top:2px;">...共 ${skillData.workflow.length} 步</div>
              </div>
            </div>

            <!-- Resources -->
            <div class="card" style="padding:10px;">
              <div style="font-weight:600;color:var(--amber);margin-bottom:6px;font-size:0.8rem;">
                📦 Resources
              </div>
              <div style="font-size:0.7rem;line-height:1.4;color:var(--text-secondary);">
                <div><strong>scripts:</strong></div>
                ${skillData.resources.scripts.map(s => `<div style="margin-left:4px;">• ${s}</div>`).join('')}
                <div style="margin-top:3px;"><strong>templates:</strong></div>
                ${skillData.resources.templates.map(t => `<div style="margin-left:4px;">• ${t}</div>`).join('')}
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    // 动画：进度条加载
    setTimeout(() => {
      const loadBar = document.getElementById('load-bar');
      const loadProgress = document.getElementById('load-progress');
      if (loadBar && loadProgress) {
        let progress = 0;
        const interval = setInterval(() => {
          progress += 10;
          loadBar.style.width = progress + '%';
          loadProgress.textContent = progress + '%';
          if (progress >= 100) {
            clearInterval(interval);
          }
        }, 100);
      }
    }, 300);
  };

  // 阶段3：上下文注入
  const renderStage3 = () => {
    stageContent.innerHTML = `
      <div>
        <div style="font-size:0.95rem;font-weight:600;color:var(--text-primary);margin-bottom:10px;text-align:center;">
          💉 阶段3：上下文注入
        </div>
        <p style="margin-bottom:12px;color:var(--text-secondary);font-size:0.8rem;text-align:center;">
          将 Skill 内容注入到 System Prompt，增强 Agent 能力
        </p>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;max-width:900px;margin:0 auto;">
          <!-- 注入前 -->
          <div>
            <div style="text-align:center;font-weight:600;color:var(--text-secondary);margin-bottom:6px;font-size:0.8rem;">
              ❌ 注入前
            </div>
            <div style="background:var(--bg-cool);border:1px solid var(--border);padding:12px;border-radius:var(--radius-md);">
              <div style="font-size:0.8rem;line-height:1.5;color:var(--text-secondary);">
                <div style="font-weight:600;margin-bottom:6px;">System Prompt (基础版)</div>
                <div>你是一个 AI 助手，帮助用户完成各种任务。</div>
                <div style="margin-top:8px;padding:6px;background:var(--bg-base);border-radius:4px;font-size:0.75rem;">
                  <strong>Token 消耗：</strong> 200 tokens
                </div>
              </div>
            </div>
          </div>

          <!-- 注入后 -->
          <div>
            <div style="text-align:center;font-weight:600;color:var(--teal);margin-bottom:6px;font-size:0.8rem;">
              ✅ 注入后
            </div>
            <div style="background:var(--teal-pale);border:2px solid var(--teal);padding:12px;border-radius:var(--radius-md);">
              <div style="font-size:0.8rem;line-height:1.5;color:var(--text-primary);">
                <div style="font-weight:600;margin-bottom:6px;">System Prompt (增强版)</div>
                <div>你是一个 AI 助手，帮助用户完成各种任务。</div>
                <div style="margin-top:6px;padding:6px;background:rgba(13,148,136,0.1);border-left:3px solid var(--teal);border-radius:4px;font-size:0.75rem;">
                  <strong style="color:var(--teal);">+ test-driven-development Skill</strong>
                  <div style="margin-top:3px;font-size:0.7rem;">
                    • Workflow: ${skillData.workflow.length} 步骤<br>
                    • Resources: ${skillData.resources.scripts.length} 脚本 + ${skillData.resources.templates.length} 模板
                  </div>
                </div>
                <div style="margin-top:8px;padding:6px;background:var(--bg-base);border-radius:4px;font-size:0.75rem;">
                  <strong>Token 消耗：</strong> 200 + ${skillData.fullTokens} = ${200 + skillData.fullTokens} tokens
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Token 对比柱状图 -->
        <div style="margin-top:16px;max-width:700px;margin-left:auto;margin-right:auto;">
          <div style="font-weight:600;color:var(--text-secondary);margin-bottom:8px;text-align:center;font-size:0.8rem;">
            Token 消耗对比
          </div>
          <div style="display:grid;gap:8px;">
            <div>
              <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="font-size:0.75rem;color:var(--text-secondary);">注入前</span>
                <span style="font-size:0.75rem;font-weight:600;color:var(--text-secondary);">200 tokens</span>
              </div>
              <div style="height:32px;background:var(--bg-cool);border-radius:var(--radius-sm);overflow:hidden;">
                <div id="token-bar-old" class="token-bar old" style="width:0%;background:linear-gradient(90deg, #94A3B8, #CBD5E1);font-size:0.8rem;">200</div>
              </div>
            </div>
            <div>
              <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="font-size:0.75rem;color:var(--teal);">注入后</span>
                <span style="font-size:0.75rem;font-weight:600;color:var(--teal);">${200 + skillData.fullTokens} tokens</span>
              </div>
              <div style="height:32px;background:var(--bg-cool);border-radius:var(--radius-sm);overflow:hidden;">
                <div id="token-bar-new" class="token-bar" style="width:0%;font-size:0.8rem;">${200 + skillData.fullTokens}</div>
              </div>
            </div>
          </div>
        </div>

        <div style="margin-top:12px;text-align:center;padding:8px;background:var(--teal-pale);border-left:4px solid var(--teal);border-radius:var(--radius-sm);max-width:700px;margin:12px auto 0;font-size:0.8rem;">
          <strong>💡 关键洞察：</strong> 按需加载，只在需要时注入 Skill 内容，避免上下文浪费
        </div>
      </div>
    `;

    // 动画：Token 柱状图
    setTimeout(() => {
      const oldBar = document.getElementById('token-bar-old');
      const newBar = document.getElementById('token-bar-new');
      if (oldBar && newBar) {
        gsap.to(oldBar, { width: '30%', duration: 1, ease: 'power2.out' });
        gsap.to(newBar, { width: '100%', duration: 1, ease: 'power2.out', delay: 0.3 });
      }
    }, 300);
  };
  // 阶段4：执行编排
  const renderStage4 = () => {
    stageContent.innerHTML = `
      <div>
        <div style="font-size:0.95rem;font-weight:600;color:var(--text-primary);margin-bottom:10px;text-align:center;">
          ⚙️ 阶段4：执行编排（Workflow 步骤 + Tool 调用）
        </div>
        <p style="margin-bottom:12px;color:var(--text-secondary);font-size:0.8rem;text-align:center;">
          按照 Skill 定义的 workflow 步骤执行，调用 scripts 和 tools
        </p>

        <div style="max-width:800px;margin:0 auto;">
          <!-- Workflow 步骤列表 -->
          <div id="workflow-steps">
            ${skillData.workflow.map((step, idx) => `
              <div class="workflow-step" data-step="${idx}" style="opacity:0.4;">
                <div style="display:flex;align-items:start;gap:10px;">
                  <div style="flex-shrink:0;width:24px;height:24px;border-radius:50%;background:var(--bg-cool);border:2px solid var(--border);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.75rem;color:var(--text-tertiary);">
                    ${idx + 1}
                  </div>
                  <div style="flex:1;">
                    <div style="font-weight:600;color:var(--text-primary);font-size:0.85rem;margin-bottom:3px;">
                      ${step}
                    </div>
                    <div class="step-detail" style="display:none;font-size:0.75rem;color:var(--text-secondary);margin-top:4px;padding:6px;background:var(--bg-base);border-radius:4px;">
                      ${getStepDetail(idx)}
                    </div>
                  </div>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;

    // 动画：逐步激活 workflow 步骤
    setTimeout(() => {
      const steps = document.querySelectorAll('.workflow-step');
      steps.forEach((step, idx) => {
        setTimeout(() => {
          // 激活当前步骤
          step.style.opacity = '1';
          step.classList.add('active');

          // 显示详情
          const detail = step.querySelector('.step-detail');
          if (detail) {
            detail.style.display = 'block';
            gsap.from(detail, { opacity: 0, height: 0, duration: 0.3 });
          }

          // 完成前面的步骤（保持详情显示）
          if (idx > 0) {
            steps[idx - 1].classList.remove('active');
            steps[idx - 1].classList.add('completed');
            // 不再隐藏详情，让它保持显示
          }

          // 最后一步完成（保持详情显示）
          if (idx === steps.length - 1) {
            setTimeout(() => {
              step.classList.remove('active');
              step.classList.add('completed');
              // 不再隐藏详情，让它保持显示
            }, 1500);
          }
        }, idx * 1500);
      });
    }, 300);
  };

  // 获取步骤详情（包含 Tool 调用信息）
  const getStepDetail = (stepIdx) => {
    const details = [
      '🔧 调用 Tool: <strong>Read</strong> → 读取目标代码文件',
      '🔍 调用 Tool: <strong>Grep</strong> → 分析代码结构和依赖',
      '📝 生成测试用例设计文档（正常/边界/异常场景）',
      '⚙️ 执行 Script: <strong>test-runner.sh</strong> → 生成测试代码',
      '📊 执行 Script: <strong>coverage-check.py</strong> → 验证覆盖率'
    ];
    return details[stepIdx] || '执行中...';
  };

  // 阶段5：输出返回（带打字机效果）
  const renderStage5 = () => {
    stageContent.innerHTML = `
      <div>
        <div style="font-size:0.95rem;font-weight:600;color:var(--text-primary);margin-bottom:10px;text-align:center;">
          ✨ 阶段5：输出返回
        </div>
        <p style="margin-bottom:12px;color:var(--text-secondary);font-size:0.8rem;text-align:center;">
          Skill 执行完成，返回结构化结果给用户
        </p>

        <div style="max-width:800px;margin:0 auto;">
          <!-- 执行结果摘要 -->
          <div style="margin-bottom:12px;">
            <div style="background:var(--teal-pale);border:2px solid var(--teal);padding:14px;border-radius:var(--radius-md);">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                <div style="width:32px;height:32px;border-radius:50%;background:var(--teal);display:flex;align-items:center;justify-content:center;font-size:1.1rem;">
                  ✓
                </div>
                <div style="font-weight:600;color:var(--teal);font-size:0.95rem;">
                  执行成功
                </div>
              </div>
              <div id="output-text" style="color:var(--text-primary);line-height:1.6;font-size:0.85rem;">
                <span class="typewriter-text"></span>
              </div>
            </div>
          </div>

          <!-- 生成的代码 -->
          <div style="margin-bottom:12px;">
            <div style="font-weight:600;color:var(--text-secondary);margin-bottom:6px;font-size:0.8rem;">
              📝 生成的测试代码：
            </div>
            <div style="background:var(--bg-cool);border:1px solid var(--border);padding:12px;border-radius:var(--radius-md);font-family:monospace;font-size:0.75rem;line-height:1.5;color:var(--text-primary);">
              <div style="color:var(--text-tertiary);">// test/example.test.js</div>
              <div style="margin-top:6px;">
                <span style="color:#7C3AED;">describe</span>(<span style="color:#0D9488;">'UserService'</span>, () => {<br>
                &nbsp;&nbsp;<span style="color:#7C3AED;">it</span>(<span style="color:#0D9488;">'should create user'</span>, <span style="color:#7C3AED;">async</span> () => {<br>
                &nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#7C3AED;">const</span> user = <span style="color:#7C3AED;">await</span> createUser(...);<br>
                &nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#7C3AED;">expect</span>(user.id).toBeDefined();<br>
                &nbsp;&nbsp;});<br>
                });
              </div>
            </div>
          </div>

          <!-- 性能指标 -->
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
            <div class="card" style="padding:10px;text-align:center;">
              <div style="font-size:0.7rem;color:var(--text-secondary);margin-bottom:4px;">执行时间</div>
              <div style="font-size:1.1rem;font-weight:700;color:var(--teal);">2.3s</div>
            </div>
            <div class="card" style="padding:10px;text-align:center;">
              <div style="font-size:0.7rem;color:var(--text-secondary);margin-bottom:4px;">Token 消耗</div>
              <div style="font-size:1.1rem;font-weight:700;color:var(--purple);">650</div>
            </div>
            <div class="card" style="padding:10px;text-align:center;">
              <div style="font-size:0.7rem;color:var(--text-secondary);margin-bottom:4px;">Tool 调用</div>
              <div style="font-size:1.1rem;font-weight:700;color:var(--amber);">4次</div>
            </div>
          </div>
        </div>

        <div style="margin-top:12px;text-align:center;padding:8px;background:var(--teal-pale);border-left:4px solid var(--teal);border-radius:var(--radius-sm);max-width:700px;margin:12px auto 0;font-size:0.8rem;">
          <strong>🎯 完整流程总结：</strong> 从触发匹配到输出返回，Skills 通过结构化执行和按需加载，帮助 Agent 高效完成复杂任务。
        </div>
      </div>
    `;

    // 打字机效果
    const outputText = '已为你生成完整的测试用例，包含：✓ 正常场景测试（用户创建、登录、更新）✓ 边界场景测试（空值、超长输入、特殊字符）✓ 异常场景测试（重复创建、权限不足、网络错误）✓ 测试覆盖率达到 85%，符合项目要求';
    const typewriterElement = document.querySelector('.typewriter-text');

    if (typewriterElement) {
      let charIndex = 0;
      const typeInterval = setInterval(() => {
        if (charIndex < outputText.length) {
          typewriterElement.textContent += outputText[charIndex];
          charIndex++;
        } else {
          clearInterval(typeInterval);
          // 移除光标
          typewriterElement.style.borderRight = 'none';
        }
      }, 30);
    }
  };

  // 控制按钮事件
  const onPrev = () => {
    if (currentStage > 1) {
      cleanup();
      renderStage(currentStage - 1);
    }
  };

  const onNext = () => {
    if (currentStage < 5) {
      cleanup();
      renderStage(currentStage + 1);
    }
  };

  const onAuto = () => {
    if (isAutoPlaying) {
      // 停止自动播放
      cleanup();
      autoBtn.textContent = '⏩ 自动播放';
      autoBtn.style.background = 'var(--bg-white)';
      autoBtn.style.color = 'var(--text-primary)';
      return;
    }

    // 开始自动播放
    isAutoPlaying = true;
    autoBtn.textContent = '⏸ 暂停';
    autoBtn.style.background = 'var(--amber)';
    autoBtn.style.color = 'var(--text-white)';

    let stage = currentStage === 5 ? 1 : currentStage + 1;
    renderStage(stage);

    autoPlayInterval = setInterval(() => {
      stage++;
      if (stage > 5) {
        cleanup();
        autoBtn.textContent = '⏩ 自动播放';
        autoBtn.style.background = 'var(--bg-white)';
        autoBtn.style.color = 'var(--text-primary)';
        return;
      }
      renderStage(stage);
    }, 3000);
  };

  const onReset = () => {
    cleanup();
    currentStage = 0;
    stageContent.innerHTML = `
      <p style="margin:0;color:var(--text-tertiary);text-align:center;padding:20px 0;font-size:0.85rem;">
        👇 点击下方"开始演示"按钮，查看 Skill 完整运行流程
      </p>
    `;
    stageIndicators.forEach(indicator => {
      indicator.classList.remove('active', 'completed');
    });
    nextBtn.textContent = '开始演示 ▶';
    nextBtn.style.background = 'var(--teal)';
    nextBtn.style.color = 'var(--text-white)';
    nextBtn.style.border = 'none';
    nextBtn.disabled = false;
    prevBtn.disabled = true;
    autoBtn.disabled = false;
    resetBtn.disabled = false;
  };

  // 绑定事件
  prevBtn.addEventListener('click', onPrev);
  nextBtn.addEventListener('click', onNext);
  autoBtn.addEventListener('click', onAuto);
  resetBtn.addEventListener('click', onReset);

  // 返回清理函数（页面切换时调用）
  return function() {
    cleanup();
    prevBtn.removeEventListener('click', onPrev);
    nextBtn.removeEventListener('click', onNext);
    autoBtn.removeEventListener('click', onAuto);
    resetBtn.removeEventListener('click', onReset);
  };
};

