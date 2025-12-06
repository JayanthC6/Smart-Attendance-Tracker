// Main JavaScript file for Smart Attendance Tracker

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Initialize attendance charts
    initializeAttendanceCharts();

    // Initialize notification system
    initializeNotifications();

    // Initialize form validations
    initializeFormValidations();

    // Initialize attendance taking functionality
    initializeAttendanceTaking();
});

// Attendance Charts
function initializeAttendanceCharts() {
    const chartElements = document.querySelectorAll('.attendance-chart');
    
    chartElements.forEach(function(element) {
        const ctx = element.getContext('2d');
        const data = JSON.parse(element.dataset.chartData || '{}');
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Attendance %',
                    data: data.values || [],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    });
}

// Notification System
function initializeNotifications() {
    // Mark notification as read when clicked
    const notificationItems = document.querySelectorAll('.notification-item');
    notificationItems.forEach(function(item) {
        item.addEventListener('click', function() {
            const notificationId = this.dataset.notificationId;
            if (notificationId) {
                markNotificationAsRead(notificationId);
            }
        });
    });

    // Auto-refresh notifications every 30 seconds
    setInterval(function() {
        refreshNotifications();
    }, 30000);
}

function markNotificationAsRead(notificationId) {
    fetch(`/api/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI to show notification as read
            const notificationElement = document.querySelector(`[data-notification-id="${notificationId}"]`);
            if (notificationElement) {
                notificationElement.classList.remove('fw-bold');
                notificationElement.classList.add('text-muted');
            }
        }
    })
    .catch(error => {
        console.error('Error marking notification as read:', error);
    });
}

function refreshNotifications() {
    fetch('/api/notifications?limit=5')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateNotificationBadge(data.data.filter(n => !n.is_read).length);
        }
    })
    .catch(error => {
        console.error('Error refreshing notifications:', error);
    });
}

function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline';
        } else {
            badge.style.display = 'none';
        }
    }
}

// Form Validations
function initializeFormValidations() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Password confirmation validation
    const passwordConfirm = document.getElementById('confirm_password');
    const password = document.getElementById('password');
    
    if (passwordConfirm && password) {
        passwordConfirm.addEventListener('input', function() {
            if (this.value !== password.value) {
                this.setCustomValidity('Passwords do not match');
            } else {
                this.setCustomValidity('');
            }
        });
    }
}

// Attendance Taking Functionality
function initializeAttendanceTaking() {
    const selectAllCheckbox = document.getElementById('select-all-students');
    const studentCheckboxes = document.querySelectorAll('.student-checkbox');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            studentCheckboxes.forEach(function(checkbox) {
                checkbox.checked = this.checked;
            });
        });
    }

    // Update present students count
    studentCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            updatePresentStudentsCount();
        });
    });

    // Initialize attendance form
    const attendanceForm = document.getElementById('attendance-form');
    if (attendanceForm) {
        attendanceForm.addEventListener('submit', function(event) {
            const presentStudents = document.querySelectorAll('.student-checkbox:checked');
            if (presentStudents.length === 0) {
                event.preventDefault();
                alert('Please select at least one student as present.');
                return false;
            }
        });
    }
}

function updatePresentStudentsCount() {
    const presentStudents = document.querySelectorAll('.student-checkbox:checked');
    const countElement = document.getElementById('present-count');
    
    if (countElement) {
        countElement.textContent = presentStudents.length;
    }
}

// Utility Functions
function showLoading(element) {
    const originalContent = element.innerHTML;
    element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    element.disabled = true;
    
    return function() {
        element.innerHTML = originalContent;
        element.disabled = false;
    };
}

function showSuccess(message) {
    showAlert(message, 'success');
}

function showError(message) {
    showAlert(message, 'danger');
}

function showAlert(message, type) {
    const alertContainer = document.getElementById('alert-container') || createAlertContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Export functionality
function exportToCSV(data, filename) {
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

function convertToCSV(data) {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
    ].join('\n');
    
    return csvContent;
}

// Print functionality
function printPage() {
    window.print();
}

function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Print</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
                </head>
                <body>
                    ${element.outerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
}

// Search functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const targetTable = document.querySelector(this.dataset.target);
            
            if (targetTable) {
                const rows = targetTable.querySelectorAll('tbody tr');
                rows.forEach(function(row) {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            }
        });
    });
}

// Initialize search when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
});

// Date picker enhancements
function initializeDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    dateInputs.forEach(function(input) {
        // Set max date to today
        input.max = new Date().toISOString().split('T')[0];
        
        // Set default value to today if not set
        if (!input.value) {
            input.value = new Date().toISOString().split('T')[0];
        }
    });
}

// Initialize date pickers when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDatePickers();
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Back to top button
function initializeBackToTop() {
    const backToTopButton = document.createElement('button');
    backToTopButton.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTopButton.className = 'btn btn-primary position-fixed bottom-0 end-0 m-3 rounded-circle';
    backToTopButton.style.display = 'none';
    backToTopButton.style.zIndex = '9999';
    backToTopButton.title = 'Back to top';
    
    document.body.appendChild(backToTopButton);
    
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.style.display = 'block';
        } else {
            backToTopButton.style.display = 'none';
        }
    });
    
    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Initialize back to top button when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeBackToTop();
});
