# 导入tkinter模块，用于创建图形用户界面
import tkinter as tk
# 从tkinter模块中导入scrolledtext和messagebox模块，用于创建滚动文本框和消息框
from tkinter import scrolledtext, messagebox
# 导入paramiko模块，用于SSH连接
import paramiko

# 远程服务器的连接信息
HOST = '192.168.40.80'  # 远程服务器的IP地址
USERNAME = 'root'       # SSH登录的用户名
PASSWORD = '111111'     # SSH登录的密码

# Tomcat相关操作命令
TOMCAT_START_CMD = "/opt/tomcat/bin/catalina.sh start"  # 启动Tomcat的命令
TOMCAT_STOP_CMD = "/opt/tomcat/bin/catalina.sh stop"    # 停止Tomcat的命令
TOMCAT_STATUS_CMD = "ps -ef | grep tomcat | grep -v grep"  # 检查Tomcat运行状态的命令

# 连接到远程服务器
# 定义一个连接SSH的函数
def connect_ssh():
    # 尝试连接SSH
    try:
        # 创建一个SSH客户端
        client = paramiko.SSHClient()
        # 设置自动添加主机密钥策略
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接SSH服务器
        client.connect(HOST, username=USERNAME, password=PASSWORD)
        # 返回SSH客户端
        return client
    # 捕获异常
    except Exception as e:
        # 在日志中插入连接失败的提示信息
        log_text.insert(tk.END, f"连接失败: {str(e)}\n")
        # 返回None
        return None

# 启动 Tomcat 服务
def start_tomcat():
    # 连接SSH
    client = connect_ssh()
    # 如果连接成功
    if client:
        try:
            # 执行启动Tomcat的命令
            stdin, stdout, stderr = client.exec_command(TOMCAT_START_CMD)
            # 读取错误信息
            error = stderr.read().decode()
            # 如果有错误信息
            if error:
                # 在日志框中插入错误信息
                log_text.insert(tk.END, f"启动失败: {error}\n")
            else:
                # 在日志框中插入成功信息
                log_text.insert(tk.END, "Tomcat 启动成功\n")
        finally:
            # 关闭SSH连接
            client.close()

# 停止 Tomcat 服务
def stop_tomcat():
    # 连接SSH
    client = connect_ssh()
    # 如果连接成功
    if client:
        try:
            # 执行停止Tomcat的命令
            stdin, stdout, stderr = client.exec_command(TOMCAT_STOP_CMD)
            # 读取错误信息
            error = stderr.read().decode()
            # 如果有错误信息
            if error:
                # 在日志框中插入错误信息
                log_text.insert(tk.END, f"停止失败: {error}\n")
            else:
                # 在日志框中插入成功信息
                log_text.insert(tk.END, "Tomcat 已停止\n")
        finally:
            # 关闭SSH连接
            client.close()

# 检查 Tomcat 服务状态
def check_status():
    # 连接 SSH
    client = connect_ssh()
    if client:
        try:
            # 执行 Tomcat 状态检查命令
            stdin, stdout, stderr = client.exec_command(TOMCAT_STATUS_CMD)
            # 读取命令输出
            output = stdout.read().decode()
            # 读取命令错误信息
            error = stderr.read().decode()
            # 如果有错误信息，则输出错误信息
            if error:
                log_text.insert(tk.END, f"状态检查失败: {error}\n")
            else:
                if output.strip():  # 如果有输出，说明 Tomcat 正在运行
                    log_text.insert(tk.END, "Tomcat 正在运行\n")
                else:
                    log_text.insert(tk.END, "Tomcat 未运行\n")
                # 在log_text文本框的末尾插入output字符串和换行符
                log_text.insert(tk.END, output + "\n")
        finally:
            client.close()

# 创建 GUI 界面
window = tk.Tk()
window.title('Tomcat 管理助手 - 远程')

# 启动按钮
start_button = tk.Button(window, text="启动 Tomcat", command=start_tomcat, width=20)
start_button.grid(row=0, column=0, padx=10, pady=10)

# 停止按钮
stop_button = tk.Button(window, text="停止 Tomcat", command=stop_tomcat, width=20)
stop_button.grid(row=0, column=1, padx=10, pady=10)

# 查看状态按钮
status_button = tk.Button(window, text="查看服务状态", command=check_status, width=20)
status_button.grid(row=1, column=0, padx=10, pady=10)

# 滚动日志窗口
log_text = scrolledtext.ScrolledText(window, width=80, height=20)
log_text.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

# 退出按钮
# 创建一个按钮，文本为“退出”，点击按钮时调用window.quit()函数，按钮宽度为20
exit_button = tk.Button(window, text="退出", command=window.quit, width=20)
# 将按钮放置在窗口的第二行第一列，左右间距为10，上下间距为10
exit_button.grid(row=1, column=1, padx=10, pady=10)

window.mainloop()
