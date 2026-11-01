/* ==============================================================================
   BhashaLok — Digital Regional Language & Dialect Preservation Platform
   Frontend JavaScript Engine (Vanilla JS + Live FastAPI Integration)
   ============================================================================== */

// 1. Dynamic API Base Configuration (Localhost / Production on Render)
const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? (window.location.port === "8000" ? "/api/v1" : "http://127.0.0.1:8000/api/v1")
  : (window.ROOTTALK_API_URL || "https://roottalk-backend.onrender.com/api/v1");

// Helper for root API (for direct /api/categories, /api/contributors, /api/voices)
const ROOT_API = API_BASE.endsWith("/api/v1") ? API_BASE.slice(0, -3) : API_BASE;

// Global Application State
let currentSection = "home";
let currentCategory = "All";
let currentPOS = "All";
let currentDialect = "All";
let currentPage = 1;
let pageSize = 12;
let totalPages = 1;
let totalEntriesCount = 0;
let isPhoneticActive = false;
let searchDebounceTimer = null;

let lexiconData = [];
let audioVoices = [];
let allCategories = [];
let allDialects = [];
let allContributors = [];
let adminEntriesData = [];
let adminFilterStatus = "All";

let activeAudio = null;
let todaysWordEntry = null;
let authToken = localStorage.getItem("bhashalok_token") || null;
let currentUser = null;

// Real MediaRecorder & Audio Upload State
let mediaStream = null;
let mediaRecorder = null;
let audioChunks = [];
let recordedAudioBlob = null;
let recordTimerInterval = null;
let recordSeconds = 0;
let selectedAudioFile = null;

// Quiz State
let quizDecks = [];
let activeQuizDeck = null;
let activeQuestions = [];
let currentQuestionIndex = 0;
let userQuizAnswers = [];
let selectedOptionLetter = null;

// Leaflet Map State
let leafletMap = null;
let mapMarkers = [];
let activeMapDialect = null;

// WebSocket State
let activitySocket = null;

// ==============================================================================
// 2. INITIALIZATION ON DOM READY
// ==============================================================================
document.addEventListener("DOMContentLoaded", async () => {
  // Pre-load Web Speech Synthesis voices
  if ("speechSynthesis" in window) {
    window.speechSynthesis.getVoices();
  }

  // Restore session if token exists
  await restoreUserSession();

  // Load initial backend resources
  await Promise.all([
    fetchBackendStats(),
    fetchCategories(),
    fetchDialects(),
    fetchLexiconEntries(1),
    fetchAudioRecordings(),
    fetchContributors(),
    fetchQuizDecks()
  ]);

  // Load Today's Word
  await fetchTodaysWord();

  // Initialize Map
  initDialectMap();

  // Connect WebSocket Activity Feed
  initWebSocketActivityStream();
});


// ==============================================================================
// 3. AUTHENTICATION & USER SESSION
// ==============================================================================
async function restoreUserSession() {
  if (!authToken) {
    updateAuthUI(null);
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (res.ok) {
      currentUser = await res.json();
      updateAuthUI(currentUser);
    } else {
      // Token invalid or expired
      localStorage.removeItem("bhashalok_token");
      authToken = null;
      currentUser = null;
      updateAuthUI(null);
    }
  } catch (err) {
    console.warn("Auth check error, offline or server starting up.");
  }
}

function updateAuthUI(user) {
  const container = document.getElementById("header-auth-container");
  const mobileContainer = document.getElementById("mobile-auth-container");
  if (!container) return;

  if (user) {
    const roleBadge = user.role === "Admin" ? "bg-rose-100 text-rose-800" :
                      user.role === "Linguist" ? "bg-purple-100 text-purple-800" : "bg-emerald-100 text-emerald-800";
    
    container.innerHTML = `
      <div class="flex items-center gap-2">
        <div class="text-right hidden sm:block">
          <div class="text-xs font-bold text-slate-900">${user.full_name || user.username}</div>
          <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full ${roleBadge}">${user.role}</span>
        </div>
        <button onclick="handleLogout()" title="Sign Out" class="p-2 text-slate-500 hover:text-rose-600 rounded-lg hover:bg-slate-100 transition text-sm">
          <i class="fa-solid fa-arrow-right-from-bracket"></i>
        </button>
      </div>
    `;

    if (mobileContainer) {
      mobileContainer.innerHTML = `
        <div class="flex items-center justify-between py-2 text-sm">
          <span class="font-bold text-slate-800">${user.username} (${user.role})</span>
          <button onclick="handleLogout(); toggleMobileMenu()" class="text-rose-600 font-semibold text-xs">Logout</button>
        </div>
      `;
    }
  } else {
    container.innerHTML = `
      <button onclick="openAuthModal()" id="btn-login-header" class="px-3.5 py-1.5 text-xs font-semibold bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition flex items-center gap-1.5">
        <i class="fa-solid fa-right-to-bracket"></i> <span>Login</span>
      </button>
    `;

    if (mobileContainer) {
      mobileContainer.innerHTML = `
        <button onclick="openAuthModal(); toggleMobileMenu()" class="w-full py-2 bg-emerald-800 text-white rounded-lg text-sm font-semibold text-center">Login / Sign In</button>
      `;
    }
  }
}

function openAuthModal() {
  document.getElementById("auth-modal").classList.remove("hidden");
  switchAuthTab('login');
}

function closeAuthModal() {
  document.getElementById("auth-modal").classList.add("hidden");
  document.getElementById("login-error-msg").classList.add("hidden");
  document.getElementById("register-error-msg").classList.add("hidden");
}

function switchAuthTab(tab) {
  const loginTab = document.getElementById("auth-tab-login");
  const regTab = document.getElementById("auth-tab-register");
  const loginForm = document.getElementById("form-login");
  const regForm = document.getElementById("form-register");

  if (tab === "login") {
    loginTab.className = "flex-1 pb-3 text-sm font-bold text-emerald-800 border-b-2 border-emerald-800";
    regTab.className = "flex-1 pb-3 text-sm font-bold text-slate-400 border-b-2 border-transparent";
    loginForm.classList.remove("hidden");
    regForm.classList.add("hidden");
  } else {
    loginTab.className = "flex-1 pb-3 text-sm font-bold text-slate-400 border-b-2 border-transparent";
    regTab.className = "flex-1 pb-3 text-sm font-bold text-emerald-800 border-b-2 border-emerald-800";
    loginForm.classList.add("hidden");
    regForm.classList.remove("hidden");
  }
}

async function handleLoginSubmit(e) {
  e.preventDefault();
  const username = document.getElementById("login-username").value.trim();
  const password = document.getElementById("login-password").value;
  const errorEl = document.getElementById("login-error-msg");
  errorEl.classList.add("hidden");

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    if (res.ok) {
      const data = await res.json();
      authToken = data.access_token;
      currentUser = data.user;
      localStorage.setItem("bhashalok_token", authToken);
      updateAuthUI(currentUser);
      closeAuthModal();
      showToast(`Welcome back, ${currentUser.full_name || currentUser.username}!`);
      if (currentSection === "admin") {
        fetchAdminEntries();
      }
    } else {
      const err = await res.json();
      errorEl.innerText = err.detail || "Invalid username or password";
      errorEl.classList.remove("hidden");
    }
  } catch (err) {
    errorEl.innerText = "Cannot connect to server. Ensure FastAPI backend is running.";
    errorEl.classList.remove("hidden");
  }
}

