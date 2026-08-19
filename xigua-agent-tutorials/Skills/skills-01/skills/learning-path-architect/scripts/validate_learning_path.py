#!/usr/bin/env python3
"""
Learning Path Validator

验证生成的学习路径文档是否符合质量标准和模板结构。

Usage:
    python3 validate_learning_path.py <path_to_learning_path.md>
    python3 validate_learning_path.py <path_to_learning_path.md> --strict
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple


class ValidationResult:
    """验证结果"""
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.stats: Dict[str, any] = {}

    def add_error(self, message: str):
        self.errors.append(f"❌ ERROR: {message}")

    def add_warning(self, message: str):
        self.warnings.append(f"⚠️  WARNING: {message}")

    def add_info(self, message: str):
        self.info.append(f"ℹ️  INFO: {message}")

    def is_valid(self, strict: bool = False) -> bool:
        """判断是否通过验证"""
        if self.errors:
            return False
        if strict and self.warnings:
            return False
        return True

    def print_report(self):
        """打印验证报告"""
        print("\n" + "="*60)
        print("📋 Learning Path Validation Report")
        print("="*60)

        # 统计信息
        if self.stats:
            print("\n📊 Statistics:")
            for key, value in self.stats.items():
                print(f"  - {key}: {value}")

        # 错误
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")

        # 警告
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")

        # 信息
        if self.info:
            print(f"\nℹ️  Info ({len(self.info)}):")
            for info in self.info:
                print(f"  {info}")

        # 总结
        print("\n" + "="*60)
        if not self.errors and not self.warnings:
            print("✅ Validation PASSED - All checks successful!")
        elif not self.errors:
            print("⚠️  Validation PASSED with warnings")
        else:
            print("❌ Validation FAILED")
        print("="*60 + "\n")


class LearningPathValidator:
    """学习路径验证器"""

    # 必需的一级章节
    REQUIRED_SECTIONS = [
        "学习目标与边界",
        "学习路径总览",
        "阶段一：基础入门",
        "阶段二：进阶案例",
        "阶段三：项目实战",
        "学习资源推荐",
    ]

    # 推荐的一级章节
    RECOMMENDED_SECTIONS = [
        "常见问题与解决方案",
        "进阶方向",
    ]

    # 必需的子章节（在"学习目标与边界"下）
    REQUIRED_SUBSECTIONS_GOAL = [
        "核心目标",
        "学习边界",
        "前置知识",
        "预计时间",
    ]

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.content = ""
        self.lines = []
        self.result = ValidationResult()

    def validate(self, strict: bool = False) -> ValidationResult:
        """执行完整验证"""
        # 1. 文件存在性检查
        if not self._check_file_exists():
            return self.result

        # 2. 读取文件
        if not self._read_file():
            return self.result

        # 3. 基础结构检查
        self._check_basic_structure()

        # 4. 章节完整性检查
        self._check_required_sections()

        # 5. 内容质量检查
        self._check_content_quality()

        # 6. 学习路径图检查
        self._check_learning_path_diagram()

        # 7. 检查点检查
        self._check_checkpoints()

        # 8. 时间估算检查
        self._check_time_estimates()

        # 9. 依赖关系检查
        self._check_dependencies()

        # 10. 统计信息
        self._collect_statistics()

        return self.result

    def _check_file_exists(self) -> bool:
        """检查文件是否存在"""
        if not self.file_path.exists():
            self.result.add_error(f"File not found: {self.file_path}")
            return False
        if not self.file_path.is_file():
            self.result.add_error(f"Not a file: {self.file_path}")
            return False
        return True

    def _read_file(self) -> bool:
        """读取文件内容"""
        try:
            self.content = self.file_path.read_text(encoding='utf-8')
            self.lines = self.content.split('\n')
            return True
        except Exception as e:
            self.result.add_error(f"Failed to read file: {e}")
            return False

    def _check_basic_structure(self):
        """检查基础结构"""
        # 检查标题
        if not self.content.startswith('#'):
            self.result.add_error("Document must start with a title (# ...)")

        # 检查是否有一级标题
        h1_pattern = re.compile(r'^# .+', re.MULTILINE)
        h1_matches = h1_pattern.findall(self.content)
        if not h1_matches:
            self.result.add_error("No H1 title found")
        elif len(h1_matches) > 1:
            self.result.add_warning(f"Multiple H1 titles found ({len(h1_matches)})")

        # 检查文档长度
        line_count = len(self.lines)
        if line_count < 100:
            self.result.add_warning(f"Document is very short ({line_count} lines)")
        elif line_count > 1000:
            self.result.add_warning(f"Document is very long ({line_count} lines)")

    def _check_required_sections(self):
        """检查必需章节"""
        # 提取所有二级标题
        h2_pattern = re.compile(r'^## (.+)', re.MULTILINE)
        h2_sections = h2_pattern.findall(self.content)

        # 检查必需章节
        for required in self.REQUIRED_SECTIONS:
            found = any(required in section for section in h2_sections)
            if not found:
                self.result.add_error(f"Missing required section: {required}")

        # 检查推荐章节
        for recommended in self.RECOMMENDED_SECTIONS:
            found = any(recommended in section for section in h2_sections)
            if not found:
                self.result.add_warning(f"Missing recommended section: {recommended}")

        # 检查"学习目标与边界"下的子章节
        goal_section = self._extract_section("学习目标与边界")
        if goal_section:
            for required_sub in self.REQUIRED_SUBSECTIONS_GOAL:
                if f"**{required_sub}**" not in goal_section:
                    self.result.add_error(
                        f"Missing required subsection in '学习目标与边界': {required_sub}"
                    )

    def _check_content_quality(self):
        """检查内容质量"""
        # 检查是否有空章节
        h2_pattern = re.compile(r'^## (.+?)$', re.MULTILINE)
        sections = h2_pattern.split(self.content)

        for i in range(1, len(sections), 2):
            section_title = sections[i].strip()
            section_content = sections[i+1].strip() if i+1 < len(sections) else ""

            # 检查章节内容长度
            if len(section_content) < 50:
                self.result.add_warning(
                    f"Section '{section_title}' has very little content"
                )

        # 检查是否有占位符
        placeholders = [
            r'\[.*?\]',  # [待补充]
            r'TODO',
            r'TBD',
            r'XXX',
        ]
        for pattern in placeholders:
            matches = re.findall(pattern, self.content)
            if matches:
                self.result.add_warning(
                    f"Found {len(matches)} placeholder(s): {pattern}"
                )

    def _check_learning_path_diagram(self):
        """检查学习路径图"""
        # 检查是否有代码块（学习路径图通常在代码块中）
        code_block_pattern = re.compile(r'```[\s\S]*?```', re.MULTILINE)
        code_blocks = code_block_pattern.findall(self.content)

        if not code_blocks:
            self.result.add_warning("No code blocks found (learning path diagram missing?)")
            return

        # 检查是否有阶段标记
        path_diagram = self._extract_section("学习路径总览")
        if path_diagram:
            if "阶段1" not in path_diagram:
                self.result.add_error("Learning path diagram missing '阶段1'")
            if "阶段2" not in path_diagram:
                self.result.add_error("Learning path diagram missing '阶段2'")
            if "阶段3" not in path_diagram:
                self.result.add_error("Learning path diagram missing '阶段3'")

            # 检查是否有关键路径
            if "关键路径" not in path_diagram:
                self.result.add_warning("Learning path diagram missing '关键路径'")

    def _check_checkpoints(self):
        """检查检查点"""
        # 检查每个阶段是否有检查点
        for stage in ["阶段一", "阶段二", "阶段三"]:
            stage_section = self._extract_section(stage)
            if stage_section:
                if "检查点" not in stage_section:
                    self.result.add_error(f"{stage} missing checkpoint section")
                else:
                    # 检查是否有 ✓ 标记
                    checkpoint_count = stage_section.count("✓")
                    if checkpoint_count == 0:
                        self.result.add_error(f"{stage} checkpoint section has no items")
                    elif checkpoint_count < 3:
                        self.result.add_warning(
                            f"{stage} has only {checkpoint_count} checkpoints (recommended: 3-5)"
                        )

    def _check_time_estimates(self):
        """检查时间估算"""
        # 检查"预计时间"部分
        goal_section = self._extract_section("学习目标与边界")
        if goal_section:
            if "预计时间" not in goal_section:
                self.result.add_error("Missing '预计时间' in learning goals")
            else:
                # 检查是否有具体的时间估算
                time_patterns = [
                    r'\d+\s*小时',
                    r'\d+\s*天',
                    r'\d+\s*周',
                ]
                has_time = any(
                    re.search(pattern, goal_section) for pattern in time_patterns
                )
                if not has_time:
                    self.result.add_warning("No specific time estimates found")

    def _check_dependencies(self):
        """检查依赖关系"""
        # 检查学习路径图中是否有依赖标记
        path_diagram = self._extract_section("学习路径总览")
        if path_diagram:
            if "依赖" not in path_diagram:
                self.result.add_warning(
                    "No dependency information found in learning path diagram"
                )

    def _collect_statistics(self):
        """收集统计信息"""
        self.result.stats = {
            "Total lines": len(self.lines),
            "Total characters": len(self.content),
            "H1 sections": len(re.findall(r'^# ', self.content, re.MULTILINE)),
            "H2 sections": len(re.findall(r'^## ', self.content, re.MULTILINE)),
            "H3 sections": len(re.findall(r'^### ', self.content, re.MULTILINE)),
            "Code blocks": len(re.findall(r'```', self.content)) // 2,
            "Checkpoints": self.content.count("✓"),
        }

    def _extract_section(self, section_title: str) -> str:
        """提取指定章节的内容"""
        # 匹配 ## 章节标题
        pattern = re.compile(
            rf'^## .*?{re.escape(section_title)}.*?$\n(.*?)(?=^## |\Z)',
            re.MULTILINE | re.DOTALL
        )
        match = pattern.search(self.content)
        return match.group(1) if match else ""


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python3 validate_learning_path.py <path_to_learning_path.md> [--strict]")
        sys.exit(1)

    file_path = sys.argv[1]
    strict = "--strict" in sys.argv

    print(f"\n🔍 Validating learning path: {file_path}")
    if strict:
        print("   Mode: STRICT (warnings treated as errors)")

    validator = LearningPathValidator(file_path)
    result = validator.validate(strict=strict)
    result.print_report()

    # 返回退出码
    sys.exit(0 if result.is_valid(strict=strict) else 1)


if __name__ == "__main__":
    main()
