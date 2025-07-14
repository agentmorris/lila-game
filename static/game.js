/**
 * Wildlife Camera Trap Game - JavaScript Utilities
 * Common functions and utilities used across the application
 */

// Global loading state management
function showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        const text = overlay.querySelector('p');
        if (text) text.textContent = message;
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Image preloading utility
function preloadImage(src) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = src;
    });
}

// Preload multiple images
function preloadImages(urls) {
    return Promise.all(urls.map(url => preloadImage(url).catch(() => null)));
}

// Debounce utility for input handling
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Toast notification system
function showToast(message, type = 'info', duration = 3000) {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => toast.remove());
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-message">${message}</span>
            <button class="toast-close">&times;</button>
        </div>
    `;
    
    // Add styles if not already added
    if (!document.getElementById('toast-styles')) {
        const styles = document.createElement('style');
        styles.id = 'toast-styles';
        styles.textContent = `
            .toast {
                position: fixed;
                top: 20px;
                right: 20px;
                background: #333;
                color: white;
                padding: 1rem;
                border-radius: 0.5rem;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                z-index: 1001;
                animation: slideIn 0.3s ease;
                max-width: 400px;
            }
            
            .toast-info { background: #3498db; }
            .toast-success { background: #27ae60; }
            .toast-warning { background: #f39c12; }
            .toast-error { background: #e74c3c; }
            
            .toast-content {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 1rem;
            }
            
            .toast-close {
                background: none;
                border: none;
                color: white;
                font-size: 1.2rem;
                cursor: pointer;
                padding: 0;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(styles);
    }
    
    // Add to page
    document.body.appendChild(toast);
    
    // Close button functionality
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => {
        removeToast(toast);
    });
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            removeToast(toast);
        }, duration);
    }
    
    return toast;
}

function removeToast(toast) {
    toast.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

// Local storage utilities (with fallback for environments that don't support it)
const storage = {
    get: function(key, defaultValue = null) {
        try {
            if (typeof localStorage !== 'undefined') {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            }
        } catch (e) {
            console.warn('localStorage not available:', e);
        }
        return defaultValue;
    },
    
    set: function(key, value) {
        try {
            if (typeof localStorage !== 'undefined') {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            }
        } catch (e) {
            console.warn('localStorage not available:', e);
        }
        return false;
    },
    
    remove: function(key) {
        try {
            if (typeof localStorage !== 'undefined') {
                localStorage.removeItem(key);
                return true;
            }
        } catch (e) {
            console.warn('localStorage not available:', e);
        }
        return false;
    }
};

// Keyboard navigation helpers
function setupKeyboardNavigation(container, itemSelector, onSelect) {
    let currentIndex = -1;
    const items = container.querySelectorAll(itemSelector);
    
    function updateSelection() {
        items.forEach((item, index) => {
            item.classList.toggle('keyboard-selected', index === currentIndex);
        });
    }
    
    function handleKeydown(e) {
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                currentIndex = Math.min(currentIndex + 1, items.length - 1);
                updateSelection();
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                currentIndex = Math.max(currentIndex - 1, -1);
                updateSelection();
                break;
                
            case 'Enter':
                e.preventDefault();
                if (currentIndex >= 0 && items[currentIndex]) {
                    onSelect(items[currentIndex], currentIndex);
                }
                break;
                
            case 'Escape':
                currentIndex = -1;
                updateSelection();
                break;
        }
    }
    
    return {
        enable: () => {
            document.addEventListener('keydown', handleKeydown);
        },
        disable: () => {
            document.removeEventListener('keydown', handleKeydown);
            currentIndex = -1;
            updateSelection();
        },
        reset: () => {
            currentIndex = -1;
            updateSelection();
        }
    };
}

