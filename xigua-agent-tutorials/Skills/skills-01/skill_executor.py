#!/usr/bin/env python3
"""
Skill Executor 实现
用于测试和验证 Skill 加载、解析、匹配的核心逻辑
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional


class SkillExecutor:
    """
    Skill 执行器类

    职责：
    1. 从指定目录加载所有 Skill 文件
    2. 解析 Skill 的 frontmatter（元数据）和 body（执行指南）
    3. 根据用户请求匹配最合适的 Skill

    属性：
        skills_dir (Path): Skill 文件所在的目录路径
        skills (Dict[str, Dict]): 已加载的 Skill 字典，key 为 skill 名称，value 为 skill 数据
    """

    def __init__(self, skills_dir: str = ".claude/skills"):
        """
        初始化 Skill 执行器

        参数：
            skills_dir (str): Skill 目录路径，默认为 ".claude/skills"

        执行流程：
            1. 将字符串路径转换为 Path 对象
            2. 初始化空的 skills 字典
            3. 自动加载目录下的所有 Skill
        """
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, Dict] = {}
        self.load_all_skills()

    def load_all_skills(self):
        """
        加载所有 Skill 文件

        执行流程：
            1. 检查 skills 目录是否存在
            2. 遍历目录下的所有子目录
            3. 在每个子目录中查找 SKILL.md 文件
            4. 调用 load_skill() 加载找到的 Skill 文件

        注意：
            - 如果目录不存在，会打印错误信息并返回
            - 只处理子目录中的 SKILL.md 文件，忽略其他文件
        """
        if not self.skills_dir.exists():
            print(f"[错误] Skill 目录不存在: {self.skills_dir}")
            return

        # 遍历 skills 目录下的所有子目录
        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir():
                skill_file = skill_path / "SKILL.md"
                if skill_file.exists():
                    self.load_skill(skill_file)

    def load_skill(self, skill_file: Path):
        """
        加载单个 Skill 文件

        参数：
            skill_file (Path): SKILL.md 文件的完整路径

        执行流程：
            1. 读取文件内容
            2. 调用 parse_skill_content() 解析 frontmatter 和 body
            3. 提取 skill 名称和描述
            4. 将解析后的数据存储到 self.skills 字典中

        存储结构：
            self.skills[skill_name] = {
                'name': skill 名称,
                'description': skill 描述,
                'body': skill 执行指南（markdown 正文）,
                'path': skill 文件路径
            }
        """
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析 frontmatter 和 body
        frontmatter, body = self.parse_skill_content(content)

        if frontmatter and 'name' in frontmatter:
            skill_name = frontmatter['name']
            self.skills[skill_name] = {
                'name': skill_name,
                'description': frontmatter.get('description', ''),
                'body': body,
                'path': skill_file
            }
            print(f"[成功] 加载 Skill: {skill_name}")

    def parse_skill_content(self, content: str) -> tuple:
        """
        解析 Skill 文件内容，分离 frontmatter 和 body

        参数：
            content (str): SKILL.md 文件的完整内容

        返回：
            tuple: (frontmatter_dict, body_string)
                - frontmatter_dict: 解析后的 YAML 元数据字典
                - body_string: markdown 正文内容

        Frontmatter 格式：
            ---
            name: skill-name
            description: skill description
            ---

            # Skill Body
            ...

        执行流程：
            1. 检查内容是否以 '---' 开头
            2. 使用 '---' 分割内容，获取 frontmatter 和 body
            3. 使用 yaml.safe_load() 解析 frontmatter
            4. 返回解析后的元数据和正文

        异常处理：
            - 如果没有 frontmatter，返回 (None, content)
            - 如果 YAML 解析失败，打印错误并返回 (None, content)
        """
        # 检查是否有 frontmatter（以 --- 开头和结尾）
        if not content.startswith('---'):
            return None, content

        # 分离 frontmatter 和 body
        # split('---', 2) 最多分割 2 次，得到 ['', frontmatter, body]
        parts = content.split('---', 2)
        if len(parts) < 3:
            return None, content

        # 解析 YAML frontmatter
        try:
            frontmatter = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            print(f"[错误] YAML 解析错误: {e}")
            return None, content

        body = parts[2].strip()
        return frontmatter, body

    def match_skill(self, user_request: str) -> Optional[Dict]:
        """
        根据用户请求匹配最合适的 Skill

        参数：
            user_request (str): 用户的请求文本

        返回：
            Optional[Dict]: 匹配到的 Skill 数据字典，如果没有匹配则返回 None

        匹配算法：
            1. 将用户请求转换为小写并分词
            2. 遍历所有已加载的 Skill
            3. 计算每个 Skill 的匹配分数（关键词在 description 中出现的次数）
            4. 返回分数最高的 Skill

        匹配分数计算：
            score = sum(1 for keyword in keywords if keyword in description)
            即：用户请求中的每个词在 skill description 中出现一次，分数 +1

        注意：
            - 这是一个简化的匹配逻辑，实际生产环境可能需要更复杂的算法
            - 如果最高分数为 0（没有任何关键词匹配），返回 None
        """
        # 简化的匹配逻辑：基于关键词匹配
        keywords = user_request.lower().split()

        best_match = None
        best_score = 0

        # 遍历所有 Skill，计算匹配分数
        for skill_name, skill_data in self.skills.items():
            description = skill_data['description'].lower()

            # 计算匹配分数：统计有多少个关键词出现在 description 中
            score = sum(1 for keyword in keywords if keyword in description)

            if score > best_score:
                best_score = score
                best_match = skill_data

        if best_match and best_score > 0:
            print(f"[匹配] 找到 Skill: {best_match['name']} (匹配分数: {best_score})")
            return best_match

        print("[警告] 未找到匹配的 Skill")
        return None


class AgentWithSkills:
    """
    带有 Skill 支持的 Agent 类

    职责：
    1. 管理 SkillExecutor 实例
    2. 根据用户请求判断是否需要使用 Skill
    3. 构建包含 Skill 的系统提示词
    4. 处理用户请求并返回响应

    属性：
        skill_executor (SkillExecutor): Skill 执行器实例
        base_system_prompt (str): 基础系统提示词模板
    """

    def __init__(self, skills_dir: str = ".claude/skills"):
        """
        初始化 Agent

        参数：
            skills_dir (str): Skill 目录路径，默认为 ".claude/skills"

        执行流程：
            1. 创建 SkillExecutor 实例（自动加载所有 Skill）
            2. 设置基础系统提示词模板
        """
        self.skill_executor = SkillExecutor(skills_dir)
        self.base_system_prompt = """
