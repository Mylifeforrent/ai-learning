# 04. Reusable Project Template

本文件总结一套可复用的企业级 AI 项目结构。模板综合了 Project 1 的 FastAPI + CrewAI 工程结构、Project 2/3 的 XiaoPaw Harness、Project 4 的 Agent Team 工作区，以及 Project 5 的生产加固目录。

## 推荐目录结构

```text
project-root/
  README.md
  DESIGN.md
  pyproject.toml
  config.yaml.example
  .env.example
  schema.sql

  app/
    main.py
    runner.py
    models.py

    api/
      __init__.py
      schemas.py
      test_server.py

    channels/
      feishu/
        listener.py
        sender.py
        downloader.py
        session_key.py

    agents/
      __init__.py
      main_crew.py
      skill_crew.py
      models.py
      config/
        agents.yaml
        tasks.yaml

    workflows/
      __init__.py
      flows.py
      orchestrator.py

    tools/
      __init__.py
      intermediate_tool.py
      skill_loader.py
      baidu_search_tool.py
      workspace.py
      mailbox.py

    skills/
      load_skills.yaml
      memory-save/
        SKILL.md
      search_memory/
        SKILL.md
        scripts/
          search.py

    memory/
      __init__.py
      bootstrap.py
      context_mgmt.py
      indexer.py
      token_counter.py
      config.py

    knowledge/
      indexer.py
      retriever.py
      chunking.py

    hook_framework/
      __init__.py
      registry.py
      loader.py
      crew_adapter.py

    observability/
      __init__.py
      logging_config.py
      metrics.py
      metrics_server.py
      trace.py
      pii_mask.py
      security.py

    config/
      __init__.py
      validator.py
      flags.py
      safety.py

    cron/
      __init__.py
      models.py
      service.py
      storage.py

    session/
      __init__.py
      models.py
      manager.py

    cleanup/
      __init__.py
      service.py

    llm/
      __init__.py
      provider.py

    utils/
      __init__.py
      retry.py

  workspace-init/
    soul.md
    user.md
    agent.md
    memory.md

  workspace/
    shared/
      team_protocol.md
      sop/
      skills/
    manager/
      soul.md
      agent.md
      user.md
      memory.md
      skills/
    pm/
      soul.md
      agent.md
      user.md
      memory.md
      skills/
    rd/
      soul.md
      agent.md
      user.md
      memory.md
      skills/
    qa/
      soul.md
      agent.md
      user.md
      memory.md
      skills/

  shared_hooks/
    hooks.yaml
    structured_log.py
    langfuse_trace.py
    audit_logger.py
    sandbox_guard.py
    permission_gate.py
    cost_guard.py
    loop_detector.py
    retry_tracker.py

  docs/
    01-architecture.md
    02-modules.md
    03-data.md
    04-api.md
    05-concurrency.md
    06-observability.md
    07-security.md
    08-deployment.md
    09-config.md
    10-testing.md
    ssot/
      locks.md
      tasks.md
      ports.md
      feature-flags.md
      threats.md

  tests/
    unit/
    integration/
    e2e/
    fixtures/

  evals/
    cases/
    judges/
    reports/

  deploy/
    docker/
    k8s/
    grafana/

  data/
    sessions/
    ctx/
    traces/
    cron/
    workspace/
```

## 模块职责

