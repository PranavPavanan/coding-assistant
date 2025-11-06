/**
 * RAG GitHub Assistant - Frontend Application
 * Pure HTML, CSS, and JavaScript implementation
 */

class RAGApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000/api';
        this.state = {
            // Repository state
            selectedRepository: null,
            searchResults: [],
            isSearching: false,
            
            // Indexing state
            currentIndexingTask: null,
            isIndexing: false,
            indexStats: null,
            
            // Chat state
            messages: [],
            conversationId: null,
            sessionId: null,
            currentConversation: null,
            conversations: [],
            isQuerying: false,
            
            // UI state
            activeTab: 'search',
            elapsedMs: 0,
            elapsedTimer: null
        };
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadIndexStats();
        this.initializeLucideIcons();
        this.switchTab('search');
    }

    bindEvents() {
        // Tab navigation
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabId = e.currentTarget.dataset.tab;
                if (!e.currentTarget.disabled) {
                    this.switchTab(tabId);
                }
            });
        });

        // Search form
        document.getElementById('search-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSearch();
        });

        // Clear selection
        document.getElementById('clear-selection').addEventListener('click', () => {
            this.clearSelection();
        });

        // Start indexing
        document.getElementById('start-indexing').addEventListener('click', () => {
            this.handleStartIndexing();
        });

        // Clear index
        document.getElementById('clear-index').addEventListener('click', () => {
            this.handleClearIndex();
        });

        // Start querying
        document.getElementById('start-querying').addEventListener('click', () => {
            this.switchTab('chat');
        });

        // Chat form
        document.getElementById('chat-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleChatSubmit();
        });

        // New chat buttons
        document.getElementById('new-chat-btn').addEventListener('click', () => {
            this.createNewConversation();
        });
        document.getElementById('new-chat-header').addEventListener('click', () => {
            this.createNewConversation();
        });

        // Clear chat
        document.getElementById('clear-chat').addEventListener('click', () => {
            this.clearCurrentChat();
        });


        // Chat input enter key
        document.getElementById('chat-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleChatSubmit();
            }
        });
    }

    initializeLucideIcons() {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    // API Methods
    async apiRequest(endpoint, options = {}) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: 120000, // 2 minutes
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    async healthCheck() {
        return this.apiRequest('/health');
    }

    async searchRepositories(query, language, minStars) {
        return this.apiRequest('/search/repositories', {
            method: 'POST',
            body: JSON.stringify({ query, language, min_stars: minStars })
        });
    }

    async startIndexing(repositoryUrl, branch) {
        return this.apiRequest('/index/start', {
            method: 'POST',
            body: JSON.stringify({ repository_url: repositoryUrl, branch })
        });
    }

    async getIndexStatus(taskId) {
        return this.apiRequest(`/index/status/${taskId}`);
    }

    async getIndexStats() {
        return this.apiRequest('/index/stats');
    }

    async clearIndex() {
        return this.apiRequest('/index/current', { method: 'DELETE' });
    }

    async chatQuery(query, conversationId, sessionId) {
        return this.apiRequest('/chat/query', {
            method: 'POST',
            body: JSON.stringify({ query, conversation_id: conversationId, session_id: sessionId })
        });
    }

    // UI Methods
    switchTab(tabId) {
        // Update active tab buttons
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
            if (tab.dataset.tab === tabId) {
                tab.classList.add('active');
            }
        });

        // Hide all tab content areas
        const tabContentAreas = ['search-tab', 'indexing-tab', 'chat-tab'];
        tabContentAreas.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.classList.remove('active');
            }
        });

        // Show the target tab content
        const targetTabContent = document.getElementById(`${tabId}-tab`);
        if (targetTabContent) {
            targetTabContent.classList.add('active');
        }

        this.state.activeTab = tabId;
        this.updateTabStates();
        
        // If switching to indexing tab, update display
        if (tabId === 'indexing') {
            this.updateIndexDisplay();
        }
        
        // If switching to chat tab, update chat interface
        if (tabId === 'chat') {
            this.updateChatInterface();
        }
    }

    showError(elementId, message) {
        const errorElement = document.getElementById(elementId);
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
    }

    hideError(elementId) {
        const errorElement = document.getElementById(elementId);
        errorElement.classList.add('hidden');
    }

    setLoading(buttonId, isLoading, loadingText = 'Loading...') {
        const button = document.getElementById(buttonId);
        const spinner = button.querySelector('.btn-spinner');
        const text = button.querySelector('.btn-text');

        if (isLoading) {
            button.disabled = true;
            spinner.classList.remove('hidden');
            text.textContent = loadingText;
        } else {
            button.disabled = false;
            spinner.classList.add('hidden');
            text.textContent = button.dataset.originalText || 'Submit';
        }
    }

    // Search Methods
    async handleSearch() {
        const query = document.getElementById('search-query').value.trim();
        
        if (!query) {
            this.showError('search-error', 'Please enter a search query');
            return;
        }

        this.hideError('search-error');
        this.state.isSearching = true;
        this.setLoading('search-btn', true, 'Searching...');

        try {
            const response = await this.searchRepositories(query);
            this.state.searchResults = response.repositories || [];
            this.displaySearchResults();

            if (this.state.searchResults.length === 0) {
                this.showError('search-error', 'No repositories found');
            }
        } catch (error) {
            this.showError('search-error', error.message || 'Failed to search repositories');
            this.state.searchResults = [];
        } finally {
            this.state.isSearching = false;
            this.setLoading('search-btn', false);
        }
    }

    displaySearchResults() {
        const resultsContainer = document.getElementById('search-results');
        const resultsList = document.getElementById('results-list');
        const resultsTitle = document.getElementById('results-title');

        if (this.state.searchResults.length === 0) {
            resultsContainer.classList.add('hidden');
            return;
        }

        resultsTitle.textContent = `Search Results (${this.state.searchResults.length})`;
        resultsList.innerHTML = '';

        this.state.searchResults.forEach(repo => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            resultItem.innerHTML = `
                <div class="result-header">
                    <div class="result-name">
                        <span>${repo.full_name}</span>
                        <a href="${repo.html_url}" target="_blank" rel="noopener noreferrer" class="result-link">
                            <i data-lucide="external-link"></i>
                        </a>
                    </div>
                    <button class="btn btn-sm">Select</button>
                </div>
                ${repo.description ? `<p class="result-description">${repo.description}</p>` : ''}
                <div class="result-stats">
                    ${repo.language ? `
                        <span class="repo-stat">
                            <span class="language-dot"></span>
                            <span class="language-text">${repo.language}</span>
                        </span>
                    ` : ''}
                    <span class="repo-stat">
                        <i data-lucide="star"></i>
                        <span>${(repo.stars || 0).toLocaleString()}</span>
                    </span>
                </div>
            `;

            resultItem.addEventListener('click', () => {
                this.selectRepository(repo);
            });

            resultsList.appendChild(resultItem);
        });

        resultsContainer.classList.remove('hidden');
        this.initializeLucideIcons();
    }

    selectRepository(repo) {
        this.state.selectedRepository = repo;
        this.displaySelectedRepository();
        this.switchTab('indexing');
    }

    displaySelectedRepository() {
        const selectedRepoElement = document.getElementById('selected-repo');
        const repoName = document.getElementById('repo-name');
        const repoLink = document.getElementById('repo-link');
        const repoDescription = document.getElementById('repo-description');
        const repoLanguage = document.getElementById('repo-language');
        const repoStars = document.getElementById('repo-stars');

        if (this.state.selectedRepository) {
            repoName.textContent = this.state.selectedRepository.full_name;
            repoLink.href = this.state.selectedRepository.html_url;
            repoDescription.textContent = this.state.selectedRepository.description || '';
            repoStars.textContent = (this.state.selectedRepository.stars || 0).toLocaleString();

            if (this.state.selectedRepository.language) {
                repoLanguage.classList.remove('hidden');
                repoLanguage.querySelector('.language-text').textContent = this.state.selectedRepository.language;
            } else {
                repoLanguage.classList.add('hidden');
            }

            selectedRepoElement.classList.remove('hidden');
        } else {
            selectedRepoElement.classList.add('hidden');
        }
    }

    clearSelection() {
        this.state.selectedRepository = null;
        this.displaySelectedRepository();
    }

    // Indexing Methods
    async handleStartIndexing() {
        const url = this.state.selectedRepository?.html_url || document.getElementById('repo-url').value.trim();

        if (!url) {
            this.showError('indexing-error', 'Please select a repository or enter a URL');
            return;
        }

        this.hideError('indexing-error');
        this.state.isIndexing = true;
        this.setLoading('start-indexing', true, 'Indexing in Progress...');

        try {
            const response = await this.startIndexing(url);
            this.state.currentIndexingTask = response;
            this.displayIndexingProgress();
            this.startIndexingPolling();
        } catch (error) {
            this.showError('indexing-error', error.message || 'Failed to start indexing');
            this.state.isIndexing = false;
        } finally {
            this.setLoading('start-indexing', false);
        }
    }

    displayIndexingProgress() {
        const progressContainer = document.getElementById('indexing-progress');
        progressContainer.classList.remove('hidden');
        this.updateIndexingStatus();
    }

    updateIndexingStatus() {
        if (!this.state.currentIndexingTask) return;

        const task = this.state.currentIndexingTask;
        const progressIcon = document.getElementById('progress-icon');
        const progressStatus = document.getElementById('progress-status');
        const progressPercentage = document.getElementById('progress-percentage');
        const progressFill = document.getElementById('progress-fill');
        const filesProcessed = document.getElementById('files-processed');
        const totalFiles = document.getElementById('total-files');
        const progressError = document.getElementById('progress-error');
        const startQueryingBtn = document.getElementById('start-querying');

        // Update status
        progressStatus.textContent = task.status;
        
        // Update icon
        const iconMap = {
            'completed': 'check-circle-2',
            'failed': 'x-circle',
            'running': 'loader-2',
            'pending': 'alert-circle'
        };
        
        progressIcon.setAttribute('data-lucide', iconMap[task.status] || 'alert-circle');
        
        if (task.status === 'running') {
            progressIcon.classList.add('animate-spin');
        } else {
            progressIcon.classList.remove('animate-spin');
        }

        // Update progress
        progressPercentage.textContent = `${task.progress.percentage.toFixed(1)}%`;
        progressFill.style.width = `${task.progress.percentage}%`;
        filesProcessed.textContent = task.progress.files_processed;
        totalFiles.textContent = task.progress.total_files;

        // Show/hide error
        if (task.error) {
            progressError.textContent = task.error;
            progressError.classList.remove('hidden');
        } else {
            progressError.classList.add('hidden');
        }

        // Show start querying button when completed
        if (task.status === 'completed') {
            startQueryingBtn.classList.remove('hidden');
            this.state.isIndexing = false;
        } else {
            startQueryingBtn.classList.add('hidden');
        }

        this.initializeLucideIcons();
    }

    startIndexingPolling() {
        if (!this.state.currentIndexingTask?.task_id) return;

        const pollInterval = setInterval(async () => {
            try {
                const status = await this.getIndexStatus(this.state.currentIndexingTask.task_id);
                this.state.currentIndexingTask = status;
                this.updateIndexingStatus();

                if (status.status === 'completed' || status.status === 'failed') {
                    clearInterval(pollInterval);
                    this.state.isIndexing = false;
                    
                    // Refresh index stats
                    await this.loadIndexStats();
                }
            } catch (error) {
                console.error('Failed to fetch indexing status:', error);
            }
        }, 2000);
    }

    async handleClearIndex() {
        if (!confirm('Are you sure you want to clear the index?')) {
            return;
        }

        try {
            await this.clearIndex();
            this.state.indexStats = null;
            this.state.currentIndexingTask = null;
            this.hideError('indexing-error');
            this.updateIndexDisplay();
            this.switchTab('search');
        } catch (error) {
            this.showError('indexing-error', error.message || 'Failed to clear index');
        }
    }

    async loadIndexStats() {
        try {
            const stats = await this.getIndexStats();
            this.state.indexStats = stats;
            this.updateIndexDisplay();
            this.updateChatInterface();
            this.updateTabStates();
        } catch (error) {
            // Backend not available - disable chat tab
            this.state.indexStats = null;
            this.updateTabStates();
        }
    }

    updateTabStates() {
        const chatTab = document.querySelector('[data-tab="chat"]');
        const indexingTab = document.querySelector('[data-tab="indexing"]');
        
        // Check if repository is indexed - try multiple possible indicators
        const isIndexed = this.state.indexStats?.is_indexed || 
                         (this.state.indexStats?.file_count > 0) ||
                         (this.state.indexStats?.vector_count > 0) ||
                         (this.state.indexStats?.repository_name && this.state.indexStats?.file_count >= 0);
        
        if (isIndexed) {
            // Enable chat tab if repository is indexed
            if (chatTab) {
                chatTab.disabled = false;
                chatTab.classList.remove('disabled');
            }
            
            // Show indexing tab as completed
            if (indexingTab) {
                indexingTab.classList.add('indexed');
            }
        } else {
            // Disable chat tab if no repository is indexed
            if (chatTab) {
                chatTab.disabled = true;
                chatTab.classList.add('disabled');
            }
            
            if (indexingTab) {
                indexingTab.classList.remove('indexed');
            }
        }
    }

    updateIndexDisplay() {
        const currentIndexElement = document.getElementById('current-index');
        const indexingProgressElement = document.getElementById('indexing-progress');
        const selectedRepoDisplayElement = document.getElementById('selected-repo-display');
        const urlInputGroupElement = document.getElementById('url-input-group');
        const startIndexingBtn = document.getElementById('start-indexing');

        // Check if repository is indexed using the same logic as updateTabStates
        const isIndexed = this.state.indexStats?.is_indexed || 
                         (this.state.indexStats?.file_count > 0) ||
                         (this.state.indexStats?.vector_count > 0) ||
                         (this.state.indexStats?.repository_name && this.state.indexStats?.file_count >= 0);

        if (isIndexed) {
            // Show current index information
            currentIndexElement.classList.remove('hidden');
            document.getElementById('index-repo-name').textContent = this.state.indexStats.repository_name || 'Unknown';
            document.getElementById('index-file-count').textContent = this.state.indexStats.file_count || 0;
            document.getElementById('index-vector-count').textContent = this.state.indexStats.vector_count || 0;
            
            // Update button text to show we can query
            if (startIndexingBtn) {
                const btnText = startIndexingBtn.querySelector('.btn-text');
                if (btnText) {
                    btnText.textContent = 'Re-index Repository';
                }
            }
        } else {
            currentIndexElement.classList.add('hidden');
            
            // Reset button text
            if (startIndexingBtn) {
                const btnText = startIndexingBtn.querySelector('.btn-text');
                if (btnText) {
                    btnText.textContent = 'Start Indexing';
                }
            }
        }

        if (this.state.currentIndexingTask) {
            indexingProgressElement.classList.remove('hidden');
        } else {
            indexingProgressElement.classList.add('hidden');
        }

        if (this.state.selectedRepository) {
            selectedRepoDisplayElement.classList.remove('hidden');
            document.getElementById('selected-repo-name').textContent = this.state.selectedRepository.full_name;
            urlInputGroupElement.classList.add('hidden');
        } else {
            selectedRepoDisplayElement.classList.add('hidden');
            urlInputGroupElement.classList.remove('hidden');
        }
    }

    // Chat Methods
    updateChatInterface() {
        const noIndexMessage = document.getElementById('no-index-message');
        const welcomeMessage = document.getElementById('welcome-message');
        const chatInput = document.getElementById('chat-input');
        const chatSubmit = document.getElementById('chat-submit');
        const repoInfoBar = document.getElementById('repo-info-bar');
        const indexStatsBar = document.getElementById('index-stats-bar');
        const clearChatBtn = document.getElementById('clear-chat');

        if (this.state.indexStats?.is_indexed) {
            noIndexMessage.classList.add('hidden');
            welcomeMessage.classList.remove('hidden');
            chatInput.disabled = this.state.isQuerying;
            chatInput.placeholder = `Ask a question about ${this.state.indexStats.repository_name || 'the code'}...`;
            chatSubmit.disabled = this.state.isQuerying;
            
            // Update send button loading state
            const sendIcon = chatSubmit.querySelector('[data-lucide="send"]');
            const spinnerIcon = chatSubmit.querySelector('[data-lucide="loader-2"]');
            
            if (this.state.isQuerying) {
                sendIcon.classList.add('hidden');
                spinnerIcon.classList.remove('hidden');
                chatSubmit.title = 'AI is processing your query...';
            } else {
                sendIcon.classList.remove('hidden');
                spinnerIcon.classList.add('hidden');
                chatSubmit.title = 'Send message';
            }
            
            if (this.state.messages.length > 0) {
                clearChatBtn.disabled = false;
            }

            // Show repository info
            if (this.state.indexStats.repository_name) {
                document.getElementById('chat-repo-name').textContent = this.state.indexStats.repository_name;
                repoInfoBar.classList.remove('hidden');
            }

            // Show index stats
            document.getElementById('stats-repo-name').textContent = this.state.indexStats.repository_name || 'Unknown';
            document.getElementById('stats-file-count').textContent = `${this.state.indexStats.file_count} files indexed`;
            indexStatsBar.classList.remove('hidden');
        } else {
            noIndexMessage.classList.remove('hidden');
            welcomeMessage.classList.add('hidden');
            chatInput.disabled = true;
            chatInput.placeholder = 'Index a repository first...';
            chatSubmit.disabled = true;
            clearChatBtn.disabled = true;
            repoInfoBar.classList.add('hidden');
            indexStatsBar.classList.add('hidden');
        }
    }

    async handleChatSubmit() {
        const input = document.getElementById('chat-input');
        const query = input.value.trim();

        if (!query || this.state.isQuerying) {
            return;
        }

        if (!this.state.indexStats?.is_indexed) {
            this.showError('chat-error', 'Please index a repository first');
            return;
        }

        // Add user message
        const userMessage = {
            role: 'user',
            content: query,
            timestamp: new Date().toISOString()
        };

        this.addMessage(userMessage);
        input.value = '';
        this.hideError('chat-error');
        this.state.isQuerying = true;
        this.startElapsedTimer();
        this.updateChatInterface(); // Update UI to show loading state
        this.displayMessages(); // Show loading animation immediately

        try {
            const response = await this.chatQuery(
                query,
                this.state.conversationId,
                this.state.sessionId
            );

            // Handle session and conversation IDs
            if (!this.state.sessionId) {
                this.state.sessionId = response.session_id;
            }
            
            if (!this.state.conversationId) {
                this.state.conversationId = response.conversation_id;
                
                // Create new conversation if this is the first message
                if (!this.state.currentConversation) {
                    const newConversation = {
                        id: response.conversation_id,
                        title: 'New Chat',
                        messages: [userMessage],
                        createdAt: new Date().toISOString(),
                        lastActivity: new Date().toISOString()
                    };
                    this.state.currentConversation = newConversation;
                    this.state.conversations.push(newConversation);
                    this.updateConversationTabs();
                }
            }

            const assistantMessage = {
                role: 'assistant',
                content: response.answer || response.response,
                timestamp: new Date().toISOString(),
                sources: response.sources || response.references
            };

            this.addMessage(assistantMessage);
            this.displayMessages(); // Remove loading animation and show response
            
            // Update conversation title based on first user message
            if (this.state.currentConversation && this.state.currentConversation.title === 'New Chat' && this.state.currentConversation.messages.length === 1) {
                const title = query.slice(0, 30);
                this.state.currentConversation.title = title.length < query.length ? `${title}...` : title;
                this.updateConversationTabs();
            }
        } catch (error) {
            this.showError('chat-error', error.message || 'Failed to process query');
        } finally {
            this.state.isQuerying = false;
            this.stopElapsedTimer();
            this.updateChatInterface(); // Update UI to hide loading state
        }
    }

    addMessage(message) {
        this.state.messages.push(message);
        
        // Update current conversation if it exists
        if (this.state.currentConversation) {
            this.state.currentConversation.messages.push(message);
            this.state.currentConversation.lastActivity = new Date().toISOString();
        }
        
        this.displayMessages();
    }

    displayMessages() {
        const messagesContainer = document.getElementById('chat-messages');
        const noIndexMessage = document.getElementById('no-index-message');
        const welcomeMessage = document.getElementById('welcome-message');

        if (this.state.messages.length === 0) {
            noIndexMessage.classList.remove('hidden');
            welcomeMessage.classList.add('hidden');
            return;
        }

        noIndexMessage.classList.add('hidden');
        welcomeMessage.classList.add('hidden');

        // Clear existing messages (except system messages) and loading animation
        const existingMessages = messagesContainer.querySelectorAll('.message, .generating-message');
        existingMessages.forEach(msg => msg.remove());

        // Display messages
        this.state.messages.forEach((message, index) => {
            const messageElement = this.createMessageElement(message, index);
            messagesContainer.appendChild(messageElement);
        });

        // Show generating message if querying
        if (this.state.isQuerying) {
            const generatingElement = this.createGeneratingElement();
            messagesContainer.appendChild(generatingElement);
        }

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    createMessageElement(message, index) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = message.content;
        contentDiv.appendChild(textDiv);

        // Add sources if available
        if (message.sources && message.sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            
            const sourcesTitle = document.createElement('div');
            sourcesTitle.className = 'message-sources-title';
            sourcesTitle.textContent = 'Sources:';
            sourcesDiv.appendChild(sourcesTitle);

            message.sources.forEach(source => {
                const sourceDiv = document.createElement('div');
                sourceDiv.className = 'source-item';
                
                const sourceHeader = document.createElement('div');
                sourceHeader.className = 'source-header';
                
                // Handle different field names from backend (file vs file_path, line_start vs start_line)
                const filePath = source.file || source.file_path || source.path || 'unknown';
                const lineStart = source.line_start || source.start_line || 1;
                const lineEnd = source.line_end || source.end_line || lineStart;
                const score = source.score !== undefined ? ` (${(source.score * 100).toFixed(0)}%)` : '';
                
                // Debug logging
                console.log('Source data:', {
                    file: source.file,
                    line_start: source.line_start,
                    line_end: source.line_end,
                    score: source.score,
                    computed: { filePath, lineStart, lineEnd, score }
                });
                
                sourceHeader.innerHTML = `
                    <i data-lucide="file-text"></i>
                    <span class="source-file">${filePath}</span>
                    <span class="source-lines">(lines ${lineStart}-${lineEnd})${score}</span>
                `;
                sourceDiv.appendChild(sourceHeader);

                const sourceCode = document.createElement('div');
                sourceCode.className = 'source-code';
                const content = source.content || '';
                sourceCode.textContent = content.length > 200 ? content.substring(0, 200) + '...' : content;
                sourceDiv.appendChild(sourceCode);

                sourcesDiv.appendChild(sourceDiv);
            });

            contentDiv.appendChild(sourcesDiv);
        }

        // Add timestamp
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'message-timestamp';
        timestampDiv.textContent = new Date(message.timestamp).toLocaleTimeString();
        contentDiv.appendChild(timestampDiv);

        messageDiv.appendChild(contentDiv);
        return messageDiv;
    }

    createGeneratingElement() {
        const generatingDiv = document.createElement('div');
        generatingDiv.className = 'generating-message';
        generatingDiv.innerHTML = `
            <div class="flex items-center gap-3">
                <span class="loading loading-infinity loading-md text-primary"></span>
                <div class="flex flex-col">
                    <span class="text-sm font-medium">AI is thinking...</span>
                    <span class="text-xs text-gray-500 generating-timer">${Math.floor(this.state.elapsedMs / 1000)}s</span>
                </div>
            </div>
        `;
        return generatingDiv;
    }

    startElapsedTimer() {
        this.state.elapsedMs = 0;
        this.state.elapsedTimer = setInterval(() => {
            this.state.elapsedMs += 1000;
            this.updateGeneratingTimer();
        }, 1000);
    }

    stopElapsedTimer() {
        if (this.state.elapsedTimer) {
            clearInterval(this.state.elapsedTimer);
            this.state.elapsedTimer = null;
        }
    }

    updateGeneratingTimer() {
        const timerElement = document.querySelector('.generating-timer');
        if (timerElement) {
            timerElement.textContent = `${Math.floor(this.state.elapsedMs / 1000)}s`;
        }
    }

    createNewConversation() {
        const newConversation = {
            id: `conv-${Date.now()}`,
            title: 'New Chat',
            messages: [],
            createdAt: new Date().toISOString(),
            lastActivity: new Date().toISOString()
        };
        
        this.state.conversations.push(newConversation);
        this.state.currentConversation = newConversation;
        this.state.messages = [];
        this.state.conversationId = newConversation.id;
        
        this.updateConversationTabs();
        this.displayMessages();
        this.updateChatInterface();
    }

    updateConversationTabs() {
        const tabsContainer = document.getElementById('conversation-tabs');
        const tabsList = document.getElementById('tabs-list');

        if (this.state.conversations.length === 0) {
            tabsContainer.classList.add('hidden');
            return;
        }

        tabsContainer.classList.remove('hidden');
        tabsList.innerHTML = '';

        this.state.conversations.forEach(conversation => {
            const tabElement = document.createElement('div');
            tabElement.className = `conversation-tab ${conversation.id === this.state.currentConversation?.id ? 'active' : ''}`;
            
            const title = this.generateConversationTitle(conversation);
            tabElement.innerHTML = `
                <i data-lucide="message-square"></i>
                <span class="conversation-tab-title">${title}</span>
                ${this.state.conversations.length > 1 ? `
                    <button class="conversation-tab-close" data-conversation-id="${conversation.id}">
                        <i data-lucide="x"></i>
                    </button>
                ` : ''}
            `;

            tabElement.addEventListener('click', () => {
                this.switchToConversation(conversation.id);
            });

            const closeBtn = tabElement.querySelector('.conversation-tab-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.closeConversation(conversation.id);
                });
            }

            tabsList.appendChild(tabElement);
        });

        this.initializeLucideIcons();
    }

    generateConversationTitle(conversation) {
        if (conversation.title !== 'New Chat') {
            return conversation.title;
        }

        const firstUserMessage = conversation.messages.find(msg => msg.role === 'user');
        if (firstUserMessage) {
            const title = firstUserMessage.content.slice(0, 30);
            return title.length < firstUserMessage.content.length ? `${title}...` : title;
        }

        return 'New Chat';
    }

    switchToConversation(conversationId) {
        const conversation = this.state.conversations.find(conv => conv.id === conversationId);
        if (conversation) {
            this.state.currentConversation = conversation;
            this.state.messages = conversation.messages;
            this.state.conversationId = conversation.id;
            this.updateConversationTabs();
            this.displayMessages();
        }
    }

    closeConversation(conversationId) {
        if (this.state.conversations.length <= 1) {
            return;
        }

        // If closing current conversation, switch to another one
        if (this.state.currentConversation?.id === conversationId) {
            const otherConversation = this.state.conversations.find(conv => conv.id !== conversationId);
            if (otherConversation) {
                this.switchToConversation(otherConversation.id);
            }
        }

        // Remove conversation
        this.state.conversations = this.state.conversations.filter(conv => conv.id !== conversationId);
        this.updateConversationTabs();
    }

    clearCurrentChat() {
        if (confirm('Clear current conversation?')) {
            this.state.messages = [];
            this.state.conversationId = null;
            this.displayMessages();
            this.hideError('chat-error');
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ragApp = new RAGApp();
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RAGApp;
}
