"""
Agent Skills Engine - 基于 LangChain 1.0 的完整实现

核心流程：
1. 预加载所有 Skill 的元信息（name、description、触发条件）
2. 用户输入后，通过路由器选择合适的 Skill
3. 加载完整 Skill 文档并执行
4. 返回最终结果

技术栈：
- LangChain 1.0 (ChatOpenAI, ChatPromptTemplate, LCEL)
- 结构化输出 (with_structured_output)
- LCEL Chains (LangChain Expression Language)

架构说明：
- SkillRegistry: 负责扫描、解析和管理所有 Skill 文件
- SkillRouter: 使用 LLM 根据用户输入选择最合适的 Skill
- SkillExecutor: 加载完整 Skill 文档并执行具体任务
- AgentSkillsEngine: 统一的系统入口，协调上述三个组件
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# LangChain 1.0 核心组件导入
from langchain_openai import ChatOpenAI  # OpenAI 兼容的聊天模型接口
from langchain_core.prompts import ChatPromptTemplate  # 聊天提示词模板
from langchain_core.output_parsers import StrOutputParser  # 字符串输出解析器
from langchain_core.runnables import RunnablePassthrough  # LCEL 管道传递组件

# 从项目根目录的 .env 文件加载环境变量（如 DEEPSEEK_API_KEY）
load_dotenv()


@dataclass
class SkillMetadata:
    """
    Skill 元信息数据类

    用于存储单个 Skill 的核心信息，包括名称、描述、触发条件等。
    在系统初始化时，会预加载所有 Skill 的元信息到内存中，
    以便快速进行路由判断，避免每次都读取完整文件。

    属性说明：
        name: Skill 的唯一标识名称（如 "get-weather"）
        description: Skill 的功能描述（用于路由判断）
        trigger_conditions: 触发该 Skill 的条件描述（从 description 中提取）
        file_path: Skill 文件的完整路径
        full_content: Skill 文件的完整内容（可选，执行时才加载）
    """
    name: str
    description: str
    trigger_conditions: str
    file_path: str
    full_content: Optional[str] = None


class SkillRegistry:
    """
    Skill 注册表 - 负责加载和管理所有 Skills

    职责说明：
    1. 扫描指定目录下的所有 Skill 文件（支持 .skill 文件和 SKILL.md 文件）
    2. 解析每个 Skill 文件的 YAML frontmatter，提取元信息
    3. 将所有 Skill 的元信息缓存到内存中，供路由器快速查询
    4. 提供获取单个 Skill 完整内容的接口

    支持的文件格式：
    - 直接的 .skill 文件（如 get-weather.skill）
    - 目录中的 SKILL.md 文件（如 get-weather/SKILL.md）

    属性说明：
        skills_dir: Skill 文件所在的目录路径
        skills: 字典，key 为 Skill 名称，value 为 SkillMetadata 对象
    """

    def __init__(self, skills_dir: str):
        """
        初始化 Skill 注册表

        参数：
            skills_dir: Skill 文件所在的目录路径（字符串格式）
        """
        self.skills_dir = Path(skills_dir)  # 转换为 Path 对象，方便路径操作
        self.skills: Dict[str, SkillMetadata] = {}  # 存储所有 Skill 的元信息
        self._load_all_skills()  # 立即加载所有 Skill

    def _parse_skill_file(self, file_path: Path) -> Optional[SkillMetadata]:
        """
        解析单个 Skill 文件，提取元信息

        解析流程：
        1. 读取文件内容
        2. 使用正则表达式提取 YAML frontmatter（--- 包裹的部分）
        3. 从 frontmatter 中提取 name 和 description 字段
        4. 从 description 中提取触发条件（如"在...时使用"）
        5. 构造 SkillMetadata 对象返回

        参数：
            file_path: Skill 文件的路径（Path 对象）

        返回：
            SkillMetadata 对象，如果解析失败则返回 None
        """
        try:
            # 读取文件内容（使用 UTF-8 编码）
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 使用正则表达式提取 YAML frontmatter
            # 格式：--- 开头，--- 结尾，中间是 YAML 内容
            # re.DOTALL 使 . 匹配包括换行符在内的所有字符
            frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            if not frontmatter_match:
                print(f"警告: {file_path.name} 缺少 frontmatter，跳过")
                return None

            frontmatter = frontmatter_match.group(1)

            # 从 frontmatter 中提取 name 和 description 字段
            name_match = re.search(r'name:\s*(.+)', frontmatter)
            desc_match = re.search(r'description:\s*(.+)', frontmatter)

            if not name_match or not desc_match:
                print(f"警告: {file_path.name} 缺少 name 或 description，跳过")
                return None

            name = name_match.group(1).strip()
            description = desc_match.group(1).strip()

            # 从 description 中提取触发条件
            # 例如："在查询天气时使用" -> 提取 "查询天气"
            trigger_match = re.search(r'在(.+?)时使用', description)
            trigger_conditions = trigger_match.group(1) if trigger_match else description

            # 构造并返回 SkillMetadata 对象
            return SkillMetadata(
                name=name,
                description=description,
                trigger_conditions=trigger_conditions,
                file_path=str(file_path),
                full_content=content  # 保存完整内容，供执行时使用
            )

        except Exception as e:
            print(f"错误: 解析 {file_path.name} 失败: {e}")
            return None

    def _load_all_skills(self):
        """
        扫描并加载所有 Skill 文件

        扫描策略：
        1. 查找所有 .skill 文件（如 get-weather.skill）
        2. 查找所有目录中的 SKILL.md 文件（如 get-weather/SKILL.md）
        3. 逐个解析文件，提取元信息
        4. 将成功解析的 Skill 存储到 self.skills 字典中

        注意：
        - 如果目录不存在，会打印错误信息并返回
        - 解析失败的文件会被跳过，不影响其他文件的加载
        """
        # 检查 Skills 目录是否存在
        if not self.skills_dir.exists():
            print(f"错误: Skills 目录不存在: {self.skills_dir}")
            return

        # 查找所有 .skill 文件
        skill_files = list(self.skills_dir.glob("*.skill"))

        # 查找所有目录中的 SKILL.md 文件
        skill_dirs = [d for d in self.skills_dir.iterdir() if d.is_dir()]
        for skill_dir in skill_dirs:
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                skill_files.append(skill_md)

        print(f"扫描 Skills 目录: {self.skills_dir}")
        print(f"找到 {len(skill_files)} 个 Skill 文件\n")

        # 逐个解析 Skill 文件
        for file_path in skill_files:
            skill = self._parse_skill_file(file_path)
            if skill:
                # 将 Skill 存储到字典中，key 为 Skill 名称
                self.skills[skill.name] = skill
                print(f"加载 Skill: {skill.name}")
                print(f"   描述: {skill.description[:60]}...")
                print(f"   触发条件: {skill.trigger_conditions}\n")

        print(f"成功加载 {len(self.skills)} 个 Skills\n")

    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        """
        获取指定 Skill 的完整内容

        参数：
            name: Skill 的名称（如 "get-weather"）

        返回：
            SkillMetadata 对象，如果不存在则返回 None
        """
        return self.skills.get(name)

    def get_all_skills_summary(self) -> str:
        """
        获取所有 Skills 的摘要信息（用于路由判断）

        返回格式：
        当前系统可用的 Skills：

        - **get-weather**: 在查询天气时使用
        - **translate-text**: 在翻译文本时使用
        ...

        返回：
            格式化的 Skills 摘要字符串
        """
        summary = "当前系统可用的 Skills：\n\n"
        for skill in self.skills.values():
            summary += f"- **{skill.name}**: {skill.description}\n"
        return summary

    def get_skill_names(self) -> List[str]:
        """
        获取所有 Skill 名称列表

        返回：
            Skill 名称的列表（如 ["get-weather", "translate-text"]）
        """
        return list(self.skills.keys())


class SkillRouter:
    """
    Skill 路由器 - 使用 LangChain 1.0 实现路由逻辑

    职责说明：
    1. 接收用户输入和所有可用 Skills 的摘要信息
    2. 使用 LLM 分析用户意图，选择最合适的 Skill
    3. 返回选中的 Skill 名称，如果没有合适的则返回 None

    技术实现：
    - 使用 ChatPromptTemplate 构建路由提示词模板
    - 使用 LCEL (LangChain Expression Language) 构建处理链
    - 处理链：Prompt -> LLM -> StrOutputParser
    - 使用 DeepSeek API 作为 LLM 后端（temperature=0 确保稳定输出）

    属性说明：
        registry: SkillRegistry 实例，用于获取 Skills 信息
        llm: ChatOpenAI 实例，用于调用 LLM
        route_prompt: 路由提示词模板
        routing_chain: LCEL 处理链
    """

    def __init__(self, registry: SkillRegistry):
        """
        初始化 Skill 路由器

        参数：
            registry: SkillRegistry 实例
        """
        self.registry = registry

        # 初始化 ChatOpenAI（使用 DeepSeek API）
        # temperature=0 确保输出稳定，避免随机性
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            temperature=0
        )

        # 构建路由 Prompt Template
        # 使用 ChatPromptTemplate.from_messages 创建多轮对话模板
        # system 消息：定义路由器的角色和规则
        # human 消息：用户的实际输入
        self.route_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个 Skill 路由器。根据用户的输入，判断应该激活哪个 Skill。

{skills_summary}

**重要规则**:
1. 仔细分析用户意图，选择最匹配的 Skill
2. 如果没有合适的 Skill，返回 "NONE"
3. 只返回 Skill 名称，不要添加任何解释或额外文字

**输出格式**: 只返回一个单词，例如：get-weather 或 NONE"""),
            ("human", "{user_input}")
        ])

        # 构建 LCEL Chain（LangChain Expression Language 链式调用）
        # 使用 | 操作符连接多个组件：
        # 1. route_prompt: 将输入格式化为提示词
        # 2. llm: 调用 LLM 生成响应
        # 3. StrOutputParser: 将 LLM 输出解析为字符串
        self.routing_chain = (
            self.route_prompt
            | self.llm
            | StrOutputParser()
        )

    def route(self, user_input: str) -> Optional[str]:
        """
        根据用户输入，选择最合适的 Skill

        处理流程：
        1. 获取所有 Skills 的摘要信息
        2. 将摘要和用户输入传递给 LCEL Chain
        3. LLM 返回 Skill 名称或 "NONE"
        4. 验证返回的 Skill 是否在注册表中
        5. 返回有效的 Skill 名称，或 None

        参数：
            user_input: 用户的输入文本

        返回：
            Skill 名称（字符串），如果没有匹配则返回 None
        """
        # 获取所有 Skills 的摘要信息
        skills_summary = self.registry.get_all_skills_summary()

        try:
            # 调用 LCEL Chain 进行路由
            # invoke 方法接收一个字典，包含所有模板变量
            result = self.routing_chain.invoke({
                "skills_summary": skills_summary,
                "user_input": user_input
            })

            # result 是 StrOutputParser 返回的字符串
            skill_name = result.strip()

            # 调试信息：打印路由结果
            print(f"路由结果: skill_name='{skill_name}'")
            print(f"注册表中的 Skills: {self.registry.get_skill_names()}")

            # 验证返回的 Skill 是否存在
            # 如果 LLM 返回 "NONE" 或不存在的 Skill 名称，返回 None
            if skill_name == "NONE" or skill_name not in self.registry.skills:
                print(f"路由失败: skill_name='{skill_name}', 是否在注册表={skill_name in self.registry.skills}")
                return None

            return skill_name

        except Exception as e:
            print(f"错误: 路由过程出错: {e}")
            return None


