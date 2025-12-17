// Configurazione
const CONFIG = {
    ORCHESTRATOR_URL: 'http://localhost:5000/invoke',  // Backend proxy per orchestrator AWS
    API_URL: 'http://localhost:5000/api',  // API Gateway locale (sarà aggiornato dopo deploy)
    ACTOR_ID: 'chat-user'
};

// Stato dell'applicazione
let sessionId = generateSessionId();
let isLoading = false;
let currentView = 'chat';

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

// Inizializzazione
function init() {
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
    
    // Load data when switching to goals/projects
    if (viewName === 'goals') {
        loadGoals();
    } else if (viewName === 'projects') {
        loadProjects();
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
    
    const params = new URLSearchParams();
    const ambito = projectFilterAmbito.value.trim();
    const tag = projectFilterTag.value.trim();
    
    if (ambito) params.append('ambito', ambito);
    if (tag) params.append('tag', tag);
    
    try {
        const response = await fetch(`${CONFIG.API_URL}/projects?${params.toString()}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayProjects(data.projects || []);
        
    } catch (error) {
        console.error('Error loading projects:', error);
        projectsList.innerHTML = `<p class="error-message">Errore caricamento progetti: ${error.message}</p>`;
    }
}

function displayProjects(projects) {
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

function closeEditGoalModal() {
    document.getElementById('editGoalModal').style.display = 'none';
    currentEditGoal = null;
}

function closeEditProjectModal() {
    document.getElementById('editProjectModal').style.display = 'none';
    currentEditProject = null;
}

// ========================================
// INITIALIZATION
// ========================================

// Avvia l'app
init();
