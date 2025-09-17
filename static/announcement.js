// Announcement management for FoodFast
// Handles employee announcement creation and customer viewing

// API endpoints for announcements
const ANNOUNCEMENT_API = {
  create: '/api/v1/announcements',
  list: '/api/v1/announcements',
  stream: '/api/v1/announcements/stream'
};

// Global variables for announcements
let announcementSSE = null;

// Employee Announcement Functions
function initEmployeeAnnouncements() {
  console.log('Initializing employee announcement features');
  
  // Load existing announcements to display
  loadExistingAnnouncementsForEmployee();
  
  // Set up event listeners for the form that's already in the HTML
  setupEmployeeAnnouncementEventListeners();
}

function setupEmployeeAnnouncementEventListeners() {
  // Event listeners are handled by onclick attributes in the HTML
  console.log('Employee announcement event listeners ready');
}

async function loadExistingAnnouncementsForEmployee() {
  console.log('Loading existing announcements for employee view');
  
  try {
    const result = await apiFetch(ANNOUNCEMENT_API.list);
    console.log('Announcements response for employee:', result);
    
    if (result.success && result.data && result.data.length > 0) {
      displayAnnouncementsForEmployee(result.data);
    } else {
      displayNoAnnouncementsForEmployee();
    }
  } catch (error) {
    console.error('Failed to load announcements for employee:', error);
    displayAnnouncementErrorForEmployee();
  }
}

