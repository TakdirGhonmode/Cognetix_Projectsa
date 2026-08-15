const API_BASE_URL = window.location.origin;

class WorkflowAPI {
  static getAuthToken() {
    return localStorage.getItem('token');
  }

  static setAuthToken(token) {
    localStorage.setItem('token', token);
  }

  static clearAuthToken() {
    localStorage.removeItem('token');
  }

  static async request(endpoint, options = {}) {
    const token = this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers
      });

      if (response.status === 401 && !endpoint.includes('/auth/login')) {
        this.clearAuthToken();
        window.location.reload();
        return;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'An unexpected error occurred' }));
        throw new Error(errorData.detail || `HTTP Error ${response.status}`);
      }

      if (response.status === 204) return null;
      return await response.json();
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  }

  // Auth APIs
  static async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const data = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    }).then(res => {
      if (!res.ok) throw new Error('Invalid credentials');
      return res.json();
    });

    this.setAuthToken(data.access_token);
    return data;
  }

  static async getCurrentUser() {
    return this.request('/auth/me');
  }

  // Templates
  static async getTemplates() {
    return this.request('/templates');
  }

  static async createTemplate(templateData) {
    return this.request('/templates', {
      method: 'POST',
      body: JSON.stringify(templateData)
    });
  }

  // Instances
  static async getInstances(status = null) {
    const query = status ? `?status_filter=${status}` : '';
    return this.request(`/instances${query}`);
  }

  static async getInstanceById(id) {
    return this.request(`/instances/${id}`);
  }

  static async startWorkflow(template_id, title, payload) {
    return this.request('/instances', {
      method: 'POST',
      body: JSON.stringify({ template_id, title, payload })
    });
  }

  // Tasks
  static async getPendingTasks() {
    return this.request('/tasks/pending');
  }

  static async approveTask(taskId, comments = '') {
    return this.request(`/tasks/${taskId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ comments })
    });
  }

  static async rejectTask(taskId, reason) {
    return this.request(`/tasks/${taskId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    });
  }

  static async requestModification(taskId, comments) {
    return this.request(`/tasks/${taskId}/modify`, {
      method: 'POST',
      body: JSON.stringify({ comments })
    });
  }

  // Analytics
  static async getApprovalTimeMetrics() {
    return this.request('/analytics/approval-time');
  }

  static async getBottlenecks() {
    return this.request('/analytics/bottlenecks');
  }

  static async getCompletionRate() {
    return this.request('/analytics/completion-rate');
  }

  // Audit
  static async getAuditLogs(instanceId = null) {
    const query = instanceId ? `?instance_id=${instanceId}` : '';
    return this.request(`/audit${query}`);
  }

  static async verifyAuditIntegrity() {
    return this.request('/audit/verify');
  }

  // Users
  static async listUsers() {
    return this.request('/users');
  }
}
