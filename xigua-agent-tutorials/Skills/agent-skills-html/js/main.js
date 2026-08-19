/* ========== Agent Skills Explorable Main Lesson v2 - Core Navigation ========== */

const slideFiles = [
    'slides/S001-cover.html',
    'slides/S005A-part1-transition.html',
    'slides/S006-skill-not-prompt.html',
    'slides/S007-definition.html',
    'slides/S008-core-traits.html',
    'slides/S008A-part2-transition.html',
    'slides/S010A-skill-execution-flow.html',
    'slides/S011-routing-decision-tree.html',
    'slides/S010B-token-economics.html',
    'slides/S012A-part3-transition.html',
    'slides/S013-semantic-zoom.html',
    'slides/S013B-skill-collaboration-map.html',
    'slides/S013C-skill-tree-explorer.html',
    'slides/S014-frontmatter-deep-dive.html',
    'slides/S016-resource-layer.html',
    'slides/S015-skillmd-deep-dive.html',
    'slides/S017-ecosystem-map.html',
    'slides/S017A-part4-transition.html',
    'slides/S018-source-landscape.html',
    'slides/S019-lifecycle-flow.html',
    'slides/S020-task-quiz.html',
    'slides/S021-boundary-counterfactual.html',
    'slides/S022-boundary-checklist.html',
    'slides/S022A-skills-vs-fc-mcp.html',
    'slides/S023-use-to-design.html',
    'slides/S024-learning-roadmap.html',
    'slides/S025-summary.html'
];

const slideTitles = [
    '封面：Skills 从入门到精通实战课',
    '第一部分：Agent Skills 是什么',
    'Skill 不是长 Prompt',
    '一句话理解 Skill',
    'Skill 的三大核心特征',
    '第二部分：Skills 如何运行',
    'Skills 触发与执行全流程',
    '路由不是拍脑袋',
    'Token 经济学：为什么 Skill 设计如此高效',
    '第三部分：Skills 内部结构',
    '从外面看 Skill，到里面看 Skill',
    'Skill 内部协同关系',
    'Agent Skills 完整目录结构（可探索）',
    '深入看 frontmatter',
    '深入看资源层',
    '深入看 SKILL.md',
    'Skill 从哪来，怎么进入 Agent',
    '第四部分：实践与设计',
    '能力来源全景',
    '发现到管理的完整生命周期',
    '这个需求会触发哪个 Skill？',
    '设计对了和设计错了，差别在哪',
    '什么时候 Skill 会失效',
    'Skills vs Function Calling vs MCP',
    '从会用到会设计',
    '四阶段学习路径',
    '最后记住这一张图'
];

let currentSlide = 1;
let loadedSlides = {};
const totalSlides = slideFiles.length;

async function loadSlide(n) {
    if (n < 1 || n > totalSlides) return '';
    const file = slideFiles[n - 1];
    if (loadedSlides[file]) return loadedSlides[file];

    try {
        const resp = await fetch(file + '?t=' + Date.now());
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const html = await resp.text();
        loadedSlides[file] = html;
        return html;
    } catch (error) {
        console.error('加载失败:', file, error);
        return '<div class="slide" style="justify-content:center;align-items:center;">' +
            '<div class="content content-centered">' +
            '<h2 style="color:#DC2626;">页面加载失败</h2>' +
            '<p style="color:#64748B;">' + file + '</p>' +
            '</div></div>';
    }
}

async function showSlide(n) {
    if (n < 1 || n > totalSlides) return;
    currentSlide = n;

    if (window._slideCleanup) {
        window._slideCleanup();
        window._slideCleanup = null;
    }

    const container = document.getElementById('slide-container');
    container.style.opacity = '0';

    const html = await loadSlide(n);
    container.innerHTML = html;

    setTimeout(() => {
        container.style.opacity = '1';
        const file = slideFiles[n - 1];
        const hookFn = window.slideHooks && window.slideHooks[file];
        if (typeof hookFn === 'function') {
            const cleanup = hookFn();
            if (typeof cleanup === 'function') {
                window._slideCleanup = cleanup;
            }
        }
        animateSlideElements();
        syncMenuState();
    }, 50);

    updateProgress();
    updatePageIndicator();
}

