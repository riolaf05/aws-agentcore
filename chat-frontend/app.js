// Configurazione
const CONFIG = {
    ORCHESTRATOR_URL: 'http://localhost:5000/invoke',
    API_URL: 'http://localhost:5000/api',
    ACTOR_ID: 'chat-user',
    // Cognito Configuration
    COGNITO_USER_POOL_ID: 'us-east-1_Lza70tSUs',
    COGNITO_CLIENT_ID: '1pm6fmgvar40go8cpimf6bo9lm',
    COGNITO_REGION: 'us-east-1'
};

// Cognito User Pool Setup
let userPool;
let cognitoUser;

if (typeof AmazonCognitoIdentity !== 'undefined') {
    const poolData = {
        UserPoolId: CONFIG.COGNITO_USER_POOL_ID,
        ClientId: CONFIG.COGNITO_CLIENT_ID
    };
    userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
}

// Stato dell'applicazione
let sessionId = generateSessionId();
let isLoading = false;
let currentView = 'chat';
let currentUser = null;
let idToken = null;

// Elementi DOM - Login
const loginScreen = document.getElementById('loginScreen');
const mainApp = document.getElementById('mainApp');
const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');
const logoutBtn = document.getElementById('logoutBtn');

// Elementi DOM - Chat
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const sessionIdDisplay = document.getElementById('sessionId');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const newSessionButton = document.getElementById('newSessionButton');

// Elementi DOM - Navigation
const navItems = document.querySelectorAll('.nav-item');
const views = document.querySelectorAll('.view');

// Elementi DOM - Goals
const newGoalBtn = document.getElementById('newGoalBtn');
const goalForm = document.getElementById('goalForm');
const createGoalForm = document.getElementById('createGoalForm');
const cancelGoalBtn = document.getElementById('cancelGoalBtn');
const goalsList = document.getElementById('goalsList');
const refreshGoalsBtn = document.getElementById('refreshGoalsBtn');
const goalFilterAmbito = document.getElementById('goalFilterAmbito');
const goalFilterStatus = document.getElementById('goalFilterStatus');
const goalFilterPriorita = document.getElementById('goalFilterPriorita');

// Elementi DOM - Projects
const newProjectBtn = document.getElementById('newProjectBtn');
const projectForm = document.getElementById('projectForm');
const createProjectForm = document.getElementById('createProjectForm');
const cancelProjectBtn = document.getElementById('cancelProjectBtn');
const projectsList = document.getElementById('projectsList');
const refreshProjectsBtn = document.getElementById('refreshProjectsBtn');
const projectFilterAmbito = document.getElementById('projectFilterAmbito');
const projectFilterTag = document.getElementById('projectFilterTag');

// Elementi DOM - Contacts
const newContactBtn = document.getElementById('newContactBtn');
const contactForm = document.getElementById('contactForm');
const createContactForm = document.getElementById('createContactForm');
const cancelContactBtn = document.getElementById('cancelContactBtn');
const contactsList = document.getElementById('contactsList');
const refreshContactsBtn = document.getElementById('refreshContactsBtn');
const contactFilterTipo = document.getElementById('contactFilterTipo');

// Elementi DOM - Events & Places
const newEventBtn = document.getElementById('newEventBtn');
const newPlaceBtn = document.getElementById('newPlaceBtn');
const eventForm = document.getElementById('eventForm');
const placeForm = document.getElementById('placeForm');
const createEventForm = document.getElementById('createEventForm');
const createPlaceForm = document.getElementById('createPlaceForm');
const cancelEventBtn = document.getElementById('cancelEventBtn');
const cancelPlaceBtn = document.getElementById('cancelPlaceBtn');
const eventsPlacesList = document.getElementById('eventsPlacesList');
const refreshEventsPlacesBtn = document.getElementById('refreshEventsPlacesBtn');
const eventPlaceType = document.getElementById('eventPlaceType');
const eventPlaceFilterLocation = document.getElementById('eventPlaceFilterLocation');
const eventPlaceFilterCategory = document.getElementById('eventPlaceFilterCategory');

// Elementi DOM - Knowledge-base
const addKBBtn = document.getElementById('addKBBtn');
const kbModal = document.getElementById('kbModal');
const kbUploadForm = document.getElementById('kbUploadForm');
const kbFile = document.getElementById('kbFile');
const kbText = document.getElementById('kbText');
const kbType = document.getElementById('kbType');
const kbList = document.getElementById('kbList');
const toggleKBEndpointBtn = document.getElementById('toggleKBEndpointBtn');
const kbEndpointLabel = document.getElementById('kbEndpointLabel');

// Debug
if (!kbList) console.error('Elemento kbList non trovato!');
if (!kbModal) console.error('Elemento kbModal non trovato!');
if (!addKBBtn) console.error('Elemento addKBBtn non trovato!');

// Configuration for Knowledge-base
let isKBUploading = false; // Prevent double-submit
let currentKBEndpoint = 'prod'; // Default: prod

// ========================================
// KNOWLEDGE-BASE FUNCTIONS
// ========================================

function updateKBEndpointUI() {
    if (kbEndpointLabel) {
        kbEndpointLabel.innerHTML = `Endpoint: <strong>${currentKBEndpoint}</strong>`;
    }
    console.log(`📡 KB Endpoint switched to: ${currentKBEndpoint}`);
}

function toggleKBEndpoint() {
    currentKBEndpoint = currentKBEndpoint === 'prod' ? 'test' : 'prod';
    updateKBEndpointUI();
}

function closeKBModal() {
    kbModal.style.display = 'none';
    kbUploadForm.reset();
}