async function handleRegisterSubmit(e) {
  e.preventDefault();
  const username = document.getElementById("reg-username").value.trim();
  const full_name = document.getElementById("reg-fullname").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  const errorEl = document.getElementById("register-error-msg");
  errorEl.classList.add("hidden");

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, full_name, email, password })
    });

    if (res.ok) {
      showToast("Account created successfully! Logging in...");
      // Auto login
      document.getElementById("login-username").value = username;
      document.getElementById("login-password").value = password;
      await handleLoginSubmit(new Event("submit"));
    } else {
      const err = await res.json();
      errorEl.innerText = err.detail || "Registration failed. Try another username/email.";
      errorEl.classList.remove("hidden");
    }
  } catch (err) {
    errorEl.innerText = "Server connection error.";
    errorEl.classList.remove("hidden");
  }
}

function quickLoginDemo(role) {
  if (role === "admin") {
    document.getElementById("login-username").value = "admin";
    document.getElementById("login-password").value = "Admin123!";
  } else if (role === "linguist") {
    document.getElementById("login-username").value = "dr_chitnis";
    document.getElementById("login-password").value = "chitnis_secret";
  } else {
    document.getElementById("login-username").value = "parth_kadam";
    document.getElementById("login-password").value = "parthpassword123";
  }
  handleLoginSubmit(new Event("submit"));
}

function handleLogout() {
  localStorage.removeItem("bhashalok_token");
  authToken = null;
  currentUser = null;
  updateAuthUI(null);
  showToast("You have been signed out.");
  if (currentSection === "admin") {
    renderAdminTable();
  }
}


// ==============================================================================
// 4. NAVIGATION & SECTION SWITCHING
// ==============================================================================
function showSection(secName) {
  const sections = ['home', 'explore', 'voices', 'map', 'quizzes', 'contributors', 'contribute', 'about', 'admin'];
  sections.forEach(sec => {
    const el = document.getElementById(`sec-${sec}`);
    const navBtn = document.getElementById(`nav-${sec}`);
    if (el) el.classList.add('hidden');
    if (navBtn) navBtn.classList.remove('active');
  });

  const targetSec = document.getElementById(`sec-${secName}`);
  const targetNav = document.getElementById(`nav-${secName}`);
  if (targetSec) targetSec.classList.remove('hidden');
  if (targetNav) targetNav.classList.add('active');

  currentSection = secName;
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Section specific triggers
  if (secName === "admin") {
    fetchAdminEntries();
  } else if (secName === "map") {
    setTimeout(() => {
      if (leafletMap) leafletMap.invalidateSize();
    }, 200);
  }
}

function toggleMobileMenu() {
  const menu = document.getElementById('mobile-menu');
  menu.classList.toggle('hidden');
}

function focusGlobalSearch() {
  showSection('explore');
  setTimeout(() => {
    const input = document.getElementById('dict-search-input');
    if (input) input.focus();
  }, 200);
}


// ==============================================================================
// 5. BACKEND STATS & CATEGORIES & DIALECTS
// ==============================================================================
async function fetchBackendStats() {
  try {
    const res = await fetch(`${API_BASE}/analytics/stats`);
    if (res.ok) {
      const data = await res.json();
      document.getElementById("stat-words").innerText = (data.total_words_preserved || 155).toLocaleString();
      document.getElementById("stat-audio").innerText = (data.total_audio_recordings || 9).toLocaleString();
      document.getElementById("stat-contributors").innerText = (data.total_active_contributors || 6).toLocaleString();
      document.getElementById("stat-dialects").innerText = (data.total_dialects || 7).toLocaleString();
    }
  } catch (err) {
    console.warn("Using default metrics until server is reached.");
  }
}

async function fetchCategories() {
  try {
    const res = await fetch(`${ROOT_API}/categories`);
    if (res.ok) {
      allCategories = await res.json();
      renderCategoryPills(allCategories);
      populateCategoryDropdown(allCategories);
    }
  } catch (err) {
    console.warn("Failed to fetch dynamic categories.", err);
  }
}

function renderCategoryPills(categories) {
  const container = document.getElementById("category-pills-container");
  if (!container) return;

  const totalWords = categories.reduce((sum, c) => sum + (c.count || 0), 0) || 155;
  let html = `<button onclick="selectCategory('All')" class="filter-tag active" id="cat-All">All (${totalWords})</button>`;

  categories.forEach(cat => {
    const safeId = `cat-${cat.name.replace(/\s+/g, '-')}`;
    html += `<button onclick="selectCategory('${cat.name}')" class="filter-tag" id="${safeId}">${cat.name} (${cat.count || 0})</button>`;
  });

  container.innerHTML = html;
}

function populateCategoryDropdown(categories) {
  const select = document.getElementById("form-category");
  if (!select) return;
  select.innerHTML = "";
  categories.forEach(cat => {
    const opt = document.createElement("option");
    opt.value = cat.name;
    opt.textContent = `${cat.name} — ${cat.description || ''}`;
    select.appendChild(opt);
  });
}

async function fetchDialects() {
  try {
    const res = await fetch(`${API_BASE}/dialects/`);
    if (res.ok) {
      allDialects = await res.json();
      populateDialectDropdowns(allDialects);
      updateMapMarkers(allDialects);
    }
  } catch (err) {
    console.warn("Failed to fetch dialects.", err);
  }
}

function populateDialectDropdowns(dialects) {
  // 1. Explore filter dropdown
  const filterSelect = document.getElementById("dialect-filter");
  if (filterSelect) {
    filterSelect.innerHTML = `<option value="All">All Dialects</option>`;
    dialects.forEach(d => {
      const opt = document.createElement("option");
      opt.value = d.id;
      opt.textContent = `${d.name} (${d.region_name || 'Maharashtra'})`;
      filterSelect.appendChild(opt);
    });
  }

  // 2. Contribution form dropdown
  const formSelect = document.getElementById("form-dialect");
  if (formSelect) {
    formSelect.innerHTML = "";
    dialects.forEach(d => {
      const opt = document.createElement("option");
      opt.value = d.id;
      opt.textContent = `${d.name} (${d.region_name || 'Maharashtra'})`;
      formSelect.appendChild(opt);
    });
  }
}


// ==============================================================================
// 6. DYNAMIC "TODAY'S WORD"
// ==============================================================================
async function fetchTodaysWord() {
  try {
    const res = await fetch(`${API_BASE}/lexicon/?limit=20`);
    if (res.ok) {
      const data = await res.json();
      if (data && data.length > 0) {
        // Pick an interesting entry (e.g. index 0 or random)
        const item = data[Math.floor(Math.random() * data.length)];
        renderTodaysWord(item);
      }
    }
  } catch (err) {
    console.warn("Failed to fetch today's word dynamically.", err);
  }
}

function renderTodaysWord(item) {
  if (!item) return;
  todaysWordEntry = item;

  const dialect = allDialects.find(d => d.id === item.dialect_id);
  const dialectName = dialect ? dialect.name : (item.dialect_name || "Regional Dialect");

  document.getElementById("today-dialect").innerText = `${dialectName} Dialect`;
  document.getElementById("today-term").innerText = item.term;
  document.getElementById("today-ipa").innerText = item.ipa_transcription || "";
  document.getElementById("today-meaning-en").innerText = item.meaning_en;
  document.getElementById("today-meaning-std").innerText = item.meaning_standard_lang || "—";
  document.getElementById("today-sentence").innerText = item.example_sentence_dialect ? `"${item.example_sentence_dialect}"` : "—";
}

