/**
 * Admin Panel JavaScript
 * Handles group and user management functionality
 */

// Global variables
let currentSelectedGroupId = null;
let currentSelectedGroupKey = null;
let currentSelectedGroupName = null;

/**
 * Utility function to escape HTML to prevent XSS attacks
 */
function escapeHtml(text) {
    if (text === null || text === undefined) {
        return '';
    }
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, function(m) { return map[m]; });
}

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeAdmin();
});

/**
 * Initialize admin panel functionality
 */
function initializeAdmin() {
    // Initialize form handlers
    initializeGroupForms();
    initializeUserForms();
    initializeCoinsManagement();
    initializeHistoryManagement();
    
    // Auto-generate group key from name
    setupGroupKeyAutoGeneration();
    
    console.log('Admin panel initialized');
}

/**
 * Initialize group form handlers
 */
function initializeGroupForms() {
    // Add Group Form
    const addGroupForm = document.getElementById('addGroupForm');
    if (addGroupForm) {
        addGroupForm.addEventListener('submit', handleAddGroup);
    }
    
    // Edit Group Form
    const editGroupForm = document.getElementById('editGroupForm');
    if (editGroupForm) {
        editGroupForm.addEventListener('submit', handleEditGroup);
    }
}

/**
 * Initialize user form handlers
 */
function initializeUserForms() {
    // Add User Form
    const addUserForm = document.getElementById('addUserForm');
    if (addUserForm) {
        addUserForm.addEventListener('submit', handleAddUser);
    }
    
    // Edit User Form
    const editUserForm = document.getElementById('editUserForm');
    if (editUserForm) {
        editUserForm.addEventListener('submit', handleEditUser);
    }
}

/**
 * Setup auto-generation of group key from name
 */
function setupGroupKeyAutoGeneration() {
    const groupNameInput = document.getElementById('groupName');
    const groupKeyInput = document.getElementById('groupKey');
    
    if (groupNameInput && groupKeyInput) {
        groupNameInput.addEventListener('input', function() {
            const name = this.value;
            const key = generateGroupKey(name);
            groupKeyInput.value = key;
        });
    }
}

/**
 * Generate a URL-friendly group key from name
 */
function generateGroupKey(name) {
    return name
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
        .replace(/\s+/g, '-') // Replace spaces with hyphens
        .replace(/-+/g, '-') // Replace multiple hyphens with single
        .replace(/^-|-$/g, ''); // Remove leading/trailing hyphens
}

/**
 * Handle add group form submission
 */
async function handleAddGroup(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const groupData = {
        name: formData.get('groupName') || document.getElementById('groupName').value,
        group_key: formData.get('groupKey') || document.getElementById('groupKey').value
    };
    
    if (!groupData.name || !groupData.group_key) {
        showAlert('Please fill in all required fields', 'warning');
        return;
    }
    
    try {
        showLoading(true);
        
        console.log('Creating group with data:', groupData);
        
        const response = await fetch('/api/groups/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(groupData)
        });
        
        const result = await response.json();
        console.log('Group creation response:', response.status, result);
        
        if (response.ok && result.success) {
            showAlert('Group created successfully!', 'success');
            closeModal('addGroupModal');
            resetForm('addGroupForm');
            // Small delay to ensure backend processing is complete
            setTimeout(async () => {
                await refreshGroupsTable();
            }, 500);
        } else {
            console.error('Group creation failed:', result);
            showAlert(result.detail || 'Failed to create group', 'danger');
        }
    } catch (error) {
        console.error('Error creating group:', error);
        showAlert('An error occurred while creating the group', 'danger');
    } finally {
        showLoading(false);
    }
}

/**
 * Handle edit group form submission
 */
async function handleEditGroup(event) {
    event.preventDefault();
    
    const groupId = document.getElementById('editGroupId').value;
    const groupKey = document.getElementById('editGroupKey').value;
    const groupName = document.getElementById('editGroupName').value;
    
    if (!groupName) {
        showAlert('Please enter a group name', 'warning');
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch(`/api/groups/${groupKey}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: groupName })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showAlert('Group updated successfully!', 'success');
            closeModal('editGroupModal');
            // Small delay to ensure backend processing is complete
            setTimeout(async () => {
                await refreshGroupsTable();
            }, 500);
        } else {
            showAlert(result.detail || 'Failed to update group', 'danger');
        }
    } catch (error) {
        console.error('Error updating group:', error);
        showAlert('An error occurred while updating the group', 'danger');
    } finally {
        showLoading(false);
    }
}

/**
 * Handle add user form submission
 */
async function handleAddUser(event) {
    event.preventDefault();
    
    const groupKey = document.getElementById('userGroupKey').value;
    const userName = document.getElementById('userName').value;
    const userAlias = document.getElementById('userAlias').value;
    
    if (!userName || !userAlias) {
        showAlert('Please enter both name and alias', 'warning');
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch(`/api/groups/${groupKey}/users`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: userName,
                alias: userAlias
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showAlert('User added successfully!', 'success');
            closeModal('addUserModal');
            resetForm('addUserForm');
            await loadGroupUsers(currentSelectedGroupId, currentSelectedGroupKey);
        } else {
            showAlert(result.detail || 'Failed to add user', 'danger');
        }
    } catch (error) {
        console.error('Error adding user:', error);
        showAlert('An error occurred while adding the user', 'danger');
    } finally {
        showLoading(false);
    }
}

/**
 * Handle edit user form submission
 */
async function handleEditUser(event) {
    event.preventDefault();
    
    const groupKey = document.getElementById('editUserGroupKey').value;
    const userName = document.getElementById('editUserName').value;
    const userAlias = document.getElementById('editUserAlias').value;
    
    if (!userAlias) {
        showAlert('Please enter an alias', 'warning');
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch(`/api/groups/${groupKey}/users/${userName}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                alias: userAlias
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showAlert('User updated successfully!', 'success');
            closeModal('editUserModal');
            await loadGroupUsers(currentSelectedGroupId, currentSelectedGroupKey);
        } else {
            showAlert(result.detail || 'Failed to update user', 'danger');
        }
    } catch (error) {
        console.error('Error updating user:', error);
        showAlert('An error occurred while updating the user', 'danger');
    } finally {
        showLoading(false);
    }
}

