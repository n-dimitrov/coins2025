// My EuroCoins - Main Application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('🪙 My EuroCoins application loaded');
    
    // Initialize common functionality
    initializeApp();
});

function initializeApp() {
    // Add smooth scrolling to all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Add loading states to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
                submitBtn.disabled = true;
            }
        });
    });

    // Add hover effects to cards (excluding admin panel cards)
    document.querySelectorAll('.card').forEach(card => {
        // Skip hover effects for admin panel cards
        if (card.closest('.admin-panel')) {
            return;
        }
        
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Utility functions
function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

function showToast(message, type = 'info') {
    // Simple toast notification (could be enhanced with Bootstrap toast)
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// API helper functions
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(endpoint, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Export for use in other files
window.MyEuroCoins = {
    formatNumber,
    showToast,
    apiCall
};
