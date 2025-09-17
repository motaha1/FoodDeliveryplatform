// Minimal frontend helper for FoodFast
// Auto-detect environment for Socket.IO connections
function getSocketIOUrl() {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  
  // If running on Azure
  if (hostname.includes('azurewebsites.net')) {
    return `${protocol}//${hostname}`;
  }
  
  // If running locally
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return `${protocol}//${hostname}:5000`;
  }
  
  // Default to current host
  return `${protocol}//${window.location.host}`;
}

// Endpoints base assumptions (same Flask app serves all blueprints)
const API = {
  register: '/api/v1/account/register',
  login: '/api/v1/account/login',
  refresh: '/api/v1/account/refresh',
  profile: '/api/v1/account/profile',
  orders: '/api/v1/orders',
  allOrders: '/api/v1/orders/all',
  ordersOf: (cid)=>`/api/v1/orders/customer/${cid}`,
  track: (oid,last)=>`/api/v1/orders/${oid}/track${last?`?last_status=${encodeURIComponent(last)}&timeout=45`:''}`,
  sseLocation: (oid,cid)=>`/api/v1/tracking/order/${oid}/stream?customer_id=${cid}`,
  ordersSSE: '/api/v1/orders/stream',
  driverOnline: (id)=>`/api/v1/drivers/${id}/online`,
  driverLoc: (id)=>`/api/v1/drivers/${id}/location`
}

// Cookie helpers
function setCookie(name, value, days=1) {
  const expires = new Date(Date.now()+days*864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}
function getCookie(name){
  return document.cookie.split('; ').reduce((r,v)=>{
    const [k,...rest]=v.split('=');
    if(k===name) r=decodeURIComponent(rest.join('='));
    return r;
  },'');
}
function deleteCookie(name){ document.cookie = `${name}=; Max-Age=0; path=/`; }

let auth = {
  user: null,
  access: getCookie('access_token'),
  refresh: getCookie('refresh_token')
};

// Global helpers
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.style.cssText = `
    position: fixed; top: 20px; right: 20px; z-index: 9999;
    background: ${type === 'success' ? '#059669' : type === 'error' ? '#dc2626' : '#3b82f6'};
    color: white; padding: 12px 24px; border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transition: all 0.3s ease;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => document.body.removeChild(toast), 300);
  }, 3000);
}

// Enhanced notification for order creation
function showOrderCreatedNotification(orderNumber, restaurantName, totalAmount) {
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
    background: linear-gradient(135deg, #059669, #10b981); color: white;
    padding: 2rem; border-radius: 16px; z-index: 10000;
    box-shadow: 0 20px 40px rgba(0,0,0,0.3);
    text-align: center; min-width: 300px; max-width: 400px;
    animation: slideInScale 0.4s ease-out;
  `;
  
  notification.innerHTML = `
    <div style="font-size: 3rem; margin-bottom: 1rem;">🎉</div>
    <h2 style="margin: 0 0 0.5rem 0; font-size: 1.5rem;">Order Placed Successfully!</h2>
    <div style="font-size: 1.1rem; margin-bottom: 1rem;">
      <strong>Order #${orderNumber}</strong><br>
      ${restaurantName} • $${totalAmount}
    </div>
    <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 1.5rem;">
      You'll receive real-time updates as your order progresses
    </div>
    <button onclick="this.parentElement.remove()" 
            style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); 
                   color: white; padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer;
                   font-size: 1rem; transition: all 0.2s ease;">
      Got it! 👍
    </button>
  `;
  
  // Add CSS animation
  if (!document.getElementById('orderNotificationCSS')) {
    const style = document.createElement('style');
    style.id = 'orderNotificationCSS';
    style.textContent = `
      @keyframes slideInScale {
        0% { transform: translate(-50%, -50%) scale(0.8); opacity: 0; }
        100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
      }
      @keyframes urgentPulse {
        0%, 100% { transform: translate(-50%, -50%) scale(1); }
        50% { transform: translate(-50%, -50%) scale(1.02); }
      }
    `;
    document.head.appendChild(style);
  }
  
  document.body.appendChild(notification);
  
  // Auto-remove after 8 seconds
  setTimeout(() => {
    if (notification.parentElement) {
      notification.style.transition = 'all 0.3s ease';
      notification.style.opacity = '0';
      notification.style.transform = 'translate(-50%, -50%) scale(0.9)';
      setTimeout(() => notification.remove(), 300);
    }
  }, 8000);
}