class SkillExecutor:
    """
    Skill 执行器 - 使用 LangChain 1.0 LCEL Chains 实现

    职责说明：
    1. 接收选中的 Skill 名称和用户输入
    2. 从注册表中加载完整的 Skill 文档
    3. 将 Skill 文档和用户输入传递给 LLM
    4. LLM 按照 Skill 文档中的 Workflow 执行任务
    5. 返回执行结果

    技术实现：
    - 使用 ChatPromptTemplate 构建执行提示词模板
    - 使用 LCEL 构建处理链：Prompt -> LLM -> StrOutputParser
    - 使用 DeepSeek API 作为 LLM 后端（temperature=0.7 允许一定创造性）
    - 支持传递额外的上下文信息（如对话历史、用户偏好等）

    属性说明：
        registry: SkillRegistry 实例，用于获取 Skill 完整内容
        llm: ChatOpenAI 实例，用于调用 LLM
        execution_prompt: 执行提示词模板
        execution_chain: LCEL 处理链
    """

    def __init__(self, registry: SkillRegistry):
        """
        初始化 Skill 执行器

        参数：
            registry: SkillRegistry 实例
        """
        self.registry = registry

        # 初始化 ChatOpenAI（使用 DeepSeek API）
        # temperature=0.7 允许一定的创造性，适合生成自然语言响应
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            temperature=0.7
        )

        # 构建执行 Prompt Template
        # system 消息：包含完整的 Skill 文档和执行要求
        # human 消息：用户的实际输入
        self.execution_prompt = ChatPromptTemplate.from_messages([
            ("system", """你现在要执行以下 Skill：

            {skill_content}

            ---

            **执行要求**:
            1. 严格按照 Skill 文档中的 Workflow 步骤执行
            2. 遵守所有 Constraints 约束条件
            3. 参考 Examples 中的示例风格
            4. 直接返回最终结果，不要解释执行过程

            {context_info}"""),
            ("human", "{user_input}")
        ])

        # 构建 LCEL Chain（LangChain Expression Language 链式调用）
        # 处理流程：
        # 1. execution_prompt: 将 Skill 文档和用户输入格式化为提示词
        # 2. llm: 调用 LLM 执行任务
        # 3. StrOutputParser: 将 LLM 输出解析为字符串
        self.execution_chain = (
            self.execution_prompt
            | self.llm
            | StrOutputParser()
        )

    def execute(self, skill_name: str, user_input: str, context: Optional[Dict] = None) -> str:
        """
        执行指定的 Skill

        处理流程：
        1. 从注册表中获取 Skill 的完整内容
        2. 准备上下文信息（如果提供）
        3. 将 Skill 内容、上下文和用户输入传递给 LCEL Chain
        4. LLM 按照 Skill 文档执行任务
        5. 返回执行结果

        参数：
            skill_name: Skill 的名称（如 "get-weather"）
            user_input: 用户的输入文本
            context: 额外的上下文信息（可选），如：
                    {
                        "conversation_history": [...],
                        "user_preferences": {...},
                        "current_location": "北京"
                    }

        返回：
            执行结果（字符串），如果执行失败则返回错误信息
        """
        # 从注册表中获取 Skill 的完整内容
        skill = self.registry.get_skill(skill_name)
        if not skill:
            return f"错误: Skill '{skill_name}' 不存在"

        # 准备上下文信息
        # 如果提供了 context，将其格式化为 JSON 字符串
        context_info = ""
        if context:
            context_info = f"\n\n**额外上下文**:\n{json.dumps(context, ensure_ascii=False, indent=2)}"

        try:
            # 调用 LCEL Chain 执行 Skill
            # invoke 方法接收一个字典，包含所有模板变量
            result = self.execution_chain.invoke({
                "skill_content": skill.full_content,  # Skill 的完整文档
                "context_info": context_info,  # 额外的上下文信息
                "user_input": user_input  # 用户的输入
            })

            return result

        except Exception as e:
            return f"错误: 执行 Skill 时出错: {e}"


