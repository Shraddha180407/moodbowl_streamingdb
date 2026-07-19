/* ── MoodBite App — Full API Integration ──────────────────────────────────── */
'use strict';

const API = '/api';
// ── Mood alias map: frontend mood names → backend mood IDs ───────────────────
const MOOD_ALIAS = {
  comfort: 'soothing',   // frontend uses 'comfort', backend calls it 'soothing'
  neutral: 'happy',      // fallback
};
function normalizeMood(m) { return MOOD_ALIAS[m] || m || 'happy'; }

let authToken  = localStorage.getItem('mb_access')  || null;
let refreshTok = localStorage.getItem('mb_refresh') || null;
let currentUser  = JSON.parse(localStorage.getItem('mb_user') || 'null');
let currentMood  = localStorage.getItem('mb_mood') || 'happy';
let cartCount    = 0;
let cartItems    = [];
let selectedRating = 0;
let currentOrderId = null;

// ── Helpers ──────────────────────────────────────────────────────────────────
async function api(method, path, body, isForm=false) {
  const opts = { method, headers: {} };
  if (authToken) opts.headers['Authorization'] = `Bearer ${authToken}`;
  if (body && !isForm) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
  if (isForm) opts.body = body;
  const r = await fetch(API + path, opts);
  if (r.status === 401 && refreshTok) {
    const ok = await doRefresh();
    if (ok) { opts.headers['Authorization'] = `Bearer ${authToken}`; return fetch(API + path, opts).then(r => r.json()); }
  }
  return r.json();
}

async function doRefresh() {
  try {
    const r = await fetch(API + '/auth/token/refresh/', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({refresh: refreshTok}) });
    const d = await r.json();
    if (d.access) { authToken = d.access; localStorage.setItem('mb_access', authToken); return true; }
  } catch(e) {}
  logout();
  return false;
}

function toast(msg, type='') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast' + (type ? ' '+type : '');
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3200);
}

function showLoader() { document.getElementById('loading-overlay').classList.add('show'); }
function hideLoader() { document.getElementById('loading-overlay').classList.remove('show'); }

function formatPrice(p) { return '₹' + parseFloat(p).toFixed(0); }
function formatRating(r) { return '⭐ ' + parseFloat(r).toFixed(1); }

const MOOD_EMOJI = {happy:'😊',sad:'😢',stressed:'😰',tired:'😴',excited:'🤩',anxious:'😟',romantic:'❤️',energetic:'💪',bored:'😑',celebratory:'🎉',neutral:'😐',comfort:'🤗'};
const MOOD_THEME = {happy:'#FFD700',sad:'#4169E1',stressed:'#FF6347',tired:'#9370DB',excited:'#FF69B4',anxious:'#20B2AA',romantic:'#DC143C',energetic:'#32CD32',bored:'#9CA3AF',celebratory:'#FFA500',neutral:'#6B7280',comfort:'#F97316'};

// ── View switching ────────────────────────────────────────────────────────────
const VIEWS = ['splash','onboarding-1','onboarding-2','onboarding-3','login','mood-selection','home','explore','cart','favorites','profile','recommendations','tracking'];

function switchView(name, direction='forward') {
  const prev = document.querySelector('.view.active');
  const next = document.getElementById(name + '-view');
  if (!next || prev === next) return;
  if (prev) { prev.classList.remove('active'); if (direction==='back') prev.classList.add('slide-back'); setTimeout(()=>prev.classList.remove('slide-back'),350); }
  next.classList.add('active');
  updateBottomNav(name);
  onViewEnter(name);
}

function updateBottomNav(view) {
  const mainViews = ['home','explore','cart','favorites','profile'];
  const nav = document.querySelector('.bottom-nav');
  const bito = document.getElementById('bito-container');
  if (mainViews.includes(view)) {
    nav.style.display = 'flex';
    if (view !== 'splash') bito.style.display = 'block';
    document.querySelectorAll('.nav-item').forEach(b => {
      b.classList.toggle('active', b.dataset.view === view);
    });
  } else {
    nav.style.display = view === 'recommendations' || view === 'tracking' ? 'none' : 'flex';
    if (['login','onboarding-1','onboarding-2','onboarding-3','splash','mood-selection'].includes(view)) bito.style.display = 'none';
  }
}