function fetchRandomWord() {
  if (lexiconData.length > 0) {
    const random = lexiconData[Math.floor(Math.random() * lexiconData.length)];
    renderTodaysWord(random);
    showToast(`Featured word updated: ${random.term}`);
  } else {
    fetchTodaysWord();
  }
}

function playTodayWordAudio() {
  if (!todaysWordEntry) return;
  playSampleAudio(todaysWordEntry.audio_sample_url, todaysWordEntry.term);
}

function openTodayWordModal() {
  if (!todaysWordEntry) return;
  openWordDetailModal(todaysWordEntry.id);
}


// ==============================================================================
// 7. LEXICON DICTIONARY REPOSITORY & PAGINATION
// ==============================================================================
async function fetchLexiconEntries(page = 1) {
  currentPage = page;
  const grid = document.getElementById("lexicon-grid");
  const counter = document.getElementById("entries-counter");
  if (counter) counter.innerText = "Loading entries from database...";

  try {
    const params = new URLSearchParams({
      page: page,
      limit: pageSize
    });

    const searchVal = document.getElementById("dict-search-input") ? document.getElementById("dict-search-input").value.trim() : "";
    if (searchVal) params.append("search", searchVal);

    if (currentCategory && currentCategory !== "All") {
      params.append("category", currentCategory);
    }

    const posSelect = document.getElementById("pos-filter");
    if (posSelect && posSelect.value !== "All") {
      params.append("part_of_speech", posSelect.value);
    }

    const dialectSelect = document.getElementById("dialect-filter");
    if (dialectSelect && dialectSelect.value !== "All") {
      params.append("dialect_id", dialectSelect.value);
    }

    const res = await fetch(`${API_BASE}/lexicon/?${params.toString()}`);
    if (res.ok) {
      const data = await res.json();
      lexiconData = data;

      // Extract pagination headers
      const totalCountHeader = res.headers.get("X-Total-Count");
      const totalPagesHeader = res.headers.get("X-Total-Pages");

      totalEntriesCount = totalCountHeader ? parseInt(totalCountHeader) : data.length;
      totalPages = totalPagesHeader ? parseInt(totalPagesHeader) : Math.max(1, Math.ceil(totalEntriesCount / pageSize));

      renderLexiconGrid(lexiconData);
      renderPagination();
    } else {
      renderLexiconGrid([]);
    }
  } catch (err) {
    console.error("Lexicon fetch error:", err);
    renderLexiconGrid([]);
  }
}

function renderLexiconGrid(items) {
  const grid = document.getElementById("lexicon-grid");
  const counter = document.getElementById("entries-counter");
  if (!grid) return;

  grid.innerHTML = "";
  if (counter) {
    counter.innerText = `Showing ${items.length} of ${totalEntriesCount} entries`;
  }

  if (!items || items.length === 0) {
    grid.innerHTML = `
      <div class="col-span-full text-center py-12 bg-white rounded-2xl border border-slate-200">
        <i class="fa-solid fa-folder-open text-4xl text-slate-300 mb-3"></i>
        <h3 class="text-base font-bold text-slate-700">No matching entries found</h3>
        <p class="text-xs text-slate-500 mt-1">Try relaxing your search query or choosing another category.</p>
      </div>
    `;
    return;
  }

  items.forEach(item => {
    const card = document.createElement("div");
    card.className = "bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between";
    const audioUrl = item.audio_sample_url || "";
    const escapedTerm = (item.term || "").replace(/'/g, "\\'");
    const category = item.semantic_category || item.category || "General";
    const upvotes = item.upvotes || 0;

    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full">${category}</span>
          <span class="text-xs text-slate-400 font-medium">${item.part_of_speech || 'Noun'}</span>
        </div>
        <h3 class="text-2xl font-extrabold text-slate-900 mb-0.5 cursor-pointer hover:text-emerald-800" onclick="openWordDetailModal(${item.id})">${item.term}</h3>
        <div class="text-xs font-mono text-emerald-700 mb-3">${item.ipa_transcription || ''}</div>
        <p class="text-sm font-semibold text-slate-800 mb-1">${item.meaning_en}</p>
        <p class="text-xs text-slate-500 line-clamp-2">${item.meaning_standard_lang || ''}</p>
      </div>

      <div class="flex items-center justify-between pt-4 mt-4 border-t border-slate-100">
        <div class="flex items-center gap-2">
          <button onclick="playSampleAudio('${audioUrl}', '${escapedTerm}')" class="play-btn" title="Listen Pronunciation">
            <i class="fa-solid fa-volume-high text-sm ml-0.5"></i>
          </button>
          <!-- Upvote Button -->
          <button onclick="voteEntry(${item.id}, 1, event)" class="px-2.5 py-1 bg-slate-50 hover:bg-emerald-50 text-slate-600 hover:text-emerald-800 rounded-lg text-xs font-semibold border border-slate-200 flex items-center gap-1 transition" title="Upvote Entry">
            <i class="fa-solid fa-thumbs-up text-[11px]"></i> <span id="vote-count-${item.id}">${upvotes}</span>
          </button>
        </div>

        <button onclick="openWordDetailModal(${item.id})" class="text-xs font-bold text-slate-600 hover:text-emerald-800 flex items-center gap-1">
          Details <i class="fa-solid fa-chevron-right text-[10px]"></i>
        </button>
      </div>
    `;
    grid.appendChild(card);
  });
}

function renderPagination() {
  const container = document.getElementById("pagination-container");
  const info = document.getElementById("pagination-info");
  const numbersDiv = document.getElementById("pagination-numbers");
  const btnPrev = document.getElementById("btn-page-prev");
  const btnNext = document.getElementById("btn-page-next");

  if (!container || !numbersDiv) return;

  info.innerText = `Page ${currentPage} of ${totalPages} (${totalEntriesCount} total words)`;
  btnPrev.disabled = currentPage <= 1;
  btnNext.disabled = currentPage >= totalPages;

  numbersDiv.innerHTML = "";
  const maxButtons = 5;
  let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  if (endPage - startPage < maxButtons - 1) {
    startPage = Math.max(1, endPage - maxButtons + 1);
  }

  for (let p = startPage; p <= endPage; p++) {
    const btn = document.createElement("button");
    btn.className = `page-btn ${p === currentPage ? 'active' : ''}`;
    btn.innerText = p;
    btn.onclick = () => goToPage(p);
    numbersDiv.appendChild(btn);
  }
}

function goToPage(p) {
  if (p >= 1 && p <= totalPages) {
    fetchLexiconEntries(p);
    window.scrollTo({ top: document.getElementById("sec-explore").offsetTop - 80, behavior: 'smooth' });
  }
}

function goToPreviousPage() {
  if (currentPage > 1) goToPage(currentPage - 1);
}

function goToNextPage() {
  if (currentPage < totalPages) goToPage(currentPage + 1);
}

function changePageSize(size) {
  pageSize = parseInt(size);
  fetchLexiconEntries(1);
}


// ==============================================================================
// 8. SEARCH, PHONETIC SEARCH & FILTERING
// ==============================================================================
function handleSearchInput() {
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    if (isPhoneticActive) {
      executePhoneticSearch();
    } else {
      fetchLexiconEntries(1);
    }
  }, 350);
}

function togglePhoneticSearch() {
  const toggle = document.getElementById("phonetic-toggle");
  isPhoneticActive = toggle.checked;

  if (isPhoneticActive) {
    showToast("Phonetic Devanagari Search activated!");
    executePhoneticSearch();
  } else {
    fetchLexiconEntries(1);
  }
}

async function executePhoneticSearch() {
  const query = document.getElementById("dict-search-input").value.trim();
  if (!query) {
    fetchLexiconEntries(1);
    return;
  }

  const grid = document.getElementById("lexicon-grid");
  const counter = document.getElementById("entries-counter");
  if (counter) counter.innerText = `Phonetic search for "${query}"...`;

  try {
    const res = await fetch(`${API_BASE}/lexicon/phonetic-search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query_term: query,
        dialect_id: null,
        max_distance: 3
      })
    });

    if (res.ok) {
      const results = await res.json();
      totalEntriesCount = results.length;
      totalPages = 1;
      renderLexiconGrid(results);
      renderPagination();
      if (counter) counter.innerText = `Found ${results.length} phonetic match(es) for "${query}"`;
    } else {
      renderLexiconGrid([]);
    }
  } catch (err) {
    console.error("Phonetic search error:", err);
    fetchLexiconEntries(1);
  }
}

