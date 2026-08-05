"""
PAIP LLM Service — Vendor-agnostic AI model router.

Hỗ trợ: OpenAI, Google Gemini, Anthropic Claude.
Có thể switch provider mà không đổi business logic.

Usage:
    from core.llm import llm_service

    result = await llm_service.generate(
        prompt="Kiểm tra chính tả đoạn văn sau...",
        system_prompt="Bạn là chuyên gia kiểm tra chính tả tiếng Việt.",
        provider=LLMProvider.OPENAI,  # optional, dùng default nếu không chỉ định
    )
"""

import asyncio
import json
import time
from dataclasses import dataclass

from core.common.config import settings
from core.common.logger import logger
from core.common.schemas import LLMProvider


@dataclass
class LLMResult:
    """Kết quả trả về từ LLM."""
    content: str
    model: str
    provider: LLMProvider
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0


# Approximate pricing per 1M tokens (input/output in USD)
MODEL_PRICING: dict[str, dict[str, float]] = {
    # OpenAI
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    # Gemini
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    # Claude
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-haiku-3-5": {"input": 0.80, "output": 4.00},
}


class LLMService:
    """Vendor-agnostic LLM service with model routing."""

    def __init__(self) -> None:
        self._openai_client = None
        self._gemini_client = None
        self._anthropic_client = None

    # ── Client Initialization (Lazy) ──────────────────────

    def _get_openai_client(self):
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY chưa được cấu hình. Vui lòng thiết lập trong file .env"
            )
        if self._openai_client is None:
            from openai import AsyncOpenAI
            self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._openai_client

    def _get_gemini_client(self):
        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY chưa được cấu hình. Vui lòng thiết lập trong file .env"
            )
        if self._gemini_client is None:
            from google import genai
            self._gemini_client = genai.Client(api_key=settings.google_api_key)
        return self._gemini_client

    def _get_anthropic_client(self):
        if not settings.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY chưa được cấu hình. Vui lòng thiết lập trong file .env"
            )
        if self._anthropic_client is None:
            from anthropic import AsyncAnthropic
            self._anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._anthropic_client

    # ── Main Generate Method ──────────────────────────────

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        provider: LLMProvider | str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 8192,
        response_mime_type: str | None = None,
    ) -> LLMResult:
        """
        Gọi LLM để generate text.

        Args:
            prompt: User prompt
            system_prompt: System instruction
            provider: LLM provider (default từ settings)
            model: Model name (default từ settings theo provider)
            temperature: Creativity level (0-1)
            max_tokens: Max output tokens

        Returns:
            LLMResult với content, token counts, cost estimate
        """
        # Normalize provider
        if provider is None:
            provider = LLMProvider(settings.default_llm_provider.lower())
        elif isinstance(provider, str):
            provider = LLMProvider(provider.lower())

        # Auto-fallback to MOCK if API key is not configured
        if provider == LLMProvider.OPENAI and (not settings.openai_api_key or "your-key" in settings.openai_api_key):
            logger.warning("[MOCK MODE] OpenAI API key chưa cấu hình. Tự động chuyển sang Mock LLM để demo test!")
            provider = LLMProvider.MOCK
        elif provider == LLMProvider.GEMINI and (not settings.google_api_key or "your-key" in settings.google_api_key):
            logger.warning("[MOCK MODE] Google Gemini API key chưa cấu hình. Tự động chuyển sang Mock LLM để demo test!")
            provider = LLMProvider.MOCK
        elif provider == LLMProvider.CLAUDE and (not settings.anthropic_api_key or "your-key" in settings.anthropic_api_key):
            logger.warning("[MOCK MODE] Anthropic Claude API key chưa cấu hình. Tự động chuyển sang Mock LLM để demo test!")
            provider = LLMProvider.MOCK

        if not model or str(model).strip().lower() in ("", "string", "null", "none"):
            model = self._get_default_model(provider)
        else:
            model = str(model).strip()

        logger.info(f"LLM Request: provider={provider.value}, model={model}")
        start_time = time.time()

        max_retries = 3
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                # Route to correct provider
                if provider == LLMProvider.MOCK:
                    result = await self._call_mock(prompt, system_prompt, model, temperature, max_tokens)
                elif provider == LLMProvider.OPENAI:
                    result = await self._call_openai(prompt, system_prompt, model, temperature, max_tokens)
                elif provider == LLMProvider.GEMINI:
                    result = await self._call_gemini(prompt, system_prompt, model, temperature, max_tokens)
                elif provider == LLMProvider.CLAUDE:
                    result = await self._call_claude(prompt, system_prompt, model, temperature, max_tokens)
                else:
                    raise ValueError(f"Unsupported provider: {provider}")

                # Calculate metrics
                result.latency_ms = (time.time() - start_time) * 1000
                result.estimated_cost_usd = self._estimate_cost(
                    model, result.input_tokens, result.output_tokens
                )

                logger.info(
                    f"LLM Response: tokens={result.total_tokens}, "
                    f"latency={result.latency_ms:.0f}ms, "
                    f"cost=${result.estimated_cost_usd:.4f}"
                )
                return result

            except Exception as e:
                last_error = e
                err_str = str(e)
                # Check for transient errors that warrant retry
                is_transient = any(code in err_str for code in ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "RateLimitError", "ConnectError", "Timeout"))
                if is_transient and attempt < max_retries:
                    wait_sec = attempt * 1.5
                    logger.warning(f"LLM Transient Error ({provider.value}/{model}) on attempt {attempt}/{max_retries}: {e}. Retrying in {wait_sec}s...")
                    await asyncio.sleep(wait_sec)
                else:
                    logger.error(f"LLM Error ({provider.value}/{model}) after {attempt} attempt(s): {e}")
                    raise last_error

        if last_error:
            raise last_error
        raise RuntimeError(f"LLM generation failed for provider {provider.value}")

    # ── Provider-specific Calls ───────────────────────────

    async def _call_openai(
        self, prompt: str, system_prompt: str, model: str,
        temperature: float, max_tokens: int,
    ) -> LLMResult:
        client = self._get_openai_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choices = getattr(response, "choices", []) or []
        choice = choices[0] if len(choices) > 0 else None
        content = ""
        if choice and getattr(choice, "message", None):
            content = choice.message.content or ""

        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0) if usage else 0
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0) if usage else 0

        return LLMResult(
            content=content,
            model=model,
            provider=LLMProvider.OPENAI,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

    async def _call_gemini(
        self, prompt: str, system_prompt: str, model: str,
        temperature: float, max_tokens: int,
    ) -> LLMResult:
        client = self._get_gemini_client()

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n---\n\n{prompt}"

        response = await client.aio.models.generate_content(
            model=model,
            contents=full_prompt,
            config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "response_mime_type": "application/json",
                "thinking_config": {"thinking_budget": 0},
            },
        )

        content = ""
        try:
            content = getattr(response, "text", "") or ""
        except Exception:
            candidates = getattr(response, "candidates", None)
            if candidates and len(candidates) > 0:
                first_cand = candidates[0]
                cand_content = getattr(first_cand, "content", None)
                if cand_content:
                    parts = getattr(cand_content, "parts", None)
                    if parts and len(parts) > 0:
                        content = getattr(parts[0], "text", "") or ""

        input_tokens = 0
        output_tokens = 0
        usage_meta = getattr(response, "usage_metadata", None)
        if usage_meta:
            input_tokens = int(getattr(usage_meta, "prompt_token_count", 0) or 0)
            output_tokens = int(getattr(usage_meta, "candidates_token_count", 0) or 0)

        return LLMResult(
            content=content,
            model=model,
            provider=LLMProvider.GEMINI,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

    async def _call_claude(
        self, prompt: str, system_prompt: str, model: str,
        temperature: float, max_tokens: int,
    ) -> LLMResult:
        client = self._get_anthropic_client()

        kwargs = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await client.messages.create(**kwargs)

        content_parts = []
        raw_blocks = getattr(response, "content", []) or []
        for block in raw_blocks:
            if hasattr(block, "text"):
                content_parts.append(getattr(block, "text", ""))
            elif getattr(block, "type", None) == "text":
                content_parts.append(getattr(block, "text", ""))

        content = "".join(content_parts)

        input_tokens = 0
        output_tokens = 0
        usage = getattr(response, "usage", None)
        if usage:
            input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
            output_tokens = int(getattr(usage, "output_tokens", 0) or 0)

        return LLMResult(
            content=content,
            model=model,
            provider=LLMProvider.CLAUDE,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

    async def _call_mock(
        self, prompt: str, system_prompt: str, model: str,
        temperature: float, max_tokens: int,
    ) -> LLMResult:
        """Mock LLM response để test offline ngay lập tức khi chưa có API key."""
        await asyncio.sleep(0.3)  # Giả lập độ trễ mạng nhanh

        errors = []
        lower_prompt = prompt.lower()
        if "bổ xung" in lower_prompt:
            errors.append({
                "original": "bổ xung",
                "suggestion": "bổ sung",
                "type": "spelling",
                "severity": "high",
                "explanation": "Từ đúng chính tả tiếng Việt trong văn bản hành chính là 'bổ sung' (âm 's').",
                "context": "...bổ xung..."
            })
        if "sắp sếp" in lower_prompt or "xắp xếp" in lower_prompt:
            errors.append({
                "original": "sắp sếp" if "sắp sếp" in lower_prompt else "xắp xếp",
                "suggestion": "sắp xếp",
                "type": "spelling",
                "severity": "medium",
                "explanation": "Từ chuẩn chính tả tiếng Việt là 'sắp xếp' (âm 's' và 'x').",
                "context": "...sắp xếp..."
            })
        if "xử lí" in lower_prompt:
            errors.append({
                "original": "xử lí",
                "suggestion": "xử lý",
                "type": "spelling",
                "severity": "low",
                "explanation": "Theo quy chuẩn chính tả tiếng Việt hành chính hiện hành, nên dùng 'xử lý' (y dài).",
                "context": "...xử lí..."
            })

        if not errors:
            errors = [
                {
                    "original": "căn cứ theo",
                    "suggestion": "Căn cứ",
                    "type": "word_choice",
                    "severity": "low",
                    "explanation": "Trong thể thức văn bản hành chính công văn, nên mở đầu ngắn gọn bằng 'Căn cứ...' thay vì 'căn cứ theo'.",
                    "context": "...căn cứ theo..."
                }
            ]

        score = round(max(5.0, 10.0 - len(errors) * 1.0), 1)
        mock_data = {
            "total_errors": len(errors),
            "errors": errors,
            "summary": f"[MOCK DEMO] Đã rà soát văn bản thành công trong chế độ Offline Test. Phát hiện {len(errors)} điểm cần lưu ý và chuẩn hóa.",
            "score": score,
        }

        mock_content = f"```json\n{json.dumps(mock_data, ensure_ascii=False, indent=2)}\n```"
        return LLMResult(
            content=mock_content,
            model=model or "mock-demo-ai",
            provider=LLMProvider.MOCK,
            input_tokens=120,
            output_tokens=180,
            total_tokens=300,
        )

    # ── Helpers ───────────────────────────────────────────

    def _get_default_model(self, provider: LLMProvider) -> str:
        mapping = {
            LLMProvider.OPENAI: settings.openai_default_model,
            LLMProvider.GEMINI: settings.gemini_default_model,
            LLMProvider.CLAUDE: settings.claude_default_model,
            LLMProvider.MOCK: "mock-demo-ai",
        }
        return mapping.get(provider, "mock-demo-ai")

    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
        inp = (input_tokens or 0) / 1_000_000 * pricing.get("input", 0.0)
        out = (output_tokens or 0) / 1_000_000 * pricing.get("output", 0.0)
        return round(inp + out, 6)


# Singleton instance — import này để dùng
llm_service = LLMService()

