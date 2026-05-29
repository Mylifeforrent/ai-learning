## MCP 工具说明文档（m2l10）

本文件整理了当前 MCP 环境中可用的所有工具，包含：

- **工具名（name）**
- **英文原始描述（Original Description）**
- **中文说明**
- **主要入参（参数说明）**

> 说明：以下内容全部根据 MCP 返回的 `tools` 列表整理而来，仅描述接口含义，不涉及具体业务逻辑。

---

### 1. `sandbox_get_browser_info`

- **Original Description**

  Get information about browser, like cdp url, viewport size, etc.

      Args:
          request (Dict): The incoming request context.

- **中文说明**

  获取浏览器相关信息，例如 CDP URL、视口大小等。  
  不需要额外参数，通常返回当前浏览器会话的环境信息，用于后续浏览器相关操作的基础信息。

- **参数**

  - 无参数（`inputSchema` 中 `properties` 为空对象）。

---

### 2. `sandbox_browser_screenshot`

- **Original Description**

  Take a screenshot of the current display.

      Returns:
          Image: A screenshot of the current display in JPEG format with metadata.

- **中文说明**

  对当前显示内容进行截图，返回一张带有元数据的 JPEG 图片。一般用于可视化记录或配合视觉模型分析当前画面。

- **参数**

  - 无参数。

---

### 3. `sandbox_browser_execute_action`

- **Original Description**

  Execute a browser action on the current display.

  Args:
      `action`: Dictionary containing `action_type` and relevant parameters.
              The `action_type` determines which parameters are required.

  Action types and their parameters (auto-generated from models):
      - CLICK: {action_type: 'CLICK', x: Optional?, y: Optional?, button: Literal?, num_clicks: Literal?}
      - DOUBLE_CLICK: {action_type: 'DOUBLE_CLICK', x: Optional?, y: Optional?}
      - DRAG_REL: {action_type: 'DRAG_REL', x_offset: float, y_offset: float}
      - DRAG_TO: {action_type: 'DRAG_TO', x: float, y: float}
      - HOTKEY: {action_type: 'HOTKEY', keys: List}
      - KEY_DOWN: {action_type: 'KEY_DOWN', key: str}
      - KEY_UP: {action_type: 'KEY_UP', key: str}
      - MOUSE_DOWN: {action_type: 'MOUSE_DOWN', button: Literal?}
      - MOUSE_UP: {action_type: 'MOUSE_UP', button: Literal?}
      - MOVE_REL: {action_type: 'MOVE_REL', x_offset: float, y_offset: float}
      - MOVE_TO: {action_type: 'MOVE_TO', x: float, y: float}
      - PRESS: {action_type: 'PRESS', key: str}
      - RIGHT_CLICK: {action_type: 'RIGHT_CLICK', x: Optional?, y: Optional?}
      - SCROLL: {action_type: 'SCROLL', dx: int?, dy: int?}
      - TYPING: {action_type: 'TYPING', text: str, use_clipboard: Optional?}
      - WAIT: {action_type: 'WAIT', duration: float}

  Returns:
      Dict containing `status` and `action_performed`

  Raises:
      ValueError: If `action_type` is invalid or required parameters are missing

- **中文说明**

  在当前显示的页面上执行浏览器动作。  
  通过传入 `action` 字典，指定 `action_type` 和对应的参数，实现点击、双击、拖拽、键盘输入、滚动等多种操作。  
  返回值包含执行状态和已执行动作的详细信息；如果 `action_type` 非法或缺少必需参数会抛出错误。

- **参数**

  - **`action`**（必填，`object`）：  
    - 必须包含字段 `action_type`（字符串，枚举为 CLICK / DOUBLE_CLICK / DRAG_REL / DRAG_TO / HOTKEY / KEY_DOWN / KEY_UP / MOUSE_DOWN / MOUSE_UP / MOVE_REL / MOVE_TO / PRESS / RIGHT_CLICK / SCROLL / TYPING / WAIT）。  
    - 其余字段依赖于 `action_type`，常见参数：
      - 坐标类：`x`, `y`, `x_offset`, `y_offset`
      - 鼠标：`button`, `num_clicks`
      - 键盘：`key`, `keys`
      - 文本输入：`text`, `use_clipboard`
      - 滚动：`dx`, `dy`
      - 等待：`duration`

---

### 4. `sandbox_execute_code`

