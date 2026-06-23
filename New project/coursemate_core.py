from typing import Any


SYSTEM_PROMPT = """
你是一个面向中国大学计算机专业学生的 AI 课程复习助手。
用户的主要目标是应对课程考试，同时希望理解必要的前沿知识。

回答必须遵守以下规则：
1. 使用中文。
2. 优先采用教材、考试和简答题风格，内容准确、清晰、便于记忆。
3. 涉及前沿观点时，明确区分“教材考试版”和“前沿理解版”。
4. 不得伪造教材原文。若用户未提供教材内容，应提醒：
   “以下为通用答案，考试请以任课教师和教材要求为准。”
5. 使用结构清晰的 Markdown，但不要堆砌无关内容。
""".strip()


TASKS = {
    "summary": {
        "file_name": "考点总结.md",
        "prompt": """
请根据下面的课程内容整理期末考试复习考点。

要求：
1. 先提炼核心考点，并标注建议掌握程度。
2. 再列出可能出现的简答题及答题关键词。
3. 最后列出容易混淆、容易失分的地方。
4. 只基于用户提供的材料总结；必要的通用补充须明确标注。

课程内容：
{user_input}
""",
    },
    "answer": {
        "file_name": "简答题答案.md",
        "prompt": """
请回答下面这道课程简答题。

要求：
1. 先给出可直接写在试卷上的“教材考试版答案”。
2. 再给出“答题分析”，说明得分点和组织顺序。
3. 必要时补充“前沿理解版”，但不能干扰考试答案。
4. 答案简洁完整，避免空泛和过度展开。

题目：
{user_input}
""",
    },
    "card": {
        "file_name": "错题卡片.md",
        "prompt": """
请根据下面的信息生成一张错题复习卡片。

卡片必须包含：
1. 题目
2. 正确答案
3. 我的错误点
4. 失分原因
5. 记忆方法
6. 下次答题模板
7. 一道用于自测的变式题

使用 Markdown 输出，重点帮助学生避免再次犯错。

错题信息：
{user_input}
""",
    },
}


def validate_api_key(api_key: str | None) -> str:
    """Validate a key before it is placed in the HTTP Authorization header."""
    if not api_key:
        raise ValueError("尚未填写 OpenAI API Key。")

    cleaned_key = api_key.strip()
    if not cleaned_key:
        raise ValueError("尚未填写 OpenAI API Key。")

    try:
        cleaned_key.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(
            "API Key 包含中文、中文引号或其他非英文字符。"
            "请从 OpenAI API Keys 页面复制以 sk- 开头的真实密钥。"
        ) from exc

    if cleaned_key[0] in {'"', "'"} or cleaned_key[-1] in {'"', "'"}:
        raise ValueError("API Key 两端不能包含引号，请只粘贴密钥本身。")

    if any(character.isspace() for character in cleaned_key):
        raise ValueError("API Key 中包含空格或换行，请重新完整复制。")

    if not cleaned_key.startswith("sk-"):
        raise ValueError(
            "这不是有效的 OpenAI API Key：密钥通常以 sk- 开头。"
            "ChatGPT 账号密码或其他平台密钥不能在此使用。"
        )

    if len(cleaned_key) < 20:
        raise ValueError("API Key 长度明显不足，请粘贴完整的 OpenAI API Key。")

    return cleaned_key


def rate_limit_message(error: Exception) -> str:
    details = " ".join(
        str(value)
        for value in (
            getattr(error, "code", ""),
            getattr(error, "body", ""),
            error,
        )
        if value
    ).lower()

    if any(
        marker in details
        for marker in ("insufficient_quota", "quota", "billing", "credit balance")
    ):
        return (
            "OpenAI API 余额不足或尚未开通 API 计费。"
            "请前往 OpenAI Platform 的 Billing 页面添加付款方式并购买 API credits；"
            "充值生效后再重试。ChatGPT Plus 订阅不包含 API 额度。"
        )

    return (
        "请求速度超过当前账户的 API 速率限制。"
        "请等待约一分钟后重试；如果持续发生，请在 OpenAI Platform 的 Limits 页面"
        "查看当前 RPM/TPM 限额。"
    )


def build_prompt(task_key: str, user_input: str) -> str:
    if task_key not in TASKS:
        raise ValueError(f"未知任务类型：{task_key}")
    cleaned_input = user_input.strip()
    if not cleaned_input:
        raise ValueError("输入内容不能为空")
    return TASKS[task_key]["prompt"].strip().format(user_input=cleaned_input)


def generate_review(
    client: Any,
    model: str,
    task_key: str,
    user_input: str,
) -> str:
    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=build_prompt(task_key, user_input),
    )
    output = (response.output_text or "").strip()
    if not output:
        raise RuntimeError("模型没有返回可显示的文本内容")
    return output