// Enhanced notification for employees when new order arrives
function showNewOrderEmployeeNotification(orderNumber, restaurantName, totalAmount, orderData) {
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
    background: linear-gradient(135deg, #f59e0b, #f97316); color: white;
    padding: 2rem; border-radius: 16px; z-index: 10000;
    box-shadow: 0 20px 40px rgba(0,0,0,0.3);
    text-align: center; min-width: 350px; max-width: 450px;
    animation: urgentPulse 2s ease-in-out infinite;
    border: 3px solid #fbbf24;
  `;
  
  const deliveryAddress = orderData.delivery_address || 'Address not provided';
  const timeNow = new Date().toLocaleTimeString();
  
  notification.innerHTML = `
    <div style="font-size: 3rem; margin-bottom: 1rem;">🚨</div>
    <h2 style="margin: 0 0 0.5rem 0; font-size: 1.6rem;">New Order Alert!</h2>
    <div style="font-size: 1.2rem; margin-bottom: 1rem; background: rgba(255,255,255,0.2); 
                padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.3);">
      <strong>Order #${orderNumber}</strong><br>
      🍽️ ${restaurantName}<br>
      💰 $${totalAmount}<br>
      📍 ${deliveryAddress}<br>
      🕒 ${timeNow}
    </div>
    <div style="font-size: 0.95rem; opacity: 0.95; margin-bottom: 1.5rem; 
                background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 6px;">
      ⚠️ This order needs immediate attention!
    </div>
    <div style="display: flex; gap: 0.75rem; justify-content: center;">
      <button onclick="this.parentElement.parentElement.remove()" 
              style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); 
                     color: white; padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer;
                     font-size: 1rem; transition: all 0.2s ease;">
        Acknowledge ✓
      </button>
      <button onclick="scrollToOrder(${orderNumber}); this.parentElement.parentElement.remove();" 
              style="background: rgba(255,255,255,0.9); border: 1px solid rgba(255,255,255,0.3); 
                     color: #f59e0b; padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer;
                     font-size: 1rem; transition: all 0.2s ease; font-weight: bold;">
        View Order 👀
      </button>
    </div>
  `;
  
  document.body.appendChild(notification);
  
  // Auto-remove after 12 seconds (longer for employee notifications)
  setTimeout(() => {
    if (notification.parentElement) {
      notification.style.transition = 'all 0.3s ease';
      notification.style.opacity = '0';
      notification.style.transform = 'translate(-50%, -50%) scale(0.9)';
      setTimeout(() => notification.remove(), 300);
    }
  }, 12000);
  
  // Play notification sound (if browser allows)
  try {
    const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmQeBC+H0fPTgjMGHH/P8tmJOgocXq/v7a5VFQhGneH0wWcgBTuB0fPPlz4KCl+n7O6wWRIHXq7q8a5YEQ');
    audio.play().catch(() => {}); // Silent fail if audio not allowed
  } catch (e) {
    // Silent fail
  }
}

// Helper function to scroll to a specific order
function scrollToOrder(orderNumber) {
  const statusElement = document.getElementById(`status_${orderNumber}`);
  if (statusElement) {
    statusElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    // Highlight the order briefly
    const orderItem = statusElement.closest('.item');
    if (orderItem) {
      const originalBackground = orderItem.style.background;
      orderItem.style.background = '#fef3c7';
      orderItem.style.transition = 'background 0.3s ease';
      setTimeout(() => {
        orderItem.style.background = originalBackground;
      }, 2000);
    }
  }
}

// Auth helpers
async function apiFetch(url, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (auth.access) headers['Authorization'] = `Bearer ${auth.access}`;
  
  const res = await fetch(url, { ...options, headers });
  if (res.status === 401 && auth.refresh) {
    try {
      const refreshRes = await fetch(API.refresh, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${auth.refresh}` }
      });
      if (refreshRes.ok) {
        const authData = await refreshRes.json();
        auth.access = authData.access_token;
        setCookie('access_token', auth.access, 1);
        headers['Authorization'] = `Bearer ${auth.access}`;
        const retryRes = await fetch(url, {...options, headers});
        return retryRes.json();
      }
    } catch (e) {
      deleteCookie('access_token');
      deleteCookie('refresh_token');
      sessionStorage.removeItem('user');
      window.location.href = '/';
      throw e;
    }
  }
  return res.json();
}

// Global variables for SSE and chat
let sse = null;
let sseOrders = null;
let ioScriptLoaded = false, socket = null, currentChatId = null;

function ensureSocketIO(){
  return Promise.resolve(); // SocketIO already loaded via CDN in HTML
}

async function initCustomerChat(){
  await ensureSocketIO();
  socket = io(getSocketIOUrl());
  const name = (auth.user?.email||'user').split('@')[0];
  socket.on('connect', ()=>{ 
    console.log('Socket connected, sending handshake for user:', name);
    socket.emit('customer_handshake', {user:name}); 
  });
  socket.on('customer_chat', (payload)=>{
    console.log('Customer chat received:', payload);
    currentChatId = payload.chat_id;
    console.log('Current chat ID set to:', currentChatId);
    const box = document.getElementById('chatMessages'); box.innerHTML='';
    (payload.history||[]).forEach(m=>appendMsg(box, m, name));
  });
  socket.on('message', (m)=>{ 
    const box = document.getElementById('chatMessages'); 
    const isNewAgentMessage = m.role === 'employee';
    appendMsg(box, m, name, isNewAgentMessage); 
  });
  document.getElementById('chatSend').onclick = ()=>{
    const input = document.getElementById('chatInput'); 
    const text = input.value.trim(); 
    console.log('Send clicked:', {text, currentChatId, socket: !!socket});
    
    if(!text) {
      alert('Please enter a message');
      return;
    }
    if(!currentChatId) {
      alert('Chat not initialized. Please refresh the page.');
      return;
    }
    if(!socket || !socket.connected) {
      alert('Not connected to chat server. Please refresh the page.');
      return;
    }
    
    console.log('Sending message:', {chat_id: currentChatId, text, role:'customer', user:name});
    socket.emit('send_message', {chat_id: currentChatId, text, role:'customer', user:name});
    input.value='';
  };
  const input = document.getElementById('chatInput');
  let typing=false, to=null;
  input.addEventListener('input', ()=>{
    if(!typing){ typing=true; socket.emit('typing',{chat_id:currentChatId,user:name,is_typing:true}); }
    clearTimeout(to); to=setTimeout(()=>{ typing=false; socket.emit('typing',{chat_id:currentChatId,user:name,is_typing:false}); }, 800);
  });
  socket.on('typing_status', (d)=>{ document.getElementById('typing').textContent = d.users.length? `${d.users.join(', ')} typing...`:''; });
}

