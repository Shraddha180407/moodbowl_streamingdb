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

// Returns true only when the logged-in user has staff/admin privileges
function isAdmin() { return !!(currentUser && currentUser.is_staff); }


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
  const mainViews = ['home','explore','cart','favorites','profile','recommendations'];
  const nav = document.querySelector('.bottom-nav');
  const bito = document.getElementById('bito-container');
  if (mainViews.includes(view)) {
    if (nav) nav.style.display = 'flex';
    if (bito) bito.style.display = 'block';
    document.querySelectorAll('.nav-item').forEach(b => {
      b.classList.toggle('active', b.dataset.view === view);
    });
  } else {
    if (nav) nav.style.display = 'none';
    if (bito) bito.style.display = 'none';
  }
}

let favoritesList = JSON.parse(localStorage.getItem('mb_favorites') || '[]');

function toggleFavorite(itemId, btn) {
  const idx = favoritesList.indexOf(itemId);
  if (idx > -1) {
    favoritesList.splice(idx, 1);
    btn.textContent = '🤍';
    toast('Removed from saved items');
  } else {
    favoritesList.push(itemId);
    btn.textContent = '❤️';
    toast('Saved to your favorites! ❤️', 'success');
  }
  localStorage.setItem('mb_favorites', JSON.stringify(favoritesList));
  if (document.getElementById('favorites-view').classList.contains('active')) {
    loadFavorites();
  }
}

async function loadFavorites() {
  const container = document.getElementById('favorites-list');
  if (!container) return;
  if (!favoritesList.length) {
    container.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted)">No saved items yet</div>';
    return;
  }
  container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted)">Loading…</div>';
  try {
    const res = await api('GET', '/menu/items/?limit=50');
    if (res.success && res.data?.items) {
      const allItems = res.data.items;
      const favItems = allItems.filter(item => favoritesList.includes(item.id));
      if (!favItems.length) {
        container.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted)">No saved items yet</div>';
        return;
      }
      const FOOD_EMOJI = {main_course:'🍛',comfort_food:'🍲',healthy:'🥗',dessert:'🍰',beverage:'🧃',starter:'🥗',street_food:'🌯',breakfast:'🥞',snack:'🍿'};
      container.innerHTML = favItems.map(item => {
        const isFav = favoritesList.includes(item.id);
        const imgContent = item.image ? `<img src="${item.image}" alt="${item.name}" style="width:100%; height:100%; object-fit:cover; border-radius:inherit;" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'">` : '';
        const fallbackContent = `<span style="${item.image ? 'display:none;' : 'display:flex;'} justify-content:center; align-items:center; width:100%; height:100%;">${FOOD_EMOJI[item.category]||'🍽️'}</span>`;
        return `
        <div class="food-card">
          <div class="food-card-img" style="overflow:hidden; display:flex; align-items:center; justify-content:center; background:#fee2e6; position:relative;">
            ${imgContent}${fallbackContent}
          </div>
          <div class="food-card-body">
            <div class="food-card-name">${item.name}</div>
            <div class="food-card-sub">${item.cuisine} · ${item.category.replace('_',' ')} · ${item.is_vegetarian?'🟢':'🔴'}</div>
            <div class="food-card-row">
              <span class="food-card-price">${formatPrice(item.price)}</span>
              <span class="food-card-rating">${formatRating(item.rating)}</span>
              <div style="display:flex; gap:8px; align-items:center;">
                <button class="fav-icon-btn" onclick="toggleFavorite(${item.id}, this)" style="background:none; border:none; font-size:18px; cursor:pointer; padding:0; outline:none;">${isFav?'❤️':'🤍'}</button>
                <button class="food-card-add" onclick="addToCart(${item.id}, '${item.name.replace(/'/g,"\\'")}', ${item.price})">+ Add</button>
              </div>
            </div>
          </div>
        </div>`;
      }).join('');
    } else {
      container.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted)">Could not load saved items</div>';
    }
  } catch (err) {
    container.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted)">Connection error</div>';
  }
}