function animateSlideElements() {
    const elements = document.querySelectorAll('.animate-ready');
    elements.forEach((el, idx) => {
        const delay = parseFloat(el.getAttribute('data-delay') || (idx * 0.07));
        el.classList.remove('animate-ready');
        if (window.gsap) {
            window.gsap.fromTo(
                el,
                { opacity: 0, y: 12 },
                { opacity: 1, y: 0, duration: 0.35, delay, ease: 'power2.out' }
            );
        } else {
            setTimeout(() => {
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, delay * 1000);
        }
    });
}

function updateProgress() {
    const fill = document.getElementById('progressFill');
    if (!fill) return;
    fill.style.width = ((currentSlide / totalSlides) * 100) + '%';
}

function updatePageIndicator() {
    const indicator = document.getElementById('pageIndicator');
    if (!indicator) return;
    indicator.textContent = currentSlide + ' / ' + totalSlides;
}

function prevSlide() {
    if (currentSlide > 1) showSlide(currentSlide - 1);
}

function nextSlide() {
    if (currentSlide < totalSlides) showSlide(currentSlide + 1);
}

function toggleMenu() {
    const menu = document.getElementById('sidebarMenu');
    const overlay = document.getElementById('menuOverlay');
    if (!menu || !overlay) return;
    const isOpen = menu.classList.contains('open');
    if (isOpen) {
        closeMenu();
    } else {
        menu.classList.add('open');
        overlay.classList.add('active');
    }
}

function closeMenu() {
    const menu = document.getElementById('sidebarMenu');
    const overlay = document.getElementById('menuOverlay');
    if (!menu || !overlay) return;
    menu.classList.remove('open');
    overlay.classList.remove('active');
}

function jumpToSlide(n) {
    showSlide(n);
    closeMenu();
}

function buildMenu() {
    const menuItems = document.getElementById('menuItems');
    if (!menuItems) return;
    menuItems.innerHTML = '';

    slideFiles.forEach((file, idx) => {
        const item = document.createElement('div');
        item.className = 'menu-item';
        item.dataset.slide = String(idx + 1);

        const number = document.createElement('span');
        number.className = 'menu-item-number';
        number.textContent = String(idx + 1).padStart(2, '0');

        const title = document.createElement('span');
        title.className = 'menu-item-title';
        title.textContent = slideTitles[idx];

        item.appendChild(number);
        item.appendChild(title);
        item.onclick = () => jumpToSlide(idx + 1);
        menuItems.appendChild(item);
    });
}

function syncMenuState() {
    document.querySelectorAll('.menu-item').forEach((item) => {
        item.classList.toggle('active', Number(item.dataset.slide) === currentSlide);
    });
}

/* ========== 钢笔拖尾 ========== */
let isPenTrailOn = false;
let penPoints = [];
const PEN_TRAIL_LENGTH = 20;
let penCanvas, penCtx;

function initPenTrail() {
    penCanvas = document.getElementById('pen-trail-canvas');
    penCtx = penCanvas.getContext('2d');
    resizePenCanvas();
    window.addEventListener('resize', resizePenCanvas);
    document.addEventListener('mousemove', trackPenPoint);
}

function resizePenCanvas() {
    if (!penCanvas) return;
    penCanvas.width = window.innerWidth;
    penCanvas.height = window.innerHeight;
}

function trackPenPoint(e) {
    if (isPenTrailOn) {
        penPoints.push({ x: e.clientX, y: e.clientY, age: 0 });
    }
}

function togglePenTrail() {
    isPenTrailOn = !isPenTrailOn;
    penCanvas.classList.toggle('active', isPenTrailOn);
    if (isPenTrailOn) {
        penPoints = [];
        animatePenTrail();
    }
}

function animatePenTrail() {
    if (!isPenTrailOn) return;
    penCtx.clearRect(0, 0, penCanvas.width, penCanvas.height);

    for (let i = 0; i < penPoints.length; i++) {
        penPoints[i].age++;
    }
    penPoints = penPoints.filter((p) => p.age < PEN_TRAIL_LENGTH);

    if (penPoints.length >= 2) {
        for (let i = 1; i < penPoints.length; i++) {
            const p1 = penPoints[i - 1];
            const p2 = penPoints[i];
            const opacity = i / penPoints.length;

            penCtx.beginPath();
            penCtx.moveTo(p1.x, p1.y);
            penCtx.lineTo(p2.x, p2.y);
            penCtx.lineWidth = 4 * opacity;
            penCtx.lineCap = 'round';
            penCtx.lineJoin = 'round';
            penCtx.strokeStyle = `rgba(13, 148, 136, ${opacity})`;
            penCtx.stroke();
        }
    }
    requestAnimationFrame(animatePenTrail);
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') prevSlide();
    else if (e.key === 'ArrowRight') nextSlide();
    else if (e.key === 'f' || e.key === 'F') toggleFullscreen();
    else if (e.key === 'm' || e.key === 'M') toggleMenu();
    else if (e.key === 't' || e.key === 'T') togglePenTrail();
});

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}

let touchStartX = 0;
let touchEndX = 0;

document.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
});

document.addEventListener('touchend', (e) => {
    touchEndX = e.changedTouches[0].screenX;
    const diff = touchStartX - touchEndX;
    if (Math.abs(diff) > 50) {
        if (diff > 0) nextSlide();
        else prevSlide();
    }
});

window.addEventListener('DOMContentLoaded', () => {
    buildMenu();
    showSlide(1);
    initPenTrail();
});
