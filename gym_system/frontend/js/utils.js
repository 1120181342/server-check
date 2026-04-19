const Utils = {
    BASE_URL: 'http://localhost:5000/api',
    
    setStorage(key, value) {
        if (typeof value === 'object') {
            localStorage.setItem(key, JSON.stringify(value));
        } else {
            localStorage.setItem(key, value);
        }
    },
    
    getStorage(key) {
        const value = localStorage.getItem(key);
        try {
            return JSON.parse(value);
        } catch (e) {
            return value;
        }
    },
    
    removeStorage(key) {
        localStorage.removeItem(key);
    },
    
    clearStorage() {
        localStorage.clear();
    },
    
    showToast(message, type = 'info', duration = 3000) {
        const toast = document.getElementById('toast');
        if (!toast) {
            const toastDiv = document.createElement('div');
            toastDiv.id = 'toast';
            toastDiv.className = 'toast';
            document.body.appendChild(toastDiv);
        }
        
        const toastEl = document.getElementById('toast');
        toastEl.textContent = message;
        toastEl.className = `toast toast-${type} show`;
        
        setTimeout(() => {
            toastEl.classList.remove('show');
        }, duration);
    },
    
    formatDate(date, format = 'YYYY-MM-DD') {
        if (!date) return '';
        
        let d;
        if (typeof date === 'string') {
            d = new Date(date.replace(/-/g, '/'));
        } else {
            d = new Date(date);
        }
        
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    },
    
    formatDateTime(date) {
        return this.formatDate(date, 'YYYY-MM-DD HH:mm:ss');
    },
    
    getToday() {
        const now = new Date();
        return this.formatDate(now);
    },
    
    getWeekDays() {
        const days = [];
        const now = new Date();
        for (let i = 0; i < 7; i++) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            days.push(this.formatDate(date));
        }
        return days.reverse();
    },
    
    debounce(fn, delay = 300) {
        let timer = null;
        return function(...args) {
            if (timer) clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    },
    
    throttle(fn, delay = 300) {
        let lastTime = 0;
        return function(...args) {
            const now = Date.now();
            if (now - lastTime >= delay) {
                lastTime = now;
                fn.apply(this, args);
            }
        };
    },
    
    checkAuth() {
        const token = this.getStorage('access_token');
        if (!token) {
            window.location.href = 'index.html';
            return false;
        }
        return true;
    },
    
    logout() {
        this.clearStorage();
        window.location.href = 'index.html';
    },
    
    renderPagination(containerId, currentPage, totalPages, totalItems, onPageChange) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }
        
        let html = '<div class="pagination">';
        
        html += `<button class="btn btn-sm ${currentPage === 1 ? 'disabled' : ''}" 
                    onclick="(${onPageChange})(${currentPage - 1})" 
                    ${currentPage === 1 ? 'disabled' : ''}>上一页</button>`;
        
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        
        if (startPage > 1) {
            html += `<button class="btn btn-sm" onclick="(${onPageChange})(1)">1</button>`;
            if (startPage > 2) {
                html += '<span class="page-ellipsis">...</span>';
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="btn btn-sm ${i === currentPage ? 'btn-active' : ''}" 
                        onclick="(${onPageChange})(${i})">${i}</button>`;
        }
        
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                html += '<span class="page-ellipsis">...</span>';
            }
            html += `<button class="btn btn-sm" onclick="(${onPageChange})(${totalPages})">${totalPages}</button>`;
        }
        
        html += `<button class="btn btn-sm ${currentPage === totalPages ? 'disabled' : ''}" 
                    onclick="(${onPageChange})(${currentPage + 1})" 
                    ${currentPage === totalPages ? 'disabled' : ''}>下一页</button>`;
        
        html += `<span class="page-info">共 ${totalItems} 条，第 ${currentPage}/${totalPages} 页</span>`;
        html += '</div>';
        
        container.innerHTML = html;
    }
};
