(function () {
  "use strict";

  /* ══ PARTICLES ══ */
  function initParticles() {
    if (document.getElementById('particle-canvas')) return;
    var c = document.createElement('canvas');
    c.id = 'particle-canvas';
    c.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;opacity:0.35;';
    document.body.appendChild(c);
    var ctx = c.getContext('2d'), W, H, pts = [];
    function resize() { W = c.width = window.innerWidth; H = c.height = window.innerHeight; }
    resize(); window.addEventListener('resize', resize);
    var N = Math.min(50, Math.floor(window.innerWidth * window.innerHeight / 18000));
    for (var i = 0; i < N; i++) pts.push({ x: Math.random() * W, y: Math.random() * H, vx: (Math.random() - .5) * .28, vy: (Math.random() - .5) * .28, r: Math.random() * 1.4 + .5, phase: Math.random() * Math.PI * 2 });
    var t = 0;
    function frame() {
      t += .007; ctx.clearRect(0, 0, W, H);
      for (var i = 0; i < pts.length; i++) {
        var p = pts[i]; p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > W) p.vx *= -1; if (p.y < 0 || p.y > H) p.vy *= -1;
        var al = .18 + .12 * Math.sin(t + p.phase);
        for (var j = i + 1; j < pts.length; j++) {
          var q = pts[j], dx = p.x - q.x, dy = p.y - q.y, d = Math.sqrt(dx * dx + dy * dy);
          if (d < 120) { ctx.beginPath(); ctx.strokeStyle = 'rgba(0,229,160,' + (0.15 * (1 - d / 120)) + ')'; ctx.lineWidth = .6; ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke(); }
        }
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fillStyle = 'rgba(0,229,160,' + (al + .08) + ')'; ctx.fill();
      }
      requestAnimationFrame(frame);
    }
    frame();
  }

  /* ══ GLOW / TILT ══ */
  function initGlowCards() {
    document.querySelectorAll('.glow-card,.match-card,.stat-pill').forEach(function (el) {
      if (el._gi) return; el._gi = true;
      el.addEventListener('mousemove', function (e) {
        var r = el.getBoundingClientRect();
        el.style.setProperty('--mx', ((e.clientX - r.left) / r.width * 100) + '%');
        el.style.setProperty('--my', ((e.clientY - r.top) / r.height * 100) + '%');
      });
    });
  }
  function initTilt() {
    document.querySelectorAll('.match-card,.tilt-card').forEach(function (el) {
      if (el._ti) return; el._ti = true;
      el.addEventListener('mousemove', function (e) {
        var r = el.getBoundingClientRect(), dx = (e.clientX - r.left) / r.width - .5, dy = (e.clientY - r.top) / r.height - .5;
        el.style.transform = 'perspective(500px) rotateX(' + (dy * -5) + 'deg) rotateY(' + (dx * 5) + 'deg) translateY(-2px)';
      });
      el.addEventListener('mouseleave', function () { el.style.transform = ''; });
    });
  }

  /* ══ COUNTUP ══ */
  function initCountUp() {
    document.querySelectorAll('.countup-num:not([data-done])').forEach(function (el) {
      var target = parseFloat(el.getAttribute('data-target'));
      if (isNaN(target)) return;
      el.setAttribute('data-done', '1');
      var dur = 1100, t0 = null, isF = String(target).indexOf('.') >= 0;
      function step(ts) { if (!t0) t0 = ts; var p = Math.min((ts - t0) / dur, 1), e = 1 - Math.pow(1 - p, 3), v = target * e; el.textContent = isF ? v.toFixed(2) : Math.round(v); if (p < 1) requestAnimationFrame(step); }
      requestAnimationFrame(step);
    });
  }

  /* ══ SPOTLIGHT ══ */
  function initSpotlight() {
    if (document.getElementById('cursor-spotlight')) return;
    var s = document.createElement('div');
    s.id = 'cursor-spotlight';
    s.style.cssText = 'position:fixed;pointer-events:none;width:350px;height:350px;border-radius:50%;z-index:0;opacity:0;transition:opacity 0.3s;background:radial-gradient(circle,rgba(0,229,160,0.04) 0%,transparent 70%);transform:translate(-50%,-50%)';
    document.body.appendChild(s);
    document.addEventListener('mousemove', function (e) { s.style.left = e.clientX + 'px'; s.style.top = e.clientY + 'px'; s.style.opacity = '1'; });
  }


  /* ══════════════════════════════════════════════════════
   SIDEBAR — 3-breakpoint logic
   Desktop  >1200px : starts expanded, toggle collapses
   Tablet  768-1200px : starts as icon rail, toggle expands
   Mobile   <768px  : always hidden, hamburger opens drawer
   State saved in localStorage key 'sb-state'
   ══════════════════════════════════════════════════════ */
  function getBreakpoint() {
    var w = window.innerWidth;
    if (w > 1200) return 'desktop';
    if (w > 768) return 'tablet';
    return 'mobile';
  }

  function applyDesktopState(collapsed) {
    var sb = document.getElementById('statdium-sidebar');
    var mc = document.getElementById('statdium-main-content');
    if (!sb) return;
    if (collapsed) {
      sb.classList.add('collapsed'); sb.classList.remove('expanded');
      if (mc) { mc.classList.add('collapsed'); mc.classList.remove('expanded'); }
    } else {
      sb.classList.remove('collapsed'); sb.classList.remove('expanded');
      if (mc) { mc.classList.remove('collapsed'); mc.classList.remove('expanded'); }
    }
  }

  function applyTabletState(expanded) {
    var sb = document.getElementById('statdium-sidebar');
    var mc = document.getElementById('statdium-main-content');
    if (!sb) return;
    if (expanded) {
      sb.classList.add('expanded'); sb.classList.remove('collapsed');
      if (mc) { mc.classList.add('expanded'); mc.classList.remove('collapsed'); }
    } else {
      sb.classList.remove('expanded'); sb.classList.remove('collapsed');
      if (mc) { mc.classList.remove('expanded'); mc.classList.remove('collapsed'); }
    }
  }

  function openMobileSidebar() {
    var sb = document.getElementById('statdium-sidebar');
    var ov = document.getElementById('sidebar-overlay');
    if (sb) sb.classList.add('mobile-open');
    if (ov) { ov.style.display = 'block'; requestAnimationFrame(function () { ov.classList.add('visible'); }); }
  }
  function closeMobileSidebar() {
    var sb = document.getElementById('statdium-sidebar');
    var ov = document.getElementById('sidebar-overlay');
    if (sb) sb.classList.remove('mobile-open');
    if (ov) { ov.classList.remove('visible'); setTimeout(function () { ov.style.display = 'none'; }, 280); }
  }

  function saveSidebarState(key, val) {
    try { localStorage.setItem('sb-' + key, val ? '1' : '0'); } catch (e) { }
  }
  function loadSidebarState(key, defaultVal) {
    try { var v = localStorage.getItem('sb-' + key); return v === null ? defaultVal : v === '1'; }
    catch (e) { return defaultVal; }
  }

  function initSidebarState() {
    var bp = getBreakpoint();
    if (bp === 'mobile') {
      /* Always hidden on mobile, ignore saved state */
      closeMobileSidebar();
      return;
    }
    if (bp === 'desktop') {
      /* Default: expanded. Respect saved choice. */
      var collapsed = loadSidebarState(false);
      applyDesktopState(collapsed);
      return;

      // /* Default: expanded(false = not collapsed).Respect saved choice. */
      // var saved = localStorage.getItem('sb-desktop-collapsed');
      // var collapsed = saved === '1';   // only collapse if explicitly saved as '1'
      // applyDesktopState(collapsed);
      // return;
    }
    if (bp === 'tablet') {
      /* Default: icon rail (not expanded). Respect saved choice. */
      var expanded = loadSidebarState('tablet-expanded', false);
      applyTabletState(expanded);
      return;
    }
  }

  function handleToggleClick(e) {
    e.stopPropagation();
    var bp = getBreakpoint();
    if (bp === 'mobile') {
      var sb = document.getElementById('statdium-sidebar');
      if (sb && sb.classList.contains('mobile-open')) closeMobileSidebar();
      else openMobileSidebar();
      return;
    }
    if (bp === 'desktop') {
      var sb = document.getElementById('statdium-sidebar');
      var willCollapse = !sb.classList.contains('collapsed');
      applyDesktopState(willCollapse);
      saveSidebarState('desktop-collapsed', willCollapse);
      return;
    }
    if (bp === 'tablet') {
      var sb = document.getElementById('statdium-sidebar');
      var willExpand = !sb.classList.contains('expanded');
      applyTabletState(willExpand);
      saveSidebarState('tablet-expanded', willExpand);
      return;
    }
  }

  function bindSidebar() {
    initSidebarState();

    /* Main toggle button */
    var btn = document.getElementById('sidebar-toggle-btn');
    if (btn && !btn._sbInit) {
      btn._sbInit = true;
      btn.addEventListener('click', handleToggleClick);
    }

    /* Mobile topbar hamburger */
    document.querySelectorAll('[data-mobile-toggle]').forEach(function (b) {
      if (b._mbInit) return; b._mbInit = true;
      b.addEventListener('click', function (e) {
        e.stopPropagation();
        var sb = document.getElementById('statdium-sidebar');
        if (sb && sb.classList.contains('mobile-open')) closeMobileSidebar();
        else openMobileSidebar();
      });
    });

    /* Overlay click closes mobile drawer */
    var ov = document.getElementById('sidebar-overlay');
    if (ov && !ov._ovInit) {
      ov._ovInit = true;
      ov.addEventListener('click', closeMobileSidebar);
    }

    /* Nav links close drawer on mobile */
    document.querySelectorAll('.sidebar-link').forEach(function (link) {
      if (link._lnkInit) return; link._lnkInit = true;
      link.addEventListener('click', function () {
        if (getBreakpoint() === 'mobile') closeMobileSidebar();
      });
    });

    /* Re-apply correct state on window resize */
    if (!window._sbResizeInit) {
      window._sbResizeInit = true;
      window.addEventListener('resize', function () {
        clearTimeout(window._sbResizeTimer);
        window._sbResizeTimer = setTimeout(initSidebarState, 120);
      });
    }
  }


  /* ══ ACTIVE SIDEBAR LINK ══ */
  function updateActiveLink() {
    var path = window.location.pathname || '/';
    document.querySelectorAll('.sidebar-link').forEach(function (link) {
      var href = link.getAttribute('href') || '';
      var active = (href === '/' && path === '/') || (href !== '/' && (path === href || path.startsWith(href + '/')));
      link.classList.toggle('active', active);
    });
  }
  /* Patch Dash pushState so active link updates on navigation */
  (function () {
    var orig = history.pushState;
    history.pushState = function () { orig.apply(this, arguments); setTimeout(updateActiveLink, 80); };
  })();

  /* ══════════════════════════════════════════════════════
     MATCH MODAL
     Open: card click sets match-modal-id Dash store (via hidden input).
     Close: backdrop click OR ✕ button.
     Backdrop close: we trigger the match-modal-close Dash store
     by finding its hidden input and dispatching a change event,
     which fires the Dash callback that resets match-modal-id to null
     and hides the modal via CSS.
     ══════════════════════════════════════════════════════ */
  function triggerDashStore(storeId, value) {
    /* Dash stores render as a script tag with data-dash-store or a hidden div.
       The reliable way to update from JS is via the window.dash_clientside
       or by firing on the store's underlying element. */
    var store = document.getElementById(storeId);
    if (!store) return;
    /* Try setting data attribute that Dash watches */
    try {
      var event = new CustomEvent('_dashprivate_update', {
        bubbles: true, detail: { value: value }
      });
      store.dispatchEvent(event);
    } catch (e) { }
  }

  function hideModal() {
    var bd = document.getElementById('match-modal-backdrop');
    var dr = document.getElementById('match-modal-drawer');
    if (bd) bd.style.display = 'none';
    if (dr) dr.style.display = 'none';
  }

  function initModalBackdropClose() {
    var bd = document.getElementById('match-modal-backdrop');
    if (bd && !bd._closeInit) {
      bd._closeInit = true;
      bd.addEventListener('click', function () {
        /* Hide immediately for snappy UX, Dash will confirm via callback */
        hideModal();
        /* Find the modal-close-btn and click it to trigger the Dash callback */
        var closeBtn = document.getElementById('modal-close-btn');
        if (closeBtn) closeBtn.click();
      });
    }
  }

  function initMatchCardClicks() {
    document.querySelectorAll('[data-match-id]').forEach(function (card) {
      if (card._modalInit) return; card._modalInit = true;
      card.addEventListener('click', function (e) {
        if (e.target.closest('a') || e.target.closest('button')) return;
        /* Show modal shell immediately (body filled by Dash callback) */
        var bd = document.getElementById('match-modal-backdrop');
        var dr = document.getElementById('match-modal-drawer');
        if (bd) bd.style.display = 'block';
        if (dr) dr.style.display = 'block';
      });
    });
    initModalBackdropClose();
  }

  /* ══ KEYBOARD SHORTCUTS ══ */
  var SHORTCUTS = {
    'g': '/', 'b': '/bracket', 't': '/teams', 'k': '/leaderboards',
    'i': '/insights', 'h': '/history', 'w': '/scenario', 's': '/simulator',
    'p': '/predictor', 'f': '/formations', 'c': '/confederations', 'd': '/tactical-dna',
  };
  function initKeyboard() {
    if (window._kbInit) return; window._kbInit = true;
    document.addEventListener('keydown', function (e) {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      var key = e.key.toLowerCase();
      if (key === 'escape') { hideModal(); return; }
      if (key === '?' || (e.shiftKey && e.key === '/')) { toggleHelpModal(); return; }
      if (SHORTCUTS[key] && !e.ctrlKey && !e.metaKey && !e.altKey) { e.preventDefault(); window.location.href = SHORTCUTS[key]; }
    });
    buildHelpModal();
  }
  function buildHelpModal() {
    if (document.getElementById('kb-help-modal')) return;
    var m = document.createElement('div');
    m.id = 'kb-help-modal';
    m.style.cssText = 'display:none;position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.8);backdrop-filter:blur(6px);align-items:center;justify-content:center;';
    m.innerHTML = '<div style="background:#111118;border:1px solid #252530;border-radius:16px;padding:28px;max-width:460px;width:90%;box-shadow:0 24px 80px rgba(0,0,0,0.6);">' +
      '<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:22px;font-weight:800;color:#F2F2F7;margin-bottom:4px;">⌨️ Keyboard Shortcuts</div>' +
      '<div style="font-size:12px;color:#8E8E9A;margin-bottom:16px;">Press any key to navigate</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">' +
      [['G', 'Live'], ['B', 'Bracket'], ['T', 'Teams'], ['K', 'Leaderboards'],
      ['I', 'Insights'], ['H', 'History'], ['W', 'What If'], ['S', 'Simulator'],
      ['P', 'Predictor'], ['F', 'Formations'], ['C', 'Confederations'], ['D', 'Tactical DNA']]
        .map(function (r) { return '<div style="display:flex;align-items:center;gap:8px;padding:5px 8px;background:#18181F;border-radius:6px;"><kbd style="background:#252530;color:#00E5A0;border-radius:4px;padding:2px 7px;font-family:monospace;font-size:12px;font-weight:700;">' + r[0] + '</kbd><span style="font-size:12px;color:#8E8E9A;">' + r[1] + '</span></div>'; }).join('') +
      '</div><div style="margin-top:16px;font-size:11px;color:#48484A;">Press <kbd style="background:#252530;color:#8E8E9A;border-radius:3px;padding:1px 6px;font-family:monospace;">ESC</kbd> to close</div></div>';
    m.addEventListener('click', function (e) { if (e.target === m) closeHelpModal(); });
    document.body.appendChild(m);
  }
  function toggleHelpModal() { var m = document.getElementById('kb-help-modal'); if (m) m.style.display = m.style.display === 'flex' ? 'none' : 'flex'; }
  function closeHelpModal() { var m = document.getElementById('kb-help-modal'); if (m) m.style.display = 'none'; }

  /* ══ WATCH DASH PAGE NAVIGATION ══ */
  function watchDashNav() {
    var pc = document.getElementById('page-content');
    if (!pc || pc._watched) return; pc._watched = true;
    new MutationObserver(function () {
      setTimeout(function () {
        updateActiveLink();
        initCountUp();
        initGlowCards();
        initTilt();
        initMatchCardClicks();
      }, 100);
    }).observe(pc, { childList: true, subtree: false });
  }

  /* ══ BOOT ══ */
  function boot() {
    initParticles();
    initSpotlight();
    initGlowCards();
    initTilt();
    initCountUp();
    bindSidebar();      // bind once — sidebar is outside page-content
    initKeyboard();
    updateActiveLink();
    initMatchCardClicks();
    watchDashNav();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
  window.addEventListener('load', function () { setTimeout(boot, 250); });

})();
