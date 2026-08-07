/**
 * PAIP Frontend Main Application Entry Point
 */

import { $ } from './utils/dom.js';
import { appState } from './state.js';
import { inlineEditor } from './modules/inline_editor.js';
import { proofreader } from './modules/proofreader.js';
import { glossaryAdmin } from './modules/glossary_admin.js';

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Subsystems
  inlineEditor.init();
  proofreader.init();
  glossaryAdmin.init();

  // Workspace Navigation Switching
  const navAgent0 = $('#navAgent0');
  const navGlossary = $('#navGlossary');
  const glossaryWorkspace = $('#glossaryWorkspace');
  const workspaceToolbar = $('.workspace-toolbar');
  const appLayout = $('.app-layout');

  if (navAgent0 && navGlossary) {
    navAgent0.addEventListener('click', () => {
      appState.currentView = 'agent0';
      navGlossary.classList.remove('active');
      navAgent0.classList.add('active');
      if (workspaceToolbar) workspaceToolbar.style.display = '';
      if (appLayout) appLayout.style.display = '';
      if (glossaryWorkspace) glossaryWorkspace.style.display = 'none';
    });

    navGlossary.addEventListener('click', () => {
      appState.currentView = 'glossary';
      navAgent0.classList.remove('active');
      navGlossary.classList.add('active');
      if (workspaceToolbar) workspaceToolbar.style.display = 'none';
      if (appLayout) appLayout.style.display = 'none';
      if (glossaryWorkspace) glossaryWorkspace.style.display = 'flex';
      glossaryAdmin.loadData();
      glossaryAdmin.loadStats();
    });
  }

  // Subscribe to state changes if needed
  appState.on('errorsUpdated', (errors) => {
    proofreader.updateFilterCounts();
    proofreader.renderErrorCards();
    if (appState.currentInputTab === 'highlight') {
      proofreader.renderInteractiveHighlights();
    }
  });

  console.log('🚀 PTSC AI Platform (PAIP) Frontend Loaded Successfully.');
});
