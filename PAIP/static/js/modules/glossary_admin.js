/**
 * PAIP Glossary Management Admin Module
 */

import { $, $$, escapeHtml } from '../utils/dom.js';
import { showToast } from '../utils/toast.js';

export const glossaryAdmin = {
  editMode: null,
  debounceTimer: null,

  init() {
    this.bindEvents();
    // Expose global handlers for row action buttons
    window._glossaryEdit = (term) => this.handleEdit(term);
    window._glossaryDelete = (term) => this.handleDelete(term);
  },

  bindEvents() {
    const glossarySearchInput = $('#glossarySearchInput');
    const glossaryDomainFilter = $('#glossaryDomainFilter');
    const btnAddTerm = $('#btnAddTerm');
    const btnReloadRules = $('#btnReloadRules');
    const btnTestRules = $('#btnTestRules');
    const btnModalCancel = $('#btnModalCancel');
    const btnModalClose = $('#btnModalClose');
    const btnModalSave = $('#btnModalSave');

    if (glossarySearchInput) {
      glossarySearchInput.addEventListener('input', () => {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => this.loadData(), 300);
      });
    }

    if (glossaryDomainFilter) {
      glossaryDomainFilter.addEventListener('change', () => this.loadData());
    }

    if (btnAddTerm) {
      btnAddTerm.addEventListener('click', () => this.openModal('add'));
    }

    if (btnModalCancel) btnModalCancel.addEventListener('click', () => this.closeModal());
    if (btnModalClose) btnModalClose.addEventListener('click', () => this.closeModal());

    if (btnModalSave) {
      btnModalSave.addEventListener('click', () => this.handleSave());
    }

    if (btnReloadRules) {
      btnReloadRules.addEventListener('click', () => this.handleReload());
    }

    if (btnTestRules) {
      btnTestRules.addEventListener('click', () => this.handleTest());
    }
  },

  async loadData() {
    const searchInput = $('#glossarySearchInput');
    const domainFilter = $('#glossaryDomainFilter');
    const tableBody = $('#glossaryTableBody');
    const totalCount = $('#glossaryTotalCount');

    const query = searchInput ? searchInput.value.trim() : '';
    const domain = domainFilter ? domainFilter.value : '';

    let url = '/api/v1/rules/glossary?';
    if (query) url += `query=${encodeURIComponent(query)}&`;
    if (domain) url += `domain=${encodeURIComponent(domain)}&`;

    try {
      const res = await fetch(url);
      const data = await res.json();
      this.renderTable(data.items || []);
      if (totalCount) totalCount.textContent = `${data.total || 0} thuật ngữ`;
    } catch (e) {
      if (tableBody) {
        tableBody.innerHTML = `<tr class="glossary-empty-row"><td colspan="5"><div class="glossary-empty-state"><span>⚠️</span><p>Lỗi tải dữ liệu</p></div></td></tr>`;
      }
    }
  },

  renderTable(items) {
    const tableBody = $('#glossaryTableBody');
    if (!tableBody) return;

    if (!items.length) {
      tableBody.innerHTML = `<tr class="glossary-empty-row"><td colspan="5"><div class="glossary-empty-state"><span>📚</span><p>Không tìm thấy thuật ngữ nào</p></div></td></tr>`;
      return;
    }

    tableBody.innerHTML = items.map(item => `
      <tr>
        <td class="glossary-term-cell">${escapeHtml(item.term)}</td>
        <td class="glossary-fullname-cell" title="${escapeHtml(item.full_name_vi || '')}">
          ${escapeHtml(item.full_name_vi || item.full_name_en || '—')}
        </td>
        <td><span class="glossary-domain-badge" data-domain="${escapeHtml(item.domain)}">${escapeHtml(item.domain)}</span></td>
        <td class="glossary-variants-cell" title="${escapeHtml((item.incorrect_variants || []).join(', '))}">
          ${(item.incorrect_variants || []).slice(0, 3).map(v => escapeHtml(v)).join(', ') || '—'}
        </td>
        <td class="glossary-actions-cell">
          <button onclick="window._glossaryEdit('${escapeHtml(item.term)}')">✏️</button>
          <button class="btn-delete" onclick="window._glossaryDelete('${escapeHtml(item.term)}')">🗑️</button>
        </td>
      </tr>
    `).join('');
  },

  async loadStats() {
    const statTotalTerms = $('#statTotalTerms');
    const statTotalDomains = $('#statTotalDomains');
    const statsDomainBreakdown = $('#statsDomainBreakdown');
    const glossaryDomainFilter = $('#glossaryDomainFilter');

    try {
      const res = await fetch('/api/v1/rules/stats');
      const data = await res.json();
      if (statTotalTerms) statTotalTerms.textContent = data.total_glossary_terms || 0;
      const domains = data.domains || {};
      const domainKeys = Object.keys(domains);
      if (statTotalDomains) statTotalDomains.textContent = domainKeys.length;

      if (statsDomainBreakdown) {
        statsDomainBreakdown.innerHTML = domainKeys.map(d =>
          `<span class="glossary-domain-badge" data-domain="${escapeHtml(d)}">${escapeHtml(d)} (${domains[d]})</span>`
        ).join('');
      }

      if (glossaryDomainFilter) {
        const currentVal = glossaryDomainFilter.value;
        glossaryDomainFilter.innerHTML = '<option value="">Tất cả lĩnh vực</option>' +
          domainKeys.sort().map(d => `<option value="${escapeHtml(d)}">${escapeHtml(d)}</option>`).join('');
        glossaryDomainFilter.value = currentVal;
      }
    } catch (e) {
      // Silently ignore
    }
  },

  async handleReload() {
    const btn = $('#btnReloadRules');
    if (btn) {
      btn.disabled = true;
      btn.textContent = '⏳ Đang nạp...';
    }
    try {
      const res = await fetch('/api/v1/rules/reload', { method: 'POST' });
      const data = await res.json();
      showToast(`✅ ${data.message} (${data.glossary_count} thuật ngữ, ${data.reload_time_ms}ms)`, 'success');
      this.loadData();
      this.loadStats();
    } catch (e) {
      showToast('❌ Lỗi reload Rule Engine', 'error');
    }
    if (btn) {
      btn.disabled = false;
      btn.textContent = '🔄 Đồng Bộ';
    }
  },

  async handleTest() {
    const testInput = $('#glossaryTestInput');
    const testResult = $('#glossaryTestResult');
    const btn = $('#btnTestRules');

    const text = testInput ? testInput.value.trim() : '';
    if (!text) return;

    if (btn) {
      btn.disabled = true;
      btn.textContent = '⏳ Đang kiểm tra...';
    }

    try {
      const res = await fetch('/api/v1/rules/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      if (testResult) {
        testResult.style.display = 'block';
        if (data.violations && data.violations.length > 0) {
          testResult.innerHTML = data.violations.map(v => `
            <div class="test-violation-item">
              <span class="test-violation-original">${escapeHtml(v.original_text)}</span>
              <span class="test-violation-arrow">➔</span>
              <span class="test-violation-fix">${escapeHtml(v.suggested_fix)}</span>
            </div>
          `).join('') + `<div class="test-processing-time">⚡ ${data.processing_time_ms}ms</div>`;
        } else {
          testResult.innerHTML = `<div class="test-no-issues">✅ Không phát hiện vi phạm quy chuẩn</div><div class="test-processing-time">⚡ ${data.processing_time_ms}ms</div>`;
        }
      }
    } catch (e) {
      if (testResult) {
        testResult.style.display = 'block';
        testResult.innerHTML = `<div style="color: #ef4444;">❌ Lỗi kiểm tra</div>`;
      }
    }

    if (btn) {
      btn.disabled = false;
      btn.textContent = '⚡ Kiểm Tra';
    }
  },

  openModal(mode = 'add', termData = null) {
    this.editMode = mode === 'edit' ? termData.term : null;
    const modal = $('#glossaryModal');
    const title = $('#modalTitle');
    const termInput = $('#modalTermInput');
    const domainInput = $('#modalDomainInput');
    const fullNameVi = $('#modalFullNameVi');
    const fullNameEn = $('#modalFullNameEn');
    const variantsInput = $('#modalVariantsInput');
    const descInput = $('#modalDescInput');
    const doNotTranslate = $('#modalDoNotTranslate');

    if (!modal) return;

    if (title) title.textContent = mode === 'edit' ? '✏️ Chỉnh Sửa Thuật Ngữ' : '➕ Thêm Thuật Ngữ Mới';
    if (termInput) {
      termInput.value = termData ? termData.term : '';
      termInput.disabled = mode === 'edit';
    }
    if (domainInput) domainInput.value = termData ? (termData.domain || '') : '';
    if (fullNameVi) fullNameVi.value = termData ? (termData.full_name_vi || '') : '';
    if (fullNameEn) fullNameEn.value = termData ? (termData.full_name_en || '') : '';
    if (variantsInput) variantsInput.value = termData ? (termData.incorrect_variants || []).join(', ') : '';
    if (descInput) descInput.value = termData ? (termData.description || '') : '';
    if (doNotTranslate) doNotTranslate.checked = termData ? !!termData.do_not_translate : false;

    modal.style.display = 'flex';
  },

  closeModal() {
    const modal = $('#glossaryModal');
    if (modal) modal.style.display = 'none';
    this.editMode = null;
  },

  async handleSave() {
    const termInput = $('#modalTermInput');
    const domainInput = $('#modalDomainInput');
    const fullNameVi = $('#modalFullNameVi');
    const fullNameEn = $('#modalFullNameEn');
    const variantsInput = $('#modalVariantsInput');
    const descInput = $('#modalDescInput');
    const doNotTranslate = $('#modalDoNotTranslate');
    const btnSave = $('#btnModalSave');

    const term = termInput ? termInput.value.trim() : '';
    if (!term) {
      showToast('⚠️ Vui lòng nhập thuật ngữ chuẩn', 'warning');
      return;
    }

    const variants = variantsInput ? variantsInput.value.split(',').map(v => v.trim()).filter(Boolean) : [];

    const payload = {
      term,
      domain: domainInput ? domainInput.value.trim() || 'General' : 'General',
      full_name_vi: fullNameVi ? fullNameVi.value.trim() : '',
      full_name_en: fullNameEn ? fullNameEn.value.trim() : '',
      incorrect_variants: variants,
      description: descInput ? descInput.value.trim() : '',
      do_not_translate: doNotTranslate ? doNotTranslate.checked : false,
    };

    if (btnSave) btnSave.disabled = true;

    try {
      let res;
      if (this.editMode) {
        res = await fetch(`/api/v1/rules/glossary/${encodeURIComponent(this.editMode)}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      } else {
        res = await fetch('/api/v1/rules/glossary', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      }

      const data = await res.json();
      if (res.ok) {
        showToast(`✅ ${data.message}`, 'success');
        this.closeModal();
        this.loadData();
        this.loadStats();
      } else {
        showToast(`⚠️ ${data.detail || 'Lỗi lưu thuật ngữ'}`, 'warning');
      }
    } catch (e) {
      showToast('❌ Lỗi kết nối server', 'error');
    }

    if (btnSave) btnSave.disabled = false;
  },

  async handleEdit(term) {
    try {
      const res = await fetch(`/api/v1/rules/glossary/${encodeURIComponent(term)}`);
      if (res.ok) {
        const data = await res.json();
        this.openModal('edit', data);
      }
    } catch (e) {
      showToast('Lỗi tải thông tin thuật ngữ', 'error');
    }
  },

  async handleDelete(term) {
    if (!confirm(`Xóa thuật ngữ "${term}" khỏi kho từ điển?`)) return;
    try {
      const res = await fetch(`/api/v1/rules/glossary/${encodeURIComponent(term)}`, { method: 'DELETE' });
      const data = await res.json();
      if (res.ok) {
        showToast(`✅ ${data.message}`, 'success');
        this.loadData();
        this.loadStats();
      } else {
        showToast(`⚠️ ${data.detail || 'Lỗi xóa'}`, 'warning');
      }
    } catch (e) {
      showToast('❌ Lỗi kết nối server', 'error');
    }
  }
};