function appendMsg(container, m, my, showNotification = false){
  const div = document.createElement('div');
  const me = m.role==='customer' && (m.sender||my)===my ? 'me':'other';
  div.className = `bubble ${me}`;
  div.innerHTML = `<strong>${m.role === 'customer' ? 'You' : 'Agent'}:</strong> ${m.text}`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  
  if (showNotification) {
    showToast('New message from support agent', 'info');
  }
}

// Driver location SSE
function startLocationStream(){
  const orderId = parseInt(document.getElementById('trackOrderId').value||'0');
  const driverId = parseInt(document.getElementById('driverId').value||'1');
  console.log('Starting location stream:', {orderId, driverId, user: auth.user?.id});
  
  if(!orderId) {
    alert('Please enter an Order ID to track');
    return;
  }
  
  // Use mock customer ID if user not logged in
  const customerId = auth.user?.id || 1;
  console.log('Using customer ID:', customerId);
  
  stopLocationStream();
  const url = API.sseLocation(orderId, customerId);
  console.log('SSE URL:', url);
  sse = new EventSource(url);
  const log = document.getElementById('locLog');
  sse.onmessage = (e)=>{
    console.log('SSE message received:', e.data);
    try{ 
      const d = JSON.parse(e.data); 
      console.log('SSE parsed data:', d);
      if (d.latitude && d.longitude) {
        updateMarker(d.latitude, d.longitude); 
        log.textContent = `[${new Date().toLocaleTimeString()}] Driver moved to: ${d.latitude.toFixed(6)}, ${d.longitude.toFixed(6)}\n`+log.textContent;
      } else {
        log.textContent = `[${new Date().toLocaleTimeString()}] ${e.data}\n`+log.textContent;
      }
    }catch(err){
      console.error('Error parsing SSE data:', err, 'Raw data:', e.data);
      log.textContent = `[${new Date().toLocaleTimeString()}] Error: ${e.data}\n`+log.textContent;
    }
  };
  sse.onopen = ()=>{ 
    console.log('SSE connected');
    log.textContent = 'SSE connected\n'+log.textContent; 
  };
  sse.onerror = (e)=>{ 
    console.error('SSE error:', e);
    log.textContent = 'SSE error\n'+log.textContent; 
  };
  startDriverSimulation(driverId, orderId);
}

function stopLocationStream(){ 
  if(sse){ 
    sse.close(); 
    sse=null; 
  } 
  stopDriverSimulation(); 
}

function updateMarker(lat, lng){
  const mk = document.getElementById('marker');
  if (!mk) {
    console.error('Marker element not found!');
    return;
  }
  
  const centerLat = 31.95;
  const centerLng = 35.91;
  const range = 0.02;
  
  const mapEl = document.getElementById('map');
  if (!mapEl) {
    console.warn('Map element not found');
    return;
  }
  
  const rect = mapEl.getBoundingClientRect();
  console.log('Map dimensions:', rect.width, 'x', rect.height);
  
  // Calculate marker position as percentage of map
  const x = ((lng - (centerLng - range/2)) / range) * rect.width;
  const y = ((centerLat + range/2 - lat) / range) * rect.height;
  
  // Clamp to map boundaries
  const clampedX = Math.max(10, Math.min(rect.width-10, x));
  const clampedY = Math.max(10, Math.min(rect.height-10, y));
  
  console.log('Marker position:', { lat, lng, x: clampedX, y: clampedY });
  
  // Set position directly without accounting for transform (CSS handles centering)
  mk.style.left = clampedX + 'px';
  mk.style.top = clampedY + 'px';
  mk.style.display = 'block';
  mk.style.position = 'absolute';
  
  console.log('Marker updated to:', mk.style.left, mk.style.top);
}

let driverSim = null;
function startDriverSimulation(driverId, orderId) {
  console.log('Starting driver simulation for driver', driverId, 'order', orderId);
  if(driverSim) {
    console.log('Clearing existing driver simulation');
    clearInterval(driverSim);
  }
  
  let lat = 31.95 + (Math.random()-0.5)*0.02;
  let lng = 35.91 + (Math.random()-0.5)*0.02;
  console.log('Initial driver position:', {lat, lng});
  
  driverSim = setInterval(async () => {
    lat += (Math.random()-0.5)*0.01; // Even bigger movement - 5x more than before
    lng += (Math.random()-0.5)*0.01; // Should be very visible now
    console.log('*** DRIVER MOVING ***', {lat, lng, time: new Date().toLocaleTimeString()});
    
    try {
      await apiFetch(API.driverLoc(driverId), {
        method: 'POST',
        body: JSON.stringify({ latitude: lat, longitude: lng, order_id: orderId })
      });
      console.log('Driver location update sent successfully');
    } catch(e) {
      console.error('Driver simulation error:', e);
    }
  }, 15000);
}

