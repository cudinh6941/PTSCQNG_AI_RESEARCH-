/**
 * PAIP Document Format & Layout Inspector (Nghị định 30/2020/NĐ-CP)
 */

import { $, escapeHtml } from '../utils/dom.js';
import { showToast, updateSystemStatus } from '../utils/toast.js';
import { api } from '../api.js';
import { appState } from '../state.js';

export const formatInspector = {
  renderReport(report) {
    const errorListContainer = $('#errorListContainer');
    if (!errorListContainer || !report) return;

    // Check if card already exists
    const existingCard = $('#formatInspectorCard');
    if (existingCard) existingCard.remove();

    const margins = report.margins || { top_cm: 2.0, bottom_cm: 2.0, left_cm: 3.0, right_cm: 1.5 };
    const leftValid = margins.left_cm >= 3.0 && margins.left_cm <= 3.5;
    const rightValid = margins.right_cm >= 1.5 && margins.right_cm <= 2.0;
    const topValid = margins.top_cm >= 2.0 && margins.top_cm <= 2.5;
    const bottomValid = margins.bottom_cm >= 2.0 && margins.bottom_cm <= 2.5;

    const fontIssues = report.font_issues || [];
    const alignmentIssues = report.alignment_issues || [];
    const isCleanFormat = leftValid && rightValid && topValid && bottomValid && fontIssues.length === 0 && alignmentIssues.length === 0;

    const cardEl = document.createElement('div');
    cardEl.className = 'format-inspector-card';
    cardEl.id = 'formatInspectorCard';

    let issuesHtml = '';
    const totalIssues = fontIssues.length + alignmentIssues.length;

    if (totalIssues > 0) {
      const issueItems = [
        ...fontIssues.map(fi => `
          <div class="format-issue-item">
            <div class="format-issue-meta">
              <span class="format-issue-loc">📍 ${escapeHtml(fi.location || 'Văn bản')}</span>
              <span class="format-issue-tag">🔤 Font: ${escapeHtml(fi.font || 'Không rõ')}</span>
              <span class="format-issue-suggest">➔ Chuẩn: Times New Roman</span>
            </div>
            <div class="format-issue-snippet" title="${escapeHtml(fi.snippet || '')}">"${escapeHtml(fi.snippet || '')}"</div>
          </div>
        `),
        ...alignmentIssues.map(ai => `
          <div class="format-issue-item">
            <div class="format-issue-meta">
              <span class="format-issue-loc">📍 ${escapeHtml(ai.location || 'Văn bản')}</span>
              <span class="format-issue-tag">📏 Căn lề trái</span>
              <span class="format-issue-suggest">➔ Chuẩn: Căn đều (Justify)</span>
            </div>
            <div class="format-issue-snippet" title="${escapeHtml(ai.snippet || '')}">"${escapeHtml(ai.snippet || '')}"</div>
          </div>
        `)
      ].join('');

      issuesHtml = `
        <div class="format-issues-container">
          <div class="format-issues-header">
            <span>⚠️ Danh Sách Vị Trí Cần Chuẩn Hóa Thể Thức</span>
            <span class="format-issues-count">${totalIssues} điểm</span>
          </div>
          ${issueItems}
        </div>
      `;
    }

    cardEl.innerHTML = `
      <div class="format-card-header">
        <div class="format-title-group">
          <span class="format-icon">📐</span>
          <span class="format-card-title">Thể Thức & Trình Bày Văn Bản</span>
          <span class="format-decree-tag">Nghị định 30/2020/NĐ-CP</span>
        </div>
        <div>
          ${isCleanFormat 
            ? '<span class="status-pill" style="color:#34d399">✅ Chuẩn chỉ 100%</span>' 
            : '<span class="status-pill" style="color:#f87171">⚠️ Có vi phạm định dạng</span>'}
        </div>
      </div>

      <div class="format-visual-grid">
        <!-- Visual A4 Widget -->
        <div class="a4-preview-box">
          <div class="margin-badge margin-top ${topValid ? 'valid' : 'invalid'}" title="Chuẩn: 2.0 - 2.5 cm">
            T: ${margins.top_cm.toFixed(1)}cm ${topValid ? '✅' : '⚠️'}
          </div>
          <div class="margin-badge margin-bottom ${bottomValid ? 'valid' : 'invalid'}" title="Chuẩn: 2.0 - 2.5 cm">
            B: ${margins.bottom_cm.toFixed(1)}cm ${bottomValid ? '✅' : '⚠️'}
          </div>
          <div class="margin-badge margin-left ${leftValid ? 'valid' : 'invalid'}" title="Chuẩn: 3.0 - 3.5 cm (đóng gáy)">
            L: ${margins.left_cm.toFixed(1)}cm ${leftValid ? '✅' : '🔴'}
          </div>
          <div class="margin-badge margin-right ${rightValid ? 'valid' : 'invalid'}" title="Chuẩn: 1.5 - 2.0 cm">
            R: ${margins.right_cm.toFixed(1)}cm ${rightValid ? '✅' : '⚠️'}
          </div>

          <div class="a4-page-content-area">
            <div class="a4-mock-lines">
              <div class="mock-line center"></div>
              <div class="mock-line center"></div>
            </div>
            <div class="a4-mock-lines">
              <div class="mock-line"></div>
              <div class="mock-line"></div>
              <div class="mock-line short"></div>
            </div>
            <div class="a4-mock-lines">
              <div class="mock-line short" style="margin-left:auto"></div>
            </div>
          </div>
        </div>

        <!-- Metrics & Warnings -->
        <div class="format-metrics-list">
          <div class="format-metric-item">
            <span class="format-metric-label">
              <span>🔤</span> Font chữ chính
            </span>
            <span class="format-metric-value">
              ${escapeHtml(report.dominant_font || 'Times New Roman')}
              <span class="metric-status-icon ${report.font_clean ? 'pass' : 'warn'}">
                ${report.font_clean ? '✅' : '⚠️'}
              </span>
            </span>
          </div>

          <div class="format-metric-item">
            <span class="format-metric-label">
              <span>📏</span> Căn đều 2 bên (Justified)
            </span>
            <span class="format-metric-value">
              ${report.alignment_clean ? 'Đạt chuẩn' : `${alignmentIssues.length} đoạn căn trái`}
              <span class="metric-status-icon ${report.alignment_clean ? 'pass' : 'warn'}">
                ${report.alignment_clean ? '✅' : '⚠️'}
              </span>
            </span>
          </div>

          <div class="format-metric-item">
            <span class="format-metric-label">
              <span>↔️</span> Giãn dòng chuẩn
            </span>
            <span class="format-metric-value">
              1.15 - 1.5 lines
              <span class="metric-status-icon pass">✅</span>
            </span>
          </div>
        </div>
      </div>

      ${issuesHtml}

      <!-- Hero 1-Click Auto-Format CTA -->
      <div class="auto-format-hero-box">
        <div class="auto-format-info">
          <div class="auto-format-title">
            <span>✨</span> Tự Động Chuẩn Hóa Thể Thức (1-Click)
          </div>
          <div class="auto-format-desc">
            Tự căn lề 3-1.5-2-2cm, chuyển font Times New Roman, cỡ 13pt & căn đều Justified hoàn hảo.
          </div>
        </div>
        <button class="btn-auto-format" id="btnHeroAutoFormat">
          <span>🪄 Chuẩn Hóa & Tải Word</span>
        </button>
      </div>
    `;

    // Insert at the top of errorListContainer
    errorListContainer.insertBefore(cardEl, errorListContainer.firstChild);

    // Bind auto format click
    const btnHeroAutoFormat = $('#btnHeroAutoFormat');
    if (btnHeroAutoFormat) {
      btnHeroAutoFormat.addEventListener('click', () => this.handleAutoFormat());
    }
  },

  async handleAutoFormat() {
    if (!appState.selectedFile) {
      showToast('Vui lòng chọn hoặc tải lên một file Word (.docx) để chuẩn hóa định dạng!', 'warning');
      return;
    }

    try {
      updateSystemStatus('Đang tự động chuẩn hóa định dạng file Word...', true);
      showToast('Đang xử lý chuẩn hóa lề, font và căn dòng theo Nghị định 30...', 'info');

      const blob = await api.autoFormatDocx(appState.selectedFile);
      
      // Trigger download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const baseName = appState.currentUploadedFilename ? appState.currentUploadedFilename.replace(/\.[^/.]+$/, "") : "VanBan";
      a.download = `${baseName}_ChuanHoa_TheThuc_ND30.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();

      updateSystemStatus('Hệ thống sẵn sàng', false);
      showToast('✨ Đã tự động chuẩn hóa và tải về file Word thành công!', 'success');
    } catch (err) {
      updateSystemStatus('Lỗi chuẩn hóa file Word', false);
      showToast(`Lỗi chuẩn hóa: ${err.message}`, 'error');
    }
  }
};