function onViewEnter(view) {
  if (view === 'home') loadHomeRecs();
  if (view === 'explore') loadExplore();
  if (view === 'cart') loadCart();
  if (view === 'profile') loadProfile();
  if (view === 'recommendations') loadRecommendations();
}

// ── Auth ──────────────────────────────────────────────────────────────────────
async function performAuth(mode) {
  const email = document.getElementById('login-email').value.trim();
  const pwd   = document.getElementById('login-password').value;
  const errEl = document.getElementById('auth-error');
  errEl.classList.remove('show');
  if (!email || !pwd) { errEl.textContent='Please fill in all fields'; errEl.classList.add('show'); return; }

  showLoader();
  try {
    let res;
    if (mode === 'login') {
      res = await api('POST', '/auth/login/', {email, password:pwd});
    } else {
      const name = email.split('@')[0];
      res = await api('POST', '/auth/register/', {email, password:pwd, name, phone:''});
    }
    if (res.success || res.token) {
      authToken  = res.token.access;
      refreshTok = res.token.refresh;
      currentUser = res.data;
      localStorage.setItem('mb_access',  authToken);
      localStorage.setItem('mb_refresh', refreshTok);
      localStorage.setItem('mb_user', JSON.stringify(currentUser));
      toast('Welcome to MoodBite! 🎉', 'success');
      switchView('mood-selection');
    } else {
      errEl.textContent = res.error?.message || 'Authentication failed';
      errEl.classList.add('show');
    }
  } catch(e) {
    errEl.textContent = 'Network error. Is the server running?';
    errEl.classList.add('show');
  } finally { hideLoader(); }
}

function logout() {
  if (refreshTok) api('POST', '/auth/logout/', {refresh: refreshTok}).catch(()=>{});
  authToken = refreshTok = currentUser = null;
  localStorage.removeItem('mb_access');
  localStorage.removeItem('mb_refresh');
  localStorage.removeItem('mb_user');
  toast('Logged out');
  switchView('login');
}

// ── Mood selection ────────────────────────────────────────────────────────────
const BITO_MSGS = {
  happy: "You're happy! Let me find something delicious to celebrate 🎉",
  sad: "Aww, cheer up! Let me find the perfect comfort food 💙",
  stressed: "Take a deep breath. I'll find something calming and light 🍃",
  tired: "I'll find you something warm and energising right away! ☕",
  excited: "Let's celebrate with something fun and adventurous! 🔥",
  neutral: "Let's explore all options and find something you'll love!",
  energetic: "Love the energy! How about something nutritious and powerful? 💪",
  comfort: "I've got you. Comfort food coming right up ❤️",
};

document.querySelectorAll('.mood-card').forEach(card => {
  card.addEventListener('click', () => {
    document.querySelectorAll('.mood-card').forEach(c => c.classList.remove('active'));
    card.classList.add('active');
    currentMood = card.dataset.mood;
    localStorage.setItem('mb_mood', currentMood);
    document.getElementById('mood-bito-bubble').textContent = BITO_MSGS[currentMood] || "Let me find the perfect meal for you!";
    moodFlash(MOOD_THEME[currentMood]);
    updateBitoMood(currentMood);
  });
});

function moodFlash(color) {
  const el = document.getElementById('mood-flash-overlay');
  el.style.background = color;
  el.classList.add('flash');
  setTimeout(() => el.classList.remove('flash'), 500);
}

function updateBitoMood(mood) {
  const mouth = document.getElementById('bito-mouth-main');
  if (!mouth) return;
  const paths = {
    happy: 'M43 50 Q50 58 57 50',
    sad: 'M43 54 Q50 48 57 54',
    stressed: 'M43 52 Q50 52 57 52',
    tired: 'M44 53 Q50 50 56 53',
    excited: 'M41 49 Q50 60 59 49',
    neutral: 'M43 52 Q50 52 57 52',
  };
  mouth.setAttribute('d', paths[mood] || paths.happy);
}

function enterApp() {
  document.getElementById('home-mood-label').textContent = currentMood.charAt(0).toUpperCase() + currentMood.slice(1);
  // Auto-send mood to text analysis if logged in
  if (authToken) {
    api('POST', '/ai/analyze-text/', {text: `I am feeling ${currentMood} today`}).catch(()=>{});
  }
  switchView('home');
  loadHomeRecs();
  bitaSay("Great choice! Here are your personalised picks 🍽️");
}

