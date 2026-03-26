import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import json
import threading
import queue
import re

# 移除默认的蓝色主题，使用系统默认以支持完全自定义黑白灰
ctk.set_appearance_mode("System")

class APITesterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI 大模型 API 测试工具")
        self.geometry("650x750")
        
        # OpenAI 黑白灰风格颜色定义 (亮色模式, 暗色模式)
        self.C_BG = ("#FFFFFF", "#212121")             # 整体背景
        self.C_FRAME = ("#F7F7F8", "#2F2F2F")          # 区域背景 (稍微区分)
        self.C_TEXT = ("#2D333A", "#ECECEC")           # 主文本颜色
        self.C_BORDER = ("#D9D9E3", "#565869")         # 默认细边框
        self.C_BTN_PRI_FG = ("#000000", "#FFFFFF")     # 主按钮背景色 (黑/白)
        self.C_BTN_PRI_TXT = ("#FFFFFF", "#000000")    # 主按钮文字色 (白/黑)
        self.C_BTN_PRI_HOV = ("#333333", "#E5E5E5")    # 主按钮悬停色
        self.C_BTN_SEC_FG = ("#FFFFFF", "#343541")     # 次要按钮背景
        self.C_BTN_SEC_TXT = ("#2D333A", "#ECECEC")    # 次要按钮文字
        self.C_BTN_SEC_HOV = ("#F7F7F8", "#40414F")    # 次要按钮悬停

        self.configure(fg_color=self.C_BG)
        
        # 线程通信队列：传递 (消息类型, 消息内容) 的元组
        self.result_queue = queue.Queue()
        
        self.create_widgets()
        self.process_queue()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        
        # --- 顶部：标题与导入按钮 ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(header_frame, text="API 配置", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.C_TEXT)
        title_label.grid(row=0, column=0, sticky="w")
        
        import_btn = ctk.CTkButton(
            header_frame, text="📄 从 TXT 导入", width=120, 
            fg_color=self.C_BTN_SEC_FG, text_color=self.C_BTN_SEC_TXT, hover_color=self.C_BTN_SEC_HOV,
            border_width=1, border_color=self.C_BORDER,
            command=self.import_from_txt
        )
        import_btn.grid(row=0, column=1, sticky="e")

        # --- 配置区域 ---
        config_frame = ctk.CTkFrame(self, fg_color=self.C_FRAME, border_width=1, border_color=self.C_BORDER, corner_radius=8)
        config_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        config_frame.grid_columnconfigure(1, weight=1)

        # 统一样式字典：用于输入框 (已移除不支持的 focus_border_color)
        entry_kwargs = {
            "fg_color": "transparent",
            "text_color": self.C_TEXT,
            "border_color": self.C_BORDER,
            "border_width": 1,
            "corner_radius": 6
        }

        # URL
        ctk.CTkLabel(config_frame, text="API URL:", text_color=self.C_TEXT).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        self.url_entry = ctk.CTkEntry(config_frame, placeholder_text="例如: https://api.openai.com/v1/chat/completions", **entry_kwargs)
        self.url_entry.insert(0, "https://api.openai.com/v1/chat/completions")
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=15, pady=(15, 5))

        # API Key
        ctk.CTkLabel(config_frame, text="API Key:", text_color=self.C_TEXT).grid(row=1, column=0, sticky="w", padx=15, pady=5)
        self.key_entry = ctk.CTkEntry(config_frame, placeholder_text="sk-...", **entry_kwargs)
        self.key_entry.grid(row=1, column=1, sticky="ew", padx=15, pady=5)

        # Model
        ctk.CTkLabel(config_frame, text="模型名称:", text_color=self.C_TEXT).grid(row=2, column=0, sticky="w", padx=15, pady=(5, 15))
        self.model_entry = ctk.CTkEntry(config_frame, placeholder_text="例如: gpt-3.5-turbo", **entry_kwargs)
        self.model_entry.insert(0, "gpt-3.5-turbo")
        self.model_entry.grid(row=2, column=1, sticky="ew", padx=15, pady=(5, 15))

        # --- 输入区域 ---
        ctk.CTkLabel(self, text="测试提示词 (Prompt)", font=ctk.CTkFont(weight="bold"), text_color=self.C_TEXT).grid(row=2, column=0, sticky="w", padx=20, pady=(15, 5))
        self.prompt_text = ctk.CTkTextbox(
            self, height=80, 
            fg_color=self.C_FRAME, text_color=self.C_TEXT, 
            border_width=1, border_color=self.C_BORDER, corner_radius=8
        )
        self.prompt_text.insert("1.0", "你好，请确认你可以正常接收消息，回复你什么模型。")
        self.prompt_text.grid(row=3, column=0, sticky="ew", padx=20, pady=0)

        # --- 测试按钮 ---
        self.test_btn = ctk.CTkButton(
            self, text="🚀 发送请求测试", height=45, font=ctk.CTkFont(weight="bold", size=14),
            fg_color=self.C_BTN_PRI_FG, text_color=self.C_BTN_PRI_TXT, hover_color=self.C_BTN_PRI_HOV,
            corner_radius=8,
            command=self.start_test
        )
        self.test_btn.grid(row=4, column=0, sticky="ew", padx=20, pady=20)

        # --- 输出区域 ---
        ctk.CTkLabel(self, text="测试结果", font=ctk.CTkFont(weight="bold"), text_color=self.C_TEXT).grid(row=5, column=0, sticky="w", padx=20, pady=(0, 5))
        self.result_text = ctk.CTkTextbox(
            self, height=200, font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=self.C_FRAME, text_color=self.C_TEXT,
            border_width=1, border_color=self.C_BORDER, corner_radius=8
        )
        self.result_text.grid(row=6, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.grid_rowconfigure(6, weight=1)

    def import_from_txt(self):
        """增强版 TXT 智能导入"""
        filepath = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not filepath: return
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if not line: continue
                lower_line = line.lower()
                
                # 识别 URL
                if line.startswith("http"):
                    self.url_entry.delete(0, 'end')
                    self.url_entry.insert(0, line)
                    continue
                match_url = re.search(r'(https?://[^\s]+)', line)
                if match_url:
                    self.url_entry.delete(0, 'end')
                    self.url_entry.insert(0, match_url.group(1))
                    continue

                # 识别 Key
                match_key = re.search(r'(sk-[^\s"\'>]+)', line)
                if match_key:
                    self.key_entry.delete(0, 'end')
                    self.key_entry.insert(0, match_key.group(1))
                    continue
                elif "key" in lower_line or "api" in lower_line:
                    val = ""
                    if ':' in line: val = line.split(':', 1)[1].strip()
                    elif '=' in line: val = line.split('=', 1)[1].strip()
                    if val and len(val) > 10:
                        self.key_entry.delete(0, 'end')
                        self.key_entry.insert(0, val.strip("\"'"))
                        continue

                # 识别 模型
                if "model" in lower_line or "模型" in lower_line:
                    val = ""
                    if ':' in line: val = line.split(':', 1)[1].strip()
                    elif '=' in line: val = line.split('=', 1)[1].strip()
                    if val:
                        self.model_entry.delete(0, 'end')
                        self.model_entry.insert(0, val.strip("\"'"))
                        continue
                elif ' ' not in line and ('/' in line or '-' in line) and len(line) < 60:
                    self.model_entry.delete(0, 'end')
                    self.model_entry.insert(0, line)
                    continue
                        
            messagebox.showinfo("导入成功", "文本解析完成！")
        except Exception as e:
            messagebox.showerror("读取失败", f"无法读取该文件: {str(e)}")

    def process_queue(self):
        """队列轮询：安全更新 UI"""
        try:
            while True:
                msg_type, msg_content = self.result_queue.get_nowait()
                
                if msg_type == "START":
                    self.result_text.delete("1.0", "end")
                    self.result_text.insert("end", msg_content)
                
                elif msg_type == "CHUNK":
                    try:
                        self.result_text.insert("end", msg_content)
                    except tk.TclError:
                        clean_msg = "".join(c for c in msg_content if ord(c) <= 0xFFFF)
                        self.result_text.insert("end", clean_msg)
                    self.result_text.see("end") 
                
                elif msg_type == "END":
                    self.result_text.insert("end", msg_content)
                    self.result_text.see("end")
                    self.test_btn.configure(state="normal", text="🚀 发送请求测试")
                
                elif msg_type == "ERROR":
                    self.result_text.delete("1.0", "end")
                    self.result_text.insert("end", msg_content)
                    self.test_btn.configure(state="normal", text="🚀 发送请求测试")

        except queue.Empty:
            pass
        finally:
            self.after(50, self.process_queue) 

    def start_test(self):
        url = self.url_entry.get().strip()
        api_key = self.key_entry.get().strip()
        model = self.model_entry.get().strip()
        prompt = self.prompt_text.get("1.0", "end-1c").strip()

        if not url or not prompt:
            messagebox.showwarning("输入错误", "API URL 和 测试提示词不能为空！")
            return

        self.test_btn.configure(state="disabled", text="⏳ 正在接收流式数据...")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", "正在连接服务器并等待首字响应，请稍候...\n")

        threading.Thread(target=self.make_request, args=(url, api_key, model, prompt), daemon=True).start()

    def make_request(self, url, api_key, model, prompt):
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True # 开启流式输出
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=(10, 30), stream=True)
            
            # 关卡 1：如果状态码不是 200，直接抛出 HTTP 错误
            if response.status_code != 200:
                self.result_queue.put(("ERROR", f"❌ 请求失败 (HTTP {response.status_code})\n\n服务器返回信息：\n{response.text}"))
                return

            # 获取服务器返回的内容类型
            content_type = response.headers.get('Content-Type', '').lower()

            # 关卡 2：标准流式输出处理 (text/event-stream)
            if 'text/event-stream' in content_type:
                self.result_queue.put(("START", "✅ 连接成功！正在接收数据...\n\n【模型回复】:\n"))
                chunk_received = False 
                
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8', errors='replace')
                        if decoded_line.startswith("data: "):
                            data_str = decoded_line[6:].strip()
                            if data_str == "[DONE]": 
                                break
                            try:
                                data_json = json.loads(data_str)
                                if "choices" in data_json and len(data_json["choices"]) > 0:
                                    delta = data_json["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        chunk_received = True
                                        self.result_queue.put(("CHUNK", content))
                            except json.JSONDecodeError:
                                pass 
                
                # 关卡 3：数据空跑校验
                if not chunk_received:
                    self.result_queue.put(("ERROR", "\n❌ 警告：虽然网络连接成功，但未解析到任何有效的模型回复内容！\n请检查：\n1. 模型名称是否输入正确？\n2. 接口是否并非标准的 OpenAI 格式？"))
                else:
                    self.result_queue.put(("END", "\n\n[✅ 输出完毕]"))
                    
            # 兼容处理：服务器无视了 stream=True，直接返回了完整 JSON
            elif 'application/json' in content_type:
                result_json = response.json()
                try:
                    if 'choices' in result_json and len(result_json['choices']) > 0:
                        reply = result_json['choices'][0]['message']['content']
                        self.result_queue.put(("START", f"✅ 调用成功！(服务器返回了非流式 JSON)\n\n【模型回复】:\n{reply}"))
                        self.result_queue.put(("END", "\n\n[✅ 输出完毕]"))
                    else:
                        self.result_queue.put(("ERROR", f"❌ 解析失败：服务器返回了 JSON，但未找到标准回复字段。\n\n完整内容：\n{json.dumps(result_json, indent=2, ensure_ascii=False)}"))
                except Exception as e:
                    self.result_queue.put(("ERROR", f"❌ JSON 解析异常：{str(e)}"))

            # 绝杀关卡：普通网页直接拦截 (如 bing.com)
            else:
                 self.result_queue.put(("ERROR", f"❌ 接口地址错误！\n\n期待接收 API 数据，但服务器返回了 '{content_type}' 类型的普通网页或文件。\n你确定输入的是大模型的 API 端点（Endpoint），而不是官网首页吗？"))

        except requests.exceptions.Timeout:
            self.result_queue.put(("ERROR", "❌ 调用失败：请求超时！可能是网络原因或服务器无响应。"))
        except requests.exceptions.RequestException as e:
            self.result_queue.put(("ERROR", f"❌ 网络请求错误：\n{str(e)}"))
        except Exception as e:
            self.result_queue.put(("ERROR", f"❌ 发生未知错误：\n{str(e)}"))

if __name__ == "__main__":
    app = APITesterApp()
    app.mainloop()