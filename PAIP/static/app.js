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
  const tabFileBtn = document.getElementById('tabFileBtn');
  const textModeContainer = document.getElementById('textModeContainer');
  const fileModeContainer = document.getElementById('fileModeContainer');
  const documentText = document.getElementById('documentText');
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
  let currentInputTab = 'text'; // 'text' | 'file'
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
    tabFileBtn.classList.remove('active');
    textModeContainer.style.display = 'flex';
    fileModeContainer.style.display = 'none';
    updateStats();
  }

  function switchToFileTab() {
    currentInputTab = 'file';
    tabFileBtn.classList.add('active');
    tabTextBtn.classList.remove('active');
    textModeContainer.style.display = 'none';
    fileModeContainer.style.display = 'flex';
  }

  tabTextBtn.addEventListener('click', switchToTextTab);
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

  async function analyzeText(text, mode, model, customInstructions) {
    setAnalyzingState(true);
    renderLoadingState();

    try {
      const payload = {
        document_text: text,
        mode: mode,
        custom_instructions: customInstructions || null,
        provider: model === 'mock' ? 'mock' : (model === 'openai' ? 'openai' : 'gemini')
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

  async function analyzeFile(file, mode, model, customInstructions) {
    setAnalyzingState(true);
    renderLoadingState();

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('mode', mode);
      if (customInstructions) {
        formData.append('custom_instructions', customInstructions);
      }
      formData.append('provider', model === 'mock' ? 'mock' : (model === 'openai' ? 'openai' : 'gemini'));

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
    latencyStats.textContent = `Tốc độ: ${latency}ms • Tokens lần này: ${tokens}`;

    // Render Score & Banner
    renderScore(result.score);
    renderScoreDetails(result);

    // Render Error Cards
    updateFilterCounts();
    renderErrorCards();

    if (currentErrors.length === 0) {
      showToast('Tuyệt vời! Không phát hiện lỗi nào trong văn bản.', 'info');
    } else {
      showToast(`Đã phát hiện ${currentErrors.length} điểm cần chuẩn hóa.`);
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
      punctuation: pendingErrors.filter(e => e.type === 'punctuation').length
    };

    document.getElementById('filterAll').textContent = `Tất cả (${counts.all})`;
    document.getElementById('filterSpelling').textContent = `Chính tả (${counts.spelling})`;
    document.getElementById('filterGrammar').textContent = `Ngữ pháp (${counts.grammar})`;
    document.getElementById('filterWordChoice').textContent = `Dùng từ (${counts.word_choice})`;
    document.getElementById('filterPunct').textContent = `Dấu câu (${counts.punctuation})`;
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

    let html = '';
    filtered.forEach(err => {
      const typeLabel = getTypeLabel(err.type);
      const badgeClass = `badge-${err.type}`;
      const original = escapeHtml(err.original);
      const suggested = escapeHtml(err.suggested || err.suggestion || '');
      const explanation = escapeHtml(err.explanation);

      html += `
        <div class="error-card" data-id="${err.id}">
          <div class="error-card-header">
            <span class="error-badge ${badgeClass}">${typeLabel}</span>
            <span style="font-size: 0.72rem; color: var(--text-muted);">${getSeverityLabel(err.severity)}</span>
          </div>

          <div class="diff-box">
            <span class="diff-original">${original}</span>
            <span class="diff-arrow">➔</span>
            <span class="diff-suggested">${suggested}</span>
          </div>

          <div class="error-explanation">${explanation}</div>

          <div class="card-actions">
            <button class="btn-apply-single" onclick="window.applySingleError('${err.id}')">
              Áp dụng
            </button>
          </div>
        </div>
      `;
    });

    errorListContainer.innerHTML = html;
  }

  function getTypeLabel(type) {
    const map = {
      spelling: 'Chính tả',
      grammar: 'Ngữ pháp',
      word_choice: 'Dùng từ',
      punctuation: 'Dấu câu'
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
});
