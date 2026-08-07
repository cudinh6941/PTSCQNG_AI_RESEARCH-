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

    // Default to enabled if format issues exist
    if (appState.isFormatApplied === undefined || appState.isFormatApplied === null) {
      appState.isFormatApplied = true;
    }

    const isApplied = appState.isFormatApplied;

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

      <!-- Option 2: Apply Format Integration Box -->
      <div class="auto-format-hero-box">
        <div class="auto-format-info">
          <div class="auto-format-title">
            <span>✨</span> Tự Động Chuẩn Hóa Thể Thức (Nghị định 30)
          </div>
          <div class="auto-format-desc" id="formatDescText">
            ${isApplied 
              ? '✅ <strong>Đang kích hoạt:</strong> Lề 3-1.5-2-2cm, toàn bộ font Times New Roman & căn đều sẽ tự động chuẩn hóa khi bạn bấm <em>"Tải File Word"</em> bên dưới.' 
              : 'Tự động căn lề 3-1.5-2-2cm, chuyển font Times New Roman, cỡ 13pt & căn đều Justified hoàn hảo khi xuất văn bản.'}
          </div>
        </div>
        <button class="btn-auto-format ${isApplied ? 'btn-format-applied' : ''}" id="btnHeroAutoFormat">
          <span id="btnHeroFormatIcon">${isApplied ? '✅' : '🪄'}</span>
          <span id="btnHeroFormatText">${isApplied ? 'Đã Bật Chuẩn Hóa Thể Thức' : 'Áp Dụng Chuẩn Hóa Thể Thức'}</span>
        </button>
      </div>
    `;

    // Insert at the top of errorListContainer
    errorListContainer.insertBefore(cardEl, errorListContainer.firstChild);

    // Bind auto format click
    const btnHeroAutoFormat = $('#btnHeroAutoFormat');
    if (btnHeroAutoFormat) {
      btnHeroAutoFormat.addEventListener('click', () => this.toggleFormatApplication());
    }
  },

  toggleFormatApplication() {
    appState.isFormatApplied = !appState.isFormatApplied;
    const isApplied = appState.isFormatApplied;

    const btn = $('#btnHeroAutoFormat');
    const icon = $('#btnHeroFormatIcon');
    const text = $('#btnHeroFormatText');
    const desc = $('#formatDescText');
    const btnExportDocx = $('#btnExportDocx');

    if (btn && icon && text && desc) {
      if (isApplied) {
        btn.classList.add('btn-format-applied');
        icon.textContent = '✅';
        text.textContent = 'Đã Bật Chuẩn Hóa Thể Thức';
        desc.innerHTML = '✅ <strong>Đang kích hoạt:</strong> Lề 3-1.5-2-2cm, toàn bộ font Times New Roman & căn đều sẽ tự động chuẩn hóa khi bạn bấm <em>"Tải File Word"</em> bên dưới.';
        
        showToast('✨ Đã kích hoạt chuẩn hóa thể thức NĐ 30! Hãy duyệt các lỗi chính tả bên dưới và bấm "Tải File Word" để nhận tài liệu hoàn chỉnh.', 'success');

        if (btnExportDocx) {
          btnExportDocx.classList.add('pulse-highlight');
          setTimeout(() => btnExportDocx.classList.remove('pulse-highlight'), 3500);
        }
      } else {
        btn.classList.remove('btn-format-applied');
        icon.textContent = '🪄';
        text.textContent = 'Áp Dụng Chuẩn Hóa Thể Thức';
        desc.textContent = 'Tự động căn lề 3-1.5-2-2cm, chuyển font Times New Roman, cỡ 13pt & căn đều Justified hoàn hảo khi xuất văn bản.';
        
        showToast('Đã tắt tự động chuẩn hóa thể thức khi xuất file.', 'info');
      }
    }
  }
};

