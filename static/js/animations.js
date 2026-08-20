/**
 * 校桥 CampusBridge - 动画增强库
 * 提供滚动触发动画、数字计数、涟漪效果、视差等交互增强
 */

const CampusAnimations = (function () {
    'use strict';

    // ==================== Intersection Observer（滚动触发动画） ====================

    /**
     * 初始化滚动触发动画
     * 为带有 data-animate 属性的元素添加进入视口时的动画
     *
     * 支持的属性：
     *   data-animate="fade-up" | "fade-in" | "slide-left" | "slide-right" | "scale-in" | "flip-in"
     *   data-animate-delay="200"        —— 延迟（ms）
     *   data-animate-duration="600"     —— 持续时间（ms）
     *   data-animate-once="true"        —— 只触发一次（默认 true）
     *   data-animate-stagger="100"      —— 子元素交错延迟（ms），配合子选择器 .stagger-item 使用
     */
    function initScrollReveal() {
        const observerOptions = {
            root: null,
            rootMargin: '0px 0px -50px 0px',
            threshold: 0.1
        };

        // 需要交错的容器单独处理
        const staggerContainers = document.querySelectorAll('[data-animate-stagger]');

        staggerContainers.forEach(container => {
            const staggerMs = parseInt(container.getAttribute('data-animate-stagger')) || 100;
            const staggerObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const items = container.querySelectorAll('.stagger-item');
                        items.forEach((item, index) => {
                            setTimeout(() => {
                                item.classList.add('animate-visible');
                            }, index * staggerMs);
                        });
                        staggerObserver.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });

            staggerObserver.observe(container);
        });

        // 普通元素逐个处理
        const animatedElements = document.querySelectorAll('[data-animate]:not([data-animate-stagger])');

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const animation = el.getAttribute('data-animate');
                    const delay = parseInt(el.getAttribute('data-animate-delay')) || 0;
                    const duration = parseInt(el.getAttribute('data-animate-duration')) || 600;
                    const once = el.getAttribute('data-animate-once') !== 'false';

                    setTimeout(() => {
                        el.classList.add('animate-visible');
                        el.style.animationDuration = duration + 'ms';
                    }, delay);

                    if (once) {
                        observer.unobserve(el);
                    }
                } else if (el.getAttribute('data-animate-once') === 'false') {
                    el.classList.remove('animate-visible');
                }
            });
        }, observerOptions);

        animatedElements.forEach(el => observer.observe(el));
    }

    // ==================== 数字滚动计数 ====================

    /**
     * 数字递增动画
     * @param {HTMLElement} el - 目标元素
     * @param {number} target - 目标数字
     * @param {number} duration - 动画时长（ms），默认 2000
     * @param {string} prefix - 前缀（如 "+"）
     * @param {string} suffix - 后缀（如 "万"）
     */
    function animateCount(el, target, duration, prefix, suffix) {
        duration = duration || 2000;
        prefix = prefix || '';
        suffix = suffix || '';
        const start = 0;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // easeOutExpo 缓动函数
            const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
            const current = Math.floor(start + (target - start) * eased);

            el.textContent = prefix + current.toLocaleString() + suffix;

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                el.textContent = prefix + target.toLocaleString() + suffix;
            }
        }

        requestAnimationFrame(update);
    }

    /**
     * 为带有 data-count 属性的元素初始化计数动画
     * 当元素进入视口时触发
     */
    function initCountUp() {
        const counters = document.querySelectorAll('[data-count]');

        if (counters.length === 0) return;

        const countObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const target = parseInt(el.getAttribute('data-count')) || 0;
                    const duration = parseInt(el.getAttribute('data-count-duration')) || 2000;
                    const prefix = el.getAttribute('data-count-prefix') || '';
                    const suffix = el.getAttribute('data-count-suffix') || '';

                    animateCount(el, target, duration, prefix, suffix);
                    countObserver.unobserve(el);
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(el => countObserver.observe(el));
    }

    // ==================== 按钮涟漪效果 ====================

    /**
     * 为按钮添加 Material Design 风格的涟漪效果
     * 使用事件委托绑定到 document
     */
    function initRipple() {
        document.addEventListener('click', function (e) {
            const rippleTarget = e.target.closest('[data-ripple]');
            if (!rippleTarget) return;

            // 防止在同一元素上重复创建涟漪容器
            if (!rippleTarget.style.position || rippleTarget.style.position === 'static') {
                rippleTarget.style.position = 'relative';
            }
            rippleTarget.style.overflow = 'hidden';

            const ripple = document.createElement('span');
            const rect = rippleTarget.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height) * 2;
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.className = 'ripple-effect';
            ripple.style.cssText = [
                'position: absolute',
                'border-radius: 50%',
                'pointer-events: none',
                'background: rgba(255, 255, 255, 0.4)',
                'width: ' + size + 'px',
                'height: ' + size + 'px',
                'left: ' + x + 'px',
                'top: ' + y + 'px',
                'transform: scale(0)',
                'opacity: 1',
                'animation: rippleExpand 0.6s ease-out forwards',
                'z-index: 0'
            ].join(';');

            rippleTarget.appendChild(ripple);

            ripple.addEventListener('animationend', function () {
                ripple.remove();
            });
        });
    }

    // ==================== 页面过渡 ====================

    function initPageTransition() {
        // 页面加载完成后淡入
        document.addEventListener('DOMContentLoaded', function () {
            const main = document.querySelector('main');
            if (main) {
                main.style.opacity = '0';
                main.style.transform = 'translateY(10px)';
                main.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out';

                requestAnimationFrame(function () {
                    main.style.opacity = '1';
                    main.style.transform = 'translateY(0)';
                });
            }
        });
    }

    // ==================== 视差效果 ====================

    function initParallax() {
        const parallaxEls = document.querySelectorAll('[data-parallax]');

        if (parallaxEls.length === 0) return;

        function updateParallax() {
            parallaxEls.forEach(el => {
                const speed = parseFloat(el.getAttribute('data-parallax')) || 0.3;
                const rect = el.getBoundingClientRect();
                const windowHeight = window.innerHeight;

                // 仅当元素在视口内时计算
                if (rect.bottom > 0 && rect.top < windowHeight) {
                    const center = rect.top + rect.height / 2;
                    const offset = (center - windowHeight / 2) * speed;
                    el.style.transform = 'translateY(' + offset + 'px)';
                }
            });
        }

        window.addEventListener('scroll', function () {
            requestAnimationFrame(updateParallax);
        }, { passive: true });

        updateParallax();
    }

    // ==================== 打字机效果 ====================

    /**
     * 打字机文字效果
     * @param {HTMLElement} el - 目标元素
     * @param {string} text - 要打出的文字
     * @param {number} speed - 每字速度（ms），默认 80
     * @param {Function} callback - 完成回调
     */
    function typeWriter(el, text, speed, callback) {
        speed = speed || 80;
        let index = 0;
        el.textContent = '';

        function type() {
            if (index < text.length) {
                el.textContent += text.charAt(index);
                index++;
                setTimeout(type, speed);
            } else if (callback) {
                callback();
            }
        }

        type();
    }

    // ==================== 导航栏滚动阴影 ====================

    function initNavShadow() {
        const nav = document.querySelector('nav');
        if (!nav) return;

        let ticking = false;

        function updateNavShadow() {
            if (window.scrollY > 10) {
                nav.classList.add('nav-scrolled');
            } else {
                nav.classList.remove('nav-scrolled');
            }
            ticking = false;
        }

        window.addEventListener('scroll', function () {
            if (!ticking) {
                requestAnimationFrame(updateNavShadow);
                ticking = true;
            }
        }, { passive: true });

        updateNavShadow();
    }

    // ==================== 回到顶部按钮 ====================

    function initBackToTop() {
        // 检查是否已存在按钮
        if (document.getElementById('back-to-top')) return;

        const btn = document.createElement('button');
        btn.id = 'back-to-top';
        btn.innerHTML = '<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/></svg>';
        btn.className = 'back-to-top-btn';
        btn.setAttribute('aria-label', '回到顶部');
        btn.setAttribute('title', '回到顶部');
        document.body.appendChild(btn);

        let ticking = false;

        function toggleVisibility() {
            if (window.scrollY > 400) {
                btn.classList.add('visible');
            } else {
                btn.classList.remove('visible');
            }
            ticking = false;
        }

        window.addEventListener('scroll', function () {
            if (!ticking) {
                requestAnimationFrame(toggleVisibility);
                ticking = true;
            }
        }, { passive: true });

        btn.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });

        toggleVisibility();
    }

    // ==================== 图片懒加载 + 模糊渐显 ====================

    function initLazyImages() {
        const lazyImages = document.querySelectorAll('img[data-src]');

        if (lazyImages.length === 0) return;

        const imgObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    const src = img.getAttribute('data-src');

                    if (src) {
                        // 创建一个新 Image 来预加载
                        const tempImg = new Image();
                        tempImg.onload = function () {
                            img.src = src;
                            img.classList.add('lazy-loaded');
                            img.removeAttribute('data-src');
                        };
                        tempImg.src = src;
                    }

                    imgObserver.unobserve(img);
                }
            });
        }, {
            rootMargin: '100px 0px',
            threshold: 0.01
        });

        lazyImages.forEach(img => imgObserver.observe(img));
    }

    // ==================== 卡片 3D 倾斜效果 ====================

    function initTilt() {
        const tiltCards = document.querySelectorAll('[data-tilt]');

        tiltCards.forEach(card => {
            const maxTilt = parseInt(card.getAttribute('data-tilt-max')) || 8;

            card.addEventListener('mousemove', function (e) {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;

                const rotateX = ((y - centerY) / centerY) * -maxTilt;
                const rotateY = ((x - centerX) / centerX) * maxTilt;

                card.style.transform = 'perspective(1000px) rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg) scale3d(1.02, 1.02, 1.02)';
                card.style.transition = 'transform 0.1s ease-out';
            });

            card.addEventListener('mouseleave', function () {
                card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
                card.style.transition = 'transform 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
            });
        });
    }

    // ==================== 导航当前页高亮 ====================

    function initActiveNav() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('nav a[href]');

        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (!href || href === '/' || href === '#') return;

            // 匹配当前路径
            if (currentPath.startsWith(href) && href !== '/') {
                link.classList.add('nav-active');
            }
        });

        // 首页特殊处理
        if (currentPath === '/') {
            const homeLink = document.querySelector('nav a[href="/"]');
            if (homeLink && !homeLink.closest('.flex.items-center.space-x-2')) {
                homeLink.classList.add('nav-active');
            }
        }
    }

    // ==================== Toast 通知 ====================

    /**
     * 显示 Toast 通知
     * @param {string} message - 消息内容
     * @param {string} type - 类型：'success' | 'error' | 'warning' | 'info'
     * @param {number} duration - 持续时间（ms），默认 3500
     */
    function showToast(message, type, duration) {
        type = type || 'info';
        duration = duration || 3500;

        const container = document.getElementById('toast-container');
        if (!container) {
            const div = document.createElement('div');
            div.id = 'toast-container';
            div.className = 'toast-container';
            document.body.appendChild(div);
        }

        const toastContainer = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = 'toast-item toast-' + type;

        const icons = {
            success: '<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
            error: '<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
            warning: '<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>',
            info: '<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
        };

        toast.innerHTML = icons[type] + '<span>' + message + '</span>';

        // 进度条
        const progressBar = document.createElement('div');
        progressBar.className = 'toast-progress';
        progressBar.style.animationDuration = duration + 'ms';
        toast.appendChild(progressBar);

        toastContainer.appendChild(toast);

        // 点击关闭
        toast.addEventListener('click', function () {
            toast.classList.add('toast-hiding');
            setTimeout(function () { toast.remove(); }, 300);
        });

        // 自动关闭
        setTimeout(function () {
            if (toast.parentNode) {
                toast.classList.add('toast-hiding');
                setTimeout(function () { toast.remove(); }, 300);
            }
        }, duration);
    }

    // ==================== 初始化 ====================

    function init() {
        initPageTransition();
        initScrollReveal();
        initCountUp();
        initRipple();
        initNavShadow();
        initBackToTop();
        initLazyImages();
        initTilt();
        initActiveNav();
        initParallax();
    }

    // ==================== 公开 API ====================

    return {
        init: init,
        animateCount: animateCount,
        showToast: showToast,
        typeWriter: typeWriter,
        // 按需初始化单项
        initScrollReveal: initScrollReveal,
        initCountUp: initCountUp,
        initRipple: initRipple,
        initTilt: initTilt,
        initBackToTop: initBackToTop,
        initLazyImages: initLazyImages
    };
})();

// 自动初始化（当 DOM 就绪时）
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
        CampusAnimations.init();
    });
} else {
    CampusAnimations.init();
}
