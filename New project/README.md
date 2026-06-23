# CourseMate：AI 课程复习助手

CourseMate 是一个使用 Python、Streamlit 和 OpenAI Responses API 构建的课程复习应用，适合大学生整理期末考试材料。

## 功能

- 根据课程材料提炼核心考点、可能的简答题和易混淆点
- 生成适合写在试卷上的简答题答案与得分点分析
- 将错题整理为可复习、可自测的 Markdown 卡片
- 在网页中预览结果并下载 Markdown 文件

## 项目结构

```text
.
├── app.py
├── coursemate_core.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example
└── tests/
    └── test_coursemate_core.py
```

## 运行环境

- Python 3.10 或更高版本
- 一个可用的 OpenAI API Key

ChatGPT 订阅与 OpenAI API 账户是两个独立的产品；使用 API 需要在 API 平台中单独配置账户和额度。

## 安装与配置

在项目目录打开 PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

复制密钥示例文件：

```powershell
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

编辑 `.streamlit/secrets.toml`：

```toml
OPENAI_API_KEY = "你的 OpenAI API Key"
OPENAI_MODEL = "gpt-5.5"
```

真实的 `secrets.toml` 已被 `.gitignore` 忽略，不应上传到 GitHub。也可以不创建该文件，在应用左侧边栏临时输入 API Key。

API Key 必须是在 OpenAI API 平台生成、以 `sk-` 开头的完整英文密钥。不要填写“你的 API Key”等中文占位文字，不要带引号、空格或换行，也不能使用 ChatGPT 登录密码或其他 AI 平台的密钥。

## 启动

```powershell
streamlit run app.py
```

浏览器通常会自动打开；也可以访问终端显示的地址，默认是：

```text
http://localhost:8501
```

## 运行测试

```powershell
python -m unittest discover -s tests -v
```

测试不会调用真实 OpenAI API，也不会产生 API 费用。

## 配置说明

应用按以下优先级读取配置：

1. `.streamlit/secrets.toml`
2. 系统环境变量 `OPENAI_API_KEY` 和 `OPENAI_MODEL`
3. 未配置密钥时，可在网页侧边栏临时输入

默认模型为 `gpt-5.5`。如果账户暂时无法使用该模型，可把 `OPENAI_MODEL` 改为账户可访问且支持 Responses API 的模型。

## 使用提醒

AI 输出可能存在错误。涉及考试定义、固定表述和教师指定答案时，请以课程教材、课件和任课教师要求为准。
