const API = {
    async request(url, options = {}) {
        const token = Utils.getStorage('access_token');
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        try {
            const response = await fetch(`${Utils.BASE_URL}${url}`, {
                method: options.method || 'GET',
                headers,
                body: options.body ? JSON.stringify(options.body) : undefined,
                credentials: 'include'
            });
            
            if (response.status === 401) {
                const refreshToken = Utils.getStorage('refresh_token');
                if (refreshToken) {
                    const refreshed = await this.refreshToken(refreshToken);
                    if (refreshed) {
                        return this.request(url, options);
                    }
                }
                Utils.logout();
                throw new Error('登录已过期');
            }
            
            return await response.json();
        } catch (error) {
            console.error('API请求错误:', error);
            throw error;
        }
    },
    
    async refreshToken(refreshToken) {
        try {
            const response = await fetch(`${Utils.BASE_URL}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${refreshToken}`
                }
            });
            
            const data = await response.json();
            
            if (data.code === 200) {
                Utils.setStorage('access_token', data.data.access_token);
                return true;
            }
            return false;
        } catch (error) {
            console.error('刷新Token失败:', error);
            return false;
        }
    },
    
    async login(username, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: { username, password }
        });
    },
    
    async logout() {
        return this.request('/auth/logout', {
            method: 'POST'
        });
    },
    
    async getProfile() {
        return this.request('/auth/profile');
    },
    
    async changePassword(oldPassword, newPassword) {
        return this.request('/auth/change-password', {
            method: 'POST',
            body: { old_password: oldPassword, new_password: newPassword }
        });
    },
    
    async getCoachProfile() {
        return this.request('/coach/profile');
    },
    
    async updateCoachProfile(data) {
        return this.request('/coach/profile', {
            method: 'PUT',
            body: data
        });
    },
    
    async getCoachStudents(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/coach/students?${query}`);
    },
    
    async getCoachStudentDetail(studentId) {
        return this.request(`/coach/students/${studentId}`);
    },
    
    async getCoachCourses(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/coach/courses?${query}`);
    },
    
    async getCoachSchedules(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/coach/schedules?${query}`);
    },
    
    async getScheduleStudents(scheduleId) {
        return this.request(`/coach/schedules/${scheduleId}/students`);
    },
    
    async coachCheckIn(data) {
        return this.request('/coach/check-in', {
            method: 'POST',
            body: data
        });
    },
    
    async getCoachCheckInRecords(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/coach/check-in/records?${query}`);
    },
    
    async addGrade(data) {
        return this.request('/coach/grades', {
            method: 'POST',
            body: data
        });
    },
    
    async getCoachGrades(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/coach/grades?${query}`);
    },
    
    async updateGrade(gradeId, data) {
        return this.request(`/coach/grades/${gradeId}`, {
            method: 'PUT',
            body: data
        });
    },
    
    async getStudentProfile() {
        return this.request('/student/profile');
    },
    
    async updateStudentProfile(data) {
        return this.request('/student/profile', {
            method: 'PUT',
            body: data
        });
    },
    
    async getStudentCoach() {
        return this.request('/student/coach');
    },
    
    async getStudentCourses(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/student/courses?${query}`);
    },
    
    async getAvailableSchedules(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/student/schedules/available?${query}`);
    },
    
    async enrollCourse(scheduleId) {
        return this.request('/student/courses/enroll', {
            method: 'POST',
            body: { schedule_id: scheduleId }
        });
    },
    
    async cancelCourse(scheduleId) {
        return this.request('/student/courses/cancel', {
            method: 'POST',
            body: { schedule_id: scheduleId }
        });
    },
    
    async studentCheckIn(data) {
        return this.request('/student/check-in', {
            method: 'POST',
            body: data
        });
    },
    
    async getStudentCheckInRecords(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/student/check-in/records?${query}`);
    },
    
    async getStudentGrades(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/student/grades?${query}`);
    },
    
    async getStudentGradesStats() {
        return this.request('/student/grades/stats');
    },
    
    async getUsers(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/users?${query}`);
    },
    
    async getUserDetail(userId) {
        return this.request(`/admin/users/${userId}`);
    },
    
    async createUser(data) {
        return this.request('/admin/users', {
            method: 'POST',
            body: data
        });
    },
    
    async updateUser(userId, data) {
        return this.request(`/admin/users/${userId}`, {
            method: 'PUT',
            body: data
        });
    },
    
    async deleteUser(userId) {
        return this.request(`/admin/users/${userId}`, {
            method: 'DELETE'
        });
    },
    
    async getCoaches(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/coaches?${query}`);
    },
    
    async getStudents(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/students?${query}`);
    },
    
    async getCourses(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/courses?${query}`);
    },
    
    async createCourse(data) {
        return this.request('/admin/courses', {
            method: 'POST',
            body: data
        });
    },
    
    async getSchedules(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/schedules?${query}`);
    },
    
    async createSchedule(data) {
        return this.request('/admin/schedules', {
            method: 'POST',
            body: data
        });
    },
    
    async getAllGrades(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/grades?${query}`);
    },
    
    async getAllCheckIns(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/check-ins?${query}`);
    },
    
    async getOperationLogs(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/logs?${query}`);
    },
    
    async getDashboardStats() {
        return this.request('/admin/dashboard/stats');
    },
    
    async getRoles() {
        return this.request('/common/roles');
    }
};