/**
 * Edit group function called from template
 */
function editGroup(groupId, groupName, groupKey) {
    document.getElementById('editGroupId').value = groupId;
    document.getElementById('editGroupKey').value = groupKey;
    document.getElementById('editGroupName').value = groupName;
    document.getElementById('editGroupKeyDisplay').value = groupKey;
    
    const modal = new bootstrap.Modal(document.getElementById('editGroupModal'));
    modal.show();
}

/**
 * Delete group function called from template
 */
async function deleteGroup(groupId, groupName) {
    if (!confirm(`Are you sure you want to delete the group "${groupName}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        showLoading(true);
        
        // Find the group key from the table row
        const row = document.querySelector(`tr[data-group-id="${groupId}"]`);
        const groupKey = row ? row.dataset.groupKey : null;
        
        if (!groupKey) {
            showAlert('Could not find group key', 'danger');
            return;
        }
        
        const response = await fetch(`/api/groups/${groupKey}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showAlert('Group deleted successfully!', 'success');
            // Small delay to ensure backend processing is complete
            setTimeout(async () => {
                await refreshGroupsTable();
            }, 500);
            
            // Clear users table if this group was selected
            if (currentSelectedGroupId === groupId) {
                clearUsersTable();
            }
        } else {
            showAlert(result.detail || 'Failed to delete group', 'danger');
        }
    } catch (error) {
        console.error('Error deleting group:', error);
        showAlert('An error occurred while deleting the group', 'danger');
    } finally {
        showLoading(false);
    }
}

/**
 * View group users function called from template
 */
async function viewGroupUsers(groupId, groupKey, groupName) {
    currentSelectedGroupId = groupId;
    currentSelectedGroupKey = groupKey;
    currentSelectedGroupName = groupName;
    
    // Highlight selected group row
    document.querySelectorAll('#groupsTable tbody tr').forEach(row => {
        row.classList.remove('table-active');
    });
    document.querySelector(`tr[data-group-id="${groupId}"]`).classList.add('table-active');
    
    // Update UI
    document.getElementById('selectedGroupName').textContent = `(${groupName})`;
    document.getElementById('addUserBtn').disabled = false;
    
    // Set group info in add user form
    document.getElementById('userGroupId').value = groupId;
    document.getElementById('userGroupKey').value = groupKey;
    
    // Load users
    await loadGroupUsers(groupId, groupKey);
}

/**
 * Load group users
 */
async function loadGroupUsers(groupId, groupKey) {
    try {
        const response = await fetch(`/api/groups/${groupKey}/users`);
        const result = await response.json();
        
        if (response.ok) {
            displayUsersTable(result.users || []);
        } else {
            showAlert('Failed to load group users', 'warning');
            clearUsersTable();
        }
    } catch (error) {
        console.error('Error loading group users:', error);
        showAlert('An error occurred while loading users', 'danger');
        clearUsersTable();
    }
}

/**
 * Display users table
 */