- **Original Description**

  Execute code in Python or JavaScript runtime.

      Args:
          code: Code to execute
          language: Programming language ('python', 'javascript')
          timeout: Optional execution timeout in seconds

      Returns:
          Dict containing output, errors, and execution details

- **中文说明**

  在沙箱环境中执行一段 Python 或 JavaScript 代码，可选设置超时时间。  
  返回包含标准输出、错误输出以及执行细节的字典。

- **参数**

  - **`code`**（必填，`string`）：要执行的代码文本。
  - **`language`**（可选，`string`，枚举：`python` / `javascript`，默认：`python`）：指定运行语言。
  - **`timeout`**（可选，`integer | null`，默认：`null`）：执行超时时间（秒）。

---

### 5. `sandbox_file_operations`

- **Original Description**

  Unified file system operations tool for agents. `/tmp` and `/home/$USER` are fully accessible.

      Args:
          action: Operation type - "read", "write", "replace", "search", "find", "list"
          path: File or directory path
          content: Content for write/replace operations (or regex for search)
          target: Target string for replace operations (new_str)
          pattern: Pattern for find operations (glob syntax)
          encoding: File encoding (utf-8, base64, raw)
          start_line: Starting line for read operations (0-based)
          end_line: Ending line for read operations (not included)
          append: Append mode for write operations
          recursive: Recursive mode for find/list operations
          show_hidden: Show hidden files in list operations
          file_types: Filter by file extensions for list operations
          sudo: Use sudo privileges

      Returns:
          Dict containing operation result and relevant data

- **中文说明**

  统一的文件系统操作工具，支持在沙箱内对 `/tmp` 和 `/home/$USER` 等路径进行读写、搜索、查找和列出等操作。  
  可执行 `read`、`write`、`replace`、`search`、`find`、`list` 六类子操作。

- **参数**

  - **`action`**（必填，`string`）：操作类型，取值：
    - `"read"`：读取文件
    - `"write"`：写入文件
    - `"replace"`：字符串替换
    - `"search"`：内容搜索（正则）
    - `"find"`：按模式查找文件
    - `"list"`：列出目录内容
  - **`path`**（必填，`string`）：文件或目录路径。
  - **`content`**（可选，`string | null`，默认：`null`）：  
    - `write` / `replace` 时为写入内容；  
    - `search` 时为正则表达式。
  - **`target`**（可选，`string | null`，默认：`null`）：`replace` 操作中的新字符串。
  - **`pattern`**（可选，`string | null`，默认：`null`）：`find` 操作使用的 glob 模式。
  - **`encoding`**（可选，`string | null`，默认：`utf-8`）：文件编码，可为 `utf-8`、`base64`、`raw` 等。
  - **`start_line`**（可选，`integer | null`，默认：`null`）：`read` 时的起始行（0 基）。
  - **`end_line`**（可选，`integer | null`，默认：`null`）：`read` 时的结束行（不包含）。
  - **`append`**（可选，`boolean`，默认：`false`）：`write` 时是否追加写入。
  - **`recursive`**（可选，`boolean`，默认：`false`）：`find` / `list` 时是否递归。
  - **`show_hidden`**（可选，`boolean`，默认：`false`）：`list` 时是否显示隐藏文件。
  - **`file_types`**（可选，`string[] | null`，默认：`null`）：限制列出或查找的文件扩展名列表。
  - **`sudo`**（可选，`boolean`，默认：`false`）：是否使用 sudo 权限（视沙箱策略而定）。

---

### 6. `sandbox_str_replace_editor`

- **Original Description**

  Professional file editor tool using openhands_aci editor.

      This tool provides advanced file editing capabilities compatible with Anthropic's
      str_replace_editor interface. Parameters and behavior match the standard interface.

      Args:
          command: Command to execute ("view", "create", "str_replace", "insert", "undo_edit")
          path: File path to operate on
          file_text: File content for create command
          old_str: Original string to replace (for str_replace command)
          new_str: New string to replace with (for str_replace and insert commands)
          insert_line: Line number to insert at (for insert command)
          view_range: Line range for view command [start, end]

      Returns:
          Dict containing editor operation result

- **中文说明**

  基于 `openhands_aci` 编辑器的专业文件编辑工具，实现了与 Anthropic `str_replace_editor` 接口兼容的行为。  
  支持查看、创建、字符串替换、插入、撤销编辑等操作。

