// Configurazione
const CONFIG = {
    ORCHESTRATOR_URL: 'http://localhost:5000/invoke',  // Backend proxy per orchestrator AWS
    ACTOR_ID: 'chat-user'
};

// Stato dell'applicazione
let sessionId = generateSessionId();
let isLoading = false;

// Elementi DOM
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const sessionIdDisplay = document.getElementById('sessionId');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const newSessionButton = document.getElementById('newSessionButton');

// Inizializzazione
function init() {
    sessionIdDisplay.textContent = sessionId;
    checkOrchestratorStatus();
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    newSessionButton.addEventListener('click', startNewSession);
    
    // Focus sull'input
    messageInput.focus();
}

// Genera Session ID univoco (min 33 caratteri per AWS)
function generateSessionId() {
    const timestamp = Date.now().toString();
    const random = Math.random().toString(36).substr(2, 15);
    const sessionId = 'session-' + timestamp + '-' + random;
    
    // Assicura che sia almeno 33 caratteri
    return sessionId.padEnd(33, '0');
}

// Controlla lo stato dell'orchestrator
async function checkOrchestratorStatus() {
    try {
        const response = await fetch(CONFIG.ORCHESTRATOR_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                prompt: 'ping',
                actor_id: CONFIG.ACTOR_ID,
                session_id: sessionId
            })
        });
        
        if (response.ok) {
            setStatus(true);
        } else {
            setStatus(false);
        }
    } catch (error) {
        setStatus(false);
        console.error('Errore connessione orchestrator:', error);
    }
}

// Imposta stato connessione
function setStatus(connected) {
    if (connected) {
        statusIndicator.className = 'status-dot connected';
        statusText.textContent = 'Connesso';
    } else {
        statusIndicator.className = 'status-dot disconnected';
        statusText.textContent = 'Disconnesso';
    }
}

// Invia messaggio
async function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message || isLoading) return;
    
    // Aggiungi messaggio utente
    addMessage(message, 'user');
    messageInput.value = '';
    
    // Mostra loading
    const loadingId = showLoading();
    isLoading = true;
    sendButton.disabled = true;
    
    try {
        const response = await fetch(CONFIG.ORCHESTRATOR_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: message,
                actor_id: CONFIG.ACTOR_ID,
                session_id: sessionId
            })
        });
        
        removeLoading(loadingId);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            addErrorMessage(data.error);
        } else {
            const assistantMessage = data.result || data.message || JSON.stringify(data);
            addMessage(assistantMessage, 'assistant');
        }
        
        setStatus(true);
        
    } catch (error) {
        removeLoading(loadingId);
        addErrorMessage(`Errore di connessione: ${error.message}`);
        setStatus(false);
        console.error('Errore:', error);
    } finally {
        isLoading = false;
        sendButton.disabled = false;
        messageInput.focus();
    }
}

// Converti markdown base in HTML
function formatMarkdown(text) {
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')  // **bold**
        .replace(/\*(.+?)\*/g, '<em>$1</em>')  // *italic*
        .replace(/\n/g, '<br>')  // newlines
        .replace(/`(.+?)`/g, '<code>$1</code>')  // `code`
        .replace(/- (.+?)(<br>|$)/g, '• $1$2');  // - bullet points
}

// Aggiungi messaggio alla chat
function addMessage(content, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = formatMarkdown(content);
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll in basso
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Mostra loading
function showLoading() {
    const loadingId = 'loading-' + Date.now();
    const loadingDiv = document.createElement('div');
    loadingDiv.id = loadingId;
    loadingDiv.className = 'message assistant-message';
    loadingDiv.innerHTML = `
        <div class="loading">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    `;
    
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return loadingId;
}

// Rimuovi loading
function removeLoading(loadingId) {
    const loadingDiv = document.getElementById(loadingId);
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// Aggiungi messaggio di errore
function addErrorMessage(errorText) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <strong>⚠️ Errore:</strong><br>
        ${errorText}
    `;
    
    chatMessages.appendChild(errorDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Avvia nuova sessione
function startNewSession() {
    if (confirm('Vuoi iniziare una nuova sessione? La conversazione corrente verrà persa.')) {
        sessionId = generateSessionId();
        sessionIdDisplay.textContent = sessionId;
        
        // Pulisci chat
        chatMessages.innerHTML = `
            <div class="system-message">
                Nuova sessione iniziata! Session ID: <strong>${sessionId}</strong>
                <br><br>
                Come posso aiutarti?
            </div>
        `;
        
        messageInput.focus();
    }
}

// Avvia l'app
init();
