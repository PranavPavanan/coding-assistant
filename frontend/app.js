/**
 * RAG GitHub Assistant - Reworked Frontend
 * Sidebar layout, panel routing, and modular API helpers
 */

class ApiClient {
  constructor(baseUrl) { this.baseUrl = baseUrl; }
  async req(path, opts = {}) {
    const res = await fetch(`${this.baseUrl}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...opts
    });
    if (!res.ok) {
      let detail = '';
      try { const j = await res.json(); detail = j.detail || JSON.stringify(j); } catch {}
      throw new Error(detail || `${res.status} ${res.statusText}`);
    }
    return res.json();
  }
  health() { return this.req('/health'); }
  searchRepositories(query, language, minStars) { return this.req('/search/repositories', { method: 'POST', body: JSON.stringify({ query, language, min_stars: minStars }) }); }
  startIndexing(repository_url, branch) { return this.req('/index/start', { method: 'POST', body: JSON.stringify({ repository_url, branch }) }); }
  indexStatus(taskId) { return this.req(`/index/status/${taskId}`); }
  indexStats() { return this.req('/index/stats'); }
  clearIndex() { return this.req('/index/current', { method: 'DELETE' }); }
  chatQuery(query, conversation_id, session_id) { return this.req('/chat/query', { method: 'POST', body: JSON.stringify({ query, conversation_id, session_id }) }); }
}

class RAGApp {
  constructor() {
    this.api = new ApiClient('http://localhost:8000/api');
    this.state = {
      // Repository & index
      selectedRepository: null,
      searchResults: [],
      isSearching: false,
      indexStats: null,
      currentIndexingTask: null,
      isIndexing: false,
      // Chat
      messages: [],
      conversationId: null,
      sessionId: null,
      currentConversation: null,
      conversations: [],
      isQuerying: false,
      // UI
      route: 'search',
      elapsedMs: 0,
      elapsedTimer: null
    };
    this.init();
  }

  init() {
    this.ensureToastContainer();
    this.bindNav();
    this.bindEvents();
    this.loadIndexStats();
    // Restore last route if possible
    const savedRoute = localStorage.getItem('rag.route');
    if (savedRoute && ['search','index','chat'].includes(savedRoute)) {
      // If chat saved but not indexed, fallback to search
      this.switchPanel(savedRoute === 'chat' && !this.isIndexed() ? 'search' : savedRoute);
    } else {
      this.switchPanel('search');
    }
    this.setupScrollToBottom();
    this.setupGlobalShortcuts();
    this.icons();
  }

  icons() { if (typeof lucide !== 'undefined') lucide.createIcons(); }

  // Routing
  bindNav() {
    document.querySelectorAll('.nav-item').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const route = e.currentTarget.dataset.route;
        if (!e.currentTarget.disabled) this.switchPanel(route);
      });
    });
    const goToChat = document.getElementById('go-to-chat');
    if (goToChat) goToChat.addEventListener('click', () => this.switchPanel('chat'));
  }

  switchPanel(route) {
    this.state.route = route;
    try { localStorage.setItem('rag.route', route); } catch {}
    // nav active
    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.route === route);
    });
    // panels
    ['panel-search', 'panel-index', 'panel-chat'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.remove('active');
    });
    const map = { search: 'panel-search', index: 'panel-index', chat: 'panel-chat' };
    const panelId = map[route];
    const panel = document.getElementById(panelId);
    if (panel) panel.classList.add('active');

    // headline
    const headline = document.getElementById('headline-text');
    const title = route === 'search' ? 'Search GitHub' : route === 'index' ? 'Repository Indexing' : 'Chat about the Code';
    if (headline) headline.textContent = title;

    // route-specific refresh
    if (route === 'index') this.updateIndexDisplay();
    if (route === 'chat') this.updateChatInterface();
  }

  // Toasts (minimal)
  toast(msg) { console.info('[Toast]', msg); }
  ensureToastContainer() {
    if (!document.querySelector('.toast-container')) {
      const c = document.createElement('div'); c.className = 'toast-container'; document.body.appendChild(c);
    }
  }
  showToast(message, timeout = 2000) {
    this.ensureToastContainer();
    const c = document.querySelector('.toast-container');
    const t = document.createElement('div'); t.className = 'toast'; t.textContent = message; c.appendChild(t);
    setTimeout(() => { t.remove(); }, timeout);
  }

  // API wrappers
  async safe(call, onError) {
    try { return await call(); } catch (e) { onError?.(e); throw e; }
  }

  // Events binding (forms/buttons)
  bindEvents() {
    // Search
    const searchForm = document.getElementById('search-form');
    if (searchForm) searchForm.addEventListener('submit', (e) => { e.preventDefault(); this.handleSearch(); });
    const clearSel = document.getElementById('clear-selection');
    if (clearSel) clearSel.addEventListener('click', () => this.clearSelection());

    // Indexing
    const startIdx = document.getElementById('start-indexing');
    if (startIdx) startIdx.addEventListener('click', () => this.handleStartIndexing());
    const clearIdx = document.getElementById('clear-index');
    if (clearIdx) clearIdx.addEventListener('click', () => this.handleClearIndex());
    const startQueryBtn = document.getElementById('start-querying');
    if (startQueryBtn) startQueryBtn.addEventListener('click', () => this.switchPanel('chat'));

    // Chat
    const chatForm = document.getElementById('chat-form');
    if (chatForm) chatForm.addEventListener('submit', (e) => { e.preventDefault(); this.handleChatSubmit(); });
    const newChatA = document.getElementById('new-chat-btn');
    const newChatB = document.getElementById('new-chat-header');
    if (newChatA) newChatA.addEventListener('click', () => this.createNewConversation());
    if (newChatB) newChatB.addEventListener('click', () => this.createNewConversation());
    const clearChat = document.getElementById('clear-chat');
    if (clearChat) clearChat.addEventListener('click', () => this.clearCurrentChat());
    const chatInput = document.getElementById('chat-input');
    if (chatInput) chatInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this.handleChatSubmit(); } });
  }

  // Icons refresh
  refreshIcons() { this.icons(); }

  // Helpers
  showError(id, msg) { const el = document.getElementById(id); if (el) { el.textContent = msg; el.classList.remove('hidden'); } }
  hideError(id) { const el = document.getElementById(id); if (el) el.classList.add('hidden'); }
  setLoading(btnId, isLoading, text = 'Loading...') {
    const btn = document.getElementById(btnId); if (!btn) return;
    const spinner = btn.querySelector('.btn-spinner'); const label = btn.querySelector('.btn-text');
    if (isLoading) { btn.disabled = true; spinner?.classList.remove('hidden'); if (label) label.textContent = text; }
    else { btn.disabled = false; spinner?.classList.add('hidden'); if (label) label.textContent = btn.dataset.originalText || label?.textContent || 'Submit'; }
  }

  // Search
  async handleSearch() {
    const q = document.getElementById('search-query').value.trim();
    if (!q) return this.showError('search-error', 'Please enter a search query');
    this.hideError('search-error');
    this.state.isSearching = true; this.setLoading('search-btn', true, 'Searching...');
    try {
      const res = await this.api.searchRepositories(q);
      this.state.searchResults = res.repositories || [];
      this.displaySearchResults();
      if (this.state.searchResults.length === 0) this.showError('search-error', 'No repositories found');
    } catch (e) {
      this.showError('search-error', e.message || 'Failed to search repositories');
      this.state.searchResults = [];
    } finally {
      this.state.isSearching = false; this.setLoading('search-btn', false);
    }
  }

  displaySearchResults() {
    const container = document.getElementById('search-results');
    const list = document.getElementById('results-list');
    const title = document.getElementById('results-title');
    if (this.state.searchResults.length === 0) { container.classList.add('hidden'); return; }
    title.textContent = `Search Results (${this.state.searchResults.length})`;
    list.innerHTML = '';
    this.state.searchResults.forEach(repo => {
      const item = document.createElement('div'); item.className = 'result-item';
      item.innerHTML = `
        <div class="result-header">
          <div class="result-name">
            <span>${repo.full_name}</span>
            <a href="${repo.html_url}" target="_blank" rel="noopener noreferrer" class="result-link"><i data-lucide="external-link"></i></a>
          </div>
          <button class="btn btn-sm">Select</button>
        </div>
        ${repo.description ? `<p class="result-description">${repo.description}</p>` : ''}
        <div class="result-stats">
          ${repo.language ? `<span class="repo-stat"><span class="language-dot"></span><span class="language-text">${repo.language}</span></span>` : ''}
          <span class="repo-stat"><i data-lucide="star"></i><span>${(repo.stars || 0).toLocaleString()}</span></span>
        </div>`;
      item.addEventListener('click', () => this.selectRepository(repo));
      list.appendChild(item);
    });
    container.classList.remove('hidden');
    this.refreshIcons();
  }

  selectRepository(repo) { this.state.selectedRepository = repo; this.displaySelectedRepository(); this.switchPanel('index'); }
  displaySelectedRepository() {
    const sel = document.getElementById('selected-repo');
    const name = document.getElementById('repo-name');
    const link = document.getElementById('repo-link');
    const desc = document.getElementById('repo-description');
    const lang = document.getElementById('repo-language');
    const stars = document.getElementById('repo-stars');
    if (this.state.selectedRepository) {
      name.textContent = this.state.selectedRepository.full_name;
      link.href = this.state.selectedRepository.html_url;
      desc.textContent = this.state.selectedRepository.description || '';
      stars.textContent = (this.state.selectedRepository.stars || 0).toLocaleString();
      if (this.state.selectedRepository.language) { lang.classList.remove('hidden'); lang.querySelector('.language-text').textContent = this.state.selectedRepository.language; } else { lang.classList.add('hidden'); }
      sel.classList.remove('hidden');
    } else { sel.classList.add('hidden'); }
  }
  clearSelection() { this.state.selectedRepository = null; this.displaySelectedRepository(); }

  // Indexing
  async handleStartIndexing() {
    const url = this.state.selectedRepository?.html_url || document.getElementById('repo-url').value.trim();
    if (!url) return this.showError('indexing-error', 'Please select a repository or enter a URL');
    this.hideError('indexing-error'); this.state.isIndexing = true; this.setLoading('start-indexing', true, 'Indexing in Progress...');
    try {
      const res = await this.api.startIndexing(url);
      this.state.currentIndexingTask = res; this.displayIndexingProgress(); this.startIndexingPolling();
    } catch (e) {
      this.showError('indexing-error', e.message || 'Failed to start indexing'); this.state.isIndexing = false;
    } finally { this.setLoading('start-indexing', false); }
  }
  displayIndexingProgress() { const el = document.getElementById('indexing-progress'); el.classList.remove('hidden'); this.updateIndexingStatus(); }
  updateIndexingStatus() {
    if (!this.state.currentIndexingTask) return;
    const t = this.state.currentIndexingTask;
    const icon = document.getElementById('progress-icon');
    const status = document.getElementById('progress-status');
    const perc = document.getElementById('progress-percentage');
    const fill = document.getElementById('progress-fill');
    const files = document.getElementById('files-processed');
    const total = document.getElementById('total-files');
    const err = document.getElementById('progress-error');
    const startQ = document.getElementById('start-querying');
    status.textContent = t.status;
    const iconMap = { completed: 'check-circle-2', failed: 'x-circle', running: 'loader-2', pending: 'alert-circle' };
    icon.setAttribute('data-lucide', iconMap[t.status] || 'alert-circle');
    if (t.status === 'running') icon.classList.add('animate-spin'); else icon.classList.remove('animate-spin');
    perc.textContent = `${t.progress.percentage.toFixed(1)}%`;
    fill.style.width = `${t.progress.percentage}%`;
    files.textContent = t.progress.files_processed; total.textContent = t.progress.total_files;
    if (t.error) { err.textContent = t.error; err.classList.remove('hidden'); } else { err.classList.add('hidden'); }
    if (t.status === 'completed') { startQ.classList.remove('hidden'); this.state.isIndexing = false; } else { startQ.classList.add('hidden'); }
    this.refreshIcons();
  }
  startIndexingPolling() {
    if (!this.state.currentIndexingTask?.task_id) return;
    const it = setInterval(async () => {
      try {
        const st = await this.api.indexStatus(this.state.currentIndexingTask.task_id);
        this.state.currentIndexingTask = st; this.updateIndexingStatus();
        if (st.status === 'completed' || st.status === 'failed') { clearInterval(it); this.state.isIndexing = false; await this.loadIndexStats(); }
      } catch (e) { console.error('Failed to fetch indexing status:', e); }
    }, 2000);
  }
  async handleClearIndex() {
    if (!confirm('Are you sure you want to clear the index?')) return;
    try { await this.api.clearIndex(); this.state.indexStats = null; this.state.currentIndexingTask = null; this.hideError('indexing-error'); this.updateIndexDisplay(); this.switchPanel('search'); this.updateIndexAwareness(); }
    catch (e) { this.showError('indexing-error', e.message || 'Failed to clear index'); }
  }
  async loadIndexStats() {
    try {
      const stats = await this.api.indexStats();
      this.state.indexStats = stats; this.updateIndexDisplay(); this.updateChatInterface(); this.updateIndexAwareness();
    } catch {
      this.state.indexStats = null; this.updateIndexAwareness();
    }
  }
  updateIndexAwareness() {
    // Enable/disable chat route
    const chatBtn = document.querySelector('.nav-item[data-route="chat"]');
    const isIndexed = this.isIndexed();
    if (chatBtn) { chatBtn.disabled = !isIndexed; }
    // Status chip and banner
    const chip = document.getElementById('status-chip');
    const text = document.getElementById('status-text');
    const banner = document.getElementById('repo-banner');
    const name = document.getElementById('repo-banner-name');
    const files = document.getElementById('repo-banner-files');
    if (isIndexed) {
      chip?.classList.add('ready'); if (text) text.textContent = 'Ready';
      if (banner) {
        banner.classList.remove('hidden');
        if (name) name.textContent = this.state.indexStats.repository_name || 'Unknown';
        if (files) files.textContent = `${this.state.indexStats.file_count} files`;
      }
      this.showToast('Index ready');
    } else {
      chip?.classList.remove('ready'); if (text) text.textContent = 'No index';
      banner?.classList.add('hidden');
    }
    this.refreshIcons();
  }
  isIndexed() {
    const s = this.state.indexStats; return !!(s?.is_indexed || (s?.file_count > 0) || (s?.vector_count > 0) || (s?.repository_name && s?.file_count >= 0));
  }
  updateIndexDisplay() {
    const cur = document.getElementById('current-index');
    const prog = document.getElementById('indexing-progress');
    const sel = document.getElementById('selected-repo-display');
    const urlGrp = document.getElementById('url-input-group');
    const startBtn = document.getElementById('start-indexing');
    const isIndexed = this.isIndexed();
    if (isIndexed) {
      cur.classList.remove('hidden');
      document.getElementById('index-repo-name').textContent = this.state.indexStats.repository_name || 'Unknown';
      document.getElementById('index-file-count').textContent = this.state.indexStats.file_count || 0;
      document.getElementById('index-vector-count').textContent = this.state.indexStats.vector_count || 0;
      const t = startBtn?.querySelector('.btn-text'); if (t) t.textContent = 'Re-index Repository';
    } else {
      cur.classList.add('hidden'); const t = startBtn?.querySelector('.btn-text'); if (t) t.textContent = 'Start Indexing';
    }
    if (this.state.currentIndexingTask) prog.classList.remove('hidden'); else prog.classList.add('hidden');
    if (this.state.selectedRepository) { sel.classList.remove('hidden'); document.getElementById('selected-repo-name').textContent = this.state.selectedRepository.full_name; urlGrp.classList.add('hidden'); }
    else { sel.classList.add('hidden'); urlGrp.classList.remove('hidden'); }
  }

  // Chat
  updateChatInterface() {
    const noIdx = document.getElementById('no-index-message');
    const welcome = document.getElementById('welcome-message');
    const input = document.getElementById('chat-input');
    const submit = document.getElementById('chat-submit');
    const repoBar = document.getElementById('repo-info-bar');
    const statsBar = document.getElementById('index-stats-bar');
    const clearBtn = document.getElementById('clear-chat');
    if (this.isIndexed()) {
      noIdx.classList.add('hidden'); welcome.classList.remove('hidden');
      input.disabled = this.state.isQuerying; input.placeholder = `Ask a question about ${this.state.indexStats?.repository_name || 'the code'}...`;
      submit.disabled = this.state.isQuerying;
      const sendIcon = submit.querySelector('[data-lucide="send"]');
      const spinIcon = submit.querySelector('[data-lucide="loader-2"]');
      if (this.state.isQuerying) { sendIcon.classList.add('hidden'); spinIcon.classList.remove('hidden'); submit.title = 'AI is processing your query...'; }
      else { sendIcon.classList.remove('hidden'); spinIcon.classList.add('hidden'); submit.title = 'Send message'; }
      if (this.state.messages.length > 0) clearBtn.disabled = false;
      if (this.state.indexStats?.repository_name) {
        document.getElementById('chat-repo-name').textContent = this.state.indexStats.repository_name;
        repoBar.classList.remove('hidden');
      }
  const statsRepoName = document.getElementById('stats-repo-name');
  const statsFileCount = document.getElementById('stats-file-count');
  if (statsRepoName) statsRepoName.textContent = this.state.indexStats?.repository_name || 'Unknown';
  if (statsFileCount) statsFileCount.textContent = `${this.state.indexStats?.file_count ?? 0} files indexed`;
  if (statsBar) statsBar.classList.remove('hidden');
    } else {
      noIdx.classList.remove('hidden'); welcome.classList.add('hidden');
  input.disabled = true; input.placeholder = 'Index a repository first...'; submit.disabled = true; clearBtn.disabled = true; repoBar.classList.add('hidden'); if (statsBar) statsBar.classList.add('hidden');
    }
  }

  async handleChatSubmit() {
    const input = document.getElementById('chat-input');
    const query = input.value.trim(); if (!query || this.state.isQuerying) return;
    if (!this.isIndexed()) return this.showError('chat-error', 'Please index a repository first');
    const userMsg = { role: 'user', content: query, timestamp: new Date().toISOString() };
    this.addMessage(userMsg); input.value = ''; this.hideError('chat-error'); this.state.isQuerying = true; this.startElapsedTimer(); this.updateChatInterface(); this.displayMessages();
    try {
      const res = await this.api.chatQuery(query, this.state.conversationId, this.state.sessionId);
      if (!this.state.sessionId) this.state.sessionId = res.session_id;
      if (!this.state.conversationId) {
        this.state.conversationId = res.conversation_id;
        if (!this.state.currentConversation) {
          const conv = { id: res.conversation_id, title: 'New Chat', messages: [userMsg], createdAt: new Date().toISOString(), lastActivity: new Date().toISOString() };
          this.state.currentConversation = conv; this.state.conversations.push(conv); this.updateConversationTabs();
        }
      }
      const assistantMsg = { role: 'assistant', content: res.answer || res.response, timestamp: new Date().toISOString(), sources: res.sources || res.references };
      this.addMessage(assistantMsg); this.displayMessages();
      if (this.state.currentConversation && this.state.currentConversation.title === 'New Chat' && this.state.currentConversation.messages.length === 1) {
        const title = query.slice(0, 30); this.state.currentConversation.title = title.length < query.length ? `${title}...` : title; this.updateConversationTabs();
      }
    } catch (e) {
      this.showError('chat-error', e.message || 'Failed to process query');
    } finally {
      this.state.isQuerying = false; this.stopElapsedTimer(); this.updateChatInterface();
    }
  }

  addMessage(m) { this.state.messages.push(m); if (this.state.currentConversation) { this.state.currentConversation.messages.push(m); this.state.currentConversation.lastActivity = new Date().toISOString(); } this.displayMessages(); }
  displayMessages() {
    const box = document.getElementById('chat-messages'); const noIdx = document.getElementById('no-index-message'); const welcome = document.getElementById('welcome-message');
    if (this.state.messages.length === 0) { noIdx.classList.remove('hidden'); welcome.classList.add('hidden'); return; }
    noIdx.classList.add('hidden'); welcome.classList.add('hidden');
    box.querySelectorAll('.message, .generating-message').forEach(n => n.remove());
    this.state.messages.forEach((m, i) => box.appendChild(this.createMessageElement(m, i)));
    if (this.state.isQuerying) box.appendChild(this.createGeneratingElement());
    box.scrollTop = box.scrollHeight;
  }
  createMessageElement(m) {
    const wrap = document.createElement('div'); wrap.className = `message ${m.role}`;
    const content = document.createElement('div'); content.className = 'message-content';
    const text = document.createElement('div'); text.className = 'message-text'; text.textContent = m.content; content.appendChild(text);
    if (m.sources && m.sources.length > 0) {
      const sources = document.createElement('div'); sources.className = 'message-sources';
      const title = document.createElement('div'); title.className = 'message-sources-title'; title.textContent = 'Sources:'; sources.appendChild(title);
      m.sources.forEach(s => {
        const item = document.createElement('div'); item.className = 'source-item';
        const header = document.createElement('div'); header.className = 'source-header';
        const filePath = s.file || s.file_path || s.path || 'unknown';
        const lineStart = s.line_start || s.start_line || 1; const lineEnd = s.line_end || s.end_line || lineStart;
        const score = s.score !== undefined ? ` (${(s.score * 100).toFixed(0)}%)` : '';
        header.innerHTML = `<i data-lucide=\"file-text\"></i><span class=\"source-file\">${filePath}</span><span class=\"source-lines\">(lines ${lineStart}-${lineEnd})${score}</span>`;
        const copyBtn = document.createElement('button'); copyBtn.className = 'btn btn-ghost btn-sm'; copyBtn.type = 'button'; copyBtn.textContent = 'Copy';
        copyBtn.addEventListener('click', async (ev) => {
          ev.stopPropagation();
          try { await navigator.clipboard.writeText((s.content || '')); this.showToast('Copied source'); } catch { this.showToast('Copy failed'); }
        });
        header.appendChild(copyBtn);
        item.appendChild(header);
        const code = document.createElement('div'); code.className = 'source-code'; const c = s.content || ''; code.textContent = c.length > 200 ? c.substring(0, 200) + '...' : c; item.appendChild(code);
        sources.appendChild(item);
      });
      content.appendChild(sources);
    }
    const ts = document.createElement('div'); ts.className = 'message-timestamp'; ts.textContent = new Date(m.timestamp).toLocaleTimeString(); content.appendChild(ts);
    wrap.appendChild(content); this.refreshIcons(); return wrap;
  }
  createGeneratingElement() { const d = document.createElement('div'); d.className = 'generating-message'; d.innerHTML = `<div class="flex items-center gap-3"><span class="loading loading-infinity loading-md text-primary"></span><div class="flex flex-col"><span class="text-sm font-medium">AI is thinking...</span><span class="text-xs text-gray-500 generating-timer">${Math.floor(this.state.elapsedMs / 1000)}s</span></div></div>`; return d; }
  startElapsedTimer() { this.state.elapsedMs = 0; this.state.elapsedTimer = setInterval(() => { this.state.elapsedMs += 1000; this.updateGeneratingTimer(); }, 1000); }
  stopElapsedTimer() { if (this.state.elapsedTimer) { clearInterval(this.state.elapsedTimer); this.state.elapsedTimer = null; } }
  updateGeneratingTimer() { const el = document.querySelector('.generating-timer'); if (el) el.textContent = `${Math.floor(this.state.elapsedMs / 1000)}s`; }
  createNewConversation() { const c = { id: `conv-${Date.now()}`, title: 'New Chat', messages: [], createdAt: new Date().toISOString(), lastActivity: new Date().toISOString() }; this.state.conversations.push(c); this.state.currentConversation = c; this.state.messages = []; this.state.conversationId = c.id; this.updateConversationTabs(); this.displayMessages(); this.updateChatInterface(); }
  updateConversationTabs() {
    const cont = document.getElementById('conversation-tabs'); const list = document.getElementById('tabs-list');
    if (this.state.conversations.length === 0) { cont.classList.add('hidden'); return; }
    cont.classList.remove('hidden'); list.innerHTML = '';
    this.state.conversations.forEach(c => {
      const el = document.createElement('div'); el.className = `conversation-tab ${c.id === this.state.currentConversation?.id ? 'active' : ''}`;
      const title = this.generateConversationTitle(c);
      el.innerHTML = `<i data-lucide="message-square"></i><span class="conversation-tab-title">${title}</span>${this.state.conversations.length > 1 ? `<button class="conversation-tab-close" data-conversation-id="${c.id}"><i data-lucide="x"></i></button>` : ''}`;
      el.addEventListener('click', () => this.switchToConversation(c.id));
      const closeBtn = el.querySelector('.conversation-tab-close'); if (closeBtn) closeBtn.addEventListener('click', (e) => { e.stopPropagation(); this.closeConversation(c.id); });
      list.appendChild(el);
    });
    this.refreshIcons();
  }
  generateConversationTitle(c) { if (c.title !== 'New Chat') return c.title; const first = c.messages.find(m => m.role === 'user'); if (first) { const t = first.content.slice(0, 30); return t.length < first.content.length ? `${t}...` : t; } return 'New Chat'; }
  switchToConversation(id) { const c = this.state.conversations.find(x => x.id === id); if (c) { this.state.currentConversation = c; this.state.messages = c.messages; this.state.conversationId = c.id; this.updateConversationTabs(); this.displayMessages(); } }
  closeConversation(id) { if (this.state.conversations.length <= 1) return; if (this.state.currentConversation?.id === id) { const other = this.state.conversations.find(x => x.id !== id); if (other) this.switchToConversation(other.id); } this.state.conversations = this.state.conversations.filter(x => x.id !== id); this.updateConversationTabs(); }
  clearCurrentChat() { if (confirm('Clear current conversation?')) { this.state.messages = []; this.state.conversationId = null; this.displayMessages(); this.hideError('chat-error'); } }

  // Scroll-to-bottom support
  setupScrollToBottom() {
    const chatContainer = document.querySelector('.chat-container');
    if (!chatContainer) return;
    let btn = document.getElementById('scroll-bottom-btn');
    if (!btn) {
      btn = document.createElement('button');
      btn.id = 'scroll-bottom-btn';
      btn.className = 'scroll-bottom-btn';
      btn.innerHTML = '<i data-lucide="chevrons-down"></i><span>New</span>';
      btn.addEventListener('click', () => {
        const box = document.getElementById('chat-messages');
        if (box) box.scrollTop = box.scrollHeight;
      });
      chatContainer.appendChild(btn);
    }
    const box = document.getElementById('chat-messages');
    if (!box) return;
    const toggle = () => {
      const nearBottom = (box.scrollHeight - box.scrollTop - box.clientHeight) < 80;
      btn.classList.toggle('show', !nearBottom);
      this.refreshIcons();
    };
    box.addEventListener('scroll', toggle);
    // initial
    setTimeout(toggle, 50);
  }

  // Global shortcuts
  setupGlobalShortcuts() {
    document.addEventListener('keydown', (e) => {
      if (e.key === '/' && this.state.route === 'chat') {
        const input = document.getElementById('chat-input');
        if (input && !input.disabled) { e.preventDefault(); input.focus(); }
      }
    });
  }
}

document.addEventListener('DOMContentLoaded', () => { window.ragApp = new RAGApp(); });
if (typeof module !== 'undefined' && module.exports) { module.exports = RAGApp; }
