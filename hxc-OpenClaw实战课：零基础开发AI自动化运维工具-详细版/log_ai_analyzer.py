# 导入必要的Python库和模块
import json  # 用于处理JSON格式数据,如解析AI返回的结果
import threading  # 用于支持多线程编程,如在GUI中执行长时间运行的任务时保持界面响应
import re  # 用于正则表达式操作,如从AI返回的文本中提取JSON数据,以及从日志中提取时间戳,IP地址和错误信息


# 处理日期和时间相关的操作
from datetime import datetime, timedelta  # 提供日期和时间的计算功能,如获取当前时间、计算时间范围等
from elasticsearch import Elasticsearch  # Elasticsearch客户端库，用于连接和操作Elasticsearch数据库,需要安装elasticsearch库（pip3 install elasticsearch==7.17.9）
from openai import OpenAI  #  导入OpenAI客户端，用于与OpenAI API进行交互,实现LLM大模型调用,需要安装openai库（pip3 install openai）
import tkinter as tk  # Tkinter是Python的标准GUI库，用于创建图形用户界面,提供窗口、标签、输入框、按钮等基本组件
from tkinter import scrolledtext, messagebox, ttk  # Tkinter的扩展组件，提供滚动文本框、消息框和 ttk 控件
from docx import Document  # python-docx库，用于创建和修改Word文档,需要安装python-docx库（pip3 install python-docx）
from docx.shared import RGBColor  # 用于设置Word文档中的颜色,如在报告中高亮显示高风险等级
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer  # ReportLab库中用于创建PDF文档的组件,如文档模板、段落和间距
from reportlab.lib.styles import ParagraphStyle  # 用于设置PDF文档中段落的样式,如字体、大小和颜色
from reportlab.pdfbase.cidfonts import UnicodeCIDFont  # 支持PDF文档中的Unicode CID字体,用于显示中文字符
from reportlab.pdfbase import pdfmetrics  # 用于注册和管理PDF中的字体,支持中文显示

# ===============================
# 默认 ES 配置
# ===============================

# Elasticsearch相关配置信息
DEFAULT_ES_IP = "192.168.40.180"  # Elasticsearch服务器的默认IP地址
DEFAULT_ES_PORT = "30920"         # Elasticsearch服务器的默认端口号
DEFAULT_ES_INDEX = "logstash-*"   # 默认的 Elasticsearch 索引名称，用于指定默认要查询的索引模式


# Deepseek API相关配置信息
DEEPSEEK_BASE_URL = "https://api.deepseek.com"  
# Deepseek API的基础URL地址，用于构建API请求的完整URL，用于调用Deepseek的聊天模型接口，实现LLM大模型调用
DEEPSEEK_MODEL = "deepseek-chat"  
# Deepseek API使用的模型名称，指定要使用的Deepseek模型，如"deepseek-chat"，用于调用Deepseek的聊天模型接口，实现LLM大模型调用