function displayUsersTable(users) {
    const container = document.getElementById('usersTableContainer');
    
    if (users.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-users me-2"></i>
                No users in this group
            </div>
        `;
        return;
    }
    
    const tableHTML = `
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead class="table-dark">
                    <tr>
                        <th>Name</th>
                        <th>Alias</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${users.map(user => `
                        <tr>
                            <td><code>${user.name}</code></td>
                            <td>${user.alias}</td>
                            <td>
                                ${user.is_active ? 
                                    '<span class="badge bg-success">Active</span>' : 
                                    '<span class="badge bg-secondary">Inactive</span>'
                                }
                            </td>
                            <td>
                                <div class="btn-group" role="group">
                                    <button type="button" class="btn btn-outline-primary btn-sm" onclick="editUser('${user.name}', '${user.alias}')">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button type="button" class="btn btn-outline-danger btn-sm" onclick="deleteUser('${user.name}', '${user.alias}')">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = tableHTML;
}

/**
 * Edit user function
 */
function editUser(userName, userAlias) {
    document.getElementById('editUserGroupId').value = currentSelectedGroupId;
    document.getElementById('editUserGroupKey').value = currentSelectedGroupKey;
    document.getElementById('editUserName').value = userName;
    document.getElementById('editUserNameDisplay').value = userName;
    document.getElementById('editUserAlias').value = userAlias;
    
    const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
    modal.show();
}

/**
 * Delete user function
 */
async function deleteUser(userName, userAlias) {
    if (!confirm(`Are you sure you want to remove "${userAlias}" from the group? This action cannot be undone.`)) {
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch(`/api/groups/${currentSelectedGroupKey}/users/${userName}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showAlert('User removed successfully!', 'success');
            await loadGroupUsers(currentSelectedGroupId, currentSelectedGroupKey);
        } else {
            showAlert(result.detail || 'Failed to remove user', 'danger');
        }
    } catch (error) {
        console.error('Error removing user:', error);
        showAlert('An error occurred while removing the user', 'danger');
    } finally {
        showLoading(false);
    }
}

/**
 * Clear users table
 */
function clearUsersTable() {
    currentSelectedGroupId = null;
    currentSelectedGroupKey = null;
    currentSelectedGroupName = null;
    
    document.getElementById('selectedGroupName').textContent = '';
    document.getElementById('addUserBtn').disabled = true;
    
    const container = document.getElementById('usersTableContainer');
    container.innerHTML = `
        <div class="text-center text-muted py-4">
            <i class="fas fa-arrow-left me-2"></i>
            Select a group to view users
        </div>
    `;
}

/**
 * Refresh groups table
 */
async function refreshGroupsTable() {
    try {
        showLoading(true);
        
        // Fetch updated groups data
        const response = await fetch('/api/groups/');
        const result = await response.json();
        
        if (response.ok) {
            updateGroupsTable(result.groups || []);
        } else {
            console.error('Failed to fetch groups:', result);
            showAlert('Failed to refresh groups list', 'warning');
            // Fallback to page reload if API call fails
            setTimeout(() => window.location.reload(), 1000);
        }
    } catch (error) {
        console.error('Error refreshing groups:', error);
        showAlert('Failed to refresh groups list', 'warning');
        // Fallback to page reload if fetch fails
        setTimeout(() => window.location.reload(), 1000);
    } finally {
        showLoading(false);
    }
}

/**
 * Update the groups table with new data
 */
function updateGroupsTable(groups) {
    const tbody = document.querySelector('#groupsTable tbody');
    if (!tbody) {
        console.error('Groups table body not found');
        return;
    }
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    // Add new rows
    groups.forEach(group => {
        const row = document.createElement('tr');
        row.dataset.groupId = group.id;
        row.dataset.groupKey = group.group_key;
        
        row.innerHTML = `
            <td>${group.name}</td>
            <td><code>${group.group_key}</code></td>
            <td>
                ${group.is_active ? 
                    '<span class="badge bg-success">Active</span>' : 
                    '<span class="badge bg-secondary">Inactive</span>'
                }
            </td>
            <td>
                <div class="btn-group" role="group">
                    <button type="button" class="btn btn-outline-primary btn-sm" onclick="editGroup('${group.id}', '${group.name}', '${group.group_key}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button type="button" class="btn btn-outline-info btn-sm" onclick="viewGroupUsers('${group.id}', '${group.group_key}', '${group.name}')">
                        <i class="fas fa-users"></i>
                    </button>
                    <button type="button" class="btn btn-outline-danger btn-sm" onclick="deleteGroup('${group.id}', '${group.name}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    console.log(`Updated groups table with ${groups.length} groups`);
}

/**
 * Show loading modal
 */
function showLoading(show) {
    const modal = document.getElementById('loadingModal');
    if (show) {
        const loadingModal = new bootstrap.Modal(modal);
        loadingModal.show();
    } else {
        const loadingModal = bootstrap.Modal.getInstance(modal);
        if (loadingModal) {
            loadingModal.hide();
        }
    }
}

/**
 * Close modal by ID
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    const modalInstance = bootstrap.Modal.getInstance(modal);
    if (modalInstance) {
        modalInstance.hide();
    }
}

/**
 * Reset form by ID
 */
function resetForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
    }
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert at the top of the content
    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// ========================
// COINS MANAGEMENT
// ========================

// Global variables for coins import
let uploadedCoinsData = [];
let currentCoinsPage = 0;
let currentCoinsLimit = 100;
let currentCoinsTotal = 0;
let currentFilters = {};

/**
 * Initialize coins management functionality
 */
function initializeCoinsManagement() {
    const csvFileInput = document.getElementById('csvFile');
    const uploadCsvBtn = document.getElementById('uploadCsvBtn');
    const exportCsvBtn = document.getElementById('exportCsvBtn');
    const selectAllBtn = document.getElementById('selectAllBtn');
    const deselectAllBtn = document.getElementById('deselectAllBtn');
    const importSelectedBtn = document.getElementById('importSelectedBtn');
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    
    // View coins elements
    const loadCoinsBtn = document.getElementById('loadCoinsBtn');
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');

    // File input change handler
    if (csvFileInput) {
        csvFileInput.addEventListener('change', function() {
            uploadCsvBtn.disabled = !this.files.length;
        });
    }

    // Upload CSV button handler
    if (uploadCsvBtn) {
        uploadCsvBtn.addEventListener('click', handleCsvUpload);
    }

    // Export CSV button handler
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', handleCsvExport);
    }

    // Select/Deselect buttons
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', () => selectAllNewCoins(true));
    }
    
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', () => selectAllNewCoins(false));
    }

    // Import selected button
    if (importSelectedBtn) {
        importSelectedBtn.addEventListener('click', handleImportSelected);
    }

    // Select all checkbox
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            selectAllNewCoins(this.checked);
        });
    }

    // View coins handlers
    if (loadCoinsBtn) {
        loadCoinsBtn.addEventListener('click', loadCoinsFromDatabase);
    }

    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', applyCoinsFilters);
    }

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearCoinsFilters);
    }

    if (prevPageBtn) {
        prevPageBtn.addEventListener('click', () => changePage(-1));
    }

    if (nextPageBtn) {
        nextPageBtn.addEventListener('click', () => changePage(1));
    }

    // Reset catalog button
    const resetCatalogBtn = document.getElementById('resetCatalogBtn');
    if (resetCatalogBtn) {
        resetCatalogBtn.addEventListener('click', async function() {
            // Require explicit confirmation
            const confirmText = prompt('Type RESET to confirm deletion and recreation of the catalog table. This is irreversible.');
            if (confirmText !== 'RESET') {
                showAlert('Reset cancelled', 'info');
                return;
            }

            try {
                showLoading(true);
                resetCatalogBtn.disabled = true;
                const originalHtml = resetCatalogBtn.innerHTML;
                resetCatalogBtn.innerHTML = '<i class="spinner-border spinner-border-sm me-1"></i>Resetting...';

                const response = await fetch('/api/admin/coins/reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ recreate: true })
                });

                const result = await response.json();
                if (response.ok && result.success) {
                    showAlert(result.message || 'Catalog reset successfully', 'success');
                    // Clear cached UI state if any
                    try { window.uploadedCoinsData = []; } catch (e) {}
                } else {
                    showAlert(result.message || result.detail || 'Failed to reset catalog', 'danger');
                }

            } catch (error) {
                console.error('Reset error:', error);
                showAlert('Error resetting catalog. Check server logs.', 'danger');
            } finally {
                resetCatalogBtn.disabled = false;
                resetCatalogBtn.innerHTML = '<i class="fas fa-trash-alt me-1"></i>Reset Catalog';
                showLoading(false);
            }
        });
    }
}

/**
 * Handle CSV export
 */
async function handleCsvExport() {
    const exportBtn = document.getElementById('exportCsvBtn');
    
    try {
        // Show loading state
        exportBtn.disabled = true;
        exportBtn.innerHTML = '<i class="spinner-border spinner-border-sm me-1"></i>Exporting...';

        // Make request to export endpoint
        const response = await fetch('/api/admin/coins/export', {
            method: 'GET'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Export failed');
        }

        // Get the CSV content as blob
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'coins_export.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        showAlert('Coins exported successfully!', 'success');

    } catch (error) {
        console.error('Export error:', error);
        showAlert(`Export failed: ${error.message}`, 'danger');
    } finally {
        // Reset button state
        exportBtn.disabled = false;
        exportBtn.innerHTML = '<i class="fas fa-download me-1"></i>Export All Coins to CSV';
    }
}

/**
 * Handle CSV file upload
 */
async function handleCsvUpload() {
    const fileInput = document.getElementById('csvFile');
    const uploadBtn = document.getElementById('uploadCsvBtn');
    
    if (!fileInput.files.length) {
        showAlert('Please select a CSV file', 'danger');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
        // Show loading state
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<i class="spinner-border spinner-border-sm me-1"></i>Analyzing...';

        const response = await fetch('/api/admin/coins/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || 'Upload failed');
        }

        // Store uploaded data
        uploadedCoinsData = result.coins;

        // Update UI with results
        updateUploadSummary(result);
        populateCoinsPreviewTable(result.coins);
        
        // Show results section
        document.getElementById('uploadResults').style.display = 'block';
        
        showAlert('CSV file processed successfully!', 'success');

    } catch (error) {
        console.error('Upload error:', error);
        showAlert(`Upload failed: ${error.message}`, 'danger');
    } finally {
        // Reset button state
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = '<i class="fas fa-cloud-upload-alt me-1"></i>Upload and Analyze';
    }
}

/**
 * Update upload summary statistics
 */
function updateUploadSummary(result) {
    document.getElementById('totalUploaded').textContent = result.total_uploaded;
    document.getElementById('newCoins').textContent = result.new_coins;
    document.getElementById('duplicateCoins').textContent = result.duplicates;
    updateSelectedCount();
}

/**
 * Populate the coins preview table
 */
function populateCoinsPreviewTable(coins) {
    const tbody = document.getElementById('coinsPreviewTableBody');
    tbody.innerHTML = '';

    coins.forEach((coin, index) => {
        const row = document.createElement('tr');
        
        // Add class based on status
        if (coin.status === 'duplicate') {
            row.classList.add('table-warning');
        }

        row.innerHTML = `
            <td>
                <input type="checkbox" 
                       class="coin-checkbox" 
                       data-index="${index}"
                       ${coin.selected_for_import ? 'checked' : ''}
                       ${coin.status === 'duplicate' ? 'disabled' : ''} />
            </td>
            <td>
                ${coin.status === 'new' 
                    ? '<span class="badge bg-success">New</span>' 
                    : '<span class="badge bg-warning">Duplicate</span>'}
            </td>
            <td>${coin.coin_type}</td>
            <td>${coin.year}</td>
            <td>${coin.country}</td>
            <td>${coin.series}</td>
            <td>${coin.value}€</td>
            <td><code style="font-size: 0.9em; white-space: nowrap;">${coin.coin_id}</code></td>
            <td style="max-width: 150px; overflow: hidden; text-overflow: ellipsis;" title="${coin.feature || ''}">${coin.feature || '-'}</td>
            <td>
                ${coin.image_url ? 
                    `<div class="coin-image-preview">
                        <a href="${coin.image_url}" target="_blank" class="btn btn-outline-info btn-sm">
                            <i class="fas fa-image"></i>
                        </a>
                        <div class="preview-tooltip">
                            <div class="loading">
                                <i class="fas fa-spinner fa-spin"></i><br>Loading...
                            </div>
                        </div>
                    </div>` : 
                    '<span class="text-muted">-</span>'
                }
            </td>
        `;

        tbody.appendChild(row);
    });

    // Add event listeners to checkboxes
    const checkboxes = tbody.querySelectorAll('.coin-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const index = parseInt(this.dataset.index);
            uploadedCoinsData[index].selected_for_import = this.checked;
            updateSelectedCount();
        });
    });

    // Add image preview functionality if there are images
    setupImagePreviews();
}

/**
 * Select/deselect all new coins
 */
function selectAllNewCoins(select) {
    uploadedCoinsData.forEach((coin, index) => {
        if (coin.status === 'new') {
            coin.selected_for_import = select;
            const checkbox = document.querySelector(`input[data-index="${index}"]`);
            if (checkbox) {
                checkbox.checked = select;
            }
        }
    });
    
    updateSelectedCount();
    updateSelectAllCheckbox();
}

/**
 * Update selected count display
 */
function updateSelectedCount() {
    const selectedCount = uploadedCoinsData.filter(coin => coin.selected_for_import).length;
    document.getElementById('selectedForImport').textContent = selectedCount;
    
    // Enable/disable import button
    const importBtn = document.getElementById('importSelectedBtn');
    importBtn.disabled = selectedCount === 0;
    
    updateSelectAllCheckbox();
}

/**
 * Update select all checkbox state
 */
function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const newCoins = uploadedCoinsData.filter(coin => coin.status === 'new');
    const selectedNewCoins = newCoins.filter(coin => coin.selected_for_import);
    
    if (selectedNewCoins.length === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    } else if (selectedNewCoins.length === newCoins.length) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    }
}

/**
 * Handle import of selected coins
 */
async function handleImportSelected() {
    const selectedCoins = uploadedCoinsData.filter(coin => coin.selected_for_import);
    
    if (selectedCoins.length === 0) {
        showAlert('No coins selected for import', 'warning');
        return;
    }

    // Confirm import
    if (!confirm(`Are you sure you want to import ${selectedCoins.length} coins?`)) {
        return;
    }

    const importBtn = document.getElementById('importSelectedBtn');
    
    try {
        // Show loading state
        importBtn.disabled = true;
        importBtn.innerHTML = '<i class="spinner-border spinner-border-sm me-1"></i>Importing...';

        const response = await fetch('/api/admin/coins/import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(selectedCoins)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || 'Import failed');
        }

        showAlert(`Successfully imported ${result.imported_count} coins!`, 'success');
        
        // Reset the form
        resetCoinsImport();

    } catch (error) {
        console.error('Import error:', error);
        showAlert(`Import failed: ${error.message}`, 'danger');
    } finally {
        // Reset button state
        importBtn.disabled = false;
        importBtn.innerHTML = '<i class="fas fa-download me-1"></i>Import Selected';
    }
}

/**
 * Reset coins import form
 */
function resetCoinsImport() {
    // Clear file input
    document.getElementById('csvFile').value = '';
    document.getElementById('uploadCsvBtn').disabled = true;
    
    // Hide results
    document.getElementById('uploadResults').style.display = 'none';
    
    // Clear data
    uploadedCoinsData = [];
}

// ========================
// COINS VIEW FUNCTIONALITY
// ========================

/**
 * Load coins from database
 */
async function loadCoinsFromDatabase() {
    const loadBtn = document.getElementById('loadCoinsBtn');
    
    try {
        // Show loading state
        showCoinsViewLoading(true);
        loadBtn.disabled = true;
        loadBtn.innerHTML = '<i class="spinner-border spinner-border-sm me-1"></i>Loading...';

        // Reset pagination
        currentCoinsPage = 0;
        currentFilters = {};

        // Load coins
        await fetchCoinsData();
        
        // Load filter options
        await loadFilterOptions();
        
        // Show filters and table
        document.getElementById('coinsFilters').style.display = 'block';
        document.getElementById('coinsViewContainer').style.display = 'block';
        document.getElementById('coinsViewEmpty').style.display = 'none';
        
        showAlert('Coins loaded successfully!', 'success');

    } catch (error) {
        console.error('Load coins error:', error);
        showAlert(`Failed to load coins: ${error.message}`, 'danger');
    } finally {
        showCoinsViewLoading(false);
        loadBtn.disabled = false;
        loadBtn.innerHTML = '<i class="fas fa-sync me-1"></i>Load Coins';
    }
}

/**
 * Load filter options from API
 */
async function loadFilterOptions() {
    try {
        const response = await fetch('/api/admin/coins/filter-options');
        
        if (!response.ok) {
            throw new Error('Failed to load filter options');
        }

        const result = await response.json();
        
        // Populate country dropdown
        const countrySelect = document.getElementById('filterCountry');
        const currentValue = countrySelect.value; // Preserve current selection
        
        // Clear existing options except "All Countries"
        countrySelect.innerHTML = '<option value="">All Countries</option>';
        
        // Add country options
        result.countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country;
            option.textContent = country;
            if (country === currentValue) {
                option.selected = true;
            }
            countrySelect.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error loading filter options:', error);
        // Don't show alert for this, just log the error
    }
}

/**
 * Fetch coins data from API
 */
async function fetchCoinsData() {
    const params = new URLSearchParams({
        limit: currentCoinsLimit,
        offset: currentCoinsPage * currentCoinsLimit,
        ...currentFilters
    });

    const response = await fetch(`/api/admin/coins/view?${params}`);
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to load coins');
    }

    const result = await response.json();
    currentCoinsTotal = result.total;
    
    populateCoinsViewTable(result.coins);
    updatePaginationInfo();
    updatePaginationButtons();
}

/**
 * Populate the coins view table
 */
function populateCoinsViewTable(coins) {
    const tbody = document.getElementById('coinsViewTableBody');
    tbody.innerHTML = '';

    coins.forEach(coin => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <span class="badge ${coin.coin_type === 'CC' ? 'bg-warning' : 'bg-primary'}">
                    ${coin.coin_type}
                </span>
            </td>
            <td>${coin.year}</td>
            <td>${coin.country}</td>
            <td>${coin.series}</td>
            <td>${coin.value}€</td>
            <td><code style="font-size: 0.9em; white-space: nowrap;">${coin.coin_id}</code></td>
            <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;" title="${coin.feature || ''}">${coin.feature || '-'}</td>
            <td>
                ${coin.image_url ? 
                    `<div class="coin-image-preview">
                        <a href="${coin.image_url}" target="_blank" class="btn btn-outline-info btn-sm">
                            <i class="fas fa-image"></i>
                        </a>
                        <div class="preview-tooltip">
                            <div class="loading">
                                <i class="fas fa-spinner fa-spin"></i><br>Loading...
                            </div>
                        </div>
                    </div>` : 
                    '<span class="text-muted">-</span>'
                }
            </td>
        `;
        tbody.appendChild(row);
    });

    // Add image preview functionality
    setupImagePreviews();
}

/**
 * Setup image preview functionality
 */
function setupImagePreviews() {
    const imagePreviewElements = document.querySelectorAll('.coin-image-preview');
    
    imagePreviewElements.forEach(element => {
        const link = element.querySelector('a');
        const tooltip = element.querySelector('.preview-tooltip');
        const imageUrl = link ? link.getAttribute('href') : null;
        
        if (!imageUrl || !tooltip) return;
        
        let imageLoaded = false;
        let imageElement = null;
        
        element.addEventListener('mouseenter', function() {
            if (!imageLoaded) {
                // Create and load image
                imageElement = new Image();
                imageElement.onload = function() {
                    tooltip.innerHTML = `<img src="${imageUrl}" alt="Coin preview" />`;
                    imageLoaded = true;
                };
                imageElement.onerror = function() {
                    tooltip.innerHTML = `<div class="error"><i class="fas fa-exclamation-triangle"></i><br>Failed to load image</div>`;
                    imageLoaded = true;
                };
                imageElement.src = imageUrl;
            }
        });
    });
}

/**
 * Apply filters
 */
async function applyCoinsFilters() {
    const search = document.getElementById('filterSearch').value.trim();
    const country = document.getElementById('filterCountry').value;
    const type = document.getElementById('filterType').value;

    currentFilters = {};
    if (search) currentFilters.search = search;
    if (country) currentFilters.country = country;
    if (type) currentFilters.coin_type = type;

    currentCoinsPage = 0; // Reset to first page
    
    try {
        showCoinsViewLoading(true);
        await fetchCoinsData();
    } catch (error) {
        console.error('Filter error:', error);
        showAlert(`Failed to apply filters: ${error.message}`, 'danger');
    } finally {
        showCoinsViewLoading(false);
    }
}

/**
 * Clear all filters
 */
async function clearCoinsFilters() {
    document.getElementById('filterSearch').value = '';
    document.getElementById('filterCountry').value = '';
    document.getElementById('filterType').value = '';
    
    currentFilters = {};
    currentCoinsPage = 0;
    
    try {
        showCoinsViewLoading(true);
        await fetchCoinsData();
    } catch (error) {
        console.error('Clear filters error:', error);
        showAlert(`Failed to clear filters: ${error.message}`, 'danger');
    } finally {
        showCoinsViewLoading(false);
    }
}

/**
 * Change page
 */
async function changePage(direction) {
    const newPage = currentCoinsPage + direction;
    const maxPage = Math.ceil(currentCoinsTotal / currentCoinsLimit) - 1;
    
    if (newPage < 0 || newPage > maxPage) return;
    
    currentCoinsPage = newPage;
    
    try {
        showCoinsViewLoading(true);
        await fetchCoinsData();
    } catch (error) {
        console.error('Pagination error:', error);
        showAlert(`Failed to load page: ${error.message}`, 'danger');
    } finally {
        showCoinsViewLoading(false);
    }
}

/**
 * Update pagination info
 */
function updatePaginationInfo() {
    const start = currentCoinsPage * currentCoinsLimit + 1;
    const end = Math.min((currentCoinsPage + 1) * currentCoinsLimit, currentCoinsTotal);
    
    document.getElementById('coinsViewInfo').textContent = 
        `Showing ${start}-${end} of ${currentCoinsTotal} coins`;
}

/**
 * Update pagination buttons
 */
function updatePaginationButtons() {
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    const maxPage = Math.ceil(currentCoinsTotal / currentCoinsLimit) - 1;
    
    prevBtn.disabled = currentCoinsPage === 0;
    nextBtn.disabled = currentCoinsPage >= maxPage;
}

/**
 * Show/hide loading state for coins view
 */
function showCoinsViewLoading(show) {
    document.getElementById('coinsViewLoading').style.display = show ? 'block' : 'none';
    document.getElementById('coinsViewContainer').style.display = show ? 'none' : 'block';
}

// History Management Functions
let historyUploadData = [];
let currentHistoryPage = 0;
let currentHistoryLimit = 50;
let currentHistoryTotal = 0;
let currentHistoryFilters = {};

/**
 * Initialize history management functionality
 */
function initializeHistoryManagement() {
    // File upload handler
    const historyCsvFile = document.getElementById('historyCsvFile');
    if (historyCsvFile) {
        historyCsvFile.addEventListener('change', function(e) {
            const uploadBtn = document.getElementById('uploadHistoryCsvBtn');
            uploadBtn.disabled = !e.target.files[0];
        });
    }

    // Upload button handler
    const uploadHistoryCsvBtn = document.getElementById('uploadHistoryCsvBtn');
    if (uploadHistoryCsvBtn) {
        uploadHistoryCsvBtn.addEventListener('click', uploadHistoryCsv);
    }

    // Export button handler
    const exportHistoryCsvBtn = document.getElementById('exportHistoryCsvBtn');
    if (exportHistoryCsvBtn) {
        exportHistoryCsvBtn.addEventListener('click', exportHistoryCsv);
    }

    // Import buttons
    const selectAllHistoryBtn = document.getElementById('selectAllHistoryBtn');
    if (selectAllHistoryBtn) {
        selectAllHistoryBtn.addEventListener('click', () => selectAllHistoryEntries(true));
    }

    const deselectAllHistoryBtn = document.getElementById('deselectAllHistoryBtn');
    if (deselectAllHistoryBtn) {
        deselectAllHistoryBtn.addEventListener('click', () => selectAllHistoryEntries(false));
    }

    const importSelectedHistoryBtn = document.getElementById('importSelectedHistoryBtn');
    if (importSelectedHistoryBtn) {
        importSelectedHistoryBtn.addEventListener('click', importSelectedHistoryEntries);
    }

    // History view buttons
    const loadHistoryBtn = document.getElementById('loadHistoryBtn');
    if (loadHistoryBtn) {
        loadHistoryBtn.addEventListener('click', loadHistoryData);
    }

    const prevHistoryPageBtn = document.getElementById('prevHistoryPageBtn');
    if (prevHistoryPageBtn) {
        prevHistoryPageBtn.addEventListener('click', () => changeHistoryPage(-1));
    }

    const nextHistoryPageBtn = document.getElementById('nextHistoryPageBtn');
    if (nextHistoryPageBtn) {
        nextHistoryPageBtn.addEventListener('click', () => changeHistoryPage(1));
    }

    // Filter buttons
    const applyHistoryFiltersBtn = document.getElementById('applyHistoryFiltersBtn');
    if (applyHistoryFiltersBtn) {
        applyHistoryFiltersBtn.addEventListener('click', applyHistoryFilters);
    }

    const clearHistoryFiltersBtn = document.getElementById('clearHistoryFiltersBtn');
    if (clearHistoryFiltersBtn) {
        clearHistoryFiltersBtn.addEventListener('click', clearHistoryFilters);
    }

    // Checkbox handlers
    const selectAllHistoryCheckbox = document.getElementById('selectAllHistoryCheckbox');
    if (selectAllHistoryCheckbox) {
        selectAllHistoryCheckbox.addEventListener('change', function(e) {
            selectAllHistoryEntries(e.target.checked);
        });
    }
}

/**
 * Upload and analyze History CSV
 */
async function uploadHistoryCsv() {
    const fileInput = document.getElementById('historyCsvFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showAlert('Please select a CSV file', 'warning');
        return;
    }

    const uploadBtn = document.getElementById('uploadHistoryCsvBtn');
    const originalText = uploadBtn.innerHTML;
    uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Analyzing...';
    uploadBtn.disabled = true;

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/admin/history/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            historyUploadData = result.data;
            displayHistoryUploadResults(result);
            document.getElementById('historyUploadResults').style.display = 'block';
            showAlert(`Analyzed ${result.total_uploaded} history entries. ${result.new_entries} new, ${result.duplicate_entries} duplicates.`, 'success');
        } else {
            showAlert('Error uploading file: ' + result.detail, 'danger');
        }
    } catch (error) {
        console.error('Error uploading history CSV:', error);
        showAlert('Error uploading file. Please try again.', 'danger');
    } finally {
        uploadBtn.innerHTML = originalText;
        uploadBtn.disabled = false;
    }
}