function finishOnboarding() {
  localStorage.setItem('mb_onboarded', '1');
  switchView('login');
}

// ── Home ──────────────────────────────────────────────────────────────────────
async function loadHomeRecs() {
  if (!authToken) { loadHomeMock(); return; }
  const container = document.querySelector('.home-rec-cards');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted)">Loading…</div>';
  try {
    const res = await api('POST', '/recommendations/generate/', {mood: normalizeMood(currentMood), filters: {}});
    if (res.success && res.data?.recommendations) {
      renderFoodCards(container, res.data.recommendations.slice(0,4), true);
    }
  } catch(e) { loadHomeMock(); }
}

function loadHomeMock() {
  const container = document.querySelector('.home-rec-cards');
  if (!container) return;
  const SAMPLE = [
    {item_id:1,name:'Butter Chicken',description:'Rich North Indian curry',price:349,rating:4.7,is_vegetarian:false,category:'main_course',cuisine:'Indian'},
    {item_id:2,name:'Mac & Cheese Bowl',description:'Creamy comfort food',price:299,rating:4.5,is_vegetarian:true,category:'comfort_food',cuisine:'Italian'},
    {item_id:3,name:'Mango Lassi',description:'Sweet chilled yogurt drink',price:129,rating:4.8,is_vegetarian:true,category:'beverage',cuisine:'Indian'},
  ];
  renderFoodCards(container, SAMPLE, true);
}

function renderFoodCards(container, items, showAdd=true) {
  const FOOD_EMOJI = {main_course:'🍛',comfort_food:'🍲',healthy:'🥗',dessert:'🍰',beverage:'🧃',starter:'🥗',street_food:'🌯',breakfast:'🥞',snack:'🍿'};
  container.innerHTML = items.map(item => `
    <div class="food-card" data-id="${item.item_id||item.id}">
      <div class="food-card-img">${FOOD_EMOJI[item.category]||'🍽️'}</div>
      <div class="food-card-body">
        <div class="food-card-name">${item.name}</div>
        <div class="food-card-sub">${item.cuisine} · ${item.is_vegetarian?'🟢 Veg':'🔴 Non-veg'}</div>
        <div class="food-card-row">
          <span class="food-card-price">${formatPrice(item.price)}</span>
          <span class="food-card-rating">${formatRating(item.rating)}</span>
          ${showAdd ? `<button class="food-card-add" onclick="addToCart(${item.item_id||item.id}, '${item.name}', ${item.price})">+ Add</button>` : ''}
        </div>
      </div>
    </div>`).join('');
}

// Pill mood filter on home
document.querySelectorAll('.pill').forEach(pill => {
  pill.addEventListener('click', () => {
    document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    const moodMap = {'Happy':'happy','Stressed':'stressed','Tired':'tired','Celebrating':'celebratory','Comfort Food':'soothing'};
    currentMood = normalizeMood(moodMap[pill.textContent] || pill.textContent.toLowerCase());
    localStorage.setItem('mb_mood', currentMood);
    loadHomeRecs();
  });
});

// ── Explore ───────────────────────────────────────────────────────────────────
let exploreTimeout;
async function loadExplore(search='', category='') {
  const list = document.getElementById('restaurant-list');
  list.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted)">Loading menu…</div>';
  try {
    let res;
    if (search) {
      res = await api('POST', '/menu/search/', {query: search, filters: category && category!=='All' ? {cuisine:[category]} : {}});
      const items = res.data?.results || [];
      renderExploreItems(list, items);
    } else {
      const params = new URLSearchParams({limit:'20', sort_by:'popularity'});
      if (category && category !== 'All') params.append('cuisine', category);
      res = await api('GET', `/menu/items/?${params}`);
      renderExploreItems(list, res.data?.items || []);
    }
  } catch(e) {
    list.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted)">Connect to the backend to see the menu</div>';
  }
}

