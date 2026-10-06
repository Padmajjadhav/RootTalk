/* BhashaLok - Frontend Core JavaScript Engine */

const API_BASE = "http://127.0.0.1:8000/api/v1";

// State Management
let currentSection = "home";
let currentCategory = "All";
let lexiconData = [
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
    category: "Culture",
    dialect: "Malvani",
    speaker_name: "Sushila Tai",
    speaker_role: "Native Speaker, Malvan",
    status: "Published",
    upvotes: 24,
    audio: "https://actions.google.com/sounds/v1/human/speech_male_cheerful.ogg"
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
    category: "Food",
    dialect: "Malvani",
    speaker_name: "Ganpat Kaka",
    speaker_role: "Native Speaker",
    status: "Published",
    upvotes: 19,
    audio: "https://actions.google.com/sounds/v1/human/speech_female_giggle.ogg"
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
    category: "Nature",
    dialect: "Malvani",
    speaker_name: "Ramesh Patil",
    speaker_role: "Community Member",
    status: "Published",
    upvotes: 40,
    audio: "https://actions.google.com/sounds/v1/human/speech_male_cheerful.ogg"
  },
  {
    id: 4,
    term: "उन्हाळा",
    script: "Devanagari",
    ipa_transcription: "/unha:la/",
    meaning_en: "Summer Season",
    meaning_standard_lang: "उन्हाळा",
    part_of_speech: "Noun",
    example_sentence_dialect: "उन्हाळ्यात समुद्र शांत असतो.",
    example_sentence_translation: "The ocean stays calm in summer.",
    category: "Nature",
    dialect: "Varhadi",
    speaker_name: "Lata Bai",
    speaker_role: "Native Speaker",
    status: "Published",
    upvotes: 12,
    audio: "https://actions.google.com/sounds/v1/human/speech_female_giggle.ogg"
  },
  {
    id: 5,
    term: "जत्रा",
    script: "Devanagari",
    ipa_transcription: "/dga:tra/",
    meaning_en: "Village Fair / Festival",
    meaning_standard_lang: "ग्रामोत्सव / जत्रा",
    part_of_speech: "Noun",
    example_sentence_dialect: "आज गावात जत्रा आसा.",
    example_sentence_translation: "There is a village fair in our town today.",
    category: "Festival",
    dialect: "Ahirani",
    speaker_name: "Ganpat Kaka",
    speaker_role: "Native Speaker",
    status: "Pending",
    upvotes: 8,
    audio: "https://actions.google.com/sounds/v1/human/speech_male_cheerful.ogg"
  },
  {
    id: 6,
    term: "भात",
    script: "Devanagari",
    ipa_transcription: "/bha:t/",
    meaning_en: "Cooked Rice",
    meaning_standard_lang: "भात",
    part_of_speech: "Noun",
    example_sentence_dialect: "गरम भात नि मासोळीची कडी मस्त लागते.",
    example_sentence_translation: "Hot rice with fish curry tastes amazing.",
    category: "Agriculture",
    dialect: "Malvani",
    speaker_name: "Sushila Tai",
    speaker_role: "Native Speaker",
    status: "Published",
    upvotes: 15,
    audio: "https://actions.google.com/sounds/v1/human/speech_female_giggle.ogg"
  }
];

let audioVoices = [
  {
    id: 101,
    title: "Traditional Farming Practices",
    speaker: "Ganpat Kaka",
    topic: "Agriculture",
    duration: "02:14",
    dialect: "Malvani",
    audio: "https://actions.google.com/sounds/v1/human/speech_male_cheerful.ogg",
    img: "https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=400&auto=format&fit=crop"
  },
  {
    id: 102,
    title: "Festival Memories & Dashavatara Lore",
    speaker: "Sushila Tai",
    topic: "Culture",
    duration: "03:21",
    dialect: "Malvani",
    audio: "https://actions.google.com/sounds/v1/human/speech_female_giggle.ogg",
    img: "https://images.unsplash.com/photo-1544717305-2782549b5136?q=80&w=400&auto=format&fit=crop"
  },
  {
    id: 103,
    title: "Life in the Konkan Fishing Village",
    speaker: "Ramesh Patil",
    topic: "Daily Life",
    duration: "01:48",
    dialect: "Konkani",
    audio: "https://actions.google.com/sounds/v1/human/speech_male_cheerful.ogg",
    img: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=400&auto=format&fit=crop"
  },
  {
    id: 104,
    title: "Traditional Folk Song (Bharud)",
    speaker: "Bhima Kaka",
    topic: "Culture",
    duration: "04:12",
    dialect: "Varhadi",
    audio: "https://actions.google.com/sounds/v1/human/speech_male_cheerful.ogg",
    img: "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=400&auto=format&fit=crop"
  }
];