// Form validation helpers
function validateForm(form, rules) {
    const errors = {};
    
    Object.keys(rules).forEach(fieldName => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        const rule = rules[fieldName];
        
        if (!field) return;
        
        const value = field.value.trim();
        
        // Required field check
        if (rule.required && !value) {
            errors[fieldName] = rule.requiredMessage || `${fieldName} is required`;
            return;
        }
        
        // Skip other validations if field is empty and not required
        if (!value) return;
        
        // Length validation
        if (rule.minLength && value.length < rule.minLength) {
            errors[fieldName] = rule.minLengthMessage || `${fieldName} must be at least ${rule.minLength} characters`;
        }
        
        if (rule.maxLength && value.length > rule.maxLength) {
            errors[fieldName] = rule.maxLengthMessage || `${fieldName} must be no more than ${rule.maxLength} characters`;
        }
        
        // Pattern validation
        if (rule.pattern && !rule.pattern.test(value)) {
            errors[fieldName] = rule.patternMessage || `${fieldName} format is invalid`;
        }
        
        // Custom validation
        if (rule.validate && typeof rule.validate === 'function') {
            const customError = rule.validate(value);
            if (customError) {
                errors[fieldName] = customError;
            }
        }
    });
    
    return {
        isValid: Object.keys(errors).length === 0,
        errors: errors
    };
}

// Display form errors
function displayFormErrors(form, errors) {
    // Clear existing errors
    form.querySelectorAll('.field-error').forEach(error => error.remove());
    form.querySelectorAll('.error').forEach(field => field.classList.remove('error'));
    
    // Display new errors
    Object.keys(errors).forEach(fieldName => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.classList.add('error');
            
            const errorElement = document.createElement('div');
            errorElement.className = 'field-error';
            errorElement.textContent = errors[fieldName];
            
            field.parentNode.insertBefore(errorElement, field.nextSibling);
        }
    });
}

// Analytics helpers (placeholder for future implementation)
const analytics = {
    trackEvent: function(category, action, label = null, value = null) {
        // Placeholder for analytics tracking
        console.log('Analytics event:', { category, action, label, value });
    },
    
    trackPageView: function(page) {
        console.log('Analytics page view:', page);
    },
    
    trackGameStart: function() {
        this.trackEvent('Game', 'Start');
    },
    
    trackGameComplete: function(score, questions) {
        this.trackEvent('Game', 'Complete', 'Score', score);
        this.trackEvent('Game', 'Complete', 'Questions', questions);
    },
    
    trackGuess: function(isCorrect, points) {
        this.trackEvent('Game', 'Guess', isCorrect ? 'Correct' : 'Incorrect', points);
    }
};

// Performance monitoring
const performance = {
    marks: {},
    
    mark: function(name) {
        this.marks[name] = Date.now();
    },
    
    measure: function(startMark, endMark = null) {
        const start = this.marks[startMark];
        const end = endMark ? this.marks[endMark] : Date.now();
        
        if (!start) {
            console.warn(`Performance mark '${startMark}' not found`);
            return 0;
        }
        
        return end - start;
    },
    
    log: function(name, startMark, endMark = null) {
        const duration = this.measure(startMark, endMark);
        console.log(`Performance: ${name} took ${duration}ms`);
        return duration;
    }
};

// Device and browser detection
const device = {
    isMobile: function() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },
    
    isTablet: function() {
        return /iPad|Android/i.test(navigator.userAgent) && !this.isMobile();
    },
    
    isDesktop: function() {
        return !this.isMobile() && !this.isTablet();
    },
    
    supportsTouch: function() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
};

// Initialize global event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Add any global initialization here
    
    // Close modals when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Escape key closes modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal[style*="block"]');
            if (openModal) {
                openModal.style.display = 'none';
            }
        }
    });
    
    // Handle form submissions with loading states
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.classList.contains('loading-form')) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Loading...';
                
                // Re-enable after 10 seconds as failsafe
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.textContent = submitBtn.getAttribute('data-original-text') || 'Submit';
                }, 10000);
            }
        }
    });
});

// Export utilities for use in other scripts
if (typeof window !== 'undefined') {
    window.gameUtils = {
        showLoading,
        hideLoading,
        preloadImage,
        preloadImages,
        debounce,
        formatNumber,
        showToast,
        removeToast,
        storage,
        setupKeyboardNavigation,
        validateForm,
        displayFormErrors,
        analytics,
        performance,
        device
    };
}