- **参数**

  - **`command`**（必填，`string`）：编辑命令，允许值：
    - `"view"`：查看文件指定范围内容
    - `"create"`：创建新文件
    - `"str_replace"`：按字符串替换
    - `"insert"`：在指定行插入内容
    - `"undo_edit"`：撤销最近一次编辑
  - **`path`**（必填，`string`）：目标文件路径。
  - **`file_text`**（可选，`string | null`）：  
    - `create` 时：新文件的全部内容。
  - **`old_str`**（可选，`string | null`）：  
    - `str_replace` 时：要被替换的原字符串。
  - **`new_str`**（可选，`string | null`）：  
    - `str_replace`、`insert` 时：新字符串内容。
  - **`insert_line`**（可选，`integer | null`）：  
    - `insert` 时：插入的目标行号。
  - **`view_range`**（可选，`integer[] | null`）：  
    - `view` 时：查看范围 `[start, end]` 行。

---

### 7. `sandbox_get_context`

- **Original Description**

  Get sandbox environment information. aio system's version.

      Returns:
          Dict containing aio sandbox's environment info, version, and home directory

- **中文说明**

  获取沙箱环境的整体信息，包括 AIO 系统版本、环境信息、home 目录等。

- **参数**

  - 无参数。

---

### 8. `sandbox_get_packages`

- **Original Description**

  Get installed packages by language.

      Args:
          language: Optional language filter ('python' or 'nodejs')

      Returns: String listing installed packages

- **中文说明**

  按语言列出当前沙箱中已安装的依赖包，可用于诊断依赖环境。  

- **参数**

  - **`language`**（可选，`string`，枚举：`python`, `nodejs`，默认：`null`）：  
    - 不传或为 `null` 时可由实现决定返回所有或默认语言的包；  
    - 指定时仅列出对应语言的包。

---

### 9. `sandbox_execute_bash`

- **Original Description**

  Execute a shell command. Sessions are managed automatically.

      Args:
          cmd: Shell command to execute
          cwd: Optional working directory (absolute path), default to '/tmp'
          new_session: If True, creates a new session instead of using the default
          timeout: Optional timeout in seconds for command execution (default: 30)

      Returns:
          Dict containing command, status, output, and exit_code

- **中文说明**

  在沙箱中执行一条 Shell 命令，会自动管理会话（如复用或新建）。  
  可指定工作目录、是否新建会话以及超时时间，返回包括命令、状态、输出和退出码等信息。

- **参数**

  - **`cmd`**（必填，`string`）：要执行的 Shell 命令。
  - **`cwd`**（可选，`string | null`，默认：`null`）：工作目录（绝对路径），默认使用 `/tmp`。
  - **`new_session`**（可选，`boolean`，默认：`false`）：是否新建会话。
  - **`timeout`**（可选，`integer | null`，默认：`30`）：执行超时时间（秒）。

---

### 10. `sandbox_convert_to_markdown`

- **Original Description**

  Convert a resource described by an http:, https:, file: or data: URI to markdown

- **中文说明**

  将一个由 `http: / https: / file: / data:` URI 描述的资源转换为 Markdown 文本。  
  常用于网页内容或本地文件内容的提取与标准化展示。

- **参数**

  - **`uri`**（必填，`string`）：资源的 URI。

---

### 11. `browser_navigate`

- **Original Description**

  Navigate to a URL

- **中文说明**

  在浏览器中跳转到指定 URL，等价于在地址栏输入链接并访问。

- **参数**

  - **`url`**（必填，`string`）：目标网页的 URL。

---

### 12. `browser_go_back`

- **Original Description**

  Go back to the previous page

- **中文说明**

  在浏览器中后退到上一个页面，相当于点击浏览器“后退”按钮。

- **参数**

  - 无参数。

---

### 13. `browser_go_forward`

- **Original Description**

  Go forward to the next page

- **中文说明**

  在浏览器中前进到下一个页面，相当于点击浏览器“前进”按钮。

- **参数**

  - 无参数。

---

### 14. `browser_form_input_fill`

- **Original Description**

  Fill out an input field, before using the tool, Either 'index' or 'selector' must be provided

- **中文说明**

  向页面上的某个输入框填充值。  
  在调用该工具时，必须通过 `index`（元素索引）或 `selector`（CSS 选择器）定位到具体输入框。