function selectCategory(cat) {
  currentCategory = cat;
  document.querySelectorAll("#category-pills-container .filter-tag").forEach(tag => tag.classList.remove("active"));
  const safeId = `cat-${cat.replace(/\s+/g, '-')}`;
  const btn = document.getElementById(safeId);
  if (btn) btn.classList.add("active");
  fetchLexiconEntries(1);
}

function quickFilterTag(cat) {
  showSection('explore');
  selectCategory(cat);
}

function filterLexiconEntries() {
  fetchLexiconEntries(1);
}

function handleHeroSearch(event) {
  if (event.key === "Enter") triggerHeroSearch();
}

function triggerHeroSearch() {
  const query = document.getElementById("hero-search-input").value;
  showSection('explore');
  const dictInput = document.getElementById("dict-search-input");
  if (dictInput) {
    dictInput.value = query;
    handleSearchInput();
  }
}

async function voteEntry(id, voteType, event) {
  if (event) event.stopPropagation();

  // Validate authentication before voting
  if (!authToken) {
    showToast("Please log in to vote on vocabulary entries.");
    openAuthModal();
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/lexicon/${id}/vote?vote_type=${voteType}`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${authToken}`
      }
    });

    if (res.ok) {
      const data = await res.json();
      const countEl = document.getElementById(`vote-count-${id}`);
      if (countEl) countEl.innerText = data.upvotes || 0;

      // Update in-memory entry cache
      const item = lexiconData.find(x => x.id === id);
      if (item) {
        item.upvotes = data.upvotes;
        item.downvotes = data.downvotes;
      }
      showToast(voteType > 0 ? "Upvote recorded successfully!" : "Downvote recorded successfully.");
    } else if (res.status === 401) {
      showToast("Session expired. Please log in again to vote.");
      handleLogout();
      openAuthModal();
    } else if (res.status === 403) {
      showToast("You do not have permission to vote on this entry.");
    } else {
      const err = await res.json().catch(() => ({}));
      showToast(err.detail || "Voting failed. Please try again.");
    }
  } catch (err) {
    console.error("Voting network error:", err);
    showToast("Network error submitting vote.");
  }
}


// ==============================================================================
// 9. HIGH-RELIABILITY AUDIO & TEXT-TO-SPEECH PRONUNCIATION
// ==============================================================================
function playSampleAudio(audioUrl, textToSpeak = "मायाळू") {
  // 1. Play real audio URL if provided
  if (audioUrl && audioUrl.length > 5 && !audioUrl.includes("sample_generic")) {
    if (activeAudio) {
      activeAudio.pause();
    }
    const fullAudioUrl = audioUrl.startsWith("http") ? audioUrl : `${ROOT_API}${audioUrl.startsWith('/') ? '' : '/'}${audioUrl}`;
    activeAudio = new Audio(fullAudioUrl);
    activeAudio.play().then(() => {
      showToast(`🔊 Playing Audio: "${textToSpeak}"`);
    }).catch(err => {
      // Fallback to Web Speech Synthesis if audio fails
      speakTextWithWebSpeech(textToSpeak);
    });
    return;
  }

  // 2. Web Speech Synthesis TTS (Native Marathi pronunciation)
  speakTextWithWebSpeech(textToSpeak);
}

function speakTextWithWebSpeech(textToSpeak) {
  if ('speechSynthesis' in window && textToSpeak) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = "mr-IN";
    utterance.rate = 0.85;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const marathiVoice = voices.find(v => v.lang.includes("mr") || v.lang.includes("hi") || v.name.includes("India"));
    if (marathiVoice) utterance.voice = marathiVoice;

    window.speechSynthesis.speak(utterance);
    showToast(`🔊 Pronouncing: "${textToSpeak}"`);
  }
}