/**
 * Display upload results
 */
function displayHistoryUploadResults(result) {
    // Update summary cards
    document.getElementById('totalHistoryUploaded').textContent = result.total_uploaded;
    document.getElementById('newHistoryEntries').textContent = result.new_entries;
    document.getElementById('duplicateHistoryEntries').textContent = result.duplicate_entries;
    
    // Update table
    const tableBody = document.getElementById('historyPreviewTableBody');
    tableBody.innerHTML = '';

    result.data.forEach((entry, index) => {
        const row = document.createElement('tr');
        const statusClass = entry.status === 'new' ? 'badge bg-success' : 'badge bg-warning';
        const isChecked = entry.status === 'new' ? 'checked' : '';
        
        row.innerHTML = `
            <td>
                <input type="checkbox" class="history-import-checkbox" data-index="${index}" ${isChecked} ${entry.status === 'duplicate' ? 'disabled' : ''}>
            </td>
            <td><span class="${statusClass}">${entry.status}</span></td>
            <td>${escapeHtml(entry.name)}</td>
            <td><code>${escapeHtml(entry.id)}</code></td>
            <td>${formatDate(entry.date)}</td>
        `;
        
        tableBody.appendChild(row);
    });

    // Add checkbox event listeners
    document.querySelectorAll('.history-import-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateHistoryImportSummary);
    });

    updateHistoryImportSummary();
}