let hasAutoGreeted = false;

function onViewEnter(view) {
  if (view === 'home') {
    loadHomeRecs();
    renderAdminDashboardButton();   // show/hide the ⚙️ Live Dashboard button
    if (!hasAutoGreeted) {
      hasAutoGreeted = true;
      setTimeout(autoGreetAndListen, 500);
    }
  }
  if (view === 'mood-selection') {
    if (!hasAutoGreeted) {
      hasAutoGreeted = true;
      setTimeout(autoGreetAndListen, 500);
    }
  }
  if (view === 'explore') loadExplore();
  if (view === 'cart') loadCart();
  if (view === 'favorites') loadFavorites();
  if (view === 'profile') loadProfile();
  if (view === 'recommendations') loadRecommendations();
}

// ── Auth ──────────────────────────────────────────────────────────────────────
async function performAuth(mode) {
  const email = document.getElementById('login-email').value.trim().toLowerCase();
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
      toast('Welcome to MoodBowl! 🎉', 'success');
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

async function loginAsGuest() {
  try {
    showLoader();
    const res = await api('POST', '/auth/login/', {email: 'user1@moodbite.demo', password: 'demo1234'});
    if (res.success || res.token) {
      authToken  = res.token.access;
      refreshTok = res.token.refresh;
      currentUser = res.data;
      localStorage.setItem('mb_access',  authToken);
      localStorage.setItem('mb_refresh', refreshTok);
      localStorage.setItem('mb_user', JSON.stringify(currentUser));
      toast('Welcome to MoodBowl! 🎉', 'success');
      switchView('mood-selection');
    } else {
      toast('Guest login failed. Try typing demo login instead.', 'error');
    }
  } catch(e) {
    toast('Network error during guest login.', 'error');
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

// ── Admin-only Dashboard Button ───────────────────────────────────────────────
/**
 * Injects (or removes) the "Live Dashboard" button in the home view.
 * Visible ONLY when the logged-in user has is_staff === true.
 * The button opens /dashboard/ in a new tab.
 */
function renderAdminDashboardButton() {
  // Remove any existing admin button first to avoid duplicates
  const existing = document.getElementById('admin-dashboard-btn');
  if (existing) existing.remove();

  if (!isAdmin()) return;   // ← nothing to show for non-admins

  // Build button element
  const btn = document.createElement('div');
  btn.id = 'admin-dashboard-btn';
  btn.style.cssText = 'margin-top: 14px; display: flex; justify-content: center;';
  btn.innerHTML = `
    <button
      onclick="openAdminDashboard()"
      style="
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, #f97316 0%, #a855f7 100%);
        border: none;
        padding: 10px 22px;
        border-radius: 24px;
        color: white;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 18px rgba(249,115,22,0.40);
        transition: transform 0.18s, box-shadow 0.18s;
        outline: none;
        letter-spacing: 0.3px;
      "
      onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 6px 24px rgba(249,115,22,0.55)'"
      onmouseout="this.style.transform='';this.style.boxShadow='0 4px 18px rgba(249,115,22,0.40)'"
      title="Admin only — opens the live analytics dashboard"
    >
      <span style="display:inline-block;width:8px;height:8px;background:#4ade80;border-radius:50%;animation:livePulse 1.5s infinite;flex-shrink:0;"></span>
      ⚙️ Live Dashboard
    </button>`;

  // Insert it inside the main-mic-section, after the live-waiter button wrapper
  const micSection = document.querySelector('.main-mic-section');
  if (micSection) {
    micSection.appendChild(btn);
  }
}

function openAdminDashboard() {
  if (!isAdmin()) {
    toast('Access denied — admin only 🔒', 'error');
    return;
  }
  // Pass the JWT in a query param so Django can verify admin status
  // (The dashboard view checks Bearer token via SimpleJWT)
  const url = `/dashboard/?token=${encodeURIComponent(authToken || '')}`;
  window.open(url, '_blank');
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
  container.innerHTML = items.map(item => {
    const itemId = item.item_id || item.id;
    const isFav = favoritesList.includes(itemId);
    const imgContent = item.image ? `<img src="${item.image}" alt="${item.name}" style="width:100%; height:100%; object-fit:cover; border-radius:inherit;" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'">` : '';
    const fallbackContent = `<span style="${item.image ? 'display:none;' : 'display:flex;'} justify-content:center; align-items:center; width:100%; height:100%;">${FOOD_EMOJI[item.category]||'🍽️'}</span>`;
    return `
    <div class="food-card" data-id="${itemId}">
      <div class="food-card-img" style="overflow:hidden; display:flex; align-items:center; justify-content:center; background:#fee2e6; position:relative;">
        ${imgContent}${fallbackContent}
      </div>
      <div class="food-card-body">
        <div class="food-card-name">${item.name}</div>
        <div class="food-card-sub">${item.cuisine} · ${item.is_vegetarian?'🟢 Veg':'🔴 Non-veg'}</div>
        <div class="food-card-row">
          <span class="food-card-price">${formatPrice(item.price)}</span>
          <span class="food-card-rating">${formatRating(item.rating)}</span>
          <div style="display:flex; gap:8px; align-items:center;">
            <button class="fav-icon-btn" onclick="event.stopPropagation(); toggleFavorite(${itemId}, this)" style="background:none; border:none; font-size:18px; cursor:pointer; padding:0; outline:none;">${isFav?'❤️':'🤍'}</button>
            ${showAdd ? `<button class="food-card-add" onclick="addToCart(${itemId}, '${item.name.replace(/'/g,"\\'")}', ${item.price})">+ Add</button>` : ''}
          </div>
        </div>
      </div>
    </div>`;
  }).join('');
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
  container.innerHTML = items.map(item => {
    const isFav = favoritesList.includes(item.id);
    const imgContent = item.image ? `<img src="${item.image}" alt="${item.name}" style="width:100%; height:100%; object-fit:cover; border-radius:inherit;" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'">` : '';
    const fallbackContent = `<span style="${item.image ? 'display:none;' : 'display:flex;'} justify-content:center; align-items:center; width:100%; height:100%;">${FOOD_EMOJI[item.category]||'🍽️'}</span>`;
    return `
    <div class="food-card">
      <div class="food-card-img" style="overflow:hidden; display:flex; align-items:center; justify-content:center; background:#fee2e6; position:relative;">
        ${imgContent}${fallbackContent}
      </div>
      <div class="food-card-body">
        <div class="food-card-name">${item.name}</div>
        <div class="food-card-sub">${item.cuisine} · ${item.category.replace('_',' ')} · ${item.is_vegetarian?'🟢':'🔴'}</div>
        <div class="food-card-row">
          <span class="food-card-price">${formatPrice(item.price)}</span>
          <span class="food-card-rating">${formatRating(item.rating)}</span>
          <div style="display:flex; gap:8px; align-items:center;">
            <button class="fav-icon-btn" onclick="toggleFavorite(${item.id}, this)" style="background:none; border:none; font-size:18px; cursor:pointer; padding:0; outline:none;">${isFav?'❤️':'🤍'}</button>
            <button class="food-card-add" onclick="addToCart(${item.id}, '${item.name.replace(/'/g,"\\'")}', ${item.price})">+ Add</button>
          </div>
        </div>
      </div>
    </div>`;
  }).join('');
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
      const itemId = top.item_id || top.id;
      
      const tp = document.querySelector('.top-pick-card .card-body');
      if (tp) {
        tp.querySelector('h5').textContent = top.name;
        tp.querySelector('.card-price').textContent = formatPrice(top.price);
        tp.querySelector('.vendor').textContent = top.cuisine + ' · ' + top.category.replace('_',' ');
        tp.querySelector('.card-desc').textContent = top.recommendation_reason;
        tp.querySelector('.cart-add').onclick = () => addToCart(itemId, top.name, top.price);
      }
      
      const tp_img = document.querySelector('.top-pick-card .card-img');
      if (tp_img) {
        const FOOD_EMOJI = {main_course:'🍛',comfort_food:'🍲',healthy:'🥗',dessert:'🍰',beverage:'🧃',starter:'🥗',street_food:'🌯',breakfast:'🥞',snack:'🍿'};
        const emoji = FOOD_EMOJI[top.category] || '🍛';
        const imgContent = top.image ? `<img src="${top.image}" alt="${top.name}" style="width:100%; height:100%; object-fit:cover; border-radius:inherit;" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'">` : '';
        const fallbackContent = `<span style="${top.image ? 'display:none;' : 'display:flex;'} justify-content:center; align-items:center; width:100%; height:100%; font-size:52px;">${emoji}</span>`;
        tp_img.innerHTML = `${imgContent}${fallbackContent}`;
      }
      
      const favBtn = document.querySelector('.top-pick-card .fav-btn');
      if (favBtn) {
        const isFav = favoritesList.includes(itemId);
        favBtn.textContent = isFav ? '❤️' : '🤍';
        favBtn.onclick = () => toggleFavorite(itemId, favBtn);
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
  
  // Verbally speak the message out loud (strip emojis first)
  const cleanMsg = msg.replace(/[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF]/g, "");
  speakTextLocal(cleanMsg);
}

document.getElementById('bito-container')?.addEventListener('click', () => {
  const msgs = ["What can I get for you? 😊","I'll find something delicious!","Tell me your mood and I'll match it!","Psst — try the mood-based recommendations!"];
  bitaSay(msgs[Math.floor(Math.random()*msgs.length)]);
});

// ── Voice Command Control ──────────────────────────────────────────────────────
let loadedMenuItems = [];
async function cacheMenuItems() {
  try {
    const res = await api('GET', '/menu/items/?limit=50');
    if (res.success && res.data?.items) {
      loadedMenuItems = res.data.items;
      console.log("[VoiceControl] Cached menu items for voice matching:", loadedMenuItems.length);
    }
  } catch(e) {
    console.error("[VoiceControl] Failed to cache menu items:", e);
  }
}

function parseVoiceCommand(text) {
  if (!text) return false;
  const cleanText = text.toLowerCase().trim();
  console.log("[VoiceControl] Parsing command: ", cleanText);
  
  // Cart / Checkout navigation
  if (cleanText.includes("cart") || cleanText.includes("checkout") || cleanText.includes("basket") || cleanText.includes("check out")) {
    switchView('cart');
    bitaSay("Opening your cart! 🛒");
    return true;
  }

  // Explore / Menu navigation
  if (cleanText.includes("explore") || cleanText.includes("menu") || cleanText.includes("search") || cleanText.includes("browse") || cleanText.includes("dishes")) {
    switchView('explore');
    bitaSay("Opening the Explore menu! 🔍");
    return true;
  }

  // Home navigation
  if (cleanText.includes("home") || cleanText.includes("go back") || cleanText.includes("main page")) {
    switchView('home');
    bitaSay("Going to the home screen. 🏠");
    return true;
  }

  // Favorites / Saved navigation
  if (cleanText.includes("favorite") || cleanText.includes("saved") || cleanText.includes("wishlist")) {
    switchView('favorites');
    bitaSay("Opening your saved favorites! ❤️");
    return true;
  }

  // Profile / Settings navigation
  if (cleanText.includes("profile") || cleanText.includes("account") || cleanText.includes("setting")) {
    switchView('profile');
    bitaSay("Opening your profile. 👤");
    return true;
  }
  
  // Add item to cart by name
  if (cleanText.includes("add") || cleanText.includes("order") || cleanText.includes("buy") || cleanText.includes("put")) {
    for (const item of loadedMenuItems) {
      const itemNameLower = item.name.toLowerCase();
      if (cleanText.includes(itemNameLower)) {
        addToCart(item.id, item.name, item.price);
        bitaSay(`Added ${item.name} to your cart! 🛒`);
        return true;
      }
    }
  }
  
  return false;
}

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
    if (parseVoiceCommand(text)) {
      return;
    }
    bitaSay(`I heard: "${text}" — analyzing mood…`);
    try {
      if (authToken) {
        const res = await api('POST', '/ai/analyze-text/', {text, context:{time_of_day: getTimeOfDay()}});
        if (res.success) {
          const mood = res.data.mood_analysis.primary_mood;
          const conf = res.data.mood_analysis.confidence || 0;
          if (mood === 'unknown' || conf <= 0.1) {
            bitaSay("I didn't quite catch your mood! Try saying 'I feel happy', 'stressed', 'tired', or ask me to 'open cart'!");
            return;
          }
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
}

let isContinuousListening = false;
let continuousRecognition = null;

function autoGreetAndListen() {
  const greeting = "Welcome to MoodBite! Tell me your mood or what you feel like eating today!";
  bitaSay(greeting);
  setTimeout(() => {
    startContinuousVoice();
  }, 3200);
}

function startContinuousVoice() {
  if (isContinuousListening) return;
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) return;
  
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  continuousRecognition = new SR();
  continuousRecognition.lang = 'en-IN';
  continuousRecognition.continuous = true;
  continuousRecognition.interimResults = false;
  
  const micBtns = document.querySelectorAll('.voice-trigger');
  micBtns.forEach(btn => btn.classList.add('recording'));
  
  continuousRecognition.onresult = async e => {
    const text = e.results[e.results.length - 1][0].transcript.trim();
    if (!text) return;
    console.log("[ContinuousVoice] Heard:", text);
    
    if (parseVoiceCommand(text)) return;
    
    bitaSay(`I heard: "${text}" — finding matching meals…`);
    try {
      if (authToken) {
        const res = await api('POST', '/ai/analyze-text/', {text, context:{time_of_day: getTimeOfDay()}});
        if (res.success) {
          const mood = res.data.mood_analysis.primary_mood;
          const conf = res.data.mood_analysis.confidence || 0;
          if (mood === 'unknown' || conf <= 0.1) {
            bitaSay("I didn't quite catch your mood! Try saying 'I feel happy', 'stressed', 'tired', or ask me to 'open cart'!");
            return;
          }
          currentMood = mood;
          localStorage.setItem('mb_mood', mood);
          const emoji = res.data.mood_analysis.emoji;
          bitaSay(`Detected: ${mood} ${emoji} — showing recommendations!`);
          const labelEl = document.getElementById('home-mood-label');
          if (labelEl) labelEl.textContent = mood.charAt(0).toUpperCase()+mood.slice(1);
          loadHomeRecs();
          switchView('recommendations');
        }
      } else {
        toast(`Heard: "${text}"`);
      }
    } catch(err) { toast('Could not analyze. Try speaking again.', 'error'); }
  };
  
  continuousRecognition.onerror = (err) => {
    console.warn("[ContinuousVoice] Error:", err);
  };
  
  continuousRecognition.onend = () => {
    const currentView = document.querySelector('.view.active')?.id;
    if (isContinuousListening && (currentView === 'home-view' || currentView === 'mood-selection-view')) {
      try { continuousRecognition.start(); } catch(e) {}
    } else {
      micBtns.forEach(btn => btn.classList.remove('recording'));
      isContinuousListening = false;
    }
  };
  
  try {
    continuousRecognition.start();
    isContinuousListening = true;
    toast("AI Waiter is listening continuously 🎙️", "info");
  } catch(e) {
    console.error("[ContinuousVoice] Start error:", e);
  }
}

function getTimeOfDay() {
  const h = new Date().getHours();
  if (h < 12) return 'morning';
  if (h < 17) return 'afternoon';
  if (h < 21) return 'evening';
  return 'night';
}

// ── Live Voice Waiter (Gemini Live API WebSocket Stream) ──────────────────────
let liveWs = null;
let liveAudioCtx = null;
let liveMediaStream = null;
let liveProcessor = null;
let liveAudioQueue = [];
let isLivePlaying = false;
let livePlayCtx = null;

function showCallUI(show) {
  const modal = document.getElementById('live-call-modal');
  if (!modal) return;
  modal.style.display = show ? 'flex' : 'none';
}

function updateCallStatus(text) {
  const el = document.getElementById('live-call-status');
  if (el) el.textContent = text;
}

function updateCallTranscript(text) {
  const el = document.getElementById('live-call-transcript');
  if (el) el.textContent = `"${text}"`;
}

let isMockSession = false;
let callRecognition = null;

function speakTextLocal(text) {
  if ('speechSynthesis' in window) {
    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      const voices = window.speechSynthesis.getVoices();
      const engVoice = voices.find(v => v.lang.startsWith('en'));
      if (engVoice) utterance.voice = engVoice;
      utterance.rate = 0.95;
      window.speechSynthesis.speak(utterance);
    } catch(e) {
      console.error("Local TTS Error:", e);
    }
  }
}

function startLocalSpeechForCall() {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) return;
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  callRecognition = new SR();
  callRecognition.lang = 'en-IN';
  callRecognition.continuous = true;
  callRecognition.interimResults = false;
  
  callRecognition.onresult = (e) => {
    const text = e.results[e.results.length - 1][0].transcript.trim();
    if (text) {
      console.log("[CallRecognition] Heard:", text);
      const userTranscript = document.getElementById('live-call-transcript');
      if (userTranscript) userTranscript.textContent = `You: "${text}"`;
      
      // Parse for local voice commands
      if (parseVoiceCommand(text)) {
        return;
      }
      
      if (liveWs && liveWs.readyState === WebSocket.OPEN) {
        liveWs.send(JSON.stringify({ client_content: text }));
      }
    }
  };
  
  callRecognition.onerror = (err) => {
    console.error("[CallRecognition] Error:", err);
  };
  
  callRecognition.onend = () => {
    if (liveWs && liveWs.readyState === WebSocket.OPEN && isMockSession) {
      try { callRecognition.start(); } catch(err) {}
    }
  };
  
  try { callRecognition.start(); } catch(err) {}
}

async function startLiveSession() {
  isMockSession = false;
  updateCallStatus("Connecting to Live Voice Stream…");
  updateCallTranscript("Waiting for response…");
  showCallUI(true);

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/voice/?user_id=${(currentUser && currentUser.id) || 1}&session_id=live`;
  
  console.log("[LiveSession] Connecting to:", wsUrl);
  liveWs = new WebSocket(wsUrl);
  liveWs.binaryType = 'arraybuffer';

  liveWs.onopen = async () => {
    updateCallStatus("Connected. Initializing microphone…");
    try {
      liveMediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      liveAudioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      const source = liveAudioCtx.createMediaStreamSource(liveMediaStream);
      
      liveProcessor = liveAudioCtx.createScriptProcessor(4096, 1, 1);
      source.connect(liveProcessor);
      liveProcessor.connect(liveAudioCtx.destination);
      
      liveProcessor.onaudioprocess = (e) => {
        if (!liveWs || liveWs.readyState !== WebSocket.OPEN) return;
        // Only stream raw PCM if it's not a mock session (mock session transcribes locally)
        if (isMockSession) return;
        const inputData = e.inputBuffer.getChannelData(0);
        const pcmData = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          const val = Math.max(-1, Math.min(1, inputData[i]));
          pcmData[i] = val < 0 ? val * 0x8000 : val * 0x7FFF;
        }
        liveWs.send(pcmData.buffer);
      };
      updateCallStatus("Listening… Talk naturally!");
    } catch (err) {
      console.error("[LiveSession] Microphone access error:", err);
      updateCallStatus("Failed to access microphone");
      toast("Could not access microphone.", "error");
      endCall();
    }
  };

  liveWs.onmessage = (e) => {
    if (typeof e.data === 'string') {
      try {
        const payload = JSON.parse(e.data);
        if (payload.error) {
          toast(payload.error, "error");
          endCall();
          return;
        }
        const serverContent = payload.server_content;
        if (serverContent) {
          if (serverContent.is_mock) {
            if (!isMockSession) {
              isMockSession = true;
              startLocalSpeechForCall();
            }
            if (serverContent.text) {
              speakTextLocal(serverContent.text);
            }
          }
          if (serverContent.text) {
            console.log("[LiveSession] Text:", serverContent.text);
            updateCallTranscript(serverContent.text);
          } else if (serverContent.inline_data) {
            playAudioChunk(serverContent.inline_data);
          }
        }
      } catch (err) {
        console.error("[LiveSession] Message parsing error:", err);
      }
    }
  };

  liveWs.onclose = () => {
    console.log("[LiveSession] Closed");
    endCall();
  };

  liveWs.onerror = (err) => {
    console.error("[LiveSession] WebSocket error:", err);
    endCall();
  };
}

function playAudioChunk(base64Data) {
  const binaryString = atob(base64Data);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  liveAudioQueue.push(bytes.buffer);
  if (!isLivePlaying) {
    playNextChunk();
  }
}

async function playNextChunk() {
  if (liveAudioQueue.length === 0) {
    isLivePlaying = false;
    return;
  }
  isLivePlaying = true;
  const chunk = liveAudioQueue.shift();
  if (!livePlayCtx) {
    livePlayCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  try {
    const int16View = new Int16Array(chunk);
    const float32Data = new Float32Array(int16View.length);
    for (let i = 0; i < int16View.length; i++) {
      float32Data[i] = int16View[i] / 32768.0;
    }
    
    const audioBuffer = livePlayCtx.createBuffer(1, float32Data.length, 24000);
    audioBuffer.copyToChannel(float32Data, 0);
    
    const source = livePlayCtx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(livePlayCtx.destination);
    source.onended = () => {
      playNextChunk();
    };
    source.start();
  } catch (err) {
    console.error("[LiveSession] Playback error:", err);
    playNextChunk();
  }
}

function endCall() {
  showCallUI(false);
  isMockSession = false;
  if ('speechSynthesis' in window) {
    try { window.speechSynthesis.cancel(); } catch(e) {}
  }
  if (callRecognition) {
    try { callRecognition.abort(); } catch(e) {}
    callRecognition = null;
  }
  if (liveProcessor) {
    try { liveProcessor.disconnect(); } catch(e) {}
    liveProcessor = null;
  }
  if (liveMediaStream) {
    try { liveMediaStream.getTracks().forEach(track => track.stop()); } catch(e) {}
    liveMediaStream = null;
  }
  if (liveAudioCtx) {
    try { liveAudioCtx.close(); } catch(e) {}
    liveAudioCtx = null;
  }
  if (liveWs) {
    if (liveWs.readyState === WebSocket.OPEN) {
      try { liveWs.close(); } catch(e) {}
    }
    liveWs = null;
  }
  liveAudioQueue = [];
  isLivePlaying = false;
}

// Wire up the live waiter button and end call button
document.getElementById('live-waiter-btn')?.addEventListener('click', startLiveSession);
document.getElementById('end-call-btn')?.addEventListener('click', endCall);

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
  cacheMenuItems();

  // Show a toast if we were redirected after a failed dashboard access attempt
  if (new URLSearchParams(window.location.search).get('dashboard_denied') === '1') {
    setTimeout(() => toast('Dashboard is admin-only 🔒', 'error'), 2200);
    history.replaceState(null, '', '/app/'); // clean up the URL
  }

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