function stopDriverSimulation() {
  if(driverSim) {
    console.log('Stopping driver simulation');
    clearInterval(driverSim);
    driverSim = null;
  }
}

// Customer functions
async function initCommon() {
  // Initialize auth object from cookies
  auth.access = getCookie('access_token');
  auth.refresh = getCookie('refresh_token');
  
  // Get user from both sessionStorage and cookies
  let userStr = sessionStorage.getItem('user');
  if (!userStr) {
    userStr = getCookie('user');
  }
  
  if (userStr) {
    try {
      auth.user = JSON.parse(userStr);
      // Store in sessionStorage for consistency
      sessionStorage.setItem('user', JSON.stringify(auth.user));
    } catch (e) {
      console.error('Error parsing user data:', e);
    }
  }
  
  // If no user but we have tokens, try to fetch profile
  if (!auth.user && (auth.access || auth.refresh)) {
    try {
      const data = await apiFetch(API.profile);
      if (data.success) {
        auth.user = data.data;
        sessionStorage.setItem('user', JSON.stringify(auth.user));
        setCookie('user', JSON.stringify(auth.user), 7);
      }
    } catch (e) {
      console.error('Failed to load user profile:', e);
    }
  }
  
  document.getElementById('logoutBtn')?.addEventListener('click', () => {
    deleteCookie('access_token');
    deleteCookie('refresh_token');
    sessionStorage.removeItem('user');
    window.location.href = '/';
  });
}

async function loadProfile() {
  try {
    const data = await apiFetch(API.profile);
    if (data.success) {
      const u = data.data;
      document.getElementById('firstName').value = u.first_name || '';
      document.getElementById('lastName').value = u.last_name || '';
      document.getElementById('email').value = u.email || '';
    }
  } catch (e) {
    showToast('Failed to load profile', 'error');
  }
}

