# =========================
# 导入模块
# =========================
# 导入所需的库和模块
import paramiko  # 用于SSH连接和远程执行命令,需要安装paramiko库（pip3 install paramiko）
import threading  # 用于多线程处理，实现并发执行任务,如在GUI中执行长时间运行的诊断任务时保持界面响应
import tkinter as tk  # 创建图形用户界面(GUI)的基础库,提供窗口、标签、输入框、按钮等基本组件
from tkinter import ttk, messagebox, scrolledtext  # tkinter的扩展组件，提供更丰富的界面元素,如组合框、消息框和滚动文本框
from openai import OpenAI  # 导入OpenAI客户端，用于与OpenAI API进行交互,实现LLM调用,需要安装openai库（pip3 install openai）

# =========================
# DeepSeek API配置
# =========================
# DeepSeek API的基础URL，用于构建API请求的完整地址
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
# DeepSeek API使用的模型名称，指定要调用的具体模型
DEEPSEEK_MODEL = "deepseek-chat"

ssh_client = None


# =========================
# SSH 连接
# =========================
def connect_ssh():
    global ssh_client

    host = host_entry.get().strip()
    user = user_entry.get().strip()
    password = pass_entry.get().strip()
    key_path = key_entry.get().strip()
    mode = login_mode.get()

    if not host or not user:
        messagebox.showwarning("提示", "请填写完整的主机和用户名")
        return

    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if mode == "密码登录":
            if not password:
                messagebox.showwarning("提示", "请输入密码")
                return

            ssh_client.connect(
                hostname=host,
                username=user,
                password=password,
                timeout=10
            )

        elif mode == "私钥登录":
            if not key_path:
                messagebox.showwarning("提示", "请输入私钥路径")
                return

            private_key = paramiko.RSAKey.from_private_key_file(key_path)

            ssh_client.connect(
                hostname=host,
                username=user,
                pkey=private_key,
                timeout=10
            )

        status_label.config(text="已连接", fg="green")
        log("SSH 连接成功")

    except Exception as e:
        status_label.config(text="连接失败", fg="red")
        messagebox.showerror("SSH错误", str(e))


def run_remote_cmd(cmd):
    if ssh_client is None:
        return "SSH 未连接，请先连接服务器"

    try:
        stdin, stdout, stderr = ssh_client.exec_command(cmd)
        return stdout.read().decode() + stderr.read().decode()
    except Exception as e:
        return f"执行命令异常: {str(e)}"


# =========================
# 获取 namespace
# =========================
def load_namespaces():
    output = run_remote_cmd("kubectl get ns -o jsonpath='{.items[*].metadata.name}'")
    if "SSH 未连接" in output:
        messagebox.showwarning("提示", output)
        return

    ns_list = output.replace("'", "").split()
    namespace_combo["values"] = ns_list
    if ns_list:
        namespace_combo.current(0)


# =========================
# 获取 pod
# =========================
def load_pods(event=None):
    namespace = namespace_combo.get()
    if not namespace:
        return

    cmd = f"kubectl get pods -n {namespace} -o jsonpath='{{.items[*].metadata.name}}'"
    output = run_remote_cmd(cmd)
    pod_list = output.replace("'", "").split()
    pod_combo["values"] = pod_list
    if pod_list:
        pod_combo.current(0)


# =========================
# LLM 调用
# =========================
def call_llm(api_key, prompt):
    client = OpenAI(
        api_key=api_key,
        base_url=DEEPSEEK_BASE_URL
    )

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": "你是资深 Kubernetes 运维专家"},
            {"role": "user", "content": prompt}
        ],
        temperature=1.3
    )

    return response.choices[0].message.content


