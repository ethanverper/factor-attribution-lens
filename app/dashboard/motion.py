"""Phase 10g: the interaction/motion layer -- implements decision
0015-phase10f-interactivity-and-tools-section.md's spec (tab fade, Results
entrance choreography, per-mark-type data reveals, the allocation slider's
sweep-in, and the three Learning diagrams' scroll-triggered reveals).

GSAP is vendored (self-hosted, `app/static/vendor/gsap.min.js`, not a CDN --
see decision 0015's own flag) and loaded before this module's script. This
module never generates a displayed value: every animated number, bar width,
or curve position is already correct in the server-rendered HTML (`viz.py`,
`diagrams.py`) before any of this runs -- GSAP only tweens *from* a
temporary state *to* that real value (decision 0015's "progressive
enhancement, non-negotiable" rule). Concretely, this means every "hide the
starting state" call below happens in JS immediately before the matching
animation starts, never via server-rendered CSS -- a no-JS or
reduced-motion visitor always sees the final, correct state with zero
flicker and zero dependency on this script running at all.

`prefers-reduced-motion: reduce` is read once via `gsap.matchMedia()` into a
shared `FL_REDUCED` flag (decision 0015's accessibility rule): every reveal
function below checks it first and, when true, does nothing beyond what the
server already rendered -- no stuck mid-animation states, ever.
"""
from __future__ import annotations

GSAP_VENDOR_SCRIPT_TAG = '<script src="/static/vendor/gsap.min.js"></script>'