- **参数**

  - **`value`**（必填，`string`）：要填入的文本内容。
  - **`index`**（可选，`number`）：目标输入元素在内部列表中的索引，优先使用。
  - **`selector`**（可选，`string`）：目标输入元素的 CSS 选择器（当未提供 `index` 时使用）。
  - **`clear`**（可选，`boolean`，默认：`false`）：在填充前是否清空已有文本。

---

### 15. `browser_get_markdown`

- **Original Description**

  Get the markdown content of the current page

- **中文说明**

  将当前页面内容转换为 Markdown 文本并返回，适合做结构化抽取或作为上下文输入给 LLM。

- **参数**

  - 无参数。

---

### 16. `browser_get_text`

- **Original Description**

  Get the text content of the current page

- **中文说明**

  获取当前页面的纯文本内容（去除 HTML 标签），用于文本分析或搜索。

- **参数**

  - 无参数。

---

### 17. `browser_read_links`

- **Original Description**

  Get all links on the current page

- **中文说明**

  读取当前页面中的所有链接，返回包含链接文字和 `href` 地址的列表。

- **参数**

  - 无参数。

- **输出结构（简要）**

  - `links`：数组，每个元素包含：
    - `text`：链接文本
    - `href`：链接地址

---

### 18. `browser_new_tab`

- **Original Description**

  Open a new tab

- **中文说明**

  在浏览器中新开一个标签页，并访问指定 URL。

- **参数**

  - **`url`**（必填，`string`）：新标签页中要打开的 URL。

---

### 19. `browser_tab_list`

- **Original Description**

  Get the list of tabs

- **中文说明**

  获取当前浏览器中所有标签页的信息列表，包含索引、是否激活、标题和 URL。

- **参数**

  - 无参数。

- **输出结构（简要）**

  - `tabList`：数组，每个元素包含：
    - `index`：标签页索引
    - `active`：是否为当前激活标签
    - `title`：页面标题
    - `url`：页面 URL

---

### 20. `browser_switch_tab`

- **Original Description**

  Switch to a specific tab

- **中文说明**

  切换当前浏览器激活标签页到指定索引对应的标签。

- **参数**

  - **`index`**（必填，`number`）：要切换到的标签页索引。

---

### 21. `browser_close_tab`

- **Original Description**

  Close the current tab

- **中文说明**

  关闭当前激活的浏览器标签页。

- **参数**

  - 无参数。

---

### 22. `browser_evaluate`

- **Original Description**

  Execute JavaScript in the browser console

- **中文说明**

  在浏览器页面上下文中执行一段 JavaScript 代码，相当于在开发者工具 Console 中运行脚本。

- **参数**

  - **`script`**（必填，`string`）：要执行的 JavaScript 代码，通常形式为 `() => { /* code */ }`。

---

### 23. `browser_vision_screen_capture`

- **Original Description**

  Take a screenshot of the current page for vision mode

- **中文说明**

  为“视觉模式”截取当前页面的屏幕图像，用于视觉模型识别或进一步点击操作的定位。

- **参数**

  - 无参数。

---

### 24. `browser_vision_screen_click`

- **Original Description**

  Click left mouse button on the page with vision and snapshot, before calling this tool, you should call `browser_vision_screen_capture` first only once, fallback to `browser_click` if failed

- **中文说明**

  基于视觉截图坐标，在页面上执行一次**左键点击**。  
  使用前应先调用一次 `browser_vision_screen_capture` 获取最新画面；如失败可回退到 `browser_click`。

- **参数**

  - **`x`**（必填，`number`）：点击位置的 X 像素坐标。
  - **`y`**（必填，`number`）：点击位置的 Y 像素坐标。
  - **`factors`**（可选，`number[]`）：视觉模型坐标缩放因子 `[width_factor, height_factor]`。  
    一般模型无需此参数，不确定时可留空。

---

### 25. `browser_get_download_list`

- **Original Description**

  Get the list of downloaded files

- **中文说明**

  获取浏览器中的下载文件列表，包含下载状态、URL、文件名和本地资源路径等信息。

- **参数**

  - 无参数。

- **输出结构（简要）**

  - `list`：数组，每个元素包含：
    - `guid`：下载任务唯一 ID
    - `url`：下载来源 URL
    - `suggestedFilename`：建议文件名
    - `resourceUri`：本地资源 URI
    - `createdAt`：创建时间
    - `progress`：进度（数值）
    - `state`：当前状态

---

### 26. `browser_screenshot`

- **Original Description**

  Take a screenshot of the current page or a specific element

