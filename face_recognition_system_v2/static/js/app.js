class FaceRecognitionApp {
    constructor() {
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas?.getContext('2d');
        this.overlay = document.getElementById('overlay-content');
        this.scanLine = document.getElementById('scanLine');
        
        this.isRecognizing = false;
        this.stream = null;
        this.recognizeInterval = null;
        this.frameCount = 0;
        this.lastFrameTime = 0;
        this.fps = 0;
        
        this.settings = {
            interval: 1000,
            qualityThreshold: 0.3
        };
        
        this.init();
    }
    
    init() {
        this.setupTabs();
        this.setupEventListeners();
        this.loadEmployees();
        this.loadLogs();
        this.loadStats();
        this.startHealthCheck();
    }
    
    setupTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.dataset.tab;
                
                tabBtns.forEach(b => b.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));
                
                btn.classList.add('active');
                const content = document.getElementById(`${tabId}-tab`);
                if (content) {
                    content.classList.add('active');
                }
                
                if (tabId === 'logs') {
                    this.loadLogs();
                } else if (tabId === 'stats') {
                    this.loadStats();
                }
            });
        });
    }
    
    setupEventListeners() {
        document.getElementById('startBtn')?.addEventListener('click', () => this.startContinuousRecognition());
        document.getElementById('stopBtn')?.addEventListener('click', () => this.stopRecognition());
        document.getElementById('captureBtn')?.addEventListener('click', () => this.singleCapture());
        
        document.getElementById('employeeForm')?.addEventListener('submit', (e) => this.handleEmployeeSubmit(e));
        document.getElementById('faceImage')?.addEventListener('change', (e) => this.handleImagePreview(e));
        
        document.getElementById('searchEmployee')?.addEventListener('input', (e) => this.filterEmployees(e.target.value));
        document.getElementById('searchLogs')?.addEventListener('click', () => this.loadLogsWithFilter());
        
        document.querySelectorAll('.quick-filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleQuickFilter(e.target));
        });
        
        const intervalSlider = document.getElementById('intervalSlider');
        const intervalValue = document.getElementById('intervalValue');
        if (intervalSlider && intervalValue) {
            intervalSlider.addEventListener('input', (e) => {
                this.settings.interval = parseInt(e.target.value);
                intervalValue.textContent = `${this.settings.interval}ms`;
                
                if (this.recognizeInterval) {
                    clearInterval(this.recognizeInterval);
                    this.recognizeInterval = setInterval(() => this.captureAndRecognize(), this.settings.interval);
                }
            });
        }
        
        const qualitySlider = document.getElementById('qualityThreshold');
        const qualityValue = document.getElementById('qualityThresholdValue');
        if (qualitySlider && qualityValue) {
            qualitySlider.addEventListener('input', (e) => {
                this.settings.qualityThreshold = parseInt(e.target.value) / 100;
                qualityValue.textContent = `${e.target.value}%`;
            });
        }
        
        const fileUploadWrapper = document.querySelector('.file-upload-wrapper');
        const fileInput = document.getElementById('faceImage');
        
        if (fileUploadWrapper && fileInput) {
            fileUploadWrapper.addEventListener('dragover', (e) => {
                e.preventDefault();
                fileUploadWrapper.style.borderColor = 'var(--primary-color)';
                fileUploadWrapper.style.background = 'rgba(102, 126, 234, 0.1)';
            });
            
            fileUploadWrapper.addEventListener('dragleave', () => {
                fileUploadWrapper.style.borderColor = '';
                fileUploadWrapper.style.background = '';
            });
            
            fileUploadWrapper.addEventListener('drop', (e) => {
                e.preventDefault();
                fileUploadWrapper.style.borderColor = '';
                fileUploadWrapper.style.background = '';
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    this.handleImagePreview({ target: fileInput });
                }
            });
        }
    }
    
    async startCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { 
                    width: { ideal: 640 }, 
                    height: { ideal: 480 },
                    facingMode: 'user'
                },
                audio: false
            });
            
            this.video.srcObject = this.stream;
            
            if (this.canvas) {
                this.canvas.width = 640;
                this.canvas.height = 480;
            }
            
            return true;
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.showToast('无法访问摄像头，请检查权限设置', 'error');
            this.showStatus('无法访问摄像头，请检查权限设置', 'error');
            return false;
        }
    }
    
    async startContinuousRecognition() {
        const cameraStarted = await this.startCamera();
        if (!cameraStarted) return;
        
        document.getElementById('startBtn').style.display = 'none';
        document.getElementById('stopBtn').style.display = 'block';
        
        this.isRecognizing = true;
        this.scanLine?.classList.add('active');
        
        this.showStatus('正在识别中，请将面部对准摄像头...', 'info');
        this.updateRecognitionStatus('识别中');
        
        this.recognizeInterval = setInterval(() => this.captureAndRecognize(), this.settings.interval);
    }
    
    stopRecognition() {
        this.isRecognizing = false;
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        if (this.recognizeInterval) {
            clearInterval(this.recognizeInterval);
            this.recognizeInterval = null;
        }
        
        document.getElementById('startBtn').style.display = 'block';
        document.getElementById('stopBtn').style.display = 'none';
        
        this.scanLine?.classList.remove('active');
        this.hideOverlay();
        this.clearStatus();
        this.updateRecognitionStatus('待机');
    }
    
    async singleCapture() {
        if (!this.stream) {
            const cameraStarted = await this.startCamera();
            if (!cameraStarted) return;
        }
        
        await this.captureAndRecognize();
    }
    
    async captureAndRecognize() {
        if (!this.isRecognizing && !this.stream) return;
        
        this.updateFPS();
        
        if (!this.ctx || !this.video) return;
        
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        
        const imageData = this.canvas.toDataURL('image/jpeg', 0.7);
        
        try {
            const response = await fetch('/api/recognize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ image: imageData })
            });
            
            const result = await response.json();
            
            if (result.quality_score !== undefined) {
                this.updateQualityDisplay(result.quality_score);
            }
            
            if (result.success) {
                this.handleRecognitionSuccess(result);
            } else {
                this.handleRecognitionFailure(result);
            }
            
        } catch (error) {
            console.error('Recognition error:', error);
            this.showStatus('网络错误，请检查连接', 'error');
        }
    }
    
    handleRecognitionSuccess(result) {
        const message = `✅ 识别成功<br>姓名: ${result.name}<br>置信度: ${(result.confidence * 100).toFixed(1)}%`;
        this.showOverlay(message, 'success');
        
        this.showStatus(`欢迎，${result.name}！置信度: ${(result.confidence * 100).toFixed(1)}%`, 'success');
        
        setTimeout(() => {
            if (this.isRecognizing) {
                this.hideOverlay();
                this.clearStatus();
            }
        }, 3000);
    }
    
    handleRecognitionFailure(result) {
        if (result.retry) {
            let message = `❌ 识别失败<br>${result.message}`;
            
            if (result.quality_score !== undefined && result.quality_score < this.settings.qualityThreshold) {
                message += `<br><small>人脸质量: ${(result.quality_score * 100).toFixed(0)}% (需要 ${this.settings.qualityThreshold * 100}% 以上)</small>`;
            }
            
            this.showOverlay(message, 'error');
            this.showStatus(result.message, 'error');
        } else {
            this.showStatus(result.message, 'error');
        }
    }
    
    updateFPS() {
        const now = performance.now();
        if (this.lastFrameTime) {
            const delta = now - this.lastFrameTime;
            this.fps = Math.round(1000 / delta);
            
            const fpsDisplay = document.getElementById('fpsDisplay');
            if (fpsDisplay) {
                fpsDisplay.textContent = this.fps;
                fpsDisplay.style.color = this.fps < 20 ? 'var(--danger-color)' : 'var(--success-color)';
            }
        }
        this.lastFrameTime = now;
    }
    
    updateQualityDisplay(quality) {
        const qualityDisplay = document.getElementById('qualityDisplay');
        if (qualityDisplay) {
            const percentage = (quality * 100).toFixed(0);
            qualityDisplay.textContent = `${percentage}%`;
            
            if (quality < this.settings.qualityThreshold) {
                qualityDisplay.style.color = 'var(--danger-color)';
            } else if (quality < 0.6) {
                qualityDisplay.style.color = 'var(--warning-color)';
            } else {
                qualityDisplay.style.color = 'var(--success-color)';
            }
        }
    }
    
    updateRecognitionStatus(status) {
        const statusDisplay = document.getElementById('recognitionStatus');
        if (statusDisplay) {
            statusDisplay.textContent = status;
        }
    }
    
    showOverlay(message, type = '') {
        if (this.overlay) {
            this.overlay.innerHTML = message;
            this.overlay.className = 'overlay-content visible ' + type;
        }
    }
    
    hideOverlay() {
        if (this.overlay) {
            this.overlay.className = 'overlay-content';
        }
    }
    
    showStatus(message, type) {
        const statusPanel = document.getElementById('statusMessage');
        if (statusPanel) {
            statusPanel.textContent = message;
            statusPanel.className = `status-message visible ${type}`;
        }
    }
    
    clearStatus() {
        const statusPanel = document.getElementById('statusMessage');
        if (statusPanel) {
            statusPanel.className = 'status-message';
        }
    }
    
    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        if (toast) {
            toast.textContent = message;
            toast.className = `toast visible ${type}`;
            
            setTimeout(() => {
                toast.className = 'toast';
            }, 3000);
        }
    }
    
    handleImagePreview(e) {
        const file = e.target.files[0];
        const preview = document.getElementById('imagePreview');
        const img = document.getElementById('previewImg');
        const qualityInfo = document.getElementById('previewQuality');
        
        if (file) {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                img.src = e.target.result;
                preview.style.display = 'block';
                
                if (qualityInfo) {
                    qualityInfo.textContent = '质量: 检测中...';
                }
            };
            
            reader.readAsDataURL(file);
        } else {
            preview.style.display = 'none';
        }
    }
    
    async handleEmployeeSubmit(e) {
        e.preventDefault();
        
        const employeeData = {
            employee_id: document.getElementById('employeeId').value,
            name: document.getElementById('employeeName').value,
            department: document.getElementById('department').value,
            email: document.getElementById('email').value || null,
            phone: document.getElementById('phone').value || null
        };
        
        try {
            const response = await fetch('/api/employees', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(employeeData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                const imageFile = document.getElementById('faceImage').files[0];
                if (imageFile) {
                    const imageFormData = new FormData();
                    imageFormData.append('file', imageFile);
                    
                    const imageResponse = await fetch(`/api/employees/${employeeData.employee_id}/face`, {
                        method: 'POST',
                        body: imageFormData
                    });
                    
                    const imageResult = await imageResponse.json();
                    
                    if (imageResult.success) {
                        this.showToast('员工添加成功！', 'success');
                        document.getElementById('employeeForm').reset();
                        document.getElementById('imagePreview').style.display = 'none';
                        this.loadEmployees();
                    } else {
                        await fetch(`/api/employees/${employeeData.employee_id}`, {
                            method: 'DELETE'
                        });
                        this.showToast(`人脸上传失败: ${imageResult.message}`, 'error');
                    }
                }
            } else {
                this.showToast(`添加失败: ${result.message}`, 'error');
            }
            
        } catch (error) {
            console.error('Error adding employee:', error);
            this.showToast('添加员工时发生错误', 'error');
        }
    }
    
    async loadEmployees() {
        try {
            const response = await fetch('/api/employees');
            const result = await response.json();
            
            if (result.success) {
                this.renderEmployees(result.employees);
                
                const totalEmployees = document.getElementById('totalEmployees');
                if (totalEmployees) {
                    totalEmployees.textContent = result.employees.length;
                }
            } else {
                document.getElementById('employeeList').innerHTML = '<p class="loading">加载失败</p>';
            }
        } catch (error) {
            console.error('Error loading employees:', error);
            document.getElementById('employeeList').innerHTML = '<p class="loading">加载失败</p>';
        }
    }
    
    renderEmployees(employees) {
        const list = document.getElementById('employeeList');
        
        if (employees.length === 0) {
            list.innerHTML = '<p class="loading">暂无员工数据</p>';
            return;
        }
        
        list.innerHTML = employees.map(emp => `
            <div class="employee-card fadeIn" data-employee-id="${emp.employee_id}" data-name="${emp.name}" data-department="${emp.department}">
                <div class="employee-info">
                    <h4>${emp.name}</h4>
                    <p>编号: ${emp.employee_id} | 部门: ${emp.department}</p>
                    ${emp.email ? `<p>邮箱: ${emp.email}</p>` : ''}
                    ${emp.phone ? `<p>电话: ${emp.phone}</p>` : ''}
                </div>
                <div class="employee-actions">
                    <button class="btn btn-danger" onclick="app.deleteEmployee('${emp.employee_id}', '${emp.name}')">删除</button>
                </div>
            </div>
        `).join('');
    }
    
    filterEmployees(query) {
        const cards = document.querySelectorAll('.employee-card');
        const searchTerm = query.toLowerCase();
        
        cards.forEach(card => {
            const id = card.dataset.employeeId.toLowerCase();
            const name = card.dataset.name.toLowerCase();
            const department = card.dataset.department.toLowerCase();
            
            if (id.includes(searchTerm) || name.includes(searchTerm) || department.includes(searchTerm)) {
                card.style.display = 'flex';
            } else {
                card.style.display = 'none';
            }
        });
    }
    
    async deleteEmployee(employeeId, name) {
        if (confirm(`确定要删除员工 ${name} 吗？`)) {
            try {
                const response = await fetch(`/api/employees/${employeeId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.showToast('删除成功！', 'success');
                    this.loadEmployees();
                } else {
                    this.showToast(`删除失败: ${result.message}`, 'error');
                }
            } catch (error) {
                console.error('Error deleting employee:', error);
                this.showToast('删除员工时发生错误', 'error');
            }
        }
    }
    
    refreshEmployees() {
        this.loadEmployees();
    }
    
    async loadLogs() {
        await this.loadLogsWithFilter();
    }
    
    async loadLogsWithFilter() {
        try {
            const startTime = document.getElementById('startTime').value;
            const endTime = document.getElementById('endTime').value;
            
            let url = '/api/access-logs?limit=1000';
            
            if (startTime) {
                url += `&start_time=${encodeURIComponent(startTime)}`;
            }
            
            if (endTime) {
                url += `&end_time=${encodeURIComponent(endTime)}`;
            }
            
            const response = await fetch(url);
            const result = await response.json();
            
            if (result.success) {
                this.renderLogs(result.logs);
                this.updateLogsSummary(result.logs);
            } else {
                document.getElementById('logsBody').innerHTML = '<tr><td colspan="7" class="loading">加载失败</td></tr>';
            }
        } catch (error) {
            console.error('Error loading logs:', error);
            document.getElementById('logsBody').innerHTML = '<tr><td colspan="7" class="loading">加载失败</td></tr>';
        }
    }
    
    updateLogsSummary(logs) {
        const total = logs.length;
        const success = logs.filter(l => l.status === 'success').length;
        const failed = total - success;
        const rate = total > 0 ? Math.round((success / total) * 100) : 0;
        
        const totalAccess = document.getElementById('totalAccess');
        const successAccess = document.getElementById('successAccess');
        const failedAccess = document.getElementById('failedAccess');
        const successRate = document.getElementById('successRate');
        
        if (totalAccess) totalAccess.textContent = total;
        if (successAccess) successAccess.textContent = success;
        if (failedAccess) failedAccess.textContent = failed;
        if (successRate) successRate.textContent = `${rate}%`;
    }
    
    handleQuickFilter(button) {
        document.querySelectorAll('.quick-filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        button.classList.add('active');
        
        const range = button.dataset.range;
        const now = new Date();
        let startTime = '';
        let endTime = '';
        
        switch (range) {
            case 'today':
                const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                startTime = this.formatDateTimeLocal(todayStart);
                endTime = this.formatDateTimeLocal(now);
                break;
                
            case 'yesterday':
                const yesterday = new Date(now);
                yesterday.setDate(yesterday.getDate() - 1);
                const yesterdayStart = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate());
                const yesterdayEnd = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate(), 23, 59, 59);
                startTime = this.formatDateTimeLocal(yesterdayStart);
                endTime = this.formatDateTimeLocal(yesterdayEnd);
                break;
                
            case '7days':
                const weekAgo = new Date(now);
                weekAgo.setDate(weekAgo.getDate() - 7);
                startTime = this.formatDateTimeLocal(weekAgo);
                endTime = this.formatDateTimeLocal(now);
                break;
                
            case '30days':
                const monthAgo = new Date(now);
                monthAgo.setDate(monthAgo.getDate() - 30);
                startTime = this.formatDateTimeLocal(monthAgo);
                endTime = this.formatDateTimeLocal(now);
                break;
                
            case 'all':
            default:
                startTime = '';
                endTime = '';
                break;
        }
        
        document.getElementById('startTime').value = startTime;
        document.getElementById('endTime').value = endTime;
        
        this.loadLogsWithFilter();
    }
    
    formatDateTimeLocal(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }
    
    renderLogs(logs) {
        const tbody = document.getElementById('logsBody');
        
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading">暂无访问记录</td></tr>';
            return;
        }
        
        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>${log.access_time}</td>
                <td>${log.employee_id || '-'}</td>
                <td>${log.name || '-'}</td>
                <td>
                    <span class="status-badge ${log.status}">${log.status === 'success' ? '成功' : '失败'}</span>
                </td>
                <td>${log.confidence ? (log.confidence * 100).toFixed(1) + '%' : '-'}</td>
                <td>${log.processing_time ? (log.processing_time * 1000).toFixed(1) + 'ms' : '-'}</td>
                <td>${log.error_message || '-'}</td>
            </tr>
        `).join('');
    }
    
    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const result = await response.json();
            
            if (result.success) {
                this.updateStatsDisplay(result);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }
    
    updateStatsDisplay(result) {
        const db = result.database || {};
        const recognizer = result.recognizer || {};
        const performance = result.performance || {};
        const circuits = result.circuit_breakers || {};
        
        const statTotalEmployees = document.getElementById('statTotalEmployees');
        const statTotalFaces = document.getElementById('statTotalFaces');
        const statTodayTotal = document.getElementById('statTodayTotal');
        const statTodaySuccess = document.getElementById('statTodaySuccess');
        const statTodayRate = document.getElementById('statTodayRate');
        
        if (statTotalEmployees) statTotalEmployees.textContent = db.total_employees || 0;
        if (statTotalFaces) statTotalFaces.textContent = db.total_faces || 0;
        if (statTodayTotal) statTodayTotal.textContent = db.today_access_count || 0;
        if (statTodaySuccess) statTodaySuccess.textContent = db.today_success_count || 0;
        if (statTodayRate) statTodayRate.textContent = `${db.today_success_rate || 0}%`;
        
        const recognizeStats = performance.recognize || {};
        const statAvgTime = document.getElementById('statAvgTime');
        const statP95Time = document.getElementById('statP95Time');
        const statTotalRecognitions = document.getElementById('statTotalRecognitions');
        
        if (statAvgTime) statAvgTime.textContent = `${(recognizeStats.mean || 0) * 1000}ms`;
        if (statP95Time) statP95Time.textContent = `${(recognizeStats.p95 || 0) * 1000}ms`;
        if (statTotalRecognitions) statTotalRecognitions.textContent = recognizeStats.count || 0;
        
        const recognitionCircuit = circuits.recognition || {};
        const statCircuitStatus = document.getElementById('statCircuitStatus');
        
        if (statCircuitStatus) {
            const state = recognitionCircuit.state || 'closed';
            statCircuitStatus.textContent = state === 'closed' ? '关闭' : (state === 'open' ? '开启' : '半开');
            statCircuitStatus.className = `stat-status ${state === 'closed' ? 'healthy' : (state === 'open' ? 'danger' : 'warning')}`;
        }
    }
    
    refreshStats() {
        this.loadStats();
    }
    
    async clearCaches() {
        if (confirm('确定要清除系统缓存吗？')) {
            try {
                this.showToast('缓存清除功能需要后端支持', 'info');
            } catch (error) {
                console.error('Error clearing caches:', error);
                this.showToast('清除缓存失败', 'error');
            }
        }
    }
    
    async startHealthCheck() {
        const checkHealth = async () => {
            try {
                const response = await fetch('/api/health');
                const result = await response.json();
                
                this.updateSystemStatus(result.healthy);
            } catch (error) {
                console.error('Health check error:', error);
                this.updateSystemStatus(false);
            }
        };
        
        await checkHealth();
        setInterval(checkHealth, 30000);
    }
    
    updateSystemStatus(healthy) {
        const statusIndicator = document.querySelector('.status-indicator');
        const statusText = document.querySelector('.status-text');
        
        if (statusIndicator) {
            statusIndicator.className = `status-indicator ${healthy ? 'healthy' : 'danger'}`;
        }
        
        if (statusText) {
            statusText.textContent = healthy ? '系统正常' : '系统异常';
        }
    }
}

const app = new FaceRecognitionApp();
