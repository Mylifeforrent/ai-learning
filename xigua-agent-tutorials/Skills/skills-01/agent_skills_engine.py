"""
Agent Skills Engine - 基于 OpenAI SDK 的完整实现

核心流程：
1. 预加载所有 Skill 的元信息（name、description、触发条件）
2. 用户输入后，通过路由器选择合适的 Skill
3. 加载完整 Skill 文档并执行
4. 返回最终结果


代码执行流程：
1. 构建Python虚拟环境
conda create -n skills python=3.11
2. 安装依赖
   pip install -r requirements.txt
3. 执行脚本

   python agent_skills_engine.py
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI

# 从项目根目录的 .env 文件加载环境变量（DEEPSEEK_API_KEY 等）
load_dotenv()

# 初始化 OpenAI 客户端（使用 DeepSeek API）
# OpenAI SDK 使用说明：
# 1. 通过 base_url 参数可以切换到兼容 OpenAI 接口的其他服务（如 DeepSeek）
# 2. api_key 从环境变量中读取，避免硬编码敏感信息
# 3. 该 client 实例将在整个模块中复用，用于调用 chat.completions.create() 方法
client = OpenAI(
    api_key="sk-e3fb24cbbab646fa9788a85c19606667",
    base_url="https://api.deepseek.com"
)


@dataclass
class SkillMetadata:
    """
    Skill 元信息数据类

    用于存储每个 Skill 的基本信息，在路由阶段只需要加载这些轻量级元数据，
    而不需要加载完整的 Skill 文档内容，从而提高系统启动速度和路由效率。

    Attributes:
        name: Skill 的唯一标识名称（如 "get-weather"）
        description: Skill 的功能描述（用于路由判断）
        trigger_conditions: 触发该 Skill 的条件描述（从 description 中提取）
        file_path: Skill 文件的完整路径
        full_content: Skill 文件的完整内容（仅在执行时加载，初始为 None）
    """
    name: str
    description: str
    trigger_conditions: str
    file_path: str
    full_content: Optional[str] = None


class SkillRegistry:
    """
    Skill 注册表 - 负责加载和管理所有 Skills

    职责：
    1. 扫描指定目录下的所有 Skill 文件（.skill 和 .md 格式）
    2. 解析每个 Skill 文件的 YAML frontmatter，提取元信息
    3. 将所有 Skill 注册到内存中的字典，供路由器和执行器使用
    4. 提供查询接口，支持按名称获取 Skill 或获取所有 Skill 的摘要
    """

    def __init__(self, skills_dir: str):
        """
        初始化 Skill 注册表

        Args:
            skills_dir: Skills 文件所在的目录路径
        """
        self.skills_dir = Path(skills_dir)
        # 存储所有已加载的 Skill，key 为 Skill 名称，value 为 SkillMetadata 对象
        self.skills: Dict[str, SkillMetadata] = {}
        # 在初始化时立即加载所有 Skills
        self._load_all_skills()

    def _parse_skill_file(self, file_path: Path) -> Optional[SkillMetadata]:
        """
        解析单个 Skill 文件，提取元信息

        Skill 文件格式要求：
        - 文件开头必须包含 YAML frontmatter（用 --- 包裹）
        - frontmatter 中必须包含 name 和 description 字段
        - 触发条件从 description 中自动提取（匹配 "在...时使用" 模式）

        Args:
            file_path: Skill 文件的路径

        Returns:
            解析成功返回 SkillMetadata 对象，失败返回 None
        """
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 使用正则表达式提取 YAML frontmatter（格式：--- ... ---）
            frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            if not frontmatter_match:
                print(f"  {file_path.name} 缺少 frontmatter，跳过")
                return None

            frontmatter = frontmatter_match.group(1)

            # 从 frontmatter 中提取 name 和 description 字段
            name_match = re.search(r'name:\s*(.+)', frontmatter)
            desc_match = re.search(r'description:\s*(.+)', frontmatter)

            if not name_match or not desc_match:
                print(f" {file_path.name} 缺少 name 或 description，跳过")
                return None

            name = name_match.group(1).strip()
            description = desc_match.group(1).strip()

            # 从 description 中提取触发条件（匹配 "在...时使用" 模式）
            # 例如："在用户询问天气时使用" -> 提取 "用户询问天气"
            trigger_match = re.search(r'在(.+?)时使用', description)
            trigger_conditions = trigger_match.group(1) if trigger_match else description

            # 创建 SkillMetadata 对象，包含完整文件内容（用于后续执行）
            return SkillMetadata(
                name=name,
                description=description,
                trigger_conditions=trigger_conditions,
                file_path=str(file_path),
                full_content=content
            )

        except Exception as e:
            print(f" 解析 {file_path.name} 失败: {e}")
            return None

    def _load_all_skills(self):
        """
        扫描并加载所有 Skill 文件

        扫描逻辑：
        1. 检查 skills_dir 目录是否存在
        2. 查找所有 .skill 和 .md 文件
        3. 逐个解析文件并注册到 self.skills 字典中
        4. 打印加载进度和结果
        """
        # 检查目录是否存在
        if not self.skills_dir.exists():
            print(f" Skills 目录不存在: {self.skills_dir}")
            return

        # 查找所有 .skill 和 .md 文件
        skill_files = list(self.skills_dir.glob("*.skill")) + list(self.skills_dir.glob("*.md"))

        print(f"扫描 Skills 目录: {self.skills_dir}")
        print(f"找到 {len(skill_files)} 个 Skill 文件\n")

        # 逐个解析并注册 Skill
        for file_path in skill_files:
            skill = self._parse_skill_file(file_path)
            if skill:
                # 使用 Skill 名称作为 key 存储到字典中
                self.skills[skill.name] = skill
                print(f"  加载 Skill: {skill.name}")
                print(f"   描述: {skill.description[:60]}...")
                print(f"   触发条件: {skill.trigger_conditions}\n")

        print(f"成功加载 {len(self.skills)} 个 Skills\n")

    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        """
        获取指定 Skill 的完整内容

        Args:
            name: Skill 名称

        Returns:
            找到返回 SkillMetadata 对象，未找到返回 None
        """
        return self.skills.get(name)

    def get_all_skills_summary(self) -> str:
        """
        获取所有 Skills 的摘要信息（用于路由判断）

        该方法生成一个包含所有 Skill 名称和描述的文本摘要，
        供路由器在判断时使用，避免将完整的 Skill 文档传递给 LLM。

        Returns:
            格式化的 Skills 摘要文本
        """
        summary = "当前系统可用的 Skills：\n\n"
        for skill in self.skills.values():
            summary += f"- **{skill.name}**: {skill.description}\n"
        return summary


class SkillRouter:
    """
    Skill 路由器 - 负责根据用户输入选择合适的 Skill

    职责：
    1. 接收用户输入和所有可用 Skills 的摘要信息
    2. 调用 LLM 分析用户意图，判断应该激活哪个 Skill
    3. 返回最匹配的 Skill 名称，如果没有合适的 Skill 则返回 None

    设计思路：
    - 使用轻量级模型（deepseek-chat）进行快速路由判断
    - 只传递 Skills 的摘要信息，不传递完整文档，减少 token 消耗
    - 使用 temperature=0 确保路由结果的稳定性和可预测性
    """

    def __init__(self, registry: SkillRegistry):
        """
        初始化路由器

        Args:
            registry: Skill 注册表实例，用于获取所有可用 Skills 的信息
        """
        self.registry = registry

    def route(self, user_input: str) -> Optional[str]:
        """
        根据用户输入，选择最合适的 Skill

        工作流程：
        1. 从注册表获取所有 Skills 的摘要信息
        2. 构造路由 Prompt，包含用户输入和 Skills 摘要
        3. 调用 LLM 进行意图识别和 Skill 匹配
        4. 验证返回的 Skill 名称是否在注册表中
        5. 返回匹配的 Skill 名称或 None

        Args:
            user_input: 用户的原始输入文本

        Returns:
            匹配的 Skill 名称（如 "get-weather"），如果没有匹配则返回 None
        """
        # 获取所有 Skills 的摘要信息
        skills_summary = self.registry.get_all_skills_summary()

        # 构造路由 Prompt
        # 要求 LLM 只返回 Skill 名称或 "NONE"，避免返回多余的解释文本
        routing_prompt = f"""
        你是一个 Skill 路由器。根据用户的输入，判断应该激活哪个 Skill。

        {skills_summary}

        用户输入: {user_input}

        请分析用户的意图，并返回最合适的 Skill 名称。如果没有合适的 Skill，返回 "NONE"。

        **重要**: 只返回 Skill 名称，不要有任何其他内容。例如：get-weather 或 NONE
        """

        # 调用 OpenAI SDK 的 chat.completions.create() 方法
        # 参数说明：
        # - model: 使用的模型名称（deepseek-chat 是轻量级快速模型）
        # - messages: 对话消息列表，这里只有一条用户消息
        # - temperature: 控制输出的随机性，0 表示完全确定性输出
        # - max_tokens: 限制返回的最大 token 数，路由只需要返回 Skill 名称，50 足够
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": routing_prompt}],
            temperature=0,
            max_tokens=50
        )

        # 从响应中提取 Skill 名称
        # response.choices[0].message.content 包含 LLM 返回的文本内容
        skill_name = response.choices[0].message.content.strip()

        # 调试信息：打印模型返回的原始内容和注册表中的 Skills
        print(f"模型返回的原始内容: '{skill_name}'")
        print(f"注册表中的 Skills: {list(self.registry.skills.keys())}")

        # 验证返回的 Skill 是否存在于注册表中
        # 如果返回 "NONE" 或不在注册表中，则路由失败
        if skill_name == "NONE" or skill_name not in self.registry.skills:
            print(f"路由失败: skill_name='{skill_name}', 是否在注册表={skill_name in self.registry.skills}")
            return None

        return skill_name


class SkillExecutor:
    """
    Skill 执行器 - 负责执行具体的 Skill

    职责：
    1. 根据 Skill 名称从注册表获取完整的 Skill 文档
    2. 构造执行 Prompt，将 Skill 文档和用户输入组合
    3. 调用 LLM 执行 Skill 中定义的工作流
    4. 返回执行结果

    设计思路：
    - 使用强大模型（deepseek-chat）执行复杂任务
    - 将完整的 Skill 文档作为 system message 传递给 LLM
    - 支持传递额外的上下文信息（如对话历史、用户偏好等）
    - 使用 temperature=0.7 在保持稳定性的同时允许一定的创造性
    """

    def __init__(self, registry: SkillRegistry):
        """
        初始化执行器

        Args:
            registry: Skill 注册表实例，用于获取 Skill 的完整内容
        """
        self.registry = registry

    def execute(self, skill_name: str, user_input: str, context: Optional[Dict] = None) -> str:
        """
        执行指定的 Skill

        工作流程：
        1. 从注册表获取 Skill 的完整内容
        2. 构造执行 Prompt（包含 Skill 文档、执行要求、额外上下文）
        3. 调用 LLM 执行 Skill 中定义的工作流
        4. 返回 LLM 生成的执行结果

        Args:
            skill_name: Skill 名称（如 "get-weather"）
            user_input: 用户的原始输入文本
            context: 额外的上下文信息（可选），例如：
                     - 对话历史：{"history": [...]}
                     - 用户偏好：{"preferences": {...}}
                     - 环境变量：{"env": {...}}

        Returns:
            Skill 执行的结果文本
        """
        # 从注册表获取 Skill 的完整内容
        skill = self.registry.get_skill(skill_name)
        if not skill:
            return f" Skill '{skill_name}' 不存在"

        # 构造执行 Prompt
        execution_prompt = self._build_execution_prompt(skill, user_input, context)

        # 调用 OpenAI SDK 执行 Skill
        # 参数说明：
        # - model: 使用强大模型执行复杂任务
        # - messages: 包含两条消息：
        #   1. system message: 包含 Skill 文档和执行要求
        #   2. user message: 用户的原始输入
        # - temperature: 0.7 允许一定的创造性，适合生成自然语言回复
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": execution_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        )

        # 返回 LLM 生成的内容
        return response.choices[0].message.content

    def _build_execution_prompt(self, skill: SkillMetadata, user_input: str, context: Optional[Dict]) -> str:
        """
        构造执行 Prompt

        该方法将 Skill 文档、执行要求和额外上下文组合成一个完整的 Prompt，
        指导 LLM 按照 Skill 中定义的工作流执行任务。

        Args:
            skill: Skill 元信息对象（包含完整的 Skill 文档）
            user_input: 用户输入（在此方法中未直接使用，但保留参数以便扩展）
            context: 额外的上下文信息（可选）

        Returns:
            格式化的执行 Prompt 文本
        """
        # 基础 Prompt：包含 Skill 文档和执行要求
        prompt = f"""
        你现在要执行以下 Skill：

        {skill.full_content}

        ---

        **执行要求**:
        1. 严格按照 Skill 文档中的 Workflow 步骤执行
        2. 遵守所有 Constraints 约束条件
        3. 参考 Examples 中的示例风格
        4. 直接返回最终结果，不要解释执行过程
        """

        # 如果有额外上下文，将其添加到 Prompt 中
        # 使用 JSON 格式序列化上下文，确保结构化数据的可读性
        if context:
            prompt += f"\n\n**额外上下文**:\n{json.dumps(context, ensure_ascii=False, indent=2)}"

        return prompt


class AgentSkillsEngine:
    """
    Agent Skills 引擎 - 完整的系统入口

    职责：
    1. 初始化并协调三个核心组件：注册表、路由器、执行器
    2. 提供统一的 process() 接口处理用户输入
    3. 提供查询接口，支持列出所有可用的 Skills

    这是整个 Agent Skills 系统的门面（Facade）类，
    外部调用者只需要与这个类交互，无需关心内部的路由和执行细节。

    使用示例：
        engine = AgentSkillsEngine(skills_dir="./skills")
        result, skill_name = engine.process("北京今天天气怎么样？")
        print(result)
    """

    def __init__(self, skills_dir: str):
        """
        初始化 Agent Skills 引擎

        初始化流程：
        1. 创建 SkillRegistry 实例，加载所有 Skills
        2. 创建 SkillRouter 实例，用于路由判断
        3. 创建 SkillExecutor 实例，用于执行 Skills

        Args:
            skills_dir: Skills 文件所在的目录路径
        """
        print(" 初始化 Agent Skills Engine...\n")
        # 初始化注册表（会自动加载所有 Skills）
        self.registry = SkillRegistry(skills_dir)
        # 初始化路由器（依赖注册表）
        self.router = SkillRouter(self.registry)
        # 初始化执行器（依赖注册表）
        self.executor = SkillExecutor(self.registry)
        print(" Agent Skills Engine 初始化完成\n")

    def process(self, user_input: str, context: Optional[Dict] = None) -> Tuple[str, Optional[str]]:
        """
        处理用户输入

        这是系统的核心方法，完整的处理流程包括：
        1. 路由阶段：调用路由器选择最合适的 Skill
        2. 执行阶段：调用执行器运行选中的 Skill
        3. 返回结果：返回执行结果和使用的 Skill 名称

        Args:
            user_input: 用户的原始输入文本
            context: 额外的上下文信息（可选），例如：
                     - 对话历史：{"history": [...]}
                     - 用户偏好：{"preferences": {...}}
                     - 会话状态：{"session": {...}}

        Returns:
            一个元组 (执行结果, 使用的 Skill 名称)
            - 执行结果: Skill 执行后返回的文本
            - Skill 名称: 使用的 Skill 名称，如果没有匹配则为 None
        """
        print(f" 用户输入: {user_input}")

        # 步骤 1: 路由 - 选择合适的 Skill
        print(" 正在路由到合适的 Skill...")
        skill_name = self.router.route(user_input)

        # 如果没有找到合适的 Skill，返回默认回复
        if not skill_name:
            print(" 没有找到合适的 Skill\n")
            return "抱歉，我无法处理这个请求。", None

        print(f" 选择 Skill: {skill_name}\n")

        # 步骤 2: 执行 - 运行 Skill
        print(f"  正在执行 Skill: {skill_name}...")
        result = self.executor.execute(skill_name, user_input, context)

        print(" 执行完成\n")

        return result, skill_name

    def list_skills(self) -> List[str]:
        """
        列出所有可用的 Skills

        Returns:
            所有已加载的 Skill 名称列表
        """
        return list(self.registry.skills.keys())


# ============ 示例用法 ============

if __name__ == "__main__":
    """
    主程序入口 - 演示 Agent Skills Engine 的基本用法

    该示例展示了三种典型场景：
    1. 成功匹配并执行 Skill（天气查询）
    2. 成功匹配并执行 Skill（多城市对比）
    3. 无法匹配 Skill 的情况（返回默认回复）
    4. 列出所有可用的 Skills

    运行方式：
        python agent_skills_engine.py
    """

    # 初始化引擎（指向你的 Skills 目录）
    # 注意：确保 ./skills 目录存在且包含有效的 .skill 或 .md 文件
    engine = AgentSkillsEngine(skills_dir="./skills")

    # 测试 1: 天气查询
    # 预期：匹配到 "get-weather" Skill，返回天气信息
    print("=" * 60)
    print("测试 1: 天气查询")
    print("=" * 60)
    result, skill = engine.process("北京今天天气怎么样？")
    print(f" AI 回复: {result}")
    print(f" 使用的 Skill: {skill}\n")

    # 测试 2: 多城市对比
    # 预期：匹配到 "get-weather" Skill，返回多城市天气对比
    print("=" * 60)
    print("测试 2: 多城市对比")
    print("=" * 60)
    result, skill = engine.process("帮我对比一下北京和上海的天气")
    print(f" AI 回复: {result}")
    print(f" 使用的 Skill: {skill}\n")

    # 测试 3: 无法匹配的请求
    # 预期：没有匹配的 Skill，返回默认回复
    print("=" * 60)
    print("测试 3: 无法匹配的请求")
    print("=" * 60)
    result, skill = engine.process("帮我写一首诗")
    print(f" AI 回复: {result}")
    print(f" 使用的 Skill: {skill}\n")

    # 列出所有可用的 Skills
    # 用于调试和验证 Skills 是否正确加载
    print("=" * 60)
    print("所有可用的 Skills:")
    print("=" * 60)
    for skill_name in engine.list_skills():
        print(f"- {skill_name}")
