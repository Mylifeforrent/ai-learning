/**
 * Agent 上下文管理系统 -- HTML 课件主控制器
 * 负责：slide 导航、侧边菜单、画笔轨迹(T)、画板(D)、颜色选择器、快捷键
 * 版本：v3 (24 页，完整工具栏)
 */

(function () {
  'use strict';

  /* ===== 配置 ===== */
  var slideFiles = [
    'S001-cover.html',
    'S004-context-rot.html','S005-layered-container.html','S006-six-modules.html',
    'S007-system-prompt.html','S008-conversation-history.html','S009-memory-injection.html',
    'S010-tool-context.html','S011-task-state.html','S012-external-knowledge.html',
    'S013-five-strategies.html','S014-strategy-overview.html','S015-write-strategy.html',
    'S016-select-strategy.html','S017-compress-overview.html','S018-compress-tool-clear.html',
    'S019-compress-obs-mask.html','S020-compress-compaction.html','S021-isolate-strategy.html',
    'S022-cache-strategy.html','S023-chapter4-transition.html',
    'S025-scenario-matrix.html','S026-token-economics.html','S027-knowledge-map.html'
  ];

  var slideTitles = [
    'Agent 上下文管理系统',
    'Context Rot：有效窗口的真相',
    '分层容器模型：上下文窗口全景',
    '第二章：六大功能模块',
    '系统提示层：Agent的操作系统',
    '对话历史管理层：三策略对比',
    '记忆检索注入层：Just-in-time',
    '工具上下文管理层：密集度分级',
    '任务状态层：Scratchpad对比',
    '外部知识层：RAG vs 长上下文',
    '第三章：五策略框架',
    '五策略全景总览',
    'Write：写入持久化',
    'Select：运行时检索',
    'Compress：上下文压缩概览',
    'Compress：工具结果清除',
    'Compress：观察遮蔽',
    'Compress：Compaction 压缩重启',
    'Isolate：上下文隔离',
    'Cache：提示缓存',
    '上下文工程总结',
    '场景-策略匹配矩阵',
    'Token 经济学与优化路线',
    '全课总结与知识图谱'
  ];

  var chapters = [
    { title: '第一章：认知升维', start: 0, end: 2 },
    { title: '第二章：六大功能模块', start: 3, end: 9 },
    { title: '第三章：五策略框架', start: 10, end: 19 },
    { title: '第四章：决策内化', start: 20, end: 23 }
  ];

  var totalSlides = slideFiles.length;
  var currentIndex = 0;
  var slideCache = {};
  var currentCleanup = null;
  var menuOpen = false;
  var drawBoardEnabled = false;
  var drawCtx = null;
  var isDrawing = false;
  var currentDrawColor = '#2D5A7A';
  var colorPickerOpen = false;

  /* ===== loadSlide ===== */
  async function loadSlide(n) {
    if (n < 0 || n >= totalSlides) return;

    // cleanup previous
    if (typeof currentCleanup === 'function') {
      try { currentCleanup(); } catch (e) { /* ignore */ }
    }
    currentCleanup = null;

    currentIndex = n;
    updateProgressBar();
    updatePageIndicator();
    updateMenuActiveState();
    updateHash();

    var file = slideFiles[n];
    var html;

    if (slideCache[file]) {
      html = slideCache[file];
    } else {
      try {
        var resp = await fetch('slides/' + file, { cache: 'no-store' });
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        html = await resp.text();
        slideCache[file] = html;
      } catch (e) {
        html = '<div style="text-align:center;padding:4rem;color:#6b5e52;">无法加载 ' + file + '</div>';
        slideCache[file] = html;
      }
    }

    var viewport = document.getElementById('slide-viewport');
    viewport.innerHTML = '<div class="slide">' + html + '</div>';

    // Re-execute scripts
    // (querySelectorAll scoped to viewport, so scripts inside .slide are found)
    var scripts = viewport.querySelectorAll('script');
    scripts.forEach(function(oldScript) {
      var newScript = document.createElement('script');
      if (oldScript.src) {
        newScript.src = oldScript.src;
        newScript.async = false;
      } else {
        newScript.textContent = oldScript.textContent;
      }
      oldScript.parentNode.replaceChild(newScript, oldScript);
    });

    // hookFn support
    if (window.__slideHookFn) {
      try {
        var cleanup = window.__slideHookFn();
        if (typeof cleanup === 'function') currentCleanup = cleanup;
      } catch (e) { console.warn('hookFn error:', e); }
      window.__slideHookFn = null;
    }

    // Animate .animate-ready elements
    setTimeout(function() {
      var els = document.querySelectorAll('.animate-ready');
      els.forEach(function(el) {
        var delay = parseFloat(el.getAttribute('data-delay') || '0');
        setTimeout(function() { el.classList.add('animated'); }, delay * 1000);
      });
    }, 8);

    // Preload adjacent
    [n - 1, n + 1].forEach(function(i) {
      if (i >= 0 && i < totalSlides && !slideCache[slideFiles[i]]) {
        fetch('slides/' + slideFiles[i], { cache: 'no-store' }).then(function(r) { return r.ok ? r.text() : ''; }).then(function(t) {
          if (t) slideCache[slideFiles[i]] = t;
        }).catch(function() {});
      }
    });

    // Update nav button states
    var prev = document.getElementById('nav-prev');
    var next = document.getElementById('nav-next');
    if (prev) prev.disabled = n === 0;
    if (next) next.disabled = n === totalSlides - 1;
  }

  /* ===== 进度条 & 页码 ===== */
  function updateProgressBar() {
    var pct = totalSlides > 1 ? (currentIndex / (totalSlides - 1)) * 100 : 100;
    var bar = document.getElementById('progress-bar');
    if (bar) bar.style.width = Math.max(4, pct) + '%';
  }

  function updatePageIndicator() {
    var cur = document.getElementById('page-current');
    var tot = document.getElementById('page-total');
    if (cur) cur.textContent = currentIndex + 1;
    if (tot) tot.textContent = totalSlides;
  }

  function updateHash() {
    history.replaceState(null, '', '#' + (currentIndex + 1));
  }

  function readHash() {
    var hash = location.hash.replace('#', '');
    var num = parseInt(hash, 10);
    if (num >= 1 && num <= totalSlides) return num - 1;
    return 0;
  }

  /* ===== 翻页 ===== */
  function prevSlide() { if (currentIndex > 0) loadSlide(currentIndex - 1); }
  function nextSlide() { if (currentIndex < totalSlides - 1) loadSlide(currentIndex + 1); }
  function goToSlide(n) { if (n >= 0 && n < totalSlides) loadSlide(n); }

  /* ===== 全屏 ===== */
  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen && document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen && document.exitFullscreen();
    }
  }

  /* ===== 侧边菜单 ===== */
  function buildMenu() {
    var list = document.getElementById('menu-list');
    if (!list) return;
    list.innerHTML = '';

    chapters.forEach(function(ch) {
      var chEl = document.createElement('div');
      chEl.className = 'menu-chapter';
      chEl.textContent = ch.title;
      list.appendChild(chEl);

      for (var i = ch.start; i <= ch.end; i++) {
        (function(idx) {
          var item = document.createElement('div');
          item.className = 'menu-item';
          item.setAttribute('data-index', idx);
          item.innerHTML = '<span class="menu-item-num">' + String(idx + 1).padStart(2, '0') + '</span>' +
            '<span>' + slideTitles[idx] + '</span>';
          item.onclick = function() { goToSlide(idx); closeMenu(); };
          list.appendChild(item);
        })(i);
      }
    });
  }

  function updateMenuActiveState() {
    var items = document.querySelectorAll('.menu-item');
    items.forEach(function(item) {
      var idx = parseInt(item.getAttribute('data-index'));
      item.classList.toggle('active', idx === currentIndex);
    });
  }

  function toggleMenu() { menuOpen ? closeMenu() : openMenu(); }

  function openMenu() {
    menuOpen = true;
    var menu = document.getElementById('side-menu');
    var overlay = document.getElementById('menu-overlay');
    if (menu) menu.classList.add('open');
    if (overlay) overlay.classList.add('visible');
    updateMenuActiveState();
  }

  function closeMenu() {
    menuOpen = false;
    var menu = document.getElementById('side-menu');
    var overlay = document.getElementById('menu-overlay');
    if (menu) menu.classList.remove('open');
    if (overlay) overlay.classList.remove('visible');
  }

  /* ===== 画笔轨迹 (T) ===== */
  var _pen = {
    active: false,
    canvas: null,
    ctx: null,
    drawing: false,
    points: [],
    trails: [],
    rafId: null,
    FADE_DURATION: 2000,
    LINE_WIDTH: 3
  };

  function initPenTrail() {
    var canvas = document.getElementById('pen-trail-canvas');
    if (!canvas) return;
    _pen.canvas = canvas;
    _pen.ctx = canvas.getContext('2d');

    function resize() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
    resize();
    window.addEventListener('resize', resize);

    canvas.addEventListener('mousedown', function(e) { _pen.drawing = true; _pen.points = [{x:e.clientX,y:e.clientY,t:Date.now()}]; });
    canvas.addEventListener('mousemove', function(e) {
      if (!_pen.drawing) return;
      _pen.points.push({x:e.clientX,y:e.clientY,t:Date.now()});
      penRender();
    });
    canvas.addEventListener('mouseup', penUp);
    canvas.addEventListener('mouseleave', penUp);

    canvas.addEventListener('touchstart', function(e) { e.preventDefault(); var t=e.touches[0]; _pen.drawing=true; _pen.points=[{x:t.clientX,y:t.clientY,t:Date.now()}]; }, {passive:false});
    canvas.addEventListener('touchmove', function(e) { e.preventDefault(); if(!_pen.drawing)return; var t=e.touches[0]; _pen.points.push({x:t.clientX,y:t.clientY,t:Date.now()}); penRender(); }, {passive:false});
    canvas.addEventListener('touchend', function(e) { e.preventDefault(); penUp(); }, {passive:false});
  }

  function penUp() {
    if (!_pen.drawing) return;
    _pen.drawing = false;
    if (_pen.points.length > 1) {
      _pen.trails.push({ points: _pen.points.slice(), startTime: Date.now() });
    }
    _pen.points = [];
    if (_pen.active) animatePenTrail();
  }

  function penRender() {
    var ctx = _pen.ctx, canvas = _pen.canvas;
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    var now = Date.now();
    _pen.trails = _pen.trails.filter(function(trail) { return now - trail.startTime < _pen.FADE_DURATION; });
    _pen.trails.forEach(function(trail) {
      var alpha = Math.max(0, 1 - (now - trail.startTime) / _pen.FADE_DURATION);
      penDrawPath(ctx, trail.points, alpha * 0.7);
    });
    if (_pen.points.length > 1) penDrawPath(ctx, _pen.points, 1);
  }

  function penDrawPath(ctx, points, alpha) {
    if (points.length < 2) return;
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (var i = 1; i < points.length; i++) {
      var prev = points[i-1], curr = points[i];
      var mx = (prev.x+curr.x)/2, my = (prev.y+curr.y)/2;
      ctx.quadraticCurveTo(prev.x, prev.y, mx, my);
    }
    ctx.lineTo(points[points.length-1].x, points[points.length-1].y);
    ctx.strokeStyle = hexToRgba(currentDrawColor, alpha);
    ctx.lineWidth = _pen.LINE_WIDTH;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
  }

  function hexToRgba(hex, alpha) {
    hex = hex.replace('#', '');
    if (hex.length === 3) hex = hex[0]+hex[0]+hex[1]+hex[1]+hex[2]+hex[2];
    var r = parseInt(hex.substring(0,2),16), g = parseInt(hex.substring(2,4),16), b = parseInt(hex.substring(4,6),16);
    return 'rgba('+r+','+g+','+b+','+alpha+')';
  }

  function togglePenTrail() {
    _pen.active = !_pen.active;
    var canvas = document.getElementById('pen-trail-canvas');
    var btn = document.getElementById('btn-pen');
    if (_pen.active) {
      if (canvas) canvas.classList.add('pen-active');
      if (btn) btn.classList.add('active');
      animatePenTrail();
    } else {
      if (canvas) canvas.classList.remove('pen-active');
      if (btn) btn.classList.remove('active');
      if (_pen.rafId) cancelAnimationFrame(_pen.rafId);
      _pen.rafId = null;
      if (_pen.ctx && canvas) _pen.ctx.clearRect(0, 0, canvas.width, canvas.height);
      _pen.trails = [];
      _pen.points = [];
    }
  }

  function animatePenTrail() {
    if (!_pen.active) return;
    penRender();
    if (_pen.trails.length > 0 || _pen.drawing) {
      _pen.rafId = requestAnimationFrame(animatePenTrail);
    } else {
      _pen.rafId = null;
    }
  }

  /* ===== 画板 (D) ===== */
  function initDrawBoard() {
    var canvas = document.getElementById('draw-board-canvas');
    if (!canvas) return;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    drawCtx = canvas.getContext('2d');
    window.addEventListener('resize', function() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; });

    canvas.addEventListener('mousedown', function(e) { if (!drawBoardEnabled) return; isDrawing=true; drawCtx.beginPath(); drawCtx.moveTo(e.clientX,e.clientY); });
    canvas.addEventListener('mousemove', function(e) {
      if (!isDrawing) return;
      drawCtx.lineTo(e.clientX,e.clientY);
      drawCtx.strokeStyle = currentDrawColor;
      drawCtx.lineWidth=3; drawCtx.lineCap='round'; drawCtx.lineJoin='round'; drawCtx.stroke();
    });
    canvas.addEventListener('mouseup', function() { isDrawing=false; });
    canvas.addEventListener('mouseleave', function() { isDrawing=false; });
  }

  function toggleDrawBoard() {
    drawBoardEnabled = !drawBoardEnabled;
    var canvas = document.getElementById('draw-board-canvas');
    if (!canvas) return;
    if (drawBoardEnabled) {
      canvas.style.pointerEvents = 'all';
      canvas.style.cursor = 'crosshair';
      document.body.classList.add('draw-mode');
    } else {
      clearDrawBoard();
    }
  }

  function clearDrawBoard() {
    drawBoardEnabled = false;
    isDrawing = false;
    var canvas = document.getElementById('draw-board-canvas');
    if (canvas && drawCtx) {
      drawCtx.clearRect(0, 0, canvas.width, canvas.height);
      canvas.style.pointerEvents = 'none';
      canvas.style.cursor = 'default';
    }
    document.body.classList.remove('draw-mode');
  }

  /* ===== 颜色选择器 ===== */
  function setDrawColor(hex) {
    currentDrawColor = hex;
    var dot = document.getElementById('color-dot-indicator');
    if (dot) dot.style.background = hex;
    document.querySelectorAll('#color-picker-popup .color-dot').forEach(function(btn) {
      btn.classList.toggle('selected', btn.dataset.color === hex);
    });
    closeColorPicker();
  }

  function toggleColorPicker() {
    colorPickerOpen = !colorPickerOpen;
    var popup = document.getElementById('color-picker-popup');
    if (popup) popup.classList.toggle('open', colorPickerOpen);
  }

  function closeColorPicker() {
    colorPickerOpen = false;
    var popup = document.getElementById('color-picker-popup');
    if (popup) popup.classList.remove('open');
  }

  /* ===== 键盘事件 ===== */
  document.addEventListener('keydown', function(e) {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    switch (e.key) {
      case 'ArrowLeft': case 'ArrowUp': e.preventDefault(); prevSlide(); break;
      case 'ArrowRight': case 'ArrowDown': case ' ': e.preventDefault(); nextSlide(); break;
      case 'Home': e.preventDefault(); goToSlide(0); break;
      case 'End': e.preventDefault(); goToSlide(totalSlides - 1); break;
      case 'Escape':
        if (drawBoardEnabled) { clearDrawBoard(); break; }
        if (_pen.active) { togglePenTrail(); break; }
        if (menuOpen) closeMenu();
        break;
      case 'f': case 'F':
        if (!e.metaKey && !e.ctrlKey) { e.preventDefault(); toggleFullscreen(); }
        break;
      case 'm': case 'M':
        if (!e.metaKey && !e.ctrlKey) { e.preventDefault(); toggleMenu(); }
        break;
      case 't': case 'T': togglePenTrail(); break;
      case 'd': case 'D': toggleDrawBoard(); break;
    }
  });

  /* ===== 触摸滑动 ===== */
  var touchStartX = 0, touchStartY = 0;
  document.addEventListener('touchstart', function(e) {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
  }, { passive: true });
  document.addEventListener('touchend', function(e) {
    var dx = e.changedTouches[0].clientX - touchStartX;
    var dy = e.changedTouches[0].clientY - touchStartY;
    if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 50) {
      if (dx < 0) nextSlide(); else prevSlide();
    }
  }, { passive: true });

  /* ===== 全局 API ===== */
  window.__nextSlide = nextSlide;
  window.__prevSlide = prevSlide;
  window.__goSlide = function(i) { closeMenu(); goToSlide(i); };
  window.__toggleMenu = toggleMenu;
  window.__closeMenu = closeMenu;
  window.__toggleFullscreen = toggleFullscreen;
  window.__togglePenTrail = togglePenTrail;
  window.__toggleColorPicker = toggleColorPicker;
  window.__setDrawColor = setDrawColor;

  /* ===== 初始化 ===== */
  document.addEventListener('DOMContentLoaded', function() {
    buildMenu();
    initPenTrail();
    initDrawBoard();
    // 初始化颜色指示器
    var dot = document.getElementById('color-dot-indicator');
    if (dot) dot.style.background = currentDrawColor;
    // 点击外部关闭色盘
    document.addEventListener('click', function(e) {
      if (colorPickerOpen && !e.target.closest('#color-picker-wrap')) closeColorPicker();
    });
    var startSlide = readHash();
    loadSlide(startSlide);
  });

})();