async function saveProfile(e) {
  e.preventDefault();
  const form = e.target;
  const data = {
    first_name: form.firstName.value,
    last_name: form.lastName.value,
    email: form.email.value
  };
  
  try {
    const result = await apiFetch(API.profile, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
    if (result.success) {
      showToast('Profile updated successfully', 'success');
      auth.user = result.data;
      sessionStorage.setItem('user', JSON.stringify(auth.user));
    } else {
      showToast(result.message || 'Failed to update profile', 'error');
    }
  } catch (e) {
    showToast('Failed to update profile', 'error');
  }
}

async function createOrder(e) {
  e.preventDefault();
  const form = e.target;
  
  console.log('createOrder called, auth.user:', auth.user);
  
  if (!auth.user?.id) {
    showToast('Please login first', 'error');
    console.log('No user ID for order creation');
    return;
  }
  
  const data = {
    customer_id: auth.user.id,
    items: form.items.value ? form.items.value.split(',').map(item => item.trim()) : [],
    delivery_address: form.deliveryAddress.value,
    restaurant_name: form.restaurantName.value || 'Default Restaurant',
    total_amount: parseFloat(form.totalAmount.value) || 0
  };
  
  console.log('Order data to send:', data);
  
  // Validate required fields
  if (!data.delivery_address) {
    showToast('Delivery address is required', 'error');
    return;
  }
  
  if (!data.total_amount || data.total_amount <= 0) {
    showToast('Please enter a valid total amount', 'error');
    return;
  }
  
  if (!data.items.length || (data.items.length === 1 && !data.items[0])) {
    showToast('Please enter order items', 'error');
    return;
  }
  
  try {
    const result = await apiFetch(API.orders, {
      method: 'POST',
      body: JSON.stringify(data)
    });
    console.log('Order creation response:', result);
    
    if (result.success) {
      // Show enhanced success notification with order details
      const orderNumber = result.data?.id || 'N/A';
      showToast(`🎉 Order #${orderNumber} created successfully! You'll receive updates as it progresses.`, 'success');
      
      // Show a more prominent notification overlay
      showOrderCreatedNotification(orderNumber, data.restaurant_name, data.total_amount);
      
      form.reset();
      listOrders(); // Refresh the orders list
    } else {
      console.error('Order creation failed:', result);
      showToast(result.message || 'Failed to create order', 'error');
    }
  } catch (e) {
    console.error('Order creation error:', e);
    showToast('Failed to create order', 'error');
  }
}

async function listOrders() {
  console.log('listOrders called, auth.user:', auth.user);
  if (!auth.user?.id) {
    console.log('No user ID, skipping order listing');
    return;
  }
  
  try {
    console.log('Fetching orders for user:', auth.user.id);
    const data = await apiFetch(API.ordersOf(auth.user.id));
    console.log('Orders response:', data);
    
    if (data.success) {
      const wrap = document.getElementById('ordersList');
      if (!wrap) {
        console.error('ordersList element not found!');
        return;
      }
      
      wrap.innerHTML = '';
      
      if (!data.data || data.data.length === 0) {
        wrap.innerHTML = '<div style="padding: 1rem; text-align: center; color: #6b7280;">No orders found</div>';
        console.log('No orders found for user');
        return;
      }
      
      console.log('Displaying', data.data.length, 'orders');
      data.data.forEach(o => {
        const div = document.createElement('div');
        div.className = 'order-item';
        div.style.cssText = 'border:1px solid #ddd; margin:0.5rem 0; padding:1rem; border-radius:0.5rem; background:#f9f9f9;';
        
        const isCompleted = o.status === 'delivered' || o.status === 'cancelled';
        const statusColor = isCompleted ? '#059669' : '#f59e0b';
        
        div.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <strong>Order #${o.id}</strong><br>
              <span style="color: #6b7280;">$${o.total_amount} • ${o.restaurant_name || 'Restaurant'}</span><br>
              <span id="st_${o.id}" style="background: ${statusColor}; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.875rem; margin-top: 0.25rem; display: inline-block;">
                ${o.status.toUpperCase()}
              </span>
              <div id="polling_status_${o.id}" style="margin-top: 0.25rem; color: #6b7280; font-size: 0.75rem;">
                ${!isCompleted ? '🔄 Long polling active...' : '✅ Order completed'}
              </div>
            </div>
            <div style="display: flex; gap: 0.5rem; align-items: center;">
              ${!isCompleted ? `
                <span style="color: #3b82f6; font-weight: 500; font-size: 0.875rem;">📡 Polling</span>
              ` : `
                <span style="color: #059669; font-weight: 500; font-size: 0.875rem;">✅ ${o.status === 'delivered' ? 'Completed' : 'Cancelled'}</span>
              `}
            </div>
          </div>
        `;
        wrap.appendChild(div);
        
        if (!isCompleted) {
          trackStatus(o.id);
        }
      });
    }
  } catch (e) {
    console.error('Failed to load orders:', e);
  }
}

async function trackStatus(orderId) {
  let lastStatus = null;
  let polling = true;
  
  const updatePollingStatus = (message) => {
    const statusEl = document.getElementById(`polling_status_${orderId}`);
    if (statusEl) statusEl.textContent = message;
  };
  
  while (polling) {
    try {
      const url = API.track(orderId, lastStatus);
      const res = await fetch(url);
      const data = await res.json();
      
      if (data.success && data.data) {
        const order = data.data;
        lastStatus = order.status;
        
        const statusEl = document.getElementById(`st_${orderId}`);
        if (statusEl) {
          statusEl.textContent = order.status.toUpperCase();
          const isCompleted = order.status === 'delivered' || order.status === 'cancelled';
          statusEl.style.background = isCompleted ? '#059669' : '#f59e0b';
        }
        
        if (order.status === 'delivered' || order.status === 'cancelled') {
          polling = false;
          updatePollingStatus('✅ Order completed');
          showToast(`Order #${orderId} is ${order.status}!`, 'success');
        } else {
          updatePollingStatus(`🔄 Status: ${order.status}`);
        }
      }
    } catch (e) {
      console.error(`Polling error for order ${orderId}:`, e);
      updatePollingStatus('❌ Polling error');
      break;
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}

// Employee functions
async function loadExistingOrders() {
  console.log('loadExistingOrders called');
  try {
    const data = await apiFetch(API.allOrders);
    console.log('loadExistingOrders response:', data);
    
    if (data.success && data.data) {
      const wrap = document.getElementById('ordersNotifications');
      if (!wrap) {
        console.error('ordersNotifications element not found!');
        return;
      }
      
      wrap.innerHTML = '';
      console.log('Loading', data.data.length, 'existing orders');
      data.data.forEach(order => addOrderToEmployeeList(order));
    } else {
      console.log('No orders data or failed response:', data);
    }
  } catch (error) {
    console.error('Failed to load orders:', error);
    showToast('Failed to load existing orders', 'warning');
  }
}

function addOrderToEmployeeList(orderData) {
  console.log('addOrderToEmployeeList called with:', orderData);
  console.log('Raw orderData keys:', Object.keys(orderData));
  console.log('Raw orderData.id:', orderData.id);
  console.log('Raw orderData.order_id:', orderData.order_id);
  
  const wrap = document.getElementById('ordersNotifications');
  if (!wrap) {
    console.error('ordersNotifications element not found!');
    return;
  }
  
  // Extract order ID with EXPLICIT fallbacks and debugging
  let orderId = orderData.id;
  if (!orderId && orderData.order_id) {
    orderId = orderData.order_id;
    console.log('Using order_id as fallback:', orderId);
  }
  
  console.log('Final extracted orderId:', orderId, typeof orderId);
  
  if (!orderId) {
    console.error('No valid order ID found in order data:', orderData);
    console.error('Checked fields: id =', orderData.id, ', order_id =', orderData.order_id);
    return;
  }
  
  console.log('Processing order with ID:', orderId);
  
  // Check if order already exists to avoid duplicates
  const existingOrder = document.getElementById(`status_${orderId}`);
  if (existingOrder) {
    console.log('Order already exists in list, skipping:', orderId);
    return;
  }
  
  const item = document.createElement('div');
  item.className = 'item';
  item.style.marginBottom = '1rem';
  item.style.padding = '1.25rem';
  item.style.border = '2px solid #e5e7eb';
  item.style.borderRadius = '0.75rem';
  item.style.background = '#ffffff';
  item.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
  
  const status = orderData.status || 'confirmed';
  const needsAttention = ['confirmed', 'preparing'].includes(status);
  if (needsAttention) {
    item.style.borderColor = '#f59e0b';
    item.style.background = '#fffbeb';
  }
  
  const timeAgo = orderData.created_at ? 
    new Date(orderData.created_at).toLocaleString() : 
    'Just now';
  
  // Extract data with proper fallbacks
  const restaurantName = orderData.restaurant_name || 'Restaurant';
  const totalAmount = orderData.total_amount || '0';
  const deliveryAddress = orderData.delivery_address || 'Address not provided';
  
  console.log('Order details for HTML:', {
    orderId,
    restaurantName,
    totalAmount,
    deliveryAddress,
    status,
    timeAgo
  });
  
  item.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div style="flex: 1;">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
          <strong style="font-size: 1.1rem; color: #1f2937;">Order #${orderId}</strong>
          ${needsAttention ? '<span style="background: #f59e0b; color: white; padding: 0.125rem 0.5rem; border-radius: 12px; font-size: 0.75rem; margin-left: 0.5rem;">⚠️ Needs Attention</span>' : ''}
        </div>
        <div style="color: #6b7280; margin-bottom: 0.25rem;">
          🍽️ ${restaurantName} • $${totalAmount}
        </div>
        <div style="color: #6b7280; margin-bottom: 0.5rem; font-size: 0.875rem;">
          📍 ${deliveryAddress}
        </div>
        <div style="color: #6b7280; font-size: 0.75rem;">
          🕒 Ordered: ${timeAgo}
        </div>
        <div style="margin-top: 0.5rem;">
          <span id="status_${orderId}" style="background: ${getStatusColor(status)}; color: white; padding: 0.375rem 0.75rem; border-radius: 6px; font-size: 0.875rem; font-weight: 500;">
            ${status.toUpperCase()}
          </span>
        </div>
      </div>
      <div style="display: flex; flex-direction: column; gap: 0.5rem; align-items: center;">
        <select id="status_${orderId}_select" onchange="updateOrderStatusManual(${orderId})" style="padding: 0.375rem; border-radius: 4px; border: 1px solid #d1d5db;">
          <option value="confirmed" ${status === 'confirmed' ? 'selected' : ''}>Confirmed</option>
          <option value="preparing" ${status === 'preparing' ? 'selected' : ''}>Preparing</option>
          <option value="ready" ${status === 'ready' ? 'selected' : ''}>Ready</option>
          <option value="picked_up" ${status === 'picked_up' ? 'selected' : ''}>Picked Up</option>
          <option value="delivered" ${status === 'delivered' ? 'selected' : ''}>Delivered</option>
          <option value="cancelled" ${status === 'cancelled' ? 'selected' : ''}>Cancelled</option>
        </select>
        <span id="update_status_${orderId}" style="color: #059669; font-size: 0.75rem; min-height: 1rem;"></span>
      </div>
    </div>
  `;
  
  wrap.appendChild(item);
  console.log('Order added to employee list successfully with ID:', orderId);
}

function getStatusColor(status) {
  const colors = {
    'confirmed': '#f59e0b',
    'preparing': '#3b82f6',
    'ready': '#8b5cf6',
    'picked_up': '#06b6d4',
    'delivered': '#059669',
    'cancelled': '#dc2626'
  };
  return colors[status] || '#6b7280';
}

async function updateOrderStatusManual(orderId) {
  const select = document.getElementById(`status_${orderId}_select`);
  const newStatus = select.value;
  const statusSpan = document.getElementById(`update_status_${orderId}`);
  
  try {
    const result = await apiFetch(`/api/v1/orders/${orderId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status: newStatus })
    });
    
    if (result.success) {
      document.getElementById(`status_${orderId}`).textContent = newStatus.toUpperCase();
      document.getElementById(`status_${orderId}`).style.background = getStatusColor(newStatus);
      statusSpan.textContent = '✓ Updated';
      setTimeout(() => statusSpan.textContent = '', 2000);
      showToast(`Order #${orderId} updated to ${newStatus}`, 'success');
      loadExistingOrders();
    } else {
      statusSpan.textContent = '✗ Failed';
      setTimeout(() => statusSpan.textContent = '', 2000);
    }
  } catch (e) {
    statusSpan.textContent = '✗ Error';
    setTimeout(() => statusSpan.textContent = '', 2000);
    showToast(`Failed to update order: ${e.message}`, 'error');
  }
}

