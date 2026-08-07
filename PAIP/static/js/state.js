/**
 * PAIP Central Application State Management
 */

export const appState = {
  currentView: 'agent0', // 'agent0' | 'glossary'
  currentInputTab: 'text', // 'text' | 'highlight' | 'file'
  selectedFile: null,
  currentUploadedFilename: '',
  currentErrors: [],
  formatReport: null,
  activeFilter: 'all',
  isAnalyzing: false,
  totalSessionTokens: 0,
  glossaryTerms: [],
  activeTooltipErrorId: null,

  listeners: {},

  on(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(callback);
  },

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  },

  addTokens(tokens) {
    if (!tokens || isNaN(tokens)) return;
    this.totalSessionTokens += tokens;
    const sessionTokensEl = document.getElementById('sessionTokens');
    if (sessionTokensEl) {
      sessionTokensEl.textContent = `${this.totalSessionTokens.toLocaleString()} Tokens`;
    }
  }
};