// ==============================================================================
// 10. WORD DETAIL MODAL
// ==============================================================================
function openWordDetailModal(id) {
  const item = lexiconData.find(x => x.id === id) || (todaysWordEntry && todaysWordEntry.id === id ? todaysWordEntry : lexiconData[0]);
  if (!item) return;

  const modal = document.getElementById("word-detail-modal");
  const content = document.getElementById("modal-content");
  const audioUrl = item.audio_sample_url || "";
  const escapedTerm = (item.term || "").replace(/'/g, "\\'");
  const dialect = allDialects.find(d => d.id === item.dialect_id);
  const dialectName = dialect ? dialect.name : (item.dialect_name || "Regional Marathi");

  content.innerHTML = `
    <div class="flex items-center gap-4 mb-4">
      <div class="w-14 h-14 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-2xl shadow-inner">
        ${item.term ? item.term[0] : 'B'}
      </div>
      <div>
        <h2 class="text-3xl font-extrabold text-slate-900">${item.term}</h2>
        <div class="text-sm font-mono text-emerald-800 font-semibold">${item.ipa_transcription || ''}</div>
      </div>
    </div>

    <!-- Audio Player Bar -->
    <div class="bg-slate-100 rounded-xl p-4 flex items-center justify-between gap-3 mb-6 border border-slate-200">
      <div class="flex items-center gap-3">
        <button onclick="playSampleAudio('${audioUrl}', '${escapedTerm}')" class="play-btn w-12 h-12 shadow-sm">
          <i class="fa-solid fa-volume-high text-base"></i>
        </button>
        <div>
          <div class="text-sm font-bold text-slate-800">Listen Pronunciation</div>
          <div class="text-xs text-slate-500">Native ${dialectName} Recording</div>
        </div>
      </div>
      <button onclick="playSampleAudio('${audioUrl}', '${escapedTerm}')" class="px-4 py-2 bg-emerald-800 text-white rounded-lg text-xs font-semibold hover:bg-emerald-900 transition flex items-center gap-1.5">
        <i class="fa-solid fa-play"></i> Speak
      </button>
    </div>

    <div class="space-y-3.5 text-sm">
      <div class="p-3 bg-slate-50 rounded-xl">
        <span class="text-xs font-bold uppercase text-slate-400 block mb-0.5">Meaning (English)</span>
        <span class="font-semibold text-slate-800">${item.meaning_en}</span>
      </div>

      <div class="p-3 bg-slate-50 rounded-xl">
        <span class="text-xs font-bold uppercase text-slate-400 block mb-0.5">Standard Language Translation</span>
        <span class="font-semibold text-slate-800">${item.meaning_standard_lang || '—'}</span>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="p-3 bg-slate-50 rounded-xl">
          <span class="text-xs font-bold uppercase text-slate-400 block mb-0.5">Dialect</span>
          <span class="font-medium text-slate-700">${dialectName}</span>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl">
          <span class="text-xs font-bold uppercase text-slate-400 block mb-0.5">Category</span>
          <span class="font-medium text-slate-700">${item.semantic_category || item.category || 'General'}</span>
        </div>
      </div>

      <div class="p-3 bg-slate-50 rounded-xl">
        <span class="text-xs font-bold uppercase text-slate-400 block mb-0.5">Part of Speech</span>
        <span class="font-medium text-slate-700">${item.part_of_speech || 'Noun'}</span>
      </div>

      ${item.example_sentence_dialect ? `
        <div class="p-3 bg-slate-50 rounded-xl">
          <span class="text-xs font-bold uppercase text-slate-400 block mb-0.5">Context Sentence</span>
          <p class="italic text-slate-700 mb-1">"${item.example_sentence_dialect}"</p>
          ${item.example_sentence_translation ? `<p class="text-xs text-slate-500">Translation: ${item.example_sentence_translation}</p>` : ''}
        </div>
      ` : ''}
    </div>
  `;

  modal.classList.remove("hidden");
}

function closeWordDetailModal() {
  document.getElementById("word-detail-modal").classList.add("hidden");
}


// ==============================================================================
// 11. COMMUNITY VOICES / AUDIO RECORDINGS
// ==============================================================================
async function fetchAudioRecordings() {
  const defaultImages = [
    "assets/rural_folklore_elder.jpg",
    "assets/konkan_heritage.jpg",
    "assets/marathi_culture_festival.jpg",
    "assets/ancient_manuscript.jpg"
  ];

  try {
    const res = await fetch(`${API_BASE}/audio-archive/`);
    if (res.ok) {
      const data = await res.json();
      audioVoices = data.map((item, idx) => ({
        id: item.id,
        title: item.title,
        speaker: item.speaker_name || "Community Elder",
        topic: item.genre || "Culture",
        duration: item.duration_seconds ? `00:${Math.round(item.duration_seconds)}` : "02:15",
        streamUrl: item.audio_file_path.startsWith("http") ? item.audio_file_path : `${API_BASE}/audio-archive/${item.id}/stream`,
        img: defaultImages[idx % defaultImages.length]
      }));
      renderAudioRecordings(audioVoices);
    }
  } catch (err) {
    console.warn("Failed to fetch audio recordings.", err);
  }
}

function renderAudioRecordings(recordings) {
  const list = document.getElementById("audio-recordings-list");
  if (!list) return;

  list.innerHTML = "";
  if (!recordings || recordings.length === 0) {
    list.innerHTML = `
      <div class="text-center py-12 bg-white rounded-2xl border border-slate-200">
        <i class="fa-solid fa-microphone-slash text-4xl text-slate-300 mb-3"></i>
        <h3 class="text-base font-bold text-slate-700">No audio recordings found</h3>
      </div>
    `;
    return;
  }

  recordings.forEach(rec => {
    const card = document.createElement("div");
    card.className = "bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition flex flex-col md:flex-row gap-5 items-center justify-between";
    const escapedTitle = (rec.title || "").replace(/'/g, "\\'");

    card.innerHTML = `
      <div class="flex items-center gap-4 w-full md:w-auto">
        <img src="${rec.img}" class="w-20 h-20 rounded-xl object-cover shadow-sm flex-shrink-0 border border-slate-100" />
        <div>
          <span class="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full">${rec.topic}</span>
          <h3 class="font-bold text-slate-900 text-lg mt-1">${rec.title}</h3>
          <div class="text-xs text-slate-500 mt-0.5">Speaker: <span class="font-medium text-slate-700">${rec.speaker}</span> • Duration: ${rec.duration}</div>
        </div>
      </div>

      <button onclick="playSampleAudio('${rec.streamUrl}', '${escapedTitle}')" class="btn-primary px-6 py-2.5 rounded-full text-xs font-bold flex items-center gap-2 shadow-sm w-full md:w-auto justify-center">
        <i class="fa-solid fa-play"></i> Play Recording
      </button>
    `;
    list.appendChild(card);
  });
}

function filterAudioGenre(genre) {
  document.querySelectorAll("#voices-genre-container .filter-tag").forEach(t => t.classList.remove("active"));
  const btn = document.getElementById(`genre-${genre}`);
  if (btn) btn.classList.add("active");

  if (genre === "All") {
    renderAudioRecordings(audioVoices);
  } else {
    const filtered = audioVoices.filter(v => v.topic.toLowerCase() === genre.toLowerCase());
    renderAudioRecordings(filtered);
  }
}


// ==============================================================================
// 12. DYNAMIC CONTRIBUTORS
// ==============================================================================
async function fetchContributors() {
  try {
    const res = await fetch(`${ROOT_API}/contributors`);
    if (res.ok) {
      allContributors = await res.json();
      renderContributors(allContributors);
    }
  } catch (err) {
    console.warn("Failed to fetch contributors.", err);
  }
}

function renderContributors(contributors) {
  const grid = document.getElementById("contributors-grid");
  if (!grid) return;

  grid.innerHTML = "";
  contributors.forEach(c => {
    const card = document.createElement("div");
    card.className = "bg-white p-6 rounded-2xl border border-slate-200 shadow-sm text-center flex flex-col items-center justify-between";
    const photo = c.profile_image || "assets/parth_kadam.jpg";

    card.innerHTML = `
      <div class="flex flex-col items-center">
        <img src="${photo}" alt="${c.name}" class="w-28 h-28 rounded-full object-cover mb-4 shadow-md border-2 border-emerald-100" onerror="this.src='assets/parth_kadam.jpg'" />
        <h3 class="font-extrabold text-slate-900 text-lg">${c.name}</h3>
        <span class="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full mt-1">${c.role || 'Preservation Contributor'}</span>
        ${c.location ? `<p class="text-xs text-slate-500 mt-2"><i class="fa-solid fa-location-dot text-emerald-700 mr-1"></i> ${c.location}</p>` : ''}
        ${c.bio ? `<p class="text-xs text-slate-600 mt-2 line-clamp-3 leading-relaxed">${c.bio}</p>` : ''}
      </div>
    `;
    grid.appendChild(card);
  });
}


// ==============================================================================
// 13. REAL AUDIO RECORDING (MediaRecorder API) & FILE UPLOAD
// ==============================================================================
async function toggleAudioRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    stopAudioRecording();
  } else {
    startAudioRecording();
  }
}

async function startAudioRecording() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showToast("Microphone recording is not supported in this browser.");
    return;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];

    const options = { mimeType: 'audio/webm' };
    if (!MediaRecorder.isTypeSupported('audio/webm')) {
      delete options.mimeType; // Let browser choose default
    }

    mediaRecorder = new MediaRecorder(mediaStream, options);

    mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        audioChunks.push(e.data);
      }
    };

    mediaRecorder.onstop = () => {
      recordedAudioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
      const audioUrl = URL.createObjectURL(recordedAudioBlob);
      
      const preview = document.getElementById("audio-playback-preview");
      preview.src = audioUrl;
      document.getElementById("audio-preview-container").classList.remove("hidden");
      document.getElementById("audio-preview-title").innerText = `Voice Note Recorded (${recordSeconds}s)`;
      document.getElementById("btn-discard-audio").classList.remove("hidden");

      // Stop mic tracks
      if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
      }
    };

    mediaRecorder.start(250); // Record chunks every 250ms
    recordSeconds = 0;
    document.getElementById("rec-status-indicator").classList.remove("hidden");
    document.getElementById("btn-record-text").innerText = "Stop Recording";
    document.getElementById("btn-start-record").classList.replace("bg-rose-50", "bg-rose-600");
    document.getElementById("btn-start-record").classList.replace("text-rose-700", "text-white");

    recordTimerInterval = setInterval(() => {
      recordSeconds++;
      const mins = String(Math.floor(recordSeconds / 60)).padStart(2, '0');
      const secs = String(recordSeconds % 60).padStart(2, '0');
      document.getElementById("rec-timer").innerText = `${mins}:${secs}`;
    }, 1000);

    showToast("Microphone active! Recording started...");
  } catch (err) {
    console.error("Microphone error:", err);
    showToast("Microphone permission denied or microphone not found.");
  }
}

function stopAudioRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
  }
  clearInterval(recordTimerInterval);
  document.getElementById("rec-status-indicator").classList.add("hidden");
  document.getElementById("btn-record-text").innerText = "Record Voice Note";
  document.getElementById("btn-start-record").classList.replace("bg-rose-600", "bg-rose-50");
  document.getElementById("btn-start-record").classList.replace("text-white", "text-rose-700");
  showToast("Audio recording completed! Ready for submission.");
}

function handleAudioFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  // File size validation (<= 25MB)
  if (file.size > 25 * 1024 * 1024) {
    showToast("Audio file size must be less than 25MB.");
    event.target.value = "";
    return;
  }

  selectedAudioFile = file;
  const audioUrl = URL.createObjectURL(file);
  const preview = document.getElementById("audio-playback-preview");
  preview.src = audioUrl;
  document.getElementById("audio-preview-container").classList.remove("hidden");
  document.getElementById("audio-preview-title").innerText = `Selected File: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
  document.getElementById("btn-discard-audio").classList.remove("hidden");

  showToast(`Attached audio file: ${file.name}`);
}

function discardCurrentAudio() {
  recordedAudioBlob = null;
  selectedAudioFile = null;
  document.getElementById("audio-file-input").value = "";
  document.getElementById("audio-playback-preview").src = "";
  document.getElementById("audio-preview-container").classList.add("hidden");
  document.getElementById("btn-discard-audio").classList.add("hidden");
  showToast("Audio attachment discarded.");
}


// ==============================================================================
// 14. WORD CONTRIBUTION FORM SUBMISSION
// ==============================================================================
async function autoGenerateIPA() {
  const term = document.getElementById("form-term").value.trim();
  if (!term) {
    showToast("Please enter a word or phrase first.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/lexicon/ipa-generate?text=${encodeURIComponent(term)}`, {
      method: "POST"
    });
    if (res.ok) {
      const data = await res.json();
      document.getElementById("form-ipa").value = data.ipa_transcription;
      showToast("IPA Generated from backend Indic engine!");
      return;
    }
  } catch (err) {}

  // Fallback client-side mapper
  const ipaMap = { 'अ':'ə','आ':'aː','इ':'i','ई':'iː','उ':'u','ऊ':'uː','ए':'eː','ऐ':'əi','ओ':'oː','औ':'əu','क':'kə','ख':'kʰə','ग':'ɡə','घ':'ɡʱə','च':'t͡ʃə','छ':'t͡ʃʰə','ज':'d͡ʒə','झ':'d͡ʒʱə','त':'t̪ə','थ':'t̪ʰə','द':'d̪ə','ध':'d̪ʱə','न':'nə','प':'pə','फ':'pʰə','ब':'bə','भ':'bʱə','म':'mə','य':'jə','र':'rə','ल':'lə','व':'ʋə','स':'sə','ह':'ɦə' };
  let res = "/";
  for (let char of term) res += ipaMap[char] || char;
  res += "/";
  document.getElementById("form-ipa").value = res;
  showToast("IPA Generated automatically!");
}

async function handleWordSubmission(e) {
  e.preventDefault();
  const submitBtn = document.getElementById("btn-submit-word");
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1"></i> Saving Entry...`;

  const payload = {
    dialect_id: parseInt(document.getElementById("form-dialect").value) || 1,
    term: document.getElementById("form-term").value.trim(),
    meaning_en: document.getElementById("form-meaning-en").value.trim(),
    meaning_standard_lang: document.getElementById("form-meaning-std").value.trim(),
    ipa_transcription: document.getElementById("form-ipa").value.trim() || null,
    part_of_speech: document.getElementById("form-pos").value,
    example_sentence_dialect: document.getElementById("form-sentence").value.trim() || null,
    semantic_category: document.getElementById("form-category").value
  };

  try {
    const headers = { "Content-Type": "application/json" };
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    const res = await fetch(`${API_BASE}/lexicon/`, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const createdEntry = await res.json();
      
      // If audio file or recording is present, upload it linked to this entry
      if (recordedAudioBlob || selectedAudioFile) {
        const audioToUpload = selectedAudioFile || new File([recordedAudioBlob], `recording_${Date.now()}.webm`, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append("file", audioToUpload);
        formData.append("entry_id", createdEntry.id);
        formData.append("variety", payload.semantic_category);
        formData.append("transcript", payload.term);

        try {
          await fetch(`${ROOT_API}/voices`, {
            method: "POST",
            body: formData
          });
        } catch (err) {
          console.warn("Audio upload secondary error:", err);
        }
      }

      showToast(`Word "${payload.term}" submitted successfully! Entry ID: #${createdEntry.id}`);
      document.getElementById("submission-form").reset();
      discardCurrentAudio();
      
      // Refresh dictionary & admin table
      await fetchLexiconEntries(1);
      showSection('explore');
    } else {
      const err = await res.json();
      showToast(`Submission error: ${err.detail || 'Could not save entry.'}`);
    }
  } catch (err) {
    showToast("Network error submitting word to backend.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `<i class="fa-solid fa-paper-plane text-sm"></i> Submit Entry for Verification`;
  }
}


// ==============================================================================
// 15. ADMIN PORTAL (fetchAdminEntries & Verification)
// ==============================================================================
async function fetchAdminEntries() {
  const tbody = document.getElementById("admin-table-body");
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="6" class="py-8 text-center text-slate-500">
        <i class="fa-solid fa-spinner fa-spin text-xl text-emerald-800 mb-2"></i>
        <div class="text-xs">Loading administrative entries from database...</div>
      </td>
    </tr>
  `;

  try {
    const res = await fetch(`${API_BASE}/lexicon/?limit=100`);
    if (res.ok) {
      adminEntriesData = await res.json();
      
      // Calculate dynamic counts
      const totalCount = adminEntriesData.length;
      const pendingCount = adminEntriesData.filter(x => (x.verification_status || x.status || "").toLowerCase() === "pending").length;
      const contributorsCount = allContributors.length || 6;

      document.getElementById("admin-total-count").innerText = totalCount;
      document.getElementById("admin-pending-count").innerText = pendingCount;
      document.getElementById("admin-contributors-count").innerText = contributorsCount;

      renderAdminTable();
    } else {
      tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-slate-500">Could not retrieve entries.</td></tr>`;
    }
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-rose-500">Server error connecting to backend.</td></tr>`;
  }
}

function filterAdminStatus(status) {
  adminFilterStatus = status;
  ['all', 'pending', 'verified'].forEach(st => {
    const btn = document.getElementById(`admin-tab-${st}`);
    if (btn) btn.classList.remove('active');
  });

  const activeBtn = document.getElementById(`admin-tab-${status.toLowerCase()}`);
  if (activeBtn) activeBtn.classList.add('active');

  renderAdminTable();
}