function displayAnnouncementsForEmployee(announcements) {
  const listEl = document.getElementById('announcementsList');
  if (!listEl) return;
  
  listEl.innerHTML = '';
  
  announcements.forEach(announcement => {
    const announcementEl = document.createElement('div');
    announcementEl.style.cssText = `
      background: white;
      border-radius: 8px;
      padding: 1rem;
      margin-bottom: 0.75rem;
      border-left: 4px solid var(--primary-orange);
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    `;
    
    const timeAgo = announcement.created_at ? 
      new Date(announcement.created_at).toLocaleString() : 
      'Just now';
    
    announcementEl.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
        <h4 style="margin: 0; color: var(--gray-800); font-size: 1rem;">
          ${announcement.title || 'Announcement'}
        </h4>
        <span style="background: var(--success); color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">
          📤 Sent
        </span>
      </div>
      
      <p style="margin: 0 0 0.75rem 0; color: var(--gray-600); line-height: 1.4; font-size: 0.875rem;">
        ${announcement.message || 'No message available'}
      </p>
      
      <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; color: var(--gray-500);">
        <span>🏪 ${announcement.restaurant_name || 'General'}</span>
        <span>🕒 ${timeAgo}</span>
      </div>
    `;
    
    listEl.appendChild(announcementEl);
  });
  
  console.log(`Displayed ${announcements.length} announcements for employee`);
}

function displayNoAnnouncementsForEmployee() {
  const listEl = document.getElementById('announcementsList');
  if (!listEl) return;
  
  listEl.innerHTML = `
    <div style="color: var(--gray-400); font-size: 2rem; margin-bottom: 0.5rem;">📢</div>
    <p style="margin: 0; color: var(--gray-600); font-weight: 500;">No announcements yet</p>
    <p style="margin: 0.25rem 0 0 0; color: var(--gray-500); font-size: 0.875rem;">
      Create your first announcement above
    </p>
  `;
}

function displayAnnouncementErrorForEmployee() {
  const listEl = document.getElementById('announcementsList');
  if (!listEl) return;
  
  listEl.innerHTML = `
    <div style="text-align: center; color: var(--error); padding: 1rem;">
      ⚠️ Failed to load announcements
    </div>
  `;
}

// Functions for employees and customers

function toggleAnnouncementForm() {
  const form = document.getElementById('announcementForm');
  const button = document.getElementById('createAnnouncementBtn');
  
  if (!form || !button) {
    console.error('Announcement form or button not found');
    return;
  }
  
  if (form.style.display === 'none' || form.style.display === '') {
    form.style.display = 'block';
    button.innerHTML = '<i class="fas fa-minus"></i> 🔼 Hide Announcement Form';
    button.classList.remove('btn-primary');
    button.classList.add('btn-secondary');
  } else {
    form.style.display = 'none';
    button.innerHTML = '<i class="fas fa-plus"></i> ➕ Create New Announcement';
    button.classList.remove('btn-secondary');
    button.classList.add('btn-primary');
    clearAnnouncementForm();
  }
}

function clearAnnouncementForm() {
  const titleEl = document.getElementById('announcementTitle');
  const messageEl = document.getElementById('announcementMessage');
  const restaurantEl = document.getElementById('announcementRestaurant');
  
  if (titleEl) titleEl.value = '';
  if (messageEl) messageEl.value = '';
  if (restaurantEl) restaurantEl.value = '';
  
  hideAnnouncementStatus();
}

function cancelAnnouncementForm() {
  const form = document.getElementById('announcementForm');
  const button = document.getElementById('createAnnouncementBtn');
  
  if (form) {
    form.style.display = 'none';
  }
  if (button) {
    button.innerHTML = '<i class="fas fa-plus"></i> ➕ Create New Announcement';
    button.classList.remove('btn-secondary');
    button.classList.add('btn-primary');
  }
  clearAnnouncementForm();
}

// Update the createAnnouncement function to refresh the employee list
async function createAnnouncement() {
  const titleEl = document.getElementById('announcementTitle');
  const messageEl = document.getElementById('announcementMessage');
  const restaurantEl = document.getElementById('announcementRestaurant');
  
  if (!titleEl || !messageEl) {
    showAnnouncementStatus('Form elements not found', 'error');
    return;
  }
  
  const title = titleEl.value.trim();
  const message = messageEl.value.trim();
  const restaurant = restaurantEl ? restaurantEl.value.trim() : '';
  
  // Validation
  if (!title) {
    showAnnouncementStatus('Please enter an announcement title', 'error');
    return;
  }
  
  if (!message) {
    showAnnouncementStatus('Please enter an announcement message', 'error');
    return;
  }
  
  if (title.length > 100) {
    showAnnouncementStatus('Title must be less than 100 characters', 'error');
    return;
  }
  
  if (message.length > 500) {
    showAnnouncementStatus('Message must be less than 500 characters', 'error');
    return;
  }
  
  const announcementData = {
    title: title,
    message: message,
    restaurant_name: restaurant || 'General',
    created_by: 'employee' // This could be dynamic based on logged-in user
  };
  
  console.log('Creating announcement:', announcementData);
  showAnnouncementStatus('Creating announcement...', 'info');
  
  try {
    // Use the same apiFetch function from app.js
    const result = await apiFetch(ANNOUNCEMENT_API.create, {
      method: 'POST',
      body: JSON.stringify(announcementData)
    });
    
    console.log('Announcement creation response:', result);
    
    if (result.success) {
      showAnnouncementStatus(`✅ Announcement "${title}" sent successfully!`, 'success');
      clearAnnouncementForm();
      
      // Refresh the announcements list for employee
      loadExistingAnnouncementsForEmployee();
      
      // Show success notification
      if (typeof showToast === 'function') {
        showToast(`📢 Announcement "${title}" broadcast to all customers!`, 'success');
      }
      
      // Hide form after successful creation
      setTimeout(() => {
        cancelAnnouncementForm();
      }, 2000);
      
    } else {
      showAnnouncementStatus(`❌ Failed to create announcement: ${result.message || 'Unknown error'}`, 'error');
    }
  } catch (error) {
    console.error('Announcement creation error:', error);
    showAnnouncementStatus('❌ Network error while creating announcement', 'error');
  }
}

function showAnnouncementStatus(message, type) {
  const statusEl = document.getElementById('announcementStatus');
  if (!statusEl) return;
  
  statusEl.style.display = 'block';
  statusEl.textContent = message;
  
  // Style based on type
  const colors = {
    success: { bg: '#d1fae5', text: '#065f46', border: '#10b981' },
    error: { bg: '#fee2e2', text: '#991b1b', border: '#ef4444' },
    info: { bg: '#dbeafe', text: '#1e40af', border: '#3b82f6' }
  };
  
  const color = colors[type] || colors.info;
  statusEl.style.backgroundColor = color.bg;
  statusEl.style.color = color.text;
  statusEl.style.border = `1px solid ${color.border}`;
  
  // Auto-hide after 5 seconds for success/info
  if (type === 'success' || type === 'info') {
    setTimeout(() => hideAnnouncementStatus(), 5000);
  }
}

function hideAnnouncementStatus() {
  const statusEl = document.getElementById('announcementStatus');
  if (statusEl) {
    statusEl.style.display = 'none';
  }
}

// Customer Announcement Functions
function initCustomerAnnouncements() {
  console.log('Initializing customer announcement features');
  
  // Load existing announcements from database
  loadExistingAnnouncements();
  
  // Set up SSE for real-time announcements
  setupAnnouncementSSE();
  
  // Add announcement display area to customer page
  addAnnouncementDisplayToCustomer();
}

function addAnnouncementDisplayToCustomer() {
  // Find a suitable container in the customer page
  const container = document.querySelector('.main-content') || document.body;
  
  // Create announcement display section
  const announcementDisplay = document.createElement('div');
  announcementDisplay.id = 'customerAnnouncementSection';
  announcementDisplay.style.cssText = `
    background: linear-gradient(135deg, #eff6ff, #dbeafe);
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
    border: 1px solid #93c5fd;
    box-shadow: 0 4px 6px rgba(59,130,246,0.1);
  `;
  
  announcementDisplay.innerHTML = `
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
      <h3 style="margin: 0; color: #1e40af; display: flex; align-items: center;">
        📢 Restaurant Announcements
      </h3>
      <div id="announcementBadge" style="background: #3b82f6; color: white; padding: 0.25rem 0.75rem; 
                                         border-radius: 12px; font-size: 0.75rem; margin-left: 1rem;
                                         display: none;">
        🔴 Live
      </div>
    </div>
    
    <div id="announcementsList" style="max-height: 300px; overflow-y: auto;">
      <div style="text-align: center; color: #6b7280; padding: 2rem;">
        📭 Loading announcements...
      </div>
    </div>
  `;
  
  // Insert at the top of the main content
  const firstChild = container.firstChild;
  if (firstChild) {
    container.insertBefore(announcementDisplay, firstChild);
  } else {
    container.appendChild(announcementDisplay);
  }
}

async function loadExistingAnnouncements() {
  console.log('Loading existing announcements from database');
  
  try {
    const result = await apiFetch(ANNOUNCEMENT_API.list);
    console.log('Announcements response:', result);
    
    if (result.success && result.data) {
      displayAnnouncements(result.data, false); // false = not real-time
    } else {
      displayNoAnnouncements();
    }
  } catch (error) {
    console.error('Failed to load announcements:', error);
    displayAnnouncementError();
  }
}

function displayAnnouncements(announcements, isRealTime = false) {
  const listEl = document.getElementById('announcementsList');
  if (!listEl) return;
  
  if (!announcements || announcements.length === 0) {
    displayNoAnnouncements();
    return;
  }
  
  // If real-time, prepend to existing announcements
  if (isRealTime) {
    announcements.forEach(announcement => {
      addAnnouncementToDisplay(announcement, true);
    });
  } else {
    // Replace all announcements
    listEl.innerHTML = '';
    announcements.forEach(announcement => {
      addAnnouncementToDisplay(announcement, false);
    });
  }
  
  console.log(`Displayed ${announcements.length} announcements`);
}

function addAnnouncementToDisplay(announcement, isNew = false) {
  const listEl = document.getElementById('announcementsList');
  if (!listEl) return;
  
  const announcementEl = document.createElement('div');
  announcementEl.className = 'announcement-item';
  announcementEl.style.cssText = `
    background: white;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    border-left: 4px solid #3b82f6;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
    ${isNew ? 'animation: slideInFade 0.5s ease-out;' : ''}
  `;
  
  if (isNew) {
    announcementEl.style.background = '#fef3c7';
    announcementEl.style.borderLeftColor = '#f59e0b';
    
    // Reset to normal colors after animation
    setTimeout(() => {
      announcementEl.style.background = 'white';
      announcementEl.style.borderLeftColor = '#3b82f6';
    }, 3000);
  }
  
  const timeAgo = announcement.created_at ? 
    new Date(announcement.created_at).toLocaleString() : 
    'Just now';
  
  announcementEl.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
      <h4 style="margin: 0; color: #1f2937; font-size: 1.1rem; flex: 1;">
        ${announcement.title || 'Announcement'}
      </h4>
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        ${isNew ? '<span style="background: #f59e0b; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">🆕 NEW</span>' : ''}
        <button onclick="this.closest('.announcement-item').remove()" 
                style="background: #dc2626; color: white; border: none; padding: 0.25rem 0.5rem; 
                       border-radius: 4px; cursor: pointer; font-size: 0.75rem; margin-left: 0.5rem;"
                title="Close announcement">
          ✕
        </button>
      </div>
    </div>
    
    <p style="margin: 0 0 0.75rem 0; color: #374151; line-height: 1.5;">
      ${announcement.message || 'No message available'}
    </p>
    
    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.875rem; color: #6b7280;">
      <span>🏪 ${announcement.restaurant_name || 'General'}</span>
      <span>🕒 ${timeAgo}</span>
    </div>
  `;
  
  // Add CSS animation for new announcements
  if (isNew && !document.getElementById('announcementAnimationCSS')) {
    const style = document.createElement('style');
    style.id = 'announcementAnimationCSS';
    style.textContent = `
      @keyframes slideInFade {
        0% { opacity: 0; transform: translateY(-20px); }
        100% { opacity: 1; transform: translateY(0); }
      }
    `;
    document.head.appendChild(style);
  }
  
  // Insert at the top for new announcements, at the bottom for existing
  if (isNew) {
    listEl.insertBefore(announcementEl, listEl.firstChild);
    
    // Show notification
    if (typeof showToast === 'function') {
      showToast(`📢 New announcement: ${announcement.title}`, 'info');
    }
  } else {
    listEl.appendChild(announcementEl);
  }
}

function displayNoAnnouncements() {
  const listEl = document.getElementById('announcementsList');
  if (!listEl) return;
  
  listEl.innerHTML = `
    <div style="text-align: center; color: #6b7280; padding: 2rem;">
      📭 No announcements available
    </div>
  `;
}

function displayAnnouncementError() {
  const listEl = document.getElementById('announcementsList');
  if (!listEl) return;
  
  listEl.innerHTML = `
    <div style="text-align: center; color: #dc2626; padding: 2rem;">
      ⚠️ Failed to load announcements
    </div>
  `;
}

function setupAnnouncementSSE() {
  console.log('Setting up SSE for real-time announcements');
  
  try {
    announcementSSE = new EventSource(ANNOUNCEMENT_API.stream);
    
    announcementSSE.onopen = function(event) {
      console.log('Announcement SSE connected');
      const badge = document.getElementById('announcementBadge');
      if (badge) {
        badge.style.display = 'inline-block';
        badge.textContent = '🟢 Live';
      }
    };
    
    announcementSSE.onmessage = function(event) {
      console.log('New announcement received via SSE:', event.data);
      
      try {
        const data = JSON.parse(event.data);
        console.log('Parsed SSE data:', data);
        
        // Extract the nested announcement object
        let announcement = data;
        if (data.announcement) {
          announcement = data.announcement;
          console.log('Extracted nested announcement:', announcement);
        }
        
        // Add to display as new announcement
        addAnnouncementToDisplay(announcement, true);
        
      } catch (error) {
        console.error('Error parsing announcement SSE data:', error);
      }
    };
    
    announcementSSE.onerror = function(event) {
      console.error('Announcement SSE error:', event);
      const badge = document.getElementById('announcementBadge');
      if (badge) {
        badge.style.display = 'inline-block';
        badge.textContent = '🔴 Offline';
        badge.style.background = '#dc2626';
      }
    };
    
  } catch (error) {
    console.error('Failed to setup announcement SSE:', error);
  }
}

function closeAnnouncementSSE() {
  if (announcementSSE) {
    announcementSSE.close();
    announcementSSE = null;
    console.log('Announcement SSE connection closed');
  }
}

// Initialize based on page and user role
function initAnnouncements() {
  // Wait for the page to be ready and auth to be available
  setTimeout(() => {
    if (typeof auth !== 'undefined' && auth.user) {
      if (auth.user.role === 'employee') {
        initEmployeeAnnouncements();
      } else {
        initCustomerAnnouncements();
      }
    } else {
      console.log('Auth not available, retrying announcement initialization...');
      // Retry after a short delay
      setTimeout(initAnnouncements, 1000);
    }
  }, 500);
}

// Auto-initialize when the script loads
document.addEventListener('DOMContentLoaded', () => {
  console.log('Announcement.js loaded');
  initAnnouncements();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  closeAnnouncementSSE();
});