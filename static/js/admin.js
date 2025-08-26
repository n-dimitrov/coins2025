/**
 * Admin Panel JavaScript
 * Handles group and user management functionality
 */

// Global variables
let currentSelectedGroupId = null;
let currentSelectedGroupKey = null;
let currentSelectedGroupName = null;

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
