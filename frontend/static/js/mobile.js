// Mobile-specific JavaScript for LogiComp Platform - All Pages

class MobileOptimizer {
    constructor() {
        this.isMobile = this.detectMobile();
        this.isTouchDevice = this.detectTouchDevice();
        this.orientation = this.getOrientation();
        this.init();
    }

    // Detect if device is mobile
    detectMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               window.innerWidth <= 768;
    }

    // Detect if device supports touch
    detectTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }

    // Get current orientation
    getOrientation() {
        return window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
    }

    init() {
        if (this.isMobile) {
            this.setupMobileOptimizations();
            this.setupTouchOptimizations();
            this.setupOrientationHandling();
            this.setupMobileNavigation();
            this.setupMobileForms();
            this.setupMobileTables();
            this.setupMobileModals();
            this.setupMobileScroll();
            this.setupMobilePerformance();
            this.setupMobileSpecificFeatures();
        }
    }

    // Setup mobile-specific optimizations
    setupMobileOptimizations() {
        // Disable hover effects on mobile
        if (this.isTouchDevice) {
            document.body.classList.add('touch-device');
        }

        // Add mobile-specific classes
        document.body.classList.add('mobile-device');

        // Optimize viewport for mobile
        this.optimizeViewport();

        // Setup mobile-specific event listeners
        this.setupMobileEventListeners();
    }

    // Optimize viewport for mobile
    optimizeViewport() {
        const viewport = document.querySelector('meta[name="viewport"]');
        if (viewport) {
            viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes');
        }
    }

    // Setup mobile event listeners
    setupMobileEventListeners() {
        // Handle orientation change
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });

        // Handle resize events
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 250);
        });

        // Handle scroll events for mobile
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                this.handleScroll();
            }, 100);
        });
    }

    // Setup touch optimizations
    setupTouchOptimizations() {
        if (!this.isTouchDevice) return;

        // Prevent double-tap zoom on buttons
        const buttons = document.querySelectorAll('button, .btn, a.btn');
        buttons.forEach(button => {
            button.addEventListener('touchend', (e) => {
                e.preventDefault();
                button.click();
            });
        });

        // Add touch feedback
        this.addTouchFeedback();

        // Optimize touch scrolling
        this.optimizeTouchScroll();
    }

    // Add touch feedback to interactive elements
    addTouchFeedback() {
        const touchElements = document.querySelectorAll('.btn, .nav-link, .list-group-item, .card');
        
        touchElements.forEach(element => {
            element.addEventListener('touchstart', () => {
                element.classList.add('touch-active');
            });

            element.addEventListener('touchend', () => {
                setTimeout(() => {
                    element.classList.remove('touch-active');
                }, 150);
            });
        });
    }

    // Optimize touch scrolling
    optimizeTouchScroll() {
        const scrollableElements = document.querySelectorAll('.table-responsive, .sidebar, .modal-body');
        
        scrollableElements.forEach(element => {
            element.style.webkitOverflowScrolling = 'touch';
            element.style.overflowScrolling = 'touch';
        });
    }

    // Setup orientation handling
    setupOrientationHandling() {
        this.handleOrientationChange();
    }

    // Handle orientation change
    handleOrientationChange() {
        this.orientation = this.getOrientation();
        document.body.setAttribute('data-orientation', this.orientation);
        
        // Adjust layout based on orientation
        if (this.orientation === 'landscape') {
            this.adjustForLandscape();
        } else {
            this.adjustForPortrait();
        }
    }

    // Adjust layout for landscape orientation
    adjustForLandscape() {
        const navbar = document.querySelector('.navbar.glassmorphism');
        if (navbar) {
            navbar.style.height = '50px';
        }
        
        document.body.style.paddingTop = '50px';
        
        // Adjust table layouts for landscape
        this.adjustTablesForLandscape();
    }

    // Adjust layout for portrait orientation
    adjustForPortrait() {
        const navbar = document.querySelector('.navbar.glassmorphism');
        if (navbar) {
            navbar.style.height = '60px';
        }
        
        document.body.style.paddingTop = '60px';
        
        // Adjust table layouts for portrait
        this.adjustTablesForPortrait();
    }

    // Handle resize events
    handleResize() {
        const newIsMobile = window.innerWidth <= 768;
        
        if (newIsMobile !== this.isMobile) {
            this.isMobile = newIsMobile;
            if (this.isMobile) {
                this.setupMobileOptimizations();
            } else {
                this.removeMobileOptimizations();
            }
        }
    }

    // Handle scroll events
    handleScroll() {
        const navbar = document.querySelector('.navbar.glassmorphism');
        if (navbar) {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }
    }

    // Setup mobile navigation
    setupMobileNavigation() {
        const navbarToggler = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');
        
        if (navbarToggler && navbarCollapse) {
            // Close mobile menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!navbarToggler.contains(e.target) && !navbarCollapse.contains(e.target)) {
                    if (navbarCollapse.classList.contains('show')) {
                        navbarToggler.click();
                    }
                }
            });

            // Close mobile menu when clicking on a link
            const navLinks = navbarCollapse.querySelectorAll('.nav-link');
            navLinks.forEach(link => {
                link.addEventListener('click', () => {
                    if (navbarCollapse.classList.contains('show')) {
                        navbarToggler.click();
                    }
                });
            });
        }
    }

    // Setup mobile forms
    setupMobileForms() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            // Add mobile-specific form handling
            this.optimizeFormForMobile(form);
        });
    }

    // Optimize form for mobile
    optimizeFormForMobile(form) {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            // Set appropriate input types for mobile
            if (input.type === 'text' && input.name && input.name.includes('email')) {
                input.type = 'email';
                input.setAttribute('autocapitalize', 'off');
            }
            
            if (input.type === 'text' && input.name && input.name.includes('phone')) {
                input.type = 'tel';
            }
            
            // Add mobile-specific attributes
            input.setAttribute('autocomplete', 'on');
            input.setAttribute('autocorrect', 'on');
            
            // Handle focus events for mobile
            input.addEventListener('focus', () => {
                this.scrollToElement(input);
            });
        });
    }

    // Setup mobile tables
    setupMobileTables() {
        const tables = document.querySelectorAll('.table');
        
        tables.forEach(table => {
            this.optimizeTableForMobile(table);
        });
    }

    // Optimize table for mobile
    optimizeTableForMobile(table) {
        if (this.orientation === 'portrait') {
            this.convertTableToCards(table);
        } else {
            this.optimizeTableLayout(table);
        }
    }

    // Convert table to cards for mobile portrait
    convertTableToCards(table) {
        if (table.classList.contains('mobile-cards')) return;
        
        const wrapper = table.parentElement;
        if (!wrapper) return;
        
        const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        
        if (headers.length === 0 || rows.length === 0) return;
        
        // Create mobile cards
        const cardsContainer = document.createElement('div');
        cardsContainer.className = 'mobile-table-cards';
        
        rows.forEach((row, index) => {
            const card = document.createElement('div');
            card.className = 'card mb-2';
            
            const cardBody = document.createElement('div');
            cardBody.className = 'card-body p-3';
            
            headers.forEach((header, headerIndex) => {
                const cell = row.cells[headerIndex];
                if (cell) {
                    const rowDiv = document.createElement('div');
                    rowDiv.className = 'd-flex justify-content-between align-items-center mb-2';
                    
                    const label = document.createElement('strong');
                    label.textContent = header + ':';
                    label.className = 'text-muted me-2';
                    
                    const value = document.createElement('span');
                    value.innerHTML = cell.innerHTML;
                    
                    rowDiv.appendChild(label);
                    rowDiv.appendChild(value);
                    cardBody.appendChild(rowDiv);
                }
            });
            
            card.appendChild(cardBody);
            cardsContainer.appendChild(card);
        });
        
        // Replace table with cards on mobile
        if (window.innerWidth <= 768) {
            table.style.display = 'none';
            wrapper.appendChild(cardsContainer);
        }
        
        table.classList.add('mobile-cards');
    }

    // Optimize table layout for mobile landscape
    optimizeTableLayout(table) {
        if (table.classList.contains('mobile-cards')) {
            table.style.display = '';
            const cardsContainer = table.parentElement.querySelector('.mobile-table-cards');
            if (cardsContainer) {
                cardsContainer.remove();
            }
            table.classList.remove('mobile-cards');
        }
    }

    // Setup mobile modals
    setupMobileModals() {
        const modals = document.querySelectorAll('.modal');
        
        modals.forEach(modal => {
            this.optimizeModalForMobile(modal);
        });
    }

    // Optimize modal for mobile
    optimizeModalForMobile(modal) {
        // Adjust modal size for mobile
        if (this.isMobile) {
            modal.classList.add('modal-mobile');
        }
        
        // Handle modal backdrop for mobile
        const backdrop = modal.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.addEventListener('click', () => {
                modal.classList.remove('show');
            });
        }
    }

    // Setup mobile scroll optimizations
    setupMobileScroll() {
        // Smooth scrolling for mobile
        if (this.isTouchDevice) {
            this.enableSmoothScrolling();
        }
        
        // Optimize scroll performance
        this.optimizeScrollPerformance();
    }

    // Enable smooth scrolling for mobile
    enableSmoothScrolling() {
        const scrollElements = document.querySelectorAll('a[href^="#"]');
        
        scrollElements.forEach(link => {
            link.addEventListener('click', (e) => {
                const targetId = link.getAttribute('href');
                if (targetId === '#') return;
                
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // Optimize scroll performance
    optimizeScrollPerformance() {
        let ticking = false;
        
        const updateScroll = () => {
            // Update scroll-based animations
            ticking = false;
        };
        
        const requestTick = () => {
            if (!ticking) {
                requestAnimationFrame(updateScroll);
                ticking = true;
            }
        };
        
        window.addEventListener('scroll', requestTick, { passive: true });
    }

    // Setup mobile performance optimizations
    setupMobilePerformance() {
        // Lazy load images for mobile
        this.setupLazyLoading();
        
        // Optimize animations for mobile
        this.optimizeAnimations();
    }

    // Setup lazy loading for mobile
    setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        observer.unobserve(img);
                    }
                });
            });
            
            const lazyImages = document.querySelectorAll('img[data-src]');
            lazyImages.forEach(img => imageObserver.observe(img));
        }
    }

    // Optimize animations for mobile
    optimizeAnimations() {
        // Reduce motion for users who prefer it
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.body.classList.add('reduce-motion');
        }
        
        // Optimize CSS animations for mobile
        const animatedElements = document.querySelectorAll('.fade-in, .slide-up');
        animatedElements.forEach(element => {
            element.style.willChange = 'transform, opacity';
        });
    }

    // Setup mobile-specific features for different pages
    setupMobileSpecificFeatures() {
        // Contest page optimizations
        this.setupContestPageMobile();
        
        // Problem page optimizations
        this.setupProblemPageMobile();
        
        // Submission page optimizations
        this.setupSubmissionPageMobile();
        
        // Admin page optimizations
        this.setupAdminPageMobile();
        
        // Auth page optimizations
        this.setupAuthPageMobile();
        
        // Leaderboard optimizations
        this.setupLeaderboardMobile();
    }

    // Setup contest page mobile features
    setupContestPageMobile() {
        const contestCards = document.querySelectorAll('.contest-card');
        const contestTimers = document.querySelectorAll('.contest-timer');
        
        contestCards.forEach(card => {
            if (this.isMobile) {
                card.classList.add('mobile-optimized');
            }
        });
        
        contestTimers.forEach(timer => {
            if (this.isMobile) {
                timer.classList.add('mobile-timer');
            }
        });
    }

    // Setup problem page mobile features
    setupProblemPageMobile() {
        const problemDescription = document.querySelector('.problem-description');
        const sampleIO = document.querySelectorAll('.sample-io');
        const testCases = document.querySelectorAll('.test-case');
        
        if (problemDescription && this.isMobile) {
            problemDescription.classList.add('mobile-problem');
        }
        
        sampleIO.forEach(io => {
            if (this.isMobile) {
                io.classList.add('mobile-sample-io');
            }
        });
        
        testCases.forEach(testCase => {
            if (this.isMobile) {
                testCase.classList.add('mobile-test-case');
            }
        });
    }

    // Setup submission page mobile features
    setupSubmissionPageMobile() {
        const submissionForm = document.querySelector('.submission-form');
        const codeEditor = document.querySelector('.code-editor');
        
        if (submissionForm && this.isMobile) {
            submissionForm.classList.add('mobile-submission');
        }
        
        if (codeEditor && this.isMobile) {
            codeEditor.classList.add('mobile-code-editor');
        }
    }

    // Setup admin page mobile features
    setupAdminPageMobile() {
        const adminPanel = document.querySelector('.admin-panel');
        const adminSidebar = document.querySelector('.admin-sidebar');
        
        if (adminPanel && this.isMobile) {
            adminPanel.classList.add('mobile-admin');
        }
        
        if (adminSidebar && this.isMobile) {
            adminSidebar.classList.add('mobile-sidebar');
        }
    }

    // Setup auth page mobile features
    setupAuthPageMobile() {
        const authContainer = document.querySelector('.auth-container');
        const authForm = document.querySelector('.auth-form');
        
        if (authContainer && this.isMobile) {
            authContainer.classList.add('mobile-auth');
        }
        
        if (authForm && this.isMobile) {
            authForm.classList.add('mobile-form');
        }
    }

    // Setup leaderboard mobile features
    setupLeaderboardMobile() {
        const leaderboardTable = document.querySelector('.leaderboard-table');
        const rankBadges = document.querySelectorAll('.rank-badge');
        
        if (leaderboardTable && this.isMobile) {
            leaderboardTable.classList.add('mobile-leaderboard');
        }
        
        rankBadges.forEach(badge => {
            if (this.isMobile) {
                badge.classList.add('mobile-badge');
            }
        });
    }

    // Scroll to element with mobile optimization
    scrollToElement(element) {
        const navbarHeight = this.isMobile ? 60 : 70;
        const elementTop = element.offsetTop - navbarHeight - 20;
        
        window.scrollTo({
            top: elementTop,
            behavior: 'smooth'
        });
    }

    // Remove mobile optimizations when switching to desktop
    removeMobileOptimizations() {
        document.body.classList.remove('mobile-device', 'touch-device');
        
        // Restore table display
        const tables = document.querySelectorAll('.table.mobile-cards');
        tables.forEach(table => {
            table.style.display = '';
            table.classList.remove('mobile-cards');
        });
        
        // Remove mobile cards
        const mobileCards = document.querySelectorAll('.mobile-table-cards');
        mobileCards.forEach(cards => cards.remove());
        
        // Remove mobile-specific classes
        document.querySelectorAll('.mobile-optimized, .mobile-timer, .mobile-problem, .mobile-sample-io, .mobile-test-case, .mobile-submission, .mobile-code-editor, .mobile-admin, .mobile-sidebar, .mobile-auth, .mobile-form, .mobile-leaderboard, .mobile-badge').forEach(element => {
            element.classList.remove('mobile-optimized', 'mobile-timer', 'mobile-problem', 'mobile-sample-io', 'mobile-test-case', 'mobile-submission', 'mobile-code-editor', 'mobile-admin', 'mobile-sidebar', 'mobile-auth', 'mobile-form', 'mobile-leaderboard', 'mobile-badge');
        });
    }

    // Public method to check if device is mobile
    isMobileDevice() {
        return this.isMobile;
    }

    // Public method to check if device supports touch
    isTouchDevice() {
        return this.isTouchDevice;
    }

    // Public method to get current orientation
    getCurrentOrientation() {
        return this.orientation;
    }

    // Public method to refresh mobile optimizations
    refreshMobileOptimizations() {
        if (this.isMobile) {
            this.setupMobileSpecificFeatures();
        }
    }
}

// Initialize mobile optimizer when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.mobileOptimizer = new MobileOptimizer();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileOptimizer;
}
