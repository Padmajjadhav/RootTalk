/* BhashaLok - Frontend Connected JavaScript Engine */

const API_BASE = "http://127.0.0.1:8000/api/v1";

// Global Application State
let currentSection = "home";
let currentCategory = "All";
let lexiconData = [];
let audioVoices = [];
let activeAudio = null;
let authToken = localStorage.getItem("bhashalok_token") || null;

// Default Fallback Data if Backend starting up
const fallbackLexicon = [
  {
    id: 1,
    term: "मायाळू",
    script: "Devanagari",
    ipa_transcription: "/ma:ja:lu/",
    meaning_en: "Kind / Affectionate / Loving Nature",
    meaning_standard_lang: "प्रेमळ / आपुलकी असणारा",
    part_of_speech: "Adjective",
    example_sentence_dialect: "तो मायाळू माणूस सगळ्यांची काळजी घेतो.",
    example_sentence_translation: "That affectionate person takes care of everyone.",
    semantic_category: "Culture",
    dialect_name: "Malvani",
    speaker_name: "Sushila Tai",
    verification_status: "Verified",
    upvotes: 24,
    audio_sample_url: "https://sdml.ac.in/story/Katta/1/fullstory.wav"
  },
  {
    id: 2,
    term: "आंबा",
    script: "Devanagari",
    ipa_transcription: "/a:mba/",
    meaning_en: "Mango Fruit",
    meaning_standard_lang: "आंबा",
    part_of_speech: "Noun",
    example_sentence_dialect: "देवगडचा हापूस आंबा लय गोड आसा.",
    example_sentence_translation: "Devgad Alphonso mango is very sweet.",
    semantic_category: "Food",
    dialect_name: "Malvani",
    speaker_name: "Ganpat Kaka",
    verification_status: "Verified",
    upvotes: 19,
    audio_sample_url: "https://sdml.ac.in/story/Dandi/2/fullstory.wav"
  },
  {
    id: 3,
    term: "कोकण",
    script: "Devanagari",
    ipa_transcription: "/ko:kon/",
    meaning_en: "Coastal Konkan Region",
    meaning_standard_lang: "कोकण किनारपट्टी",
    part_of_speech: "Noun",
    example_sentence_dialect: "येवा कोंकण आपलोच आसा!",
    example_sentence_translation: "Welcome to Konkan, it belongs to all of us!",
    semantic_category: "Nature",
    dialect_name: "Malvani",
    speaker_name: "Ramesh Patil",
    verification_status: "Verified",
    upvotes: 40,
    audio_sample_url: "https://sdml.ac.in/story/Mandwa/1/fullstory.wav"
  }
];

// Initialize Application & Connect to Live FastAPI Backend
document.addEventListener("DOMContentLoaded", async () => {
  // Pre-load Web Speech voices
  if ('speechSynthesis' in window) {
    window.speechSynthesis.getVoices();
  }

  await fetchBackendStats();
  await fetchLexiconEntries();
  await fetchAudioRecordings();
  renderContributors();
});

// --- BACKEND API DATA FETCHERS ---

// 1. Fetch Preservation Stats
async function fetchBackendStats() {
  try {
    const res = await fetch(`${API_BASE}/analytics/stats`);
    if (res.ok) {
      const data = await res.json();
      document.getElementById("stat-words").innerText = (data.total_words_preserved || 1240).toLocaleString();
      document.getElementById("stat-audio").innerText = (data.total_audio_recordings || 380).toLocaleString();
      document.getElementById("stat-contributors").innerText = "3";
      document.getElementById("stat-dialects").innerText = (data.total_dialects || 35).toLocaleString();
    }
  } catch (err) {
    console.warn("Backend server connecting... Using local cached metrics.");
  }
}

// 2. Fetch Lexicon Dictionary Entries
async function fetchLexiconEntries() {
  try {
    const res = await fetch(`${API_BASE}/lexicon/`);
    if (res.ok) {
      const data = await res.json();
      lexiconData = data.length > 0 ? data : fallbackLexicon;
    } else {
      lexiconData = fallbackLexicon;
    }
  } catch (err) {
    lexiconData = fallbackLexicon;
  }
  renderLexiconGrid(lexiconData);
  renderAdminTable();
}