async function handleKBUpload(e) {
    e.preventDefault();
    
    // Prevent double-submit
    if (isKBUploading) return;
    isKBUploading = true;
    
    const file = kbFile.files[0];
    const text = kbText.value.trim();
    
    // Controlla che almeno uno tra file e testo sia presente
    if (!file && !text) {
        alert('Inserisci almeno un file PDF o una descrizione');
        isKBUploading = false;
        return;
    }
    
    // Verifica che il file sia un PDF se presente
    if (file && file.type !== 'application/pdf') {
        alert('Il file deve essere in formato PDF');
        isKBUploading = false;
        return;
    }
    
    try {
        const formData = new FormData();
        
        // Aggiungi "data" come file se presente, altrimenti come testo
        if (file) {
            formData.append('data', file);
        } else {
            formData.append('data', text);
        }
        
        formData.append('type', kbType.value);
        formData.append('endpoint', currentKBEndpoint);  // Passa l'endpoint (test o prod)
        
        // Show loading state
        const submitBtn = kbUploadForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ Caricamento...';
        
        // Chiamata all'API backend Flask
        const response = await fetch(`${CONFIG.API_URL}/kb`, {
            method: 'POST',
            body: formData
            // No Content-Type header - FormData sets it automatically
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `Errore nell'upload: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Upload successful:', result);
        
        // Show success message
        alert('✅ Documento caricato con successo!');
        
        // Close modal and reset form
        closeKBModal();
        
        // Reload KB list
        loadKBDocuments();
        
    } catch (error) {
        console.error('KB Upload error:', error);
        alert('❌ Errore nell\'upload: ' + error.message);
    } finally {
        isKBUploading = false;
        const submitBtn = kbUploadForm.querySelector('button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.textContent = '📤 Upload';
    }
}

async function loadKBDocuments() {
    try {
        console.log('Loading KB Documents...');
        if (!kbList) {
            console.error('kbList element not found in loadKBDocuments');
            return;
        }
        
        kbList.innerHTML = '<p class="loading">⏳ Caricamento documenti...</p>';
        
        // Chiamata all'API backend Flask
        const response = await fetch(`${CONFIG.API_URL}/kb`);
        
        if (!response.ok) {
            throw new Error(`Errore nel caricamento: ${response.status}`);
        }
        
        const result = await response.json();
        const documents = result.documents || [];
        
        console.log(`KB Documents loaded: ${documents.length} documenti`);
        
        // Mostra i documenti
        if (documents.length === 0) {
            kbList.innerHTML = `
                <div class="kb-info">
                    <p>📚 Nessun documento caricato</p>
                    <p>Utilizza il pulsante "Aggiungi" per caricare nuovi documenti PDF o testi.</p>
                    <p><strong>Tipo supportato:</strong> meeting-notes</p>
                </div>
            `;
        } else {
            kbList.innerHTML = `
                <table class="kb-table">
                    <thead>
                        <tr>
                            <th>📄 Tipo</th>
                            <th>📝 Nome/Contenuto</th>
                            <th>📅 Data</th>
                            <th>🗑️ Azioni</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${documents.map(doc => `
                            <tr>
                                <td><span class="badge badge-type">${doc.tipo || 'N/A'}</span></td>
                                <td>
                                    ${doc.is_pdf ? 
                                        `<span class="kb-filename">📄 ${doc.file_name}</span>` : 
                                        `<span class="kb-text-preview">${(doc.text_content || '').substring(0, 100)}...</span>`
                                    }
                                </td>
                                <td>${formatDateTime(doc.created_at)}</td>
                                <td>
                                    <button class="btn-delete-small" onclick="deleteKBDocument('${doc.document_id}', '${doc.created_at}')">🗑️</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }
        
        console.log('KB Documents loaded successfully');
    } catch (error) {
        console.error('Error loading KB documents:', error);
        if (kbList) {
            kbList.innerHTML = '<p class="error">Errore nel caricamento dei documenti</p>';
        }
    }
}

async function deleteKBDocument(documentId, createdAt) {
    if (!confirm('Sei sicuro di voler eliminare questo documento?')) {
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/kb/${documentId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore nell\'eliminazione');
        }
        
        alert('✅ Documento eliminato con successo!');
        loadKBDocuments();
    } catch (error) {
        console.error('Error deleting KB document:', error);
        alert('❌ Errore nell\'eliminazione: ' + error.message);
    }
}

// ========================================
// INITIALIZATION
// ========================================

function init() {
    // Check if user is already logged in
    checkLoginStatus();
    
    // Login event listeners
    loginForm.addEventListener('submit', handleLogin);
    logoutBtn.addEventListener('click', handleLogout);
    
    // Chat setup
    sessionIdDisplay.textContent = sessionId;
    checkOrchestratorStatus();
    
    // Navigation
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const viewName = item.dataset.view;
            switchView(viewName);
        });
    });
    
    // Chat event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    newSessionButton.addEventListener('click', startNewSession);
    
    // Goals event listeners
    newGoalBtn.addEventListener('click', () => goalForm.style.display = 'block');
    cancelGoalBtn.addEventListener('click', () => {
        goalForm.style.display = 'none';
        createGoalForm.reset();
    });
    createGoalForm.addEventListener('submit', handleCreateGoal);
    refreshGoalsBtn.addEventListener('click', loadGoals);
    goalFilterAmbito.addEventListener('input', loadGoals);
    goalFilterStatus.addEventListener('change', loadGoals);
    goalFilterPriorita.addEventListener('change', loadGoals);
    
    // Projects event listeners
    newProjectBtn.addEventListener('click', () => projectForm.style.display = 'block');
    cancelProjectBtn.addEventListener('click', () => {
        projectForm.style.display = 'none';
        createProjectForm.reset();
    });
    createProjectForm.addEventListener('submit', handleCreateProject);
    refreshProjectsBtn.addEventListener('click', loadProjects);
    projectFilterAmbito.addEventListener('input', loadProjects);
    projectFilterTag.addEventListener('input', loadProjects);
    
    // Contacts event listeners
    newContactBtn.addEventListener('click', () => contactForm.style.display = 'block');
    cancelContactBtn.addEventListener('click', () => {
        contactForm.style.display = 'none';
        createContactForm.reset();
    });
    createContactForm.addEventListener('submit', handleCreateContact);
    refreshContactsBtn.addEventListener('click', loadContacts);
    contactFilterTipo.addEventListener('input', loadContacts);
    
    // Contact sort listener
    const contactSortOrder = document.getElementById('contactSortOrder');
    if (contactSortOrder) {
        contactSortOrder.addEventListener('change', (e) => {
            currentContactSort = e.target.value;
            loadContacts();
        });
    }
    
    // Events & Places event listeners
    newEventBtn.addEventListener('click', () => {
        eventForm.style.display = 'block';
        placeForm.style.display = 'none';
    });
    newPlaceBtn.addEventListener('click', () => {
        placeForm.style.display = 'block';
        eventForm.style.display = 'none';
    });
    cancelEventBtn.addEventListener('click', () => {
        eventForm.style.display = 'none';
        createEventForm.reset();
    });
    cancelPlaceBtn.addEventListener('click', () => {
        placeForm.style.display = 'none';
        createPlaceForm.reset();
    });
    createEventForm.addEventListener('submit', handleCreateEvent);
    createPlaceForm.addEventListener('submit', handleCreatePlace);
    refreshEventsPlacesBtn.addEventListener('click', loadEventsAndPlaces);
    eventPlaceType.addEventListener('change', loadEventsAndPlaces);
    eventPlaceFilterLocation.addEventListener('input', loadEventsAndPlaces);
    eventPlaceFilterCategory.addEventListener('change', loadEventsAndPlaces);
    
    // Knowledge-base event listeners
    addKBBtn.addEventListener('click', () => kbModal.style.display = 'block');
    kbUploadForm.addEventListener('submit', handleKBUpload);
    if (toggleKBEndpointBtn) {
        toggleKBEndpointBtn.addEventListener('click', toggleKBEndpoint);
        updateKBEndpointUI(); // Inizializza la UI con il valore di default
    }
    
    // Focus sull'input
    messageInput.focus();
}

// Switch between views
function switchView(viewName) {
    // Update navigation
    navItems.forEach(item => {
        if (item.dataset.view === viewName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    // Update views
    views.forEach(view => {
        if (view.id === viewName + 'View') {
            view.classList.add('active');
        } else {
            view.classList.remove('active');
        }
    });
    
    currentView = viewName;
    
    // Load data when switching to goals/projects/contacts
    if (viewName === 'goals') {
        loadGoals();
    } else if (viewName === 'projects') {
        loadProjects();
    } else if (viewName === 'contacts') {
        loadContacts();
    } else if (viewName === 'events') {
        loadEventsAndPlaces();
    } else if (viewName === 'knowledge-base') {
        loadKBDocuments();
    }
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
    let html = text;
    
    // Headers (## e #)
    html = html.replace(/^### (.+?)$/gm, '<h3 style="margin: 12px 0 6px 0; font-weight: bold; font-size: 1.1em;">$1</h3>');
    html = html.replace(/^## (.+?)$/gm, '<h2 style="margin: 15px 0 8px 0; font-weight: bold; font-size: 1.2em;">$1</h2>');
    html = html.replace(/^# (.+?)$/gm, '<h1 style="margin: 18px 0 10px 0; font-weight: bold; font-size: 1.4em;">$1</h1>');
    
    // Bold **text**
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Italic *text*
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Code blocks ```code```
    html = html.replace(/```([\s\S]*?)```/g, '<pre style="background: #f4f4f4; padding: 10px; border-radius: 4px; overflow-x: auto; margin: 8px 0;"><code>$1</code></pre>');
    
    // Inline code `code`
    html = html.replace(/`(.+?)`/g, '<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: monospace;">$1</code>');
    
    // Lista puntata: - item (capture the entire list block)
    html = html.replace(/(?:^|\n)((?:(?:^|\n)- .+?(?=\n(?!-)|\n*$))+)/gm, function(match) {
        let items = match.trim().split('\n').filter(line => line.startsWith('- '));
        if (items.length > 0) {
            let listHtml = '<ul style="margin: 8px 0; padding-left: 30px;">\n';
            items.forEach(item => {
                let itemText = item.replace(/^- /, '').trim();
                listHtml += `  <li style="margin: 4px 0; line-height: 1.5;">${itemText}</li>\n`;
            });
            listHtml += '</ul>';
            return '\n' + listHtml;
        }
        return match;
    });
    
    // Paragrafi: separa doppio newline
    html = html.replace(/\n\n+/g, '</p><p style="margin: 10px 0; line-height: 1.6;">');
    html = '<p style="margin: 10px 0; line-height: 1.6;">' + html + '</p>';
    
    // Newlines singole -> <br>
    html = html.replace(/\n/g, '<br>');
    
    // Chiudi tutti i <p> tag aperti
    html = html.replace(/<br><\/p>/g, '</p>');
    
    // Link markdown [text](url)
    html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" style="color: #0066cc; text-decoration: underline;">$1</a>');
    
    return html;
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

// ========================================
// GOALS MANAGEMENT
// ========================================

async function loadGoals() {
    goalsList.innerHTML = '<p class="loading">Caricamento obiettivi...</p>';
    
    const params = new URLSearchParams();
    const ambito = goalFilterAmbito.value.trim();
    const status = goalFilterStatus.value;
    const priorita = goalFilterPriorita.value;
    
    if (ambito) params.append('ambito', ambito);
    if (status) params.append('status', status);
    if (priorita) params.append('priorita', priorita);
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/goals?${params.toString()}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayGoals(data.goals || []);
        
    } catch (error) {
        console.error('Error loading goals:', error);
        goalsList.innerHTML = `<p class="error-message">Errore caricamento obiettivi: ${error.message}</p>`;
    }
}

function displayGoals(goals) {
    if (goals.length === 0) {
        goalsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🎯</div>
                <p class="empty-state-text">Nessun obiettivo trovato</p>
            </div>
        `;
        return;
    }
    
    goalsList.innerHTML = goals.map(goal => `
        <div class="item-card">
            <div class="item-header">
                <div>
                    <h3 class="item-title">${escapeHtml(goal.titolo)}</h3>
                    <div class="item-meta">
                        <span class="badge badge-ambito">${escapeHtml(goal.ambito)}</span>
                        <span class="badge badge-priority-${goal.priorita}">${getPriorityLabel(goal.priorita)}</span>
                        <span class="badge badge-status-${goal.status}">${getStatusLabel(goal.status)}</span>
                    </div>
                </div>
            </div>
            ${goal.descrizione ? `<div class="item-description">${formatDescription(goal.descrizione)}</div>` : ''}
            <div class="item-details">
                <div class="item-detail">
                    <span class="item-detail-label">Scadenza</span>
                    <span class="item-detail-value"><strong>${formatDate(goal.scadenza)}</strong></span>
                </div>
                ${goal.metriche ? `
                <div class="item-detail">
                    <span class="item-detail-label">Metriche</span>
                    <span class="item-detail-value">${formatMetrics(goal.metriche)}</span>
                </div>
                ` : ''}
                <div class="item-detail">
                    <span class="item-detail-label">Creato</span>
                    <span class="item-detail-value">${formatDateTime(goal.created_at)}</span>
                </div>
            </div>
            ${goal.sottotask && goal.sottotask.length > 0 ? `
            <div class="subtasks-section">
                <div class="subtasks-header" onclick="toggleSubtasks('goal-${goal.goal_id}')">
                    <span class="subtasks-toggle" id="toggle-goal-${goal.goal_id}">▶</span>
                    <span class="item-detail-label">Sottotask (${goal.sottotask.filter(t => t.completato).length}/${goal.sottotask.length})</span>
                </div>
                <div class="subtasks-list collapsed" id="subtasks-goal-${goal.goal_id}">
                    ${goal.sottotask.map(task => `
                        <div class="subtask-item">
                            <span class="subtask-icon">${task.completato ? '✅' : '⬜'}</span>
                            <span class="subtask-text">${escapeHtml(task.titolo)}</span>
                            ${task.scadenza ? `<span class="subtask-date">${formatDate(task.scadenza)}</span>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            ${goal.note_history && goal.note_history.length > 0 ? `
            <div class="notes-section">
                <div class="notes-header" onclick="toggleNotes('goal-${goal.goal_id}')">
                    <span class="notes-toggle" id="toggle-notes-goal-${goal.goal_id}">▶</span>
                    <span class="item-detail-label">📝 Note (${goal.note_history.length})</span>
                </div>
                <div class="notes-list collapsed" id="notes-goal-${goal.goal_id}">
                    ${goal.note_history.slice().reverse().map(note => `
                        <div class="note-card-item">
                            <div class="note-card-header">
                                <span class="note-card-date">${formatDateTime(note.timestamp)}</span>
                                <span class="note-source-badge ${note.source || 'frontend'}">${note.source === 'agent' ? '🤖 Agent' : '👤 Frontend'}</span>
                            </div>
                            <div class="note-card-content">${escapeHtml(note.note)}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            <div class="item-actions">
                <button class="btn-edit" onclick="editGoal('${goal.goal_id}')">✏️ Modifica</button>
                <button class="btn-delete" onclick="deleteGoal('${goal.goal_id}', '${escapeHtml(goal.titolo).replace(/'/g, "\\'")}')">🗑️ Elimina</button>
            </div>
        </div>
    `).join('');
}

async function handleCreateGoal(e) {
    e.preventDefault();
    
    const goalData = {
        ambito: document.getElementById('goalAmbito').value.trim(),
        titolo: document.getElementById('goalTitolo').value.trim(),
        descrizione: document.getElementById('goalDescrizione').value.trim(),
        scadenza: document.getElementById('goalScadenza').value,
        priorita: document.getElementById('goalPriorita').value,
    };
    
    // Parse metriche JSON
    const metricheText = document.getElementById('goalMetriche').value.trim();
    if (metricheText) {
        try {
            goalData.metriche = JSON.parse(metricheText);
        } catch (error) {
            alert('Formato JSON metriche non valido');
            return;
        }
    }
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/goals`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(goalData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore creazione obiettivo');
        }
        
        // Reset form and hide
        createGoalForm.reset();
        goalForm.style.display = 'none';
        
        // Reload goals
        loadGoals();
        
    } catch (error) {
        console.error('Error creating goal:', error);
        alert(`Errore: ${error.message}`);
    }
}

// ========================================
// PROJECTS MANAGEMENT
// ========================================

async function loadProjects() {
    projectsList.innerHTML = '<p class="loading">Caricamento progetti...</p>';
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/projects`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const allProjects = data.projects || [];
        
        // Filtra lato client per una ricerca più efficace
        const filteredProjects = filterProjects(allProjects);
        displayProjects(filteredProjects);
        
    } catch (error) {
        console.error('Error loading projects:', error);
        projectsList.innerHTML = `<p class="error-message">Errore caricamento progetti: ${error.message}</p>`;
    }
}

function filterProjects(projects) {
    const ambito = projectFilterAmbito.value.trim().toLowerCase();
    const tag = projectFilterTag.value.trim().toLowerCase();
    
    return projects.filter(project => {
        // Filtra per ambito
        if (ambito && !project.ambito.toLowerCase().includes(ambito)) {
            return false;
        }
        
        // Filtra per tag (cerca all'interno dell'array di tag)
        if (tag && project.tag && project.tag.length > 0) {
            const hasTag = project.tag.some(t => t.toLowerCase().includes(tag));
            if (!hasTag) {
                return false;
            }
        } else if (tag && (!project.tag || project.tag.length === 0)) {
            return false;
        }
        
        return true;
    });
}

function displayProjects(projects) {
    // Aggiorna counter
    const counter = document.getElementById('projectsCounter');
    if (counter) {
        counter.textContent = projects.length;
    }
    
    if (projects.length === 0) {
        projectsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">💼</div>
                <p class="empty-state-text">Nessun progetto trovato</p>
            </div>
        `;
        return;
    }
    
    projectsList.innerHTML = projects.map(project => `
        <div class="item-card">
            <div class="item-header">
                <div>
                    <h3 class="item-title">${escapeHtml(project.titolo)}</h3>
                    <div class="item-meta">
                        <span class="badge badge-ambito">${escapeHtml(project.ambito)}</span>
                    </div>
                </div>
            </div>
            ${project.descrizione ? `<div class="item-description">${formatDescription(project.descrizione)}</div>` : ''}
            <div class="item-details">
                ${project.github_url ? `
                <div class="item-detail">
                    <span class="item-detail-label">GitHub</span>
                    <a href="${escapeHtml(project.github_url)}" target="_blank" class="item-link"><strong>${escapeHtml(project.github_url)}</strong></a>
                </div>
                ` : ''}
                <div class="item-detail">
                    <span class="item-detail-label">Creato</span>
                    <span class="item-detail-value">${formatDateTime(project.data_creazione)}</span>
                </div>
            </div>
            ${project.tag && project.tag.length > 0 ? `
            <div class="item-details" style="margin-top: 12px;">
                <div class="item-detail" style="grid-column: 1/-1;">
                    <span class="item-detail-label">Tecnologie</span>
                    <div class="tags-list">
                        ${project.tag.map(t => `<span class="badge badge-tag">${escapeHtml(t)}</span>`).join('')}
                    </div>
                </div>
            </div>
            ` : ''}
            <div class="item-actions">
                <button class="btn-edit" onclick="editProject('${project.project_id}')">✏️ Modifica</button>
                <button class="btn-delete" onclick="deleteProject('${project.project_id}', '${escapeHtml(project.titolo).replace(/'/g, "\\'")}')">🗑️ Elimina</button>
            </div>
        </div>
    `).join('');
}

async function handleCreateProject(e) {
    e.preventDefault();
    
    const tagInput = document.getElementById('projectTag').value.trim();
    const tags = tagInput ? tagInput.split(',').map(t => t.trim()).filter(t => t) : [];
    
    const projectData = {
        ambito: document.getElementById('projectAmbito').value.trim(),
        titolo: document.getElementById('projectTitolo').value.trim(),
        github_url: document.getElementById('projectGithubUrl').value.trim(),
        descrizione: document.getElementById('projectDescrizione').value.trim(),
        tag: tags
    };
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/projects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(projectData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore creazione progetto');
        }
        
        // Reset form and hide
        createProjectForm.reset();
        projectForm.style.display = 'none';
        
        // Reload projects
        loadProjects();
        
    } catch (error) {
        console.error('Error creating project:', error);
        alert(`Errore: ${error.message}`);
    }
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', { year: 'numeric', month: 'long', day: 'numeric' });
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('it-IT', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatMetrics(metriche) {
    if (typeof metriche === 'object') {
        return Object.entries(metriche)
            .map(([key, value]) => `${key}: ${value}`)
            .join(', ');
    }
    return String(metriche);
}

function getPriorityLabel(priority) {
    const labels = {
        'urgent': 'Urgente',
        'high': 'Alta',
        'medium': 'Media',
        'low': 'Bassa'
    };
    return labels[priority] || priority;
}

function getStatusLabel(status) {
    const labels = {
        'active': 'Attivo',
        'completed': 'Completato',
        'cancelled': 'Cancellato'
    };
    return labels[status] || status;
}

function formatDescription(text) {
    if (!text) return '';
    
    // Escape HTML first
    let formatted = escapeHtml(text);
    
    // Convert **text** to <strong>text</strong>
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert newlines to <br>
    formatted = formatted.replace(/\n/g, '<br>');
    
    return formatted;
}

function toggleSubtasks(goalId) {
    const toggleIcon = document.getElementById(`toggle-${goalId}`);
    const subtasksList = document.getElementById(`subtasks-${goalId}`);
    
    if (subtasksList.classList.contains('collapsed')) {
        subtasksList.classList.remove('collapsed');
        toggleIcon.textContent = '▼';
    } else {
        subtasksList.classList.add('collapsed');
        toggleIcon.textContent = '▶';
    }
}

function toggleNotes(goalId) {
    const toggleIcon = document.getElementById(`toggle-notes-${goalId}`);
    const notesList = document.getElementById(`notes-${goalId}`);
    
    if (notesList.classList.contains('collapsed')) {
        notesList.classList.remove('collapsed');
        toggleIcon.textContent = '▼';
    } else {
        notesList.classList.add('collapsed');
        toggleIcon.textContent = '▶';
    }
}

// ========================================
// DELETE FUNCTIONS
// ========================================

async function deleteGoal(goalId, goalTitle) {
    if (!confirm(`Sei sicuro di voler eliminare l'obiettivo "${goalTitle}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/goals?goal_id=${goalId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Goal deleted:', result);
        
        // Ricarica la lista
        await loadGoals();
        
        alert('Obiettivo eliminato con successo!');
        
    } catch (error) {
        console.error('Error deleting goal:', error);
        alert(`Errore durante l'eliminazione: ${error.message}`);
    }
}

async function deleteProject(projectId, projectTitle) {
    if (!confirm(`Sei sicuro di voler eliminare il progetto "${projectTitle}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/projects?project_id=${projectId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Project deleted:', result);
        
        // Ricarica la lista
        await loadProjects();
        
        alert('Progetto eliminato con successo!');
        
    } catch (error) {
        console.error('Error deleting project:', error);
        alert(`Errore durante l'eliminazione: ${error.message}`);
    }
}

// ========================================
// EDIT FUNCTIONS
// ========================================

let currentEditGoal = null;
let currentEditProject = null;

async function editGoal(goalId) {
    try {
        // Get goal data
        const response = await fetch(`${CONFIG.API_URL}/goals?goal_id=${goalId}`);
        if (!response.ok) throw new Error('Failed to fetch goal');
        
        const data = await response.json();
        const goal = data.goals[0];
        
        if (!goal) {
            alert('Obiettivo non trovato');
            return;
        }
        
        currentEditGoal = goal;
        
        // Populate edit modal
        document.getElementById('editGoalId').value = goal.goal_id;
        document.getElementById('editGoalAmbito').value = goal.ambito || '';
        document.getElementById('editGoalTitolo').value = goal.titolo || '';
        document.getElementById('editGoalDescrizione').value = goal.descrizione || '';
        document.getElementById('editGoalScadenza').value = goal.scadenza || '';
        document.getElementById('editGoalPriorita').value = goal.priorita || 'medium';
        document.getElementById('editGoalStatus').value = goal.status || 'active';
        document.getElementById('editGoalMetriche').value = goal.metriche ? JSON.stringify(goal.metriche, null, 2) : '';
        document.getElementById('editGoalNote').value = ''; // Clear note field
        
        // Display note history if exists
        const notesHistorySection = document.getElementById('notesHistorySection');
        const notesHistoryList = document.getElementById('notesHistoryList');
        
        if (goal.note_history && goal.note_history.length > 0) {
            notesHistorySection.style.display = 'block';
            notesHistoryList.innerHTML = goal.note_history.map(note => `
                <div class="note-item">
                    <span class="note-timestamp">${formatDateTime(note.timestamp)}</span>
                    <span class="note-source ${note.source || 'frontend'}">${note.source === 'agent' ? '🤖 Agent' : '👤 Frontend'}</span>
                    <div class="note-content">${escapeHtml(note.note)}</div>
                </div>
            `).join('');
        } else {
            notesHistorySection.style.display = 'none';
        }
        
        // Show modal
        document.getElementById('editGoalModal').style.display = 'flex';
        
    } catch (error) {
        console.error('Error loading goal:', error);
        alert(`Errore: ${error.message}`);
    }
}

async function editProject(projectId) {
    try {
        // Get project data
        const response = await fetch(`${CONFIG.API_URL}/projects?project_id=${projectId}`);
        if (!response.ok) throw new Error('Failed to fetch project');
        
        const data = await response.json();
        const project = data.projects[0];
        
        if (!project) {
            alert('Progetto non trovato');
            return;
        }
        
        currentEditProject = project;
        
        // Populate edit modal
        document.getElementById('editProjectId').value = project.project_id;
        document.getElementById('editProjectAmbito').value = project.ambito || '';
        document.getElementById('editProjectTitolo').value = project.titolo || '';
        document.getElementById('editProjectDescrizione').value = project.descrizione || '';
        document.getElementById('editProjectGithubUrl').value = project.github_url || '';
        document.getElementById('editProjectTag').value = project.tag ? project.tag.join(', ') : '';
        document.getElementById('editProjectStatus').value = project.status || 'active';
        
        // Show modal
        document.getElementById('editProjectModal').style.display = 'flex';
        
    } catch (error) {
        console.error('Error loading project:', error);
        alert(`Errore: ${error.message}`);
    }
}

async function handleUpdateGoal(e) {
    e.preventDefault();
    
    const goalData = {
        goal_id: document.getElementById('editGoalId').value,
        ambito: document.getElementById('editGoalAmbito').value.trim(),
        title: document.getElementById('editGoalTitolo').value.trim(),
        description: document.getElementById('editGoalDescrizione').value.trim(),
        deadline: document.getElementById('editGoalScadenza').value,
        priority: document.getElementById('editGoalPriorita').value,
        status: document.getElementById('editGoalStatus').value
    };
    
    // Parse metriche JSON
    const metricheText = document.getElementById('editGoalMetriche').value.trim();
    if (metricheText) {
        try {
            goalData.metriche = JSON.parse(metricheText);
        } catch (error) {
            alert('Formato JSON metriche non valido');
            return;
        }
    }
    
    // Add note if present
    const noteText = document.getElementById('editGoalNote').value.trim();
    if (noteText) {
        goalData.note = noteText;
        goalData.note_source = 'frontend';
    }
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/goals`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(goalData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore aggiornamento obiettivo');
        }
        
        // Close modal
        document.getElementById('editGoalModal').style.display = 'none';
        currentEditGoal = null;
        
        // Reload goals
        await loadGoals();
        alert('Obiettivo aggiornato con successo!');
        
    } catch (error) {
        console.error('Error updating goal:', error);
        alert(`Errore: ${error.message}`);
    }
}

async function handleUpdateProject(e) {
    e.preventDefault();
    
    const tagInput = document.getElementById('editProjectTag').value.trim();
    const tags = tagInput ? tagInput.split(',').map(t => t.trim()).filter(t => t) : [];
    
    const projectData = {
        project_id: document.getElementById('editProjectId').value,
        ambito: document.getElementById('editProjectAmbito').value.trim(),
        title: document.getElementById('editProjectTitolo').value.trim(),
        description: document.getElementById('editProjectDescrizione').value.trim(),
        github_url: document.getElementById('editProjectGithubUrl').value.trim(),
        tech_stack: tags,
        status: document.getElementById('editProjectStatus').value
    };
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/projects`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(projectData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore aggiornamento progetto');
        }
        
        // Close modal
        document.getElementById('editProjectModal').style.display = 'none';
        currentEditProject = null;
        
        // Reload projects
        await loadProjects();
        alert('Progetto aggiornato con successo!');
        
    } catch (error) {
        console.error('Error updating project:', error);
        alert(`Errore: ${error.message}`);
    }
}

// ========================================
// CONTACTS MANAGEMENT
// ========================================

async function loadContacts() {
    const contactsList = document.getElementById('contactsList');
    if (!contactsList) return;
    
    contactsList.innerHTML = '<p class="loading">Caricamento contatti...</p>';
    
    try {
        // Recupera filtri
        const tipoFilter = document.getElementById('contactFilterTipo')?.value || '';
        
        const params = new URLSearchParams();
        if (tipoFilter) params.append('tipo', tipoFilter);
        
        const url = `${CONFIG.API_URL}/contacts${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayContacts(data.contacts || []);
        
    } catch (error) {
        console.error('Error loading contacts:', error);
        contactsList.innerHTML = `<p class="error-message">Errore caricamento contatti: ${error.message}</p>`;
    }
}

let currentContactSort = 'name-asc';

function displayContacts(contacts) {
    const contactsList = document.getElementById('contactsList');
    
    // Aggiorna counter
    const counter = document.getElementById('contactsCounter');
    if (counter) {
        counter.textContent = contacts.length;
    }
    
    if (contacts.length === 0) {
        contactsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">👤</div>
                <p class="empty-state-text">Nessun contatto trovato</p>
            </div>
        `;
        return;
    }
    
    // Applica ordinamento
    const sortedContacts = sortContacts([...contacts], currentContactSort);
    
    // Crea tabella
    contactsList.innerHTML = `
        <table class="contacts-table">
            <thead>
                <tr>
                    <th style="width: 40px;"></th>
                    <th style="width: 30%;">Nome</th>
                    <th style="width: 20%;">Tipo</th>
                    <th style="width: 50%;">Note</th>
                </tr>
            </thead>
            <tbody>
                ${sortedContacts.map(contact => {
                    const displayName = escapeHtml([contact.nome, contact.cognome].filter(Boolean).join(' ') || 'Senza nome');
                    const notePreview = contact.note ? escapeHtml(contact.note.substring(0, 100)) + (contact.note.length > 100 ? '...' : '') : '-';
                    return `
                        <tr class="contact-row" data-contact-id="${contact.contact_id}">
                            <td class="expand-cell">
                                <span class="expand-icon" id="expand-${contact.contact_id}">▶</span>
                            </td>
                            <td class="contact-name">
                                <strong>${displayName}</strong>
                            </td>
                            <td>
                                ${contact.tipo ? `<span class="badge badge-tipo">${escapeHtml(contact.tipo)}</span>` : '-'}
                            </td>
                            <td class="contact-notes">${notePreview}</td>
                        </tr>
                        <tr class="contact-details-row" id="details-row-${contact.contact_id}" style="display: none;">
                            <td colspan="4">
                                <div class="contact-details-content">
                                    <div class="details-grid">
                                        ${contact.email ? `
                                        <div class="detail-item">
                                            <span class="detail-label">📧 Email:</span>
                                            <a href="mailto:${escapeHtml(contact.email)}" class="item-link">${escapeHtml(contact.email)}</a>
                                        </div>
                                        ` : ''}
                                        ${contact.telefono ? `
                                        <div class="detail-item">
                                            <span class="detail-label">📱 Telefono:</span>
                                            <a href="tel:${escapeHtml(contact.telefono)}" class="item-link">${escapeHtml(contact.telefono)}</a>
                                        </div>
                                        ` : ''}
                                        ${contact.dove_conosciuto ? `
                                        <div class="detail-item">
                                            <span class="detail-label">📍 Dove Conosciuto:</span>
                                            <span>${escapeHtml(contact.dove_conosciuto)}</span>
                                        </div>
                                        ` : ''}
                                        ${contact.url ? `
                                        <div class="detail-item">
                                            <span class="detail-label">🔗 URL:</span>
                                            <a href="${escapeHtml(contact.url)}" target="_blank" class="item-link">${escapeHtml(contact.url)}</a>
                                        </div>
                                        ` : ''}
                                        <div class="detail-item">
                                            <span class="detail-label">📅 Creato:</span>
                                            <span>${formatDateTime(contact.created_at)}</span>
                                        </div>
                                        ${contact.updated_at && contact.updated_at !== contact.created_at ? `
                                        <div class="detail-item">
                                            <span class="detail-label">🔄 Aggiornato:</span>
                                            <span>${formatDateTime(contact.updated_at)}</span>
                                        </div>
                                        ` : ''}
                                    </div>
                                    ${contact.descrizione ? `
                                    <div class="detail-section">
                                        <span class="detail-label">📝 Descrizione:</span>
                                        <div class="item-description">${formatDescription(contact.descrizione)}</div>
                                    </div>
                                    ` : ''}
                                    ${contact.note ? `
                                    <div class="detail-section">
                                        <span class="detail-label">📄 Note Complete:</span>
                                        <div class="item-description">${formatDescription(contact.note)}</div>
                                    </div>
                                    ` : ''}
                                    <div class="detail-actions">
                                        <button class="btn-edit" onclick="editContact('${contact.contact_id}')">✏️ Modifica</button>
                                        <button class="btn-delete" onclick="deleteContact('${contact.contact_id}', '${displayName.replace(/'/g, "\\'")}')">🗑️ Elimina</button>
                                    </div>
                                </div>
                            </td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;
    
    // Aggiungi event listeners per espandere/comprimere
    document.querySelectorAll('.contact-row').forEach(row => {
        row.addEventListener('click', function() {
            const contactId = this.dataset.contactId;
            toggleContactDetails(contactId);
        });
    });
}

function sortContacts(contacts, sortOrder) {
    switch(sortOrder) {
        case 'date-desc':
            return contacts.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''));
        case 'date-asc':
            return contacts.sort((a, b) => (a.created_at || '').localeCompare(b.created_at || ''));
        case 'name-asc':
            return contacts.sort((a, b) => {
                const nameA = [a.cognome, a.nome].filter(Boolean).join(' ').toLowerCase();
                const nameB = [b.cognome, b.nome].filter(Boolean).join(' ').toLowerCase();
                return nameA.localeCompare(nameB);
            });
        case 'name-desc':
            return contacts.sort((a, b) => {
                const nameA = [a.cognome, a.nome].filter(Boolean).join(' ').toLowerCase();
                const nameB = [b.cognome, b.nome].filter(Boolean).join(' ').toLowerCase();
                return nameB.localeCompare(nameA);
            });
        default:
            return contacts;
    }
}

function toggleContactDetails(contactId) {
    const detailsRow = document.getElementById(`details-row-${contactId}`);
    const expandIcon = document.getElementById(`expand-${contactId}`);
    
    if (detailsRow.style.display === 'none' || !detailsRow.style.display) {
        detailsRow.style.display = 'table-row';
        expandIcon.textContent = '▼';
    } else {
        detailsRow.style.display = 'none';
        expandIcon.textContent = '▶';
    }
}

async function handleCreateContact(e) {
    e.preventDefault();
    
    const contactData = {
        nome: document.getElementById('contactNome').value.trim(),
        cognome: document.getElementById('contactCognome').value.trim(),
        email: document.getElementById('contactEmail').value.trim(),
        telefono: document.getElementById('contactTelefono').value.trim(),
        descrizione: document.getElementById('contactDescrizione').value.trim(),
        tipo: document.getElementById('contactTipo').value.trim(),
        dove_conosciuto: document.getElementById('contactDoveConosciuto').value.trim(),
        note: document.getElementById('contactNote').value.trim(),
        url: document.getElementById('contactUrl').value.trim()
    };
    
    // Rimuovi campi vuoti
    Object.keys(contactData).forEach(key => {
        if (!contactData[key]) delete contactData[key];
    });
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/contacts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(contactData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore creazione contatto');
        }
        
        // Reset form e nascondi
        document.getElementById('createContactForm').reset();
        document.getElementById('contactForm').style.display = 'none';
        
        // Ricarica lista
        await loadContacts();
        alert('Contatto creato con successo!');
        
    } catch (error) {
        console.error('Error creating contact:', error);
        alert(`Errore: ${error.message}`);
    }
}

let currentEditContact = null;

async function editContact(contactId) {
    try {
        const response = await fetch(`${CONFIG.API_URL}/contacts?contact_id=${contactId}`);
        if (!response.ok) {
            throw new Error('Errore caricamento contatto');
        }
        
        const data = await response.json();
        const contact = data.contacts[0];
        
        if (!contact) {
            throw new Error('Contatto non trovato');
        }
        
        currentEditContact = contact;
        
        // Popola il modal
        document.getElementById('editContactId').value = contact.contact_id;
        document.getElementById('editContactNome').value = contact.nome || '';
        document.getElementById('editContactCognome').value = contact.cognome || '';
        document.getElementById('editContactEmail').value = contact.email || '';
        document.getElementById('editContactTelefono').value = contact.telefono || '';
        document.getElementById('editContactDescrizione').value = contact.descrizione || '';
        document.getElementById('editContactTipo').value = contact.tipo || '';
        document.getElementById('editContactDoveConosciuto').value = contact.dove_conosciuto || '';
        document.getElementById('editContactNote').value = contact.note || '';
        document.getElementById('editContactUrl').value = contact.url || '';
        
        // Mostra modal
        document.getElementById('editContactModal').style.display = 'flex';
        
    } catch (error) {
        console.error('Error loading contact for edit:', error);
        alert(`Errore: ${error.message}`);
    }
}

async function deleteContact(contactId, contactName) {
    if (!confirm(`Sei sicuro di voler eliminare "${contactName}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/contacts`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ contact_id: contactId })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore eliminazione contatto');
        }
        
        await loadContacts();
        alert('Contatto eliminato con successo!');
        
    } catch (error) {
        console.error('Error deleting contact:', error);
        alert(`Errore: ${error.message}`);
    }
}

async function handleUpdateContact(e) {
    e.preventDefault();
    
    const contactData = {
        contact_id: document.getElementById('editContactId').value,
        nome: document.getElementById('editContactNome').value.trim(),
        cognome: document.getElementById('editContactCognome').value.trim(),
        email: document.getElementById('editContactEmail').value.trim(),
        telefono: document.getElementById('editContactTelefono').value.trim(),
        descrizione: document.getElementById('editContactDescrizione').value.trim(),
        tipo: document.getElementById('editContactTipo').value.trim(),
        dove_conosciuto: document.getElementById('editContactDoveConosciuto').value.trim(),
        note: document.getElementById('editContactNote').value.trim(),
        url: document.getElementById('editContactUrl').value.trim()
    };
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/contacts`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(contactData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore aggiornamento contatto');
        }
        
        // Close modal
        document.getElementById('editContactModal').style.display = 'none';
        currentEditContact = null;
        
        // Reload contacts
        await loadContacts();
        alert('Contatto aggiornato con successo!');
        
    } catch (error) {
        console.error('Error updating contact:', error);
        alert(`Errore: ${error.message}`);
    }
}

function closeEditContactModal() {
    document.getElementById('editContactModal').style.display = 'none';
    currentEditContact = null;
}

function closeEditGoalModal() {
    document.getElementById('editGoalModal').style.display = 'none';
    currentEditGoal = null;
}

function closeEditProjectModal() {
    document.getElementById('editProjectModal').style.display = 'none';
    currentEditProject = null;
}

// ========================================
// EVENTS & PLACES
// ========================================

// Load Events and Places
async function loadEventsAndPlaces() {
    try {
        const type = eventPlaceType.value;
        const location = eventPlaceFilterLocation.value.trim();
        const category = eventPlaceFilterCategory.value;
        
        let events = [];
        let places = [];
        
        // Load events if needed
        if (type === 'all' || type === 'events') {
            const eventParams = new URLSearchParams();
            if (location) eventParams.append('luogo', location);
            
            const eventResponse = await fetch(`${CONFIG.API_URL}/events?${eventParams}`);
            if (eventResponse.ok) {
                const eventData = await eventResponse.json();
                events = eventData.events || [];
            }
        }
        
        // Load places if needed
        if (type === 'all' || type === 'places') {
            const placeParams = new URLSearchParams();
            if (location) placeParams.append('indirizzo', location);
            if (category) placeParams.append('categoria', category);
            
            const placeResponse = await fetch(`${CONFIG.API_URL}/places?${placeParams}`);
            if (placeResponse.ok) {
                const placeData = await placeResponse.json();
                places = placeData.places || [];
            }
        }
        
        displayEventsAndPlaces(events, places);
        
    } catch (error) {
        console.error('Error loading events and places:', error);
        eventsPlacesList.innerHTML = '<p class="error">Errore nel caricamento. Riprova.</p>';
    }
}

function displayEventsAndPlaces(events, places) {
    if (events.length === 0 && places.length === 0) {
        eventsPlacesList.innerHTML = '<p class="no-data">Nessun evento o luogo trovato. Aggiungine uno!</p>';
        return;
    }
    
    let html = '';
    
    // Display events
    events.forEach(event => {
        html += `
            <div class="item-card">
                <div class="item-header">
                    <div>
                        <div class="item-badge event-badge">📅 Evento</div>
                        <h3>${escapeHtml(event.nome)}</h3>
                    </div>
                    <div class="item-actions">
                        <button onclick="editEvent('${event.event_id}')" class="edit-btn" title="Modifica">✏️</button>
                        <button onclick="deleteEvent('${event.event_id}')" class="delete-btn" title="Elimina">🗑️</button>
                    </div>
                </div>
                <div class="item-body">
                    ${event.data ? `<p><strong>📅 Data:</strong> ${formatDate(event.data)}</p>` : ''}
                    ${event.luogo ? `<p><strong>📍 Luogo:</strong> ${escapeHtml(event.luogo)}</p>` : ''}
                    ${event.descrizione ? `<p><strong>📝 Descrizione:</strong> ${escapeHtml(event.descrizione)}</p>` : ''}
                </div>
                <div class="item-footer">
                    <small>Creato: ${new Date(event.created_at).toLocaleString('it-IT')}</small>
                </div>
            </div>
        `;
    });
    
    // Display places
    places.forEach(place => {
        const categoryEmoji = getCategoryEmoji(place.categoria);
        html += `
            <div class="item-card">
                <div class="item-header">
                    <div>
                        <div class="item-badge place-badge">📍 Luogo</div>
                        <h3>${categoryEmoji} ${escapeHtml(place.nome)}</h3>
                    </div>
                    <div class="item-actions">
                        <button onclick="editPlace('${place.place_id}')" class="edit-btn" title="Modifica">✏️</button>
                        <button onclick="deletePlace('${place.place_id}')" class="delete-btn" title="Elimina">🗑️</button>
                    </div>
                </div>
                <div class="item-body">
                    ${place.categoria ? `<p><strong>🏷️ Categoria:</strong> ${getCategoryLabel(place.categoria)}</p>` : ''}
                    ${place.indirizzo ? `<p><strong>📮 Indirizzo:</strong> ${escapeHtml(place.indirizzo)}</p>` : ''}
                    ${place.descrizione ? `<p><strong>📝 Descrizione:</strong> ${escapeHtml(place.descrizione)}</p>` : ''}
                </div>
                <div class="item-footer">
                    <small>Creato: ${new Date(place.created_at).toLocaleString('it-IT')}</small>
                </div>
            </div>
        `;
    });
    
    eventsPlacesList.innerHTML = html;
}

// Helper functions for places
function getCategoryEmoji(category) {
    const emojiMap = {
        'ristorante': '🍽️',
        'sport': '⚽',
        'agriturismo': '🌾',
        'museo': '🏛️',
        'teatro': '🎭',
        'cinema': '🎬',
        'bar': '🍺',
        'hotel': '🏨',
        'parco': '🌳',
        'altro': '📌'
    };
    return emojiMap[category] || '📍';
}

function getCategoryLabel(category) {
    const labelMap = {
        'ristorante': 'Ristorante',
        'sport': 'Sport',
        'agriturismo': 'Agriturismo',
        'museo': 'Museo',
        'teatro': 'Teatro',
        'cinema': 'Cinema',
        'bar': 'Bar/Pub',
        'hotel': 'Hotel',
        'parco': 'Parco',
        'altro': 'Altro'
    };
    return labelMap[category] || category;
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('it-IT', { year: 'numeric', month: 'long', day: 'numeric' });
}

// Create Event
async function handleCreateEvent(e) {
    e.preventDefault();
    
    const eventData = {
        nome: document.getElementById('eventNome').value,
        data: document.getElementById('eventData').value,
        luogo: document.getElementById('eventLuogo').value,
        descrizione: document.getElementById('eventDescrizione').value
    };
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/events`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(eventData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore nella creazione dell\'evento');
        }
        
        eventForm.style.display = 'none';
        createEventForm.reset();
        await loadEventsAndPlaces();
        alert('Evento creato con successo!');
        
    } catch (error) {
        console.error('Error creating event:', error);
        alert(`Errore: ${error.message}`);
    }
}

