/**
 * PAIP Backend API Client
 */

export const api = {
  /**
   * Proofread plain text
   */
  async proofreadText({ text, mode, model, customInstructions }) {
    const res = await fetch('/api/v1/proofread', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        mode: mode || 'standard',
        model_name: model || 'gemini:gemini-2.5-flash',
        custom_instructions: customInstructions || null
      })
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Lỗi máy chủ (${res.status})`);
    }
    return await res.json();
  },

  /**
   * Proofread uploaded file (.docx / .pdf / .txt)
   */
  async proofreadFile({ file, mode, model, customInstructions }) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', mode || 'standard');
    formData.append('model_name', model || 'gemini:gemini-2.5-flash');
    if (customInstructions) {
      formData.append('custom_instructions', customInstructions);
    }

    const res = await fetch('/api/v1/proofread/file', {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Lỗi máy chủ (${res.status})`);
    }
    return await res.json();
  },

  /**
   * Export corrected document to Word (.docx)
   */
  async exportDocx({ originalText, errors, filename }) {
    const res = await fetch('/api/v1/export/docx', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        original_text: originalText,
        errors: errors || [],
        output_filename: filename || 'PAIP_Document_Corrected.docx'
      })
    });
    if (!res.ok) {
      throw new Error(`Lỗi xuất file Word (${res.status})`);
    }
    return await res.blob();
  },

  /**
   * 1-Click Auto-Format Word document according to Decree 30 / PTSC
   */
  async autoFormatDocx(file) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch('/api/v1/format/auto-format', {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Lỗi chuẩn hóa file Word (${res.status})`);
    }
    return await res.blob();
  },

  /**
   * Inspect document format
   */
  async inspectFormat(file) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch('/api/v1/format/inspect', {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Lỗi kiểm tra định dạng (${res.status})`);
    }
    return await res.json();
  },

  /**
   * Glossary API endpoints
   */
  async getGlossaryTerms(domain = '', search = '') {
    const params = new URLSearchParams();
    if (domain) params.set('domain', domain);
    if (search) params.set('search', search);
    params.set('page_size', '100');

    const res = await fetch(`/api/v1/rules/dictionary?${params.toString()}`);
    if (!res.ok) throw new Error('Không thể tải danh sách từ điển');
    return await res.json();
  },

  async createGlossaryTerm(termData) {
    const res = await fetch('/api/v1/rules/dictionary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(termData)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Lỗi thêm từ điển');
    }
    return await res.json();
  },

  async updateGlossaryTerm(termId, termData) {
    const res = await fetch(`/api/v1/rules/dictionary/${termId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(termData)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Lỗi cập nhật từ điển');
    }
    return await res.json();
  },

  async deleteGlossaryTerm(termId) {
    const res = await fetch(`/api/v1/rules/dictionary/${termId}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error('Lỗi xóa từ điển');
    return await res.json();
  },

  async testGlossaryText(text, domain = '') {
    const res = await fetch('/api/v1/rules/dictionary/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, domain: domain || null })
    });
    if (!res.ok) throw new Error('Lỗi kiểm tra quy tắc');
    return await res.json();
  }
};