// 3. Fetch Audio Archives
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
        speaker: item.speaker_name || "Native Speaker",
        topic: item.genre || "Culture",
        duration: item.duration_seconds ? `00:${Math.round(item.duration_seconds)}` : "01:45",
        streamUrl: item.audio_file_path.startsWith("http") ? item.audio_file_path : `${API_BASE}/audio-archive/${item.id}/stream`,
        img: defaultImages[idx % defaultImages.length]
      }));
    }
  } catch (err) {
    audioVoices = [
      {
        id: 101,
        title: "Traditional Farming Practices",
        speaker: "Ganpat Kaka",
        topic: "Agriculture",
        duration: "02:14",
        streamUrl: "https://sdml.ac.in/story/Brahmanwada/1/fullstory.wav",
        img: "assets/rural_folklore_elder.jpg"
      },
      {
        id: 102,
        title: "Festival Memories & Dashavatara Lore",
        speaker: "Sushila Tai",
        topic: "Culture",
        duration: "03:21",
        streamUrl: "https://sdml.ac.in/story/Katta/1/fullstory.wav",
        img: "assets/marathi_culture_festival.jpg"
      },
      {
        id: 103,
        title: "Life in the Konkan Fishing Village",
        speaker: "Ramesh Patil",
        topic: "Daily Life",
        duration: "01:48",
        streamUrl: "https://sdml.ac.in/story/Dandi/2/fullstory.wav",
        img: "assets/konkan_heritage.jpg"
      }
    ];
  }
  renderAudioRecordings(audioVoices);
}

// --- NAVIGATION SWITCHER ---
function showSection(secName) {
  const sections = ['home', 'explore', 'voices', 'contributors', 'contribute', 'about', 'admin'];
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
}

function toggleMobileMenu() {
  const menu = document.getElementById('mobile-menu');
  menu.classList.toggle('hidden');
}

function focusGlobalSearch() {
  showSection('explore');
  setTimeout(() => {
    document.getElementById('dict-search-input').focus();
  }, 200);
}

