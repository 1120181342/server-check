/**
 * 简单文档编辑器 - 前端JavaScript
 */

class DocEditor {
    constructor() {
        this.baseUrl = '/api';
        this.currentDocId = null;
        this.currentFilename = 'untitled.txt';
        this.accessToken = null;
        this.user = null;
        this.init();
    }
    
    init() {
        this.checkAuth();
        this.bindEvents();
    }
    
    async checkAuth() {
        const token = localStorage.getItem('access_token');
        if (token) {
            this.accessToken = token;
            try {
                await this.getUserProfile();
                this.showEditorPage();
            } catch (error) {
                this.showAuthPage();
            }
        } else {
            this.showAuthPage();
        }
    }
    
    showAuthPage() {
        document.getElementById('auth-page').classList.add('active');
        document.getElementById('editor-page').classList.remove('active');
    }
    
    showEditorPage() {
        document.getElementById('auth-page').classList.remove('active');
        document.getElementById('editor-page').classList.add('active');
        if (this.user) {
            document.getElementById('user-name').textContent = this.user.username;
        }
    }
    
    bindEvents() {
        // 认证标签切换
        document.getElementById('login-tab').addEventListener('click', () => this.switchTab('login'));
        document.getElementById('register-tab').addEventListener('click', () => this.switchTab('register'));
        
        // 登录表单
        document.getElementById('login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.login();
        });
        
