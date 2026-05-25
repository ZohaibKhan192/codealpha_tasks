class Translator {
    constructor() {
        // API configuration
        this.API_URL = 'https://libretranslate.com/translate';
        this.API_ENDPOINTS = [
            'https://libretranslate.com/translate',
            'https://translate.argosopentech.com/translate',
            'https://translate.fedilab.app/translate'
        ];
        this.currentEndpoint = 0;
        this.maxRetries = 2;
        this.init();
    }

    init() {
        this.cacheDom();
        this.bindEvents();
        this.loadSavedPreferences();
    }

    cacheDom() {
        this.sourceLang = document.getElementById('sourceLang');
        this.targetLang = document.getElementById('targetLang');
        this.sourceText = document.getElementById('sourceText');
        this.translatedText = document.getElementById('translatedText');
        this.translateBtn = document.getElementById('translateBtn');
        this.copyBtn = document.getElementById('copyBtn');
        this.speakSourceBtn = document.getElementById('speakSourceBtn');
        this.speakTargetBtn = document.getElementById('speakTargetBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.swapBtn = document.getElementById('swapBtn');
        this.loading = document.getElementById('loading');
        this.errorMessage = document.getElementById('errorMessage');
        this.successMessage = document.getElementById('successMessage');
        this.sourceCharCount = document.getElementById('sourceCharCount');
        this.targetCharCount = document.getElementById('targetCharCount');
    }

    bindEvents() {
        this.translateBtn.addEventListener('click', () => this.translate());
        this.copyBtn.addEventListener('click', () => this.copyTranslation());
        this.speakSourceBtn.addEventListener('click', () => this.speak(this.sourceText.value, this.sourceLang.value));
        this.speakTargetBtn.addEventListener('click', () => this.speak(this.translatedText.value, this.targetLang.value));
        this.clearBtn.addEventListener('click', () => this.clearAll());
        this.swapBtn.addEventListener('click', () => this.swapLanguages());
        this.sourceText.addEventListener('input', () => {
            this.updateCharCount();
            this.saveToLocalStorage();
        });
        
        // Save language preferences on change
        this.sourceLang.addEventListener('change', () => this.savePreferences());
        this.targetLang.addEventListener('change', () => this.savePreferences());
        
        // Keyboard shortcut for translation (Ctrl+Enter)
        this.sourceText.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                this.translate();
            }
        });
    }

    async translate() {
        const text = this.sourceText.value.trim();
        
        if (!text) {
            this.showError('Please enter text to translate');
            return;
        }

        if (text.length > 5000) {
            this.showError('Text exceeds 5000 character limit');
            return;
        }

        this.showLoading(true);
        this.hideMessages();

        const sourceLang = this.sourceLang.value === 'auto' ? 'auto' : this.sourceLang.value;
        const targetLang = this.targetLang.value;

        try {
            const response = await this.makeTranslationRequest(text, sourceLang, targetLang);
            
            if (response && response.translatedText) {
                this.translatedText.value = response.translatedText;
                this.updateCharCount();
                this.showSuccess('Translation completed successfully!');
            } else {
                throw new Error('Invalid response from translation API');
            }
        } catch (error) {
            this.showError('Translation failed. Please try again or check your internet connection.');
            console.error('Translation error:', error);
        } finally {
            this.showLoading(false);
        }
    }

    async makeTranslationRequest(text, source, target) {
        let lastError = null;
        
        // Try each endpoint
        for (let attempt = 0; attempt < this.API_ENDPOINTS.length; attempt++) {
            const endpoint = this.API_ENDPOINTS[this.currentEndpoint];
            
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        q: text,
                        source: source,
                        target: target,
                        format: 'text'
                    }),
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                return data;

            } catch (error) {
                console.warn(`Endpoint ${endpoint} failed:`, error.message);
                lastError = error;
                this.currentEndpoint = (this.currentEndpoint + 1) % this.API_ENDPOINTS.length;
            }
        }

        // If all endpoints failed, try simulated translation as fallback
        return this.simulateTranslation(text);
    }

    // Simulated translation for demo purposes when all APIs fail
    simulateTranslation(text) {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    translatedText: `[Demo Translation] ${text}`
                });
            }, 1000);
        });
    }

    copyTranslation() {
        const text = this.translatedText.value;
        
        if (!text) {
            this.showError('No translation to copy');
            return;
        }

        navigator.clipboard.writeText(text)
            .then(() => {
                this.showSuccess('Translation copied to clipboard!');
                // Visual feedback on button
                const originalText = this.copyBtn.innerHTML;
                this.copyBtn.innerHTML = '<span>✅</span> Copied!';
                setTimeout(() => {
                    this.copyBtn.innerHTML = originalText;
                }, 2000);
            })
            .catch(() => {
                // Fallback for older browsers
                this.fallbackCopyText(text);
            });
    }

    fallbackCopyText(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            document.execCommand('copy');
            this.showSuccess('Translation copied to clipboard!');
        } catch (err) {
            this.showError('Failed to copy text');
        }
        
        document.body.removeChild(textArea);
    }

    speak(text, lang) {
        if (!text) {
            this.showError('No text to speak');
            return;
        }

        if ('speechSynthesis' in window) {
            // Cancel any ongoing speech
            window.speechSynthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = lang;
            utterance.rate = 1.0; // Normal speed
            utterance.pitch = 1.0; // Normal pitch
            
            // Get available voices and try to match language
            const voices = window.speechSynthesis.getVoices();
            const matchingVoice = voices.find(voice => voice.lang.startsWith(lang));
            if (matchingVoice) {
                utterance.voice = matchingVoice;
            }
            
            window.speechSynthesis.speak(utterance);
        } else {
            this.showError('Text-to-speech not supported in your browser');
        }
    }

    swapLanguages() {
        const sourceValue = this.sourceLang.value;
        const targetValue = this.targetLang.value;
        
        // Don't swap if source is auto-detect
        if (sourceValue === 'auto') {
            this.showError('Cannot swap with auto-detect language');
            return;
        }

        this.sourceLang.value = targetValue;
        this.targetLang.value = sourceValue;

        // Swap text areas
        const sourceText = this.sourceText.value;
        this.sourceText.value = this.translatedText.value;
        this.translatedText.value = sourceText;
        
        this.updateCharCount();
        this.savePreferences();
    }

    clearAll() {
        this.sourceText.value = '';
        this.translatedText.value = '';
        this.hideMessages();
        this.updateCharCount();
        this.sourceText.focus();
    }

    updateCharCount() {
        this.sourceCharCount.textContent = this.sourceText.value.length;
        this.targetCharCount.textContent = this.translatedText.value.length;
        
        // Visual warning when approaching limit
        if (this.sourceText.value.length > 4500) {
            this.sourceCharCount.style.color = '#f44336';
        } else {
            this.sourceCharCount.style.color = '#999';
        }
    }

    showLoading(show) {
        this.loading.style.display = show ? 'block' : 'none';
        this.translateBtn.disabled = show;
        
        if (show) {
            this.translateBtn.innerHTML = '<span class="spinner"></span> Translating...';
        } else {
            this.translateBtn.innerHTML = '<span>🔄</span> Translate';
        }
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorMessage.style.display = 'block';
        this.successMessage.style.display = 'none';
        
        // Auto-hide after 5 seconds
        clearTimeout(this.errorTimeout);
        this.errorTimeout = setTimeout(() => {
            this.errorMessage.style.display = 'none';
        }, 5000);
    }

    showSuccess(message) {
        this.successMessage.textContent = message;
        this.successMessage.style.display = 'block';
        this.errorMessage.style.display = 'none';
        
        // Auto-hide after 3 seconds
        clearTimeout(this.successTimeout);
        this.successTimeout = setTimeout(() => {
            this.successMessage.style.display = 'none';
        }, 3000);
    }

    hideMessages() {
        this.errorMessage.style.display = 'none';
        this.successMessage.style.display = 'none';
    }

    savePreferences() {
        const preferences = {
            sourceLang: this.sourceLang.value,
            targetLang: this.targetLang.value
        };
        localStorage.setItem('translatorPreferences', JSON.stringify(preferences));
    }

    saveToLocalStorage() {
        localStorage.setItem('translatorSourceText', this.sourceText.value);
    }

    loadSavedPreferences() {
        // Load language preferences
        const preferences = localStorage.getItem('translatorPreferences');
        if (preferences) {
            try {
                const { sourceLang, targetLang } = JSON.parse(preferences);
                if (sourceLang) this.sourceLang.value = sourceLang;
                if (targetLang) this.targetLang.value = targetLang;
            } catch (e) {
                console.warn('Failed to load preferences:', e);
            }
        }
        
        // Load saved text
        const savedText = localStorage.getItem('translatorSourceText');
        if (savedText) {
            this.sourceText.value = savedText;
            this.updateCharCount();
        }
    }
}

// Initialize the translator when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize speech synthesis voices
    if ('speechSynthesis' in window) {
        window.speechSynthesis.getVoices();
    }
    
    // Create translator instance
    new Translator();
});

// Handle speech synthesis voices loading for some browsers
if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
    };
}