"""
用户上下文模块单元测试
"""
import pytest

from app.core.context import set_user_id, get_user_id, require_user_id


class TestContext:
    """测试用户上下文"""

    def test_set_and_get(self):
        """测试设置并获取 user_id"""
        set_user_id("user-abc")
        assert get_user_id() == "user-abc"

    def test_require_user_id_success(self):
        """测试 require_user_id 有值时返回"""
        set_user_id("user-xyz")
        assert require_user_id() == "user-xyz"

    def test_require_user_id_missing(self):
        """测试 require_user_id 缺失时抛异常"""
        # 通过新的 contextvars 上下文确保无值
        import contextvars
        ctx = contextvars.copy_context()

        def _run():
            from app.core.context import _user_id_var
            _user_id_var.set(None)
            require_user_id()

        with pytest.raises(ValueError, match="缺少 X-User-Id"):
            ctx.run(_run)