/**
 * Update import summary
 */
function updateHistoryImportSummary() {
    const checkboxes = document.querySelectorAll('.history-import-checkbox:not(:disabled)');
    const checkedCount = document.querySelectorAll('.history-import-checkbox:checked').length;
    
    document.getElementById('selectedHistoryForImport').textContent = checkedCount;
    
    const importBtn = document.getElementById('importSelectedHistoryBtn');
    importBtn.disabled = checkedCount === 0;
    
    const selectAllCheckbox = document.getElementById('selectAllHistoryCheckbox');
    selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
    selectAllCheckbox.checked = checkedCount === checkboxes.length && checkboxes.length > 0;
}

/**
 * Select/deselect all history entries
 */
function selectAllHistoryEntries(select) {
    document.querySelectorAll('.history-import-checkbox:not(:disabled)').forEach(checkbox => {
        checkbox.checked = select;
    });
    updateHistoryImportSummary();
}

/**
 * Import selected history entries
 */
async function importSelectedHistoryEntries() {
    const selectedEntries = [];
    document.querySelectorAll('.history-import-checkbox:checked').forEach(checkbox => {
        const index = parseInt(checkbox.dataset.index);
        selectedEntries.push(historyUploadData[index]);
    });

    if (selectedEntries.length === 0) {
        showAlert('No entries selected for import', 'warning');
        return;
    }

    const importBtn = document.getElementById('importSelectedHistoryBtn');
    const originalText = importBtn.innerHTML;
    importBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Importing...';
    importBtn.disabled = true;

    try {
        const response = await fetch('/api/admin/history/import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(selectedEntries)
        });

        const result = await response.json();

        if (result.success) {
            showAlert(`Successfully imported ${result.imported_count} history entries`, 'success');
            document.getElementById('historyUploadResults').style.display = 'none';
            document.getElementById('historyCsvFile').value = '';
            document.getElementById('uploadHistoryCsvBtn').disabled = true;
        } else {
            showAlert('Error importing entries: ' + result.detail, 'danger');
        }
    } catch (error) {
        console.error('Error importing history entries:', error);
        showAlert('Error importing entries. Please try again.', 'danger');
    } finally {
        importBtn.innerHTML = originalText;
        importBtn.disabled = false;
    }
}

