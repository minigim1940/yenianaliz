// Main JavaScript file for Güvenilir Analiz

// Global variables
let analysisCache = new Map();
let currentUser = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize animations
    animateOnScroll();
    
    // Set up global event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // AJAX form handling
    document.addEventListener('submit', function(e) {
        if (e.target.classList.contains('ajax-form')) {
            e.preventDefault();
            handleAjaxForm(e.target);
        }
    });
    
    // Auto-save form data
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('auto-save')) {
            saveFormData(e.target);
        }
    });
}

// API Communication
async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data) {
        if (method === 'GET') {
            const params = new URLSearchParams(data);
            endpoint += '?' + params.toString();
        } else {
            options.body = JSON.stringify(data);
        }
    }
    
    try {
        const response = await fetch(endpoint, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || 'API hatası oluştu');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        showNotification('Hata: ' + error.message, 'error');
        throw error;
    }
}

// Match Analysis Functions
async function analyzeMatch(homeTeam, awayTeam, showModal = true) {
    const cacheKey = `${homeTeam}-${awayTeam}`;
    
    // Check cache first
    if (analysisCache.has(cacheKey)) {
        const cachedResult = analysisCache.get(cacheKey);
        if (showModal) {
            displayAnalysisResult(cachedResult);
        }
        return cachedResult;
    }
    
    if (showModal) {
        showAnalysisModal();
    }
    
    try {
        const formData = new FormData();
        formData.append('home_team', homeTeam);
        formData.append('away_team', awayTeam);
        
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Cache the result
            analysisCache.set(cacheKey, result);
            
            if (showModal) {
                displayAnalysisResult(result);
            }
            
            return result;
        } else {
            throw new Error(result.detail || 'Analiz hatası');
        }
    } catch (error) {
        if (showModal) {
            displayAnalysisError(error.message);
        }
        throw error;
    }
}

function showAnalysisModal() {
    const modal = new bootstrap.Modal(document.getElementById('analysisModal'));
    document.getElementById('analysisContent').innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Analiz yapılıyor...</span>
            </div>
            <p class="mt-3">AI modeli analiz yapıyor, lütfen bekleyin...</p>
            <div class="progress mt-3">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 0%"></div>
            </div>
        </div>
    `;
    
    // Fake progress animation
    animateProgress();
    modal.show();
}

function animateProgress() {
    const progressBar = document.querySelector('#analysisModal .progress-bar');
    if (!progressBar) return;
    
    let width = 0;
    const interval = setInterval(() => {
        width += Math.random() * 15;
        if (width >= 90) {
            width = 90;
            clearInterval(interval);
        }
        progressBar.style.width = width + '%';
    }, 200);
}

function displayAnalysisResult(result) {
    const content = `
        <div class="analysis-result fade-in">
            <div class="text-center mb-4">
                <h4 class="mb-3">
                    <span class="badge bg-primary me-2">${result.home_team}</span>
                    <span class="text-muted">vs</span>
                    <span class="badge bg-danger ms-2">${result.away_team}</span>
                </h4>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card bg-gradient bg-primary text-white">
                        <div class="card-body text-center">
                            <i class="fas fa-trophy fs-1 mb-2"></i>
                            <h5>AI Tahmini</h5>
                            <h3 class="fw-bold">${result.prediction}</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card bg-gradient bg-success text-white">
                        <div class="card-body text-center">
                            <i class="fas fa-chart-line fs-1 mb-2"></i>
                            <h5>Güven Oranı</h5>
                            <h3 class="fw-bold">${result.confidence}%</h3>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-4">
                    <div class="text-center p-3 bg-light rounded">
                        <i class="fas fa-bullseye text-primary"></i>
                        <div class="mt-2">
                            <strong>Beklenen Skor</strong>
                            <div class="h5 mb-0">${result.expected_score || '2-1'}</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="text-center p-3 bg-light rounded">
                        <i class="fas fa-percentage text-warning"></i>
                        <div class="mt-2">
                            <strong>2.5 Üst</strong>
                            <div class="h5 mb-0">${result.over_2_5 || '65%'}</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="text-center p-3 bg-light rounded">
                        <i class="fas fa-handshake text-info"></i>
                        <div class="mt-2">
                            <strong>KG Var</strong>
                            <div class="h5 mb-0">${result.both_score || '58%'}</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="d-grid gap-2">
                <a href="/analysis?home=${encodeURIComponent(result.home_team)}&away=${encodeURIComponent(result.away_team)}" 
                   class="btn btn-primary btn-lg">
                    <i class="fas fa-eye me-2"></i>Detaylı Analizi Görüntüle
                </a>
                <button class="btn btn-outline-secondary" onclick="shareAnalysis('${result.home_team}', '${result.away_team}')">
                    <i class="fas fa-share me-2"></i>Analizi Paylaş
                </button>
            </div>
        </div>
    `;
    
    document.getElementById('analysisContent').innerHTML = content;
}

function displayAnalysisError(message) {
    document.getElementById('analysisContent').innerHTML = `
        <div class="text-center">
            <i class="fas fa-exclamation-triangle fs-1 text-warning mb-3"></i>
            <h5>Analiz Yapılamadı</h5>
            <p class="text-muted">${message}</p>
            <button class="btn btn-primary" onclick="location.reload()">
                <i class="fas fa-redo me-2"></i>Tekrar Dene
            </button>
        </div>
    `;
}

// Notification System
function showNotification(message, type = 'info', duration = 5000) {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${getIconForType(type)} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                    data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, { delay: duration });
    bsToast.show();
    
    // Remove from DOM after hiding
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

function getIconForType(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle',
        'primary': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Utility Functions
function animateOnScroll() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    });
    
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
}

function saveFormData(input) {
    const formId = input.closest('form')?.id;
    if (formId) {
        const data = localStorage.getItem(`form_${formId}`) || '{}';
        const formData = JSON.parse(data);
        formData[input.name] = input.value;
        localStorage.setItem(`form_${formId}`, JSON.stringify(formData));
    }
}

function loadFormData(formId) {
    const data = localStorage.getItem(`form_${formId}`);
    if (data) {
        const formData = JSON.parse(data);
        Object.keys(formData).forEach(key => {
            const input = document.querySelector(`#${formId} [name="${key}"]`);
            if (input) {
                input.value = formData[key];
            }
        });
    }
}

// Share functionality
function shareAnalysis(homeTeam, awayTeam) {
    const url = `${window.location.origin}/analysis?home=${encodeURIComponent(homeTeam)}&away=${encodeURIComponent(awayTeam)}`;
    const text = `${homeTeam} vs ${awayTeam} maç analizi - Güvenilir Analiz`;
    
    if (navigator.share) {
        navigator.share({
            title: text,
            url: url
        });
    } else {
        // Fallback: Copy to clipboard
        navigator.clipboard.writeText(url).then(() => {
            showNotification('Link kopyalandı!', 'success');
        });
    }
}

// Chart utilities
function createChart(ctx, type, data, options = {}) {
    return new Chart(ctx, {
        type: type,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            ...options
        }
    });
}

// Export functions for global use
window.analyzeMatch = analyzeMatch;
window.showNotification = showNotification;
window.shareAnalysis = shareAnalysis;
window.createChart = createChart;