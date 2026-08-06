/**
 * PAIP Enterprise Web Application — Client Logic
 * Agent 0: Document Proofreader & Smart Word (.docx) Editor
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements - Navigation & Telemetry
  const sessionTokens = document.getElementById('sessionTokens');
  const systemStatus = document.getElementById('systemStatus');
  const statusLabel = document.getElementById('statusLabel');

  // DOM Elements - Workspace Toolbar
  const modeSelector = document.getElementById('modeSelector');
  const modelSelector = document.getElementById('modelSelector');
  const customInstructionsInput = document.getElementById('customInstructionsInput');
  const btnAnalyze = document.getElementById('btnAnalyze');
  const btnText = document.getElementById('btnText');
  const btnIcon = document.getElementById('btnIcon');

  // DOM Elements - Left Panel (Editor & Upload)
  const tabTextBtn = document.getElementById('tabTextBtn');
  const tabHighlightBtn = document.getElementById('tabHighlightBtn');
  const highlightCount = document.getElementById('highlightCount');
  const tabFileBtn = document.getElementById('tabFileBtn');
  const textModeContainer = document.getElementById('textModeContainer');
  const fileModeContainer = document.getElementById('fileModeContainer');
  const documentText = document.getElementById('documentText');
  const interactiveViewer = document.getElementById('interactiveViewer');
  const quickFixTooltip = document.getElementById('quickFixTooltip');
  const tooltipBadge = document.getElementById('tooltipBadge');
  const tooltipTypeLabel = document.getElementById('tooltipTypeLabel');
  const tooltipOriginal = document.getElementById('tooltipOriginal');
  const tooltipSuggested = document.getElementById('tooltipSuggested');
  const tooltipExplanation = document.getElementById('tooltipExplanation');
  const tooltipLegalRef = document.getElementById('tooltipLegalRef');
  const btnTooltipApply = document.getElementById('btnTooltipApply');
  const btnTooltipFocus = document.getElementById('btnTooltipFocus');
  let activeTooltipErrorId = null;

  const fileInput = document.getElementById('fileInput');
  const fileSelectedCard = document.getElementById('fileSelectedCard');
  const selectedFileName = document.getElementById('selectedFileName');
  const selectedFileSize = document.getElementById('selectedFileSize');
  const btnRemoveFile = document.getElementById('btnRemoveFile');
  
  const charCount = document.getElementById('charCount');
  const wordCount = document.getElementById('wordCount');
  const btnLoadSample = document.getElementById('btnLoadSample');
  const btnClearText = document.getElementById('btnClearText');
  const btnCopyText = document.getElementById('btnCopyText');
  const btnExportDocx = document.getElementById('btnExportDocx');

  // DOM Elements - Right Panel (Inspector & Corrections)
  const scoreValue = document.getElementById('scoreValue');
  const scoreProgressPath = document.getElementById('scoreProgressPath');
  const scoreTitle = document.getElementById('scoreTitle');
  const scoreSummary = document.getElementById('scoreSummary');
  const errorListContainer = document.getElementById('errorListContainer');
  const latencyStats = document.getElementById('latencyStats');
  const btnApplyAll = document.getElementById('btnApplyAll');
  const filterPills = document.querySelectorAll('.filter-pill');
  const toastContainer = document.getElementById('toastContainer');

  // Application State
  let currentInputTab = 'text'; // 'text' | 'highlight' | 'file'
  let selectedFile = null;
  let currentUploadedFilename = '';
  let currentErrors = [];
  let activeFilter = 'all';
  let isAnalyzing = false;
  let totalSessionTokens = 0;

  const SAMPLE_TEXT = `Kính gởi Ban giám đốc,
Phòng dự án xin báo cáo tình hình triễn khai gói thầu số 02 tại dự án Lô B. 
Hiện tại tiến độ thi công đang bị chậm trể do điều kiện thời tiết trên biển không thuận lợi và một số vật tư thiết bị về chậm.
Kính đề nghị Ban lảnh đạo xem xét phê duyệt phương án bổ xung thêm nhân sự kỹ thuật và sắp sếp lại kế hoạch làm ca kíp để kịp hoàn thành đúng tiến độ cam kết.`;

  // ── 1. Tab Switching ────────────────────────────────────
  function switchToTextTab() {
    currentInputTab = 'text';
    tabTextBtn.classList.add('active');
    tabHighlightBtn.classList.remove('active');
    tabFileBtn.classList.remove('active');
    documentText.style.display = 'block';
    interactiveViewer.style.display = 'none';
    textModeContainer.style.display = 'flex';
    fileModeContainer.style.display = 'none';
    hideQuickFixTooltip();
    updateStats();
  }

  function switchToHighlightTab() {
    currentInputTab = 'highlight';
    tabHighlightBtn.classList.add('active');
    tabTextBtn.classList.remove('active');
    tabFileBtn.classList.remove('active');
    documentText.style.display = 'none';
    interactiveViewer.style.display = 'block';
    textModeContainer.style.display = 'flex';
    fileModeContainer.style.display = 'none';
    renderInteractiveHighlights();
    updateStats();
  }

  function switchToFileTab() {
    currentInputTab = 'file';
    tabFileBtn.classList.add('active');
    tabTextBtn.classList.remove('active');
    tabHighlightBtn.classList.remove('active');
    textModeContainer.style.display = 'none';
    fileModeContainer.style.display = 'flex';
    hideQuickFixTooltip();
  }

  tabTextBtn.addEventListener('click', switchToTextTab);
  tabHighlightBtn.addEventListener('click', switchToHighlightTab);
  tabFileBtn.addEventListener('click', switchToFileTab);

  // ── 2. Word & Character Counter ─────────────────────────
  function updateStats() {
    const text = documentText.value || '';
    const chars = text.length;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    charCount.textContent = `${chars.toLocaleString()} ký tự`;
    wordCount.textContent = `${words.toLocaleString()} từ`;
  }

  documentText.addEventListener('input', updateStats);

  // ── 3. Sample & Clear Actions ───────────────────────────
  btnLoadSample.addEventListener('click', () => {
    documentText.value = SAMPLE_TEXT;
    currentUploadedFilename = 'van_ban_mau.docx';
    updateStats();
    switchToTextTab();
    showToast('Đã nạp văn bản mẫu chứa lỗi thực tế!');
  });

  btnClearText.addEventListener('click', () => {
    documentText.value = '';
    updateStats();
    resetResults();
    showToast('Đã xóa trắng khung soạn thảo');
  });

  // ── 4. File Drag & Drop Handling ────────────────────────
  fileModeContainer.addEventListener('click', (e) => {
    if (e.target !== btnRemoveFile && !selectedFile) {
      fileInput.click();
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
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
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  function handleFileSelected(file) {
    const validExtensions = ['.docx', '.pdf', '.txt', '.md'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validExtensions.includes(ext)) {
      showToast(`Định dạng file '${ext}' chưa được hỗ trợ. Vui lòng chọn .docx, .pdf, .txt`, 'warning');
      return;
    }

    selectedFile = file;
    currentUploadedFilename = file.name;
    selectedFileName.textContent = file.name;
    selectedFileSize.textContent = formatBytes(file.size);
    fileSelectedCard.style.display = 'flex';
    showToast(`Đã chọn file: ${file.name}`);
  }

  btnRemoveFile.addEventListener('click', (e) => {
    e.stopPropagation();
    selectedFile = null;
    currentUploadedFilename = '';
    fileInput.value = '';
    fileSelectedCard.style.display = 'none';
    showToast('Đã hủy file đã chọn');
  });

  function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  // ── 5. AI Proofreading Trigger ──────────────────────────
  btnAnalyze.addEventListener('click', async () => {
    if (isAnalyzing) return;

    const mode = modeSelector.value;
    const selectedModel = modelSelector.value;
    const customInstructions = customInstructionsInput.value.trim();

    // Validate Input
    if (currentInputTab === 'text') {
      const text = documentText.value.trim();
      if (!text) {
        showToast('Vui lòng nhập nội dung văn bản cần kiểm tra!', 'warning');
        documentText.focus();
        return;
      }
      await analyzeText(text, mode, selectedModel, customInstructions);
    } else {
      if (!selectedFile) {
        showToast('Vui lòng chọn hoặc kéo thả file cần kiểm tra!', 'warning');
        return;
      }
      await analyzeFile(selectedFile, mode, selectedModel, customInstructions);
    }
  });

  function setAnalyzingState(loading) {
    isAnalyzing = loading;
    if (loading) {
      btnAnalyze.disabled = true;
      btnIcon.innerHTML = '⏳';
      btnText.textContent = 'Đang Rà Soát...';
      statusLabel.textContent = 'AI đang xử lý...';
      systemStatus.style.background = 'rgba(245, 158, 11, 0.15)';
      systemStatus.style.color = '#f59e0b';
      systemStatus.querySelector('.status-dot').style.background = '#f59e0b';
      systemStatus.querySelector('.status-dot').style.boxShadow = '0 0 8px #f59e0b';
    } else {
      btnAnalyze.disabled = false;
      btnIcon.innerHTML = '⚡';
      btnText.textContent = 'Bắt Đầu Rà Soát';
      statusLabel.textContent = 'Hệ thống sẵn sàng';
      systemStatus.style.background = 'rgba(16, 185, 129, 0.12)';
      systemStatus.style.color = '#34d399';
      systemStatus.querySelector('.status-dot').style.background = '#10b981';
      systemStatus.querySelector('.status-dot').style.boxShadow = '0 0 8px #10b981';
    }
  }

  function parseSelectedModel(rawValue) {
    if (!rawValue) return { provider: 'gemini', model: 'gemini-2.5-flash' };
    if (rawValue.includes(':')) {
      const parts = rawValue.split(':');
      return { provider: parts[0], model: parts[1] };
    }
    if (rawValue === 'mock') return { provider: 'mock', model: 'mock' };
    if (rawValue === 'openai') return { provider: 'openai', model: 'gpt-4o-mini' };
    if (rawValue === 'claude') return { provider: 'claude', model: 'claude-3-5-sonnet-20241022' };
    return { provider: 'gemini', model: 'gemini-2.5-flash' };
  }

  async function analyzeText(text, mode, rawModel, customInstructions) {
    setAnalyzingState(true);
    renderLoadingState();

    try {
      const { provider, model } = parseSelectedModel(rawModel);
      const payload = {
        document_text: text,
        mode: mode,
        custom_instructions: customInstructions || null,
        provider: provider,
        model: model
      };

      const response = await fetch('/api/v1/proofread/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      handleAnalysisResult(data);
    } catch (err) {
      console.error('API Error:', err);
      showToast('Lỗi kết nối máy chủ: ' + err.message, 'error');
      renderErrorState(err.message);
    } finally {
      setAnalyzingState(false);
    }
  }

  async function analyzeFile(file, mode, rawModel, customInstructions) {
    setAnalyzingState(true);
    renderLoadingState();

    try {
      const { provider, model } = parseSelectedModel(rawModel);
      const formData = new FormData();
      formData.append('file', file);
      formData.append('mode', mode);
      if (customInstructions) {
        formData.append('custom_instructions', customInstructions);
      }
      formData.append('provider', provider);
      formData.append('model', model);

      const response = await fetch('/api/v1/proofread/file', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      
      // Auto transfer extracted text to the Editor tab for interactive editing
      if (data.success && data.extracted_text) {
        documentText.value = data.extracted_text;
        updateStats();
        switchToTextTab();
        showToast('Đã bóc tách nội dung file sang khung soạn thảo!');
      }

      handleAnalysisResult(data);
    } catch (err) {
      console.error('File Upload Error:', err);
      showToast('Lỗi khi tải hoặc xử lý file: ' + err.message, 'error');
      renderErrorState(err.message);
    } finally {
      setAnalyzingState(false);
    }
  }

  // ── 6. Handle & Render Results ──────────────────────────
  function handleAnalysisResult(data) {
    if (!data.success) {
      showToast(data.message || 'Kiểm tra thất bại', 'error');
      renderErrorState(data.message);
      return;
    }

    const result = data.result || { total_errors: 0, errors: [], score: 10.0, summary: 'Hoàn hảo!' };
    
    // Add unique IDs to errors
    currentErrors = (result.errors || []).map((err, idx) => ({
      ...err,
      id: 'err_' + Date.now() + '_' + idx,
      applied: false,
      dismissed: false
    }));

    // Update Session Telemetry
    const tokens = data.tokens_used || 0;
    totalSessionTokens += tokens;
    sessionTokens.textContent = `${totalSessionTokens.toLocaleString()} Tokens`;

    // Render Stats
    const latency = Math.round(data.processing_time_ms || 0);
    const modelUsed = data.model_used || 'AI Engine';
    latencyStats.textContent = `Model: ${modelUsed} • Tốc độ: ${latency}ms • Tokens: ${tokens}`;

    // Render Score & Banner
    renderScore(result.score);
    renderScoreDetails(result);

    // Render Error Cards & Highlights
    updateFilterCounts();
    renderErrorCards();

    const pendingErrors = currentErrors.filter(e => !e.dismissed);
    if (pendingErrors.length > 0) {
      tabHighlightBtn.style.display = 'inline-block';
      highlightCount.textContent = pendingErrors.length;
      switchToHighlightTab();
      showToast(`Đã phát hiện ${pendingErrors.length} điểm cần chuẩn hóa.`);
    } else {
      tabHighlightBtn.style.display = 'none';
      switchToTextTab();
      showToast('Tuyệt vời! Không phát hiện lỗi nào trong văn bản.', 'info');
    }
  }

  function renderScore(score) {
    const numScore = parseFloat(score) || 0;
    scoreValue.textContent = numScore.toFixed(1);

    const circumference = 100;
    const progress = (numScore / 10.0) * circumference;
    scoreProgressPath.style.strokeDasharray = `${progress}, 100`;

    if (numScore >= 8.5) {
      scoreProgressPath.style.stroke = '#10b981';
      scoreValue.style.color = '#34d399';
    } else if (numScore >= 6.5) {
      scoreProgressPath.style.stroke = '#f59e0b';
      scoreValue.style.color = '#fbbf24';
    } else {
      scoreProgressPath.style.stroke = '#ef4444';
      scoreValue.style.color = '#f87171';
    }
  }

  function renderScoreDetails(result) {
    const score = result.score || 0;
    const count = result.total_errors || (result.errors ? result.errors.length : 0);

    if (score >= 9.0) {
      scoreTitle.textContent = 'Văn Bản Rất Chuẩn Mực 🌟';
    } else if (score >= 7.5) {
      scoreTitle.textContent = `Phát Hiện ${count} Điểm Cần Chỉnh Sửa 📝`;
    } else {
      scoreTitle.textContent = `Cần Chuẩn Hóa Lại (${count} Lỗi) ⚠️`;
    }

    scoreSummary.textContent = result.summary || `Phát hiện ${count} lỗi chính tả, ngữ pháp hoặc văn phong cần hoàn thiện.`;
  }

  function updateFilterCounts() {
    const pendingErrors = currentErrors.filter(e => !e.dismissed);
    const counts = {
      all: pendingErrors.length,
      spelling: pendingErrors.filter(e => e.type === 'spelling').length,
      grammar: pendingErrors.filter(e => e.type === 'grammar').length,
      word_choice: pendingErrors.filter(e => e.type === 'word_choice').length,
      punctuation: pendingErrors.filter(e => e.type === 'punctuation').length,
      legal: pendingErrors.filter(e => e.type === 'legal').length
    };

    document.getElementById('filterAll').textContent = `Tất cả (${counts.all})`;
    document.getElementById('filterSpelling').textContent = `Chính tả (${counts.spelling})`;
    document.getElementById('filterGrammar').textContent = `Ngữ pháp (${counts.grammar})`;
    document.getElementById('filterWordChoice').textContent = `Dùng từ (${counts.word_choice})`;
    document.getElementById('filterPunct').textContent = `Dấu câu (${counts.punctuation})`;
    const filterLegal = document.getElementById('filterLegal');
    if (filterLegal) {
      filterLegal.textContent = `⚖️ Pháp lý (${counts.legal})`;
    }

    highlightCount.textContent = counts.all;
    if (counts.all === 0) {
      tabHighlightBtn.style.display = 'none';
    } else {
      tabHighlightBtn.style.display = 'inline-block';
    }
  }

  function extractContextSnippet(fullText, targetWord) {
    if (!fullText || !targetWord) return '';
    const index = fullText.indexOf(targetWord);
    if (index === -1) return '';

    const start = Math.max(0, index - 35);
    const end = Math.min(fullText.length, index + targetWord.length + 35);
    const prefix = (start > 0 ? '...' : '') + fullText.substring(start, index);
    const suffix = fullText.substring(index + targetWord.length, end) + (end < fullText.length ? '...' : '');

    return `${escapeHtml(prefix)}<mark class="snippet-mark">${escapeHtml(targetWord)}</mark>${escapeHtml(suffix)}`;
  }

  function renderErrorCards() {
    const pendingErrors = currentErrors.filter(e => !e.dismissed);
    const filtered = activeFilter === 'all' 
      ? pendingErrors 
      : pendingErrors.filter(e => e.type === activeFilter);

    if (filtered.length === 0) {
      if (currentErrors.length > 0 && pendingErrors.length === 0) {
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

    const currentFullText = documentText.value || '';
    let html = '';

    filtered.forEach(err => {
      const typeLabel = getTypeLabel(err.type);
      const badgeClass = `badge-${err.type}`;
      const original = escapeHtml(err.original);
      const suggested = escapeHtml(err.suggested || err.suggestion || '');
      const explanation = escapeHtml(err.explanation);
      const snippet = extractContextSnippet(currentFullText, err.original);

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
            <span style="font-size: 0.72rem; color: var(--text-muted);">${getSeverityLabel(err.severity)}</span>
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
  }

  // ── In-Text Highlighting Visualizer ─────────────────────
  function renderInteractiveHighlights() {
    const rawText = documentText.value || '';
    const pendingErrors = currentErrors.filter(e => !e.dismissed && e.original);

    if (!rawText) {
      interactiveViewer.innerHTML = '<div style="color: var(--text-muted); font-style: italic;">Chưa có nội dung văn bản.</div>';
      return;
    }

    if (pendingErrors.length === 0) {
      interactiveViewer.innerHTML = `
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px dashed rgba(16, 185, 129, 0.3); padding: 10px 14px; border-radius: var(--radius-sm); margin-bottom: 14px; color: #34d399; font-weight: 600; font-size: 0.86rem;">
          🎉 Tuyệt vời! Toàn bộ văn bản đã sạch lỗi và chuẩn mực.
        </div>
        <div>${escapeHtml(rawText).replace(/\n/g, '<br>')}</div>
      `;
      return;
    }

    let annotatedText = escapeHtml(rawText);

    // Sort by longest original text first to prevent partial substring collision
    const sortedErrors = [...pendingErrors].sort((a, b) => (b.original || '').length - (a.original || '').length);

    sortedErrors.forEach(err => {
      const orig = escapeHtml(err.original);
      if (!orig) return;
      const regex = new RegExp(escapeRegex(orig), 'g');
      const badgeClass = `highlight-${err.type}`;
      annotatedText = annotatedText.replace(regex, `<mark class="highlight-error ${badgeClass}" data-id="${err.id}" id="mark_${err.id}">${orig}</mark>`);
    });

    interactiveViewer.innerHTML = annotatedText.replace(/\n/g, '<br>');

    // Bind hover & click events on highlighted marks
    const marks = interactiveViewer.querySelectorAll('.highlight-error');
    marks.forEach(mark => {
      mark.addEventListener('mouseenter', () => {
        showQuickFixTooltip(mark.dataset.id, mark);
      });
      mark.addEventListener('click', (e) => {
        e.stopPropagation();
        showQuickFixTooltip(mark.dataset.id, mark);
        focusCardFromText(mark.dataset.id);
      });
    });
  }

  function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // ── Floating Quick-Fix Tooltip ──────────────────────────
  function showQuickFixTooltip(id, anchorEl) {
    const err = currentErrors.find(e => e.id === id);
    if (!err || err.dismissed) {
      hideQuickFixTooltip();
      return;
    }

    activeTooltipErrorId = id;
    tooltipBadge.className = `error-badge badge-${err.type}`;
    tooltipBadge.textContent = getTypeLabel(err.type);
    tooltipTypeLabel.textContent = getSeverityLabel(err.severity);
    tooltipOriginal.textContent = err.original;
    tooltipSuggested.textContent = err.suggested || err.suggestion || '';
    tooltipExplanation.textContent = err.explanation;

    if (err.reference) {
      tooltipLegalRef.style.display = 'block';
      tooltipLegalRef.textContent = `⚖️ Căn cứ: ${err.reference}`;
    } else {
      tooltipLegalRef.style.display = 'none';
    }

    // Position tooltip relative to textModeContainer
    const containerRect = textModeContainer.getBoundingClientRect();
    const anchorRect = anchorEl.getBoundingClientRect();

    let top = anchorRect.bottom - containerRect.top + textModeContainer.scrollTop + 8;
    let left = anchorRect.left - containerRect.left + textModeContainer.scrollLeft - 20;

    // Boundary check
    if (left < 10) left = 10;
    if (left + 300 > containerRect.width) left = Math.max(10, containerRect.width - 310);

    quickFixTooltip.style.top = `${top}px`;
    quickFixTooltip.style.left = `${left}px`;
    quickFixTooltip.style.display = 'block';
  }

  function hideQuickFixTooltip() {
    if (quickFixTooltip) {
      quickFixTooltip.style.display = 'none';
    }
    activeTooltipErrorId = null;
  }

  // Close tooltip when clicking outside
  document.addEventListener('click', (e) => {
    if (quickFixTooltip && !quickFixTooltip.contains(e.target) && !e.target.classList.contains('highlight-error')) {
      hideQuickFixTooltip();
    }
  });

  if (btnTooltipApply) {
    btnTooltipApply.addEventListener('click', () => {
      if (activeTooltipErrorId) {
        window.applySingleError(activeTooltipErrorId);
        hideQuickFixTooltip();
      }
    });
  }

  if (btnTooltipFocus) {
    btnTooltipFocus.addEventListener('click', () => {
      if (activeTooltipErrorId) {
        focusCardFromText(activeTooltipErrorId);
        hideQuickFixTooltip();
      }
    });
  }

  // ── Bi-directional Scrolling & Focus Synchronization ───
  window.focusErrorInText = function(id) {
    if (currentInputTab !== 'highlight') {
      switchToHighlightTab();
    }
    hideQuickFixTooltip();

    setTimeout(() => {
      const markEl = document.getElementById(`mark_${id}`);
      if (markEl) {
        markEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        markEl.classList.remove('highlight-pulse');
        void markEl.offsetWidth;
        markEl.classList.add('highlight-pulse');
        setTimeout(() => markEl.classList.remove('highlight-pulse'), 3000);
      }
    }, 50);
  };

  function focusCardFromText(id) {
    const card = document.querySelector(`.error-card[data-id="${id}"]`);
    if (card) {
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      card.classList.remove('card-focused');
      void card.offsetWidth;
      card.classList.add('card-focused');
      setTimeout(() => card.classList.remove('card-focused'), 2500);
    }
  }

  function getTypeLabel(type) {
    const map = {
      spelling: 'Chính tả',
      grammar: 'Ngữ pháp',
      word_choice: 'Dùng từ',
      punctuation: 'Dấu câu',
      legal: '⚖️ Pháp lý & Luật'
    };
    return map[type] || 'Lỗi';
  }

  function getSeverityLabel(sev) {
    if (sev === 'high') return '⚠️ Cần sửa';
    if (sev === 'low') return '💡 Gợi ý nhẹ';
    return '🔸 Lưu ý';
  }

  function renderLoadingState() {
    errorListContainer.innerHTML = `
      <div class="clean-state-box">
        <div class="clean-icon" style="animation: spin 1s infinite linear;">⚡</div>
        <div style="font-weight: 700; color: #f3f4f6; margin-bottom: 4px;">Đang Phân Tích Văn Bản...</div>
        <div style="font-size: 0.82rem; color: var(--text-muted);">AI đang đối chiếu từ điển, ngữ pháp tiếng Việt và thể thức hành chính...</div>
      </div>
    `;
  }

  function renderErrorState(msg) {
    errorListContainer.innerHTML = `
      <div class="clean-state-box">
        <div class="clean-icon" style="color: #ef4444;">⚠️</div>
        <div style="font-weight: 700; color: #ef4444; margin-bottom: 4px;">Phân Tích Thất Bại</div>
        <div style="font-size: 0.82rem; color: var(--text-muted);">${escapeHtml(msg)}</div>
      </div>
    `;
  }

  // ── 7. Filter Tabs Switching ────────────────────────────
  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeFilter = pill.dataset.filter;
      renderErrorCards();
    });
  });

  // ── 8. Apply Single Error ───────────────────────────────
  window.applySingleError = function(id) {
    const err = currentErrors.find(e => e.id === id);
    if (!err || err.applied) return;

    const original = err.original;
    const suggested = err.suggested || err.suggestion || '';

    const currentText = documentText.value;
    if (currentText.includes(original)) {
      documentText.value = currentText.replace(original, suggested);
      updateStats();
      err.applied = true;
      err.dismissed = true;
      showToast(`Đã sửa: "${original}" ➔ "${suggested}"`);
    } else {
      showToast(`Không tìm thấy vị trí từ "${original}" trong văn bản hiện tại.`, 'warning');
      err.dismissed = true;
    }

    updateFilterCounts();
    renderErrorCards();
    if (currentInputTab === 'highlight') {
      renderInteractiveHighlights();
    }
  };

  // ── 9. Apply All Errors ─────────────────────────────────
  btnApplyAll.addEventListener('click', () => {
    const pendingErrors = currentErrors.filter(e => !e.dismissed);
    if (pendingErrors.length === 0) {
      showToast('Không có lỗi nào để áp dụng!', 'warning');
      return;
    }

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
    updateStats();
    updateFilterCounts();
    renderErrorCards();
    if (currentInputTab === 'highlight') {
      renderInteractiveHighlights();
    }
    renderScore(10.0);
    scoreTitle.textContent = 'Đã Chuẩn Hóa Toàn Bộ! 🎉';
    scoreSummary.textContent = `Đã tự động thay thế ${count} vị trí từ trong văn bản.`;
    showToast(`Đã tự động sửa ${count} lỗi trong văn bản!`);
  });

  // ── 10. Copy Text to Clipboard ──────────────────────────
  btnCopyText.addEventListener('click', () => {
    const text = documentText.value.trim();
    if (!text) {
      showToast('Chưa có văn bản để sao chép!', 'warning');
      return;
    }
    navigator.clipboard.writeText(text).then(() => {
      showToast('📋 Đã sao chép văn bản vào Clipboard!');
    }).catch(err => {
      showToast('Không thể copy: ' + err.message, 'error');
    });
  });

  // ── 11. Export Clean Document to Word (.docx) ────────────
  btnExportDocx.addEventListener('click', async () => {
    const text = documentText.value.trim();
    if (!text && !selectedFile) {
      showToast('Chưa có nội dung hoặc file để xuất!', 'warning');
      return;
    }

    try {
      btnExportDocx.disabled = true;
      btnExportDocx.innerHTML = '<span>⏳</span><span>Đang Xử Lý File Word...</span>';

      // TRƯỜNG HỢP 1: Đã upload file Word (.docx) -> Sửa trực tiếp trên file gốc GIỮ NGUYÊN 100% FORMAT
      if (selectedFile && selectedFile.name.toLowerCase().endsWith('.docx')) {
        const hasSpecificApplied = currentErrors.some(e => e.applied);
        const targetErrors = hasSpecificApplied 
          ? currentErrors.filter(e => e.applied)
          : currentErrors;

        const appliedReplacements = targetErrors.map(e => ({
          original: e.original,
          suggested: e.suggested || e.suggestion || ''
        })).filter(e => e.original && e.suggested && e.original !== e.suggested);

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('replacements', JSON.stringify(appliedReplacements));
        formData.append('highlight_changes', 'false');

        const response = await fetch('/api/v1/proofread/export-docx-inplace', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          throw new Error(`In-place export failed with HTTP ${response.status}`);
        }

        const blob = await response.blob();
        const baseName = selectedFile.name.replace(/\.[^/.]+$/, "");
        const filename = `${baseName}_da_chinh_sua.docx`;
        
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);

        showToast(`📥 Đã tải file Word gốc (Giữ nguyên 100% Bảng biểu & Format): ${filename}`);
      } 
      // TRƯỜNG HỢP 2: Người dùng gõ text hoặc văn bản từ PDF/TXT -> Tạo file Word mới chuẩn NĐ 30
      else {
        let filename = 'Van_ban_hoan_chinh.docx';
        if (currentUploadedFilename) {
          const base = currentUploadedFilename.replace(/\.[^/.]+$/, "");
          filename = `${base}_da_chinh_sua.docx`;
        }

        const response = await fetch('/api/v1/proofread/export-docx', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: text,
            filename: filename
          })
        });

        if (!response.ok) {
          throw new Error(`Export failed with HTTP ${response.status}`);
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);

        showToast(`📥 Đã xuất file Word chuẩn thể thức: ${filename}`);
      }
    } catch (err) {
      console.error('Export docx error:', err);
      showToast('Lỗi khi xuất file Word: ' + err.message, 'error');
    } finally {
      btnExportDocx.disabled = false;
      btnExportDocx.innerHTML = '<span>📥</span><span>Tải File Word (.docx)</span>';
    }
  });


  // ── 12. Reset State Helper ──────────────────────────────
  function resetResults() {
    currentErrors = [];
    renderScore(0);
    scoreValue.textContent = '--';
    scoreTitle.textContent = 'Sẵn Sàng Phân Tích';
    scoreSummary.textContent = 'Nhập văn bản hoặc tải file lên, sau đó bấm "Bắt Đầu Rà Soát" để AI quét lỗi.';
    latencyStats.textContent = 'Tốc độ: -- ms • Tokens: --';
    tabHighlightBtn.style.display = 'none';
    switchToTextTab();
    hideQuickFixTooltip();
    updateFilterCounts();
    renderErrorCards();
  }

  // ── 13. Toast Notification Helper ───────────────────────
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';
    if (type === 'error') {
      toast.style.borderLeft = '4px solid #ef4444';
    } else if (type === 'warning') {
      toast.style.borderLeft = '4px solid #f59e0b';
    } else {
      toast.style.borderLeft = '4px solid #10b981';
    }
    toast.innerHTML = `<span>${message}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(20px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function escapeHtml(text) {
    if (!text) return '';
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  }
  // ════════════════════════════════════════════════════════
  // GLOSSARY MANAGEMENT MODULE
  // ════════════════════════════════════════════════════════

  const navAgent0 = document.getElementById('navAgent0');
  const navGlossary = document.getElementById('navGlossary');
  const glossaryWorkspace = document.getElementById('glossaryWorkspace');
  const workspaceToolbar = document.querySelector('.workspace-toolbar');
  const appLayout = document.querySelector('.app-layout');

  // Glossary DOM Elements
  const glossarySearchInput = document.getElementById('glossarySearchInput');
  const glossaryDomainFilter = document.getElementById('glossaryDomainFilter');
  const glossaryTableBody = document.getElementById('glossaryTableBody');
  const glossaryTotalCount = document.getElementById('glossaryTotalCount');
  const btnAddTerm = document.getElementById('btnAddTerm');
  const btnReloadRules = document.getElementById('btnReloadRules');
  const btnTestRules = document.getElementById('btnTestRules');
  const glossaryTestInput = document.getElementById('glossaryTestInput');
  const glossaryTestResult = document.getElementById('glossaryTestResult');

  // Stats
  const statTotalTerms = document.getElementById('statTotalTerms');
  const statTotalDomains = document.getElementById('statTotalDomains');
  const statsDomainBreakdown = document.getElementById('statsDomainBreakdown');

  // Modal
  const glossaryModal = document.getElementById('glossaryModal');
  const modalTitle = document.getElementById('modalTitle');
  const modalTermInput = document.getElementById('modalTermInput');
  const modalDomainInput = document.getElementById('modalDomainInput');
  const modalFullNameVi = document.getElementById('modalFullNameVi');
  const modalFullNameEn = document.getElementById('modalFullNameEn');
  const modalVariantsInput = document.getElementById('modalVariantsInput');
  const modalDescInput = document.getElementById('modalDescInput');
  const modalDoNotTranslate = document.getElementById('modalDoNotTranslate');
  const btnModalSave = document.getElementById('btnModalSave');
  const btnModalCancel = document.getElementById('btnModalCancel');
  const btnModalClose = document.getElementById('btnModalClose');

  let glossaryEditMode = null; // null = add, string = term being edited

  // ── Navigation Toggle ──────────────────────────────────
  if (navGlossary) {
    navGlossary.addEventListener('click', () => {
      navAgent0.classList.remove('active');
      navGlossary.classList.add('active');
      workspaceToolbar.style.display = 'none';
      appLayout.style.display = 'none';
      glossaryWorkspace.style.display = 'flex';
      loadGlossaryData();
      loadGlossaryStats();
    });
  }
  if (navAgent0) {
    navAgent0.addEventListener('click', () => {
      navGlossary.classList.remove('active');
      navAgent0.classList.add('active');
      workspaceToolbar.style.display = '';
      appLayout.style.display = '';
      glossaryWorkspace.style.display = 'none';
    });
  }

  // ── Load Glossary Data ─────────────────────────────────
  let glossaryDebounceTimer = null;

  async function loadGlossaryData() {
    const query = glossarySearchInput ? glossarySearchInput.value.trim() : '';
    const domain = glossaryDomainFilter ? glossaryDomainFilter.value : '';

    let url = '/api/v1/rules/glossary?';
    if (query) url += `query=${encodeURIComponent(query)}&`;
    if (domain) url += `domain=${encodeURIComponent(domain)}&`;

    try {
      const res = await fetch(url);
      const data = await res.json();
      renderGlossaryTable(data.items || []);
      glossaryTotalCount.textContent = `${data.total || 0} thuật ngữ`;
    } catch (e) {
      glossaryTableBody.innerHTML = `<tr class="glossary-empty-row"><td colspan="5"><div class="glossary-empty-state"><span>⚠️</span><p>Lỗi tải dữ liệu</p></div></td></tr>`;
    }
  }

  function renderGlossaryTable(items) {
    if (!items.length) {
      glossaryTableBody.innerHTML = `<tr class="glossary-empty-row"><td colspan="5"><div class="glossary-empty-state"><span>📚</span><p>Không tìm thấy thuật ngữ nào</p></div></td></tr>`;
      return;
    }
    glossaryTableBody.innerHTML = items.map(item => `
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
  }

  // Search & Filter (with debounce)
  if (glossarySearchInput) {
    glossarySearchInput.addEventListener('input', () => {
      clearTimeout(glossaryDebounceTimer);
      glossaryDebounceTimer = setTimeout(loadGlossaryData, 300);
    });
  }
  if (glossaryDomainFilter) {
    glossaryDomainFilter.addEventListener('change', loadGlossaryData);
  }

  // ── Load Stats ─────────────────────────────────────────
  async function loadGlossaryStats() {
    try {
      const res = await fetch('/api/v1/rules/stats');
      const data = await res.json();
      statTotalTerms.textContent = data.total_glossary_terms || 0;
      const domains = data.domains || {};
      const domainKeys = Object.keys(domains);
      statTotalDomains.textContent = domainKeys.length;

      // Domain breakdown badges
      statsDomainBreakdown.innerHTML = domainKeys.map(d =>
        `<span class="glossary-domain-badge" data-domain="${escapeHtml(d)}">${escapeHtml(d)} (${domains[d]})</span>`
      ).join('');

      // Populate domain filter dropdown
      if (glossaryDomainFilter) {
        const currentVal = glossaryDomainFilter.value;
        glossaryDomainFilter.innerHTML = '<option value="">Tất cả lĩnh vực</option>' +
          domainKeys.sort().map(d => `<option value="${escapeHtml(d)}">${escapeHtml(d)}</option>`).join('');
        glossaryDomainFilter.value = currentVal;
      }
    } catch (e) {
      // Silently fail
    }
  }

  // ── Reload Rules ───────────────────────────────────────
  if (btnReloadRules) {
    btnReloadRules.addEventListener('click', async () => {
      btnReloadRules.disabled = true;
      btnReloadRules.textContent = '⏳ Đang nạp...';
      try {
        const res = await fetch('/api/v1/rules/reload', { method: 'POST' });
        const data = await res.json();
        showToast(`✅ ${data.message} (${data.glossary_count} thuật ngữ, ${data.reload_time_ms}ms)`);
        loadGlossaryData();
        loadGlossaryStats();
      } catch (e) {
        showToast('❌ Lỗi reload Rule Engine');
      }
      btnReloadRules.disabled = false;
      btnReloadRules.textContent = '🔄 Đồng Bộ';
    });
  }

  // ── Test Playground ────────────────────────────────────
  if (btnTestRules) {
    btnTestRules.addEventListener('click', async () => {
      const text = glossaryTestInput.value.trim();
      if (!text) return;
      btnTestRules.disabled = true;
      btnTestRules.textContent = '⏳ Đang kiểm tra...';
      try {
        const res = await fetch('/api/v1/rules/test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text }),
        });
        const data = await res.json();
        glossaryTestResult.style.display = 'block';

        if (data.violations && data.violations.length > 0) {
          glossaryTestResult.innerHTML = data.violations.map(v => `
            <div class="test-violation-item">
              <span class="test-violation-original">${escapeHtml(v.original_text)}</span>
              <span class="test-violation-arrow">➔</span>
              <span class="test-violation-fix">${escapeHtml(v.suggested_fix)}</span>
            </div>
          `).join('') + `<div class="test-processing-time">⚡ ${data.processing_time_ms}ms</div>`;
        } else {
          glossaryTestResult.innerHTML = `<div class="test-no-issues">✅ Không phát hiện vi phạm quy chuẩn</div><div class="test-processing-time">⚡ ${data.processing_time_ms}ms</div>`;
        }
      } catch (e) {
        glossaryTestResult.style.display = 'block';
        glossaryTestResult.innerHTML = `<div style="color: #ef4444;">❌ Lỗi kiểm tra</div>`;
      }
      btnTestRules.disabled = false;
      btnTestRules.textContent = '⚡ Kiểm Tra';
    });
  }

  // ── Modal: Add / Edit ──────────────────────────────────
  function openModal(mode = 'add', termData = null) {
    glossaryEditMode = mode === 'edit' ? termData.term : null;
    modalTitle.textContent = mode === 'edit' ? '✏️ Chỉnh Sửa Thuật Ngữ' : '➕ Thêm Thuật Ngữ Mới';
    modalTermInput.value = termData ? termData.term : '';
    modalTermInput.disabled = mode === 'edit';
    modalDomainInput.value = termData ? (termData.domain || '') : '';
    modalFullNameVi.value = termData ? (termData.full_name_vi || '') : '';
    modalFullNameEn.value = termData ? (termData.full_name_en || '') : '';
    modalVariantsInput.value = termData ? (termData.incorrect_variants || []).join(', ') : '';
    modalDescInput.value = termData ? (termData.description || '') : '';
    modalDoNotTranslate.checked = termData ? !!termData.do_not_translate : false;
    glossaryModal.style.display = 'flex';
  }

  function closeModal() {
    glossaryModal.style.display = 'none';
    glossaryEditMode = null;
  }

  if (btnAddTerm) btnAddTerm.addEventListener('click', () => openModal('add'));
  if (btnModalCancel) btnModalCancel.addEventListener('click', closeModal);
  if (btnModalClose) btnModalClose.addEventListener('click', closeModal);

  if (btnModalSave) {
    btnModalSave.addEventListener('click', async () => {
      const term = modalTermInput.value.trim();
      if (!term) {
        showToast('⚠️ Vui lòng nhập thuật ngữ chuẩn');
        return;
      }
      const variants = modalVariantsInput.value.split(',').map(v => v.trim()).filter(Boolean);

      const payload = {
        term,
        domain: modalDomainInput.value.trim() || 'General',
        full_name_vi: modalFullNameVi.value.trim(),
        full_name_en: modalFullNameEn.value.trim(),
        incorrect_variants: variants,
        description: modalDescInput.value.trim(),
        do_not_translate: modalDoNotTranslate.checked,
      };

      btnModalSave.disabled = true;
      try {
        let res;
        if (glossaryEditMode) {
          res = await fetch(`/api/v1/rules/glossary/${encodeURIComponent(glossaryEditMode)}`, {
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
          showToast(`✅ ${data.message}`);
          closeModal();
          loadGlossaryData();
          loadGlossaryStats();
        } else {
          showToast(`⚠️ ${data.detail || 'Lỗi lưu thuật ngữ'}`);
        }
      } catch (e) {
        showToast('❌ Lỗi kết nối server');
      }
      btnModalSave.disabled = false;
    });
  }

  // Global edit/delete handlers
  window._glossaryEdit = async (term) => {
    try {
      const res = await fetch(`/api/v1/rules/glossary/${encodeURIComponent(term)}`);
      if (res.ok) {
        const data = await res.json();
        openModal('edit', data);
      }
    } catch (e) { /* silent */ }
  };

  window._glossaryDelete = async (term) => {
    if (!confirm(`Xóa thuật ngữ "${term}" khỏi kho từ điển?`)) return;
    try {
      const res = await fetch(`/api/v1/rules/glossary/${encodeURIComponent(term)}`, { method: 'DELETE' });
      const data = await res.json();
      if (res.ok) {
        showToast(`✅ ${data.message}`);
        loadGlossaryData();
        loadGlossaryStats();
      } else {
        showToast(`⚠️ ${data.detail || 'Lỗi xóa'}`);
      }
    } catch (e) {
      showToast('❌ Lỗi kết nối server');
    }
  };

});