let activeAudio = null;

// Initialize App
document.addEventListener("DOMContentLoaded", () => {
  renderLexiconGrid(lexiconData);
  renderAudioRecordings(audioVoices);
  renderContributors();
  renderAdminTable();
  tryFetchBackendStats();
});

// --- NAVIGATION ---
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
    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full">${item.category || 'General'}</span>
          <span class="text-xs text-slate-400 font-medium">${item.part_of_speech || 'Noun'}</span>
        </div>
        <h3 class="text-2xl font-extrabold text-slate-900 mb-0.5 cursor-pointer hover:text-emerald-800" onclick="openWordDetailModal(${item.id})">${item.term}</h3>
        <div class="text-xs font-mono text-emerald-700 mb-3">${item.ipa_transcription || ''}</div>
        <p class="text-sm font-semibold text-slate-800 mb-1">${item.meaning_en}</p>
        <p class="text-xs text-slate-500 line-clamp-2">${item.meaning_standard_lang || ''}</p>
      </div>

      <div class="flex items-center justify-between pt-4 mt-4 border-t border-slate-100">
        <button onclick="playSampleAudio('${item.audio}')" class="play-btn">
          <i class="fa-solid fa-play text-sm ml-0.5"></i>
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
function filterLexiconEntries() {
  const query = document.getElementById("dict-search-input").value.toLowerCase().trim();
  const posFilter = document.getElementById("pos-filter").value;

  const filtered = lexiconData.filter(item => {
    const matchQuery = !query || 
      item.term.toLowerCase().includes(query) ||
      item.meaning_en.toLowerCase().includes(query) ||
      (item.ipa_transcription && item.ipa_transcription.toLowerCase().includes(query)) ||
      (item.meaning_standard_lang && item.meaning_standard_lang.toLowerCase().includes(query));

    const matchCategory = currentCategory === "All" || item.category.toLowerCase() === currentCategory.toLowerCase();
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

// --- AUDIO PLAYBACK API CONTROL ---
function playSampleAudio(audioUrl) {
  if (activeAudio) {
    activeAudio.pause();
  }
  activeAudio = new Audio(audioUrl);
  activeAudio.play().catch(e => {
    showToast("Audio playback preview simulated.");
  });
}

// --- WORD DETAIL MODAL ---
function openWordDetailModal(id) {
  const item = lexiconData.find(x => x.id === id) || lexiconData[0];
  const modal = document.getElementById("word-detail-modal");
  const content = document.getElementById("modal-content");

  content.innerHTML = `
    <div class="flex items-center gap-4 mb-4">
      <img src="${item.img || 'https://images.unsplash.com/photo-1544717305-2782549b5136?q=80&w=200&auto=format&fit=crop'}" class="w-16 h-16 rounded-full object-cover shadow-md" />
      <div>
        <h2 class="text-3xl font-extrabold text-slate-900">${item.term}</h2>
        <div class="text-base font-mono text-emerald-800 font-semibold">${item.ipa_transcription || '/ma:ja:lu/'}</div>
      </div>
    </div>

    <!-- Audio Control -->
    <div class="bg-slate-100 rounded-xl p-3 flex items-center gap-3 mb-6">
      <button onclick="playSampleAudio('${item.audio}')" class="play-btn w-10 h-10">
        <i class="fa-solid fa-play text-xs"></i>
      </button>
      <div class="flex-grow">
        <div class="text-xs font-semibold text-slate-700">Audio Pronunciation</div>
        <div class="text-[11px] text-slate-500">Duration: 0:07 • Recorded by Native Speaker</div>
      </div>
    </div>

    <div class="space-y-4 text-sm">
      <div class="p-3 bg-slate-50 rounded-xl">
        <span class="text-xs font-bold uppercase text-slate-400 block mb-0.5">Meaning</span>
        <span class="font-semibold text-slate-800">${item.meaning_en}</span>
      </div>

      <div class="p-3 bg-slate-50 rounded-xl">
        <span class="text-xs font-bold uppercase text-slate-400 block mb-0.5">Part of Speech</span>
        <span class="font-medium text-slate-700">${item.part_of_speech || 'Adjective'}</span>
      </div>

      <div class="p-3 bg-slate-50 rounded-xl">
        <span class="text-xs font-bold uppercase text-slate-400 block mb-0.5">Context Sentence</span>
        <p class="italic text-slate-700 mb-1">"${item.example_sentence_dialect || ''}"</p>
        <p class="text-xs text-slate-500">Translation: ${item.example_sentence_translation || ''}</p>
      </div>

      <div class="p-3 bg-slate-50 rounded-xl">
        <span class="text-xs font-bold uppercase text-slate-400 block mb-0.5">Native Speaker & Contributor</span>
        <span class="font-medium text-slate-800">${item.speaker_name || 'Sushila Tai'}, ${item.speaker_role || 'Native Speaker, Malvan'}</span>
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
    card.innerHTML = `
      <div class="flex items-center gap-4 w-full md:w-auto">
        <img src="${rec.img}" class="w-16 h-16 rounded-xl object-cover shadow-sm flex-shrink-0" />
        <div>
          <span class="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full">${rec.topic}</span>
          <h3 class="font-bold text-slate-900 text-lg mt-1">${rec.title}</h3>
          <div class="text-xs text-slate-500 mt-0.5">Speaker: <span class="font-medium text-slate-700">${rec.speaker}</span> • Duration: ${rec.duration}</div>
        </div>
      </div>

      <button onclick="playSampleAudio('${rec.audio}')" class="btn-primary px-6 py-2.5 rounded-full text-xs font-bold flex items-center gap-2 shadow-sm w-full md:w-auto justify-center">
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

// --- CONTRIBUTORS RENDER ---
function renderContributors() {
  const grid = document.getElementById("contributors-grid");
  if (!grid) return;

  const contributors = [
    { name: "Ganpat Kaka", role: "Native Speaker", region: "Konkan", recordings: 24, img: "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=200&auto=format&fit=crop" },
    { name: "Sushila Tai", role: "Native Speaker", region: "Malvan", recordings: 18, img: "https://images.unsplash.com/photo-1544717305-2782549b5136?q=80&w=200&auto=format&fit=crop" },
    { name: "Ramesh Patil", role: "Community Member", region: "Sindhudurg", recordings: 12, img: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=200&auto=format&fit=crop" },
    { name: "Lata Bai", role: "Native Speaker", region: "Rural Community", recordings: 15, img: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=200&auto=format&fit=crop" }
  ];

  grid.innerHTML = "";
  contributors.forEach(c => {
    const card = document.createElement("div");
    card.className = "bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center";
    card.innerHTML = `
      <img src="${c.img}" class="w-20 h-20 rounded-full object-cover mx-auto mb-3 shadow-md border-2 border-emerald-100" />
      <h3 class="font-bold text-slate-900 text-base">${c.name}</h3>
      <div class="text-xs font-semibold text-emerald-800 mb-1">${c.role}</div>
      <div class="text-xs text-slate-500 mb-3"><i class="fa-solid fa-location-dot text-slate-400 mr-1"></i> ${c.region}</div>
      <div class="text-xs font-medium bg-slate-50 py-1.5 px-3 rounded-lg text-slate-700">${c.recordings} Contributions</div>
    `;
    grid.appendChild(card);
  });
}

// --- FORM SUBMISSION & AUTO IPA GENERATOR ---
function autoGenerateIPA() {
  const term = document.getElementById("form-term").value;
  if (!term) {
    showToast("Please enter a word or phrase first.");
    return;
  }

  // Simple client-side Devanagari IPA mapper fallback
  const ipaMap = { 'अ':'ə','आ':'aː','इ':'i','ई':'iː','उ':'u','ऊ':'uː','ए':'eː','ऐ':'əi','ओ':'oː','औ':'əu','क':'kə','ख':'kʰə','ग':'ɡə','घ':'ɡʱə','च':'t͡ʃə','छ':'t͡ʃʰə','ज':'d͡ʒə','झ':'d͡ʒʱə','त':'t̪ə','थ':'t̪ʰə','द':'d̪ə','ध':'d̪ʱə','न':'nə','प':'pə','फ':'pʰə','ब':'bə','भ':'bʱə','म':'mə','य':'jə','र':'rə','ल':'lə','व':'ʋə','स':'sə','ह':'ɦə' };
  let res = "/";
  for (let char of term) {
    res += ipaMap[char] || char;
  }
  res += "/";

  document.getElementById("form-ipa").value = res;
  showToast("IPA Generated automatically!");
}

function handleWordSubmission(e) {
  e.preventDefault();
  const newEntry = {
    id: lexiconData.length + 1,
    term: document.getElementById("form-term").value,
    meaning_en: document.getElementById("form-meaning-en").value,
    meaning_standard_lang: document.getElementById("form-meaning-std").value,
    ipa_transcription: document.getElementById("form-ipa").value || "/new_term/",
    part_of_speech: document.getElementById("form-pos").value,
    example_sentence_dialect: document.getElementById("form-sentence").value,
    category: document.getElementById("form-category").value,
    dialect: "Malvani",
    speaker_name: "Community Contributor",
    speaker_role: "Native Contributor",
    status: "Pending",
    upvotes: 0,
    audio: "https://actions.google.com/sounds/v1/human/speech_male_cheerful.ogg"
  };

  lexiconData.unshift(newEntry);
  renderLexiconGrid(lexiconData);
  renderAdminTable();

  showToast("Thank you! Your word submission has been sent for review.");
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
    const row = document.createElement("tr");
    row.className = "hover:bg-slate-50 transition";
    row.innerHTML = `
      <td class="py-3.5 px-4 font-bold text-slate-900">${item.term}</td>
      <td class="py-3.5 px-4 text-slate-700">${item.meaning_en}</td>
      <td class="py-3.5 px-4"><span class="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded font-medium">${item.category}</span></td>
      <td class="py-3.5 px-4">
        <span class="text-xs px-2.5 py-1 rounded-full font-semibold ${item.status === 'Published' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
          ${item.status}
        </span>
      </td>
      <td class="py-3.5 px-4 text-right space-x-2">
        ${item.status === 'Pending' ? 
          `<button onclick="verifyEntry(${item.id})" class="text-xs bg-emerald-800 hover:bg-emerald-900 text-white font-bold px-3 py-1 rounded">Approve</button>` :
          `<button onclick="openWordDetailModal(${item.id})" class="text-xs bg-slate-200 hover:bg-slate-300 text-slate-700 font-medium px-2.5 py-1 rounded">View</button>`
        }
      </td>
    `;
    tbody.appendChild(row);
  });
}

function verifyEntry(id) {
  const item = lexiconData.find(x => x.id === id);
  if (item) {
    item.status = "Published";
    renderAdminTable();
    renderLexiconGrid(lexiconData);
    showToast(`Approved "${item.term}" entry!`);
  }
}

// --- BACKEND API INTEGRATION ---
async function tryFetchBackendStats() {
  try {
    const res = await fetch(`${API_BASE}/analytics/stats`);
    if (res.ok) {
      const data = await res.json();
      document.getElementById("stat-words").innerText = data.total_words_preserved || "1,240";
      document.getElementById("stat-audio").innerText = data.total_audio_recordings || "380";
      document.getElementById("stat-contributors").innerText = data.total_active_contributors || "12";
      document.getElementById("stat-dialects").innerText = data.total_dialects || "4";
    }
  } catch (e) {
    console.log("Backend offline or using pre-loaded client repository.");
  }
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