        // 注册表单
        document.getElementById('register-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.register();
        });
        
        // 工具栏按钮
        document.getElementById('btn-new').addEventListener('click', () => this.newFile());
        document.getElementById('btn-open').addEventListener('click', () => this.openFileList());
        document.getElementById('btn-save').addEventListener('click', () => this.saveFile());
        document.getElementById('btn-saveas').addEventListener('click', () => this.saveAsFile());
        document.getElementById('btn-logout').addEventListener('click', () => this.logout());
        
        // 侧边栏
        document.getElementById('btn-close-sidebar').addEventListener('click', () => this.closeFileSidebar());
        
        // 模态框
        document.getElementById('btn-close-modal').addEventListener('click', () => this.closeModal());
        document.getElementById('btn-modal-cancel').addEventListener('click', () => this.closeModal());
        document.getElementById('btn-modal-confirm').addEventListener('click', () => this.handleModalConfirm());
        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target.id === 'modal-overlay') {
                this.closeModal();
            }
        });
        
        // 编辑器内容变化
        document.getElementById('editor').addEventListener('input', () => this.onEditorChange());
    }
    
    switchTab(tab) {
        const loginTab = document.getElementById('login-tab');
        const registerTab = document.getElementById('register-tab');
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        
        if (tab === 'login') {
            loginTab.classList.add('active');
            registerTab.classList.remove('active');
            loginForm.classList.add('active');
            registerForm.classList.remove('active');
        } else {
            loginTab.classList.remove('active');
            registerTab.classList.add('active');
            loginForm.classList.remove('active');
            registerForm.classList.add('active');
        }
    }
    
    async request(url, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (this.accessToken) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }
        
        const response = await fetch(`${this.baseUrl}${url}`, {
            ...options,
            headers
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || '请求失败');
        }
        
        return data;
    }
    
    async login() {
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        
        try {
            const response = await this.request('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });
            
            this.accessToken = response.data.access_token;
            this.user = response.data.user;
            
            localStorage.setItem('access_token', this.accessToken);
            localStorage.setItem('refresh_token', response.data.refresh_token);
            
            this.showMessage('登录成功！', 'success');
            setTimeout(() => this.showEditorPage(), 500);
            
        } catch (error) {
            this.showMessage(error.message, 'error');
        }
    }
    
    async register() {
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const realName = document.getElementById('register-realname').value;
        const password = document.getElementById('register-password').value;
        
        try {
            const response = await this.request('/auth/register', {
                method: 'POST',
                body: JSON.stringify({ 
                    username, 
                    email: email || null, 
                    real_name: realName || null, 
                    password 
                })
            });
            
            this.showMessage('注册成功！请登录', 'success');
            setTimeout(() => this.switchTab('login'), 500);
            
        } catch (error) {
            this.showMessage(error.message, 'error');
        }
    }
    
    async getUserProfile() {
        const response = await this.request('/auth/profile');
        this.user = response.data;
    }
    
    async logout() {
        try {
            await this.request('/auth/logout', { method: 'POST' });
        } catch (error) {
            // 忽略登出API错误
        }
        
        this.accessToken = null;
        this.user = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        this.showAuthPage();
        this.resetEditor();
    }
    
    showMessage(text, type) {
        const messageEl = document.getElementById('auth-message');
        messageEl.textContent = text;
        messageEl.className = `message ${type}`;
        
        setTimeout(() => {
            messageEl.textContent = '';
            messageEl.className = 'message';
        }, 3000);
    }
    
    setStatus(message) {
        document.getElementById('status-message').textContent = message;
    }
    
    updateFileSize() {
        const content = document.getElementById('editor').value;
        const size = new Blob([content]).size;
        let sizeText;
        
        if (size < 1024) {
            sizeText = `${size} 字节`;
        } else if (size < 1024 * 1024) {
            sizeText = `${(size / 1024).toFixed(2)} KB`;
        } else {
            sizeText = `${(size / (1024 * 1024)).toFixed(2)} MB`;
        }
        
        document.getElementById('file-size').textContent = sizeText;
    }
    
    onEditorChange() {
        this.updateFileSize();
        this.setStatus('已修改 - 未保存');
    }
    
    resetEditor() {
        document.getElementById('editor').value = '';
        this.currentDocId = null;
        this.currentFilename = 'untitled.txt';
        document.getElementById('current-filename').textContent = this.currentFilename;
        this.updateFileSize();
        this.setStatus('就绪');
    }
    
    // 文件操作
    newFile() {
        this.showModal('新建文件', '文件名（.txt）', 'untitled.txt', 'new');
    }
    
    async openFileList() {
        try {
            const response = await this.request('/files/');
            this.renderFileList(response.data);
            document.getElementById('file-sidebar').classList.remove('hidden');
        } catch (error) {
            this.setStatus(`获取文件列表失败: ${error.message}`);
        }
    }
    
    renderFileList(files) {
        const fileListEl = document.getElementById('file-list');
        
        if (files.length === 0) {
            fileListEl.innerHTML = '<div class="file-item">暂无文件</div>';
            return;
        }
        
        fileListEl.innerHTML = files.map(file => `
            <div class="file-item" data-id="${file.id}" data-filename="${file.filename}">
                <div class="file-name">${file.filename}</div>
                <div class="file-info">
                    ${this.formatFileSize(file.file_size)} · 
                    ${this.formatDate(file.updated_at)}
                </div>
            </div>
        `).join('');
        
        // 绑定点击事件
        fileListEl.querySelectorAll('.file-item').forEach(item => {
            item.addEventListener('click', () => {
                const docId = parseInt(item.dataset.id);
                const filename = item.dataset.filename;
                this.openFile(docId, filename);
            });
        });
    }
    
    async openFile(docId, filename) {
        try {
            const response = await this.request(`/files/${docId}`);
            
            this.currentDocId = docId;
            this.currentFilename = filename;
            document.getElementById('editor').value = response.data.content;
            document.getElementById('current-filename').textContent = filename;
            this.updateFileSize();
            this.setStatus('已打开');
            this.closeFileSidebar();
            
        } catch (error) {
            this.setStatus(`打开文件失败: ${error.message}`);
        }
    }
    
    closeFileSidebar() {
        document.getElementById('file-sidebar').classList.add('hidden');
    }
    
    async saveFile() {
        if (!this.currentDocId) {
            // 如果没有当前文档，提示新建或另存为
            this.saveAsFile();
            return;
        }
        
        const content = document.getElementById('editor').value;
        
        try {
            await this.request(`/files/${this.currentDocId}`, {
                method: 'PUT',
                body: JSON.stringify({ content })
            });
            
            this.updateFileSize();
            this.setStatus('已保存');
            
        } catch (error) {
            this.setStatus(`保存失败: ${error.message}`);
        }
    }
    
    saveAsFile() {
        const defaultName = this.currentFilename.replace('.txt', '') + '_副本.txt';
        this.showModal('另存为', '新文件名（.txt）', defaultName, 'saveas');
    }
    
    // 模态框相关
    showModal(title, label, defaultValue, action) {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-label').textContent = label;
        document.getElementById('modal-input').value = defaultValue;
        document.getElementById('modal-overlay').dataset.action = action;
        document.getElementById('modal-overlay').classList.remove('hidden');
        document.getElementById('modal-input').focus();
        document.getElementById('modal-input').select();
    }
    
    closeModal() {
        document.getElementById('modal-overlay').classList.add('hidden');
    }
    
    async handleModalConfirm() {
        const action = document.getElementById('modal-overlay').dataset.action;
        const inputValue = document.getElementById('modal-input').value.trim();
        
        if (!inputValue) {
            this.setStatus('文件名不能为空');
            return;
        }
        
        // 确保文件名以.txt结尾
        const filename = inputValue.endsWith('.txt') ? inputValue : inputValue + '.txt';
        
        this.closeModal();
        
        try {
            if (action === 'new') {
                await this.createNewFile(filename);
            } else if (action === 'saveas') {
                await this.saveAsExistingFile(filename);
            }
        } catch (error) {
            this.setStatus(`操作失败: ${error.message}`);
        }
    }
    
    async createNewFile(filename) {
        const response = await this.request('/files/new', {
            method: 'POST',
            body: JSON.stringify({ filename })
        });
        
        this.currentDocId = response.data.id;
        this.currentFilename = filename;
        document.getElementById('editor').value = '';
        document.getElementById('current-filename').textContent = filename;
        this.updateFileSize();
        this.setStatus('已创建新文件');
    }
    
    async saveAsExistingFile(filename) {
        // 先保存当前内容
        if (this.currentDocId) {
            const content = document.getElementById('editor').value;
            await this.request(`/files/${this.currentDocId}`, {
                method: 'PUT',
                body: JSON.stringify({ content })
            });
        }
        
        // 然后另存为
        const response = await this.request(`/files/${this.currentDocId || 0}/save-as`, {
            method: 'POST',
            body: JSON.stringify({ filename })
        });
        
        this.currentDocId = response.data.id;
        this.currentFilename = filename;
        document.getElementById('current-filename').textContent = filename;
        this.setStatus('已另存为');
    }
    
    // 工具函数
    formatFileSize(bytes) {
        if (bytes < 1024) return `${bytes} 字节`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    }
    
    formatDate(isoString) {
        const date = new Date(isoString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new DocEditor();
});
