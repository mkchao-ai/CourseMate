import unittest
from types import SimpleNamespace

from coursemate_core import (
    TASKS,
    build_prompt,
    generate_review,
    rate_limit_message,
    validate_api_key,
)


class FakeResponses:
    def __init__(self, output_text="生成结果"):
        self.output_text = output_text
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return SimpleNamespace(output_text=self.output_text)


class CoreTests(unittest.TestCase):
    def test_quota_error_gets_billing_guidance(self):
        error = SimpleNamespace(code="insufficient_quota", body={})
        message = rate_limit_message(error)
        self.assertIn("余额不足", message)
        self.assertIn("Billing", message)

    def test_rate_error_gets_retry_guidance(self):
        error = SimpleNamespace(code="rate_limit_exceeded", body={})
        message = rate_limit_message(error)
        self.assertIn("等待约一分钟", message)
        self.assertIn("RPM/TPM", message)

    def test_valid_api_key_is_trimmed(self):
        key = "sk-" + ("a" * 30)
        self.assertEqual(validate_api_key(f"  {key}  "), key)

    def test_chinese_api_key_is_rejected_before_http_request(self):
        with self.assertRaisesRegex(ValueError, "包含中文"):
            validate_api_key("你的OpenAI API Key")

    def test_short_api_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "长度明显不足"):
            validate_api_key("sk-test")

    def test_non_openai_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "sk-"):
            validate_api_key("a" * 30)

    def test_every_task_builds_a_prompt(self):
        for task_key in TASKS:
            with self.subTest(task_key=task_key):
                prompt = build_prompt(task_key, "  测试内容  ")
                self.assertIn("测试内容", prompt)
                self.assertNotIn("{user_input}", prompt)

    def test_empty_input_is_rejected(self):
        with self.assertRaises(ValueError):
            build_prompt("summary", "   ")

    def test_unknown_task_is_rejected(self):
        with self.assertRaises(ValueError):
            build_prompt("missing", "测试")

    def test_generate_review_calls_responses_api(self):
        responses = FakeResponses("  合格答案  ")
        client = SimpleNamespace(responses=responses)

        result = generate_review(client, "gpt-5.5", "answer", "简述云计算。")

        self.assertEqual(result, "合格答案")
        self.assertEqual(responses.last_request["model"], "gpt-5.5")
        self.assertIn("简述云计算", responses.last_request["input"])
        self.assertIn("使用中文", responses.last_request["instructions"])

    def test_empty_model_output_is_rejected(self):
        client = SimpleNamespace(responses=FakeResponses(" "))
        with self.assertRaises(RuntimeError):
            generate_review(client, "gpt-5.5", "card", "错题")


if __name__ == "__main__":
    unittest.main()
