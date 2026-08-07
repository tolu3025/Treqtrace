/* TreqTrace - Application JavaScript */

document.addEventListener('DOMContentLoaded', function() {
    // Theme Management
    const themeToggle = document.getElementById('themeToggleBtn');
    
    // Check local storage or system preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        updateThemeToggleIcon(true);
    } else if (savedTheme === 'light') {
        document.body.classList.remove('dark-theme');
        updateThemeToggleIcon(false);
    } else {
        // Default to dark theme if not set
        document.body.classList.add('dark-theme');
        updateThemeToggleIcon(true);
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const isDark = document.body.classList.toggle('dark-theme');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            updateThemeToggleIcon(isDark);
            
            // Re-render chart if it exists to match theme border colors
            if (window.validationChartInstance) {
                window.validationChartInstance.options.datasets[0].borderColor = isDark ? '#111827' : '#ffffff';
                window.validationChartInstance.options.plugins.legend.labels.color = isDark ? '#94a3b8' : '#64748b';
                window.validationChartInstance.update();
            }
        });
    }

    function updateThemeToggleIcon(isDark) {
        if (!themeToggle) return;
        const icon = themeToggle.querySelector('i');
        if (isDark) {
            icon.className = 'bi bi-sun-fill';
        } else {
            icon.className = 'bi bi-moon-fill';
        }
    }

    // Password Visibility Toggle
    document.querySelectorAll('.password-toggle-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const container = this.closest('.input-group');
            const input = container.querySelector('input');
            const icon = this.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // Confirm deletes
    document.querySelectorAll('form[onsubmit]').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to proceed?')) {
                e.preventDefault();
            }
        });
    });

    // Notifications Management
    const notifBadge = document.getElementById('notifBadge');
    const notifListContainer = document.getElementById('notifListContainer');
    const markAllReadBtn = document.getElementById('markAllReadBtn');

    function fetchNotifications() {
        fetch('/api/notifications')
            .then(res => res.json())
            .then(data => {
                if (data.unread_count > 0) {
                    notifBadge.textContent = data.unread_count;
                    notifBadge.classList.remove('d-none');
                } else {
                    notifBadge.classList.add('d-none');
                }

                if (data.notifications && data.notifications.length > 0) {
                    notifListContainer.innerHTML = data.notifications.map(n => `
                        <li>
                            <div class="dropdown-item py-2 border-bottom" style="border-color: var(--border) !important; white-space: normal;">
                                <div class="d-flex justify-content-between align-items-start mb-1">
                                    <span class="fw-semibold text-main small" style="line-height:1.2; display:block;">${n.message}</span>
                                    ${!n.is_read ? '<span class="status-dot success ms-2" style="flex-shrink:0;"></span>' : ''}
                                </div>
                                <span class="text-muted" style="font-size: 0.72rem;">${n.created_at}</span>
                            </div>
                        </li>
                    `).join('');
                } else {
                    notifListContainer.innerHTML = `
                        <li><span class="dropdown-item-text text-muted small text-center py-3 d-block">No notifications</span></li>
                    `;
                }
            })
            .catch(err => console.error("Error loading notifications:", err));
    }

    if (notifBadge) {
        fetchNotifications();
        setInterval(fetchNotifications, 30000);
    }

    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            fetch('/notifications/mark-all-read', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        fetchNotifications();
                    }
                })
                .catch(err => console.error(err));
        });
    }
});


// Traceability link management
function addLink(requirementId, artifactId, artifactType) {
    fetch('/api/trace-link', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            requirement_id: requirementId,
            artifact_id: artifactId,
            artifact_type: artifactType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert(data.message || 'Failed to create link');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while creating the link');
    });
}

function removeLink(linkId) {
    if (!confirm('Remove this traceability link?')) return;

    fetch(`/api/trace-link/${linkId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Report generation helper
function generateReport(projectId) {
    window.open(`/projects/${projectId}/reports/export`, '_blank');
}
