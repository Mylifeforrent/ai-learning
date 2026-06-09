# 导入tkinter模块，用于创建GUI界面
import tkinter as tk
# 从tkinter模块中导入messagebox和scrolledtext，用于创建消息框和滚动文本框
from tkinter import messagebox, scrolledtext
# 导入paramiko模块，用于SSH连接
import paramiko

# SSH 连接参数
# 定义主机地址
HOST = "192.168.40.80"
# 定义用户名
USERNAME = "root"
# 定义密码
PASSWORD = "111111"
# 定义httpd服务名称
HTTPD_SERVICE = "httpd"
LOG_FILE_PATH = "/var/log/httpd/access_log"  # 根据实际情况修改日志路径

def create_ssh_client():
    """创建 SSH 客户端"""
    try:
        # 创建 SSH 客户端
        client = paramiko.SSHClient()
        # 设置自动添加主机密钥策略
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接到服务器
        client.connect(HOST, username=USERNAME, password=PASSWORD)
        # 返回 SSH 客户端
        return client
    except Exception as e:
        # 弹出错误提示框
        messagebox.showerror("错误", f"无法连接到服务器: {str(e)}")
        # 返回 None
        return None

def check_status():
    """检查 httpd 服务状态"""
    # 创建 ssh 客户端
    client = create_ssh_client()
    # 如果客户端创建成功
    if client:
        # 执行命令检查 httpd 服务状态
        stdin, stdout, stderr = client.exec_command(f"systemctl status {HTTPD_SERVICE}")
        # 读取命令输出
        output = stdout.read().decode()
        # 如果输出中包含 "running"，则表示服务正在运行
        if "running" in output:
            # 清空状态文本框
            status_text.delete(1.0, tk.END)
            # 插入 "运行中" 文本
            status_text.insert(tk.END, "运行中")
        else:
            # 清空状态文本框
            status_text.delete(1.0, tk.END)
            # 插入 "未运行" 文本
            status_text.insert(tk.END, "未运行")
        # 关闭 ssh 客户端
        client.close()

def start_service():
    """启动 httpd 服务"""
    # 创建 ssh 客户端
    client = create_ssh_client()
    # 如果客户端连接成功
    if client:
        # 执行启动 httpd 服务的命令
        client.exec_command(f"systemctl start {HTTPD_SERVICE}")
        # 弹出提示框，显示 httpd 服务已启动
        messagebox.showinfo("信息", "HTTPD 服务已启动")
        # 关闭 ssh 客户端连接
        client.close()

def stop_service():
    """停止 httpd 服务"""
    client = create_ssh_client()
    if client:
        client.exec_command(f"systemctl stop {HTTPD_SERVICE}")
        messagebox.showinfo("信息", "HTTPD 服务已停止")
        client.close()

def view_log():
    """查看 httpd 服务日志"""
    # 创建 ssh 客户端
    client = create_ssh_client()
    # 如果客户端创建成功
    if client:
        # 执行命令，查看 httpd 服务日志
        stdin, stdout, stderr = client.exec_command(f"cat {LOG_FILE_PATH}")
        # 读取日志内容
        log_content = stdout.read().decode()
        # 创建一个新的窗口
        log_window = tk.Toplevel(root)
        # 设置窗口标题
        log_window.title("HTTPD 服务日志")
        # 创建一个滚动文本框
        log_text = scrolledtext.ScrolledText(log_window, height=20, width=80)
        # 将滚动文本框添加到窗口中
        log_text.pack()
        # 将日志内容插入到滚动文本框中
        log_text.insert(tk.END, log_content)
        # 关闭 ssh 客户端
        client.close()


# 创建主窗口
root = tk.Tk()
# 设置窗口标题
root.title("HTTPD 服务管理工具")

# 创建一个标签，用于显示HTTPD服务状态
status_label = tk.Label(root, text="HTTPD 服务状态:")
# 将标签放置在窗口中
status_label.pack()

# 创建一个文本框，用于显示HTTPD服务状态
status_text = tk.Text(root, height=1, width=30)
# 将文本框放置在窗口中
status_text.pack()

# 创建一个按钮，用于查看HTTPD服务状态
check_status_button = tk.Button(root, text="查看状态", command=check_status)
# 将按钮放置在窗口中
check_status_button.pack()

# 创建一个按钮，用于启动HTTPD服务
start_button = tk.Button(root, text="启动服务", command=start_service)
# 将按钮放置在窗口中
start_button.pack()

# 创建一个按钮，用于停止HTTPD服务
stop_button = tk.Button(root, text="停止服务", command=stop_service)
# 将按钮放置在窗口中
stop_button.pack()

# 创建一个按钮，用于查看HTTPD服务日志
log_button = tk.Button(root, text="查看日志", command=view_log)
# 将按钮放置在窗口中
log_button.pack()

# 进入主循环，等待用户操作
root.mainloop()

