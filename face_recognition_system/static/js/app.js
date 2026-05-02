class FaceRecognitionApp {
    constructor() {
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.overlay = document.getElementById('overlay-content');
        this.status = document.getElementById('status');
        
        this.isRecognizing = false;
        this.stream = null;
        this.recognizeInterval = null;
        
        this.init();
    }
    
    init() {
        this.setupTabs();
        this.setupEventListeners();
        this.loadEmployees();
        this.loadLogs();
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
                document.getElementById(`${tabId}-tab`).classList.add('active');
                
                if (tabId === 'logs') {
                    this.loadLogs();
                }
            });
        });
    }
    
    setupEventListeners() {
        document.getElementById('startBtn').addEventListener('click', () => this.startRecognition());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopRecognition());
        
        document.getElementById('employeeForm').addEventListener('submit', (e) => this.handleEmployeeSubmit(e));
        
        document.getElementById('faceImage').addEventListener('change', (e) => this.handleImagePreview(e));
        
        document.getElementById('searchEmployee').addEventListener('input', (e) => this.filterEmployees(e.target.value));
        
        document.getElementById('refreshLogs').addEventListener('click', () => this.loadLogs());
    }
    
    async startRecognition() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 },
                audio: false
            });
            
            this.video.srcObject = this.stream;
            
            this.canvas.width = 640;
            this.canvas.height = 480;
            
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'block';
            
            this.isRecognizing = true;
            this.showStatus('正在识别中，请将面部对准摄像头...', 'info');
            
            this.recognizeInterval = setInterval(() => this.captureAndRecognize(), 1000);
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.showStatus('无法访问摄像头，请检查权限设置', 'error');
        }
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
        
        this.hideOverlay();
        this.clearStatus();
    }
    
    async captureAndRecognize() {
        if (!this.isRecognizing) return;
        
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        
        const imageData = this.canvas.toDataURL('image/jpeg', 0.8);
        
        try {
            const response = await fetch('/api/recognize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ image: imageData })
            });
            
            const result = await response.json();
            
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
        this.showOverlay(`✅ 识别成功<br>姓名: ${result.name}<br>置信度: ${(result.confidence * 100).toFixed(1)}%`);
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
            this.showOverlay(`❌ 识别失败<br>${result.message}<br><br>请重试...`);
            this.showStatus(result.message, 'error');
        } else {
            this.showStatus(result.message, 'error');
        }
    }
    
    showOverlay(message) {
        this.overlay.innerHTML = message;
        this.overlay.classList.add('visible');
    }
    
    hideOverlay() {
        this.overlay.classList.remove('visible');
    }
    
    showStatus(message, type) {
        this.status.textContent = message;
        this.status.className = `status ${type}`;
    }
    
    clearStatus() {
        this.status.textContent = '';
        this.status.className = 'status';
    }
    
    handleImagePreview(e) {
        const file = e.target.files[0];
        const preview = document.getElementById('imagePreview');
        const img = document.getElementById('previewImg');
        
        if (file) {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                img.src = e.target.result;
                preview.style.display = 'block';
            };
            
            reader.readAsDataURL(file);
        } else {
            preview.style.display = 'none';
        }
    }
    
    async handleEmployeeSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData();
        
        const employeeData = {
            employee_id: document.getElementById('employeeId').value,
            name: document.getElementById('employeeName').value,
            department: document.getElementById('department').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value
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
                        alert('员工添加成功！');
                        document.getElementById('employeeForm').reset();
                        document.getElementById('imagePreview').style.display = 'none';
                        this.loadEmployees();
                    } else {
                        await fetch(`/api/employees/${employeeData.employee_id}`, {
                            method: 'DELETE'
                        });
                        alert(`人脸上传失败: ${imageResult.message}`);
                    }
                }
            } else {
                alert(`添加失败: ${result.message}`);
            }
            
        } catch (error) {
            console.error('Error adding employee:', error);
            alert('添加员工时发生错误');
        }
    }
    
    async loadEmployees() {
        try {
            const response = await fetch('/api/employees');
            const result = await response.json();
            
            if (result.success) {
                this.renderEmployees(result.employees);
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
                    alert('删除成功！');
                    this.loadEmployees();
                } else {
                    alert(`删除失败: ${result.message}`);
                }
            } catch (error) {
                console.error('Error deleting employee:', error);
                alert('删除员工时发生错误');
            }
        }
    }
    
    async loadLogs() {
        try {
            const response = await fetch('/api/access-logs?limit=50');
            const result = await response.json();
            
            if (result.success) {
                this.renderLogs(result.logs);
            } else {
                document.getElementById('logsBody').innerHTML = '<tr><td colspan="6" class="loading">加载失败</td></tr>';
            }
        } catch (error) {
            console.error('Error loading logs:', error);
            document.getElementById('logsBody').innerHTML = '<tr><td colspan="6" class="loading">加载失败</td></tr>';
        }
    }
    
    renderLogs(logs) {
        const tbody = document.getElementById('logsBody');
        
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">暂无访问记录</td></tr>';
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
                <td>${log.error_message || '-'}</td>
            </tr>
        `).join('');
    }
}

const app = new FaceRecognitionApp();
