/**
 * Sidebar ClawCode Integration - JavaScript Module
 * 
 * Drop-in replacement for sidebar chat functionality.
 * Connects to clawcode_server.py with HMAC signing.
 */

const ClawCodeChat = (function() {
    // Configuration
    const CONFIG = {
        serverUrl: 'http://localhost:11435',
        secret: 'change-this-secret-in-production', // Must match server
        timeout: 120000, // 2 minutes
    };

    // State
    let sessionId = null;
    let isLoading = false;
    let messageHistory = [];

    /**
     * Generate HMAC-SHA256 signature for payload
     */
    async function generateSignature(payload) {
        const encoder = new TextEncoder();
        const keyData = encoder.encode(CONFIG.secret);
        const messageData = encoder.encode(payload);
        
        const key = await crypto.subtle.importKey(
            'raw',
            keyData,
            { name: 'HMAC', hash: 'SHA-256' },
            false,
            ['sign']
        );
        
        const signature = await crypto.subtle.sign('HMAC', key, messageData);
        return Array.from(new Uint8Array(signature))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }

    /**
     * Send message to ClawCode server
     */
    async function sendMessage(message) {
        if (isLoading) {
            return { error: 'Request in progress' };
        }

        isLoading = true;
        const startTime = Date.now();

        try {
            const payload = JSON.stringify({
                message: message,
                session_id: sessionId
            });

            const signature = await generateSignature(payload);

            const response = await fetch(`${CONFIG.serverUrl}/clawcode/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Sidebar-Signature': signature
                },
                body: payload,
                signal: AbortSignal.timeout(CONFIG.timeout)
            });

            const data = await response.json();
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

            if (response.ok) {
                messageHistory.push({
                    role: 'user',
                    content: message,
                    timestamp: new Date().toISOString()
                });
                messageHistory.push({
                    role: 'assistant',
                    content: data.response,
                    timestamp: new Date().toISOString(),
                    elapsed: elapsed
                });

                return {
                    success: true,
                    response: data.response,
                    elapsed: elapsed
                };
            } else {
                return {
                    success: false,
                    error: data.error || data.reason || 'Unknown error',
                    elapsed: elapsed
                };
            }
        } catch (error) {
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
            
            if (error.name === 'TimeoutError') {
                return {
                    success: false,
                    error: 'Request timed out',
                    elapsed: elapsed
                };
            }
            
            return {
                success: false,
                error: error.message,
                elapsed: elapsed
            };
        } finally {
            isLoading = false;
        }
    }

    /**
     * Check server health
     */
    async function checkHealth() {
        try {
            const response = await fetch(`${CONFIG.serverUrl}/clawcode/health`, {
                signal: AbortSignal.timeout(5000)
            });
            return await response.json();
        } catch (error) {
            return {
                healthy: false,
                error: error.message
            };
        }
    }

    /**
     * Get quick actions
     */
    async function getQuickActions() {
        try {
            const response = await fetch(`${CONFIG.serverUrl}/clawcode/quick-actions`, {
                signal: AbortSignal.timeout(5000)
            });
            return await response.json();
        } catch (error) {
            return [];
        }
    }

    /**
     * Create chat UI elements
     */
    function createChatUI(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        container.innerHTML = `
            <div class="clawcode-chat" style="display: flex; flex-direction: column; height: 100%;">
                <div class="chat-header" style="padding: 10px; background: #1a1a2e; border-bottom: 1px solid #333;">
                    <span style="font-weight: bold;">🦀 ClawCode Chat</span>
                    <span id="clawcode-status" style="float: right; font-size: 12px;">⏳ Connecting...</span>
                </div>
                
                <div id="quick-actions" style="padding: 8px; background: #16213e; display: flex; flex-wrap: wrap; gap: 5px;">
                    <!-- Quick action buttons populated here -->
                </div>
                
                <div id="chat-messages" style="flex: 1; overflow-y: auto; padding: 10px; background: #0f0f1a;">
                    <!-- Messages appear here -->
                </div>
                
                <div id="typing-indicator" style="display: none; padding: 8px 10px; color: #888; font-style: italic;">
                    ClawCode thinking...
                </div>
                
                <div class="chat-input" style="padding: 10px; background: #1a1a2e; border-top: 1px solid #333;">
                    <div style="display: flex; gap: 8px;">
                        <input type="text" id="clawcode-input" 
                            placeholder="Ask ClawCode..." 
                            style="flex: 1; padding: 8px 12px; border-radius: 4px; border: 1px solid #333; background: #0f0f1a; color: white;">
                        <button id="clawcode-send" 
                            style="padding: 8px 16px; border-radius: 4px; border: none; background: #4a9eff; color: white; cursor: pointer;">
                            Send
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Bind events
        const input = document.getElementById('clawcode-input');
        const sendBtn = document.getElementById('clawcode-send');

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        });

        sendBtn.addEventListener('click', handleSend);

        // Initialize
        initializeChat();
    }

    /**
     * Initialize chat - check health and load quick actions
     */
    async function initializeChat() {
        const statusEl = document.getElementById('clawcode-status');
        
        // Check health
        const health = await checkHealth();
        if (health.healthy) {
            statusEl.textContent = '🟢 Connected';
            statusEl.style.color = '#4ade80';
        } else {
            statusEl.textContent = '🔴 Offline';
            statusEl.style.color = '#ef4444';
            addMessage('system', `ClawCode server not available: ${health.error || 'Connection failed'}`);
        }

        // Load quick actions
        const actions = await getQuickActions();
        const actionsContainer = document.getElementById('quick-actions');
        
        if (actions.length > 0) {
            actionsContainer.innerHTML = actions.map(action => `
                <button class="quick-action" data-command="${action.command}" 
                    style="padding: 4px 8px; font-size: 12px; border-radius: 4px; border: 1px solid #333; background: #1a1a2e; color: #ccc; cursor: pointer;">
                    ${action.label}
                </button>
            `).join('');

            // Bind quick action clicks
            actionsContainer.querySelectorAll('.quick-action').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.getElementById('clawcode-input').value = btn.dataset.command;
                    handleSend();
                });
            });
        }
    }

    /**
     * Handle send button click
     */
    async function handleSend() {
        const input = document.getElementById('clawcode-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        input.value = '';
        input.disabled = true;

        // Show user message
        addMessage('user', message);

        // Show typing indicator
        const typingEl = document.getElementById('typing-indicator');
        typingEl.style.display = 'block';
        
        let timerInterval;
        let elapsed = 0;
        timerInterval = setInterval(() => {
            elapsed += 0.1;
            typingEl.textContent = `ClawCode thinking... ${elapsed.toFixed(1)}s`;
        }, 100);

        // Send to server
        const result = await sendMessage(message);

        // Hide typing indicator
        clearInterval(timerInterval);
        typingEl.style.display = 'none';

        // Show response
        if (result.success) {
            addMessage('assistant', result.response, result.elapsed);
        } else {
            addMessage('error', `Error: ${result.error}`, result.elapsed);
        }

        input.disabled = false;
        input.focus();
    }

    /**
     * Add message to chat display
     */
    function addMessage(role, content, elapsed = null) {
        const messagesEl = document.getElementById('chat-messages');
        
        const styles = {
            user: 'background: #1e3a5f; margin-left: 20%;',
            assistant: 'background: #1a1a2e;',
            system: 'background: #2d2d3a; color: #888; font-style: italic;',
            error: 'background: #3a1a1a; color: #ff6b6b;'
        };

        const messageHtml = `
            <div class="chat-message" style="padding: 10px; margin: 5px 0; border-radius: 8px; ${styles[role] || ''}">
                <div style="font-size: 11px; color: #666; margin-bottom: 4px;">
                    ${role === 'user' ? '👤 You' : role === 'assistant' ? '🦀 ClawCode' : '⚙️ System'}
                    ${elapsed ? `<span style="float: right;">${elapsed}s</span>` : ''}
                </div>
                <div style="white-space: pre-wrap; font-family: monospace; font-size: 13px;">
                    ${escapeHtml(content)}
                </div>
            </div>
        `;

        messagesEl.insertAdjacentHTML('beforeend', messageHtml);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    /**
     * Escape HTML for safe display
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Configure the client
     */
    function configure(options) {
        Object.assign(CONFIG, options);
    }

    // Public API
    return {
        sendMessage,
        checkHealth,
        getQuickActions,
        createChatUI,
        configure,
        getHistory: () => [...messageHistory],
        clearHistory: () => { messageHistory = []; },
        isLoading: () => isLoading
    };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ClawCodeChat;
}