# =========================
# 诊断逻辑
# =========================
def diagnose_thread():
    api_key = api_entry.get().strip()
    namespace = namespace_combo.get()
    pod = pod_combo.get()

    if not api_key:
        messagebox.showwarning("提示", "请输入 API Key")
        return

    if not namespace or not pod:
        messagebox.showwarning("提示", "请选择 Namespace 和 Pod")
        return

    log("开始采集远程数据...")

    describe = run_remote_cmd(f"kubectl describe pod {pod} -n {namespace}")
    logs_data = run_remote_cmd(f"kubectl logs {pod} -n {namespace} --tail=100")
    events = run_remote_cmd(f"kubectl get events -n {namespace} --sort-by=.lastTimestamp")
    top = run_remote_cmd(f"kubectl top pod {pod} -n {namespace}")

    prompt = f"""
以下是 Kubernetes Pod 故障信息：

=== Describe ===
{describe}

=== Logs ===
{logs_data}

=== Events ===
{events}

=== Resource ===
{top}

你是资深 Kubernetes SRE 专家，请按照企业级故障分析报告标准输出：

一、故障概述
- 当前异常现象
- 关键错误信息
- Pod 当前状态

二、影响范围评估
- 是否影响业务流量
- 是否影响核心服务
- 是否存在扩散风险
- 风险等级（高 / 中 / 低）

三、根因分析（按概率排序）
- 可能原因1（概率高）
- 可能原因2（概率中）
- 可能原因3（概率低）

四、紧急处置措施（优先恢复服务）
- 可立即执行的操作步骤
- 推荐执行命令
- 如果涉及到对pod里容器操作的命令,要指定容器名称
- 在容器里执行的命令之前,如果是kubectl命令,需要先--help查看当前最新的参数,给出最新的命令

五、修复验证方法
- 应检查的状态
- 应观察的指标
- 成功判断标准

六、长期优化建议
- 配置优化建议
- 监控告警建议
- 资源容量建议
- 架构改进建议

输出要求：
- 语言专业
- 结构清晰
- 操作可执行
- 避免泛泛而谈
"""

    log("调用 DeepSeek 分析中...")

    result = call_llm(api_key, prompt)

    log("\n===== 智能诊断结果 =====")
    log(result)


def start_diagnose():
    thread = threading.Thread(target=diagnose_thread)
    thread.start()


# =========================
# GUI
# =========================
root = tk.Tk()
root.title("K8s LLM 智能诊断平台（远程企业版）")
root.geometry("1100x950")

# ===== SSH 登录信息 =====
tk.Label(root, text="控制节点 IP").pack()
host_entry = tk.Entry(root, width=60)
host_entry.pack()

tk.Label(root, text="SSH 用户名").pack()
user_entry = tk.Entry(root, width=60)
user_entry.pack()

tk.Label(root, text="登录方式").pack()
login_mode = ttk.Combobox(root, values=["密码登录", "私钥登录"], state="readonly")
login_mode.pack()
login_mode.current(0)

tk.Label(root, text="SSH 密码（密码模式使用）").pack()
pass_entry = tk.Entry(root, width=60, show="*")
pass_entry.pack()

tk.Label(root, text="私钥路径（私钥模式使用）").pack()
key_entry = tk.Entry(root, width=60)
key_entry.pack()

status_label = tk.Label(root, text="未连接", fg="red")
status_label.pack(pady=5)

tk.Button(root, text="连接远程K8s控制节点", command=connect_ssh).pack(pady=10)

# ===== DeepSeek API =====
tk.Label(root, text="DeepSeek API Key").pack()
api_entry = tk.Entry(root, width=80, show="*")
api_entry.pack(pady=5)

# ===== Namespace =====
tk.Label(root, text="选择 Namespace").pack()
namespace_combo = ttk.Combobox(root, width=60)
namespace_combo.pack()

tk.Button(root, text="加载 Namespace", command=load_namespaces).pack(pady=5)

# ===== Pod =====
tk.Label(root, text="选择 Pod").pack()
pod_combo = ttk.Combobox(root, width=60)
pod_combo.pack()

namespace_combo.bind("<<ComboboxSelected>>", load_pods)

# ===== 诊断按钮 =====
tk.Button(root, text="开始智能诊断", command=start_diagnose).pack(pady=10)

# ===== 输出区域 =====
output = scrolledtext.ScrolledText(root, font=("Consolas", 10))
output.pack(expand=True, fill="both", padx=10, pady=10)


def log(text):
    output.insert(tk.END, text + "\n")
    output.see(tk.END)


root.mainloop()