"""
邮件工具单元测试
使用 mock 替代实际邮件服务调用
"""
import contextvars

import pytest
from unittest.mock import patch, AsyncMock

from app.core.context import set_user_id
from app.services.user_store import EmailAccount


class TestMailTools:
    """测试邮件 MCP 工具"""

    @pytest.mark.asyncio
    async def test_get_mail_list_success(self):
        """测试获取邮件列表成功"""
        set_user_id("user1")
        mock_account = EmailAccount(email="test@qq.com", passkey="pass123")
        mock_mails = [
            {"uid": "1", "subject": "Test", "from": "a@b.com", "to": ["test@qq.com"],
             "date": "2025-01-01", "seen": False}
        ]

        with patch("app.tools.mail.user_store") as mock_store, \
             patch("app.tools.mail.imap_service") as mock_imap:
            mock_store.validate_access.return_value = mock_account
            mock_imap.fetch_mail_list = AsyncMock(return_value=mock_mails)

            from app.tools.mail import get_mail_list
            result = await get_mail_list(email="test@qq.com")

            assert result["total"] == 1
            assert result["mails"][0]["subject"] == "Test"
            mock_store.validate_access.assert_called_once_with("user1", "test@qq.com")

    @pytest.mark.asyncio
    async def test_get_mail_detail_success(self):
        """测试获取邮件详情成功"""
        set_user_id("user1")
        mock_account = EmailAccount(email="test@qq.com", passkey="pass123")
        mock_detail = {
            "uid": "1", "subject": "Test", "from": "a@b.com",
            "to": ["test@qq.com"], "cc": [], "date": "2025-01-01",
            "text_body": "hello", "html_body": "", "attachments": [],
        }

        with patch("app.tools.mail.user_store") as mock_store, \
             patch("app.tools.mail.imap_service") as mock_imap:
            mock_store.validate_access.return_value = mock_account
            mock_imap.fetch_mail_detail = AsyncMock(return_value=mock_detail)

            from app.tools.mail import get_mail_detail
            result = await get_mail_detail(email="test@qq.com", mail_uid="1")

            assert result["subject"] == "Test"
            assert result["text_body"] == "hello"

    @pytest.mark.asyncio
    async def test_get_mail_detail_not_found(self):
        """测试邮件详情未找到"""
        set_user_id("user1")
        mock_account = EmailAccount(email="test@qq.com", passkey="pass123")

        with patch("app.tools.mail.user_store") as mock_store, \
             patch("app.tools.mail.imap_service") as mock_imap:
            mock_store.validate_access.return_value = mock_account
            mock_imap.fetch_mail_detail = AsyncMock(return_value=None)

            from app.tools.mail import get_mail_detail
            result = await get_mail_detail(email="test@qq.com", mail_uid="999")

            assert "error" in result

    @pytest.mark.asyncio
    async def test_send_email_success(self):
        """测试发送邮件成功"""
        set_user_id("user1")
        mock_account = EmailAccount(email="test@qq.com", passkey="pass123")
        mock_result = {
            "success": True, "from": "test@qq.com",
            "to": "recv@163.com", "subject": "Hi",
        }

        with patch("app.tools.mail.user_store") as mock_store, \
             patch("app.tools.mail.smtp_service") as mock_smtp:
            mock_store.validate_access.return_value = mock_account
            mock_smtp.send_email = AsyncMock(return_value=mock_result)

            from app.tools.mail import send_mail
            result = await send_mail(
                from_email="test@qq.com",
                to_email="recv@163.com",
                subject="Hi",
                body="Hello!",
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_tool_requires_user_id(self):
        """测试缺少 user_id 时抛异常"""
        ctx = contextvars.copy_context()

        async def _run():
            from app.core.context import _user_id_var
            _user_id_var.set(None)
            from app.tools.mail import get_mail_list
            await get_mail_list(email="test@qq.com")

        with pytest.raises(ValueError, match="缺少 X-User-Id"):
            await ctx.run(_run)

    @pytest.mark.asyncio
    async def test_tool_validates_access(self):
        """测试未注册邮箱时抛权限异常"""
        set_user_id("user1")

        with patch("app.tools.mail.user_store") as mock_store:
            mock_store.validate_access.side_effect = PermissionError("未注册邮箱")

            from app.tools.mail import get_mail_list
            with pytest.raises(PermissionError, match="未注册邮箱"):
                await get_mail_list(email="not-registered@qq.com")
