"""
加密用户存储单元测试
"""
import os
import tempfile

import pytest
from cryptography.fernet import Fernet

from app.services.user_store import UserStore


@pytest.fixture
def fernet_key():
    return Fernet.generate_key().decode()


@pytest.fixture
async def store(fernet_key, monkeypatch):
    """创建一个使用临时文件的 UserStore 实例。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = os.path.join(tmpdir, "test_users.enc")
        monkeypatch.setenv("USER_STORE_ENCRYPTION_KEY", fernet_key)
        monkeypatch.setenv("USER_STORE_PATH", store_path)

        from app.core.config import get_settings
        get_settings.cache_clear()

        s = UserStore()
        await s.initialize()
        yield s

        get_settings.cache_clear()


class TestUserStore:
    """测试用户存储"""

    @pytest.mark.asyncio
    async def test_register_and_get(self, store):
        """测试注册后可获取账号"""
        await store.register_account("user1", "test@qq.com", "pass123")
        account = store.get_account("user1", "test@qq.com")
        assert account is not None
        assert account.email == "test@qq.com"
        assert account.passkey == "pass123"

    @pytest.mark.asyncio
    async def test_register_update_passkey(self, store):
        """测试重复注册更新 passkey"""
        await store.register_account("user1", "test@qq.com", "old_pass")
        await store.register_account("user1", "test@qq.com", "new_pass")
        account = store.get_account("user1", "test@qq.com")
        assert account.passkey == "new_pass"

    @pytest.mark.asyncio
    async def test_remove_account(self, store):
        """测试移除账号"""
        await store.register_account("user1", "test@qq.com", "pass123")
        removed = await store.remove_account("user1", "test@qq.com")
        assert removed is True
        assert store.get_account("user1", "test@qq.com") is None

    @pytest.mark.asyncio
    async def test_remove_nonexistent(self, store):
        """测试移除不存在的账号"""
        removed = await store.remove_account("user1", "no@qq.com")
        assert removed is False

    @pytest.mark.asyncio
    async def test_validate_access_success(self, store):
        """测试权限校验成功"""
        await store.register_account("user1", "test@qq.com", "pass123")
        account = store.validate_access("user1", "test@qq.com")
        assert account.email == "test@qq.com"

    @pytest.mark.asyncio
    async def test_validate_access_failure(self, store):
        """测试权限校验失败"""
        with pytest.raises(PermissionError, match="未注册邮箱"):
            store.validate_access("user1", "no@qq.com")

    @pytest.mark.asyncio
    async def test_list_accounts(self, store):
        """测试列出用户邮箱"""
        await store.register_account("user1", "a@qq.com", "p1")
        await store.register_account("user1", "b@163.com", "p2")
        accounts = store.list_accounts("user1")
        assert set(accounts) == {"a@qq.com", "b@163.com"}

    @pytest.mark.asyncio
    async def test_list_accounts_empty(self, store):
        """测试空用户的邮箱列表"""
        accounts = store.list_accounts("nobody")
        assert accounts == []

    @pytest.mark.asyncio
    async def test_persistence(self, fernet_key, monkeypatch):
        """测试数据持久化：重新加载后数据仍在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = os.path.join(tmpdir, "persist.enc")
            monkeypatch.setenv("USER_STORE_ENCRYPTION_KEY", fernet_key)
            monkeypatch.setenv("USER_STORE_PATH", store_path)

            from app.core.config import get_settings
            get_settings.cache_clear()

            s1 = UserStore()
            await s1.initialize()
            await s1.register_account("user1", "test@qq.com", "pass123")

            # 新实例重新加载
            s2 = UserStore()
            await s2.initialize()
            account = s2.get_account("user1", "test@qq.com")
            assert account is not None
            assert account.passkey == "pass123"

            get_settings.cache_clear()
