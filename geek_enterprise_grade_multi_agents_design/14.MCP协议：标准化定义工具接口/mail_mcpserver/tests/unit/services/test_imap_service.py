"""
IMAP 服务单元测试
"""
import pytest
from imap_tools import AND

from app.services.imap_service import _parse_search_query


class TestParseSearchQuery:
    """测试搜索查询解析函数"""

    def test_empty_query(self):
        """测试空查询"""
        result = _parse_search_query("")
        assert result == "ALL"

    def test_no_prefix_default_subject(self):
        """测试无前缀时默认搜索主题"""
        result = _parse_search_query("会议")
        assert isinstance(result, AND)
        # 验证返回的是 AND(subject="会议")
        assert str(result) == str(AND(subject="会议"))

    def test_subject_prefix(self):
        """测试 subject: 前缀"""
        result = _parse_search_query("subject:会议")
        assert isinstance(result, AND)
        assert str(result) == str(AND(subject="会议"))

    def test_from_prefix(self):
        """测试 from: 前缀"""
        result = _parse_search_query("from:alice@qq.com")
        assert isinstance(result, AND)
        assert str(result) == str(AND(from_="alice@qq.com"))

    def test_from_prefix_partial(self):
        """测试 from: 前缀部分匹配"""
        result = _parse_search_query("from:@qq.com")
        assert isinstance(result, AND)
        assert str(result) == str(AND(from_="@qq.com"))

    def test_to_prefix(self):
        """测试 to: 前缀"""
        result = _parse_search_query("to:bob@163.com")
        assert isinstance(result, AND)
        assert str(result) == str(AND(to="bob@163.com"))

    def test_text_prefix(self):
        """测试 text: 前缀"""
        result = _parse_search_query("text:重要")
        assert isinstance(result, AND)
        assert str(result) == str(AND(text="重要"))

    def test_body_prefix(self):
        """测试 body: 前缀"""
        result = _parse_search_query("body:报告")
        assert isinstance(result, AND)
        assert str(result) == str(AND(body="报告"))

    def test_prefix_case_insensitive(self):
        """测试前缀大小写不敏感"""
        result1 = _parse_search_query("SUBJECT:会议")
        result2 = _parse_search_query("Subject:会议")
        result3 = _parse_search_query("subject:会议")
        assert str(result1) == str(AND(subject="会议"))
        assert str(result2) == str(AND(subject="会议"))
        assert str(result3) == str(AND(subject="会议"))

    def test_prefix_with_spaces(self):
        """测试前缀和值带空格的情况"""
        result = _parse_search_query("subject: 会议通知 ")
        assert isinstance(result, AND)
        assert str(result) == str(AND(subject="会议通知"))

    def test_unknown_prefix(self):
        """测试未知前缀，应回退到默认搜索主题"""
        result = _parse_search_query("unknown:value")
        assert isinstance(result, AND)
        # 未知前缀应该回退到搜索整个查询字符串作为主题
        assert str(result) == str(AND(subject="unknown:value"))

    def test_empty_value_after_prefix(self):
        """测试前缀后无值的情况"""
        result = _parse_search_query("subject:")
        assert result == "ALL"

    def test_empty_value_after_prefix_with_spaces(self):
        """测试前缀后只有空格的情况"""
        result = _parse_search_query("subject:   ")
        assert result == "ALL"

    def test_colon_in_value(self):
        """测试值中包含冒号的情况"""
        result = _parse_search_query("subject:会议:通知")
        assert isinstance(result, AND)
        # 应该只分割第一个冒号
        assert str(result) == str(AND(subject="会议:通知"))

    def test_multiple_colons(self):
        """测试多个冒号的情况"""
        result = _parse_search_query("subject:http://example.com")
        assert isinstance(result, AND)
        # 应该只分割第一个冒号
        assert str(result) == str(AND(subject="http://example.com"))

    def test_whitespace_only(self):
        """测试只有空白字符的查询"""
        result = _parse_search_query("   ")
        assert isinstance(result, AND)
        # 空白字符会被 strip，然后作为主题搜索
        assert str(result) == str(AND(subject=""))

    def test_special_characters(self):
        """测试特殊字符"""
        result = _parse_search_query("subject:test@example.com")
        assert isinstance(result, AND)
        assert str(result) == str(AND(subject="test@example.com"))

    def test_unicode_characters(self):
        """测试 Unicode 字符"""
        result = _parse_search_query("subject:测试邮件")
        assert isinstance(result, AND)
        assert str(result) == str(AND(subject="测试邮件"))

    def test_from_prefix_with_unicode(self):
        """测试 from: 前缀包含 Unicode"""
        result = _parse_search_query("from:测试@qq.com")
        assert isinstance(result, AND)
        assert str(result) == str(AND(from_="测试@qq.com"))