- **中文说明**

  对当前页面或指定元素进行截图，可控制范围尺寸，支持整页截图和高亮指定元素。

- **参数**

  - **`name`**（可选，`string`）：截图名称，用于标识。
  - **`selector`**（可选，`string`）：目标元素的 CSS 选择器。
  - **`index`**（可选，`number`）：元素索引，用于在一组匹配元素中选择其一。
  - **`width`**（可选，`number`）：截图宽度（像素），默认视口宽度。
  - **`height`**（可选，`number`）：截图高度（像素），默认视口高度。
  - **`fullPage`**（可选，`boolean`）：是否整页截图（默认 `false`）。
  - **`highlight`**（可选，`boolean`，默认：`false`）：是否高亮目标元素。

---

### 27. `browser_click`

- **Original Description**

  Click an element on the page, before using the tool, use `browser_get_clickable_elements` to get the index of the element, but not call `browser_get_clickable_elements` multiple times

- **中文说明**

  点击页面上的某个可点击元素。  
  调用前推荐先使用 `browser_get_clickable_elements` 获取元素列表及索引（避免多次重复调用该列表接口）。

- **参数**

  - **`index`**（必填，`number`）：要点击的元素在可点击元素列表中的索引。

---

### 28. `browser_select`

- **Original Description**

  Select an element on the page with index, Either 'index' or 'selector' must be provided

- **中文说明**

  为页面上的某个下拉框或可选元素设置选中值。  
  通过 `index` 或 `selector` 定位元素，然后将其设置为指定的 `value`。

- **参数**

  - **`value`**（必填，`string`）：要选择的值（通常是选项的 `value` 属性）。
  - **`index`**（可选，`number`）：目标元素索引。
  - **`selector`**（可选，`string`）：目标元素 CSS 选择器。

---

### 29. `browser_hover`

- **Original Description**

  Hover an element on the page, Either 'index' or 'selector' must be provided

- **中文说明**

  将鼠标悬停在页面上的某个元素上，常用于触发悬浮菜单、提示气泡等 hover 行为。

- **参数**

  - **`index`**（可选，`number`）：目标元素索引。
  - **`selector`**（可选，`string`）：目标元素 CSS 选择器。

---

### 30. `browser_get_clickable_elements`

- **Original Description**

  Get the clickable or hoverable or selectable elements on the current page, don't call this tool multiple times

- **中文说明**

  获取当前页面上所有可点击、可悬停、可选择的元素列表。  
  该列表通常用于后续 `browser_click`、`browser_hover`、`browser_select` 等操作中的 `index` 参数。  
  出于性能考虑，不建议在同一任务中多次调用。

- **参数**

  - 无参数。

---

### 31. `browser_scroll`

- **Original Description**

  Scroll the page

- **中文说明**

  控制页面滚动，可以指定滚动像素值；若未指定则通常滚动到底部。

- **参数**

  - **`amount`**（可选，`number`）：滚动像素值（正数向下、负数向上）。未提供时，默认行为是滚动到底部（具体由实现决定）。

---

### 32. `browser_close`

- **Original Description**

  Close the browser when the task is done and the browser is not needed anymore

- **中文说明**

  在任务完成且不再需要浏览器时，关闭整个浏览器会话，释放资源。

- **参数**

  - 无参数。

---

### 33. `browser_press_key`

- **Original Description**

  Press a key on the keyboard

- **中文说明**

  在浏览器环境中模拟按下某个键盘按键，可用于触发快捷键或页面行为，如 Enter、Tab、方向键等。

- **参数**

  - **`key`**（必填，`string`，枚举）：  
    可选值较多，包括功能键和控制键，例如：
    - `Enter`, `Tab`, `Escape`, `Backspace`, `Delete`, `Insert`
    - `F1` ~ `F12`
    - `ArrowLeft`, `ArrowRight`, `ArrowUp`, `ArrowDown`
    - `PageUp`, `PageDown`, `Home`, `End`
    - `ShiftLeft`, `ShiftRight`, `ControlLeft`, `ControlRight`
    - `AltLeft`, `AltRight`, `MetaLeft`, `MetaRight`
    - `CapsLock`, `PrintScreen`, `ScrollLock`, `Pause`, `ContextMenu`

---

以上即为 MCP 响应中列出的所有工具的**英文原文描述**与**中文说明**整理，可直接作为 `m2l10` 任务中使用 MCP 工具的参考文档。