// --- DYNAMIC DICTIONARY RENDER ---
function renderLexiconGrid(items) {
  const grid = document.getElementById("lexicon-grid");
  const counter = document.getElementById("entries-counter");
  if (!grid) return;

  grid.innerHTML = "";
  if (counter) counter.innerText = `Showing ${items.length} entries`;

  if (items.length === 0) {
    grid.innerHTML = `
      <div class="col-span-full text-center py-12 bg-white rounded-2xl border border-slate-200">
        <i class="fa-solid fa-folder-open text-4xl text-slate-300 mb-3"></i>
        <h3 class="text-base font-bold text-slate-700">No matching entries found</h3>
        <p class="text-xs text-slate-500 mt-1">Try changing your search terms or category filter.</p>
      </div>
    `;
    return;
  }

  items.forEach(item => {
    const card = document.createElement("div");
    card.className = "bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between";
    const audioUrl = item.audio_sample_url || "";
    const escapedTerm = item.term.replace(/'/g, "\\'");

    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full">${item.semantic_category || item.category || 'General'}</span>
          <span class="text-xs text-slate-400 font-medium">${item.part_of_speech || 'Noun'}</span>
        </div>
        <h3 class="text-2xl font-extrabold text-slate-900 mb-0.5 cursor-pointer hover:text-emerald-800" onclick="openWordDetailModal(${item.id})">${item.term}</h3>
        <div class="text-xs font-mono text-emerald-700 mb-3">${item.ipa_transcription || ''}</div>
        <p class="text-sm font-semibold text-slate-800 mb-1">${item.meaning_en}</p>
        <p class="text-xs text-slate-500 line-clamp-2">${item.meaning_standard_lang || ''}</p>
      </div>

      <div class="flex items-center justify-between pt-4 mt-4 border-t border-slate-100">
        <button onclick="playSampleAudio('${audioUrl}', '${escapedTerm}')" class="play-btn">
          <i class="fa-solid fa-volume-high text-sm ml-0.5"></i>
        </button>
        <button onclick="openWordDetailModal(${item.id})" class="text-xs font-bold text-slate-600 hover:text-emerald-800 flex items-center gap-1">
          Details <i class="fa-solid fa-chevron-right text-[10px]"></i>
        </button>
      </div>
    `;
    grid.appendChild(card);
  });
}

// --- SEARCH & FILTERING ---
async function filterLexiconEntries() {
  const query = document.getElementById("dict-search-input").value.toLowerCase().trim();
  const posFilter = document.getElementById("pos-filter").value;

  const filtered = lexiconData.filter(item => {
    const categoryName = item.semantic_category || item.category || "";
    const matchQuery = !query || 
      item.term.toLowerCase().includes(query) ||
      item.meaning_en.toLowerCase().includes(query) ||
      (item.ipa_transcription && item.ipa_transcription.toLowerCase().includes(query)) ||
      (item.meaning_standard_lang && item.meaning_standard_lang.toLowerCase().includes(query));

    const matchCategory = currentCategory === "All" || categoryName.toLowerCase() === currentCategory.toLowerCase();
    const matchPOS = posFilter === "All" || item.part_of_speech === posFilter;

    return matchQuery && matchCategory && matchPOS;
  });

  renderLexiconGrid(filtered);
}

function selectCategory(cat) {
  currentCategory = cat;
  document.querySelectorAll(".filter-tag").forEach(tag => tag.classList.remove("active"));
  const btn = document.getElementById(`cat-${cat.replace(/\s+/g, '-')}`);
  if (btn) btn.classList.add("active");
  filterLexiconEntries();
}

function quickFilterTag(cat) {
  showSection('explore');
  selectCategory(cat);
}

function handleHeroSearch(event) {
  if (event.key === "Enter") {
    triggerHeroSearch();
  }
}

function triggerHeroSearch() {
  const query = document.getElementById("hero-search-input").value;
  showSection('explore');
  const dictInput = document.getElementById("dict-search-input");
  if (dictInput) {
    dictInput.value = query;
    filterLexiconEntries();
  }
}

// --- HIGH-RELIABILITY AUDIO & TEXT-TO-SPEECH PRONUNCIATION ---
function playSampleAudio(audioUrl, textToSpeak = "मायाळू") {
  // 1. Web Speech Synthesis Text-To-Speech (Native Marathi / Indic Pronunciation)
  if ('speechSynthesis' in window && textToSpeak) {
    window.speechSynthesis.cancel(); // Stop any previous speech
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = "mr-IN"; // Marathi Language Code
    utterance.rate = 0.85;    // Clear pronunciation pace
    utterance.pitch = 1.0;

    // Pick best available Indic voice
    const voices = window.speechSynthesis.getVoices();
    const marathiVoice = voices.find(v => v.lang.includes("mr") || v.lang.includes("hi") || v.name.includes("India"));
    if (marathiVoice) {
      utterance.voice = marathiVoice;
    }

    window.speechSynthesis.speak(utterance);
    showToast(`🔊 Pronouncing: "${textToSpeak}"`);
    return;
  }

  // 2. Audio File Fallback if SpeechSynthesis not present
  if (audioUrl) {
    if (activeAudio) {
      activeAudio.pause();
    }
    activeAudio = new Audio(audioUrl);
    activeAudio.play().catch(e => {
      showToast(`🔊 Word: "${textToSpeak}"`);
    });
  }
}

// --- WORD DETAIL MODAL ---
function openWordDetailModal(id) {
  const item = lexiconData.find(x => x.id === id) || lexiconData[0];
  const modal = document.getElementById("word-detail-modal");
  const content = document.getElementById("modal-content");
  const audioUrl = item.audio_sample_url || "";
  const escapedTerm = item.term.replace(/'/g, "\\'");

  content.innerHTML = `
    <div class="flex items-center gap-4 mb-4">
      <div class="w-14 h-14 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-2xl shadow-inner">
        ${item.term ? item.term[0] : 'B'}
      </div>
      <div>
        <h2 class="text-3xl font-extrabold text-slate-900">${item.term}</h2>
        <div class="text-base font-mono text-emerald-800 font-semibold">${item.ipa_transcription || '/ma:ja:lu/'}</div>
      </div>
    </div>

    <!-- Audio Control -->
    <div class="bg-slate-100 rounded-xl p-4 flex items-center justify-between gap-3 mb-6 border border-slate-200">
      <div class="flex items-center gap-3">
        <button onclick="playSampleAudio('${audioUrl}', '${escapedTerm}')" class="play-btn w-12 h-12 shadow-sm">
          <i class="fa-solid fa-volume-high text-base"></i>
        </button>
        <div>
          <div class="text-sm font-bold text-slate-800">Listen Pronunciation</div>
          <div class="text-xs text-slate-500">Native Marathi Dialect Voice</div>
        </div>
      </div>
      <button onclick="playSampleAudio('${audioUrl}', '${escapedTerm}')" class="px-4 py-2 bg-emerald-800 text-white rounded-lg text-xs font-semibold hover:bg-emerald-900 transition">
        <i class="fa-solid fa-play mr-1"></i> Speak Out Loud
      </button>
    </div>

    <div class="space-y-4 text-sm">
      <div class="p-3 bg-slate-50 rounded-xl">
        <span class="text-xs font-bold uppercase text-slate-400 block mb-0.5">Meaning (English)</span>
        <span class="font-semibold text-slate-800">${item.meaning_en}</span>
      </div>

      <div class="p-3 bg-slate-50 rounded-xl">
        <span class="text-xs font-bold uppercase text-slate-400 block mb-0.5">Standard Language Translation</span>
        <span class="font-semibold text-slate-800">${item.meaning_standard_lang || ''}</span>
      </div>

      <div class="p-3 bg-slate-50 rounded-xl">
        <span class="text-xs font-bold uppercase text-slate-400 block mb-0.5">Part of Speech</span>
        <span class="font-medium text-slate-700">${item.part_of_speech || 'Adjective'}</span>
      </div>

      <div class="p-3 bg-slate-50 rounded-xl">
        <span class="text-xs font-bold uppercase text-slate-400 block mb-0.5">Context Sentence</span>
        <p class="italic text-slate-700 mb-1">"${item.example_sentence_dialect || 'तो मायाळू माणूस सगळ्यांची काळजी घेतो.'}"</p>
        <p class="text-xs text-slate-500">Translation: ${item.example_sentence_translation || 'Where are you heading today?'}</p>
      </div>
    </div>
  `;

  modal.classList.remove("hidden");
}

function closeWordDetailModal() {
  document.getElementById("word-detail-modal").classList.add("hidden");
}

// --- COMMUNITY VOICES RENDER ---
function renderAudioRecordings(recordings) {
  const list = document.getElementById("audio-recordings-list");
  if (!list) return;

  list.innerHTML = "";
  recordings.forEach(rec => {
    const card = document.createElement("div");
    card.className = "bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition flex flex-col md:flex-row gap-5 items-center justify-between";
    const escapedTitle = rec.title.replace(/'/g, "\\'");

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
  document.querySelectorAll("#sec-voices .filter-tag").forEach(t => t.classList.remove("active"));
  const btn = document.getElementById(`genre-${genre}`);
  if (btn) btn.classList.add("active");

  if (genre === "All") {
    renderAudioRecordings(audioVoices);
  } else {
    const filtered = audioVoices.filter(v => v.topic.toLowerCase() === genre.toLowerCase());
    renderAudioRecordings(filtered);
  }
}

// --- CONTRIBUTORS RENDER (TEAM MEMBERS WITH PHOTOS) ---
function renderContributors() {
  const grid = document.getElementById("contributors-grid");
  if (!grid) return;

  const teamContributors = [
    { name: "Parth Kadam", img: "assets/parth_kadam.jpg" },
    { name: "Aaditya Jadhav", img: "assets/aaditya_jadhav.jpg" },
    { name: "Padmaj Jadhav", img: "assets/padmaj_jadhav.jpg" }
  ];

  grid.innerHTML = "";
  teamContributors.forEach(c => {
    const card = document.createElement("div");
    card.className = "bg-white p-6 rounded-2xl border border-slate-200 shadow-sm text-center flex flex-col items-center justify-center";
    card.innerHTML = `
      <img src="${c.img}" alt="${c.name}" class="w-32 h-32 rounded-full object-cover mb-4 shadow-md border-2 border-emerald-100" />
      <h3 class="font-extrabold text-slate-900 text-lg">${c.name}</h3>
    `;
    grid.appendChild(card);
  });
}

// --- FORM SUBMISSION & AUTO IPA GENERATOR ---
async function autoGenerateIPA() {
  const term = document.getElementById("form-term").value;
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
      showToast("IPA Generated from backend!");
      return;
    }
  } catch (err) {
    // Fallback client-side Devanagari IPA mapper
  }

  const ipaMap = { 'अ':'ə','आ':'aː','इ':'i','ई':'iː','उ':'u','ऊ':'uː','ए':'eː','ऐ':'əi','ओ':'oː','औ':'əu','क':'kə','ख':'kʰə','ग':'ɡə','घ':'ɡʱə','च':'t͡ʃə','छ':'t͡ʃʰə','ज':'d͡ʒə','झ':'d͡ʒʱə','त':'t̪ə','थ':'t̪ʰə','द':'d̪ə','ध':'d̪ʱə','न':'nə','प':'pə','फ':'pʰə','ब':'bə','भ':'bʱə','म':'mə','य':'jə','र':'rə','ल':'lə','व':'ʋə','स':'sə','ह':'ɦə' };
  let res = "/";
  for (let char of term) {
    res += ipaMap[char] || char;
  }
  res += "/";
  document.getElementById("form-ipa").value = res;
  showToast("IPA Generated automatically!");
}

async function handleWordSubmission(e) {
  e.preventDefault();
  
  const payload = {
    dialect_id: parseInt(document.getElementById("form-dialect").value),
    term: document.getElementById("form-term").value,
    meaning_en: document.getElementById("form-meaning-en").value,
    meaning_standard_lang: document.getElementById("form-meaning-std").value,
    ipa_transcription: document.getElementById("form-ipa").value || null,
    part_of_speech: document.getElementById("form-pos").value,
    example_sentence_dialect: document.getElementById("form-sentence").value,
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
      const created = await res.json();
      lexiconData.unshift(created);
      showToast("Entry submitted and saved to FastAPI backend database!");
    } else {
      lexiconData.unshift({
        id: lexiconData.length + 1,
        ...payload,
        verification_status: "Pending"
      });
      showToast("Submission recorded!");
    }
  } catch (err) {
    lexiconData.unshift({
      id: lexiconData.length + 1,
      ...payload,
      verification_status: "Pending"
    });
    showToast("Submission recorded!");
  }

  renderLexiconGrid(lexiconData);
  renderAdminTable();
  document.getElementById("submission-form").reset();
  showSection('explore');
}

function simulateMicRecord() {
  showToast("Microphone recording started... Click again to stop.");
}

// --- ADMIN TABLE RENDER ---
function renderAdminTable() {
  const tbody = document.getElementById("admin-table-body");
  if (!tbody) return;

  tbody.innerHTML = "";
  lexiconData.forEach(item => {
    const status = item.verification_status || item.status || "Verified";
    const category = item.semantic_category || item.category || "General";
    
    const row = document.createElement("tr");
    row.className = "hover:bg-slate-50 transition";
    row.innerHTML = `
      <td class="py-3.5 px-4 font-bold text-slate-900">${item.term}</td>
      <td class="py-3.5 px-4 text-slate-700">${item.meaning_en}</td>
      <td class="py-3.5 px-4"><span class="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded font-medium">${category}</span></td>
      <td class="py-3.5 px-4">
        <span class="text-xs px-2.5 py-1 rounded-full font-semibold ${status === 'Verified' || status === 'Published' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
          ${status}
        </span>
      </td>
      <td class="py-3.5 px-4 text-right space-x-2">
        ${status === 'Pending' ? 
          `<button onclick="verifyEntry(${item.id})" class="text-xs bg-emerald-800 hover:bg-emerald-900 text-white font-bold px-3 py-1 rounded">Approve</button>` :
          `<button onclick="openWordDetailModal(${item.id})" class="text-xs bg-slate-200 hover:bg-slate-300 text-slate-700 font-medium px-2.5 py-1 rounded">View</button>`
        }
      </td>
    `;
    tbody.appendChild(row);
  });
}

async function verifyEntry(id) {
  try {
    const res = await fetch(`${API_BASE}/contributions/verify-lexicon/${id}?approve=true`, {
      method: "POST"
    });
    if (res.ok) {
      showToast("Submission verified & published via backend API!");
    }
  } catch (err) {
    showToast("Entry marked as verified!");
  }

  const item = lexiconData.find(x => x.id === id);
  if (item) {
    item.verification_status = "Verified";
    item.status = "Published";
  }
  renderAdminTable();
  renderLexiconGrid(lexiconData);
}

// --- TOAST NOTIFICATIONS ---
function showToast(msg) {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400"></i> <span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}