| 模块 | 职责 | 参考来源 |
| --- | --- | --- |
| `app/main.py` | 装配配置、日志、Runner、渠道、Cron、Cleanup、metrics | Project 2/3/5 |
| `app/runner.py` | 统一消息调度、slash 命令、session、loading、agent_fn 调用、最终发送 | Project 2/3/5 |
| `channels/` | 外部平台接入，转换为内部消息模型 | Project 2 `feishu/` |
| `agents/` | 主 Agent、Sub-Crew、Agent 配置、Task 配置 | Project 1-5 |
| `workflows/` | 固定流程、三阶段 flow、Orchestrator 编排 | Project 1、Project 4 |
| `tools/` | 直接 Python Tool、SkillLoader、workspace、mailbox | Project 2、Project 4 |
| `skills/` | SKILL.md 能力包和 load registry | Project 2-4 |
| `memory/` | Bootstrap、上下文生命周期、索引、token 计数 | Project 3、Project 5 |
| `knowledge/` | RAG / 搜索知识库，和 memory 可分可合 | 课程 21 |
| `hook_framework/` | 统一事件、handler 分发、策略 gate、CrewAI 适配 | Project 5 |
| `shared_hooks/` | 可观测、可靠性、安全策略 | Project 5 |
| `observability/` | 日志、指标、trace、PII、metrics server | Project 1、Project 5 |
| `config/` | 配置校验、feature flags、安全配置 | Project 5 |
| `workspace-init/` | 单助手初始化记忆和规则 | Project 3 |
| `workspace/` | 团队角色工作区、共享协议、项目产物 | Project 4 |
| `docs/ssot/` | 权威清单，降低文档和实现漂移 | Project 5 |
| `evals/` | 评测集、judge prompt、报告 | 课程 36-37 |

## 单助手最小模板

如果项目仍处于 Project 2/3 阶段，不需要团队目录，可简化为：

```text
project-root/
  app/
    main.py
    runner.py
    models.py
    agents/
      main_crew.py
      skill_crew.py
      config/
        agents.yaml
        tasks.yaml
    tools/
      skill_loader.py
      intermediate_tool.py
    memory/
      bootstrap.py
      context_mgmt.py
      indexer.py
    session/
      manager.py
    observability/
      logging_config.py
      metrics.py
  workspace-init/
    soul.md
    user.md
    agent.md
    memory.md
  skills/
    load_skills.yaml
  tests/
    unit/
    integration/
```

## 团队项目模板

当满足以下条件时再引入团队结构：

- 任务周期超过单轮或单天。
- 需要 PM/RD/QA 等专业视角互审。
- 需要人类 checkpoint。
- 产物需要通过共享工作区持续积累。
- 单 Agent 上下文或技能已经明显过载。

团队工作区结构：

```text
workspace/
  shared/
    team_protocol.md
    projects/
      {project_id}/
        requirements.md
        product_design.md
        tech_design.md
        test_design.md
        events.jsonl
        mailboxes/
          manager.json
          pm.json
          rd.json
          qa.json
    sop/
    skills/

  manager/
    soul.md
    agent.md
    memory.md
    skills/

  pm/
    soul.md
    agent.md
    memory.md
    skills/

  rd/
    soul.md
    agent.md
    memory.md
    skills/

  qa/
    soul.md
    agent.md
    memory.md
    skills/
```

## 配置模板

### `agents.yaml`

```yaml
orchestrator:
  role: "企业 AI 工作助手"
  goal: "根据用户目标选择合适 Skill 和工具完成任务，同时遵守安全、记忆和输出规范。"
  backstory: |
    运行时由 workspace-init/*.md Bootstrap 覆盖或增强。
    静态配置只写稳定身份，不写会话相关事实。
  verbose: true
  allow_delegation: false

reviewer:
  role: "质量验收专家"
  goal: "基于验收标准检查产物完整性、准确性、风险和可执行性。"
  backstory: |
    你只做验收和风险提示，不替代执行 Agent 产出。
  verbose: true
  allow_delegation: false
```

### `tasks.yaml`

```yaml
task_name:
  agent: orchestrator
  context: []
  description: |
    输入：
    - 用户请求：{user_request}
    - 可用文件：{file_refs}

    要求：
    - 不得编造文件内容。
    - 信息不足时明确列出缺口。
    - 需要调用工具时优先使用最小权限工具。
  expected_output: |
    输出必须是可解析 JSON，字段符合 TaskOutput。
```

### `load_skills.yaml`