function renderExploreItems(container, items) {
  if (!items.length) { container.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted)">No items found</div>'; return; }
  const FOOD_EMOJI = {main_course:'🍛',comfort_food:'🍲',healthy:'🥗',dessert:'🍰',beverage:'🧃',starter:'🥗',street_food:'🌯',breakfast:'🥞',snack:'🍿'};
  container.innerHTML = items.map(item => `
    <div class="food-card">
      <div class="food-card-img">${FOOD_EMOJI[item.category]||'🍽️'}</div>
      <div class="food-card-body">
        <div class="food-card-name">${item.name}</div>
        <div class="food-card-sub">${item.cuisine} · ${item.category.replace('_',' ')} · ${item.is_vegetarian?'🟢':'🔴'}</div>
        <div class="food-card-row">
          <span class="food-card-price">${formatPrice(item.price)}</span>
          <span class="food-card-rating">${formatRating(item.rating)}</span>
          <button class="food-card-add" onclick="addToCart(${item.id}, '${item.name.replace(/'/g,"\\'")}', ${item.price})">+ Add</button>
        </div>
      </div>
    </div>`).join('');
}

// Search
document.querySelector('.search-bar input')?.addEventListener('input', e => {
  clearTimeout(exploreTimeout);
  exploreTimeout = setTimeout(() => loadExplore(e.target.value.trim()), 400);
});

// Category chips
document.querySelectorAll('.cat-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('.cat-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    loadExplore('', chip.textContent.trim());
  });
});

// ── Recommendations ───────────────────────────────────────────────────────────
async function loadRecommendations() {
  const list = document.getElementById('recommendations-list');
  document.querySelector('.mood-banner').textContent = `Mood: ${currentMood} ${MOOD_EMOJI[currentMood]||''}`;
  if (!authToken) { renderMockRecs(list); return; }
  list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted)">Loading…</div>';
  try {
    const res = await api('POST', '/recommendations/generate/', {mood: normalizeMood(currentMood), filters: {}});
    if (res.success && res.data?.recommendations?.length) {
      const items = res.data.recommendations;
      // Top pick
      const top = items[0];
      const tp = document.querySelector('.top-pick-card .card-body');
      if (tp) {
        tp.querySelector('h5').textContent = top.name;
        tp.querySelector('.card-price').textContent = formatPrice(top.price);
        tp.querySelector('.vendor').textContent = top.cuisine + ' · ' + top.category.replace('_',' ');
        tp.querySelector('.card-desc').textContent = top.recommendation_reason;
        tp.querySelector('.cart-add').onclick = () => addToCart(top.item_id, top.name, top.price);
      }
      // Rest
      renderExploreItems(list, items.slice(1));
    }
  } catch(e) { renderMockRecs(list); }
}

function renderMockRecs(list) {
  list.innerHTML = '<div style="padding:12px;color:var(--text-muted);font-size:13px;text-align:center">Log in to get personalised recommendations</div>';
}

// ── Cart ──────────────────────────────────────────────────────────────────────
async function addToCart(itemId, name, price) {
  if (!authToken) { toast('Please login to add items to cart'); switchView('login'); return; }
  showLoader();
  try {
    const res = await api('POST', '/cart/add/', {item_id: itemId, quantity: 1});
    if (res.success) {
      cartCount++;
      updateCartBadge();
      toast(`${name} added to cart! 🛒`, 'success');
      bitaSay(`Great choice! ${name} added. Anything else? 😊`);
    } else {
      toast(res.error?.message || 'Could not add item', 'error');
    }
  } catch(e) { toast('Network error', 'error'); }
  finally { hideLoader(); }
}

async function loadCart() {
  const listEl   = document.getElementById('cart-list');
  const emptyEl  = document.getElementById('cart-empty-state');
  const summaryEl = document.querySelector('.cart-summary');
  if (!authToken) { emptyEl.style.display='flex'; listEl.style.display='none'; summaryEl.style.display='none'; return; }
  try {
    const res = await api('GET', '/cart/');
    if (!res.success) return;
    cartItems = res.data.items || [];
    cartCount = res.data.items_count || 0;
    updateCartBadge();
    if (!cartItems.length) {
      emptyEl.style.display='flex'; listEl.style.display='none'; summaryEl.style.display='none'; return;
    }
    emptyEl.style.display = 'none';
    listEl.style.display = 'flex';
    summaryEl.style.display = 'block';
    renderCartItems(res.data);
  } catch(e) {}
}

