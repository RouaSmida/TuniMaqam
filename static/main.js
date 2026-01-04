    // --- Admin/Expert Maqam Actions ---
    async function editMaqam(maqamId) {
      try {
        const d = await api(`/knowledge/maqam/${maqamId}`);
        // Render a simple edit form for name and description (expand as needed)
        openModal(`
          <h2 style="color:var(--tunis-gold)">Edit Maqam</h2>
          <label style="font-size:0.9rem; color:var(--tunis-teal); font-weight:700;">Name (EN)</label>
          <input id="edit-maqam-name-en" value="${d.name?.en || d.name_en || ''}" style="margin-bottom:10px;" />
          <label style="font-size:0.9rem; color:var(--tunis-teal); font-weight:700;">Name (AR)</label>
          <input id="edit-maqam-name-ar" value="${d.name?.ar || d.name_ar || ''}" style="margin-bottom:10px;" />
          <label style="font-size:0.9rem; color:var(--tunis-teal); font-weight:700;">Description (EN)</label>
          <textarea id="edit-maqam-desc-en" rows="3" style="margin-bottom:10px;">${d.descriptions?.en || d.description_en || ''}</textarea>
          <label style="font-size:0.9rem; color:var(--tunis-teal); font-weight:700;">Description (AR)</label>
          <textarea id="edit-maqam-desc-ar" rows="3" style="margin-bottom:10px;">${d.descriptions?.ar || d.description_ar || ''}</textarea>
          <button class="btn-action" style="margin-top:10px;" onclick="submitEditMaqam(${maqamId})">Save Changes</button>
          <button class="btn-ghost" style="margin-left:10px;" onclick="closeModal()">Cancel</button>
        `);
      } catch (e) {
        notify(e.message || 'Failed to load maqam', 'error');
      }
    }

    async function submitEditMaqam(maqamId) {
      const name_en = document.getElementById('edit-maqam-name-en').value.trim();
      const name_ar = document.getElementById('edit-maqam-name-ar').value.trim();
      const desc_en = document.getElementById('edit-maqam-desc-en').value.trim();
      const desc_ar = document.getElementById('edit-maqam-desc-ar').value.trim();
      try {
        await api(`/knowledge/maqam/${maqamId}`, 'PUT', {
          name_en: name_en,
          name_ar: name_ar,
          description_en: desc_en,
          description_ar: desc_ar
        });
        notify('Maqam updated');
        closeModal();
        searchMaqam();
      } catch (e) {
        notify(e.message || 'Update failed', 'error');
      }
    }

    async function deleteMaqam(maqamId) {
      if (!confirm('Are you sure you want to delete this maqam? This cannot be undone.')) return;
      try {
        await api(`/knowledge/maqam/${maqamId}`, 'DELETE');
        notify('Maqam deleted');
        closeModal();
        searchMaqam();
      } catch (e) {
        notify(e.message || 'Delete failed', 'error');
      }
    }
    const STORE_KEY = 'tuni_jwt_v4';
    const DEMO_TOKEN_ENDPOINT = '/auth/demo-token';
    const flashcardsState = { cards: [], idx: 0, topic: 'emotion' };
    let currentQuiz = null;
    let demoTokenLock = false;

    // Game state tracking
    const gameState = {
      mcq: { completed: new Set(), total: 0 },
      matching: { completed: new Set(), total: 0 },
      audio: { completed: new Set(), total: 0 },
      detective: { completed: new Set(), total: 0 },
      sequencer: { completed: new Set(), total: 0 }
    };

    async function initGameState() {
      try {
        const d = await api('/status');
        const total = d.maqamet_count || 0;
        Object.keys(gameState).forEach(k => gameState[k].total = total);
      } catch(e) { console.warn('Could not init game state'); }
    }

    async function fetchDemoToken(showToast=false) {
      if (demoTokenLock) return false;
      demoTokenLock = true;
      try {
        const res = await fetch(DEMO_TOKEN_ENDPOINT);
        if (!res.ok) return false;
        const data = await res.json();
        if (!data.access_token) return false;
        localStorage.setItem(STORE_KEY, data.access_token);
        if (showToast) notify('Demo token loaded');
        checkAuth();
        return true;
      } catch (e) {
        console.error('Demo token failed', e);
        return false;
      } finally {
        demoTokenLock = false;
      }
    }

    // --- Core Utilities ---
    function notify(msg, type='success') {
      const toaster = document.getElementById('toaster');
      const el = document.createElement('div');
      el.className = `toast ${type}`;
      el.innerHTML = type === 'success' ? `<span style="font-weight:bold; color:var(--tunis-teal);">✓</span> ${msg}` : `<span style="font-weight:bold; color:var(--tunis-rose);">✕</span> ${msg}`;
      toaster.appendChild(el);
      setTimeout(() => {
        el.style.opacity = '0';
        el.style.transform = 'translateX(100%)';
        setTimeout(() => el.remove(), 300);
      }, 4000);
    }

    function route(ev, id) {
      document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
      document.getElementById(id).classList.add('active');
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      if (ev && ev.target.classList.contains('nav-btn')) ev.target.classList.add('active');
      else if (id === 'dashboard') document.querySelector('.nav-btn').classList.add('active');
      window.scrollTo(0,0);
    }

    function openModal(html) {
      document.getElementById('modal-body').innerHTML = html;
      document.getElementById('modal').classList.add('active');
      document.body.style.overflow = 'hidden';
    }
    function closeModal() {
      document.getElementById('modal').classList.remove('active');
      document.body.style.overflow = '';
      setTimeout(() => document.getElementById('modal-body').innerHTML = '', 300);
    }

    async function api(endpoint, method='GET', body=null, skipRetry=false) {
      let token = localStorage.getItem(STORE_KEY);
      if (!token) {
        await fetchDemoToken();
        token = localStorage.getItem(STORE_KEY);
      }

      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      
      const opts = { method, headers };
      if (body instanceof FormData) {
          delete headers['Content-Type']; // let browser set boundary
          opts.body = body;
      } else if (body) {
          opts.body = JSON.stringify(body);
      }

      const res = await fetch(endpoint, opts);
      let json = {};
      try { json = await res.json(); } catch (e) {}
      if (res.status === 401 && !skipRetry) {
          const refreshed = await fetchDemoToken();
          if (refreshed) return api(endpoint, method, body, true);
      }
      if (!res.ok) throw new Error(json.error || json.message || `Error ${res.status}`);
      return json;
    }

    // Log activity completions to leaderboard/progress service
    async function completeActivity(maqamId, activity) {
      if (!maqamId || !activity) return;
      try {
        await api('/learning/complete-activity', 'POST', { maqam_id: maqamId, activity });
      } catch (e) {
        console.warn('Activity log failed', e);
      }
    }

    // Show game completion modal with stats
    function showGameComplete(gameType, correct, total) {
      const percent = total > 0 ? Math.round((correct / total) * 100) : 0;
      
      openModal(`
        <div style="text-align:center; padding:20px;">
          <h2 style="font-size:2.5rem; color:${percent >= 70 ? 'var(--tunis-teal)' : percent >= 50 ? 'var(--tunis-gold)' : 'var(--tunis-rose)'}; margin:0 0 8px;">${percent}%</h2>
          <p style="color:var(--text-muted); margin:0 0 20px;">Score: ${correct}/${total} correct</p>
          
          <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap;">
            <button class="btn-action" style="width:auto; padding:12px 24px;" onclick="closeModal()">Done</button>
            <button class="btn-ghost" style="width:auto;" onclick="runMCQ()">Play Again</button>
          </div>
        </div>
      `);
    }

    // --- Auth & Status ---
    function handleAuth() {
      const val = document.getElementById('token').value.trim();
      if (!val) return notify('Token required', 'error');
      localStorage.setItem(STORE_KEY, val);
      checkAuth();
      notify('Secure Connection Established');
    }
    function checkAuth() {
      const t = localStorage.getItem(STORE_KEY);
      const status = document.getElementById('auth-status');
      if (t) {
        try {
          const p = JSON.parse(atob(t.split('.')[1]));
          status.innerHTML = `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--tunis-teal)"></span> Connected | ${p.role || 'User'}`;
          status.style.color = "var(--tunis-teal)";
        } catch {
          status.innerHTML = `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--tunis-rose)"></span> Invalid Token`;
          status.style.color = "var(--tunis-rose)";
        }
      } else {
        status.innerHTML = `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#475569;"></span> Offline`;
        status.style.color = "var(--text-muted)";
      }
    }

    async function refreshStats() {
      try {
        const d = await api('/status');
        animateValue("stat-maqam", 0, d.maqamet_count, 800);
        animateValue("stat-contrib", 0, d.contributions_count, 800);
      } catch(e) { console.error(e); }
    }
    function animateValue(id, start, end, duration) {
      const obj = document.getElementById(id);
      let startTimestamp = null;
      const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start);
        if (progress < 1) window.requestAnimationFrame(step);
      };
      window.requestAnimationFrame(step);
    }

    // --- Knowledge / Archive ---
    function filterByMap(regionName) {
      document.querySelectorAll('.map-pin').forEach(p => p.classList.remove('active'));
      const pin = document.getElementById(`pin-${regionName.toLowerCase()}`);
      if(pin) pin.classList.add('active');
      
      document.getElementById('region-input').value = regionName;
      document.getElementById('search-input').value = "";
      searchMaqam();
      notify(`Filtered by ${regionName}`);
    }

    async function searchMaqam() {
      const q = document.getElementById('search-input').value.trim();
      const region = document.getElementById('region-input').value.trim();
      let url = '/knowledge/maqam';
      
      if (q) url = `/knowledge/maqam/by-name/${encodeURIComponent(q)}`;
      else if (region) url = `/knowledge/maqam?region=${encodeURIComponent(region)}`;

      const grid = document.getElementById('maqam-grid');
      grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; color:var(--tunis-teal); padding:20px;">Scanning Archives...</div>';
      try {
        let d = await api(url);
        if (!Array.isArray(d)) d = [d];
        grid.innerHTML = '';
        if (d.length === 0) grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:24px; color:var(--text-muted);">No records found. Try another name or region.</div>';
        // Get user role from JWT
        let userRole = null;
        try {
          const t = localStorage.getItem(STORE_KEY);
          if (t) {
            const p = JSON.parse(atob(t.split('.')[1]));
            userRole = p.role;
          }
        } catch {}
        d.forEach(m => {
          const nameEn = m.name_en || m.name?.en || 'Unknown';
          const nameAr = m.name_ar || m.name?.ar || '';
          const desc = (m.descriptions?.en || m.description?.en || m.description_en || 'No description available.').substring(0, 100);
          const rarity = m.rarity_level?.en || m.rarity_level || 'common';
          let regionList = "";
          try {
              if (m.regions) {
                  if (Array.isArray(m.regions)) regionList = m.regions.join(', ');
                  else if (m.regions.en) regionList = m.regions.en.join(', ');
              } else if (m.regions_json) {
                  regionList = JSON.parse(m.regions_json).join(', ');
              }
          } catch(e) {}
          const div = document.createElement('div');
          div.className = 'glass-card';
          let adminBtns = '';
          if (userRole === 'admin' || userRole === 'expert') {
            adminBtns = `
              <button class="btn-ghost" style="color:var(--tunis-rose);" onclick="editMaqam(${m.id})">Edit</button>
              <button class="btn-ghost" style="color:var(--tunis-rose);" onclick="deleteMaqam(${m.id})">Delete</button>
            `;
          }
          div.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
              <div>
                <h3 style="font-size:1.4rem; color:var(--tunis-gold);">${nameEn}</h3>
                <div class="ar-text" style="font-size:1.1rem; color:var(--text-muted); margin-top:2px;">${nameAr}</div>
              </div>
              <span class="tag ${rarity === 'at_risk' ? 'rose' : 'blue'}">${rarity}</span>
            </div>
            <p style="margin:16px 0; color:var(--text-main); font-size:0.9rem; line-height:1.5;">${desc}...</p>
            <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:20px;">
              <strong>Origin:</strong> ${regionList || 'Tunisia'}
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
              <button class="btn-ghost" onclick="showDetail(${m.id})">Inspect</button>
              <button class="btn-ghost" onclick="openContribForm(${m.id})">Contribute</button>
              ${adminBtns}
            </div>
          `;
          grid.appendChild(div);
        });
      } catch(e) {
        grid.innerHTML = `<div style="color:var(--tunis-rose); grid-column:1/-1; text-align:center;">Error: ${e.message}</div>`;
      }
    }

    async function showDetail(id) {
      try {
        const d = await api(`/knowledge/maqam/${id}`);
        
        const nameEn = d.name?.en || d.name_en || 'Unknown';
        const nameAr = d.name?.ar || d.name_ar || '';

        const descEn = d.descriptions?.en || d.description_en || '';
        const descAr = d.descriptions?.ar || d.description_ar || '';
        const regionsEn = d.regions?.en || [];
        const regionsAr = d.regions?.ar || [];
        const emotionEn = d.emotion?.en || d.emotion || '-';
        const emotionAr = d.emotion?.ar || d.emotion_ar || '-';
        const usageEn = Array.isArray(d.usage?.en) ? d.usage.en.join(', ') : (d.usage || '-');
        const usageAr = Array.isArray(d.usage?.ar) ? d.usage.ar.join(', ') : (d.usage_ar || '-');
        const level = d.difficulty_label?.en || d.difficulty_label || '-';
        const rarity = d.rarity_level?.en || d.rarity_level || '-';
        const rarityAr = d.rarity_level?.ar || d.rarity_level_ar || '';
        // New fields
        const historicalPeriodsEn = d.historical_periods_json ? JSON.parse(d.historical_periods_json) : (d.historical_periods?.en || []);
        const historicalPeriodsAr = d.historical_periods_ar_json ? JSON.parse(d.historical_periods_ar_json) : (d.historical_periods?.ar || []);
        const seasonalUsageEn = d.seasonal_usage_json ? JSON.parse(d.seasonal_usage_json) : (d.seasonal_usage?.en || []);
        const seasonalUsageAr = d.seasonal_usage_ar_json ? JSON.parse(d.seasonal_usage_ar_json) : (d.seasonal_usage?.ar || []);

        const ajnas = Array.isArray(d.ajnas) ? d.ajnas : [];
        const ajnasHTML = ajnas.length ? ajnas.map(a => {
            const nm = typeof a.name === 'object' ? (a.name.en || a.name.ar || '') : (a.name || '');
            const nmAr = typeof a.name === 'object' ? (a.name.ar || '') : '';
            const notesEn = (a.notes && a.notes.en) ? a.notes.en.join(', ') : Array.isArray(a.notes) ? a.notes.join(', ') : '';
            const notesAr = (a.notes && a.notes.ar) ? a.notes.ar.join('، ') : '';
            return `
                <div style="padding:10px; border:1px solid var(--glass-border); border-radius:10px; margin-bottom:8px;">
                    <div style="font-weight:700; color:var(--tunis-gold);">${nm}</div>
                    ${nmAr ? `<div class="ar-text" style="color:var(--text-muted);">${nmAr}</div>` : ''}
                    ${notesEn ? `<div style="margin-top:6px; font-size:0.9rem; color:var(--text-muted);">Notes: ${notesEn}</div>` : ''}
                    ${notesAr ? `<div class="ar-text" style="font-size:0.9rem; color:var(--text-muted);">${notesAr}</div>` : ''}
                </div>
            `;
        }).join('') : '<div style="color:var(--text-muted);">No structural data.</div>';

        const metaRow = (label, valEn, valAr) => `
            <div style="display:flex; justify-content:space-between; gap:12px; padding:10px 0; border-bottom:1px solid var(--glass-border);">
                <div style="color:var(--tunis-teal); font-weight:700;">${label}</div>
                <div style="text-align:right;">
                    <div>${valEn || '-'}</div>
                    ${valAr && valAr !== '-' ? `<div class="ar-text" style="color:var(--text-muted); font-size:0.9rem">${valAr}</div>` : ''}
                </div>
            </div>`;

        const cleanDesc = (txt='') => txt.replace(/\([^)]*regions[^)]*\)/ig, '').trim();

        // Get user role from JWT
        let userRole = null;
        try {
          const t = localStorage.getItem(STORE_KEY);
          if (t) {
            const p = JSON.parse(atob(t.split('.')[1]));
            userRole = p.role;
          }
        } catch {}
        let audioBtn = '';
        if (Array.isArray(d.audio_urls) && d.audio_urls.length > 0) {
          audioBtn = `<button class="btn-action" style="margin-top:16px;" onclick="showAudioModal(${id})">Show Audio (${d.audio_urls.length})</button>`;
        }
        let adminBtns = '';
        if (userRole === 'admin' || userRole === 'expert') {
          adminBtns = `
            <div style="margin-top:16px; display:flex; gap:8px;">
              <button class="btn-ghost" style="color:var(--tunis-rose);" onclick="editMaqam(${id})">Edit Maqam</button>
              <button class="btn-ghost" style="color:var(--tunis-rose);" onclick="deleteMaqam(${id})">Delete Maqam</button>
            </div>
          `;
        }
        const html = `
          <div style="display:grid; grid-template-columns: 1fr; gap:8px; align-items:center; margin-bottom:12px;">
            <div>
              <h2 style="color:var(--tunis-gold); font-size:2.2rem; margin:0;">${nameEn}</h2>
              <div class="ar-text" style="font-size:1.4rem; color:var(--text-muted);">${nameAr}</div>
              <div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:10px;">
                <span class="tag gold" style="border-color:rgba(251,191,36,0.4); background:rgba(251,191,36,0.12);">Level: ${level}</span>
                <span class="tag blue" style="border-color:rgba(45,212,191,0.3); background:rgba(45,212,191,0.12);">Rarity: ${rarity}</span>
              </div>
            </div>
          </div>

          <div class="glass-card" style="margin-top:4px; padding:16px; border:1px solid var(--glass-border); background:rgba(255,255,255,0.03);">
             <h4 style="color:var(--tunis-teal); margin:0 0 8px; letter-spacing:0.5px;">Description</h4>
             <p style="line-height:1.6; margin:0 0 8px;">${cleanDesc(descEn) || 'No description.'}</p>
             ${descAr ? `<p class="ar-text" style="line-height:1.6; color:var(--text-muted); margin:0;">${cleanDesc(descAr)}</p>` : ''}
          </div>

          <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:18px; margin-top:18px;">
            <div class="glass-card" style="padding:16px; border:1px solid var(--glass-border); background:rgba(255,255,255,0.03);">
               <h4 style="color:var(--text-main); margin:0 0 8px; letter-spacing:0.5px;">Profile</h4>
               ${metaRow('Emotion', emotionEn, emotionAr)}
               ${metaRow('Usage', usageEn, usageAr)}
               ${metaRow('Level', level, '')}
               ${metaRow('Regions', regionsEn.join(', '), regionsAr.join('، '))}
               ${metaRow('Historical Periods', (historicalPeriodsEn||[]).join(', '), (historicalPeriodsAr||[]).join('، '))}
               ${metaRow('Seasonal Usage', (seasonalUsageEn||[]).join(', '), (seasonalUsageAr||[]).join('، '))}
            </div>
            <div class="glass-card" style="padding:16px; border:1px solid var(--glass-border); background:rgba(255,255,255,0.03);">
               <h4 style="color:var(--text-main); margin:0 0 8px; letter-spacing:0.5px;">Ajnas</h4>
               <div>${ajnasHTML}</div>
            </div>
          </div>
          ${audioBtn}
          ${adminBtns}
        `;
        openModal(html);
        // Attach showAudioModal to window so inline onclick works
        window.showAudioModal = showAudioModal;
        // Show all audio files for a maqam in a modal (global scope)
        async function showAudioModal(id) {
          try {
            const d = await api(`/knowledge/maqam/${id}`);
            if (!Array.isArray(d.audio_urls) || d.audio_urls.length === 0) {
              return notify('No audio files available for this maqam.', 'error');
            }
            // Get user role from JWT
            let userRole = null;
            try {
              const t = localStorage.getItem(STORE_KEY);
              if (t) {
                const p = JSON.parse(atob(t.split('.')[1]));
                userRole = p.role;
              }
            } catch {}
            const audioHtml = d.audio_urls.map((url, idx) => {
              let audioAdminBtns = '';
              if (userRole === 'admin' || userRole === 'expert') {
                audioAdminBtns = `
                  <button class="btn-ghost" style="color:var(--tunis-rose); margin-left:8px;" onclick="editAudio(${d.audio_ids ? d.audio_ids[idx] : ''}, ${id})">Edit</button>
                  <button class="btn-ghost" style="color:var(--tunis-rose);" onclick="deleteAudio(${d.audio_ids ? d.audio_ids[idx] : ''}, ${id})">Delete</button>
                `;
              }
              return `
                <div style="margin-bottom:18px;">
                  <h4 style="color:var(--text-main); margin:0 0 8px; letter-spacing:0.5px;">Audio ${idx+1}</h4>
                  <audio controls src="${url}" style="width:100%;"></audio>
                  ${audioAdminBtns}
                </div>
              `;
            }).join('');
            openModal(`
              <h2 style="color:var(--tunis-gold); margin-bottom:18px;">Audio Files</h2>
              ${audioHtml}
              <button class="btn-action" style="margin-top:12px;" onclick="closeModal()">Close</button>
            `);
          } catch (e) {
            notify(e.message || 'Failed to load audio files', 'error');
          }
        }
      } catch (e) { notify(e.message, 'error'); }
    }

    async function openContribForm(id) {
      openModal(`
         <h2 style="color:var(--tunis-gold)">Contribute to Maqam</h2>
         <p style="color:var(--text-muted); margin-bottom:20px;">Help expand the archive with additional information.</p>
         <label style="font-size:0.8rem; font-weight:700; color:var(--tunis-teal); text-transform:uppercase; display:block; margin-bottom:6px;">Contribution Type</label>
         <select id="contrib-type" style="width:100%; padding:12px; border-radius:8px; background:rgba(255,255,255,0.05); border:1px solid var(--glass-border); color:white; margin-bottom:16px;">
           <option value="usage_add">Usage / Context</option>
           <option value="anecdote">Historical Anecdote</option>
           <option value="region_add">Regional Association</option>
           <option value="emotion_note">Emotional Note</option>
           <option value="audio_link">Audio Reference Link</option>
           <option value="audio_upload">Audio File Upload</option>
           <option value="correction">Correction / Fix</option>
           <option value="other">Other</option>
         </select>
         <label style="font-size:0.8rem; font-weight:700; color:var(--tunis-teal); text-transform:uppercase; display:block; margin-bottom:6px;">Title / Summary</label>
         <input id="contrib-title" placeholder="Brief title for your contribution" style="margin-bottom:16px;" />
         <label style="font-size:0.8rem; font-weight:700; color:var(--tunis-teal); text-transform:uppercase; display:block; margin-bottom:6px;">Details</label>
         <textarea id="contrib-details" rows="4" placeholder="Describe your contribution in detail..." style="margin-bottom:16px;"></textarea>
         <label style="font-size:0.8rem; font-weight:700; color:var(--tunis-teal); text-transform:uppercase; display:block; margin-bottom:6px;">Source (optional)</label>
         <input id="contrib-source" placeholder="Where did you learn this? (book, teacher, etc.)" style="margin-bottom:20px;" />
         <div id="audio-upload-section" style="margin-bottom:16px;">
           <label style="font-size:0.8rem; font-weight:700; color:var(--tunis-teal); display:block; margin-bottom:6px;">Upload Audio File (optional)</label>
           <input type="file" id="contrib-audio-file" accept="audio/*" />
         </div>
         <button class="btn-action" onclick="submitContrib(${id})">Submit Contribution</button>
         <p style="color:var(--text-muted); font-size:0.8rem; margin-top:12px;">Your contribution will be reviewed by experts before being added.</p>
       `);
    }

    async function submitContrib(id) {
      const type = document.getElementById('contrib-type').value;
      const title = document.getElementById('contrib-title').value.trim();
      const details = document.getElementById('contrib-details').value.trim();
      const source = document.getElementById('contrib-source').value.trim();
      if (!title || !details) {
        return notify('Please fill in title and details', 'error');
      }
      const payload = { title, details, source };
      try {
        const fileInput = document.getElementById('contrib-audio-file');
        const hasAudio = fileInput && fileInput.files && fileInput.files.length > 0;
        if (hasAudio) {
          const file = fileInput.files[0];
          const formData = new FormData();
          formData.append('type', type);
          formData.append('payload', JSON.stringify(payload));
          formData.append('audio', file);
          await api(`/knowledge/maqam/${id}/contributions`, 'POST', formData);
        } else {
          await api(`/knowledge/maqam/${id}/contributions`, 'POST', { type, payload });
        }
        notify('Contribution submitted for review');
        closeModal();
      } catch(e) { notify(e.message || 'Submission failed', 'error'); }
    }

    async function openNewMaqamForm() {
      openModal(`
        <h2 style="color:var(--tunis-gold)">Propose New Maqam</h2>
        <p style="color:var(--text-muted); margin-bottom:20px;">Submit a maqam that's not yet in our archive.</p>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px;">
          <div>
            <label style="font-size:0.8rem; font-weight:700; color:var(--tunis-teal); text-transform:uppercase; display:block; margin-bottom:6px;">Name (English) *</label>
            <input id="new-maqam-name-en" placeholder="e.g. Sika" />
          </div>
          <div>
            <label style="font-size:0.8rem; font-weight:700; color:var(--tunis-teal); text-transform:uppercase; display:block; margin-bottom:6px;">Name (Arabic) *</label>
            <input id="new-maqam-name-ar" placeholder="e.g. سيكا" dir="rtl" />
          </div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px;">
          <div>
            <label style="font-size:0.8rem; font-weight:700; color:var(--tunis-teal); text-transform:uppercase; display:block; margin-bottom:6px;">First Jins (Tetrachord) *</label>
            <input id="new-maqam-jins1" placeholder="e.g. Bayati, Rast, Hijaz" />
          </div>
          <div>
            <label style="font-size:0.8rem; font-weight:700; color:var(--tunis-teal); text-transform:uppercase; display:block; margin-bottom:6px;">Second Jins *</label>
            <input id="new-maqam-jins2" placeholder="e.g. Nahawand, Kurd" />
          </div>
        </div>
        <label style="font-size:0.8rem; font-weight:700; color:var(--tunis-teal); text-transform:uppercase; display:block; margin-bottom:6px;">Emotion / Mood</label>
        <input id="new-maqam-emotion" placeholder="e.g. melancholic, joyful, spiritual" style="margin-bottom:16px;" />
        <label style="font-size:0.8rem; font-weight:700; color:var(--tunis-teal); text-transform:uppercase; display:block; margin-bottom:6px;">Regions (comma-separated)</label>
        <input id="new-maqam-regions" placeholder="e.g. Tunis, Sahel" style="margin-bottom:16px;" />
        <label style="font-size:0.8rem; font-weight:700; color:var(--tunis-teal); text-transform:uppercase; display:block; margin-bottom:6px;">Usage Context</label>
        <textarea id="new-maqam-usage" rows="2" placeholder="When is this maqam traditionally used?" style="margin-bottom:16px;"></textarea>
        <label style="font-size:0.8rem; font-weight:700; color:var(--tunis-teal); text-transform:uppercase; display:block; margin-bottom:6px;">Your Source / Reference</label>
        <input id="new-maqam-source" placeholder="Where did you learn about this maqam?" style="margin-bottom:20px;" />
        <div style="margin-bottom:16px;">
          <label style="font-size:0.8rem; font-weight:700; color:var(--tunis-teal); display:block; margin-bottom:6px;">Upload Audio File (optional)</label>
          <input type="file" id="new-maqam-audio-file" accept="audio/*" />
        </div>
        <button class="btn-action" onclick="submitNewMaqam()">Submit for Review</button>
        <p style="color:var(--text-muted); font-size:0.8rem; margin-top:12px;">* Required fields. Your proposal will be reviewed by experts.</p>
      `);
    }

    async function submitNewMaqam() {
      const name_en = document.getElementById('new-maqam-name-en').value.trim();
      const name_ar = document.getElementById('new-maqam-name-ar').value.trim();
      const jins1 = document.getElementById('new-maqam-jins1').value.trim();
      const jins2 = document.getElementById('new-maqam-jins2').value.trim();
      const emotion = document.getElementById('new-maqam-emotion').value.trim();
      const regions = document.getElementById('new-maqam-regions').value.trim();
      const usage = document.getElementById('new-maqam-usage').value.trim();
      const source = document.getElementById('new-maqam-source').value.trim();
      const audioInput = document.getElementById('new-maqam-audio-file');
      if (!name_en || !name_ar || !jins1 || !jins2) {
        return notify('Please fill in name (both languages) and both ajnas', 'error');
      }
      // (No modal or HTML code should be here. Removed invalid code.)
      // If you want to show a modal, add it here as a template literal and ensure all code is valid JS.
    }

    // --- Analysis ---
    async function runAnalysis() {
      const btn = document.getElementById('btn-analyze');
      setLoading(btn, true, 'Analyzing...');
      const notes = document.getElementById('an-notes').value.split(',').map(n => n.trim());
      const mood = document.getElementById('an-mood').value;
      const out = document.getElementById('analysis-output');
      out.innerHTML = 'Processing...';
      try {
        const d = await api('/analysis/notes', 'POST', { notes, optional_mood: mood });
        renderCandidates(d.candidates);
      } catch(e) { out.innerHTML = `Error: ${e.message}`; }
      finally { setLoading(btn, false, 'Analyze Sequence'); }
    }

    async function runAudioAnalysis() {
        const fileInput = document.getElementById('an-audio-file');
      const file = fileInput.files[0];
      if (!file) return notify("Select file", "error");
      const allowed = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg'];
      if (file.type && !allowed.includes(file.type)) {
        return notify('Unsupported audio type', 'error');
      }
        const out = document.getElementById('analysis-output');
        out.innerHTML = 'Uploading & Analyzing (this may take time)...';
      const btn = document.getElementById('btn-audio');
      setLoading(btn, true, 'Uploading...');
        const formData = new FormData();
      formData.append("audio", file);
        
        try {
            const d = await api('/analysis/audio', 'POST', formData);
            out.innerHTML = `<div style="margin-bottom:10px; color:var(--tunis-teal);">Extracted Notes: ${d.extracted_notes.join(', ')}${d.warning ? ' (fallback used)' : ''}</div>`;
            renderCandidates(d.candidates, true);
      } catch(e) { out.innerHTML = `Error: ${e.message}`; }
      finally { setLoading(btn, false, 'Upload & Process'); }
    }

    function renderCandidates(candidates, append=false) {
        const out = document.getElementById('analysis-output');
        const html = (candidates || []).map(c => {
          // Build evidence tags
          const evidence = c.evidence || [];
          const evidenceTags = evidence.map(ev => {
            if (ev === 'note_pattern_match') return '<span class="tag blue" style="font-size:0.7rem; padding:4px 8px;">Notes Match</span>';
            if (ev === 'emotion_alignment') return '<span class="tag gold" style="font-size:0.7rem; padding:4px 8px;">Emotion Match</span>';
            return '';
          }).filter(t => t).join(' ');
          
          return `
             <div class="glass-card" style="margin-bottom:12px; padding:16px;">
               <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                 <strong style="font-size:1.1rem; color:var(--tunis-gold);">${c.maqam}</strong>
                 <span class="tag blue">${Math.round((c.confidence||0)*100)}% Match</span>
               </div>
               <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:8px;">${evidenceTags}</div>
               <div style="font-size:0.9rem; color:var(--text-muted); margin-top:6px;">${c.reason}</div>
               ${c.matched_notes && c.matched_notes.length ? `<div style="font-size:0.85rem; color:var(--tunis-teal); margin-top:4px;">Matched notes: ${c.matched_notes.join(', ')}</div>` : ''}
             </div>
          `;
        }).join('');
        if(append) out.innerHTML += html; else out.innerHTML = html || 'No match found.';
    }

    async function runRecommendation() {
      const btn = document.getElementById('rec-btn');
      setLoading(btn, true, 'Generating...');
      const body = {
        mood: document.getElementById('rec-mood').value,
        event: document.getElementById('rec-event').value,
        region: document.getElementById('rec-region').value,
        time_period: document.getElementById('rec-period').value,
        preserve_heritage: document.getElementById('rec-heritage').checked,
        simple_for_beginners: document.getElementById('rec-simple').checked
      };
      try {
        const d = await api('/recommendations/maqam', 'POST', body);
        const out = document.getElementById('rec-output');
        out.innerHTML = d.recommendations.map(r => `
          <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; margin-bottom:8px;">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
              <div style="color:var(--tunis-gold); font-weight:bold;">${r.maqam}</div>
              <div class="tag blue">${Math.round((r.confidence||0)*100)}% match</div>
            </div>
            <div style="font-size:0.8rem;">${r.reason}</div>
          </div>
        `).join('') || '<div style="color:var(--text-muted);">No matches.</div>';
      } catch(e) { notify(e.message, 'error'); }
      finally { setLoading(btn, false, 'Generate Ideas'); }
    }

    // --- Learning ---
    async function openFlashcardsModal() {
      const html = `
        <div>
          <h2 style="color:var(--tunis-gold); text-align:center;">Flashcards</h2>
          <p style="text-align:center; color:var(--text-muted); margin-top:4px;">All cards load together; tap any card to flip.</p>
          <div style="margin-bottom:16px; display:flex; gap:10px; justify-content:center; align-items:center; flex-wrap:wrap;">
            <select id="fc-topic-select" style="width:auto; display:inline-block;">
              <option value="emotion">Emotion</option>
              <option value="region">Region</option>
              <option value="usage">Usage</option>
              <option value="ajnas">Ajnas (Tetrachords)</option>
            </select>
            <button class="btn-action" style="width:auto;" onclick="renderFlashcardsDeck(true)">Load Deck</button>
            <button class="btn-ghost" style="width:auto;" onclick="flashcardShuffle()">Shuffle</button>
          </div>
          <div id="fc-deck-container" style="min-height:420px; width:100%;"></div>
        </div>
      `;
      openModal(html);
      renderFlashcardsDeck(true);
    }

    async function renderFlashcardsDeck(loadNew=false) {
      const topicSelect = document.getElementById('fc-topic-select');
      if (!topicSelect) return;
      const topic = topicSelect.value;
      const container = document.getElementById('fc-deck-container');
      container.innerHTML = 'Loading...';
      if (loadNew) {
        flashcardsState.topic = topic;
      }
      try {
        const d = await api(`/learning/flashcards?topic=${flashcardsState.topic}`);
        if(!d.cards || !d.cards.length) { container.innerHTML = 'No cards found.'; return; }
        flashcardsState.cards = d.cards;
        container.innerHTML = `
          <div class="fc-grid-large">
            ${flashcardsState.cards.map((card, idx) => flashcardCardHTML(card, flashcardsState.topic, idx)).join('')}
          </div>
        `;
      } catch(e) { container.innerHTML = 'Error loading cards.'; }
    }

    function flashcardCardHTML(card, topic, idx) {
      let backEn = '';
      let backLabel = topic;
      
      if (topic === 'emotion') {
        backEn = card.emotion_en || card.back;
      } else if (topic === 'usage') {
        backEn = card.usage_en || (Array.isArray(card.back) ? card.back.join(', ') : card.back);
      } else if (topic === 'ajnas') {
        // Special layout for ajnas showing first and second jins
        const first_en = card.first_jins_en || '';
        const second_en = card.second_jins_en || '';
        backLabel = 'Ajnas';
        return `
          <div class="magic-card fc-small" data-idx="${idx}" onclick="toggleFlashcard(this)">
            <div class="magic-inner">
              <div class="magic-face magic-front">
                <div style="font-weight:700; color:var(--tunis-gold); font-size:1.1rem;">${card.name_en}</div>
                <div style="margin-top:12px; color:var(--text-muted); font-size:0.85rem;">Tap to reveal ajnas</div>
              </div>
              <div class="magic-face magic-back">
                <div style="font-weight:700; color:var(--tunis-teal); margin-bottom:8px; text-transform:capitalize;">${backLabel}</div>
                <div style="text-align:left; width:100%;">
                  <div style="margin-bottom:8px; padding:8px; background:rgba(13,118,194,0.1); border-radius:6px;">
                    <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px;">1st Jins</div>
                    <div style="font-size:0.95rem; font-weight:600; color:var(--text-main);">${first_en || '—'}</div>
                  </div>
                  ${second_en ? `
                  <div style="padding:8px; background:rgba(251,191,36,0.1); border-radius:6px;">
                    <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px;">2nd Jins</div>
                    <div style="font-size:0.95rem; font-weight:600; color:var(--text-main);">${second_en}</div>
                  </div>
                  ` : ''}
                </div>
              </div>
            </div>
          </div>
        `;
      } else {
        backEn = (card.regions_en || []).join(', ');
      }

      return `
        <div class="magic-card fc-small" data-idx="${idx}" onclick="toggleFlashcard(this)">
          <div class="magic-inner">
            <div class="magic-face magic-front">
              <div style="font-weight:700; color:var(--tunis-gold); font-size:1.1rem;">${card.name_en}</div>
              <div style="margin-top:12px; color:var(--text-muted); font-size:0.85rem;">Tap to reveal</div>
            </div>
            <div class="magic-face magic-back">
              <div style="font-weight:700; color:var(--tunis-teal); margin-bottom:6px; text-transform:capitalize;">${backLabel}</div>
              <div style="font-size:0.95rem; margin-bottom:6px;">${backEn || '—'}</div>
            </div>
          </div>
        </div>
      `;
    }

    function toggleFlashcard(el) {
      el.classList.toggle('flipped');
    }

    function flashcardShuffle() {
      if (!flashcardsState.cards.length) return;
      flashcardsState.cards = flashcardsState.cards.sort(() => Math.random() - 0.5);
      const container = document.getElementById('fc-deck-container');
      container.innerHTML = `
        <div class="fc-grid-large">
          ${flashcardsState.cards.map((card, idx) => flashcardCardHTML(card, flashcardsState.topic, idx)).join('')}
        </div>
      `;
    }

    let examTimer = null;
    let examTimeLeft = 0;
    
    function startExamTimer(seconds) {
      examTimeLeft = seconds;
      updateTimerDisplay();
      examTimer = setInterval(() => {
        examTimeLeft--;
        updateTimerDisplay();
        if (examTimeLeft <= 0) {
          clearInterval(examTimer);
          notify('Time is up! Auto-submitting...', 'error');
          submitQuiz();
        }
      }, 1000);
    }
    
    function updateTimerDisplay() {
      const display = document.getElementById('exam-timer');
      if (!display) return;
      const mins = Math.floor(examTimeLeft / 60);
      const secs = examTimeLeft % 60;
      display.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
      if (examTimeLeft <= 60) {
        display.style.color = 'var(--tunis-rose)';
      }
    }

    async function startQuiz() {
      if (examTimer) clearInterval(examTimer);
      const container = document.getElementById('quiz-container');
      container.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text-muted);">Loading Exam...</div>';
      try {
        const d = await api('/learning/quiz/start', 'POST', { lang: 'en' });
        currentQuiz = d;
        container.innerHTML = `
          <div style="background:var(--glass-surface); padding:28px; border-radius:16px; border:1px solid var(--glass-border); max-width:800px; margin:0 auto;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; padding-bottom:16px; border-bottom:2px solid var(--glass-border);">
                <div>
                  <span style="color:var(--tunis-rose); font-weight:bold; font-size:0.85rem; text-transform:uppercase; letter-spacing:1px;">Mastery Exam</span>
                  <div style="font-size:0.9rem; color:var(--text-muted); margin-top:4px;">${d.questions.length} Questions</div>
                </div>
                <div style="text-align:right;">
                  <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Time Remaining</div>
                  <div id="exam-timer" style="font-size:1.4rem; font-weight:bold; color:var(--tunis-teal);">20:00</div>
                </div>
            </div>
            
            <div style="display:flex; flex-direction:column; gap:24px;">
              ${d.questions.map((q, i) => q.type === 'mcq' ? `
                <div class="quiz-question" style="background:rgba(255,255,255,0.5); padding:20px; border-radius:12px; border:1px solid var(--glass-border);">
                   <div style="display:flex; gap:12px; align-items:flex-start; margin-bottom:12px;">
                     <span style="background:var(--tunis-teal); color:white; font-weight:bold; font-size:0.85rem; padding:4px 10px; border-radius:6px; flex-shrink:0;">Q${i+1}</span>
                     <span style="color:var(--text-main); font-weight:500;">${q.prompt}</span>
                   </div>
                   <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-left:42px;">
                     ${q.choices.map(c => `
                        <label style="display:flex; align-items:center; gap:8px; padding:10px 14px; background:rgba(255,255,255,0.8); border:1px solid var(--glass-border); border-radius:8px; cursor:pointer; transition:all 0.2s;" onmouseover="this.style.borderColor='var(--tunis-teal)'" onmouseout="this.style.borderColor='var(--glass-border)'">
                          <input type="radio" name="q-${q.index}" value="${c}" style="margin:0;"> 
                          <span>${c}</span>
                        </label>
                     `).join('')}
                   </div>
                </div>
              ` : `
                <div class="quiz-question" style="background:rgba(255,255,255,0.5); padding:20px; border-radius:12px; border:1px solid var(--glass-border);">
                   <div style="display:flex; gap:12px; align-items:flex-start; margin-bottom:12px;">
                     <span style="background:var(--tunis-gold); color:white; font-weight:bold; font-size:0.85rem; padding:4px 10px; border-radius:6px; flex-shrink:0;">Q${i+1}</span>
                     <span style="color:var(--text-main); font-weight:500;">${q.prompt}</span>
                   </div>
                   <div style="margin-left:42px;">
                     <input class="quiz-input" data-idx="${q.index}" placeholder="Type your answer..." style="width:100%; max-width:400px;" />
                   </div>
                </div>
              `).join('')}
            </div>
            
            <div style="margin-top:32px; padding-top:20px; border-top:2px solid var(--glass-border); text-align:center;">
              <button class="btn-action" id="quiz-submit" style="background:var(--tunis-rose); color:white; padding:16px 48px; font-size:1rem;" onclick="submitQuiz()">Submit Exam</button>
            </div>
          </div>
        `;
        // Start 20-minute timer
        startExamTimer(20 * 60);
      } catch(e) { 
        container.innerHTML = `<div style="text-align:center; padding:40px; color:var(--tunis-rose);">Error: ${e.message}</div>`;
        notify(e.message, 'error'); 
      }
    }

    async function submitQuiz() {
       if (examTimer) clearInterval(examTimer);
       if(!currentQuiz) return;
       const answers = [];
       const btn = document.getElementById('quiz-submit');
       setLoading(btn, true, 'Submitting...');
       currentQuiz.questions.forEach(q => {
          if (q.type === 'mcq') {
             const sel = document.querySelector(`input[name="q-${q.index}"]:checked`);
             answers[q.index] = sel ? sel.value : null;
          } else {
             const inp = document.querySelector(`.quiz-input[data-idx="${q.index}"]`);
             answers[q.index] = inp ? inp.value : null;
          }
       });
       try {
         const d = await api(`/learning/quiz/${currentQuiz.quiz_id}/answer`, 'POST', { answers });
         const container = document.getElementById('quiz-container');
         const score = Math.round(d.score * 100);
         const isPassing = score >= 70;
         const isGood = score >= 50;
         
         container.innerHTML = `
            <div style="max-width:800px; margin:0 auto;">
              <div style="text-align:center; padding:40px; background:var(--glass-surface); border-radius:16px; border:1px solid var(--glass-border); margin-bottom:24px;">
                  <h2 style="font-size:4rem; color:${isPassing ? 'var(--tunis-teal)' : isGood ? 'var(--tunis-gold)' : 'var(--tunis-rose)'}; margin:0;">${score}%</h2>
                  <p style="color:var(--text-muted); margin:12px 0 0; font-size:1.1rem;">
                    ${isPassing ? 'Excellent work!' : isGood ? 'Good effort! Keep practicing.' : 'Keep studying.'}
                  </p>
                  <div style="margin-top:20px; display:flex; justify-content:center; gap:12px;">
                    <span class="tag ${isPassing ? 'blue' : 'rose'}">${d.correct}/${d.total} Correct</span>
                  </div>
              </div>
              
              <div style="background:var(--glass-surface); border-radius:16px; border:1px solid var(--glass-border); overflow:hidden;">
                <div style="padding:16px 20px; background:rgba(13,118,194,0.08); border-bottom:1px solid var(--glass-border);">
                  <h3 style="margin:0; color:var(--text-main);">Question Review</h3>
                </div>
                <div style="max-height:400px; overflow-y:auto;">
                    ${d.details.map((det, idx) => `
                        <div style="padding:16px 20px; border-bottom:1px solid var(--glass-border); display:flex; gap:16px; align-items:flex-start;">
                            <div style="flex-shrink:0; width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:0.85rem; ${det.is_correct ? 'background:rgba(13,118,194,0.15); color:var(--tunis-teal);' : 'background:rgba(244,63,94,0.15); color:var(--tunis-rose);'}">
                              ${det.is_correct ? '✓' : '✗'}
                            </div>
                            <div style="flex:1;">
                              <div style="font-weight:500; color:var(--text-main); margin-bottom:6px;">Q${idx+1}: ${det.question}</div>
                              <div style="font-size:0.9rem; color:var(--text-muted);">
                                ${det.user_answer ? `Your answer: <span style="color:${det.is_correct ? 'var(--tunis-teal)' : 'var(--tunis-rose)'}">${det.user_answer}</span>` : '<span style="color:var(--tunis-rose)">No answer</span>'}
                              </div>
                              ${!det.is_correct ? `<div style="font-size:0.9rem; color:var(--tunis-teal); margin-top:4px;">Correct: ${det.correct_answer}</div>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
              </div>
              
              <div style="text-align:center; margin-top:24px;">
                <button class="btn-action" style="width:auto; padding:14px 32px;" onclick="startQuiz()">Retake Exam</button>
              </div>
            </div>
         `;
         } catch(e) { notify(e.message, 'error'); }
         finally { setLoading(btn, false, 'Submit Exam'); }
    }

    // Mini-Game Implementations
    async function runMCQ() {
        try {
            // Randomly pick a topic each time for variety
            const topics = ['emotion', 'region', 'usage'];
            const topicLabels = { emotion: 'Emotion', region: 'Region', usage: 'Usage' };
                        // Add special MCQ(s) about Al Ardhaoui seasonal usage
                        const ardhaouiQuestions = [
                          {
                            question: "What is the seasonal usage of Al Ardhaoui?",
                            choices: [
                              "Weddings in spring and summer",
                              "Ramadan evenings",
                              "No specific seasonal usage",
                              "Love poetry evenings"
                            ].sort(() => Math.random() - 0.5),
                            answer: "Weddings in spring and summer"
                          }
                        ];
                        // ...existing code...
            const selectedTopic = topics[Math.floor(Math.random() * topics.length)];
            
            const d = await api('/learning/quiz/mcq/start', 'POST', {topic: selectedTopic});
            // Merge MCQs from API and add Ardhaoui questions at the end
            let questions = (d.questions && d.questions.length) ? d.questions : [];
            questions = questions.concat(ardhaouiQuestions);
            if(questions.length) {
                let idx = 0;
                let correctCount = 0;
                const totalQuestions = questions.length;
                
                let feedback = '';
                window.checkMCQ = (ans) => {
                    const q = questions[idx];
                    const correct = ans === q.answer;
                    let resultMsg = '';
                    if(correct) {
                      resultMsg = '<span style="color:var(--tunis-teal); font-weight:bold;">✓ Correct!</span>';
                      correctCount++;
                      if (q.maqam_id) {
                        gameState.mcq.completed.add(q.maqam_id);
                        completeActivity(q.maqam_id, `mcq_${selectedTopic}`);
                      }
                    } else {
                      resultMsg = `<span style=\"color:var(--tunis-rose)\">✗ Wrong!<br>Correct: <strong>${q.answer}</strong></span>`;
                    }
                    feedback = resultMsg;
                    // Show feedback, then move to next
                    render(true);
                    setTimeout(() => {
                      feedback = '';
                      idx++;
                      if(idx < questions.length) {
                        render();
                      } else {
                        showGameComplete('mcq', correctCount, totalQuestions);
                      }
                    }, 1200);
                };
                window.skipMCQ = () => {
                    idx++;
                    feedback = '';
                    if(idx < questions.length) {
                        render();
                    } else {
                        showGameComplete('mcq', correctCount, totalQuestions);
                    }
                };
                const render = (showFeedback=false) => {
                    const q = questions[idx];
                    const progress = Math.round((idx / totalQuestions) * 100);
                    openModal(`
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                          <div>
                            <h3 style="margin:0; color:var(--tunis-gold)">Speed MCQ</h3>
                            <span style="font-size:0.8rem; color:var(--text-muted);">Topic: ${topicLabels[selectedTopic] || ''}</span>
                          </div>
                          <span class="tag blue">Q${idx + 1}/${totalQuestions}</span>
                        </div>
                        <div style="height:4px; background:var(--glass-border); border-radius:2px; margin-bottom:16px;">
                          <div style="height:100%; width:${progress}%; background:var(--tunis-teal); border-radius:2px; transition:width 0.3s;"></div>
                        </div>
                        <p style="font-size:1.1rem; margin-bottom:16px;">${q.question}</p>
                        <div style="display:flex; flex-direction:column; gap:8px;">
                            ${q.choices.map(c=>`<button class=\"btn-ghost\" onclick=\"checkMCQ('${c.replace(/'/g,"&#39;")}')\" style=\"text-align:left; padding:12px;\">${c}</button>`).join('')}
                        </div>
                        <div id="mcq-feedback" style="margin-top:12px; min-height:24px;">${showFeedback ? feedback : ''}</div>
                        <div style="margin-top:12px; text-align:right;">
                          <button class="btn-ghost" onclick="skipMCQ()" style="width:auto; padding:8px 16px;">Skip →</button>
                        </div>
                    `);
                };
                render();
            } else {
                notify('No MCQ available', 'error');
            }
        } catch(e) { notify(e.message, 'error'); }
    }

    // Matching game: user selects left then right, build pairs, then check
    // Pastel color palette for matching pairs
    const PASTEL_COLORS = [
      { bg: '#FFE4E6', border: '#FDA4AF', text: '#9F1239' },  // Rose
      { bg: '#E0F2FE', border: '#7DD3FC', text: '#0369A1' },  // Sky
      { bg: '#FEF3C7', border: '#FCD34D', text: '#92400E' },  // Amber
      { bg: '#D1FAE5', border: '#6EE7B7', text: '#065F46' },  // Emerald
      { bg: '#EDE9FE', border: '#C4B5FD', text: '#5B21B6' },  // Violet
      { bg: '#FCE7F3', border: '#F9A8D4', text: '#9D174D' },  // Pink
      { bg: '#CFFAFE', border: '#67E8F9', text: '#0E7490' },  // Cyan
      { bg: '#FEE2E2', border: '#FCA5A5', text: '#B91C1C' },  // Red
    ];
    
    async function runMatching() {
      try {
        const d = await api('/learning/matching?topic=emotion');
        const pairs = d.solution || [];
        const right = d.right || [];
        const left = d.left || [];
        const state = { leftSel: null, rightSel: null, chosen: [], colorMap: new Map() };
        let colorIdx = 0;

        const html = `
          <div style="text-align:center; margin-bottom:20px;">
            <h2 style="margin:0; color:var(--tunis-gold); font-size:1.8rem;">Match the Pairs</h2>
            <p style="margin:8px 0 0; color:var(--text-muted);">Connect each maqam with its emotion</p>
          </div>

          <div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-bottom:20px;">
            <div>
              <div style="text-align:center; font-weight:bold; color:var(--tunis-teal); margin-bottom:12px; font-size:0.9rem; text-transform:uppercase; letter-spacing:1px;">Maqamat</div>
              <div id="match-left" style="display:flex; flex-direction:column; gap:10px;"></div>
            </div>
            <div>
              <div style="text-align:center; font-weight:bold; color:var(--tunis-gold); margin-bottom:12px; font-size:0.9rem; text-transform:uppercase; letter-spacing:1px;">Emotions</div>
              <div id="match-right" style="display:flex; flex-direction:column; gap:10px;"></div>
            </div>
          </div>

          <div style="background:rgba(255,255,255,0.95); padding:16px; border-radius:12px; border:1px solid var(--glass-border);">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;">
              <div style="font-size:0.9rem; color:var(--text-muted);">
                <span id="match-count">0</span>/${left.length} pairs matched
              </div>
              <div style="display:flex; gap:8px; flex-wrap:wrap;">
                <button class="btn-ghost" id="match-add" style="width:auto;">➕ Add Pair</button>
                <button class="btn-action" id="match-check" style="width:auto; padding:10px 18px;">✓ Check All</button>
                <button class="btn-ghost" id="match-reset" style="width:auto;">↺ Reset</button>
              </div>
            </div>
            <div id="match-result" style="margin-top:10px; min-height:24px;"></div>
          </div>
        `;
        openModal(html);

        const leftBox = document.getElementById('match-left');
        const rightBox = document.getElementById('match-right');

        function getNextColor() {
          const color = PASTEL_COLORS[colorIdx % PASTEL_COLORS.length];
          colorIdx++;
          return color;
        }

        function renderLists() {
          // Render left (maqamat)
          leftBox.innerHTML = left.map(l => {
            const paired = state.chosen.find(p => p.l === l.id);
            const isSelected = state.leftSel === l.id;
            const color = paired ? state.colorMap.get(l.id) : null;
            
            let style = `
              padding: 14px 18px;
              border-radius: 10px;
              cursor: ${paired ? 'default' : 'pointer'};
              transition: all 0.2s;
              font-weight: 500;
              text-align: center;
            `;
            
            if (paired && color) {
              style += `background: ${color.bg}; border: 2px solid ${color.border}; color: ${color.text};`;
            } else if (isSelected) {
              style += `background: var(--tunis-teal); color: white; border: 2px solid var(--tunis-teal);`;
            } else {
              style += `background: rgba(255,255,255,0.9); border: 2px solid var(--glass-border); color: var(--text-main);`;
            }
            
            return `<button class="match-item" data-left="${l.id}" style="${style}" ${paired ? 'disabled' : ''}>${l.name}${paired ? ' ✓' : ''}</button>`;
          }).join('');
          
          // Render right (emotions)
          rightBox.innerHTML = right.map((r, i) => {
            // Check if this emotion is already paired
            const pairedEntry = state.chosen.find(p => p.r === i);
            const isSelected = state.rightSel === i;
            const color = pairedEntry ? state.colorMap.get(pairedEntry.l) : null;
            
            let style = `
              padding: 14px 18px;
              border-radius: 10px;
              cursor: ${pairedEntry ? 'default' : 'pointer'};
              transition: all 0.2s;
              font-weight: 500;
              text-align: center;
            `;
            
            if (pairedEntry && color) {
              style += `background: ${color.bg}; border: 2px solid ${color.border}; color: ${color.text};`;
            } else if (isSelected) {
              style += `background: var(--tunis-gold); color: white; border: 2px solid var(--tunis-gold);`;
            } else {
              style += `background: rgba(255,255,255,0.9); border: 2px solid var(--glass-border); color: var(--text-main);`;
            }
            
            return `<button class="match-item" data-right="${i}" style="${style}" ${pairedEntry ? 'disabled' : ''}>${r}${pairedEntry ? ' ✓' : ''}</button>`;
          }).join('');
          
          // Update counter
          document.getElementById('match-count').textContent = state.chosen.length;
        }

        function wireButtons() {
          leftBox.querySelectorAll('[data-left]').forEach(btn => {
            if (!btn.disabled) {
              btn.onclick = () => {
                state.leftSel = parseInt(btn.dataset.left, 10);
                renderLists();
                wireButtons();
              };
            }
          });
          rightBox.querySelectorAll('[data-right]').forEach(btn => {
            if (!btn.disabled) {
              btn.onclick = () => {
                state.rightSel = parseInt(btn.dataset.right, 10);
                renderLists();
                wireButtons();
              };
            }
          });
        }

        document.getElementById('match-add').onclick = () => {
          if(state.leftSel == null || state.rightSel == null) return notify('Select one from each column','error');
          if(state.chosen.find(p => p.l === state.leftSel)) return notify('Maqam already paired','error');
          if(state.chosen.find(p => p.r === state.rightSel)) return notify('Emotion already paired','error');
          
          // Assign a color to this pair
          const color = getNextColor();
          state.colorMap.set(state.leftSel, color);
          
          state.chosen.push({l: state.leftSel, r: state.rightSel});
          state.leftSel = null; 
          state.rightSel = null;
          renderLists(); 
          wireButtons();
          notify('Pair added!');
        };
        
        document.getElementById('match-reset').onclick = () => {
          state.chosen = []; 
          state.leftSel = null; 
          state.rightSel = null;
          state.colorMap.clear();
          colorIdx = 0;
          renderLists(); 
          wireButtons();
          document.getElementById('match-result').innerText = '';
        };
        
        document.getElementById('match-check').onclick = () => {
          if (state.chosen.length < left.length) {
            return notify(`Match all ${left.length} pairs before checking`, 'error');
          }
          
          const solMap = new Map(pairs.map(p => [p.maqam_id, p.value]));
          let correct = 0;
          state.chosen.forEach(c => { 
            if (solMap.get(c.l) === right[c.r]) {
              correct++;
            }
          });
          
          state.chosen.forEach(c => completeActivity(c.l, 'matching_emotion'));
          
          // Show completion screen
          const percent = Math.round((correct / pairs.length) * 100);
          openModal(`
            <div style="text-align:center; padding:20px;">
              <h2 style="font-size:2.5rem; color:${percent >= 70 ? 'var(--tunis-teal)' : percent >= 50 ? 'var(--tunis-gold)' : 'var(--tunis-rose)'}; margin:0 0 8px;">${percent}%</h2>
              <p style="color:var(--text-muted); margin:0 0 20px;">Matching Complete! ${correct}/${pairs.length} correct</p>
              <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap;">
                <button class="btn-action" style="width:auto; padding:12px 24px;" onclick="closeModal()">Done</button>
                <button class="btn-ghost" style="width:auto;" onclick="runMatching()">Play Again</button>
              </div>
            </div>
          `);
        };

        renderLists();
        wireButtons();
      } catch(e) { notify(e.message, 'error'); }
    }

    // Audio recognition MCQ - loads all tracks and cycles through them
    let audioGameState = { tracks: [], idx: 0, correct: 0 };
    
    async function runAudioMCQ() {
      try {
        // Load all tracks on first call or if we've completed all
        if (audioGameState.tracks.length === 0 || audioGameState.idx >= audioGameState.tracks.length) {
          const d = await api('/learning/audio-recognition/all');
          if (d.error) return notify(d.error, 'error');
          audioGameState = { tracks: d.tracks || [], idx: 0, correct: 0 };
        }
        
        // Check if game is complete
        if (audioGameState.idx >= audioGameState.tracks.length) {
          showAudioComplete();
          return;
        }
        
        const track = audioGameState.tracks[audioGameState.idx];
        const total = audioGameState.tracks.length;
        const current = audioGameState.idx + 1;
        
        // Get 3 random wrong choices + correct one
        const otherTracks = audioGameState.tracks.filter(t => t.id !== track.id);
        const wrongChoices = otherTracks.sort(() => Math.random() - 0.5).slice(0, 3);
        const allChoices = [track, ...wrongChoices].sort(() => Math.random() - 0.5);
        
        openModal(`
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
            <h3 style="margin:0; color:var(--tunis-gold)">Ear Training</h3>
            <span class="tag blue">${current}/${total}</span>
          </div>
          <div style="height:6px; background:var(--glass-border); border-radius:3px; margin-bottom:16px;">
            <div style="height:100%; width:${(current/total)*100}%; background:linear-gradient(90deg, var(--tunis-teal), var(--tunis-gold)); border-radius:3px; transition:width 0.3s;"></div>
          </div>
          <audio controls src="${track.audio_url}" style="width:100%; margin-bottom:16px;"></audio>
          <p style="color:var(--text-muted); margin-bottom:12px;">Listen and identify the maqam:</p>
          <div id="audio-choices" style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;"></div>
          <div id="audio-result" style="margin-top:12px; min-height:24px;"></div>
          <div style="margin-top:12px; text-align:right;">
            <button class="btn-ghost" onclick="skipAudioMCQ()" style="width:auto; padding:8px 16px;">Skip →</button>
          </div>
        `);
        
        window.skipAudioMCQ = () => {
          audioGameState.idx++;
          if (audioGameState.idx >= audioGameState.tracks.length) {
            showAudioComplete();
          } else {
            runAudioMCQ();
          }
        };
        
        const box = document.getElementById('audio-choices');
        box.innerHTML = allChoices.map(c => `<button class="btn-ghost" data-audio-choice="${c.id}" style="padding:14px; text-align:center;">${c.name}</button>`).join('');
        
        box.querySelectorAll('[data-audio-choice]').forEach(btn => btn.onclick = () => {
          const resEl = document.getElementById('audio-result');
          const choiceId = parseInt(btn.dataset.audioChoice, 10);
          const isCorrect = choiceId === track.id;
          
          if (isCorrect) {
            audioGameState.correct++;
            resEl.innerHTML = '<span style="color:var(--tunis-teal); font-weight:bold;">✓ Correct!</span>';
            notify('Correct');
            completeActivity(track.id, 'audio_mcq');
          } else {
            resEl.innerHTML = `<span style="color:var(--tunis-rose)">✗ Wrong! It was <strong>${track.name}</strong></span>`;
            notify('Wrong', 'error');
          }
          
          // Disable all buttons
          box.querySelectorAll('button').forEach(b => { b.disabled = true; b.style.opacity = '0.6'; });
          
          // Highlight correct answer
          box.querySelectorAll('button').forEach(b => {
            if (parseInt(b.dataset.audioChoice) === track.id) {
              b.style.borderColor = 'var(--tunis-teal)';
              b.style.background = 'rgba(13,118,194,0.15)';
            }
          });
          
          // Auto advance after delay
          audioGameState.idx++;
          setTimeout(() => {
            if (audioGameState.idx >= audioGameState.tracks.length) {
              showAudioComplete();
            } else {
              runAudioMCQ();
            }
          }, 1500);
        });
      } catch(e) { notify(e.message, 'error'); }
    }
    
    function showAudioComplete() {
      const total = audioGameState.tracks.length;
      const correct = audioGameState.correct;
      const percent = total > 0 ? Math.round((correct / total) * 100) : 0;
      
      openModal(`
        <div style="text-align:center; padding:20px;">
          <h2 style="font-size:2.5rem; color:${percent >= 70 ? 'var(--tunis-teal)' : percent >= 50 ? 'var(--tunis-gold)' : 'var(--tunis-rose)'}; margin:0 0 8px;">${percent}%</h2>
          <p style="color:var(--text-muted); margin:0 0 20px;">Ear Training Complete - ${correct}/${total} correct</p>
          <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap;">
            <button class="btn-action" style="width:auto; padding:12px 24px;" onclick="closeModal()">Done</button>
            <button class="btn-ghost" style="width:auto;" onclick="audioGameState.tracks=[]; runAudioMCQ()">Play Again</button>
          </div>
        </div>
      `);
    }

    // Detective game - loads all puzzles and cycles through them
    let detectiveGameState = { puzzles: [], idx: 0, correct: 0 };
    
    async function runClueGame() {
      try {
        // Load all puzzles on first call or if we've completed all
        if (detectiveGameState.puzzles.length === 0 || detectiveGameState.idx >= detectiveGameState.puzzles.length) {
          const d = await api('/learning/clue-game/all');
          if (d.error) return notify(d.error, 'error');
          detectiveGameState = { puzzles: d.puzzles || [], idx: 0, correct: 0 };
        }
        
        // Check if game is complete
        if (detectiveGameState.idx >= detectiveGameState.puzzles.length) {
          showDetectiveComplete();
          return;
        }
        
        const puzzle = detectiveGameState.puzzles[detectiveGameState.idx];
        const answer = (puzzle.answer || '').trim().toLowerCase();
        const total = detectiveGameState.puzzles.length;
        const current = detectiveGameState.idx + 1;
        
        openModal(`
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
            <h3 style="margin:0; color:var(--tunis-gold)">Detective</h3>
            <span class="tag blue">${current}/${total}</span>
          </div>
          <div style="height:6px; background:var(--glass-border); border-radius:3px; margin-bottom:16px;">
            <div style="height:100%; width:${(current/total)*100}%; background:linear-gradient(90deg, var(--tunis-teal), var(--tunis-gold)); border-radius:3px; transition:width 0.3s;"></div>
          </div>
          <p style="color:var(--text-muted); margin-bottom:12px;">Use the clues to identify the maqam:</p>
          <div style="background:rgba(13,118,194,0.08); padding:16px; border-radius:12px; margin-bottom:16px;">
            <ul style="margin:0; padding-left:20px;">${(puzzle.clues || []).map(c => `<li style="margin-bottom:8px;">${c}</li>`).join('')}</ul>
          </div>
          <input id="detective-guess" placeholder="Type your guess..." style="font-size:1.1rem;" />
          <div style="display:flex; gap:8px; margin-top:12px; flex-wrap:wrap;">
            <button class="btn-action" style="flex:1;" id="detective-check">Check</button>
            <button class="btn-ghost" style="width:auto;" id="detective-reveal">Reveal & Skip</button>
          </div>
          <div id="detective-result" style="margin-top:12px; min-height:24px;"></div>
        `);
        
        const input = document.getElementById('detective-guess');
        input.focus();
        
        const checkAnswer = () => {
          const guess = (input.value || '').trim().toLowerCase();
          const el = document.getElementById('detective-result');
          if (!guess) return notify('Enter a guess', 'error');
          
          if (guess === answer) {
            detectiveGameState.correct++;
            el.innerHTML = '<span style="color:var(--tunis-teal); font-weight:bold;">✓ Correct!</span>';
            notify('Correct');
            completeActivity(puzzle.maqam_id, 'clue_game');
            advanceDetective();
          } else {
            el.innerHTML = '<span style="color:var(--tunis-rose)">✗ Try again or reveal</span>';
            notify('Wrong', 'error');
          }
        };
        
        const revealAndSkip = () => {
          const el = document.getElementById('detective-result');
          el.innerHTML = `<span style="color:var(--tunis-gold)">Answer: <strong>${puzzle.answer}</strong></span>`;
          advanceDetective();
        };
        
        const advanceDetective = () => {
          document.getElementById('detective-check').disabled = true;
          document.getElementById('detective-reveal').disabled = true;
          input.disabled = true;
          detectiveGameState.idx++;
          setTimeout(() => {
            if (detectiveGameState.idx >= detectiveGameState.puzzles.length) {
              showDetectiveComplete();
            } else {
              runClueGame();
            }
          }, 1500);
        };
        
        document.getElementById('detective-check').onclick = checkAnswer;
        document.getElementById('detective-reveal').onclick = revealAndSkip;
        input.addEventListener('keydown', (e) => { if (e.key === 'Enter') checkAnswer(); });
        
      } catch(e) { notify(e.message, 'error'); }
    }
    
    function showDetectiveComplete() {
      const total = detectiveGameState.puzzles.length;
      const correct = detectiveGameState.correct;
      const percent = total > 0 ? Math.round((correct / total) * 100) : 0;
      
      openModal(`
        <div style="text-align:center; padding:20px;">
          <h2 style="font-size:2.5rem; color:${percent >= 70 ? 'var(--tunis-teal)' : percent >= 50 ? 'var(--tunis-gold)' : 'var(--tunis-rose)'}; margin:0 0 8px;">${percent}%</h2>
          <p style="color:var(--text-muted); margin:0 0 20px;">Detective Game Complete - ${correct}/${total} solved</p>
          <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap;">
            <button class="btn-action" style="width:auto; padding:12px 24px;" onclick="closeModal()">Done</button>
            <button class="btn-ghost" style="width:auto;" onclick="detectiveGameState.puzzles=[]; runClueGame()">Play Again</button>
          </div>
        </div>
      `);
    }

    // Sequencer game - loads all puzzles and cycles through them
    let sequencerGameState = { puzzles: [], idx: 0, correct: 0 };
    
    async function runOrderNotes() {
      try {
        // Load all puzzles on first call or if we've completed all
        if (sequencerGameState.puzzles.length === 0 || sequencerGameState.idx >= sequencerGameState.puzzles.length) {
          const d = await api('/learning/order-notes/all');
          if (d.error) return notify(d.error, 'error');
          sequencerGameState = { puzzles: d.puzzles || [], idx: 0, correct: 0 };
        }
        
        // Check if game is complete
        if (sequencerGameState.idx >= sequencerGameState.puzzles.length) {
          showSequencerComplete();
          return;
        }
        
        const puzzle = sequencerGameState.puzzles[sequencerGameState.idx];
        const total = sequencerGameState.puzzles.length;
        const current = sequencerGameState.idx + 1;
        
        // Shuffle the notes for the puzzle
        const shuffled = [...(puzzle.notes || [])].sort(() => Math.random() - 0.5);
        const state = { order: shuffled };
        
        openModal(`
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
            <h3 style="margin:0; color:var(--tunis-gold)">Sequencer: ${puzzle.name}</h3>
            <span class="tag blue">${current}/${total}</span>
          </div>
          <div style="height:6px; background:var(--glass-border); border-radius:3px; margin-bottom:16px;">
            <div style="height:100%; width:${(current/total)*100}%; background:linear-gradient(90deg, var(--tunis-teal), var(--tunis-gold)); border-radius:3px; transition:width 0.3s;"></div>
          </div>
          <p style="color:var(--text-muted); margin-bottom:16px;">Drag notes to arrange them in the correct order:</p>
          <div id="dropzone" class="dropzone" style="min-height:80px; background:rgba(13,118,194,0.06);"></div>
          <div style="display:flex; gap:8px; margin-top:16px; flex-wrap:wrap;">
            <button class="btn-action" style="flex:1;" id="seq-submit">Check Order</button>
            <button class="btn-ghost" style="width:auto;" id="seq-skip">Skip</button>
          </div>
          <div id="seq-result" style="margin-top:12px; min-height:24px;"></div>
        `);
        
        const dz = document.getElementById('dropzone');
        
        function renderChips() {
          dz.innerHTML = state.order.map((n, i) => `<span class="chip" draggable="true" data-idx="${i}" style="cursor:grab; user-select:none;">${n}</span>`).join('');
          dz.querySelectorAll('.chip').forEach(chip => {
            chip.addEventListener('dragstart', e => {
              e.dataTransfer.effectAllowed = 'move';
              e.dataTransfer.setData('text/plain', chip.dataset.idx);
              chip.style.opacity = '0.5';
            });
            chip.addEventListener('dragend', e => {
              chip.style.opacity = '1';
            });
          });
        }
        
        dz.addEventListener('dragover', e => { e.preventDefault(); });
        dz.addEventListener('drop', e => {
          e.preventDefault();
          const from = parseInt(e.dataTransfer.getData('text/plain'), 10);
          const targetChip = e.target.closest('.chip');
          const to = targetChip ? parseInt(targetChip.dataset.idx, 10) : state.order.length - 1;
          const moved = state.order.splice(from, 1)[0];
          state.order.splice(to, 0, moved);
          renderChips();
        });
        
        const advanceSequencer = () => {
          document.getElementById('seq-submit').disabled = true;
          document.getElementById('seq-skip').disabled = true;
          sequencerGameState.idx++;
          setTimeout(() => {
            if (sequencerGameState.idx >= sequencerGameState.puzzles.length) {
              showSequencerComplete();
            } else {
              runOrderNotes();
            }
          }, 1500);
        };
        
        document.getElementById('seq-submit').onclick = () => {
          const correct = (puzzle.solution || []).join(',');
          const curr = state.order.join(',');
          const el = document.getElementById('seq-result');
          
          if (correct === curr) {
            sequencerGameState.correct++;
            el.innerHTML = '<span style="color:var(--tunis-teal); font-weight:bold;">✓ Correct order!</span>';
            notify('Great job');
            completeActivity(puzzle.maqam_id, 'order_notes');
            advanceSequencer();
          } else {
            el.innerHTML = '<span style="color:var(--tunis-rose)">✗ Not quite right. Keep trying or skip!</span>';
            notify('Try again', 'error');
          }
        };
        
        document.getElementById('seq-skip').onclick = () => {
          const el = document.getElementById('seq-result');
          el.innerHTML = `<span style="color:var(--tunis-gold)">Correct order: ${puzzle.solution.join(' → ')}</span>`;
          advanceSequencer();
        };
        
        renderChips();
      } catch(e) { notify(e.message, 'error'); }
    }
    
    function showSequencerComplete() {
      const total = sequencerGameState.puzzles.length;
      const correct = sequencerGameState.correct;
      const percent = total > 0 ? Math.round((correct / total) * 100) : 0;
      
      openModal(`
        <div style="text-align:center; padding:20px;">
          <h2 style="font-size:2.5rem; color:${percent >= 70 ? 'var(--tunis-teal)' : percent >= 50 ? 'var(--tunis-gold)' : 'var(--tunis-rose)'}; margin:0 0 8px;">${percent}%</h2>
          <p style="color:var(--text-muted); margin:0 0 20px;">Sequencer Complete - ${correct}/${total} correct</p>
          <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap;">
            <button class="btn-action" style="width:auto; padding:12px 24px;" onclick="closeModal()">Done</button>
            <button class="btn-ghost" style="width:auto;" onclick="sequencerGameState.puzzles=[]; runOrderNotes()">Play Again</button>
          </div>
        </div>
      `);
    }

    // Leaderboard
    async function showLeaderboard() { 
        try {
            const d = await api('/learning/leaderboard');
            const rows = (d.leaderboard||[]).map(u => `
              <div class="glass-card" style="padding:12px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between;">
                  <strong>${u.user_id}</strong>
                  <span class="tag blue">${Math.round((u.best_score||0)*100)}% best</span>
                </div>
                <div style="color:var(--text-muted); font-size:0.9rem;">Quizzes: ${u.quizzes} | Activities: ${u.activities}</div>
              </div>
            `).join('');
            openModal(`
              <h3 style="color:var(--tunis-gold)">Leaderboard</h3>
              <p style="color:var(--text-muted); font-size:0.95rem; margin-top:6px;">Ranks users by their best combined score across quizzes and activities. Data is fetched live from /learning/leaderboard.</p>
              ${rows || '<p style="color:var(--text-muted);">No leaderboard data yet.</p>'}
            `); 
        } catch(e) { notify(e.message, 'error'); }
    }

    async function showRecentActivity() {
        try {
            const d = await api('/learning/activity-log');
            const items = (d.activities || []).map(a => `
              <div class="glass-card" style="padding:12px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <div><strong>Activity:</strong> ${a.activity}</div>
                  <span class="tag blue">#${a.maqam_id}</span>
                </div>
                <div style="color:var(--text-muted); font-size:0.85rem; margin-top:4px;">${a.created_at}</div>
              </div>
            `).join('');
            openModal(`
              <h3 style="color:var(--tunis-gold)">Recent Activity</h3>
              <p style="color:var(--text-muted); font-size:0.95rem; margin-top:6px;">Showing your latest logged completions (limit 50).</p>
              ${items || '<div style="color:var(--text-muted);"><p>No activity yet. Play a game to log your first completion.</p><button class="btn-action" style="width:auto; padding:10px 16px; margin-top:8px;" onclick="runMatching()">Play Matching Now</button></div>'}
            `);
        } catch(e) { notify(e.message, 'error'); }
    }

    // Ear training single target (kept for compatibility)
    async function runAudioRec() {
        try {
            const d = await api('/learning/audio-recognition');
            if(d.error) return notify(d.error, 'error');
            openModal(`
                <h3 style="margin-top:0; color:var(--tunis-gold)">Ear Training</h3>
                <audio controls src="${d.audio_url}" style="width:100%; margin:12px 0;"></audio>
                <div style="display:flex; flex-direction:column; gap:10px;">
                    ${d.choices.map(c => `<button class="btn-ghost" onclick="alertAudioRec(${c.id}, ${d.answer_id})">${c.name}</button>`).join('')}
                </div>
            `);
        } catch(e) { notify(e.message, 'error'); }
    }
    function alertAudioRec(choiceId, answerId) {
      if (choiceId === answerId) { notify('Correct!'); completeActivity(answerId, 'audio_recognition'); }
      else notify('Try again', 'error');
    }

    // MCQ start alias (kept)
    async function runMCQAlias() { return runMCQ(); }

    (async () => {
      await fetchDemoToken();
      checkAuth();
      refreshStats();
      searchMaqam();
      initGameState();
    })();

    function setLoading(btn, isLoading, label) {
      if (!btn) return;
      btn.disabled = !!isLoading;
      if (label) btn.innerText = label;
      btn.style.opacity = isLoading ? '0.7' : '1';
      btn.style.cursor = isLoading ? 'not-allowed' : 'pointer';
    }