function renderAdminTable() {
  const tbody = document.getElementById("admin-table-body");
  if (!tbody) return;

  let items = adminEntriesData;
  if (adminFilterStatus === "Pending") {
    items = items.filter(x => (x.verification_status || x.status || "").toLowerCase() === "pending");
  } else if (adminFilterStatus === "Verified") {
    items = items.filter(x => (x.verification_status || x.status || "").toLowerCase() !== "pending");
  }

  tbody.innerHTML = "";
  if (!items || items.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="py-8 text-center text-slate-500 text-xs">
          No records matching status "${adminFilterStatus}".
        </td>
      </tr>
    `;
    return;
  }

  items.forEach(item => {
    const status = item.verification_status || item.status || "Verified";
    const category = item.semantic_category || item.category || "General";
    const dialect = allDialects.find(d => d.id === item.dialect_id);
    const dialectName = dialect ? dialect.name : (item.dialect_name || "Regional");
    const isPending = status.toLowerCase() === "pending";

    const row = document.createElement("tr");
    row.className = "hover:bg-slate-50 transition";
    row.innerHTML = `
      <td class="py-3.5 px-4 font-bold text-slate-900">
        <div>${item.term}</div>
        <div class="text-[11px] font-mono text-emerald-800">${item.ipa_transcription || ''}</div>
      </td>
      <td class="py-3.5 px-4 text-slate-700">${item.meaning_en}</td>
      <td class="py-3.5 px-4 text-slate-600 text-xs">${dialectName}</td>
      <td class="py-3.5 px-4"><span class="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded font-medium">${category}</span></td>
      <td class="py-3.5 px-4">
        <span class="text-xs px-2.5 py-1 rounded-full font-semibold ${isPending ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}">
          ${status}
        </span>
      </td>
      <td class="py-3.5 px-4 text-right space-x-2">
        ${isPending ? `
          <button onclick="verifyAdminEntry(${item.id}, true)" class="text-xs bg-emerald-800 hover:bg-emerald-900 text-white font-bold px-3 py-1.5 rounded-lg shadow-sm transition">
            <i class="fa-solid fa-check mr-1"></i> Approve
          </button>
          <button onclick="verifyAdminEntry(${item.id}, false)" class="text-xs bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold px-3 py-1.5 rounded-lg transition border border-rose-200">
            Reject
          </button>
        ` : `
          <button onclick="openWordDetailModal(${item.id})" class="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium px-3 py-1.5 rounded-lg transition">
            View
          </button>
        `}
      </td>
    `;
    tbody.appendChild(row);
  });
}

async function verifyAdminEntry(id, approve) {
  if (!authToken) {
    showToast("Please log in as an Admin or Linguist to verify entries.");
    openAuthModal();
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/contributions/verify-lexicon/${id}?approve=${approve}`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${authToken}` }
    });

    if (res.ok) {
      const data = await res.json();
      showToast(approve ? "Submission verified & published to live archive!" : "Submission rejected.");
      await fetchAdminEntries();
      await fetchLexiconEntries(currentPage);
    } else if (res.status === 403) {
      showToast("Access Denied: Only Linguists or Admins can verify entries.");
    } else {
      showToast("Verification operation failed.");
    }
  } catch (err) {
    showToast("Server error during verification.");
  }
}


// ==============================================================================
// 16. INTERACTIVE QUIZZES
// ==============================================================================
async function fetchQuizDecks() {
  try {
    const res = await fetch(`${API_BASE}/quizzes/decks`);
    if (res.ok) {
      quizDecks = await res.json();
      renderQuizDecks(quizDecks);
    }
  } catch (err) {
    console.warn("Failed to fetch quiz decks.", err);
  }
}

function renderQuizDecks(decks) {
  const container = document.getElementById("quiz-decks-container");
  if (!container) return;

  container.innerHTML = "";
  decks.forEach(deck => {
    const card = document.createElement("div");
    card.className = "bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition flex flex-col justify-between";
    const qCount = deck.questions ? deck.questions.length : 0;
    const diffBadge = deck.difficulty === "Beginner" ? "bg-emerald-100 text-emerald-800" :
                      deck.difficulty === "Intermediate" ? "bg-blue-100 text-blue-800" : "bg-purple-100 text-purple-800";

    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full ${diffBadge}">${deck.difficulty}</span>
          <span class="text-xs text-slate-400 font-medium">${qCount} Questions</span>
        </div>
        <h3 class="font-extrabold text-slate-900 text-lg mb-2">${deck.title}</h3>
        <p class="text-xs text-slate-600 line-clamp-3 mb-6">${deck.description || 'Test your knowledge on regional vocabulary and idioms.'}</p>
      </div>

      <button onclick="startQuiz(${deck.id})" class="btn-primary w-full py-2.5 rounded-xl font-bold text-xs flex items-center justify-center gap-2 shadow-sm">
        <i class="fa-solid fa-play"></i> Start Quiz Deck
      </button>
    `;
    container.appendChild(card);
  });
}

function startQuiz(deckId) {
  activeQuizDeck = quizDecks.find(d => d.id === deckId);
  if (!activeQuizDeck || !activeQuizDeck.questions || activeQuizDeck.questions.length === 0) {
    showToast("Quiz deck questions not found.");
    return;
  }

  activeQuestions = activeQuizDeck.questions;
  currentQuestionIndex = 0;
  userQuizAnswers = [];
  selectedOptionLetter = null;

  document.getElementById("quiz-decks-container").classList.add("hidden");
  document.getElementById("active-quiz-container").classList.remove("hidden");
  document.getElementById("quiz-active-title").innerText = activeQuizDeck.title;
  document.getElementById("quiz-deck-badge").innerText = activeQuizDeck.difficulty;

  renderActiveQuestion();
}

function renderActiveQuestion() {
  const q = activeQuestions[currentQuestionIndex];
  if (!q) return;

  selectedOptionLetter = null;
  document.getElementById("quiz-selected-label").innerText = "None";
  document.getElementById("quiz-progress-text").innerText = `Question ${currentQuestionIndex + 1} of ${activeQuestions.length}`;
  document.getElementById("quiz-question-text").innerText = q.question_text;

  const optionsContainer = document.getElementById("quiz-options-container");
  optionsContainer.innerHTML = "";

  const options = [
    { key: "A", text: q.option_a },
    { key: "B", text: q.option_b },
    { key: "C", text: q.option_c },
    { key: "D", text: q.option_d }
  ];

  options.forEach(opt => {
    const btn = document.createElement("div");
    btn.className = "quiz-option p-4 rounded-xl border border-slate-200 bg-white flex items-center gap-3";
    btn.id = `opt-btn-${opt.key}`;
    btn.onclick = () => selectQuizOption(opt.key);

    btn.innerHTML = `
      <span class="w-8 h-8 rounded-lg bg-slate-100 text-slate-800 font-bold flex items-center justify-center text-xs flex-shrink-0">${opt.key}</span>
      <span class="text-sm font-medium text-slate-800">${opt.text}</span>
    `;
    optionsContainer.appendChild(btn);
  });

  const nextBtn = document.getElementById("btn-quiz-next");
  if (currentQuestionIndex === activeQuestions.length - 1) {
    nextBtn.innerHTML = `<span>Submit Quiz</span> <i class="fa-solid fa-check"></i>`;
  } else {
    nextBtn.innerHTML = `<span>Next Question</span> <i class="fa-solid fa-arrow-right"></i>`;
  }
}