function renderCartItems(data) {
  const listEl = document.getElementById('cart-list');
  listEl.innerHTML = (data.items||[]).map(ci => `
    <div class="cart-item" id="ci-${ci.cart_item_id}">
      <div class="cart-item-info">
        <div class="cart-item-name">${ci.item.name}</div>
        <div class="cart-item-price">${formatPrice(ci.item.price)} each</div>
      </div>
      <div class="qty-controls">
        <button class="qty-btn" onclick="changeQty(${ci.cart_item_id}, ${ci.quantity-1})">−</button>
        <span class="qty-num">${ci.quantity}</span>
        <button class="qty-btn" onclick="changeQty(${ci.cart_item_id}, ${ci.quantity+1})">+</button>
      </div>
      <div style="font-weight:700;font-size:14px">${formatPrice(ci.item_total)}</div>
    </div>`).join('');

  document.querySelector('.cart-summary').innerHTML = `
    <div class="summary-card">
      <div class="coupon-row">
        <input type="text" id="coupon-input" placeholder="Coupon code (try FIRST50)">
        <button onclick="applyCoupon()">Apply</button>
      </div>
      <div class="summary-row"><span>Subtotal</span><span>${formatPrice(data.subtotal)}</span></div>
      <div class="summary-row"><span>Taxes (10%)</span><span>${formatPrice(data.taxes)}</span></div>
      <div class="summary-row"><span>Delivery</span><span>${formatPrice(data.delivery_fee)}</span></div>
      ${data.discount>0?`<div class="summary-row" style="color:var(--success)"><span>Discount</span><span>−${formatPrice(data.discount)}</span></div>`:''}
      <div class="summary-row total"><span>Total</span><span>${formatPrice(data.total)}</span></div>
      <button class="checkout-btn" onclick="checkout()">Place Order 🎉</button>
    </div>`;
}

async function changeQty(cartItemId, newQty) {
  if (newQty < 1) { await removeCartItem(cartItemId); return; }
  try {
    await api('PUT', `/cart/items/${cartItemId}/`, {quantity: newQty});
    loadCart();
  } catch(e) {}
}

async function removeCartItem(cartItemId) {
  try {
    await api('DELETE', `/cart/items/${cartItemId}/`);
    loadCart();
    toast('Item removed');
  } catch(e) {}
}

function applyCoupon() {
  const code = document.getElementById('coupon-input').value.trim();
  if (!code) return;
  toast(`Coupon "${code}" will be applied at checkout!`, 'success');
}

async function checkout() {
  if (!authToken) { toast('Please login first'); return; }
  const coupon = document.getElementById('coupon-input')?.value.trim() || '';
  showLoader();
  try {
    const res = await api('POST', '/orders/create/', {
      delivery_address: {line1: '123 Demo Street', city: 'Mumbai', pincode: '400001', phone: currentUser?.phone || '+919000000000'},
      payment_method: 'cod',
      coupon_code: coupon,
      mood_context: {detected_mood: currentMood, recommended_mood: normalizeMood(currentMood), voice_input: `Ordered while feeling ${currentMood}`}
    });
    if (res.success) {
      currentOrderId = res.data.order_id;
      cartCount = 0;
      updateCartBadge();
      toast('Order placed! 🎉', 'success');
      bitaSay("Your order is placed! I'll track it for you 🚗");
      switchView('tracking');
      startTracking(res.data);
    } else {
      toast(res.error?.message || 'Order failed', 'error');
    }
  } catch(e) { toast('Network error', 'error'); }
  finally { hideLoader(); }
}

function updateCartBadge() {
  const btn = document.querySelector('.nav-item[data-view="cart"]');
  if (!btn) return;
  if (cartCount > 0) {
    btn.classList.add('cart-badge');
    btn.setAttribute('data-count', cartCount > 9 ? '9+' : cartCount);
  } else {
    btn.classList.remove('cart-badge');
    btn.removeAttribute('data-count');
  }
}

