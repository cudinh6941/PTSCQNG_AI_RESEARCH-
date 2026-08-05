"""
PAIP Document Reader — đọc nội dung từ Word, PDF, Text files.

Xây từ Agent 0, dùng chung cho tất cả agents sau.

Usage:
    from core.document import document_reader

    text = document_reader.read("path/to/file.docx")
    text = document_reader.read("path/to/file.pdf")
"""

from pathlib import Path

from core.common.logger import logger


class DocumentReader:
    """Đọc nội dung text từ các định dạng file phổ biến."""

    SUPPORTED_EXTENSIONS = {".docx", ".pdf", ".txt", ".md"}

    def read(self, file_path: str | Path) -> str:
        """
        Đọc nội dung text từ file.

        Args:
            file_path: Đường dẫn tới file

        Returns:
            Nội dung text của file

        Raises:
            ValueError: Nếu file extension không được hỗ trợ
            FileNotFoundError: Nếu file không tồn tại
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File không tồn tại: {path}")

        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"File extension '{ext}' không được hỗ trợ. "
                f"Hỗ trợ: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

        logger.info(f"Reading document: {path.name} ({ext})")

        if ext == ".docx":
            return self._read_docx(path)
        elif ext == ".pdf":
            return self._read_pdf(path)
        elif ext in (".txt", ".md"):
            return self._read_text(path)
        else:
            raise ValueError(f"Unsupported: {ext}")

    def read_bytes(self, content: bytes, filename: str) -> str:
        """
        Đọc nội dung từ bytes (upload file qua API).

        Args:
            content: File content as bytes
            filename: Original filename (để xác định format)

        Returns:
            Nội dung text
        """
        import tempfile

        ext = Path(filename).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"File extension '{ext}' không được hỗ trợ. "
                f"Hỗ trợ: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

        # Write to temp file then read
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            return self.read(tmp_path)
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Could not delete temp file {tmp_path}: {e}")

    # ── Format-specific Readers ───────────────────────────

    def _read_docx(self, path: Path) -> str:
        """Đọc file Word (.docx) bao gồm cả paragraphs và bảng biểu (tables)."""
        from docx import Document

        doc = Document(str(path))
        lines = []

        # Read paragraphs
        for p in doc.paragraphs:
            t = p.text.strip()
            if t:
                lines.append(t)

        # Read tables (rất phổ biến trong văn bản PTSC)
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                # Deduplicate identical adjacent cells (due to merged cells)
                deduped = []
                for cell_text in row_cells:
                    if not deduped or cell_text != deduped[-1]:
                        deduped.append(cell_text)
                if deduped:
                    lines.append(" | ".join(deduped))

        text = "\n".join(lines)
        logger.debug(f"DOCX: {len(lines)} elements, {len(text)} chars")
        return text

    def _read_pdf(self, path: Path) -> str:
        """Đọc file PDF bằng pdfplumber."""
        import pdfplumber

        pages_text = []
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    pages_text.append(page_text.strip())

        text = "\n\n".join(pages_text)
        logger.debug(f"PDF: {len(pages_text)} pages, {len(text)} chars")
        return text

    def _read_text(self, path: Path) -> str:
        """Đọc file text/markdown hỗ trợ đa dạng encoding (UTF-8, UTF-8-SIG, Latin-1 fallback)."""
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                text = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                text = path.read_text(encoding="latin-1", errors="replace")

        logger.debug(f"TXT: {len(text)} chars")
        return text


# Singleton instance
document_reader = DocumentReader()

