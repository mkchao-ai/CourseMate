import os

import streamlit as st
from openai import APIConnectionError, APIError, AuthenticationError, OpenAI, RateLimitError

from coursemate_core import (
    TASKS,
    generate_review,
    rate_limit_message,
    validate_api_key,
)


st.set_page_config(
    page_title="CourseMate：AI课程复习助手",
    page_icon="📘",
    layout="wide",
)

DEFAULT_MODEL = "gpt-5.5"


def read_secret(name: str) -> str | None:
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return str(value).strip() if value else None


def configured_value(name: str, default: str | None = None) -> str | None:
    return read_secret(name) or os.getenv(name) or default


def show_result(task_key: str) -> None:
    result = st.session_state.get(f"result_{task_key}")
    if not result:
        return

    task = TASKS[task_key]
    st.markdown("---")
    st.markdown("### 生成结果")
    st.markdown(result)
    st.download_button(
        "下载 Markdown 文件",
        data=result,
        file_name=task["file_name"],
        mime="text/markdown",
        key=f"download_{task_key}",
        use_container_width=True,
    )


def run_task(task_key: str, content: str, api_key: str | None, model: str) -> None:
    if not content.strip():
        st.warning("请先输入内容。")
        return
    try:
        valid_api_key = validate_api_key(api_key)
    except ValueError as exc:
        st.error(str(exc))
        return

    try:
        client = OpenAI(api_key=valid_api_key, timeout=60.0, max_retries=2)
        with st.spinner("AI 正在整理复习内容，请稍候……"):
            st.session_state[f"result_{task_key}"] = generate_review(
                client=client,
                model=model,
                task_key=task_key,
                user_input=content,
            )
    except AuthenticationError:
        st.error(
            "OpenAI 拒绝了该 API Key。请确认密钥未过期、未被撤销，"
            "并且它来自 OpenAI API 平台，而不是 ChatGPT 登录账号或其他 AI 平台。"
        )
    except RateLimitError as exc:
        st.error(rate_limit_message(exc))
        st.markdown(
            "打开：[API 余额与充值](https://platform.openai.com/settings/organization/billing/overview)"
            " · [API 使用限额](https://platform.openai.com/settings/organization/limits)"
        )
    except APIConnectionError:
        st.error("暂时无法连接 OpenAI API，请检查网络后重试。")
    except APIError as exc:
        st.error(f"OpenAI API 返回错误：{exc}")
    except UnicodeEncodeError:
        st.error(
            "API Key 或网络代理配置中含有非英文字符。"
            "请重新复制以 sk- 开头的 OpenAI API Key。"
        )
    except Exception as exc:
        st.error(f"生成失败：{exc}")


st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    [data-testid="stMetricValue"] {font-size: 1rem;}
    .hero {
        padding: 1.35rem 1.5rem;
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(57, 106, 252, 0.12), rgba(125, 72, 227, 0.08));
        margin-bottom: 1.2rem;
    }
    .hero h1 {margin: 0 0 .35rem 0; font-size: 2rem;}
    .hero p {margin: 0; opacity: .8;}
    </style>
    <div class="hero">
      <h1>📘 CourseMate</h1>
      <p>面向大学课程复习的 AI 助手：整理考点、生成简答题答案、复盘错题。</p>
    </div>
    """,
    unsafe_allow_html=True,
)

model_name = configured_value("OPENAI_MODEL", DEFAULT_MODEL) or DEFAULT_MODEL
saved_api_key = configured_value("OPENAI_API_KEY")

with st.sidebar:
    st.header("使用说明")
    st.write("粘贴课程材料或题目，选择相应功能即可生成结构化复习内容。")

    st.divider()
    st.subheader("API 配置")
    if saved_api_key:
        st.success("已检测到 API Key")
        api_key = saved_api_key
    else:
        st.info("未检测到 API Key。可临时在下方输入，或按 README 创建 secrets.toml。")
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help=(
                "仅用于本次 Streamlit 会话，不会写入项目文件。"
                "必须粘贴 OpenAI API 平台生成、以 sk- 开头的完整密钥。"
            ),
        ).strip() or None

    st.caption("密钥必须以 sk- 开头；请勿输入中文占位文字，也不要提交到 GitHub。")
    with st.expander("遇到“额度不足”怎么办？"):
        st.markdown(
            "1. 打开 [API Billing](https://platform.openai.com/settings/organization/billing/overview)\n"
            "2. 添加付款方式并购买 API credits\n"
            "3. 打开 [Limits](https://platform.openai.com/settings/organization/limits) 检查使用限额\n"
            "4. 等待余额生效后重新生成\n\n"
            "注意：ChatGPT Plus/Pro 订阅不等于 OpenAI API 额度。"
        )
    st.divider()
    st.subheader("当前模型")
    st.code(model_name)
    st.caption("可通过 OPENAI_MODEL 环境变量或 Streamlit secrets 修改。")

tab_summary, tab_answer, tab_card = st.tabs(
    ["🧭 考点总结", "✍️ 简答题生成", "🗂️ 错题卡片"]
)

with tab_summary:
    st.subheader("课程内容考点总结")
    st.caption("适合粘贴教材段落、课堂笔记或复习提纲。")
    summary_input = st.text_area(
        "请输入或粘贴课程内容",
        placeholder=(
            "例如：云计算体系结构包括基础设施层、平台层、应用层和用户访问层……"
        ),
        height=260,
        key="summary_input",
    )
    if st.button(
        "生成考点总结",
        key="summary_button",
        type="primary",
        use_container_width=True,
    ):
        run_task("summary", summary_input, api_key, model_name)
    show_result("summary")

with tab_answer:
    st.subheader("简答题答案生成")
    st.caption("答案以适合写在试卷上的“教材考试版”为主，并补充答题分析。")
    answer_input = st.text_area(
        "请输入简答题题目",
        placeholder="例如：简述云计算体系结构。",
        height=200,
        key="answer_input",
    )
    if st.button(
        "生成简答题答案",
        key="answer_button",
        type="primary",
        use_container_width=True,
    ):
        run_task("answer", answer_input, api_key, model_name)
    show_result("answer")

with tab_card:
    st.subheader("错题复习卡片")
    st.caption("建议同时提供题目、你的错误答案和教材正确答案。")
    card_input = st.text_area(
        "请输入错题信息",
        placeholder=(
            "题目：简述高可用性架构设计方式。\n"
            "我的错误答案：高可用性就是多加几台服务器。\n"
            "教材正确答案：包括冗余设计、故障检测、负载均衡、故障转移等。"
        ),
        height=260,
        key="card_input",
    )
    if st.button(
        "生成错题卡片",
        key="card_button",
        type="primary",
        use_container_width=True,
    ):
        run_task("card", card_input, api_key, model_name)
    show_result("card")