function selectQuizOption(letter) {
  selectedOptionLetter = letter;
  document.getElementById("quiz-selected-label").innerText = `Option ${letter}`;

  document.querySelectorAll(".quiz-option").forEach(el => el.classList.remove("selected"));
  const chosen = document.getElementById(`opt-btn-${letter}`);
  if (chosen) chosen.classList.add("selected");
}

async function handleQuizNext() {
  if (!selectedOptionLetter) {
    showToast("Please choose an answer before proceeding.");
    return;
  }

  const currentQ = activeQuestions[currentQuestionIndex];
  userQuizAnswers.push({
    question_id: currentQ.id,
    selected_option: selectedOptionLetter
  });

  if (currentQuestionIndex < activeQuestions.length - 1) {
    currentQuestionIndex++;
    renderActiveQuestion();
  } else {
    // Submit Quiz to Backend
    await submitActiveQuiz();
  }
}

async function submitActiveQuiz() {
  const nextBtn = document.getElementById("btn-quiz-next");
  nextBtn.disabled = true;
  nextBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1"></i> Submitting...`;

  try {
    const headers = { "Content-Type": "application/json" };
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    const res = await fetch(`${API_BASE}/quizzes/submit`, {
      method: "POST",
      headers: headers,
      body: JSON.stringify({
        deck_id: activeQuizDeck.id,
        answers: userQuizAnswers
      })
    });

    if (res.ok) {
      const result = await res.json();
      document.getElementById("quiz-modal-score").innerText = `${result.score_percentage}%`;
      document.getElementById("quiz-modal-rep").innerText = `+${result.reputation_earned || 0} pts`;
      document.getElementById("quiz-modal-feedback").innerText = result.feedback || `You scored ${result.correct_count} out of ${result.total_questions}!`;
      document.getElementById("quiz-result-modal").classList.remove("hidden");
    } else {
      showToast("Error recording quiz results.");
    }
  } catch (err) {
    showToast("Network error submitting quiz.");
  } finally {
    exitActiveQuiz();
  }
}

function exitActiveQuiz() {
  document.getElementById("active-quiz-container").classList.add("hidden");
  document.getElementById("quiz-decks-container").classList.remove("hidden");
  activeQuizDeck = null;
  activeQuestions = [];
  userQuizAnswers = [];
}

function closeQuizResultModal() {
  document.getElementById("quiz-result-modal").classList.add("hidden");
}


// ==============================================================================
// 17. LEAFLET INTERACTIVE DIALECT CARTOGRAPHY MAP
// ==============================================================================
function initDialectMap() {
  const mapContainer = document.getElementById("dialect-map");
  if (!mapContainer || typeof L === "undefined") return;

  // Initialize Map Centered on Maharashtra
  leafletMap = L.map('dialect-map').setView([19.25, 75.80], 7);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap contributors | BhashaLok Preserver'
  }).addTo(leafletMap);

  if (allDialects && allDialects.length > 0) {
    updateMapMarkers(allDialects);
  }
}

function updateMapMarkers(dialects) {
  if (!leafletMap || typeof L === "undefined") return;

  // Clear existing markers
  mapMarkers.forEach(m => leafletMap.removeLayer(m));
  mapMarkers = [];

  dialects.forEach(d => {
    if (d.latitude && d.longitude) {
      const color = d.endangerment_status === "Safe" ? "#16a34a" :
                    d.endangerment_status === "Vulnerable" ? "#f59e0b" : "#e11d48";

      const circle = L.circleMarker([d.latitude, d.longitude], {
        radius: 9,
        fillColor: color,
        color: "#ffffff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.85
      }).addTo(leafletMap);

      const popupHtml = `
        <div class="text-left font-sans p-1">
          <div class="font-bold text-sm text-slate-900">${d.name}</div>
          <div class="text-xs text-slate-500">${d.region_name || 'Maharashtra'}</div>
          <div class="mt-1"><span class="text-[10px] font-semibold px-2 py-0.5 rounded-full" style="background-color: ${color}20; color: ${color}">${d.endangerment_status}</span></div>
          <div class="text-[11px] text-slate-600 mt-2">Speakers: ${d.estimated_speakers ? d.estimated_speakers.toLocaleString() : 'N/A'}</div>
        </div>
      `;

      circle.bindPopup(popupHtml);
      circle.on('click', () => {
        showDialectDetailsOnMap(d);
      });

      mapMarkers.push(circle);
    }
  });

  // Select first dialect by default
  if (dialects.length > 0) {
    showDialectDetailsOnMap(dialects[0]);
  }
}

function showDialectDetailsOnMap(dialect) {
  activeMapDialect = dialect;
  document.getElementById("map-detail-title").innerText = dialect.name;
  document.getElementById("map-detail-region").innerText = dialect.region_name || dialect.region || "Maharashtra";
  document.getElementById("map-detail-districts").innerText = dialect.districts || "Coastal & Central Maharashtra";
  document.getElementById("map-detail-speakers").innerText = dialect.estimated_speakers ? `~${dialect.estimated_speakers.toLocaleString()} speakers` : "Under Field Assessment";
  document.getElementById("map-detail-desc").innerText = dialect.description || dialect.cultural_notes || "Spoken by native community elders and heritage culture bearers.";

  const badge = document.getElementById("map-detail-badge");
  badge.innerText = dialect.endangerment_status || "Vulnerable";
  badge.className = `px-2.5 py-0.5 rounded-full text-xs font-semibold ${
    dialect.endangerment_status === "Safe" ? "bg-emerald-100 text-emerald-800" :
    dialect.endangerment_status === "Vulnerable" ? "bg-amber-100 text-amber-800" : "bg-rose-100 text-rose-800"
  }`;
}

function filterBySelectedMapDialect() {
  if (!activeMapDialect) return;
  showSection('explore');
  const dialectSelect = document.getElementById("dialect-filter");
  if (dialectSelect) {
    dialectSelect.value = activeMapDialect.id;
    filterLexiconEntries();
  }
}


// ==============================================================================
// 18. DATA EXPORT (CSV & JSON)
// ==============================================================================
function exportArchiveCSV() {
  showToast("Preparing CSV export...");
  window.open(`${API_BASE}/analytics/export/csv`, '_blank');
}

function exportArchiveJSON() {
  showToast("Preparing JSON digital archive...");
  window.open(`${API_BASE}/analytics/export/json`, '_blank');
}


// ==============================================================================
// 19. REAL-TIME WEBSOCKET LIVE ACTIVITY FEED
// ==============================================================================
function initWebSocketActivityStream() {
  const wsProtocol = API_BASE.startsWith("https") ? "wss:" : "ws:";
  const wsHost = API_BASE.replace(/^https?:\/\//, '').replace(/\/api\/v1$/, '');
  const wsUrl = `${wsProtocol}//${wsHost}/api/v1/ws/activity`;

  try {
    activitySocket = new WebSocket(wsUrl);

    activitySocket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.event === "NEW_LEXICON_ENTRY") {
          showToast(`⚡ Live Activity: New entry "${msg.term}" contributed!`);
        } else if (msg.event === "AUDIO_RECORDING_UPLOADED") {
          showToast(`🎙️ Live Activity: New audio "${msg.title}" archived!`);
        }
      } catch (e) {}
    };

    activitySocket.onerror = () => {
      console.warn("WebSocket live feed optional fallback.");
    };
  } catch (err) {}
}


// ==============================================================================
// 20. TOAST NOTIFICATIONS
// ==============================================================================
function showToast(msg) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400"></i> <span class="text-xs font-semibold">${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}
