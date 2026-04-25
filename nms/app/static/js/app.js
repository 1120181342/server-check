/**
 * 云资源池综合化网管系统 - 前端应用
 */

const NMS = {
    API_BASE: '/api',
    token: null,
    currentUser: null,
    charts: {},
    
    init: function() {
        this.checkAuth();
        this.bindEvents();
    },
    
    checkAuth: function() {
        const token = localStorage.getItem('nms_token');
        const user = localStorage.getItem('nms_user');
        
        if (token && user) {
            this.token = token;
            this.currentUser = JSON.parse(user);
            this.showMainApp();
            this.loadDashboard();
        } else {
            this.showLogin();
        }
    },
    
    showLogin: function() {
        document.getElementById('login-page').style.display = 'flex';
        document.getElementById('main-app').style.display = 'none';
    },
    
    showMainApp: function() {
        document.getElementById('login-page').style.display = 'none';
        document.getElementById('main-app').style.display = 'flex';
        
        if (this.currentUser) {
            document.getElementById('current-user').textContent = this.currentUser.real_name || this.currentUser.username;
            
            const roleNames = {
                'system_admin': '系统管理员',
                'device_admin': '设备管理员',
                'device_monitor': '设备监控员'
            };
            document.getElementById('current-role').textContent = roleNames[this.currentUser.role?.name] || '普通用户';
            
            if (this.currentUser.role?.name === 'system_admin') {
                document.getElementById('users-nav-item').style.display = 'block';
            }
            
            if (this.currentUser.role?.name === 'device_admin') {
                document.getElementById('add-device-btn').style.display = 'inline-block';
            }
        }
    },
    
    bindEvents: function() {
        const self = this;
        
        document.getElementById('login-form').addEventListener('submit', function(e) {
            e.preventDefault();
            self.login();
        });
        
        document.getElementById('logout-btn').addEventListener('click', function() {
            self.logout();
        });
        
        document.querySelectorAll('.nav-item').forEach(function(item) {
            item.addEventListener('click', function() {
                const page = this.dataset.page;
                self.switchPage(page);
            });
        });
        
        document.querySelectorAll('.modal-close').forEach(function(btn) {
            btn.addEventListener('click', function() {
                self.closeAllModals();
            });
        });
        
        document.getElementById('filter-alarms-btn').addEventListener('click', function() {
            self.loadAlarms();
        });
        
        let searchTimeout;
        document.getElementById('device-search').addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                self.loadDevices();
            }, 300);
        });
    },
    
    login: async function() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('login-error');
        
        try {
            const response = await fetch(this.API_BASE + '/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.token = result.data.access_token;
                this.currentUser = result.data.user;
                
                localStorage.setItem('nms_token', this.token);
                localStorage.setItem('nms_user', JSON.stringify(this.currentUser));
                
                errorDiv.style.display = 'none';
                this.showMainApp();
                this.loadDashboard();
            } else {
                errorDiv.textContent = result.message || '登录失败';
                errorDiv.style.display = 'block';
            }
        } catch (error) {
            errorDiv.textContent = '网络错误，请重试';
            errorDiv.style.display = 'block';
            console.error('Login error:', error);
        }
    },
    
    logout: function() {
        this.token = null;
        this.currentUser = null;
        localStorage.removeItem('nms_token');
        localStorage.removeItem('nms_user');
        this.showLogin();
    },
    
    switchPage: function(page) {
        document.querySelectorAll('.nav-item').forEach(function(item) {
            item.classList.remove('active');
            if (item.dataset.page === page) {
                item.classList.add('active');
            }
        });
        
        document.querySelectorAll('.page-content').forEach(function(p) {
            p.style.display = 'none';
        });
        document.getElementById(page + '-page').style.display = 'block';
        
        const titles = {
            'dashboard': '仪表板',
            'devices': '设备管理',
            'alarms': '告警管理',
            'users': '用户管理'
        };
        document.getElementById('page-title').textContent = titles[page];
        
        if (page === 'dashboard') {
            this.loadDashboard();
        } else if (page === 'devices') {
            this.loadDevices();
        } else if (page === 'alarms') {
            this.loadAlarms();
        } else if (page === 'users') {
            this.loadUsers();
        }
    },
    
    apiRequest: async function(endpoint, options = {}) {
        const url = this.API_BASE + endpoint;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (this.token) {
            headers['Authorization'] = 'Bearer ' + this.token;
        }
        
        try {
            const response = await fetch(url, {
                method: options.method || 'GET',
                headers: headers,
                body: options.body ? JSON.stringify(options.body) : undefined
            });
            
            const data = await response.json();
            
            if (response.status === 401) {
                this.logout();
                return null;
            }
            
            return data;
        } catch (error) {
            console.error('API request error:', error);
            return null;
        }
    },
    
    loadDashboard: async function() {
        const summary = await this.apiRequest('/dashboard/summary');
        const trends = await this.apiRequest('/dashboard/trends');
        
        if (summary && summary.data) {
            const data = summary.data;
            document.getElementById('total-devices').textContent = data.total_devices || 0;
            document.getElementById('online-devices').textContent = data.online_devices || 0;
            document.getElementById('active-alarms').textContent = data.active_alarms || 0;
            document.getElementById('critical-alarms').textContent = data.critical_alarms || 0;
            
            this.renderDeviceStatusChart(data.device_status);
            this.renderAlarmChart(data.alarm_severity);
        }
        
        if (trends && trends.data) {
            this.renderPerformanceChart(trends.data);
        }
    },
    
    renderDeviceStatusChart: function(statusData) {
        const ctx = document.getElementById('device-status-chart').getContext('2d');
        
        if (this.charts.deviceStatus) {
            this.charts.deviceStatus.destroy();
        }
        
        this.charts.deviceStatus = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['在线', '离线', '维护中'],
                datasets: [{
                    data: [
                        statusData?.online || 0,
                        statusData?.offline || 0,
                        statusData?.maintenance || 0
                    ],
                    backgroundColor: ['#50C878', '#FF6B6B', '#FFD700']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    },
    
    renderAlarmChart: function(severityData) {
        const ctx = document.getElementById('alarm-chart').getContext('2d');
        
        if (this.charts.alarmChart) {
            this.charts.alarmChart.destroy();
        }
        
        this.charts.alarmChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['严重', '警告', '信息'],
                datasets: [{
                    label: '告警数量',
                    data: [
                        severityData?.critical || 0,
                        severityData?.warning || 0,
                        severityData?.info || 0
                    ],
                    backgroundColor: ['#FF6B6B', '#FFD700', '#4A90E2']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    },
    
    renderPerformanceChart: function(trendsData) {
        const ctx = document.getElementById('performance-chart').getContext('2d');
        
        if (this.charts.performanceChart) {
            this.charts.performanceChart.destroy();
        }
        
        const labels = trendsData.labels || [];
        const cpuData = trendsData.cpu || [];
        const memoryData = trendsData.memory || [];
        
        this.charts.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'CPU使用率 (%)',
                        data: cpuData,
                        borderColor: '#4A90E2',
                        backgroundColor: 'rgba(74, 144, 226, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: '内存使用率 (%)',
                        data: memoryData,
                        borderColor: '#50C878',
                        backgroundColor: 'rgba(80, 200, 120, 0.1)',
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    },
    
    loadDevices: async function() {
        const search = document.getElementById('device-search').value;
        let url = '/devices/';
        if (search) {
            url += '?search=' + encodeURIComponent(search);
        }
        
        const result = await this.apiRequest(url);
        
        if (result && result.data) {
            this.renderDevicesTable(result.data);
        }
    },
    
    renderDevicesTable: function(devices) {
        const tbody = document.getElementById('devices-table-body');
        tbody.innerHTML = '';
        
        const typeNames = {
            'server': '服务器',
            'switch': '交换机',
            'router': '路由器',
            'firewall': '防火墙',
            'storage': '存储设备'
        };
        
        const statusClasses = {
            'online': 'status-online',
            'offline': 'status-offline',
            'maintenance': 'status-maintenance'
        };
        
        const statusNames = {
            'online': '在线',
            'offline': '离线',
            'maintenance': '维护中'
        };
        
        const self = this;
        
        devices.forEach(function(device) {
            const tr = document.createElement('tr');
            
            const perf = device.latest_performance || {};
            
            tr.innerHTML = `
                <td>${device.device_name}</td>
                <td>${typeNames[device.device_type] || device.device_type}</td>
                <td>${device.ip_address}</td>
                <td><span class="status-badge ${statusClasses[device.status]}">${statusNames[device.status]}</span></td>
                <td>${device.location || '-'}</td>
                <td>${self.renderProgressBar(perf.cpu_usage || 0)}</td>
                <td>${self.renderProgressBar(perf.memory_usage || 0)}</td>
                <td>
                    <button class="btn btn-sm btn-info" data-id="${device.id}" data-action="view">详情</button>
                    ${self.currentUser?.role?.name === 'device_admin' ? `
                    <button class="btn btn-sm btn-primary" data-id="${device.id}" data-action="edit">编辑</button>
                    <button class="btn btn-sm btn-danger" data-id="${device.id}" data-action="delete">删除</button>
                    ` : ''}
                </td>
            `;
            
            tbody.appendChild(tr);
        });
        
        tbody.querySelectorAll('button').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const id = this.dataset.id;
                const action = this.dataset.action;
                
                if (action === 'view') {
                    self.showDeviceDetail(id);
                } else if (action === 'edit') {
                    self.showDeviceEdit(id);
                } else if (action === 'delete') {
                    self.deleteDevice(id);
                }
            });
        });
    },
    
    renderProgressBar: function(value) {
        let color = '#50C878';
        if (value > 80) color = '#FF6B6B';
        else if (value > 60) color = '#FFD700';
        
        return `
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: ${value}%; background-color: ${color};"></div>
                <span class="progress-text">${value.toFixed(1)}%</span>
            </div>
        `;
    },
    
    showDeviceDetail: async function(deviceId) {
        const deviceResult = await this.apiRequest('/devices/' + deviceId);
        const trafficResult = await this.apiRequest('/devices/' + deviceId + '/network-traffic');
        const perfResult = await this.apiRequest('/devices/' + deviceId + '/performance');
        
        if (deviceResult && deviceResult.data) {
            const device = deviceResult.data;
            
            document.getElementById('detail-device-name').textContent = device.device_name;
            document.getElementById('detail-type').textContent = this.getTypeDisplayName(device.device_type);
            document.getElementById('detail-ip').textContent = device.ip_address;
            document.getElementById('detail-mac').textContent = device.mac_address || '-';
            document.getElementById('detail-location').textContent = device.location || '-';
            document.getElementById('detail-status').textContent = this.getStatusDisplayName(device.status);
            document.getElementById('detail-cpu-cores').textContent = device.cpu_cores + ' 核';
            document.getElementById('detail-memory-total').textContent = device.memory_total + ' GB';
            document.getElementById('detail-storage-total').textContent = device.storage_total + ' GB';
            
            if (trafficResult && trafficResult.data) {
                this.renderNetworkTrafficChart(trafficResult.data);
            }
            
            if (perfResult && perfResult.data) {
                this.renderDevicePerformanceChart(perfResult.data);
            }
            
            document.getElementById('device-detail-modal').style.display = 'flex';
        }
    },
    
    renderNetworkTrafficChart: function(trafficData) {
        const ctx = document.getElementById('network-traffic-chart').getContext('2d');
        
        if (this.charts.networkTraffic) {
            this.charts.networkTraffic.destroy();
        }
        
        const labels = trafficData.labels || [];
        
        const bytesIn = trafficData.bytes_in || [];
        const bytesOut = trafficData.bytes_out || [];
        
        const mbIn = bytesIn.map(b => (b / (1024 * 1024)).toFixed(2));
        const mbOut = bytesOut.map(b => (b / (1024 * 1024)).toFixed(2));
        
        this.charts.networkTraffic = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '入流量 (MB)',
                        data: mbIn,
                        borderColor: '#4A90E2',
                        backgroundColor: 'rgba(74, 144, 226, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: '出流量 (MB)',
                        data: mbOut,
                        borderColor: '#50C878',
                        backgroundColor: 'rgba(80, 200, 120, 0.1)',
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.raw + ' MB';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '流量 (MB)'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    },
    
    renderDevicePerformanceChart: function(perfData) {
        const ctx = document.getElementById('device-performance-chart').getContext('2d');
        
        if (this.charts.devicePerformance) {
            this.charts.devicePerformance.destroy();
        }
        
        const labels = perfData.labels || [];
        const cpuData = perfData.cpu || [];
        const memoryData = perfData.memory || [];
        const storageData = perfData.storage || [];
        
        this.charts.devicePerformance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'CPU使用率 (%)',
                        data: cpuData,
                        borderColor: '#4A90E2',
                        backgroundColor: 'rgba(74, 144, 226, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: '内存使用率 (%)',
                        data: memoryData,
                        borderColor: '#50C878',
                        backgroundColor: 'rgba(80, 200, 120, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: '存储使用率 (%)',
                        data: storageData,
                        borderColor: '#FFD700',
                        backgroundColor: 'rgba(255, 215, 0, 0.1)',
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    },
    
    getTypeDisplayName: function(type) {
        const names = {
            'server': '服务器',
            'switch': '交换机',
            'router': '路由器',
            'firewall': '防火墙',
            'storage': '存储设备'
        };
        return names[type] || type;
    },
    
    getStatusDisplayName: function(status) {
        const names = {
            'online': '在线',
            'offline': '离线',
            'maintenance': '维护中'
        };
        return names[status] || status;
    },
    
    loadAlarms: async function() {
        const severity = document.getElementById('alarm-severity-filter').value;
        const status = document.getElementById('alarm-status-filter').value;
        
        let url = '/alarms/';
        const params = [];
        if (severity) params.push('severity=' + severity);
        if (status) params.push('status=' + status);
        if (params.length > 0) {
            url += '?' + params.join('&');
        }
        
        const result = await this.apiRequest(url);
        
        if (result && result.data) {
            this.renderAlarmsTable(result.data);
        }
    },
    
    renderAlarmsTable: function(alarms) {
        const tbody = document.getElementById('alarms-table-body');
        tbody.innerHTML = '';
        
        const severityClasses = {
            'critical': 'severity-critical',
            'warning': 'severity-warning',
            'info': 'severity-info'
        };
        
        const severityNames = {
            'critical': '严重',
            'warning': '警告',
            'info': '信息'
        };
        
        const statusClasses = {
            'active': 'status-active',
            'acknowledged': 'status-acknowledged',
            'resolved': 'status-resolved'
        };
        
        const statusNames = {
            'active': '活跃',
            'acknowledged': '已确认',
            'resolved': '已解决'
        };
        
        const typeNames = {
            'cpu': 'CPU',
            'memory': '内存',
            'storage': '存储',
            'network': '网络',
            'other': '其他'
        };
        
        alarms.forEach(function(alarm) {
            const tr = document.createElement('tr');
            
            const deviceName = alarm.device?.device_name || '-';
            
            tr.innerHTML = `
                <td>${alarm.id}</td>
                <td>${alarm.title}</td>
                <td>${deviceName}</td>
                <td><span class="severity-badge ${severityClasses[alarm.severity]}">${severityNames[alarm.severity]}</span></td>
                <td>${typeNames[alarm.alarm_type] || alarm.alarm_type}</td>
                <td><span class="status-badge ${statusClasses[alarm.status]}">${statusNames[alarm.status]}</span></td>
                <td>${alarm.created_at ? new Date(alarm.created_at).toLocaleString('zh-CN') : '-'}</td>
                <td>
                    <button class="btn btn-sm btn-info" data-id="${alarm.id}" data-action="view">详情</button>
                    ${alarm.status === 'active' ? `<button class="btn btn-sm btn-warning" data-id="${alarm.id}" data-action="acknowledge">确认</button>` : ''}
                    ${alarm.status !== 'resolved' ? `<button class="btn btn-sm btn-success" data-id="${alarm.id}" data-action="resolve">解决</button>` : ''}
                </td>
            `;
            
            tbody.appendChild(tr);
        });
    },
    
    loadUsers: async function() {
        const result = await this.apiRequest('/users/');
        
        if (result && result.data) {
            this.renderUsersTable(result.data);
        }
    },
    
    renderUsersTable: function(users) {
        const tbody = document.getElementById('users-table-body');
        tbody.innerHTML = '';
        
        const roleNames = {
            'system_admin': '系统管理员',
            'device_admin': '设备管理员',
            'device_monitor': '设备监控员'
        };
        
        users.forEach(function(user) {
            const tr = document.createElement('tr');
            
            const roleName = user.role?.name ? roleNames[user.role.name] : '-';
            
            tr.innerHTML = `
                <td>${user.username}</td>
                <td>${user.real_name || '-'}</td>
                <td>${user.email || '-'}</td>
                <td>${roleName}</td>
                <td><span class="status-badge ${user.status === 'active' ? 'status-online' : 'status-offline'}">${user.status === 'active' ? '正常' : '禁用'}</span></td>
                <td>${user.last_login_at ? new Date(user.last_login_at).toLocaleString('zh-CN') : '-'}</td>
                <td>
                    <button class="btn btn-sm btn-primary" data-id="${user.id}" data-action="edit">编辑</button>
                    <button class="btn btn-sm btn-danger" data-id="${user.id}" data-action="delete">删除</button>
                </td>
            `;
            
            tbody.appendChild(tr);
        });
    },
    
    closeAllModals: function() {
        document.querySelectorAll('.modal').forEach(function(modal) {
            modal.style.display = 'none';
        });
    }
};

document.addEventListener('DOMContentLoaded', function() {
    NMS.init();
});
