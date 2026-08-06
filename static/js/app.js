/* TreqTrace - Application JavaScript */

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
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
