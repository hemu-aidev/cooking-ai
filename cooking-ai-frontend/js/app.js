// js/app.js
//
// All state and all network calls for the page. Talks ONLY to the
// Application Layer's REST API (/api/search, /api/ask, /api/substitute)
// — it has no idea the Data/Model Layer or local LLM exist underneath.

(() => {
  'use strict';

  const els = {
    searchForm: document.getElementById('searchForm'),
    searchInput: document.getElementById('searchInput'),
    resultArea: document.getElementById('resultArea'),
    chips: document.querySelectorAll('.chip'),

    videoSection: document.getElementById('videoSection'),
    videoGrid: document.getElementById('videoGrid'),

    askSection: document.getElementById('askSection'),
    askRecipeName: document.getElementById('askRecipeName'),
    askLog: document.getElementById('askLog'),
    askForm: document.getElementById('askForm'),
    askInput: document.getElementById('askInput'),
    askBtn: document.getElementById('askBtn'),

    subSection: document.getElementById('subSection'),
    subForm: document.getElementById('subForm'),
    subSelect: document.getElementById('subSelect'),
    subBtn: document.getElementById('subBtn'),
    subResult: document.getElementById('subResult'),
  };

  const state = {
    currentQuery: null,   // matched_title from the last successful search
    ticketCount: 46,      // purely cosmetic — increments per ticket "fired"
  };

  // ---------- helpers ----------

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str ?? '';
    return div.innerHTML;
  }

  function ticketNumber() {
    state.ticketCount += 1;
    return '#' + String(state.ticketCount).padStart(3, '0');
  }

  async function apiGet(path) {
    const res = await fetch(`${API_BASE_URL}${path}`);
    let data;
    try { data = await res.json(); } catch { data = {}; }
    return { ok: res.ok, status: res.status, data };
  }

  async function apiPost(path, body) {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    let data;
    try { data = await res.json(); } catch { data = {}; }
    return { ok: res.ok, status: res.status, data };
  }

  // ---------- rendering: result ticket ----------

  function showLoading() {
    els.resultArea.innerHTML = `
      <div class="ticket ticket--loading">
        <p class="ticket__firing">firing your ticket…</p>
        <div class="skeleton-line" style="width:60%;height:28px;"></div>
        <div class="skeleton-line" style="width:30%;margin-top:14px;"></div>
        <div class="skeleton-line" style="width:90%;margin-top:22px;"></div>
        <div class="skeleton-line" style="width:80%;"></div>
        <div class="skeleton-line" style="width:85%;"></div>
      </div>`;
  }

  function showEmpty(message) {
    els.resultArea.innerHTML = `<p class="result__error">${escapeHtml(
      message || "No match in the kitchen yet. Try another dish name."
    )}</p>`;
    hideFollowupSections();
  }

  function showNetworkError() {
    els.resultArea.innerHTML = `<p class="result__error">
      Couldn't reach the kitchen. Check that the Application Layer is running, then try again.
    </p>`;
    hideFollowupSections();
  }

  function renderTicket(data) {
    const recipe = data.recipe;
    const ingredientRows = recipe.ingredients.map(i => `
      <li>
        <span class="ing-qty">${escapeHtml(i.quantity)} ${escapeHtml(i.unit || '')}</span>
        <span class="ing-name">${escapeHtml(i.name)}</span>
      </li>`).join('');

    const stepRows = recipe.steps.map(s => `<li>${escapeHtml(s)}</li>`).join('');

    els.resultArea.innerHTML = `
      <article class="ticket">
        <header class="ticket__head">
          <div>
            <h2 class="ticket__title">${escapeHtml(recipe.title)}</h2>
            <p class="ticket__tags">${(recipe.tags || []).map(escapeHtml).join(' · ')}</p>
          </div>
          <span class="ticket__no">${ticketNumber()}</span>
        </header>

        <div class="ticket__meta">
          <span>serves ${escapeHtml(recipe.servings ?? '—')}</span>
          <span>prep ${escapeHtml(recipe.prep_time_minutes ?? '—')}m</span>
          <span>cook ${escapeHtml(recipe.cook_time_minutes ?? '—')}m</span>
        </div>

        <p class="ticket__section-label">Ingredients</p>
        <ul class="ticket__ingredients">${ingredientRows}</ul>

        <p class="ticket__section-label">Method</p>
        <ol class="ticket__steps">${stepRows}</ol>

        <div class="ticket__tear" role="presentation"></div>
      </article>`;
  }

  // ---------- rendering: videos ----------

  function renderVideos(videos) {
    if (!videos || !videos.length || videos[0].error) {
      els.videoSection.hidden = true;
      return;
    }
    els.videoGrid.innerHTML = videos.map(v => `
      <a class="video-card" href="${escapeHtml(v.url)}" target="_blank" rel="noopener noreferrer">
        <img src="${escapeHtml(v.thumbnail)}" alt="" loading="lazy">
        <div class="video-card__body">
          <p class="video-card__title">${escapeHtml(v.title)}</p>
          <p class="video-card__channel">${escapeHtml(v.channel)}</p>
        </div>
      </a>`).join('');
    els.videoSection.hidden = false;
  }

  // ---------- follow-up sections ----------

  function showFollowupSections(recipeTitle, ingredients) {
    els.askRecipeName.textContent = recipeTitle;
    els.askLog.innerHTML = '';
    els.askSection.hidden = false;

    els.subSelect.innerHTML = ingredients
      .map(i => `<option value="${escapeHtml(i.name)}">${escapeHtml(i.name)}</option>`)
      .join('');
    els.subResult.textContent = '';
    els.subSection.hidden = false;
  }

  function hideFollowupSections() {
    els.videoSection.hidden = true;
    els.askSection.hidden = true;
    els.subSection.hidden = true;
  }

  // ---------- search ----------

  async function handleSearch(query) {
    query = query.trim();
    if (!query) return;

    showLoading();
    hideFollowupSections();

    let result;
    try {
      result = await apiGet(`/api/search?q=${encodeURIComponent(query)}&videos=4`);
    } catch {
      showNetworkError();
      return;
    }

    if (!result.ok || !result.data.found) {
      showEmpty(result.data.message);
      return;
    }

    state.currentQuery = result.data.matched_title;
    renderTicket(result.data);
    renderVideos(result.data.videos);
    showFollowupSections(result.data.matched_title, result.data.recipe.ingredients);
  }

  els.searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    handleSearch(els.searchInput.value);
  });

  els.chips.forEach(chip => {
    chip.addEventListener('click', () => {
      const q = chip.dataset.query;
      els.searchInput.value = q;
      handleSearch(q);
    });
  });

  // ---------- ask the line cook ----------

  els.askForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const question = els.askInput.value.trim();
    if (!question || !state.currentQuery) return;

    const qaEl = document.createElement('div');
    qaEl.className = 'qa qa--pending';
    qaEl.innerHTML = `<p class="qa__q">${escapeHtml(question)}</p><p class="qa__a">thinking…</p>`;
    els.askLog.appendChild(qaEl);
    els.askInput.value = '';
    els.askBtn.disabled = true;

    try {
      const result = await apiPost('/api/ask', { query: state.currentQuery, question });
      qaEl.classList.remove('qa--pending');
      qaEl.querySelector('.qa__a').textContent = result.data.answer ||
        "Couldn't get an answer for that — try rephrasing the question.";
    } catch {
      qaEl.classList.remove('qa--pending');
      qaEl.querySelector('.qa__a').textContent = "Couldn't reach the kitchen. Try again.";
    } finally {
      els.askBtn.disabled = false;
    }
  });

  // ---------- substitutions ----------

  els.subForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const ingredient = els.subSelect.value;
    if (!ingredient || !state.currentQuery) return;

    els.subBtn.disabled = true;
    els.subResult.textContent = 'checking the pantry…';

    try {
      const result = await apiPost('/api/substitute', { query: state.currentQuery, ingredient });
      els.subResult.textContent = result.data.substitution ||
        "No substitution data available for that ingredient.";
    } catch {
      els.subResult.textContent = "Couldn't reach the kitchen. Try again.";
    } finally {
      els.subBtn.disabled = false;
    }
  });

})();