```yaml
skills:
  - name: memory-save
    type: task
    path: memory-save/SKILL.md
    description: "当用户表达长期偏好、规则或项目事实时，保存到长期记忆。"

  - name: search_memory
    type: task
    path: search_memory/SKILL.md
    description: "当用户提到上次、之前、历史决策或复盘时，搜索长期记忆。"

  - name: product_design_sop
    type: reference
    path: product_design/SKILL.md
    description: "当需要撰写产品设计方案时，读取产品设计 SOP。"
```

### `hooks.yaml`

```yaml
hooks:
  BEFORE_TURN:
    - handler: structured_log.before_turn_handler
  BEFORE_TOOL_CALL:
    - handler: structured_log.before_tool_handler
  AFTER_TURN:
    - handler: structured_log.after_turn_handler

strategies:
  - name: audit_logger
    class: audit_logger.SecurityAuditLogger
    config: {}
    hooks:
      SESSION_END: session_end_handler

  - name: permission_gate
    class: permission_gate.PermissionGate
    config: {}
    deps:
      audit: audit_logger
    hooks:
      BEFORE_TOOL_CALL: before_tool_handler
```

## Workspace 初始化文件职责

| 文件 | 内容 | 不应包含 |
| --- | --- | --- |
| `soul.md` | Agent 身份、语气、价值观、长期风格 | 具体任务数据、短期状态 |
| `user.md` | 用户档案、偏好、工作方式、长期约束 | 敏感凭证、未经确认的推测 |
| `agent.md` | 工具使用规则、记忆规则、SOP 入口、边界 | 大段历史对话 |
| `memory.md` | 长期记忆索引、主题入口、重要事实 | 无治理的流水账 |

## 命名规范

| 对象 | 推荐命名 | 示例 |
| --- | --- | --- |
| Agent | 角色名或职责名 | `orchestrator`、`xhs_visual_analyst`、`qa_reviewer` |
| Task | `task_` + 动作或产物 | `task_visual_analysis`、`task_seo_optimization` |
| Tool | 动词 + 名词 | `read_inbox`、`write_shared`、`load_skill` |
| Skill | 名词或动词短语，单一职责 | `memory-save`、`search_memory`、`product_design` |
| Hook strategy | 策略名 | `cost_guard`、`loop_detector`、`permission_gate` |
| Event | 动作过去式或状态 | `task_done`、`retro_approved`、`checkpoint_response` |

## 测试模板

```text
tests/
  unit/
    test_config.py
    test_models.py
    test_skill_loader.py
    test_memory_context.py
    test_permission_gate.py
    test_hooks.py

  integration/
    test_runner_session.py
    test_memory_system.py
    test_skill_execution.py
    test_hook_chain.py

  e2e/
    test_e2e_01_basic_turn.py
    test_e2e_02_tool_routing.py
    test_e2e_03_multi_turn.py
    test_e2e_04_memory_save.py
    test_e2e_05_search_memory.py
    test_e2e_06_guardrail_deny.py
```

## 从模板裁剪

| 项目阶段 | 保留 | 可暂缓 |
| --- | --- | --- |
| MVP | `agents/`、`tools/`、`workflows/`、`tests/unit` | `memory/`、`hook_framework/`、`workspace/team` |
| 工具助手 | `runner/`、`session/`、`skills/`、`sandbox` | Agent Team、复杂 CI/CD |
| 长期助手 | `memory/`、`workspace-init/`、`knowledge/` | 多角色团队 |
| 团队项目 | `workspace/roles`、`mailbox`、`event_log` | 复杂生产安全策略可分阶段上 |
| 生产系统 | 全部保留 | 无 |

## 初始化检查清单

- 是否有 `DESIGN.md` 描述系统边界。
- 是否有 `agents.yaml` 和 `tasks.yaml` 分离角色与任务。
- 是否有 Pydantic / schema 约束关键输出。
- 是否有统一内部消息模型。
- 是否有 session / routing_key 隔离。
- 是否有 workspace 文件作为可编辑长期上下文。
- 是否有 Skill registry 和最小权限工具策略。
- 是否有日志、metrics、trace_id。
- 是否有安全配置和凭证隔离。
- 是否有 unit / integration / e2e / eval 分层测试。

