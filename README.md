# AI 大模型 API 测试工具 (AI LLM API Tester)

这是一个基于 Python 和 CustomTkinter 构建的轻量级桌面应用程序，专门用于快速测试兼容 OpenAI 格式的大语言模型 API。它拥有极简的黑白灰外观，支持流式输出和多线程并发，让你在调试大模型接口时获得丝滑流畅的体验。
<img width="979" height="1172" alt="image" src="https://github.com/user-attachments/assets/f07593b5-132f-4053-9aa7-3a2b21c18802" />



## 核心特性

* **极简现代 UI**：采用类似 OpenAI 官网的黑白灰设计风格，支持系统原生的亮色与暗色模式切换。
* **真·流式输出**：基于 SSE (Server-Sent Events) 协议解析，实现平滑的“打字机”输出效果，且长文本接收时 UI 完全不卡顿。
* **智能文本导入**：支持从任意 `.txt` 文件中一键提取并自动识别 API URL、API Key 和模型名称，告别繁琐的复制粘贴。
* **健壮的异常处理**：内置多层拦截机制，能够精准识别 HTTP 错误、空跑数据、非标准 JSON 响应以及误填的普通网页地址。
* **多线程架构**：网络请求与 UI 渲染分离，确保在等待服务器响应或处理大量数据时，界面依然保持响应。

## 安装与运行

确保你的设备上已安装 Python 3.x 环境。

1. 克隆本仓库到本地：
```bash
git clone [https://github.com/你的用户名/你的仓库名.git](https://github.com/你的用户名/你的仓库名.git)
cd 你的仓库名

2.安装必要的依赖库：pip install customtkinter requests
3.运行程序：python API测试.py
