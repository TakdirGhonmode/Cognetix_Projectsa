class DashboardUI {
  static renderKPIs(completionData, bottleneckData, approvalData) {
    document.getElementById('kpi-total').textContent = completionData.total_instances || 0;
    document.getElementById('kpi-completed').textContent = completionData.completed_count || 0;
    document.getElementById('kpi-rate').textContent = `${completionData.completion_rate_percent || 0}%`;
    document.getElementById('kpi-bottlenecks').textContent = bottleneckData.total_bottlenecks || 0;
    document.getElementById('kpi-avg-time').textContent = `${approvalData.overall_avg_hours || 0} hrs`;
  }

  static renderPendingTasks(tasks) {
    const container = document.getElementById('pending-tasks-list');
    const badge = document.getElementById('pending-count-badge');
    badge.textContent = tasks.length;

    if (!tasks || tasks.length === 0) {
      container.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No pending task approvals for your assigned role/department.</td></tr>`;
      return;
    }

    container.innerHTML = tasks.map(task => `
      <tr>
        <td><strong>#T-${task.id}</strong></td>
        <td>Instance #${task.instance_id}</td>
        <td>${task.stage ? task.stage.name : 'Stage ' + task.stage_id}</td>
        <td>
          <span class="badge" style="background-color: var(--bg-card-hover); color: var(--accent-primary);">
            ${task.assigned_role || task.assigned_department || 'Direct User'}
          </span>
        </td>
        <td>${new Date(task.created_at).toLocaleString()}</td>
        <td>
          <button class="btn btn-success btn-sm" onclick="App.showApproveModal(${task.id})">Approve</button>
          <button class="btn btn-danger btn-sm" onclick="App.showRejectModal(${task.id})">Reject</button>
          <button class="btn btn-warning btn-sm" onclick="App.showModifyModal(${task.id})">Modify</button>
        </td>
      </tr>
    `).join('');
  }

  static renderActiveInstances(instances) {
    const container = document.getElementById('active-workflows-list');
    if (!instances || instances.length === 0) {
      container.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No active workflows currently running.</td></tr>`;
      return;
    }

    container.innerHTML = instances.map(inst => `
      <tr>
        <td><strong>#W-${inst.id}</strong></td>
        <td><strong>${inst.title}</strong></td>
        <td>${inst.current_stage ? inst.current_stage.name : 'Completed / None'}</td>
        <td><span class="status-badge status-${inst.status}">${inst.status}</span></td>
        <td>${new Date(inst.created_at).toLocaleDateString()}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="App.viewWorkflowDetails(${inst.id})">View Flow</button>
        </td>
      </tr>
    `).join('');
  }

  static renderAuditLogs(logs) {
    const container = document.getElementById('audit-logs-list');
    if (!logs || logs.length === 0) {
      container.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No audit log entries found.</td></tr>`;
      return;
    }

    container.innerHTML = logs.map(log => `
      <tr>
        <td>#A-${log.id}</td>
        <td>#W-${log.instance_id}</td>
        <td><strong>${log.action}</strong></td>
        <td>${log.actor ? log.actor.username + ' (' + log.actor.role + ')' : 'User #' + log.actor_id}</td>
        <td style="font-family: monospace; font-size: 0.75rem; color: var(--accent-primary);">${log.current_hash.substring(0, 16)}...</td>
        <td>${new Date(log.timestamp).toLocaleString()}</td>
      </tr>
    `).join('');
  }

  static renderWorkflowDetailsModal(instance) {
    const titleEl = document.getElementById('modal-workflow-title');
    const container = document.getElementById('workflow-stage-flow');
    titleEl.textContent = `${instance.title} (Status: ${instance.status})`;

    const tasksMap = {};
    if (instance.tasks) {
      instance.tasks.forEach(t => {
        tasksMap[t.stage_id] = t;
      });
    }

    let stages = [];
    if (instance.template && instance.template.stages) {
      stages = instance.template.stages;
    } else {
      stages = instance.current_stage ? [instance.current_stage] : [];
    }

    let html = '<div class="stage-timeline">';
    stages.forEach((stage, idx) => {
      const task = tasksMap[stage.id];
      let stepClass = '';
      let statusText = 'Pending';

      if (task) {
        if (task.status === 'APPROVED') { stepClass = 'completed'; statusText = 'Approved'; }
        else if (task.status === 'PENDING') { stepClass = 'active'; statusText = 'In Progress'; }
        else if (task.status === 'REJECTED') { stepClass = 'rejected'; statusText = 'Rejected'; }
        else if (task.status === 'MODIFICATION_REQUESTED') { stepClass = 'modify'; statusText = 'Modify Req'; }
      } else if (instance.current_stage_id === stage.id) {
        stepClass = 'active';
        statusText = 'Active';
      }

      html += `
        <div class="timeline-step ${stepClass}">
          <div class="step-circle">${idx + 1}</div>
          <div class="step-label">${stage.name}</div>
          <div style="font-size: 0.7rem; color: var(--text-secondary);">${statusText}</div>
        </div>
      `;
      if (idx < stages.length - 1) {
        html += `<div class="timeline-connector ${stepClass === 'completed' ? 'completed' : ''}"></div>`;
      }
    });
    html += '</div>';

    container.innerHTML = html;
  }
}
