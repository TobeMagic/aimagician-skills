/**
 * <deck-stage> — HTML幻灯片外壳web component
 *
 * 提供功能：
 * - 固定尺寸canvas（默认1920×1080）+ auto-scale + letterbox
 * - 键盘导航（←/→/↑/↓/Space/Page/Home/End）
 * - Esc / O 全局缩略图概览，F 全屏
 * - 左右点击区域导航
 * - 滚轮和触摸滑动导航
 * - slide counter (当前/总数)
 * - progress bar
 * - localStorage持久化当前slide
 * - Speaker notes postMessage (支持外层渲染)
 * - Hash导航 (#slide-5 跳到第5张)
 * - Print-to-PDF支持 (Cmd+P / Ctrl+P 一页一slide)
 * - 自动给每个slide添加 data-screen-label
 *
 * 用法：
 *   <deck-stage>
 *     <section>Slide 1</section>
 *     <section>Slide 2</section>
 *   </deck-stage>
 *
 * 自定义尺寸：
 *   <deck-stage width="1080" height="1920">...</deck-stage>
 *
 * Speaker notes：在<head>加
 *   <script type="application/json" id="speaker-notes">
 *   ["slide 1 notes", "slide 2 notes"]
 *   </script>
 */

(function() {
  const STORAGE_KEY_PREFIX = 'deck-stage-slide-';

  class DeckStage extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this._currentSlide = 0;
      this._slides = [];
      this._storageKey = STORAGE_KEY_PREFIX + (location.pathname || 'default');
      this._overviewOpen = false;
      this._wheelDelta = 0;
      this._wheelTimer = null;
      this._touchStart = null;
      this._listeners = [];
    }

    connectedCallback() {
      this._width = parseInt(this.getAttribute('width')) || 1920;
      this._height = parseInt(this.getAttribute('height')) || 1080;

      // Shadow DOM 先渲染（独立于子节点，不受 parser 时机影响）
      this._render();

      // 防御：若 script 放在 <head> 里（而非 </deck-stage> 之后），
      // parser 此刻可能还没处理完子 <section>，querySelectorAll 会返回空。
      // 延迟到下一个事件循环，确保子节点都已 parse 完毕。
        const init = () => {
          this._collectSlides();
          this._createOverview();
          this._setupEventListeners();
          this._restoreSlide();
          this._updateDisplay();
          this._setupPrintStyles();
      };

      if (this.ownerDocument.readyState === 'loading') {
        // 文档还在 parse，等 DOMContentLoaded 一次搞定所有 section
        this.ownerDocument.addEventListener('DOMContentLoaded', init, { once: true });
      } else {
        // 文档已 parse 完（script 在 body 底部或 defer），下一帧收集即可
        requestAnimationFrame(init);
      }
    }

    disconnectedCallback() {
      this._listeners.forEach(([target, type, handler, options]) => {
        target.removeEventListener(type, handler, options);
      });
      this._listeners = [];
      this._overview?.remove();
      this._overviewStyle?.remove();
      if (this._wheelTimer) clearTimeout(this._wheelTimer);
    }

    _render() {
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
            position: fixed;
            inset: 0;
            background: #000;
            overflow: hidden;
            font-family: -apple-system, 'SF Pro Text', 'PingFang SC', sans-serif;
          }

          :host([noscale]) .stage {
            transform: none !important;
            top: 0 !important;
            left: 0 !important;
          }

          :host([data-exporting]) .counter,
          :host([data-exporting]) .nav-zone,
          :host([data-exporting]) .shell-actions,
          :host([data-exporting]) .progress {
            display: none !important;
          }

          .stage {
            position: absolute;
            top: 50%;
            left: 50%;
            transform-origin: top left;
            will-change: transform;
            background: #fff;
          }

          .slide-wrapper {
            width: 100%;
            height: 100%;
            position: relative;
          }

          ::slotted(section) {
            display: none;
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
            overflow: hidden;
          }

          ::slotted(section.active) {
            display: block;
          }

          .counter {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.6);
            color: #fff;
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 13px;
            font-variant-numeric: tabular-nums;
            z-index: 100;
            user-select: none;
            opacity: 0.6;
            transition: opacity 0.2s;
          }

          .counter:hover {
            opacity: 1;
          }

          .shell-actions {
            position: fixed;
            top: 18px;
            right: 18px;
            z-index: 100;
            display: flex;
            gap: 8px;
          }

          .icon-button {
            width: 36px;
            height: 36px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 50%;
            background: rgba(0, 0, 0, 0.5);
            color: rgba(255, 255, 255, 0.84);
            cursor: pointer;
            font: 18px/1 sans-serif;
            opacity: 0.64;
            transition: opacity 0.2s, background 0.2s;
          }

          .icon-button:hover,
          .icon-button:focus-visible {
            opacity: 1;
            background: rgba(0, 0, 0, 0.72);
            outline: 2px solid rgba(255, 255, 255, 0.72);
            outline-offset: 2px;
          }

          .progress {
            position: fixed;
            left: 0;
            right: 0;
            bottom: 0;
            height: 3px;
            z-index: 100;
            background: rgba(255, 255, 255, 0.14);
          }

          .progress > span {
            display: block;
            width: 0;
            height: 100%;
            background: rgba(255, 255, 255, 0.88);
            transition: width 0.24s ease;
          }

          .nav-zone {
            position: fixed;
            top: 0;
            bottom: 0;
            width: 15%;
            cursor: pointer;
            z-index: 50;
          }

          .nav-zone.left { left: 0; }
          .nav-zone.right { right: 0; }

          .nav-hint {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            width: 44px;
            height: 44px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            opacity: 0;
            transition: opacity 0.2s;
          }

          .nav-zone.left .nav-hint { left: 20px; }
          .nav-zone.right .nav-hint { right: 20px; }

          .nav-zone:hover .nav-hint {
            opacity: 1;
          }

          @media print {
            :host {
              position: static;
              background: #fff;
            }
            .counter, .nav-zone, .shell-actions, .progress {
              display: none !important;
            }
            .stage {
              position: static;
              transform: none !important;
              page-break-after: always;
            }
            ::slotted(section) {
              display: block !important;
              position: relative !important;
              page-break-after: always;
              width: 100%;
              height: 100%;
            }
          }
        </style>

        <div class="stage" id="stage" style="width: ${this._width}px; height: ${this._height}px;">
          <div class="slide-wrapper">
            <slot></slot>
          </div>
        </div>

        <div class="nav-zone left" id="navLeft">
          <div class="nav-hint">‹</div>
        </div>
        <div class="nav-zone right" id="navRight">
          <div class="nav-hint">›</div>
        </div>

        <div class="shell-actions">
          <button class="icon-button" id="overviewButton" type="button" aria-label="Open slide overview" aria-pressed="false" title="Overview (Esc or O)">⊞</button>
          <button class="icon-button" id="fullscreenButton" type="button" aria-label="Toggle full screen" title="Full screen (F)">⛶</button>
        </div>
        <div class="counter" id="counter">1 / 1</div>
        <div class="progress" aria-hidden="true"><span id="progress"></span></div>
      `;
    }

    _collectSlides() {
      this._slides = Array.from(this.querySelectorAll(':scope > section'));

      this._slides.forEach((slide, idx) => {
        if (!slide.hasAttribute('data-screen-label')) {
          const num = String(idx + 1).padStart(2, '0');
          slide.setAttribute('data-screen-label', num);
        }
        if (!slide.hasAttribute('data-om-validate')) {
          slide.setAttribute('data-om-validate', '');
        }
      });
    }

    _listen(target, type, handler, options) {
      target.addEventListener(type, handler, options);
      this._listeners.push([target, type, handler, options]);
    }

    _setupEventListeners() {
      this._listen(window, 'resize', () => {
        this._updateScale();
        if (this._overviewOpen) this._buildOverview();
      });

      this._listen(document, 'keydown', (e) => {
        if (e.target.matches('input, textarea, [contenteditable]')) return;

        if (e.key === 'Escape') {
          e.preventDefault();
          this.toggleOverview();
          return;
        }
        if (e.key.toLowerCase() === 'o' && !e.metaKey && !e.ctrlKey && !e.altKey) {
          e.preventDefault();
          this.toggleOverview();
          return;
        }
        if (e.key.toLowerCase() === 'f' && !e.metaKey && !e.ctrlKey && !e.altKey) {
          e.preventDefault();
          this.toggleFullscreen();
          return;
        }
        if (this._overviewOpen) return;

        switch (e.key) {
          case 'ArrowRight':
          case 'ArrowDown':
          case ' ':
          case 'PageDown':
            e.preventDefault();
            this.next();
            break;
          case 'ArrowLeft':
          case 'ArrowUp':
          case 'PageUp':
            e.preventDefault();
            this.prev();
            break;
          case 'Home':
            e.preventDefault();
            this.goTo(0);
            break;
          case 'End':
            e.preventDefault();
            this.goTo(this._slides.length - 1);
            break;
        }
      });

      this._listen(this.shadowRoot.getElementById('navLeft'), 'click', () => this.prev());
      this._listen(this.shadowRoot.getElementById('navRight'), 'click', () => this.next());
      this._listen(this.shadowRoot.getElementById('overviewButton'), 'click', () => this.toggleOverview());
      this._listen(this.shadowRoot.getElementById('fullscreenButton'), 'click', () => this.toggleFullscreen());

      this._listen(window, 'wheel', (event) => {
        if (this._overviewOpen) return;
        this._wheelDelta += event.deltaY + event.deltaX;
        if (Math.abs(this._wheelDelta) >= 48) {
          this._wheelDelta > 0 ? this.next() : this.prev();
          this._wheelDelta = 0;
        }
        if (this._wheelTimer) clearTimeout(this._wheelTimer);
        this._wheelTimer = setTimeout(() => {
          this._wheelDelta = 0;
        }, 160);
      }, { passive: true });

      this._listen(window, 'touchstart', (event) => {
        const touch = event.touches[0];
        this._touchStart = touch ? { x: touch.clientX, y: touch.clientY } : null;
      }, { passive: true });

      this._listen(window, 'touchend', (event) => {
        if (this._overviewOpen || !this._touchStart) return;
        const touch = event.changedTouches[0];
        if (!touch) return;
        const dx = touch.clientX - this._touchStart.x;
        const dy = touch.clientY - this._touchStart.y;
        const primary = Math.abs(dx) >= Math.abs(dy) ? dx : dy;
        if (Math.abs(primary) >= 48) primary < 0 ? this.next() : this.prev();
        this._touchStart = null;
      }, { passive: true });

      this._listen(window, 'hashchange', () => this._handleHash());
      if (location.hash) {
        setTimeout(() => this._handleHash(), 0);
      }

      const observer = new MutationObserver(() => {
        if (this.hasAttribute('noscale')) {
          this._updateScale();
        }
      });
      observer.observe(this, { attributes: true, attributeFilter: ['noscale'] });
    }

    _createOverview() {
      this._overviewStyle = document.createElement('style');
      this._overviewStyle.dataset.deckStageOverviewStyle = '';
      this._overviewStyle.textContent = `
        [data-deck-stage-overview] {
          position: fixed;
          inset: 0;
          z-index: 2147483000;
          display: none;
          overflow: auto;
          padding: clamp(24px, 4vw, 64px);
          background: rgba(8, 9, 10, 0.94);
          color: #f4f1ea;
          backdrop-filter: blur(14px);
        }
        [data-deck-stage-overview][data-open="true"] { display: block; }
        [data-deck-stage-grid] {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr));
          gap: clamp(16px, 2vw, 28px);
          max-width: 1600px;
          margin: 0 auto;
        }
        [data-deck-stage-card] {
          min-width: 0;
          padding: 0;
          overflow: hidden;
          border: 2px solid rgba(255, 255, 255, 0.16);
          border-radius: 6px;
          background: #111;
          color: inherit;
          cursor: pointer;
          text-align: left;
        }
        [data-deck-stage-card][aria-current="true"] { border-color: rgba(255, 255, 255, 0.9); }
        [data-deck-stage-card]:hover,
        [data-deck-stage-card]:focus-visible {
          border-color: rgba(255, 255, 255, 0.68);
          outline: 2px solid rgba(255, 255, 255, 0.52);
          outline-offset: 3px;
        }
        [data-deck-stage-preview] {
          position: relative;
          width: 100%;
          overflow: hidden;
          background: #000;
        }
        [data-deck-stage-preview] > section {
          position: absolute !important;
          inset: 0 auto auto 0 !important;
          display: block !important;
          margin: 0 !important;
          transform-origin: top left !important;
          pointer-events: none !important;
        }
        [data-deck-stage-label] {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          padding: 9px 11px;
          font: 12px/1.4 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
          letter-spacing: 0.08em;
        }
        @media print {
          [data-deck-stage-overview] { display: none !important; }
        }
      `;
      document.head.appendChild(this._overviewStyle);

      this._overview = document.createElement('div');
      this._overview.dataset.deckStageOverview = '';
      this._overview.dataset.open = 'false';
      this._overview.setAttribute('role', 'dialog');
      this._overview.setAttribute('aria-modal', 'true');
      this._overview.setAttribute('aria-label', 'Slide overview');
      this._overview.innerHTML = '<div data-deck-stage-grid></div>';
      document.body.appendChild(this._overview);
    }

    _buildOverview() {
      const grid = this._overview?.querySelector('[data-deck-stage-grid]');
      if (!grid) return;
      grid.innerHTML = '';

      this._slides.forEach((slide, index) => {
        const card = document.createElement('button');
        card.type = 'button';
        card.dataset.deckStageCard = '';
        card.setAttribute('aria-current', index === this._currentSlide ? 'true' : 'false');
        card.setAttribute('aria-label', `Open slide ${index + 1} of ${this._slides.length}`);

        const preview = document.createElement('div');
        preview.dataset.deckStagePreview = '';
        preview.style.aspectRatio = `${this._width} / ${this._height}`;

        const clone = slide.cloneNode(true);
        clone.classList.add('active');
        clone.querySelectorAll('[id]').forEach((node) => node.removeAttribute('id'));
        clone.removeAttribute('id');
        clone.style.width = `${this._width}px`;
        clone.style.height = `${this._height}px`;
        preview.appendChild(clone);

        const label = document.createElement('span');
        label.dataset.deckStageLabel = '';
        const title = slide.getAttribute('data-title') || slide.querySelector('h1, h2, h3')?.textContent?.trim() || '';
        label.innerHTML = `<span>${String(index + 1).padStart(2, '0')} / ${String(this._slides.length).padStart(2, '0')}</span><span>${this._escapeText(title)}</span>`;

        card.append(preview, label);
        card.addEventListener('click', () => {
          this.goTo(index);
          this.toggleOverview(false);
        });
        grid.appendChild(card);
      });

      requestAnimationFrame(() => {
        grid.querySelectorAll('[data-deck-stage-preview]').forEach((preview) => {
          const clone = preview.firstElementChild;
          if (clone) clone.style.transform = `scale(${preview.clientWidth / this._width})`;
        });
        grid.querySelector('[aria-current="true"]')?.focus();
      });
    }

    _escapeText(value) {
      const span = document.createElement('span');
      span.textContent = value;
      return span.innerHTML;
    }

    _handleHash() {
      const match = location.hash.match(/^#slide-(\d+)$/);
      if (match) {
        const idx = parseInt(match[1]) - 1;
        if (idx >= 0 && idx < this._slides.length) {
          this.goTo(idx);
        }
      }
    }

    _restoreSlide() {
      const hashMatch = location.hash.match(/^#slide-(\d+)$/);
      if (hashMatch) {
        const index = parseInt(hashMatch[1], 10) - 1;
        if (index >= 0 && index < this._slides.length) {
          this._currentSlide = index;
          return;
        }
      }
      try {
        const stored = localStorage.getItem(this._storageKey);
        if (stored !== null) {
          const idx = parseInt(stored);
          if (idx >= 0 && idx < this._slides.length) {
            this._currentSlide = idx;
          }
        }
      } catch (e) {}
    }

    _saveSlide() {
      try {
        localStorage.setItem(this._storageKey, String(this._currentSlide));
      } catch (e) {}
    }

    _updateScale() {
      if (this.hasAttribute('noscale')) {
        const stage = this.shadowRoot.getElementById('stage');
        stage.style.transform = 'none';
        stage.style.top = '0';
        stage.style.left = '0';
        return;
      }

      const stage = this.shadowRoot.getElementById('stage');
      if (!stage) return;

      const viewportW = window.innerWidth;
      const viewportH = window.innerHeight;
      const scale = Math.min(viewportW / this._width, viewportH / this._height);
      const scaledW = this._width * scale;
      const scaledH = this._height * scale;
      const offsetX = (viewportW - scaledW) / 2;
      const offsetY = (viewportH - scaledH) / 2;

      stage.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
      stage.style.top = '0';
      stage.style.left = '0';
    }

    _updateDisplay() {
      this._slides.forEach((slide, idx) => {
        slide.classList.toggle('active', idx === this._currentSlide);
      });

      const counter = this.shadowRoot.getElementById('counter');
      if (counter) {
        counter.textContent = `${this._currentSlide + 1} / ${this._slides.length}`;
      }
      const progress = this.shadowRoot.getElementById('progress');
      if (progress) {
        const ratio = this._slides.length > 0 ? (this._currentSlide + 1) / this._slides.length : 0;
        progress.style.width = `${ratio * 100}%`;
      }

      const nextHash = `#slide-${this._currentSlide + 1}`;
      if (location.hash !== nextHash) history.replaceState(null, '', nextHash);

      this._updateScale();

      try {
        window.postMessage({
          slideIndexChanged: this._currentSlide,
          totalSlides: this._slides.length
        }, '*');
      } catch (e) {}

      try {
        if (window.parent && window.parent !== window) {
          window.parent.postMessage({
            slideIndexChanged: this._currentSlide,
            totalSlides: this._slides.length
          }, '*');
        }
      } catch (e) {}

      this.dispatchEvent(new CustomEvent('deckslidechange', {
        bubbles: true,
        detail: { index: this._currentSlide, total: this._slides.length }
      }));
    }

    _setupPrintStyles() {
      const printStyle = document.createElement('style');
      printStyle.textContent = `
        @media print {
          @page {
            size: ${this._width}px ${this._height}px;
            margin: 0;
          }
          body {
            margin: 0;
            padding: 0;
          }
          deck-stage {
            position: static !important;
          }
          deck-stage > section {
            display: block !important;
            position: relative !important;
            width: ${this._width}px !important;
            height: ${this._height}px !important;
            page-break-after: always;
            overflow: hidden;
          }
          deck-stage > section:last-child {
            page-break-after: auto;
          }
        }
      `;
      document.head.appendChild(printStyle);
    }

    next() {
      if (this._currentSlide < this._slides.length - 1) {
        this._currentSlide++;
        this._saveSlide();
        this._updateDisplay();
      }
    }

    prev() {
      if (this._currentSlide > 0) {
        this._currentSlide--;
        this._saveSlide();
        this._updateDisplay();
      }
    }

    goTo(idx) {
      if (idx >= 0 && idx < this._slides.length) {
        this._currentSlide = idx;
        this._saveSlide();
        this._updateDisplay();
      }
    }

    toggleOverview(force) {
      const next = typeof force === 'boolean' ? force : !this._overviewOpen;
      this._overviewOpen = next;
      if (next) this._buildOverview();
      if (this._overview) this._overview.dataset.open = String(next);
      this.shadowRoot.getElementById('overviewButton')?.setAttribute('aria-pressed', String(next));
      this.dispatchEvent(new CustomEvent('deckoverviewchange', {
        bubbles: true,
        detail: { open: next }
      }));
    }

    async toggleFullscreen() {
      try {
        if (document.fullscreenElement) await document.exitFullscreen();
        else await document.documentElement.requestFullscreen();
      } catch (error) {
        this.dispatchEvent(new CustomEvent('deckfullscreenerror', {
          bubbles: true,
          detail: { message: error?.message || String(error) }
        }));
      }
    }

    get currentSlide() {
      return this._currentSlide;
    }

    get totalSlides() {
      return this._slides.length;
    }
  }

  customElements.define('deck-stage', DeckStage);

  window.DeckStage = DeckStage;
})();
