/**
 * PAIP Agent 0: Document Proofreader Orchestrator Module
 */

import { $, $$, escapeHtml } from '../utils/dom.js';
import { showToast, updateSystemStatus } from '../utils/toast.js';
import { api } from '../api.js';
import { appState } from '../state.js';
import { inlineEditor } from './inline_editor.js';
import { formatInspector } from './format_inspector.js';

export const proofreader = {
  SAMPLE_TEXT: `Kính gởi Ban giám đốc,
Phòng dự án xin báo cáo tình hình triễn khai gói thầu số 02 tại dự án Lô B. 
Hiện tại tiến độ thi công đang bị chậm trể do điều kiện thời tiết trên biển không thuận lợi và một số vật tư thiết bị về chậm.
Kính đề nghị Ban lảnh đạo xem xét phê duyệt phương án bổ xung thêm nhân sự kỹ thuật và sắp sếp lại kế hoạch làm ca kíp để kịp hoàn thành đúng tiến độ cam kết.`,

  init() {
    this.bindEvents();
    // Expose global methods for inline error cards
    window.focusErrorInText = (id) => this.focusErrorInText(id);
    window.applySingleError = (id) => this.applySingleError(id);
  },

  bindEvents() {
    const tabTextBtn = $('#tabTextBtn');
    const tabHighlightBtn = $('#tabHighlightBtn');
    const tabFileBtn = $('#tabFileBtn');
    const btnLoadSample = $('#btnLoadSample');
    const btnAnalyze = $('#btnAnalyze');
    const btnApplyAll = $('#btnApplyAll');
    const btnExportDocx = $('#btnExportDocx');
    const fileInput = $('#fileInput');
    const fileModeContainer = $('#fileModeContainer');
    const btnRemoveFile = $('#btnRemoveFile');

    // Tab Switching
    if (tabTextBtn) tabTextBtn.addEventListener('click', () => this.switchToTextTab());
    if (tabHighlightBtn) tabHighlightBtn.addEventListener('click', () => this.switchToHighlightTab());
    if (tabFileBtn) tabFileBtn.addEventListener('click', () => this.switchToFileTab());

    // Sample Loader
    if (btnLoadSample) {
      btnLoadSample.addEventListener('click', () => {
        const documentText = $('#documentText');
        if (documentText) {
          documentText.value = this.SAMPLE_TEXT;
          inlineEditor.updateStats();
          this.switchToTextTab();
          showToast('Đã nạp văn bản mẫu kiểm tra', 'info');
        }
      });
    }

    // File Drag & Drop
    if (fileInput) {
      fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          this.handleFileSelected(e.target.files[0]);
        }
      });
    }

    if (fileModeContainer) {
      fileModeContainer.addEventListener('click', (e) => {
        if (e.target.closest('#btnRemoveFile') || e.target.closest('#fileSelectedCard')) return;
        if (fileInput) fileInput.click();
      });

      fileModeContainer.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileModeContainer.style.borderColor = 'var(--border-focus)';
        fileModeContainer.style.background = 'rgba(37, 99, 235, 0.08)';
      });

      fileModeContainer.addEventListener('dragleave', () => {
        fileModeContainer.style.borderColor = 'rgba(255, 255, 255, 0.12)';
        fileModeContainer.style.background = 'rgba(255, 255, 255, 0.015)';
      });

      fileModeContainer.addEventListener('drop', (e) => {
        e.preventDefault();
        fileModeContainer.style.borderColor = 'rgba(255, 255, 255, 0.12)';
        fileModeContainer.style.background = 'rgba(255, 255, 255, 0.015)';
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          this.handleFileSelected(e.dataTransfer.files[0]);
        }
      });
    }

    if (btnRemoveFile) {
      btnRemoveFile.addEventListener('click', (e) => {
        e.stopPropagation();
        appState.selectedFile = null;
        appState.currentUploadedFilename = '';
        if (fileInput) fileInput.value = '';
        const fileSelectedCard = $('#fileSelectedCard');
        if (fileSelectedCard) fileSelectedCard.style.display = 'none';
        showToast('Đã hủy file đã chọn', 'info');
      });
    }

    // Analyze Trigger
    if (btnAnalyze) {
      btnAnalyze.addEventListener('click', () => this.handleAnalyzeClick());
    }

    // Filter Pills
    $$('.filter-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        $$('.filter-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        appState.activeFilter = pill.dataset.filter || 'all';
        this.renderErrorCards();
      });
    });

    // Apply All
    if (btnApplyAll) {
      btnApplyAll.addEventListener('click', () => this.handleApplyAll());
    }

    // Export Docx
    if (btnExportDocx) {
      btnExportDocx.addEventListener('click', () => this.handleExportDocx());
    }
  },

  switchToTextTab() {
    appState.currentInputTab = 'text';
    const tabTextBtn = $('#tabTextBtn');
    const tabHighlightBtn = $('#tabHighlightBtn');
    const tabFileBtn = $('#tabFileBtn');
    const documentText = $('#documentText');
    const interactiveViewer = $('#interactiveViewer');
    const textModeContainer = $('#textModeContainer');
    const fileModeContainer = $('#fileModeContainer');

    if (tabTextBtn) tabTextBtn.classList.add('active');
    if (tabHighlightBtn) tabHighlightBtn.classList.remove('active');
    if (tabFileBtn) tabFileBtn.classList.remove('active');
    if (documentText) documentText.style.display = 'block';
    if (interactiveViewer) interactiveViewer.style.display = 'none';
    if (textModeContainer) textModeContainer.style.display = 'flex';
    if (fileModeContainer) fileModeContainer.style.display = 'none';
    inlineEditor.hideQuickFixTooltip();
    inlineEditor.updateStats();
  },

  switchToHighlightTab() {
    appState.currentInputTab = 'highlight';
    const tabTextBtn = $('#tabTextBtn');
    const tabHighlightBtn = $('#tabHighlightBtn');
    const tabFileBtn = $('#tabFileBtn');
    const documentText = $('#documentText');
    const interactiveViewer = $('#interactiveViewer');
    const textModeContainer = $('#textModeContainer');
    const fileModeContainer = $('#fileModeContainer');

    if (tabHighlightBtn) tabHighlightBtn.classList.add('active');
    if (tabTextBtn) tabTextBtn.classList.remove('active');
    if (tabFileBtn) tabFileBtn.classList.remove('active');
    if (documentText) documentText.style.display = 'none';
    if (interactiveViewer) interactiveViewer.style.display = 'block';
    if (textModeContainer) textModeContainer.style.display = 'flex';
    if (fileModeContainer) fileModeContainer.style.display = 'none';

    this.renderInteractiveHighlights();
  },

  switchToFileTab() {
    appState.currentInputTab = 'file';
    const tabTextBtn = $('#tabTextBtn');
    const tabHighlightBtn = $('#tabHighlightBtn');
    const tabFileBtn = $('#tabFileBtn');
    const textModeContainer = $('#textModeContainer');
    const fileModeContainer = $('#fileModeContainer');

    if (tabFileBtn) tabFileBtn.classList.add('active');
    if (tabTextBtn) tabTextBtn.classList.remove('active');
    if (tabHighlightBtn) tabHighlightBtn.classList.remove('active');
    if (textModeContainer) textModeContainer.style.display = 'none';
    if (fileModeContainer) fileModeContainer.style.display = 'flex';
    inlineEditor.hideQuickFixTooltip();
  },

  handleFileSelected(file) {
    const validExtensions = ['.docx', '.pdf', '.txt', '.md'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validExtensions.includes(ext)) {
      showToast(`Định dạng file '${ext}' chưa được hỗ trợ. Vui lòng chọn .docx, .pdf, .txt`, 'warning');
      return;
    }

    appState.selectedFile = file;
    appState.currentUploadedFilename = file.name;

    const selectedFileName = $('#selectedFileName');
    const selectedFileSize = $('#selectedFileSize');
    const fileSelectedCard = $('#fileSelectedCard');

    if (selectedFileName) selectedFileName.textContent = file.name;
    if (selectedFileSize) selectedFileSize.textContent = this.formatBytes(file.size);
    if (fileSelectedCard) fileSelectedCard.style.display = 'flex';

    showToast(`Đã chọn file: ${file.name}`, 'info');
  },

  formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  },

  parseSelectedModel(rawValue) {
    if (!rawValue) return { provider: 'gemini', model: 'gemini-2.5-flash' };
    if (rawValue.includes(':')) {
      const parts = rawValue.split(':');
      return { provider: parts[0], model: parts[1] };
    }
    if (rawValue === 'mock') return { provider: 'mock', model: 'mock' };
    if (rawValue === 'openai') return { provider: 'openai', model: 'gpt-4o-mini' };
    if (rawValue === 'claude') return { provider: 'claude', model: 'claude-3-5-sonnet-20241022' };
    return { provider: 'gemini', model: 'gemini-2.5-flash' };
  },

  setAnalyzingState(loading) {
    appState.isAnalyzing = loading;
    const btnAnalyze = $('#btnAnalyze');
    const btnIcon = $('#btnIcon');
    const btnText = $('#btnText');

    if (loading) {
      if (btnAnalyze) btnAnalyze.disabled = true;
      if (btnIcon) btnIcon.innerHTML = '⏳';
      if (btnText) btnText.textContent = 'Đang Rà Soát...';
      updateSystemStatus('AI đang xử lý...', true);
    } else {
      if (btnAnalyze) btnAnalyze.disabled = false;
      if (btnIcon) btnIcon.innerHTML = '⚡';
      if (btnText) btnText.textContent = 'Bắt Đầu Rà Soát';
      updateSystemStatus('Hệ thống sẵn sàng', false);
    }
  },

  async handleAnalyzeClick() {
    if (appState.isAnalyzing) return;

    const modeSelector = $('#modeSelector');
    const modelSelector = $('#modelSelector');
    const customInstructionsInput = $('#customInstructionsInput');
    const documentText = $('#documentText');

    const mode = modeSelector ? modeSelector.value : 'standard';
    const rawModel = modelSelector ? modelSelector.value : 'gemini:gemini-2.5-flash';
    const customInstructions = customInstructionsInput ? customInstructionsInput.value.trim() : '';

    if (appState.currentInputTab === 'text') {
      const text = documentText ? documentText.value.trim() : '';
      if (!text) {
        showToast('Vui lòng nhập nội dung văn bản cần kiểm tra!', 'warning');
        if (documentText) documentText.focus();
        return;
      }
      await this.analyzeText(text, mode, rawModel, customInstructions);
    } else {
      if (!appState.selectedFile) {
        showToast('Vui lòng chọn hoặc kéo thả file cần kiểm tra!', 'warning');
        return;
      }
      await this.analyzeFile(appState.selectedFile, mode, rawModel, customInstructions);
    }
  },

  async analyzeText(text, mode, rawModel, customInstructions) {
    this.setAnalyzingState(true);
    this.renderLoadingState();

    try {
      const { provider, model } = this.parseSelectedModel(rawModel);
      const payload = {
        document_text: text,
        mode: mode,
        custom_instructions: customInstructions || null,
        provider: provider,
        model: model
      };

      const res = await fetch('/api/v1/proofread/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      this.handleAnalysisResult(data);
    } catch (err) {
      showToast('Lỗi kết nối máy chủ: ' + err.message, 'error');
      this.renderErrorState(err.message);
    } finally {
      this.setAnalyzingState(false);
    }
  },

  async analyzeFile(file, mode, rawModel, customInstructions) {
    this.setAnalyzingState(true);
    this.renderLoadingState();

    try {
      const { provider, model } = this.parseSelectedModel(rawModel);
      const formData = new FormData();
      formData.append('file', file);
      formData.append('mode', mode);
      if (customInstructions) {
        formData.append('custom_instructions', customInstructions);
      }
      formData.append('provider', provider);
      formData.append('model', model);

      const res = await fetch('/api/v1/proofread/file', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      
      const documentText = $('#documentText');
      if (data.success && data.extracted_text && documentText) {
        documentText.value = data.extracted_text;
        inlineEditor.updateStats();
        this.switchToTextTab();
        showToast('Đã bóc tách nội dung file sang khung soạn thảo!', 'info');
      }

      this.handleAnalysisResult(data);
    } catch (err) {
      showToast('Lỗi khi tải hoặc xử lý file: ' + err.message, 'error');
      this.renderErrorState(err.message);
    } finally {
      this.setAnalyzingState(false);
    }
  },

  handleAnalysisResult(data) {
    if (!data.success) {
      showToast(data.message || 'Kiểm tra thất bại', 'error');
      this.renderErrorState(data.message);
      return;
    }

    const result = data.result || { total_errors: 0, errors: [], score: 10.0, summary: 'Hoàn hảo!' };
    
    appState.currentErrors = (result.errors || []).map((err, idx) => ({
      ...err,
      id: 'err_' + Date.now() + '_' + idx,
      applied: false,
      dismissed: false
    }));

    // Update tokens
    appState.addTokens(data.tokens_used || 0);

    // Render Stats
    const latencyStats = $('#latencyStats');
    if (latencyStats) {
      const latency = Math.round(data.processing_time_ms || 0);
      const modelUsed = data.model_used || 'AI Engine';
      latencyStats.textContent = `Model: ${modelUsed} • Tốc độ: ${latency}ms • Tokens: ${data.tokens_used || 0}`;
    }

    // Render Score
    this.renderScore(result.score);
    this.renderScoreDetails(result);

    // Update counts & cards
    this.updateFilterCounts();
    this.renderErrorCards();

    // Render Format Inspector Report if present
    if (data.format_report) {
      formatInspector.renderReport(data.format_report);
    }

    const pendingErrors = appState.currentErrors.filter(e => !e.dismissed);
    const tabHighlightBtn = $('#tabHighlightBtn');
    const highlightCount = $('#highlightCount');

    if (pendingErrors.length > 0) {
      if (tabHighlightBtn) tabHighlightBtn.style.display = 'inline-block';
      if (highlightCount) highlightCount.textContent = pendingErrors.length;
      this.switchToHighlightTab();
      showToast(`Đã phát hiện ${pendingErrors.length} điểm cần chuẩn hóa.`);
    } else {
      if (tabHighlightBtn) tabHighlightBtn.style.display = 'none';
      this.switchToTextTab();
      showToast('Tuyệt vời! Không phát hiện lỗi nào trong văn bản.', 'success');
    }
  },

  renderScore(score) {
    const scoreValue = $('#scoreValue');
    const scoreProgressPath = $('#scoreProgressPath');
    const numScore = parseFloat(score) || 0;

    if (scoreValue) scoreValue.textContent = numScore.toFixed(1);

    if (scoreProgressPath) {
      const progress = (numScore / 10.0) * 100;
      scoreProgressPath.style.strokeDasharray = `${progress}, 100`;

      if (numScore >= 8.5) {
        scoreProgressPath.style.stroke = '#10b981';
        if (scoreValue) scoreValue.style.color = '#34d399';
      } else if (numScore >= 6.5) {
        scoreProgressPath.style.stroke = '#f59e0b';
        if (scoreValue) scoreValue.style.color = '#fbbf24';
      } else {
        scoreProgressPath.style.stroke = '#ef4444';
        if (scoreValue) scoreValue.style.color = '#f87171';
      }
    }
  },

  renderScoreDetails(result) {
    const scoreTitle = $('#scoreTitle');
    const scoreSummary = $('#scoreSummary');
    const score = result.score || 0;
    const count = result.total_errors || (result.errors ? result.errors.length : 0);

    if (scoreTitle) {
      if (score >= 9.0) {
        scoreTitle.textContent = 'Văn Bản Rất Chuẩn Mực 🌟';
      } else if (score >= 7.5) {
        scoreTitle.textContent = `Phát Hiện ${count} Điểm Cần Chỉnh Sửa 📝`;
      } else {
        scoreTitle.textContent = `Cần Chuẩn Hóa Lại (${count} Lỗi) ⚠️`;
      }
    }

    if (scoreSummary) {
      scoreSummary.textContent = result.summary || `Phát hiện ${count} lỗi chính tả, ngữ pháp hoặc văn phong cần hoàn thiện.`;
    }
  },

  updateFilterCounts() {
    const pendingErrors = appState.currentErrors.filter(e => !e.dismissed);
    const counts = {
      all: pendingErrors.length,
      spelling: pendingErrors.filter(e => e.type === 'spelling').length,
      grammar: pendingErrors.filter(e => e.type === 'grammar').length,
      word_choice: pendingErrors.filter(e => e.type === 'word_choice').length,
      punctuation: pendingErrors.filter(e => e.type === 'punctuation').length,
      legal: pendingErrors.filter(e => e.type === 'legal').length,
      format: pendingErrors.filter(e => e.type === 'format').length
    };

    const filterAll = $('#filterAll');
    const filterSpelling = $('#filterSpelling');
    const filterGrammar = $('#filterGrammar');
    const filterWordChoice = $('#filterWordChoice');
    const filterPunct = $('#filterPunct');
    const filterLegal = $('#filterLegal');

    if (filterAll) filterAll.textContent = `Tất cả (${counts.all})`;
    if (filterSpelling) filterSpelling.textContent = `Chính tả (${counts.spelling})`;
    if (filterGrammar) filterGrammar.textContent = `Ngữ pháp (${counts.grammar})`;
    if (filterWordChoice) filterWordChoice.textContent = `Dùng từ (${counts.word_choice})`;
    if (filterPunct) filterPunct.textContent = `Dấu câu (${counts.punctuation})`;
    if (filterLegal) filterLegal.textContent = `⚖️ Pháp lý (${counts.legal})`;

    const highlightCount = $('#highlightCount');
    if (highlightCount) highlightCount.textContent = counts.all;
  },

  extractContextSnippet(fullText, targetWord) {
    if (!fullText || !targetWord) return '';
    const index = fullText.indexOf(targetWord);
    if (index === -1) return '';

    const start = Math.max(0, index - 35);
    const end = Math.min(fullText.length, index + targetWord.length + 35);
    const prefix = (start > 0 ? '...' : '') + fullText.substring(start, index);
    const suffix = fullText.substring(index + targetWord.length, end) + (end < fullText.length ? '...' : '');

    return `${escapeHtml(prefix)}<mark class="snippet-mark">${escapeHtml(targetWord)}</mark>${escapeHtml(suffix)}`;
  },

  renderErrorCards() {
    const errorListContainer = $('#errorListContainer');
    if (!errorListContainer) return;

    const pendingErrors = appState.currentErrors.filter(e => !e.dismissed);
    const filtered = appState.activeFilter === 'all' 
      ? pendingErrors 
      : pendingErrors.filter(e => e.type === appState.activeFilter);

    if (filtered.length === 0) {
      if (appState.currentErrors.length > 0 && pendingErrors.length === 0) {
        errorListContainer.innerHTML = `
          <div class="clean-state-box">
            <div class="clean-icon" style="color: #10b981;">🎉</div>
            <div style="font-weight: 700; color: #f3f4f6; margin-bottom: 4px;">Đã Chuẩn Hóa Toàn Bộ!</div>
            <div style="font-size: 0.82rem; color: var(--text-muted);">Tất cả gợi ý đã được áp dụng vào văn bản. Bạn có thể bấm nút "Tải File Word" để lưu về.</div>
          </div>
        `;
      } else {
        errorListContainer.innerHTML = `
          <div class="clean-state-box">
            <div class="clean-icon" style="color: #10b981;">✨</div>
            <div style="font-weight: 700; color: #f3f4f6; margin-bottom: 4px;">Không Có Lỗi Nào</div>
            <div style="font-size: 0.82rem; color: var(--text-muted);">Không tìm thấy lỗi thuộc nhóm này.</div>
          </div>
        `;
      }
      return;
    }

    const documentText = $('#documentText');
    const currentFullText = documentText ? documentText.value || '' : '';
    let html = '';

    filtered.forEach(err => {
      const typeLabel = this.getTypeLabel(err.type);
      const badgeClass = `badge-${err.type || 'spelling'}`;
      const original = escapeHtml(err.original);
      const suggested = escapeHtml(err.suggested || err.suggestion || '');
      const explanation = escapeHtml(err.explanation);
      const snippet = this.extractContextSnippet(currentFullText, err.original);

      let snippetHtml = '';
      if (snippet) {
        snippetHtml = `
          <div class="context-snippet-box">
            <div style="font-size: 0.68rem; color: var(--text-muted); margin-bottom: 2px;">📍 Ngữ cảnh trong bài:</div>
            <div>${snippet}</div>
          </div>
        `;
      }

      let referenceHtml = '';
      if (err.reference || err.source_link) {
        const refText = escapeHtml(err.reference || 'Căn cứ pháp luật hiện hành');
        const linkHtml = err.source_link 
          ? `<a href="${escapeHtml(err.source_link)}" target="_blank" rel="noopener noreferrer" class="legal-reference-link" onclick="event.stopPropagation();">Tra cứu nguồn ↗</a>`
          : '';
        referenceHtml = `
          <div class="legal-reference-box">
            <span class="legal-reference-icon">⚖️</span>
            <span><strong>Căn cứ:</strong> ${refText}</span>
            ${linkHtml}
          </div>
        `;
      }

      html += `
        <div class="error-card" data-id="${err.id}" onclick="window.focusErrorInText('${err.id}')">
          <div class="error-card-header">
            <span class="error-badge ${badgeClass}">${typeLabel}</span>
            <span style="font-size: 0.72rem; color: var(--text-muted);">${this.getSeverityLabel(err.severity)}</span>
          </div>

          <div class="diff-box">
            <span class="diff-original">${original}</span>
            <span class="diff-arrow">➔</span>
            <span class="diff-suggested">${suggested}</span>
          </div>

          ${snippetHtml}
          <div class="error-explanation">${explanation}</div>
          ${referenceHtml}

          <div class="card-actions">
            <button class="btn-apply-single" onclick="event.stopPropagation(); window.applySingleError('${err.id}')">
              Áp dụng
            </button>
          </div>
        </div>
      `;
    });

    errorListContainer.innerHTML = html;
  },

  renderInteractiveHighlights() {
    const documentText = $('#documentText');
    const rawText = documentText ? documentText.value || '' : '';
    const pendingErrors = appState.currentErrors.filter(e => !e.dismissed && e.original);
    inlineEditor.renderHighlights(rawText, pendingErrors);
  },

  focusErrorInText(id) {
    if (appState.currentInputTab !== 'highlight') {
      this.switchToHighlightTab();
    }
    inlineEditor.hideQuickFixTooltip();

    setTimeout(() => {
      const markEl = document.getElementById(`hl-${id}`) || document.getElementById(`mark_${id}`);
      if (markEl) {
        markEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        markEl.classList.remove('highlight-pulse');
        void markEl.offsetWidth;
        markEl.classList.add('highlight-pulse');
        setTimeout(() => markEl.classList.remove('highlight-pulse'), 3000);
      }
    }, 50);
  },

  applySingleError(id) {
    const err = appState.currentErrors.find(e => e.id === id);
    if (!err || err.applied) return;

    const original = err.original;
    const suggested = err.suggested || err.suggestion || '';

    const documentText = $('#documentText');
    if (documentText && documentText.value.includes(original)) {
      documentText.value = documentText.value.replace(original, suggested);
      inlineEditor.updateStats();
      err.applied = true;
      err.dismissed = true;
      showToast(`Đã sửa: "${original}" ➔ "${suggested}"`, 'success');
    } else {
      showToast(`Không tìm thấy vị trí từ "${original}" trong văn bản hiện tại.`, 'warning');
      err.dismissed = true;
    }

    this.updateFilterCounts();
    this.renderErrorCards();
    if (appState.currentInputTab === 'highlight') {
      this.renderInteractiveHighlights();
    }
  },

  handleApplyAll() {
    const pendingErrors = appState.currentErrors.filter(e => !e.dismissed);
    if (pendingErrors.length === 0) {
      showToast('Không có lỗi nào để áp dụng!', 'warning');
      return;
    }

    const documentText = $('#documentText');
    if (!documentText) return;

    let updatedText = documentText.value;
    let count = 0;

    pendingErrors.forEach(err => {
      const original = err.original;
      const suggested = err.suggested || err.suggestion || '';
      if (original && suggested && updatedText.includes(original)) {
        updatedText = updatedText.replaceAll(original, suggested);
        count++;
      }
      err.applied = true;
      err.dismissed = true;
    });

    documentText.value = updatedText;
    inlineEditor.updateStats();
    this.updateFilterCounts();
    this.renderErrorCards();
    if (appState.currentInputTab === 'highlight') {
      this.renderInteractiveHighlights();
    }
    this.renderScore(10.0);
    const scoreTitle = $('#scoreTitle');
    const scoreSummary = $('#scoreSummary');
    if (scoreTitle) scoreTitle.textContent = 'Đã Chuẩn Hóa Toàn Bộ! 🎉';
    if (scoreSummary) scoreSummary.textContent = `Đã tự động thay thế ${count} vị trí từ trong văn bản.`;
    showToast(`Đã tự động sửa ${count} lỗi trong văn bản!`, 'success');
  },

  async handleExportDocx() {
    const documentText = $('#documentText');
    const text = documentText ? documentText.value.trim() : '';
    if (!text && !appState.selectedFile) {
      showToast('Chưa có nội dung hoặc file để xuất!', 'warning');
      return;
    }

    const btnExportDocx = $('#btnExportDocx');

    try {
      if (btnExportDocx) {
        btnExportDocx.disabled = true;
        btnExportDocx.innerHTML = '<span>⏳</span><span>Đang Xử Lý File Word...</span>';
      }

      // TRƯỜNG HỢP 1: Đã upload file Word (.docx) -> In-place update giữ nguyên format & bảng biểu
      if (appState.selectedFile && appState.selectedFile.name.toLowerCase().endsWith('.docx')) {
        const hasSpecificApplied = appState.currentErrors.some(e => e.applied);
        const targetErrors = hasSpecificApplied 
          ? appState.currentErrors.filter(e => e.applied)
          : appState.currentErrors;

        const appliedReplacements = targetErrors.map(e => ({
          original: e.original,
          suggested: e.suggested || e.suggestion || ''
        })).filter(e => e.original && e.suggested && e.original !== e.suggested);

        const formData = new FormData();
        formData.append('file', appState.selectedFile);
        formData.append('replacements', JSON.stringify(appliedReplacements));
        formData.append('highlight_changes', 'false');

        const response = await fetch('/api/v1/proofread/export-docx-inplace', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) throw new Error(`In-place export failed (${response.status})`);

        const blob = await response.blob();
        const baseName = appState.selectedFile.name.replace(/\.[^/.]+$/, "");
        const filename = `${baseName}_da_chinh_sua.docx`;
        
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);

        showToast(`📥 Đã tải file Word gốc: ${filename}`, 'success');
      } 
      // TRƯỜNG HỢP 2: Plain text -> Tạo file Word mới
      else {
        let filename = 'Van_ban_hoan_chinh.docx';
        if (appState.currentUploadedFilename) {
          const base = appState.currentUploadedFilename.replace(/\.[^/.]+$/, "");
          filename = `${base}_da_chinh_sua.docx`;
        }

        const response = await fetch('/api/v1/proofread/export-docx', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: text, filename: filename })
        });

        if (!response.ok) throw new Error(`Export failed (${response.status})`);

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);

        showToast(`📥 Đã xuất file Word chuẩn thể thức: ${filename}`, 'success');
      }
    } catch (err) {
      showToast('Lỗi khi xuất file Word: ' + err.message, 'error');
    } finally {
      if (btnExportDocx) {
        btnExportDocx.disabled = false;
        btnExportDocx.innerHTML = '<span>📥</span><span>Tải File Word (.docx)</span>';
      }
    }
  },

  getTypeLabel(type) {
    const map = {
      spelling: 'Chính tả',
      grammar: 'Ngữ pháp',
      word_choice: 'Dùng từ',
      punctuation: 'Dấu câu',
      legal: '⚖️ Pháp lý & Luật',
      format: '📐 Thể thức NĐ30',
      consistency: '🔍 Tính nhất quán'
    };
    return map[type] || 'Lỗi';
  },

  getSeverityLabel(sev) {
    if (sev === 'high') return '⚠️ Cần sửa';
    if (sev === 'low') return '💡 Gợi ý nhẹ';
    return '🔸 Lưu ý';
  },

  renderLoadingState() {
    const errorListContainer = $('#errorListContainer');
    if (errorListContainer) {
      errorListContainer.innerHTML = `
        <div class="clean-state-box">
          <div class="clean-icon" style="animation: spin 1s infinite linear;">⚡</div>
          <div style="font-weight: 700; color: #f3f4f6; margin-bottom: 4px;">Đang Phân Tích Văn Bản...</div>
          <div style="font-size: 0.82rem; color: var(--text-muted);">AI đang đối chiếu từ điển, ngữ pháp tiếng Việt và thể thức hành chính...</div>
        </div>
      `;
    }
  },

  renderErrorState(msg) {
    const errorListContainer = $('#errorListContainer');
    if (errorListContainer) {
      errorListContainer.innerHTML = `
        <div class="clean-state-box">
          <div class="clean-icon" style="color: #ef4444;">⚠️</div>
          <div style="font-weight: 700; color: #ef4444; margin-bottom: 4px;">Phân Tích Thất Bại</div>
          <div style="font-size: 0.82rem; color: var(--text-muted);">${escapeHtml(msg)}</div>
        </div>
      `;
    }
  }
};