class AgentSkillsEngine:
    """
    Agent Skills 引擎 - 完整的系统入口（LangChain 1.0 版本）

    职责说明：
    1. 统一的系统入口，协调 SkillRegistry、SkillRouter 和 SkillExecutor
    2. 提供简单的 API 接口，隐藏内部实现细节
    3. 处理完整的请求流程：路由 -> 执行 -> 返回结果

    使用流程：
    1. 初始化引擎，传入 Skills 目录路径
    2. 调用 process() 方法处理用户输入
    3. 引擎自动完成路由和执行，返回结果

    属性说明：
        registry: SkillRegistry 实例，管理所有 Skills
        router: SkillRouter 实例，负责路由选择
        executor: SkillExecutor 实例，负责执行 Skill
    """

    def __init__(self, skills_dir: str):
        """
        初始化 Agent Skills Engine

        初始化流程：
        1. 创建 SkillRegistry，加载所有 Skills
        2. 创建 SkillRouter，准备路由功能
        3. 创建 SkillExecutor，准备执行功能

        参数：
            skills_dir: Skill 文件所在的目录路径
        """
        print("初始化 Agent Skills Engine (LangChain 1.0)...\n")

        # 创建 Skill 注册表，加载所有 Skills
        self.registry = SkillRegistry(skills_dir)

        # 创建路由器，用于选择合适的 Skill
        self.router = SkillRouter(self.registry)

        # 创建执行器，用于执行选中的 Skill
        self.executor = SkillExecutor(self.registry)

        print("Agent Skills Engine 初始化完成\n")

    def process(self, user_input: str, context: Optional[Dict] = None) -> Tuple[str, Optional[str]]:
        """
        处理用户输入

        完整流程：
        1. 接收用户输入
        2. 使用 SkillRouter 选择最合适的 Skill
        3. 如果找到合适的 Skill，使用 SkillExecutor 执行
        4. 返回执行结果和使用的 Skill 名称

        参数：
            user_input: 用户的输入文本
            context: 额外的上下文信息（可选），如：
                    {
                        "conversation_history": [...],
                        "user_preferences": {...}
                    }

        返回：
            元组 (执行结果, 使用的 Skill 名称)
            - 执行结果: 字符串，包含 Skill 的执行结果
            - Skill 名称: 字符串，如果没有找到合适的 Skill 则为 None
        """
        print(f"用户输入: {user_input}")

        # 步骤 1: 路由 - 选择合适的 Skill
        print("正在路由到合适的 Skill...")
        skill_name = self.router.route(user_input)

        # 如果没有找到合适的 Skill，返回默认响应
        if not skill_name:
            print("没有找到合适的 Skill\n")
            return "抱歉，我无法处理这个请求。", None

        print(f"选择 Skill: {skill_name}\n")

        # 步骤 2: 执行 - 运行 Skill
        print(f"正在执行 Skill: {skill_name}...")
        result = self.executor.execute(skill_name, user_input, context)

        print("执行完成\n")

        return result, skill_name

    def list_skills(self) -> List[str]:
        """
        列出所有可用的 Skills

        返回：
            Skill 名称的列表（如 ["get-weather", "translate-text"]）
        """
        return self.registry.get_skill_names()