async function initEmployee(){
  console.log('initEmployee called');
  await loadExistingOrders();
  
  console.log('Starting SSE connection to:', API.ordersSSE);
  const sse = new EventSource(API.ordersSSE);
  
  sse.onopen = function(event) {
    console.log('SSE connection opened successfully');
  };
  
  sse.onmessage = (e)=>{ 
    console.log('SSE message received:', e.data);
    try{ 
      const data=JSON.parse(e.data);
      console.log('SSE parsed data:', data);
      console.log('Data keys:', Object.keys(data));
      
      // CRITICAL: Normalize the data structure for consistency
      // The backend sends 'order_id' but our frontend expects 'id'
      let orderData = { ...data };
      
      // Ensure we have an 'id' field for consistency with existing code
      if (data.order_id && !data.id) {
        orderData.id = data.order_id;
        console.log('Converted order_id to id:', orderData.id);
      }
      
      console.log('Normalized order data:', orderData);
      console.log('Order ID field check:', {
        'orderData.id': orderData.id,
        'orderData.order_id': orderData.order_id
      });
      
      // Ensure we have a valid order ID
      const orderNumber = orderData.id || orderData.order_id;
      console.log('Final order number:', orderNumber);
      
      if (!orderNumber) {
        console.error('No valid order ID found in SSE data:', data);
        return;
      }
      
      addOrderToEmployeeList(orderData);
      
      // Enhanced notification for employees
      const restaurantName = orderData.restaurant_name || 'Restaurant';
      const totalAmount = orderData.total_amount || '0';
      
      // Show regular toast
      showToast(`🆕 New order #${orderNumber} received from ${restaurantName}`, 'info');
      
      // Show prominent notification overlay
      showNewOrderEmployeeNotification(orderNumber, restaurantName, totalAmount, orderData);
      
    }catch(err){ 
      console.error('Error processing new order SSE:', err);
    } 
  };
  
  sse.onerror = function(event) {
    console.error('SSE error:', event);
    console.log('SSE readyState:', sse.readyState);
  };

  await ensureSocketIO();
  socket = io(getSocketIOUrl());
  socket.on('connect', ()=>{ socket.emit('agent_subscribe', {}); });
  socket.on('chats_list', (p)=>{
    const list = document.getElementById('chatList'); list.innerHTML='';
    (p.chats||[]).forEach(c=>{
      const d = document.createElement('div'); d.className='item'; d.textContent = `#${c.chat_id} - ${c.customer}`;
      d.onclick = ()=>{ socket.emit('open_chat', {chat_id:c.chat_id}); };
      list.appendChild(d);
    });
  });
  socket.on('chat_opened', (p)=>{
    currentChatId = p.chat_id; const box = document.getElementById('agentMessages'); box.innerHTML='';
    (p.history||[]).forEach(m=>appendAgent(box, m));
  });
  socket.on('message', (m)=>{ 
    if(m.chat_id===currentChatId){ 
      const box=document.getElementById('agentMessages'); 
      const isNewCustomerMessage = m.role === 'customer';
      appendAgent(box, m, isNewCustomerMessage); 
    }
  });
  document.getElementById('agentSend').onclick = ()=>{
    const input = document.getElementById('agentInput'); 
    const text = input.value.trim(); 
    console.log('Agent send clicked:', {text, currentChatId});
    
    if(!text) {
      alert('Please enter a message');
      return;
    }
    if(!currentChatId) {
      alert('No chat selected. Please select a chat first.');
      return;
    }
    
    socket.emit('send_message', {chat_id: currentChatId, text, role:'employee', user:'agent'});
    input.value='';
  };
}

