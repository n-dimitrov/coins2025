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

    // Add hover effects to cards (excluding admin panel and member stat cards)
    document.querySelectorAll('.card').forEach(card => {
        // Skip hover effects for admin panel cards and member stat cards
        if (card.closest('.admin-panel') || card.classList.contains('member-stat-card')) {
            return;
        }

        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Initialize activity carousels
    initializeActivityCarousels();
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

// Activity Carousel functionality
let carouselStates = {};

function initializeActivityCarousels() {
    const carousels = document.querySelectorAll('.activity-carousel');
    carousels.forEach(carousel => {
        const member = carousel.dataset.member;
        const slides = carousel.querySelectorAll('.activity-card');

        if (slides.length > 1) { // Only initialize if there are multiple slides
            carouselStates[member] = {
                currentSlide: 0,
                totalSlides: slides.length,
                track: carousel.querySelector('.carousel-track'),
                prevBtn: carousel.querySelector('.prev-btn'),
                nextBtn: carousel.querySelector('.next-btn')
            };

            updateCarouselState(member);
            addTouchSupport(carousel, member);
        } else {
            // Hide controls if only one slide
            const controls = carousel.querySelector('.carousel-controls');
            if (controls) controls.style.display = 'none';
        }
    });

    // Add keyboard support
    addKeyboardSupport();

    // Add visual feedback for button clicks
    addClickFeedback();
}

function moveCarousel(member, direction) {
    const state = carouselStates[member];
    if (!state) return;

    const newSlide = state.currentSlide + direction;

    if (newSlide >= 0 && newSlide < state.totalSlides) {
        state.currentSlide = newSlide;
        updateCarouselState(member);
    }
}

function updateCarouselState(member) {
    const state = carouselStates[member];
    if (!state) return;

    // Simple translation: each slide is 100% width, so slide N is at -N * 100%
    const translateX = -(state.currentSlide * 100);
    state.track.style.transform = `translateX(${translateX}%)`;

    // Update button states
    if (state.prevBtn) {
        state.prevBtn.disabled = state.currentSlide === 0;
    }
    if (state.nextBtn) {
        state.nextBtn.disabled = state.currentSlide === state.totalSlides - 1;
    }
}

// Touch support for mobile devices
function addTouchSupport(carousel, member) {
    let startX = 0;
    let currentX = 0;
    let isDragging = false;

    carousel.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
        isDragging = true;
        carousel.style.cursor = 'grabbing';
    });

    carousel.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        e.preventDefault();
        currentX = e.touches[0].clientX;
    });

    carousel.addEventListener('touchend', () => {
        if (!isDragging) return;
        isDragging = false;
        carousel.style.cursor = 'grab';

        const deltaX = startX - currentX;
        const threshold = 50; // Minimum swipe distance

        if (Math.abs(deltaX) > threshold) {
            if (deltaX > 0) {
                moveCarousel(member, 1); // Swipe left -> next
            } else {
                moveCarousel(member, -1); // Swipe right -> prev
            }
        }
    });
}

// Keyboard support
function addKeyboardSupport() {
    document.addEventListener('keydown', (e) => {
        // Only respond to arrow keys when focused on the page
        if (e.target === document.body) {
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    // Move all carousels for demo purposes, in real app you'd focus one
                    Object.keys(carouselStates).forEach(member => moveCarousel(member, -1));
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    Object.keys(carouselStates).forEach(member => moveCarousel(member, 1));
                    break;
            }
        }
    });
}

// Add visual feedback for interactions
function addClickFeedback() {
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('carousel-btn')) {
            e.target.style.transform = 'scale(0.95)';
            setTimeout(() => {
                e.target.style.transform = '';
            }, 100);
        }
    });
}

// Export for use in other files
window.MyEuroCoins = {
    formatNumber,
    showToast,
    apiCall
};

// Make moveCarousel globally available for onclick handlers
window.moveCarousel = moveCarousel;