// ── Order Tracking ────────────────────────────────────────────────────────────
const TRACK_STEPS = [
  {pct:15, title:'Order Confirmed', desc:'The kitchen has received your order!', icon:'step-1'},
  {pct:40, title:'Cooking in Progress 👨‍🍳', desc:'Your food is being freshly prepared.', icon:'step-2'},
  {pct:75, title:'Out for Delivery 🚗', desc:'Your rider is on the way!', icon:'step-3'},
  {pct:100, title:'Delivered! ✅', desc:"Enjoy your meal! Don't forget to rate it.", icon:'step-4'},
];

function startTracking(orderData) {
  let step = 0;
  const bar = document.getElementById('tracking-progress') || document.querySelector('.track-bar');
  const advance = () => {
    if (step >= TRACK_STEPS.length) return;
    const s = TRACK_STEPS[step];
    document.getElementById('tracking-title').textContent = s.title;
    document.getElementById('tracking-desc').textContent = s.desc;
    if (bar) bar.style.width = s.pct + '%';
    document.querySelectorAll('.step-icon').forEach((el,i) => el.classList.toggle('done', i <= step));
    step++;
    if (step < TRACK_STEPS.length) setTimeout(advance, 5000);
    else {
      document.getElementById('back-home-btn').style.display = 'block';
      showRatingModal();
    }
  };
  advance();
}

function showRatingModal() {
  selectedRating = 0;
  const tracking = document.querySelector('.tracking-body') || document.querySelector('.tracking-container');
  if (!tracking) return;
  const modal = document.createElement('div');
  modal.className = 'rating-modal';
  modal.innerHTML = `
    <h4>How was your order?</h4>
    <div class="star-rating" id="star-rating">
      ${[1,2,3,4,5].map(n=>`<span data-star="${n}" onclick="setRating(${n})">⭐</span>`).join('')}
    </div>
    <textarea class="review-input" id="review-text" rows="2" placeholder="Tell us more (optional)…"></textarea>
    <button class="primary-btn wide" style="margin-top:10px" onclick="submitRating()">Submit Review</button>`;
  tracking.appendChild(modal);
}

function setRating(n) {
  selectedRating = n;
  document.querySelectorAll('#star-rating span').forEach((s,i) => s.classList.toggle('lit', i < n));
}

async function submitRating() {
  if (!selectedRating || !currentOrderId) { toast('Please select a star rating'); return; }
  showLoader();
  try {
    const review = document.getElementById('review-text')?.value || '';
    await api('POST', `/orders/${currentOrderId}/rate/`, {rating: selectedRating, review, food_rating: selectedRating, delivery_rating: Math.max(3, selectedRating-1)});
    toast('Thank you for your feedback! 🌟', 'success');
    bitaSay("Thanks for rating! I'll use this to recommend better next time 🤖");
    document.querySelector('.rating-modal')?.remove();
  } catch(e) { toast('Could not submit rating'); }
  finally { hideLoader(); }
}

// ── Profile ───────────────────────────────────────────────────────────────────
async function loadProfile() {
  if (!currentUser) {
    document.querySelector('.profile-large-avatar').textContent = 'G';
    document.querySelector('#profile-view h3').textContent = 'Guest User';
    return;
  }
  document.querySelector('.profile-large-avatar').textContent = (currentUser.name||'U')[0].toUpperCase();
  document.querySelector('#profile-view h3').textContent = currentUser.name || 'User';
  document.querySelector('.profile-header p').textContent = currentUser.email || '';

  // Load recent orders
  if (authToken) {
    try {
      const res = await api('GET', '/orders/history/?limit=3');
      if (res.success && res.data?.orders?.length) {
        let section = document.querySelector('.orders-mini');
        if (!section) { section = document.createElement('div'); section.className='orders-mini'; document.querySelector('.settings-list').prepend(section); }
        section.innerHTML = '<h4 style="font-size:13px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px">Recent Orders</h4>' +
          res.data.orders.map(o => `
            <div class="order-mini-card">
              <div class="order-mini-header">
                <span class="order-mini-num">${o.order_number}</span>
                <span class="order-mini-date">${new Date(o.created_at).toLocaleDateString('en-IN')}</span>
              </div>
              <div class="order-mini-items">${o.items_count} item(s) · ${o.mood||''}${MOOD_EMOJI[o.mood]||''}</div>
              <div class="order-mini-total">${formatPrice(o.total)} · <span style="color:var(--success)">${o.status}</span></div>
              <div style="display:flex;gap:8px;margin-top:8px">
                <button class="primary-btn" style="flex:1;padding:8px" onclick="reorder(${o.order_id})">Reorder</button>
              </div>
            </div>`).join('');
      }
    } catch(e) {}
  }
}

