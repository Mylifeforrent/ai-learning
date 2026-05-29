"""
邮箱提供商配置单元测试
"""
import pytest

from app.services.email_providers import get_provider_config, PROVIDER_MAP


class TestEmailProviders:
    """测试邮箱提供商配置"""

    def test_qq_provider(self):
        """测试 QQ 邮箱配置"""
        config = get_provider_config("user@qq.com")
        assert config.imap_host == "imap.qq.com"
        assert config.imap_port == 993
        assert config.smtp_host == "smtp.qq.com"
        assert config.smtp_port == 465
        assert config.smtp_use_tls is True

    def test_163_provider(self):
        """测试 163 邮箱配置"""
        config = get_provider_config("user@163.com")
        assert config.imap_host == "imap.163.com"
        assert config.smtp_host == "smtp.163.com"

    def test_sina_com_provider(self):
        """测试 sina.com 邮箱配置"""
        config = get_provider_config("user@sina.com")
        assert config.imap_host == "imap.sina.com"

    def test_sina_cn_provider(self):
        """测试 sina.cn 邮箱配置"""
        config = get_provider_config("user@sina.cn")
        assert config.imap_host == "imap.sina.com"

    def test_unsupported_domain(self):
        """测试不支持的邮箱域名"""
        with pytest.raises(ValueError, match="不支持的邮箱域名"):
            get_provider_config("user@gmail.com")

    def test_invalid_email(self):
        """测试无效的邮箱地址"""
        with pytest.raises(ValueError, match="无效的邮箱地址"):
            get_provider_config("not-an-email")

    def test_case_insensitive(self):
        """测试域名不区分大小写"""
        config = get_provider_config("user@QQ.COM")
        assert config.imap_host == "imap.qq.com"
