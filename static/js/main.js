/**
 * 校桥 CampusBridge - 通用交互脚本
 * 处理 Flash 消息、通知轮询、表单验证、下拉菜单等
 */

(function () {
    'use strict';

    // ==================== DOM Ready ====================

    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }

    // ==================== Flash 消息自动消失 ====================

    function initFlashMessages() {
        const flashContainer = document.getElementById('flash-container');
        if (!flashContainer) return;

        const handleFlash = function () {
            const msgs = flashContainer.querySelectorAll('.flash-message');
            if (msgs.length === 0) return;

            setTimeout(function () {
                msgs.forEach(function (msg) {
                    msg.style.opacity = '0';
                    msg.style.transform = 'translateY(-12px) scale(0.95)';
                    msg.style.transition = 'all 0.35s ease-in';
                });
                setTimeout(function () {
                    msgs.forEach(function (msg) { msg.remove(); });
                }, 350);
            }, 4000);
        };

        handleFlash();
    }

    // ==================== 未读消息轮询 ====================

    function initUnreadPolling() {
        var badge = document.getElementById('unread-badge');
        if (!badge) return;

        function fetchUnreadCount() {
            fetch('/message/unread-count')
                .then(function (r) { return r.json(); })
                .then(function (d) {
                    if (!badge) return;
                    if (d.count > 0) {
                        var text = d.count > 99 ? '99+' : String(d.count);
                        if (badge.textContent !== text) {
                            badge.textContent = text;
                            badge.classList.add('badge-pop');
                            setTimeout(function () { badge.classList.remove('badge-pop'); }, 400);
                        }
                        badge.classList.remove('hidden');
                    } else {
                        badge.classList.add('hidden');
                    }
                })
                .catch(function () { /* 静默失败 */ });
        }

        fetchUnreadCount();
        setInterval(fetchUnreadCount, 60000);
    }

    // ==================== 表单提交防重复点击 ====================

    function initFormGuard() {
        document.addEventListener('submit', function (e) {
            var form = e.target.closest('form');
            if (!form) return;

            // 跳过搜索表单（method="GET"）
            if (form.method.toUpperCase() === 'GET') return;

            var submitBtn = form.querySelector('button[type="submit"]');
            if (!submitBtn) return;

            // 如果已经被标记为 loading，阻止重复提交
            if (submitBtn.classList.contains('btn-loading')) {
                e.preventDefault();
                return;
            }

            // 表单验证（required 和 pattern）
            var isValid = true;
            var inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
            inputs.forEach(function (input) {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('input-shake');
                    setTimeout(function () { input.classList.remove('input-shake'); }, 400);
                }
            });

            if (!isValid) {
                e.preventDefault();
                return;
            }

            // 添加加载状态
            submitBtn.classList.add('btn-loading');
            submitBtn.setAttribute('data-original-text', submitBtn.textContent);

            // 如果表单提交失败（如网络错误），恢复按钮状态
            setTimeout(function () {
                if (submitBtn.classList.contains('btn-loading')) {
                    submitBtn.classList.remove('btn-loading');
                }
            }, 10000); // 10秒超时保护
        });
    }

    // ==================== 搜索框增强 ====================

    function initSearchEnhance() {
        var searchInputs = document.querySelectorAll('input[name="q"]');

        searchInputs.forEach(function (input) {
            var debounceTimer;

            // 为搜索框的父级添加 wrapper 类以触发 focus-within 样式
            var wrapper = input.closest('.flex');
            if (wrapper) {
                wrapper.classList.add('search-wrapper');
            }

            // 查找相邻的搜索图标
            var icon = input.parentElement.querySelector('svg');
            if (icon) {
                icon.classList.add('search-icon');
            }

            input.addEventListener('input', function () {
                clearTimeout(debounceTimer);
                // 预留防抖钩子，保持原生行为
                debounceTimer = setTimeout(function () {
                    // 未来扩展：实时搜索建议
                }, 500);
            });

            // 为搜索框添加样式类
            input.classList.add('search-input');
        });
    }

    // ==================== 下拉菜单 ====================

    function initDropdowns() {
        // 点击下拉切换按钮
        document.addEventListener('click', function (e) {
            var toggle = e.target.closest('.dropdown-toggle');
            if (toggle) {
                e.stopPropagation();
                var menu = toggle.nextElementSibling;
                if (menu && menu.classList.contains('dropdown-menu')) {
                    var isHidden = menu.classList.contains('hidden');
                    // 关闭所有其他下拉菜单
                    document.querySelectorAll('.dropdown-menu').forEach(function (m) {
                        m.classList.add('hidden');
                    });
                    // 切换当前
                    if (isHidden) {
                        menu.classList.remove('hidden');
                    }
                }
                return;
            }

            // 点击其他区域关闭所有下拉
            document.querySelectorAll('.dropdown-menu').forEach(function (m) {
                m.classList.add('hidden');
            });
        });
    }

    // ==================== 弹窗关闭（点击遮罩 / ESC） ====================

    function initModals() {
        // 点击遮罩关闭
        document.addEventListener('click', function (e) {
            if (e.target.classList.contains('modal-overlay')) {
                var modal = e.target.closest('.modal, [id$="-modal"]');
                if (modal) {
                    modal.classList.add('hidden');
                }
            }
        });

        // ESC 关闭弹窗
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                var visibleModals = document.querySelectorAll('.modal:not(.hidden), [id$="-modal"]:not(.hidden)');
                if (visibleModals.length > 0) {
                    visibleModals[visibleModals.length - 1].classList.add('hidden');
                }
            }
        });

        // data-close-modal 按钮关闭
        document.addEventListener('click', function (e) {
            var closer = e.target.closest('[data-close-modal]');
            if (closer) {
                var modalId = closer.getAttribute('data-close-modal');
                var modal;
                if (modalId) {
                    modal = document.getElementById(modalId);
                } else {
                    modal = closer.closest('.modal, [id$="-modal"]');
                }
                if (modal) {
                    modal.classList.add('hidden');
                }
            }
        });
    }

    // ==================== 回到顶部按钮状态同步 ====================

    function initBackToTopSync() {
        // CampusAnimations 已处理，这里做额外的键盘快捷键支持
        document.addEventListener('keydown', function (e) {
            // Ctrl+Shift+↑ 或 Home 键回到顶部
            if ((e.ctrlKey && e.shiftKey && e.key === 'ArrowUp') ||
                (e.key === 'Home' && !e.target.closest('input, textarea, [contenteditable]'))) {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
    }

    // ==================== 表格行 hover 增强 ====================

    function initTableEnhance() {
        var tables = document.querySelectorAll('table');
        tables.forEach(function (table) {
            var rows = table.querySelectorAll('tbody tr');
            rows.forEach(function (row) {
                row.addEventListener('mouseenter', function () {
                    row.style.transition = 'background-color 0.2s ease, transform 0.2s ease';
                });
            });
        });
    }

    // ==================== 初始化 ====================

    ready(function () {
        initFlashMessages();
        initUnreadPolling();
        initFormGuard();
        initSearchEnhance();
        initDropdowns();
        initModals();
        initBackToTopSync();
        initTableEnhance();

        console.log('校桥 CampusBridge 已就绪 🚀');
    });

})();