function appendAgent(container, m, showNotification = false) {
  const div = document.createElement('div');
  div.className = `bubble ${m.role === 'customer' ? 'other' : 'me'}`;
  div.innerHTML = `<strong>${m.role === 'customer' ? 'Customer' : 'You'}:</strong> ${m.text}`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  
  if (showNotification) {
    showToast('New message from customer', 'info');
  }
}

// Initialize based on page
document.addEventListener('DOMContentLoaded', async ()=>{
  const page = window.PAGE;
  console.log('DOMContentLoaded, page:', page);
  
  if(page==='auth') attachAuthHandlers();
  
  if(page==='customer'){
    console.log('Initializing customer page');
    await initCommon();
    console.log('After initCommon, auth.user:', auth.user);
    
    if(!auth.user){ 
      console.log('No user found, redirecting to index');
      window.location.href='/templates/index.html'; 
      return; 
    }
    
    console.log('User found, loading customer features');
    loadProfile();
    document.getElementById('profileForm')?.addEventListener('submit', saveProfile);
    document.getElementById('orderForm')?.addEventListener('submit', createOrder);
    
    // Load orders with a slight delay to ensure DOM is ready
    setTimeout(() => {
      console.log('Loading orders...');
      listOrders();
    }, 100);
    
    document.getElementById('startStream')?.addEventListener('click', startLocationStream);
    document.getElementById('stopStream')?.addEventListener('click', ()=>{ stopLocationStream(); stopDriverSimulation(); });
    initCustomerChat();
  }
  
  if(page==='employee'){
    console.log('Initializing employee page');
    await initCommon();
    console.log('After initCommon, auth.user:', auth.user);
    
    if(!auth.user || auth.user.role!=='employee'){ 
      console.log('No employee user found, redirecting to index');
      window.location.href='/templates/index.html'; 
      return; 
    }
    
    console.log('Employee user found, initializing employee features');
    initEmployee();
  }
});

