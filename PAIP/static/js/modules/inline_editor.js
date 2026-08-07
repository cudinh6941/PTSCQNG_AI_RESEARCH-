/**
 * PAIP Inline Editor & Interactive Highlighting Module
 */

import { $, $$, escapeHtml } from '../utils/dom.js';
import { showToast } from '../utils/toast.js';
import { appState } from '../state.js';

export const inlineEditor = {
  init() {
    this.bindEvents();
    this.updateStats();
  },

  bindEvents() {
    const documentText = $('#documentText');
    if (documentText) {
      documentText.addEventListener('input', () => {
        this.updateStats();
      });
    }

    const btnClearText = $('#btnClearText');
    if (btnClearText) {
      btnClearText.addEventListener('click', () => {
        if (documentText) documentText.value = '';
        this.clearHighlights();
        this.updateStats();
        showToast('Đã xóa nội dung văn bản', 'info');
      });
    }

    const btnCopyText = $('#btnCopyText');
    if (btnCopyText) {
      btnCopyText.addEventListener('click', () => {
        if (documentText && documentText.value) {
          navigator.clipboard.writeText(documentText.value);
          showToast('Đã sao chép văn bản vào bộ nhớ tạm!', 'success');
        }
      });
    }

    // Quick fix tooltip actions
    const btnTooltipApply = $('#btnTooltipApply');
    if (btnTooltipApply) {
      btnTooltipApply.addEventListener('click', () => {
        if (appState.activeTooltipErrorId) {
          this.applySingleCorrection(appState.activeTooltipErrorId);
          this.hideQuickFixTooltip();
        }
      });
    }

    const btnTooltipFocus = $('#btnTooltipFocus');
    if (btnTooltipFocus) {
      btnTooltipFocus.addEventListener('click', () => {
        if (appState.activeTooltipErrorId) {
          const card = $(`#card-${appState.activeTooltipErrorId}`);
          if (card) {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            card.classList.add('card-focused');
            setTimeout(() => card.classList.remove('card-focused'), 2000);
          }
          this.hideQuickFixTooltip();
        }
      });
    }

    // Close tooltip when clicking outside
    document.addEventListener('click', (e) => {
      const tooltip = $('#quickFixTooltip');
      if (tooltip && tooltip.style.display === 'block') {
        if (!tooltip.contains(e.target) && !e.target.closest('.highlight-error')) {
          this.hideQuickFixTooltip();
        }
      }
    });
  },

  updateStats() {
    const documentText = $('#documentText');
    const charCount = $('#charCount');
    const wordCount = $('#wordCount');
    if (!documentText) return;

    const text = documentText.value || '';
    if (charCount) charCount.textContent = `${text.length.toLocaleString()} ký tự`;
    if (wordCount) {
      const words = text.trim() ? text.trim().split(/\s+/).length : 0;
      wordCount.textContent = `${words.toLocaleString()} từ`;
    }
  },

  renderHighlights(text, errors) {
    const interactiveViewer = $('#interactiveViewer');
    const highlightCount = $('#highlightCount');
    if (!interactiveViewer) return;

    if (!errors || errors.length === 0) {
      interactiveViewer.textContent = text;
      if (highlightCount) highlightCount.textContent = '0';
      return;
    }

    if (highlightCount) highlightCount.textContent = errors.length.toString();

    // Map error occurrences inside text
    let annotatedText = escapeHtml(text);
    
    // Sort errors by length descending to prevent nesting overlaps
    const sortedErrors = [...errors].sort((a, b) => (b.original || '').length - (a.original || '').length);

    sortedErrors.forEach((err, idx) => {
      if (!err.original) return;
      const errorId = err.id || `err-${idx}`;
      const escapedOriginal = escapeHtml(err.original);
      const safeType = err.error_type || 'spelling';
      
      const highlightSpan = `<span class="highlight-error highlight-${safeType}" id="hl-${errorId}" data-error-id="${errorId}">${escapedOriginal}</span>`;
      
      // Replace only first occurrence per error item
      annotatedText = annotatedText.replace(escapedOriginal, highlightSpan);
    });

    interactiveViewer.innerHTML = annotatedText;

    // Attach click listener on highlights
    $$('.highlight-error', interactiveViewer).forEach(span => {
      span.addEventListener('click', (e) => {
        e.stopPropagation();
        const errId = span.getAttribute('data-error-id');
        const errObj = errors.find(err => (err.id || `err-${errors.indexOf(err)}`) === errId);
        if (errObj) {
          this.showQuickFixTooltip(span, errObj, errId);
        }
      });
    });
  },

  showQuickFixTooltip(anchorEl, err, errorId) {
    const tooltip = $('#quickFixTooltip');
    const tooltipBadge = $('#tooltipBadge');
    const tooltipTypeLabel = $('#tooltipTypeLabel');
    const tooltipOriginal = $('#tooltipOriginal');
    const tooltipSuggested = $('#tooltipSuggested');
    const tooltipExplanation = $('#tooltipExplanation');
    const tooltipLegalRef = $('#tooltipLegalRef');
    const textModeContainer = $('#textModeContainer');

    if (!tooltip || !textModeContainer) return;

    appState.activeTooltipErrorId = errorId;

    if (tooltipBadge) {
      tooltipBadge.className = `error-badge badge-${err.error_type || 'spelling'}`;
      tooltipBadge.textContent = (err.error_type || 'Lỗi').toUpperCase();
    }
    if (tooltipTypeLabel) tooltipTypeLabel.textContent = err.error_type || 'Chính tả';
    if (tooltipOriginal) tooltipOriginal.textContent = err.original || '';
    if (tooltipSuggested) tooltipSuggested.textContent = err.suggested || '';
    if (tooltipExplanation) tooltipExplanation.textContent = err.explanation || 'Đề xuất sửa lỗi chuẩn xác';

    if (tooltipLegalRef) {
      if (err.reference) {
        tooltipLegalRef.style.display = 'block';
        tooltipLegalRef.textContent = `⚖️ Căn cứ: ${err.reference}`;
      } else {
        tooltipLegalRef.style.display = 'none';
      }
    }

    // Positioning
    const containerRect = textModeContainer.getBoundingClientRect();
    const anchorRect = anchorEl.getBoundingClientRect();

    let top = anchorRect.bottom - containerRect.top + textModeContainer.scrollTop + 8;
    let left = anchorRect.left - containerRect.left + textModeContainer.scrollLeft - 20;

    if (left < 10) left = 10;
    if (left + 300 > containerRect.width) left = Math.max(10, containerRect.width - 310);

    tooltip.style.top = `${top}px`;
    tooltip.style.left = `${left}px`;
    tooltip.style.display = 'block';
  },

  hideQuickFixTooltip() {
    const tooltip = $('#quickFixTooltip');
    if (tooltip) tooltip.style.display = 'none';
    appState.activeTooltipErrorId = null;
  },

  applySingleCorrection(errorId) {
    const err = appState.currentErrors.find(e => (e.id || `err-${appState.currentErrors.indexOf(e)}`) === errorId);
    if (!err) return;

    const documentText = $('#documentText');
    if (documentText && err.original && err.suggested) {
      documentText.value = documentText.value.replace(err.original, err.suggested);
      this.updateStats();
    }

    // Remove from active errors list
    appState.currentErrors = appState.currentErrors.filter(e => (e.id || `err-${appState.currentErrors.indexOf(e)}`) !== errorId);
    appState.emit('errorsUpdated', appState.currentErrors);

    showToast(`Đã sửa: "${err.original}" ➔ "${err.suggested}"`, 'success');
  },

  clearHighlights() {
    const interactiveViewer = $('#interactiveViewer');
    const highlightCount = $('#highlightCount');
    if (interactiveViewer) interactiveViewer.innerHTML = '';
    if (highlightCount) highlightCount.textContent = '0';
    this.hideQuickFixTooltip();
  }
};
