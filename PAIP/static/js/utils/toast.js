/**
 * PAIP Toast Notifications & System Status Helper
 */

import { $, createElement } from './dom.js';

export function showToast(message, type = 'info', duration = 3500) {
  const container = $('#toastContainer');
  if (!container) return;

  const iconMap = {
    success: '✅',
    error: '❌',
    info: 'ℹ️',
    warning: '⚠️'
  };

  const toast = createElement('div', `toast ${type}`, `
    <span>${iconMap[type] || 'ℹ️'}</span>
    <span>${message}</span>
  `);

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

export function updateSystemStatus(label, isBusy = false) {
  const statusLabel = $('#statusLabel');
  const statusDot = $('.status-dot');
  
  if (statusLabel) statusLabel.textContent = label;
  if (statusDot) {
    if (isBusy) {
      statusDot.classList.add('busy');
    } else {
      statusDot.classList.remove('busy');
    }
  }
}