MOTION_SCRIPT = """
(function () {
  if (typeof gsap === 'undefined') return; // vendored file failed to load -- fail open to plain SSR HTML

  var FL_REDUCED = false;
  var mm = gsap.matchMedia();
  mm.add('(prefers-reduced-motion: reduce)', function () {
    FL_REDUCED = true;
    return function () { FL_REDUCED = false; };
  });

  // ---- Tab fade (decision 0015 S2) ----------------------------------------
  window.__flTabFadeIn = function (panel) {
    if (!panel) return;
    if (FL_REDUCED) return;
    gsap.fromTo(panel, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.12, ease: 'power1.out' });
  };

  // ---- Stat-tile count-up (decision 0015 S4) ------------------------------
  function startCountUps(root) {
    if (FL_REDUCED) return;
    var els = root.querySelectorAll('[data-count-target]');
    els.forEach(function (el) {
      if (el.__flCounted) return;
      el.__flCounted = true;
      var target = parseFloat(el.getAttribute('data-count-target'));
      if (isNaN(target)) return;
      var decimals = parseInt(el.getAttribute('data-count-decimals') || '0', 10);
      var suffix = el.getAttribute('data-count-suffix') || '';
      var signed = el.getAttribute('data-count-signed') === 'true';
      var finalText = el.textContent; // the true SSR value -- restored verbatim on completion
      var proxy = { v: 0 };
      gsap.to(proxy, {
        v: target,
        duration: 0.55,
        ease: 'power2.out',
        onUpdate: function () {
          var sign = signed && proxy.v > 0 ? '+' : '';
          el.textContent = sign + proxy.v.toFixed(decimals) + suffix;
        },
        onComplete: function () { el.textContent = finalText; },
      });
    });
  }

  // ---- Diverging-bar / split-bar reveal (decision 0015 S4) ----------------
  function revealBarsIn(svg) {
    if (FL_REDUCED || !svg || svg.__flRevealed) return;
    svg.__flRevealed = true;
    var bars = svg.querySelectorAll('.viz-bar-reveal');
    var whiskers = svg.querySelectorAll('.viz-whisker-reveal');
    if (!bars.length) return;
    gsap.set(bars, { scaleX: 0 });
    gsap.set(whiskers, { autoAlpha: 0 });
    gsap.to(bars, {
      scaleX: 1,
      duration: 0.45,
      ease: 'power2.out',
      stagger: 0.06,
      onComplete: function () {
        var bar = this.targets()[0];
        var order = bar.getAttribute('data-reveal-order');
        var whisker = svg.querySelector('.viz-whisker-reveal[data-reveal-order="' + order + '"]');
        if (whisker) gsap.to(whisker, { autoAlpha: 1, duration: 0.1 });
      },
    });
  }

  // ---- Frontier curve draw-in + marker pop-in (decision 0015 S4) ----------
  function revealFrontierIn(svg) {
    if (FL_REDUCED || !svg || svg.__flRevealed) return;
    svg.__flRevealed = true;
    var line = svg.querySelector('.viz-frontier-polyline');
    var markers = svg.querySelectorAll('.viz-marker-pop');
    var hasLine = line && (line.getAttribute('points') || '').trim().length > 0;
    function popMarkers() {
      if (!markers.length) return;
      gsap.set(markers, { scale: 0.8, autoAlpha: 0 });
      gsap.to(markers, { scale: 1, autoAlpha: 1, duration: 0.35, ease: 'back.out(1.4)', stagger: 0.08 });
    }
    if (hasLine) {
      var len = line.getTotalLength();
      gsap.set(line, { strokeDasharray: len, strokeDashoffset: len });
      gsap.to(line, { strokeDashoffset: 0, duration: 0.5, ease: 'power2.out', onComplete: popMarkers });
    } else {
      popMarkers();
    }
  }

  // ---- Results section reveal: tiles -> chart(s) (decision 0015 S3/S4) ---
  function revealSection(section) {
    if (!section || section.__flRevealed) return;
    section.__flRevealed = true;
    if (FL_REDUCED) return; // SSR content is already the correct final state
    var tiles = section.querySelectorAll('.viz-stat-tile');
    if (tiles.length) {
      gsap.fromTo(
        tiles,
        { autoAlpha: 0, y: 10 },
        { autoAlpha: 1, y: 0, duration: 0.22, stagger: 0.04, ease: 'power2.out' }
      );
    }
    startCountUps(section);
    section.querySelectorAll('svg[aria-label="Diverging bar chart"]').forEach(revealBarsIn);
    section.querySelectorAll('svg[aria-label="Risk attribution split"]').forEach(revealBarsIn);
    section.querySelectorAll('svg[aria-label="Efficient frontier chart"]').forEach(revealFrontierIn);
  }

  function initResultsEntrance() {
    var freshness = document.querySelector('.freshness-banner');
    if (!freshness) return; // Inputs tab / empty-results state -- nothing to choreograph
    var s1 = document.querySelector('[data-reveal-section="1"]');
    var s2 = document.querySelector('[data-reveal-section="2"]');
    var s3 = document.querySelector('[data-reveal-section="3"]');
    if (!FL_REDUCED) {
      gsap.fromTo(freshness, { autoAlpha: 0, y: 8 }, { autoAlpha: 1, y: 0, duration: 0.26, ease: 'power2.out' });
    }
    if (s1) revealSection(s1); // fires immediately on arrival, per decision 0015 S3
    [s2, s3].forEach(function (section) {
      if (!section) return;
      if (FL_REDUCED) { revealSection(section); return; }
      if (!('IntersectionObserver' in window)) { revealSection(section); return; }
      var io = new IntersectionObserver(
        function (entries, obs) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              revealSection(entry.target);
              obs.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.3 }
      );
      io.observe(section);
    });
  }

  // ---- Learning diagrams: scroll-triggered reveal, once (decision 0015 S6) --
  // The *only* scroll-linked motion in the app -- deliberately not applied to
  // Glossary/References/Tools & Technologies (they're scanning content, never
  // carry `data-diagram`, so this code never touches them).
  function revealCapmDiagram(figure) {
    var items = figure.querySelectorAll('.diag-reveal-item');
    gsap.set(items, { autoAlpha: 0, y: 8 });
    gsap.to(items, { autoAlpha: 1, y: 0, duration: 0.3, stagger: 0.15, ease: 'power2.out' });
  }

  function revealCiDiagram(figure) {
    var bars = figure.querySelectorAll('.diag-ci-bar');
    var whiskerLines = figure.querySelectorAll('.diag-ci-whisker-line');
    var whiskerGroups = figure.querySelectorAll('.diag-ci-whisker');
    var verdicts = figure.querySelectorAll('.diag-ci-verdict');
    gsap.set(bars, { autoAlpha: 0, scale: 0.85, transformOrigin: '0% 50%' });
    gsap.set(whiskerGroups, { autoAlpha: 0 });
    gsap.set(verdicts, { autoAlpha: 0 });
    whiskerLines.forEach(function (line) {
      var len = line.getTotalLength();
      gsap.set(line, { strokeDasharray: len, strokeDashoffset: len });
    });
    // Absolute timeline positions (seconds), not relative "-=" offsets -- one row's sequence
    // is point estimate -> whisker draws outward -> verdict, per decision 0015 S6; the two
    // rows (Example A / B) run the same sequence 0.15s apart via `stagger`.
    var tl = gsap.timeline();
    tl.to(bars, { autoAlpha: 1, scale: 1, duration: 0.25, stagger: 0.15, ease: 'power2.out' }, 0);
    tl.to(whiskerGroups, { autoAlpha: 1, duration: 0.01, stagger: 0.15 }, 0.2);
    tl.to(whiskerLines, { strokeDashoffset: 0, duration: 0.3, stagger: 0.15, ease: 'power2.out' }, 0.2);
    tl.to(verdicts, { autoAlpha: 1, duration: 0.2, stagger: 0.15 }, 0.5);
  }

  function revealFrontierDiagram(figure) {
    var curve = figure.querySelector('.diag-frontier-curve');
    var current = figure.querySelector('.diag-frontier-current');
    var arrows = figure.querySelectorAll('.diag-frontier-arrow');
    var tl = gsap.timeline();
    if (curve) {
      var len = curve.getTotalLength();
      gsap.set(curve, { strokeDasharray: len, strokeDashoffset: len });
      tl.to(curve, { strokeDashoffset: 0, duration: 0.45, ease: 'power2.out' });
    }
    if (current) {
      gsap.set(current, { autoAlpha: 0, scale: 0.7 });
      tl.to(current, { autoAlpha: 1, scale: 1, duration: 0.3, ease: 'back.out(1.4)' }, curve ? '-=0.1' : 0);
    }
    if (arrows.length) {
      gsap.set(arrows, { autoAlpha: 0, scale: 0.6 });
      tl.to(arrows, { autoAlpha: 1, scale: 1, duration: 0.3, ease: 'power2.out', stagger: 0.15 }, '-=0.05');
    }
  }

  function revealDiagram(figure) {
    if (FL_REDUCED || figure.__flRevealed) return;
    figure.__flRevealed = true;
    var kind = figure.getAttribute('data-diagram');
    if (kind === 'capm') revealCapmDiagram(figure);
    else if (kind === 'ci') revealCiDiagram(figure);
    else if (kind === 'frontier') revealFrontierDiagram(figure);
  }

  function initLearningDiagramReveal() {
    var figures = document.querySelectorAll('[data-diagram]');
    if (!figures.length) return;
    if (FL_REDUCED || !('IntersectionObserver' in window)) {
      figures.forEach(function (f) { f.__flRevealed = true; }); // leave SSR final state as-is
      return;
    }
    var io = new IntersectionObserver(
      function (entries, obs) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            revealDiagram(entry.target);
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.4 }
    );
    figures.forEach(function (f) { io.observe(f); });
  }

  // ---- Allocation slider: paint, two-way bind, sweep-tween (decision 0015 S5) --
  function paintRange(range) {
    var min = parseFloat(range.min) || 0;
    var max = parseFloat(range.max) || 100;
    var val = Math.min(max, Math.max(min, parseFloat(range.value) || 0));
    var pct = max > min ? ((val - min) / (max - min)) * 100 : 0;
    range.style.background =
      'linear-gradient(to right, var(--signal) ' + pct + '%, var(--border) ' + pct + '%)';
  }

  window.__flInitWeightControls = function (root) {
    root.querySelectorAll('[data-weight-range]').forEach(function (range) {
      if (range.__flBound) return;
      range.__flBound = true;
      var row = range.closest('.holding-row');
      var number = row ? row.querySelector('input[name="weight"]') : null;
      paintRange(range);
      range.addEventListener('input', function () {
        if (!number) return;
        number.value = range.value;
        paintRange(range);
        number.dispatchEvent(new Event('input', { bubbles: true }));
      });
    });
  };

  window.__flSyncWeightRange = function (numberInput) {
    var row = numberInput.closest('.holding-row');
    var range = row ? row.querySelector('[data-weight-range]') : null;
    if (!range) return;
    var v = parseFloat(numberInput.value);
    if (!isNaN(v)) range.value = Math.min(100, Math.max(0, v));
    paintRange(range);
  };

  window.__flTweenWeight = function (row, newVal) {
    var number = row.querySelector('input[name="weight"]');
    var range = row.querySelector('[data-weight-range]');
    if (!number) return;
    var oldVal = parseFloat(number.value) || 0;
    function applyFinal() {
      number.value = newVal;
      if (range) { range.value = Math.min(100, Math.max(0, newVal)); paintRange(range); }
      if (window.__flRecalcAlloc) window.__flRecalcAlloc();
    }
    if (FL_REDUCED) { applyFinal(); return; }
    var proxy = { v: oldVal };
    gsap.to(proxy, {
      v: newVal,
      duration: 0.15,
      ease: 'power1.out',
      onUpdate: function () {
        number.value = Math.round(proxy.v * 100) / 100;
        if (range) { range.value = Math.min(100, Math.max(0, proxy.v)); paintRange(range); }
        if (window.__flRecalcAlloc) window.__flRecalcAlloc();
      },
      onComplete: applyFinal,
    });
  };

  window.__flInitWeightControls(document);
  initResultsEntrance();
  initLearningDiagramReveal();
})();
"""