// Create Place
async function handleCreatePlace(e) {
    e.preventDefault();
    
    const placeData = {
        nome: document.getElementById('placeNome').value,
        categoria: document.getElementById('placeCategoria').value,
        indirizzo: document.getElementById('placeIndirizzo').value,
        descrizione: document.getElementById('placeDescrizione').value
    };
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/places`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(placeData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore nella creazione del luogo');
        }
        
        placeForm.style.display = 'none';
        createPlaceForm.reset();
        await loadEventsAndPlaces();
        alert('Luogo creato con successo!');
        
    } catch (error) {
        console.error('Error creating place:', error);
        alert(`Errore: ${error.message}`);
    }
}

// Delete Event
async function deleteEvent(eventId) {
    if (!confirm('Sei sicuro di voler eliminare questo evento?')) {
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/events/${eventId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore nell\'eliminazione dell\'evento');
        }
        
        await loadEventsAndPlaces();
        alert('Evento eliminato con successo!');
        
    } catch (error) {
        console.error('Error deleting event:', error);
        alert(`Errore: ${error.message}`);
    }
}

// Delete Place
async function deletePlace(placeId) {
    if (!confirm('Sei sicuro di voler eliminare questo luogo?')) {
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/places/${placeId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore nell\'eliminazione del luogo');
        }
        
        await loadEventsAndPlaces();
        alert('Luogo eliminato con successo!');
        
    } catch (error) {
        console.error('Error deleting place:', error);
        alert(`Errore: ${error.message}`);
    }
}

// Edit Event
let currentEditEvent = null;
async function editEvent(eventId) {
    try {
        const response = await fetch(`${CONFIG.API_URL}/events/${eventId}`);
        if (!response.ok) throw new Error('Evento non trovato');
        
        const data = await response.json();
        const event = data.event;
        
        currentEditEvent = eventId;
        document.getElementById('editEventId').value = eventId;
        document.getElementById('editEventNome').value = event.nome || '';
        document.getElementById('editEventData').value = event.data || '';
        document.getElementById('editEventLuogo').value = event.luogo || '';
        document.getElementById('editEventDescrizione').value = event.descrizione || '';
        
        document.getElementById('editEventModal').style.display = 'flex';
        
    } catch (error) {
        console.error('Error loading event:', error);
        alert(`Errore: ${error.message}`);
    }
}

async function handleUpdateEvent(e) {
    e.preventDefault();
    
    const eventId = document.getElementById('editEventId').value;
    const updateData = {
        event_id: eventId,
        nome: document.getElementById('editEventNome').value,
        data: document.getElementById('editEventData').value,
        luogo: document.getElementById('editEventLuogo').value,
        descrizione: document.getElementById('editEventDescrizione').value
    };
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/events/${eventId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore nell\'aggiornamento');
        }
        
        closeEditEventModal();
        await loadEventsAndPlaces();
        alert('Evento aggiornato con successo!');
        
    } catch (error) {
        console.error('Error updating event:', error);
        alert(`Errore: ${error.message}`);
    }
}

function closeEditEventModal() {
    document.getElementById('editEventModal').style.display = 'none';
    currentEditEvent = null;
}

// Edit Place
let currentEditPlace = null;
async function editPlace(placeId) {
    try {
        const response = await fetch(`${CONFIG.API_URL}/places/${placeId}`);
        if (!response.ok) throw new Error('Luogo non trovato');
        
        const data = await response.json();
        const place = data.place;
        
        currentEditPlace = placeId;
        document.getElementById('editPlaceId').value = placeId;
        document.getElementById('editPlaceNome').value = place.nome || '';
        document.getElementById('editPlaceCategoria').value = place.categoria || '';
        document.getElementById('editPlaceIndirizzo').value = place.indirizzo || '';
        document.getElementById('editPlaceDescrizione').value = place.descrizione || '';
        
        document.getElementById('editPlaceModal').style.display = 'flex';
        
    } catch (error) {
        console.error('Error loading place:', error);
        alert(`Errore: ${error.message}`);
    }
}

async function handleUpdatePlace(e) {
    e.preventDefault();
    
    const placeId = document.getElementById('editPlaceId').value;
    const updateData = {
        place_id: placeId,
        nome: document.getElementById('editPlaceNome').value,
        categoria: document.getElementById('editPlaceCategoria').value,
        indirizzo: document.getElementById('editPlaceIndirizzo').value,
        descrizione: document.getElementById('editPlaceDescrizione').value
    };
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/places/${placeId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore nell\'aggiornamento');
        }
        
        closeEditPlaceModal();
        await loadEventsAndPlaces();
        alert('Luogo aggiornato con successo!');
        
    } catch (error) {
        console.error('Error updating place:', error);
        alert(`Errore: ${error.message}`);
    }
}

function closeEditPlaceModal() {
    document.getElementById('editPlaceModal').style.display = 'none';
    currentEditPlace = null;
}

// ========================================
// AUTHENTICATION
// ========================================

function checkLoginStatus() {
    if (!userPool) {
        console.error('Cognito User Pool non configurato. Aggiorna CONFIG.COGNITO_USER_POOL_ID e CONFIG.COGNITO_CLIENT_ID');
        loginError.textContent = 'Errore di configurazione. Contatta l\'amministratore.';
        loginError.style.display = 'block';
        return;
    }

    cognitoUser = userPool.getCurrentUser();
    
    if (cognitoUser != null) {
        cognitoUser.getSession((err, session) => {
            if (err) {
                console.error('Session error:', err);
                showLoginScreen();
                return;
            }
            
            if (session.isValid()) {
                currentUser = cognitoUser.getUsername();
                idToken = session.getIdToken().getJwtToken();
                showMainApp();
                
                // Load data
                loadGoals();
                loadProjects();
                loadContacts();
                loadEventsAndPlaces();
            } else {
                showLoginScreen();
            }
        });
    } else {
        showLoginScreen();
    }
}

function showLoginScreen() {
    loginScreen.style.display = 'flex';
    mainApp.style.display = 'none';
}

function showMainApp() {
    loginScreen.style.display = 'none';
    mainApp.style.display = 'flex';
}

function handleLogin(e) {
    e.preventDefault();
    
    if (!userPool) {
        loginError.textContent = 'Cognito non configurato';
        loginError.style.display = 'block';
        return;
    }

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const loginBtn = document.getElementById('loginBtn');
    
    // Disable button and show loading
    loginBtn.disabled = true;
    loginBtn.textContent = 'Accesso in corso...';
    loginError.style.display = 'none';
    
    const authenticationData = {
        Username: username,
        Password: password,
    };
    
    const authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails(authenticationData);
    
    const userData = {
        Username: username,
        Pool: userPool,
    };
    
    cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);
    
    cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: (result) => {
            console.log('Login successful');
            currentUser = username;
            idToken = result.getIdToken().getJwtToken();
            
            // Clear form
            loginForm.reset();
            loginBtn.disabled = false;
            loginBtn.textContent = 'Accedi';
            
            // Show main app
            showMainApp();
            
            // Load data
            loadGoals();
            loadProjects();
            loadContacts();
            loadEventsAndPlaces();
        },
        
        onFailure: (err) => {
            console.error('Login failed:', err);
            
            // Re-enable button
            loginBtn.disabled = false;
            loginBtn.textContent = 'Accedi';
            
            // Show error message
            let errorMessage = 'Errore di accesso';
            
            if (err.code === 'NotAuthorizedException') {
                errorMessage = 'Username o password non corretti';
            } else if (err.code === 'UserNotFoundException') {
                errorMessage = 'Utente non trovato';
            } else if (err.code === 'UserNotConfirmedException') {
                errorMessage = 'Utente non confermato. Controlla la tua email.';
            } else if (err.message) {
                errorMessage = err.message;
            }
            
            loginError.textContent = errorMessage;
            loginError.style.display = 'block';
            
            // Shake animation
            loginForm.style.animation = 'shake 0.5s';
            setTimeout(() => {
                loginForm.style.animation = '';
            }, 500);
        },
        
        newPasswordRequired: (userAttributes, requiredAttributes) => {
            // Handle new password required (first login)
            const newPassword = prompt('È necessario cambiare la password. Inserisci una nuova password:');
            
            if (newPassword) {
                cognitoUser.completeNewPasswordChallenge(newPassword, {}, {
                    onSuccess: (result) => {
                        console.log('Password changed successfully');
                        idToken = result.getIdToken().getJwtToken();
                        showMainApp();
                    },
                    onFailure: (err) => {
                        console.error('Password change failed:', err);
                        loginError.textContent = 'Errore nel cambio password: ' + err.message;
                        loginError.style.display = 'block';
                        loginBtn.disabled = false;
                        loginBtn.textContent = 'Accedi';
                    }
                });
            } else {
                loginBtn.disabled = false;
                loginBtn.textContent = 'Accedi';
            }
        }
    });
}

function handleLogout() {
    if (confirm('Sei sicuro di voler uscire?')) {
        if (cognitoUser) {
            cognitoUser.signOut();
        }
        
        currentUser = null;
        idToken = null;
        cognitoUser = null;
        
        // Clear session data
        sessionId = generateSessionId();
        sessionIdDisplay.textContent = sessionId;
        chatMessages.innerHTML = '';
        
        // Show login screen
        showLoginScreen();
    }
}

// ========================================
// INITIALIZATION
// ========================================

// Avvia l'app
init();
