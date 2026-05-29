# Python __all__ 导出列表说明

## 项目里的代码

`src/app/api/dependencies.py` 末尾有这样一行：

```python
__all__ = ["require_api_key", "get_request_id"]
```

这行代码的作用是声明：

```text
这个模块对外推荐公开使用的名字是 require_api_key 和 get_request_id。
```

## __all__ 是什么

`__all__` 是 Python 模块里的一个特殊变量。

它通常是一个字符串列表，用来表示：

```text
当别人从这个模块里批量导入内容时，哪些名字应该被导出。
```

例如：

```python
__all__ = ["require_api_key", "get_request_id"]
```

表示这个模块公开导出的名字只有：

```text
require_api_key
get_request_id
```

## 它主要影响 from module import *

`__all__` 最典型的影响是控制这种写法：

```python
from app.api.dependencies import *
```

如果模块中定义了：

```python
__all__ = ["require_api_key", "get_request_id"]
```

那么上面的 `import *` 只会导入：

```python
require_api_key
get_request_id
```

不会导入模块里的其他名字，例如：

```python
uuid4
Request
set_request_id
verify_api_key
```

也就是说，`__all__` 像是在告诉 Python：

```text
如果有人使用 import *，只把这些名字暴露出去。
```

## 不会阻止显式导入

`__all__` 不是访问权限控制，也不是私有变量机制。

即使某个名字没有写进 `__all__`，依然可以被显式导入。

例如：

```python
from app.api.dependencies import require_api_key
from app.api.dependencies import get_request_id
```

这种写法不会受影响。

甚至如果你知道模块里有其他名字，也可以显式导入：

```python
from app.api.dependencies import verify_api_key
```

前提是这个名字确实存在于模块命名空间中。

所以 `__all__` 更像是：

```text
模块作者给外部使用者的一份公开 API 清单。
```

而不是强制禁止访问其他变量。

## 如果没有 __all__ 会怎样

如果模块里没有定义 `__all__`，Python 遇到：

```python
from module import *
```

时，默认会导入模块中所有“不以下划线开头”的名字。

例如：

```python
name = "demo"
_private_name = "hidden"
```

没有 `__all__` 时：

```python
from module import *
```

通常会导入 `name`，不会导入 `_private_name`。

但如果定义了 `__all__`，Python 就以 `__all__` 为准。

## 在这个项目里的意义

`src/app/api/dependencies.py` 中有：

```python
from uuid import uuid4

from fastapi import Request

from app.core.security import verify_api_key
from app.observability.logging import set_request_id

require_api_key = verify_api_key


async def get_request_id(request: Request) -> str:
    ...


__all__ = ["require_api_key", "get_request_id"]
```

这个模块内部需要用到：

```text
uuid4
Request
verify_api_key
set_request_id
```

但它真正想对外暴露的是：

```text
require_api_key
get_request_id
```

所以用 `__all__` 表达模块边界：

```text
外部代码主要应该从这里拿 require_api_key 和 get_request_id，
其他名字只是这个模块内部实现细节。
```

## 小结

```python
__all__ = ["require_api_key", "get_request_id"]
```

可以理解为：

```text
这个模块的公开导出列表。
```

它的主要作用是：

```text
1. 控制 from module import * 会导入哪些名字。
2. 表达模块作者希望外部使用哪些公共 API。
3. 避免内部实现细节被批量导入出去。
```

但它不会阻止显式导入，也不是真正的访问权限控制。