async function reorder(orderId) {
  showLoader();
  try {
    const res = await api('POST', `/orders/${orderId}/reorder/`);
    if (res.success) { toast(`${res.data.items_added} item(s) added to cart! 🛒`, 'success'); cartCount = res.data.items_added; updateCartBadge(); switchView('cart'); }
  } catch(e) { toast('Could not reorder'); }
  finally { hideLoader(); }
}

// Dark mode toggle
document.querySelector('.set-item .toggle')?.parentElement?.addEventListener('click', function() {
  document.body.classList.toggle('dark');
  this.querySelector('.toggle').textContent = document.body.classList.contains('dark') ? '⚫' : '⚪';
  toast(document.body.classList.contains('dark') ? 'Dark mode on 🌙' : 'Light mode on ☀️');
});

// ── Bito mascot ───────────────────────────────────────────────────────────────
function bitaSay(msg) {
  const speech = document.getElementById('bito-speech');
  if (!speech) return;
  speech.textContent = msg;
  speech.classList.add('visible');
  clearTimeout(bitaSay._t);
  bitaSay._t = setTimeout(() => speech.classList.remove('visible'), 5000);
}

document.getElementById('bito-container')?.addEventListener('click', () => {
  const msgs = ["What can I get for you? 😊","I'll find something delicious!","Tell me your mood and I'll match it!","Psst — try the mood-based recommendations!"];
  bitaSay(msgs[Math.floor(Math.random()*msgs.length)]);
});

// ── Voice (Web Speech API) ────────────────────────────────────────────────────
let recognition;
function startVoice(btn) {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    toast("Voice not supported on this browser. Try Chrome."); return;
  }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.lang = 'en-IN';
  recognition.interimResults = false;
  btn.classList.add('recording');
  bitaSay("Listening… speak your mood or craving! 🎤");
  recognition.onresult = async e => {
    const text = e.results[0][0].transcript;
    btn.classList.remove('recording');
    bitaSay(`I heard: "${text}" — analyzing mood…`);
    try {
      if (authToken) {
        const res = await api('POST', '/ai/analyze-text/', {text, context:{time_of_day: getTimeOfDay()}});
        if (res.success) {
          const mood = res.data.mood_analysis.primary_mood;
          currentMood = mood;
          localStorage.setItem('mb_mood', mood);
          const emoji = res.data.mood_analysis.emoji;
          bitaSay(`Detected: ${mood} ${emoji} — showing matching food!`);
          document.getElementById('home-mood-label').textContent = mood.charAt(0).toUpperCase()+mood.slice(1);
          loadHomeRecs();
          switchView('recommendations');
        }
      } else {
        toast(`Heard: "${text}"`);
      }
    } catch(err) { toast('Could not analyze. Try again.', 'error'); }
  };
  recognition.onerror = () => { btn.classList.remove('recording'); bitaSay("Couldn't hear that. Please try again."); };
  recognition.onend   = () => btn.classList.remove('recording');
  recognition.start();
}

function getTimeOfDay() {
  const h = new Date().getHours();
  if (h < 12) return 'morning';
  if (h < 17) return 'afternoon';
  if (h < 21) return 'evening';
  return 'night';
}

// Wire all voice trigger buttons
document.querySelectorAll('.voice-trigger').forEach(btn => {
  btn.addEventListener('click', () => startVoice(btn));
});

// ── Bottom nav routing ────────────────────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => switchView(btn.dataset.view));
});

// ── Init ──────────────────────────────────────────────────────────────────────
function init() {
  const splashView = document.getElementById('splash-view');
  splashView.classList.add('active');

  setTimeout(() => {
    const onboarded = localStorage.getItem('mb_onboarded');
    if (currentUser && authToken) {
      switchView('home');
      loadCart(); // get cart count on startup
    } else if (onboarded) {
      switchView('login');
    } else {
      switchView('onboarding-1');
    }
  }, 1800);
}

init();