/**
 * Export history to CSV
 */
async function exportHistoryCsv() {
    const exportBtn = document.getElementById('exportHistoryCsvBtn');
    const originalText = exportBtn.innerHTML;
    exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Exporting...';
    exportBtn.disabled = true;

    try {
        const response = await fetch('/api/admin/history/export');
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'history_export.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showAlert('History exported successfully', 'success');
        } else {
            const result = await response.json();
            showAlert('Error exporting history: ' + result.detail, 'danger');
        }
    } catch (error) {
        console.error('Error exporting history:', error);
        showAlert('Error exporting history. Please try again.', 'danger');
    } finally {
        exportBtn.innerHTML = originalText;
        exportBtn.disabled = false;
    }
}

/**
 * Load history data
 */
async function loadHistoryData() {
    showHistoryViewLoading(true);
    document.getElementById('historyFilters').style.display = 'none';
    document.getElementById('historyViewEmpty').style.display = 'none';

    try {
        // Load filter options first
        await loadHistoryFilterOptions();
        
        // Load history data
        await loadHistoryPage();
        
        document.getElementById('historyFilters').style.display = 'flex';
        document.getElementById('historyViewContainer').style.display = 'block';
    } catch (error) {
        console.error('Error loading history:', error);
        showAlert('Error loading history data. Please try again.', 'danger');
        document.getElementById('historyViewEmpty').style.display = 'block';
    } finally {
        showHistoryViewLoading(false);
    }
}

