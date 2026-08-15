class App {
  static currentUser = null;

  static async init() {
    this.bindEvents();
    await this.checkAuth();
  }

  static async checkAuth() {
    const token = WorkflowAPI.getAuthToken();
    if (!token) {
      this.showLoginModal();
      return;
    }

    try {
      this.currentUser = await WorkflowAPI.getCurrentUser();
      document.getElementById('current-user-display').textContent = `${this.currentUser.username} (${this.currentUser.role} - ${this.currentUser.department})`;
      this.hideLoginModal();
      await this.refreshDashboard();
    } catch (e) {
      this.showLoginModal();
    }
  }

  static bindEvents() {
    // Navigation Tabs
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        const tabName = item.dataset.tab;
        if (!tabName) return;

        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        item.classList.add('active');
        document.getElementById(`tab-${tabName}`).classList.add('active');

        this.refreshTab(tabName);
      });
    });

    // Login form submit
    document.getElementById('login-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const u = document.getElementById('login-username').value;
      const p = document.getElementById('login-password').value;
      try {
        await WorkflowAPI.login(u, p);
        await this.checkAuth();
      } catch (err) {
        alert('Login failed: ' + err.message);
      }
    });

    // New Workflow Form
    document.getElementById('new-workflow-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const templateId = parseInt(document.getElementById('start-template-select').value);
      const title = document.getElementById('start-title').value;
      const payloadStr = document.getElementById('start-payload').value;

      let payload = {};
      try {
        if (payloadStr) payload = JSON.parse(payloadStr);
      } catch (err) {
        alert('Invalid JSON in payload data');
        return;
      }

      try {
        await WorkflowAPI.startWorkflow(templateId, title, payload);
        this.closeModal('modal-new-workflow');
        alert('Workflow instance successfully initiated!');
        await this.refreshDashboard();
      } catch (err) {
        alert('Error starting workflow: ' + err.message);
      }
    });
  }

  static async refreshDashboard() {
    try {
      const [completion, bottlenecks, approvalTime, pendingTasks, activeInstances] = await Promise.all([
        WorkflowAPI.getCompletionRate(),
        WorkflowAPI.getBottlenecks(),
        WorkflowAPI.getApprovalTimeMetrics(),
        WorkflowAPI.getPendingTasks(),
        WorkflowAPI.getInstances('PENDING')
      ]);

      DashboardUI.renderKPIs(completion, bottlenecks, approvalTime);
      DashboardUI.renderPendingTasks(pendingTasks);
      DashboardUI.renderActiveInstances(activeInstances);
    } catch (err) {
      console.error('Error refreshing dashboard:', err);
    }
  }

  static async refreshTab(tabName) {
    if (tabName === 'dashboard') {
      await this.refreshDashboard();
    } else if (tabName === 'tasks') {
      const tasks = await WorkflowAPI.getPendingTasks();
      DashboardUI.renderPendingTasks(tasks);
    } else if (tabName === 'workflows') {
      const instances = await WorkflowAPI.getInstances();
      DashboardUI.renderActiveInstances(instances);
    } else if (tabName === 'audit') {
      const logs = await WorkflowAPI.getAuditLogs();
      DashboardUI.renderAuditLogs(logs);
    } else if (tabName === 'templates') {
      this.loadTemplatesTab();
    }
  }

  static async loadTemplatesTab() {
    const templates = await WorkflowAPI.getTemplates();
    const container = document.getElementById('templates-list');
    container.innerHTML = templates.map(t => `
      <div class="kpi-card" style="margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="color: var(--accent-primary);">${t.name}</h3>
          <span class="status-badge status-APPROVED">${t.department}</span>
        </div>
        <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0.5rem 0;">${t.description || 'No description'}</p>
        <div style="font-size: 0.8rem; color: var(--text-muted);">
          Stages: ${t.stages ? t.stages.map(s => s.name).join(' → ') : 'None'}
        </div>
      </div>
    `).join('');

    // Populate dropdown for new instance modal
    const select = document.getElementById('start-template-select');
    select.innerHTML = templates.map(t => `<option value="${t.id}">${t.name} (${t.department})</option>`).join('');
  }

  static showLoginModal() {
    document.getElementById('modal-login').classList.add('active');
  }

  static hideLoginModal() {
    document.getElementById('modal-login').classList.remove('active');
  }

  static logout() {
    WorkflowAPI.clearAuthToken();
    window.location.reload();
  }

  static openNewWorkflowModal() {
    this.loadTemplatesTab();
    document.getElementById('modal-new-workflow').classList.add('active');
  }

  static closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
  }

  static async viewWorkflowDetails(id) {
    const instance = await WorkflowAPI.getInstanceById(id);
    DashboardUI.renderWorkflowDetailsModal(instance);
    document.getElementById('modal-workflow-details').classList.add('active');
  }

  static showApproveModal(taskId) {
    const comments = prompt("Enter approval comments (optional):", "Approved");
    if (comments !== null) {
      WorkflowAPI.approveTask(taskId, comments)
        .then(() => {
          alert('Task approved successfully!');
          this.refreshDashboard();
        })
        .catch(err => alert('Approval failed: ' + err.message));
    }
  }

  static showRejectModal(taskId) {
    const reason = prompt("Enter mandatory rejection reason:", "");
    if (reason && reason.trim()) {
      WorkflowAPI.rejectTask(taskId, reason)
        .then(() => {
          alert('Task rejected successfully!');
          this.refreshDashboard();
        })
        .catch(err => alert('Rejection failed: ' + err.message));
    } else if (reason !== null) {
      alert("Rejection reason cannot be empty.");
    }
  }

  static showModifyModal(taskId) {
    const comments = prompt("Enter required modification instructions:", "");
    if (comments && comments.trim()) {
      WorkflowAPI.requestModification(taskId, comments)
        .then(() => {
          alert('Modification request sent back successfully!');
          this.refreshDashboard();
        })
        .catch(err => alert('Modification request failed: ' + err.message));
    } else if (comments !== null) {
      alert("Modification instructions cannot be empty.");
    }
  }

  static async verifyAuditIntegrity() {
    const res = await WorkflowAPI.verifyAuditIntegrity();
    alert(`Audit Integrity Check Result:\n\nStatus: ${res.is_valid ? 'VALID (100% Un-tampered)' : 'CORRUPTED DETECTED'}\nTotal Records Examined: ${res.total_records}\nMessage: ${res.message}`);
  }
}

document.addEventListener('DOMContentLoaded', () => App.init());
