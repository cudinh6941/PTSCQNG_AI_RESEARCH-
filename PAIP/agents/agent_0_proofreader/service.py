"""
Agent 0 — Service (Business Logic).

Flow: Nhận text/file → Gọi LLM → Parse kết quả → Trả về structured response.
"""

import json
import re
import time
import unicodedata

from core.common.logger import logger
from core.common.schemas import LLMProvider
from core.document import document_reader
from core.llm import llm_service
from core.rule_engine import RuleContext, rule_engine
from core.rule_engine.base import RuleType
from core.document.format_inspector import docx_format_inspector
from core.scoring import quality_scoring_engine
from core.database.session import db_session
from core.database.models import ProofreadHistory

from .prompts import SYSTEM_PROMPT, build_user_prompt

from .schemas import ErrorType, ProofreadError, ProofreadResponse, ProofreadResult, Severity



class ProofreaderService:
    """Document Proofreader — kiểm tra chính tả, ngữ pháp tiếng Việt."""

    MAX_TEXT_LENGTH = 50_000  # ~50K chars per request

    async def proofread_text(
        self,
        text: str,
        mode: str = "standard",
        custom_instructions: str | None = None,
        provider: LLMProvider | str | None = None,
        model: str | None = None,
        user_id: str | None = None,
        department: str | None = None,
    ) -> ProofreadResponse:
        """
        Kiểm tra chính tả cho đoạn text.

        Args:
            text: Nội dung cần kiểm tra
            mode: Chế độ kiểm tra (standard, formal, strict)
            custom_instructions: Ghi chú thêm từ người dùng
            provider: LLM provider (optional)
            model: Model name (optional)
            user_id: ID người dùng (optional)
            department: Phòng ban (optional)

        Returns:
            ProofreadResponse với danh sách lỗi
        """
        start_time = time.time()

        # Validate
        if not text or not text.strip():
            return ProofreadResponse(
                success=False,
                message="Văn bản trống, không có gì để kiểm tra.",
                processing_time_ms=(time.time() - start_time) * 1000,
            )

        if len(text) > self.MAX_TEXT_LENGTH:
            return ProofreadResponse(
                success=False,
                message=f"Văn bản quá dài ({len(text)} ký tự). Tối đa {self.MAX_TEXT_LENGTH:,} ký tự.",
                processing_time_ms=(time.time() - start_time) * 1000,
            )

        logger.info(f"Proofreading: {len(text)} chars, mode={mode}, user={user_id}, dept={department}")

        # ── BƯỚC 1: Rule Engine Pre-Scan (< 5ms, 0 token) ──
        rule_context = RuleContext(
            text=text,
            mode=mode,
            department=department,
            user_id=user_id,
        )
        rule_result = rule_engine.evaluate(rule_context)

        logger.info(
            f"Rule Engine: {len(rule_result.violations)} violations, "
            f"{len(rule_result.detected_terms)} terms detected, "
            f"{rule_result.processing_time_ms:.1f}ms"
        )

        # ── BƯỚC 2: Build prompt (bơm glossary context + whitelist) ──
        user_prompt = build_user_prompt(
            document_text=text,
            mode=mode,
            custom_instructions=custom_instructions,
            glossary_context=rule_result.prompt_injection,
            whitelist_terms=rule_result.whitelist_terms,
        )

        # Detect if real-time legal grounding / search is needed
        needs_search = mode in ("legal", "strict_legal") or any(
            kw in (custom_instructions or "").lower() for kw in ("luật", "nghị định", "quyết định", "pháp lý", "văn bản quy phạm")
        )

        # Call LLM
        try:
            llm_result = await llm_service.generate(
                prompt=user_prompt,
                system_prompt=SYSTEM_PROMPT,
                provider=provider,
                model=model,
                temperature=0.2,  # Low creativity for high consistency
                max_tokens=8192,
                enable_search=needs_search,
            )
        except Exception as e:
            logger.error(f"Proofread LLM generation error: {e}")
            return ProofreadResponse(
                success=False,
                message=f"Lỗi khi xử lý qua AI: {e}",
                processing_time_ms=(time.time() - start_time) * 1000,
            )

        # Parse response
        result = self._parse_llm_response(llm_result.content)

        # ── BƯỚC 4: Merge kết quả Rule Engine + LLM ──────
        result = self._merge_rule_engine_results(result, rule_result)

        # ── BƯỚC 5: Tính điểm chất lượng 4 Trụ Cột (Scoring Engine) ──
        score_breakdown = quality_scoring_engine.evaluate(
            errors=result.errors,
            format_report=None,
        )
        result.score = score_breakdown.overall_score
        result.score_breakdown = score_breakdown

        processing_time = (time.time() - start_time) * 1000

        # Ghi nhận lịch sử rà soát vào CSDL
        await self._save_history(
            input_type="text",
            filename=None,
            result=result,
            tokens_used=llm_result.total_tokens,
            processing_time_ms=processing_time,
            user_id=user_id,
        )

        return ProofreadResponse(
            success=True,
            message=f"Đã kiểm tra xong. Tìm thấy {result.total_errors} lỗi. Điểm chất lượng: {result.score}/10.",
            result=result,
            extracted_text=text,
            processing_time_ms=processing_time,
            model_used=llm_result.model,
            tokens_used=llm_result.total_tokens,
            estimated_cost_usd=llm_result.estimated_cost_usd,
        )

    async def proofread_file(
        self,
        file_content: bytes,
        filename: str,
        mode: str = "standard",
        custom_instructions: str | None = None,
        provider: LLMProvider | str | None = None,
        model: str | None = None,
        user_id: str | None = None,
        department: str | None = None,
    ) -> ProofreadResponse:
        """
        Kiểm tra chính tả cho file (Word/PDF/Text).

        Args:
            file_content: File content as bytes
            filename: Original filename
            mode: Chế độ kiểm tra (standard, formal, strict)
            custom_instructions: Ghi chú thêm từ người dùng

        Returns:
            ProofreadResponse
        """
        try:
            raw_text = document_reader.read_bytes(file_content, filename)
        except ValueError as e:
            return ProofreadResponse(success=False, message=str(e))
        except Exception as e:
            logger.error(f"Error reading file {filename}: {e}")
            return ProofreadResponse(success=False, message=f"Không đọc được file: {e}")

        # Clean repeated header/footer noise commonly found in PDF/DOCX (e.g. "QN-COM-PR01-FM09\nNHL: 22/12/2025")
        cleaned_text = self._clean_document_text(raw_text)

        response = await self.proofread_text(
            text=cleaned_text,
            mode=mode,
            custom_instructions=custom_instructions,
            provider=provider,
            model=model,
            user_id=user_id,
            department=department,
        )
        response.extracted_text = cleaned_text

        # Tự động quét vi phạm thể thức, căn lề, font chữ nếu là file Word (.docx)
        if filename.lower().endswith(".docx"):
            try:
                response.format_report = docx_format_inspector.inspect(file_content)
                # Tái tính toán điểm số 4 trụ cột kết hợp báo cáo thể thức
                if response.result:
                    score_breakdown = quality_scoring_engine.evaluate(
                        errors=response.result.errors,
                        format_report=response.format_report,
                    )
                    response.result.score = score_breakdown.overall_score
                    response.result.score_breakdown = score_breakdown
                    response.message = f"Đã kiểm tra xong. Tìm thấy {response.result.total_errors} lỗi. Điểm chất lượng: {response.result.score}/10."
                    
                    # Cập nhật lịch sử với thông tin file
                    await self._save_history(
                        input_type="file",
                        filename=filename,
                        result=response.result,
                        tokens_used=response.tokens_used or 0,
                        processing_time_ms=response.processing_time_ms or 0.0,
                        user_id=user_id,
                    )
            except Exception as e:
                logger.error(f"Format inspection error for {filename}: {e}")

        return response


    def _merge_rule_engine_results(
        self,
        llm_result: ProofreadResult,
        rule_result,
    ) -> ProofreadResult:
        """
        Hợp nhất kết quả từ Rule Engine (deterministic) và LLM (AI).

        Quy tắc:
        - Lỗi Rule Engine (source=company_standard) luôn đứng đầu và được phân loại là GLOSSARY.
        - Nếu LLM bắt lỗi cùng một từ mà Rule Engine đã nhận là đúng chuẩn
          (nằm trong whitelist) → Loại bỏ lỗi LLM (False Positive).
        """
        rule_errors: list[ProofreadError] = []
        for violation in rule_result.violations:
            err_type = ErrorType.CONSISTENCY if violation.rule_type.value == "consistency" else ErrorType.GLOSSARY
            prefix = "[Đối soát nhất quán]" if err_type == ErrorType.CONSISTENCY else "[Chuẩn PTSC]"
            rule_errors.append(
                ProofreadError(
                    type=err_type,
                    original=violation.original_text,
                    suggested=violation.suggested_fix,
                    explanation=f"{prefix} {violation.explanation}",
                    severity=Severity.HIGH,
                    side_a=violation.side_a,
                    side_b=violation.side_b,
                )
            )

        # Lọc bỏ False Positive từ LLM (LLM bắt lỗi từ nằm trong whitelist)
        whitelist_set = {t.lower() for t in rule_result.whitelist_terms}
        filtered_llm_errors: list[ProofreadError] = []
        for err in llm_result.errors:
            original_lower = err.original.lower().strip()
            # Nếu LLM bắt lỗi 1 từ nằm trong whitelist → bỏ qua
            if original_lower in whitelist_set:
                logger.debug(
                    f"Filtered LLM false positive: '{err.original}' is in whitelist"
                )
                continue
            filtered_llm_errors.append(err)

        # Merge: Rule Engine errors trước, LLM errors sau
        merged_errors = rule_errors + filtered_llm_errors

        return ProofreadResult(
            total_errors=len(merged_errors),
            errors=merged_errors,
            summary=llm_result.summary,
            score=llm_result.score,
        )


    async def _save_history(
        self,
        input_type: str,
        filename: str | None,
        result: ProofreadResult,
        tokens_used: int,
        processing_time_ms: float,
        user_id: str | None,
    ) -> None:
        """Ghi nhận lịch sử và chỉ số điểm rà soát vào CSDL async."""
        try:
            breakdown = result.score_breakdown
            spelling_score = breakdown.pillars["spelling"].score if breakdown else result.score
            format_score = breakdown.pillars["format"].score if breakdown else 10.0
            glossary_score = breakdown.pillars["glossary"].score if breakdown else 10.0
            consistency_score = breakdown.pillars["consistency"].score if breakdown else 10.0

            async with db_session() as session:
                history = ProofreadHistory(
                    filename=filename,
                    input_type=input_type,
                    overall_score=result.score,
                    spelling_score=spelling_score,
                    format_score=format_score,
                    glossary_score=glossary_score,
                    consistency_score=consistency_score,
                    total_errors=result.total_errors,
                    tokens_used=tokens_used,
                    processing_time_ms=processing_time_ms,
                    user_id=user_id or "anonymous_user",
                )
                session.add(history)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to record proofread history in DB: {e}")



    def _clean_document_text(self, text: str) -> str:
        """Làm sạch các dòng header/footer lặp lại vô nghĩa giữa các trang."""
        # Clean PTSC form headers if repeated
        cleaned = re.sub(r'QN-[A-Z0-9-]+\s*\n\s*NHL:\s*\d{2}/\d{2}/\d{4}\s*\n?', '', text)
        # Normalize excessive newlines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        # Chuẩn hóa Unicode phân mảnh (NFD) thành dựng sẵn (NFC) để Regex chạy đúng
        cleaned = unicodedata.normalize("NFC", cleaned)
        return cleaned.strip()

    def _parse_llm_response(self, content: str) -> ProofreadResult:
        """Parse JSON response từ LLM với regex extraction và fallback an toàn."""
        try:
            raw_json = self._extract_json_block(content)
            data = json.loads(raw_json)

            errors: list[ProofreadError] = []
            for item in data.get("errors", []):
                if isinstance(item, dict):
                    errors.append(self._sanitize_error(item))

            score = data.get("score", 0.0)
            try:
                score = float(score)
            except (ValueError, TypeError):
                score = 0.0

            return ProofreadResult(
                total_errors=data.get("total_errors", len(errors)),
                errors=errors,
                summary=str(data.get("summary", "")),
                score=score,
            )

        except Exception as e:
            logger.warning(f"Direct JSON parse failed: {e}. Attempting chunked object extraction...")
            # Fallback: Extract individual error dicts via regex
            fallback_errors: list[ProofreadError] = []
            for obj_match in re.finditer(r'\{[^{}]*"original"\s*:\s*"[^"]+"[^{}]*\}', content):
                try:
                    obj_dict = json.loads(obj_match.group(0))
                    fallback_errors.append(self._sanitize_error(obj_dict))
                except Exception:
                    pass

            if fallback_errors:
                return ProofreadResult(
                    total_errors=len(fallback_errors),
                    errors=fallback_errors,
                    summary="Đã phân tích và trích xuất danh sách lỗi thành công.",
                    score=round(max(10.0 - (len(fallback_errors) * 0.5), 1.0), 1),
                )

            return ProofreadResult(
                total_errors=0,
                errors=[],
                summary=f"Kết quả phân tích (raw):\n{content[:500]}",
                score=0.0,
            )

    @staticmethod
    def _extract_json_block(content: str) -> str:
        """Trích xuất khối JSON từ output của LLM."""
        text = content.strip()
        # Case 1: fenced code block ```json ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        # Case 2: raw JSON object {...}
        match = re.search(r"(\{[\s\S]*\})", text)
        if match:
            return match.group(1).strip()
        return text

    @staticmethod
    def _sanitize_error(item: dict) -> ProofreadError:
        """Chuẩn hóa thông tin lỗi để tránh crash khi LLM trả về type/severity bất thường."""
        raw_type = str(item.get("type", "spelling")).lower().strip()
        if "legal" in raw_type or "luật" in raw_type or "pháp lý" in raw_type or "quy định" in raw_type:
            err_type = ErrorType.LEGAL
        elif "gram" in raw_type or "ngữ pháp" in raw_type:
            err_type = ErrorType.GRAMMAR
        elif "punct" in raw_type or "dấu" in raw_type:
            err_type = ErrorType.PUNCTUATION
        elif "word" in raw_type or "từ" in raw_type:
            err_type = ErrorType.WORD_CHOICE
        elif "consist" in raw_type or "nhất quán" in raw_type or "bất nhất" in raw_type or "đối soát" in raw_type:
            err_type = ErrorType.CONSISTENCY
        else:
            err_type = ErrorType.SPELLING

        raw_sev = str(item.get("severity", "medium")).lower().strip()
        if raw_sev in ("high", "cao", "critical"):
            severity = Severity.HIGH
        elif raw_sev in ("low", "thấp", "minor"):
            severity = Severity.LOW
        else:
            severity = Severity.MEDIUM

        return ProofreadError(
            type=err_type,
            original=str(item.get("original", "")),
            suggested=str(item.get("suggested", item.get("suggestion", ""))),
            explanation=str(item.get("explanation", "")),
            severity=severity,
            source_link=str(item["source_link"]).strip() if item.get("source_link") else None,
            reference=str(item["reference"]).strip() if item.get("reference") else None,
        )


# Singleton instance
proofreader_service = ProofreaderService()