# ============ 示例用法 ============

if __name__ == "__main__":
    """
    主程序入口 - 演示 Agent Skills Engine 的基本用法

    示例包括：
    1. 初始化引擎
    2. 测试天气查询（单城市）
    3. 测试多城市对比
    4. 测试无法匹配的请求
    5. 列出所有可用的 Skills
    """

    # 初始化引擎（指向你的 Skills 目录）
    # 注意：需要确保 ./skills 目录存在，并包含有效的 Skill 文件
    engine = AgentSkillsEngine(skills_dir="./skills")

    # 测试 1: 天气查询
    # 预期：路由到 get-weather Skill，返回天气信息
    print("=" * 60)
    print("测试 1: 天气查询")
    print("=" * 60)
    result, skill = engine.process("北京今天天气怎么样？")
    print(f"AI 回复: {result}")
    print(f"使用的 Skill: {skill}\n")

    # 测试 2: 多城市对比
    # 预期：路由到 get-weather Skill，返回多城市天气对比
    print("=" * 60)
    print("测试 2: 多城市对比")
    print("=" * 60)
    result, skill = engine.process("帮我对比一下北京和上海的天气")
    print(f"AI 回复: {result}")
    print(f"使用的 Skill: {skill}\n")

    # 测试 3: 无法匹配的请求
    # 预期：没有找到合适的 Skill，返回默认响应
    print("=" * 60)
    print("测试 3: 无法匹配的请求")
    print("=" * 60)
    result, skill = engine.process("帮我写一首诗")
    print(f"AI 回复: {result}")
    print(f"使用的 Skill: {skill}\n")

    # 列出所有可用的 Skills
    # 显示系统中已加载的所有 Skill 名称
    print("=" * 60)
    print("所有可用的 Skills:")
    print("=" * 60)
    for skill_name in engine.list_skills():
        print(f"- {skill_name}")