你是一个智能助手，可以帮助用户完成各种任务。
你可以调用已加载的 Skill 来完成复杂的工作流。
"""

    def build_system_prompt(self, skill: Optional[Dict] = None) -> str:
        """
        构建系统提示词

        参数：
            skill (Optional[Dict]): 要注入的 Skill 数据字典，如果为 None 则只返回基础提示词

        返回：
            str: 完整的系统提示词

        系统提示词结构：
            1. 基础系统提示词（固定部分）
            2. 当前激活的 Skill 名称
            3. Skill 描述
            4. Skill 执行指南（body 内容）
            5. 执行要求说明

        注意：
            - 如果 skill 为 None，只返回基础提示词
            - Skill 的 body 内容会完整注入到系统提示词中
        """
        prompt = self.base_system_prompt

        if skill:
            # 注入 Skill 的内容到系统提示词
            prompt += f"\n\n# 当前激活的 Skill: {skill['name']}\n\n"
            prompt += f"## Skill 描述\n{skill['description']}\n\n"
            prompt += f"## Skill 执行指南\n{skill['body']}\n\n"
            prompt += "请严格按照上述 Skill 的 Workflow 执行任务。\n"

        return prompt

    def process_request(self, user_request: str) -> str:
        """
        处理用户请求的主流程

        参数：
            user_request (str): 用户的请求文本

        返回：
            str: Agent 的响应文本

        执行流程：
            1. 识别任务：打印用户请求
            2. 判断能力边界：调用 needs_skill() 判断是否需要 Skill
            3. 如果不需要 Skill，直接返回简单响应
            4. 如果需要 Skill，调用 match_skill() 匹配合适的 Skill
            5. 如果匹配失败，返回简单响应
            6. 如果匹配成功，构建包含 Skill 的系统提示词
            7. 返回激活 Skill 的确认信息

        注意：
            - 这是一个简化的实现，实际生产环境需要调用 LLM API
            - 当前实现只返回确认信息，不执行实际的 LLM 调用
        """
        # 步骤一：识别任务（简化实现）
        print(f"\n[请求] 用户请求: {user_request}")

        # 步骤二：判断能力边界（简化实现）
        needs_skill = self.needs_skill(user_request)

        if not needs_skill:
            print("[判断] 任务简单，无需 Skill")
            return self.simple_response(user_request)

        # 步骤三：匹配 Skill
        matched_skill = self.skill_executor.match_skill(user_request)

        if not matched_skill:
            print("[警告] 未找到合适的 Skill，使用默认处理")
            return self.simple_response(user_request)

        # 步骤四：执行 Skill（注入 Prompt）
        system_prompt = self.build_system_prompt(matched_skill)
        print(f"\n[执行] 系统提示词已更新，注入 Skill: {matched_skill['name']}")
        print(f"[信息] 系统提示词长度: {len(system_prompt)} 字符")

        # 步骤五：整合输出（这里简化为返回系统提示词确认信息）
        return f"已激活 Skill: {matched_skill['name']}\n系统提示词已更新"

    def needs_skill(self, user_request: str) -> bool:
        """
        判断任务是否需要 Skill

        参数：
            user_request (str): 用户请求文本

        返回：
            bool: True 表示需要 Skill，False 表示不需要

        判断逻辑：
            - 简化的关键词匹配
            - 如果用户请求中包含预定义的关键词，则认为需要 Skill
            - 实际生产环境可能需要更复杂的判断逻辑（如使用 LLM 判断）

        关键词列表：
            - 中文：测试、重构、部署、分析、生成、设计、学习、路径
            - 英文：learning、path
        """
        # 简化的判断逻辑：包含特定关键词则需要 Skill
        skill_keywords = ['测试', '重构', '部署', '分析', '生成', '设计', '学习', '路径', 'learning', 'path']
        return any(keyword in user_request for keyword in skill_keywords)

    def simple_response(self, user_request: str) -> str:
        """
        简单响应（不使用 Skill）

        参数：
            user_request (str): 用户请求文本

        返回：
            str: 简单的响应文本

        使用场景：
            - 任务不需要 Skill 时
            - 未找到匹配的 Skill 时

        注意：
            - 这是一个占位实现，实际生产环境应该调用 LLM API
        """
        return f"收到请求: {user_request}\n使用默认处理流程"


def main():
    """
    主测试函数

    功能：
        1. 初始化 AgentWithSkills 实例
        2. 运行三个测试示例
        3. 验证 Skill 加载、匹配、注入的完整流程

    测试示例：
        - 示例一：需要 Skill 的请求（英文，匹配 learning-path-architect）
        - 示例二：不需要 Skill 的简单问答
        - 示例三：查看注入后的完整系统提示词

    输出信息：
        - Skill 加载状态
        - 匹配结果
        - 系统提示词长度
        - 系统提示词预览
    """
    print("=" * 80)
    print("Skill Executor 测试")
    print("=" * 80)

    # 测试本地 learning-path-architect skill
    skills_dir = "./skills"

    print(f"\n[目录] Skill 目录: {skills_dir}")
    print("-" * 80)

    # 初始化 Agent
    agent = AgentWithSkills(skills_dir=skills_dir)

    print(f"\n[统计] 已加载 {len(agent.skill_executor.skills)} 个 Skill")
    print("-" * 80)

    # 示例一：需要 Skill 的请求（使用英文以匹配英文 description）
    print("\n" + "=" * 80)
    print("示例一：设计学习路径（英文请求）")
    print("=" * 80)
    response = agent.process_request("design a learning path for Python")
    print(f"\n[响应] Agent 响应:\n{response}")

    # 示例二：不需要 Skill 的请求
    print("\n" + "=" * 80)
    print("示例二：简单问答")
    print("=" * 80)
    response = agent.process_request("什么是 Python？")
    print(f"\n[响应] Agent 响应:\n{response}")

    # 示例三：查看注入后的系统提示词
    print("\n" + "=" * 80)
    print("示例三：查看系统提示词")
    print("=" * 80)
    matched_skill = agent.skill_executor.match_skill("create a learning roadmap")
    if matched_skill:
        system_prompt = agent.build_system_prompt(matched_skill)
        print(f"\n[预览] 完整的系统提示词预览 (前 800 字符):\n")
        print(system_prompt[:800])
        print("\n...")
        print(f"\n[统计] 系统提示词总长度: {len(system_prompt)} 字符")
        print(f"[统计] Skill Body 长度: {len(matched_skill['body'])} 字符")


if __name__ == "__main__":
    main()