/**
 * Load history filter options
 */
async function loadHistoryFilterOptions() {
    try {
        const response = await fetch('/api/admin/history/filter-options');
        const result = await response.json();
        
        if (result.success) {
            // Populate name filter
            const nameSelect = document.getElementById('filterHistoryName');
            nameSelect.innerHTML = '<option value="">All Names</option>';
            result.names.forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                nameSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading history filter options:', error);
    }
}

/**
 * Load history page
 */
async function loadHistoryPage() {
    const params = new URLSearchParams({
        page: currentHistoryPage + 1,
        limit: currentHistoryLimit,
        ...currentHistoryFilters
    });

    const response = await fetch(`/api/admin/history/view?${params}`);
    const result = await response.json();

    if (result.success) {
        currentHistoryTotal = result.pagination.total_count;
        displayHistoryData(result.data);
        updateHistoryPaginationInfo();
        updateHistoryPaginationButtons();
    } else {
        throw new Error(result.detail || 'Failed to load history');
    }
}

/**
 * Display history data in table
 */
function displayHistoryData(historyData) {
    const tableBody = document.getElementById('historyViewTableBody');
    tableBody.innerHTML = '';

    historyData.forEach(entry => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${escapeHtml(entry.name)}</td>
            <td><code>${escapeHtml(entry.id)}</code></td>
            <td>${formatDate(entry.date)}</td>
        `;
        tableBody.appendChild(row);
    });
}

/**
 * Change history page
 */
async function changeHistoryPage(direction) {
    const newPage = currentHistoryPage + direction;
    const maxPage = Math.ceil(currentHistoryTotal / currentHistoryLimit) - 1;
    
    if (newPage >= 0 && newPage <= maxPage) {
        currentHistoryPage = newPage;
        await loadHistoryPage();
    }
}

/**
 * Apply history filters
 */
async function applyHistoryFilters() {
    const search = document.getElementById('filterHistorySearch').value.trim();
    const name = document.getElementById('filterHistoryName').value;
    const dateFilter = document.getElementById('filterHistoryDate').value;

    currentHistoryFilters = {};
    if (search) currentHistoryFilters.search = search;
    if (name) currentHistoryFilters.name = name;
    if (dateFilter) currentHistoryFilters.date_filter = dateFilter;

    currentHistoryPage = 0;
    await loadHistoryPage();
}

/**
 * Clear history filters
 */
async function clearHistoryFilters() {
    document.getElementById('filterHistorySearch').value = '';
    document.getElementById('filterHistoryName').value = '';
    document.getElementById('filterHistoryDate').value = '';
    
    currentHistoryFilters = {};
    currentHistoryPage = 0;
    await loadHistoryPage();
}

/**
 * Update history pagination info
 */
function updateHistoryPaginationInfo() {
    const start = currentHistoryPage * currentHistoryLimit + 1;
    const end = Math.min((currentHistoryPage + 1) * currentHistoryLimit, currentHistoryTotal);
    
    document.getElementById('historyViewInfo').textContent = 
        `Showing ${start}-${end} of ${currentHistoryTotal} entries`;
}

/**
 * Update history pagination buttons
 */
function updateHistoryPaginationButtons() {
    const prevBtn = document.getElementById('prevHistoryPageBtn');
    const nextBtn = document.getElementById('nextHistoryPageBtn');
    const maxPage = Math.ceil(currentHistoryTotal / currentHistoryLimit) - 1;
    
    prevBtn.disabled = currentHistoryPage === 0;
    nextBtn.disabled = currentHistoryPage >= maxPage;
}

/**
 * Show/hide loading state for history view
 */
function showHistoryViewLoading(show) {
    document.getElementById('historyViewLoading').style.display = show ? 'block' : 'none';
    document.getElementById('historyViewContainer').style.display = show ? 'none' : 'block';
}

/**
 * Format date for display
 */
function formatDate(dateStr) {
    try {
        const date = new Date(dateStr);
        return date.toLocaleString();
    } catch (error) {
        return dateStr;
    }
}