// Auth page functions
async function loginUser(email, password) {
  try {
    const response = await apiFetch(API.login, {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    
    if (response.success) {
      // Store auth data
      auth.access = response.data.access_token;
      auth.refresh = response.data.refresh_token;
      auth.user = response.data.user;
      
      // Store in cookies
      setCookie('access_token', auth.access, 1);
      setCookie('refresh_token', auth.refresh, 7);
      setCookie('user', JSON.stringify(auth.user), 7);
      
      // Redirect based on role
      if (auth.user.role === 'employee') {
        window.location.href = '/templates/employee.html';
      } else {
        window.location.href = '/templates/customer.html';
      }
      
      return { success: true };
    } else {
      return { success: false, error: response.message || 'Login failed' };
    }
  } catch (e) {
    console.error('Login error:', e);
    return { success: false, error: 'Login failed' };
  }
}

async function registerUser(userData) {
  try {
    console.log('Attempting registration with:', userData);
    const response = await apiFetch(API.register, {
      method: 'POST',
      body: JSON.stringify(userData)
    });
    
    console.log('Registration response:', response);
    
    if (response.success) {
      // Switch to login tab immediately
      const loginTab = document.querySelector('[data-tab="login"]');
      const registerTab = document.querySelector('[data-tab="register"]');
      const loginPanel = document.getElementById('login');
      const registerPanel = document.getElementById('register');
      
      if (loginTab && registerTab && loginPanel && registerPanel) {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        loginPanel.classList.add('active');
        registerPanel.classList.remove('active');
      }
      
      // Show success message on login form
      const loginMsg = document.getElementById('loginMsg');
      if (loginMsg) {
        loginMsg.textContent = 'Registration successful! Please login with your credentials.';
        loginMsg.className = 'messages success';
      }
      
      // Pre-fill email in login form
      const loginEmail = document.getElementById('loginEmail');
      if (loginEmail) {
        loginEmail.value = userData.email;
      }
      
      return { success: true };
    } else {
      console.error('Registration failed:', response);
      return { success: false, error: response.message || response.error || 'Registration failed' };
    }
  } catch (e) {
    console.error('Registration error:', e);
    return { success: false, error: 'Network error during registration' };
  }
}

function attachAuthHandlers() {
  // Tab switching
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const tabName = tab.dataset.tab;
      
      // Update tabs
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      
      tab.classList.add('active');
      document.getElementById(tabName).classList.add('active');
      
      // Clear messages when switching tabs
      const loginMsg = document.getElementById('loginMsg');
      const registerMsg = document.getElementById('registerMsg');
      if (loginMsg) {
        loginMsg.textContent = '';
        loginMsg.className = 'messages';
      }
      if (registerMsg) {
        registerMsg.textContent = '';
        registerMsg.className = 'messages';
      }
    });
  });
  
  // Login form
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const email = document.getElementById('loginEmail').value.trim();
      const password = document.getElementById('loginPassword').value;
      const msgEl = document.getElementById('loginMsg');
      
      if (!email || !password) {
        msgEl.textContent = 'Please fill in all fields';
        msgEl.className = 'messages error';
        return;
      }
      
      msgEl.textContent = 'Logging in...';
      msgEl.className = 'messages';
      
      const result = await loginUser(email, password);
      
      if (result.success) {
        msgEl.textContent = 'Login successful! Redirecting...';
        msgEl.className = 'messages success';
      } else {
        msgEl.textContent = result.error;
        msgEl.className = 'messages error';
      }
    });
  }
  
  // Registration form
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const msgEl = document.getElementById('registerMsg');
      const userData = {
        first_name: document.getElementById('registerName').value.trim(),
        last_name: document.getElementById('registerName').value.trim(), // Using same for both
        email: document.getElementById('registerEmail').value.trim(),
        password: document.getElementById('registerPassword').value,
        role: document.getElementById('registerRole').value || 'customer'
      };
      
      if (!userData.first_name || !userData.email || !userData.password) {
        msgEl.textContent = 'Please fill in all fields';
        msgEl.className = 'messages error';
        return;
      }
      
      if (userData.password.length < 6) {
        msgEl.textContent = 'Password must be at least 6 characters';
        msgEl.className = 'messages error';
        return;
      }
      
      msgEl.textContent = 'Creating account...';
      msgEl.className = 'messages';
      
      const result = await registerUser(userData);
      
      if (result.success) {
        msgEl.textContent = 'Registration successful!';
        msgEl.className = 'messages success';
        registerForm.reset();
      } else {
        msgEl.textContent = result.error;
        msgEl.className = 'messages error';
      }
    });
  }
}

// Quick login helper functions for testing
function fillCustomerLogin() {
  const emailField = document.getElementById('loginEmail');
  const passwordField = document.getElementById('loginPassword');
  
  if (emailField && passwordField) {
    emailField.value = 'customer@azure.com';
    passwordField.value = 'Customer1234@';
    
    // Add visual feedback
    emailField.style.background = '#e8f5e8';
    passwordField.style.background = '#e8f5e8';
    
    setTimeout(() => {
      emailField.style.background = '';
      passwordField.style.background = '';
    }, 1000);
  }
}

function fillEmployeeLogin() {
  const emailField = document.getElementById('loginEmail');
  const passwordField = document.getElementById('loginPassword');
  
  if (emailField && passwordField) {
    emailField.value = 'emp@azure.com';
    passwordField.value = 'Emp1234@';
    
    // Add visual feedback
    emailField.style.background = '#e8f5e8';
    passwordField.style.background = '#e8f5e8';
    
    setTimeout(() => {
      emailField.style.background = '';
      passwordField.style.background = '';
    }, 1000);
  }
}