# LogAIApp 类，主程序，包含整个应用的核心类，包含了GUI界面、ES连接、日志获取、AI分析和结果展示等功能
class LogAIApp:

    def __init__(self, root):
        self.root = root
        self.root.title("企业级 AI 运维分析平台（最终稳定版）")
        self.root.geometry("1500x600")

        self.es = None
        self.client = None
        self.latest_result = None

        self.build_ui()

    # ================= UI =================

    def build_ui(self):

        top = tk.Frame(self.root)
        top.pack(fill="x", pady=5)

        tk.Label(top, text="ES IP:").grid(row=0, column=0)
        self.es_ip = tk.Entry(top, width=15)
        self.es_ip.grid(row=0, column=1)
        self.es_ip.insert(0, DEFAULT_ES_IP)

        tk.Label(top, text="端口:").grid(row=0, column=2)
        self.es_port = tk.Entry(top, width=8)
        self.es_port.grid(row=0, column=3)
        self.es_port.insert(0, DEFAULT_ES_PORT)

        tk.Button(top, text="加载索引", command=self.load_indices).grid(row=0, column=4)

        self.index_combo = ttk.Combobox(top, width=30)
        self.index_combo.grid(row=0, column=5)
        self.index_combo.set(DEFAULT_ES_INDEX)

        tk.Label(top, text="时间范围:").grid(row=0, column=6)
        self.days_combo = ttk.Combobox(top, width=10,
                                       values=["1天", "2天", "7天", "30天"])
        self.days_combo.grid(row=0, column=7)
        self.days_combo.set("1天")

        tk.Label(top, text="DeepSeek Key:").grid(row=0, column=8)
        self.api_key_entry = tk.Entry(top, width=35, show="*")
        self.api_key_entry.grid(row=0, column=9)

        tk.Button(top, text="测试ES连接", command=self.test_es).grid(row=1, column=0)
        tk.Button(top, text="开始分析", command=self.start).grid(row=1, column=1)
        tk.Button(top, text="导出Word", command=self.export_word).grid(row=1, column=2)
        tk.Button(top, text="导出PDF", command=self.export_pdf).grid(row=1, column=3)

        self.log_area = scrolledtext.ScrolledText(self.root, height=15)
        self.log_area.pack(fill="both", expand=True)

        self.result_area = scrolledtext.ScrolledText(self.root, height=30)
        self.result_area.pack(fill="both", expand=True)

    # ================= ES =================

    def test_es(self):
        try:
            es = Elasticsearch(f"http://{self.es_ip.get()}:{self.es_port.get()}")
            if es.ping():
                messagebox.showinfo("成功", "ES 连接成功")
            else:
                messagebox.showerror("失败", "ES 无法连接")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def load_indices(self):
        try:
            es = Elasticsearch(f"http://{self.es_ip.get()}:{self.es_port.get()}")
            indices = list(es.indices.get_alias("*").keys())
            self.index_combo["values"] = indices
            messagebox.showinfo("成功", "索引加载成功")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    # ================= 启动 =================

    def start(self):
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):

        self.log_area.delete(1.0, tk.END)
        self.result_area.delete(1.0, tk.END)
        self.result_area.insert(tk.END, "AI 分析中...\n")

        try:
            self.init_es()
            self.init_ai()
        except Exception as e:
            messagebox.showerror("错误", str(e))
            return

        logs = self.fetch_logs()

        if not logs:
            self.log_area.insert(tk.END, "⚠ 未查询到日志\n")
            return

        for l in logs:
            self.log_area.insert(tk.END, f"[{l['timestamp']}] {l['message']}\n")

        result = self.analyze_with_ai(logs)
        parsed = self.parse_json(result)

        self.result_area.delete(1.0, tk.END)

        if parsed:
            self.latest_result = parsed
            self.display_pretty(parsed)
        else:
            self.result_area.insert(tk.END, result)

    # ================= 初始化 =================

    def init_es(self):
        self.es = Elasticsearch(
            f"http://{self.es_ip.get()}:{self.es_port.get()}")
        if not self.es.ping():
            raise Exception("ES 无法连接")

    def init_ai(self):
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            raise Exception("请输入 DeepSeek API Key")

        self.client = OpenAI(api_key=api_key,
                             base_url=DEEPSEEK_BASE_URL)

    # ================= 获取日志（终极稳定版） =================

    def fetch_logs(self):

        days = int(self.days_combo.get().replace("天", ""))

        end = datetime.utcnow()
        start = end - timedelta(days=days)

        index = self.index_combo.get()

        # 先取一条样本
        res = self.es.search(index=index, size=1)

        if not res["hits"]["hits"]:
            return []

        sample = res["hits"]["hits"][0]["_source"]

        # 自动识别时间字段
        time_field = None
        for field in ["@timestamp", "timestamp", "logtime", "time"]:
            if field in sample:
                time_field = field
                break

        # 构造时间查询值
        gte = start.isoformat()
        lte = end.isoformat()

        try:
            if time_field:
                res = self.es.search(
                    index=index,
                    body={
                        "query": {
                            "range": {
                                time_field: {
                                    "gte": gte,
                                    "lte": lte
                                }
                            }
                        }
                    },
                    size=200
                )
            else:
                res = self.es.search(index=index, size=200)
        except Exception as e:
            print("时间查询失败，自动降级：", e)
            res = self.es.search(index=index, size=200)

        logs = []

        for hit in res["hits"]["hits"]:
            s = hit["_source"]
            logs.append({
                "timestamp": str(s.get(time_field, "")),
                "message": str(s.get("message", s))
            })

        return logs

    # ================= AI =================

    def analyze_with_ai(self, logs):

        content = "\n".join(
            [f"[{l['timestamp']}] {l['message']}" for l in logs])

        prompt = f"""
必须返回JSON，并分级编号输出。
{{
"是否异常":"",
"风险等级":"",
"影响范围":"",
"故障类型":"",
"根因分析":"",
"应急处理建议":"",
"架构优化建议":"",
"风险评估说明":"",
"架构级总结":""
}}

日志:
{content}
"""

        resp = self.client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=1.3
        )

        return resp.choices[0].message.content

    def parse_json(self, text):
        try:
            text = re.sub(r"```json|```", "", text).strip()
            return json.loads(text)
        except:
            return None

    # ================= 输出美化 =================

    def display_pretty(self, data):

        self.result_area.insert(
            tk.END, "========== 企业级 AI 运维分析报告 ==========\n\n")

        for k, v in data.items():

            if k == "风险等级":
                if "高" in v:
                    self.result_area.insert(
                        tk.END, f"{k}：{v}\n\n", "high")
                elif "中" in v:
                    self.result_area.insert(
                        tk.END, f"{k}：{v}\n\n", "medium")
                else:
                    self.result_area.insert(
                        tk.END, f"{k}：{v}\n\n")
            else:
                self.result_area.insert(tk.END, f"【{k}】\n")
                self.result_area.insert(tk.END, f"{v}\n\n")

        self.result_area.tag_config("high", foreground="red")
        self.result_area.tag_config("medium", foreground="orange")

    # ================= Word =================

    def export_word(self):

        if not self.latest_result:
            messagebox.showerror("错误", "请先分析")
            return

        doc = Document()
        doc.add_heading("企业级 AI 运维分析报告", 0)

        for k, v in self.latest_result.items():
            heading = doc.add_heading(k, level=1)
            if k == "风险等级" and "高" in v:
                heading.runs[0].font.color.rgb = RGBColor(255, 0, 0)
            doc.add_paragraph(v)

        filename = f"AI运维报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        doc.save(filename)

        messagebox.showinfo("成功", filename)

    # ================= PDF =================

    def export_pdf(self):

        if not self.latest_result:
            messagebox.showerror("错误", "请先分析")
            return

        filename = f"AI运维报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

        doc = SimpleDocTemplate(filename)
        elements = []

        style = ParagraphStyle(
            name='Chinese',
            fontName='STSong-Light',
            fontSize=12
        )

        elements.append(Paragraph("企业级 AI 运维分析报告", style))
        elements.append(Spacer(1, 12))

        for k, v in self.latest_result.items():
            elements.append(Paragraph(f"<b>{k}</b>", style))
            elements.append(Spacer(1, 8))
            elements.append(Paragraph(v.replace("\n", "<br/>"), style))
            elements.append(Spacer(1, 15))

        doc.build(elements)

        messagebox.showinfo("成功", filename)


if __name__ == "__main__":
    root = tk.Tk()
    app = LogAIApp(root)
    root.mainloop()