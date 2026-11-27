import { useEffect, useRef, useState } from 'react';

export const reducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

/** Seconds since mount, updated every animation frame (frozen when the user prefers less motion). */
export function useClock(active = true) {
  const [t, setT] = useState(0);
  useEffect(() => {
    if (!active || reducedMotion()) return undefined;
    let raf, last = 0;
    const t0 = performance.now();
    const tick = (now) => {
      if (now - last > 33) { last = now; setT((now - t0) / 1000); } // ~30 fps is plenty for map rings
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [active]);
  return t;
}

/** Cards light up under the pointer (CSS reads --mx / --my) and tilt slightly toward it. */
export function useSpotlight() {
  useEffect(() => {
    const on = (e) => {
      const el = e.target.closest?.('.spot');
      if (!el) return;
      const r = el.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      el.style.setProperty('--mx', `${x * 100}%`);
      el.style.setProperty('--my', `${y * 100}%`);
      if (el.classList.contains('tilt') && !reducedMotion()) {
        el.style.setProperty('--rx', `${(0.5 - y) * 6}deg`);
        el.style.setProperty('--ry', `${(x - 0.5) * 8}deg`);
      }
    };
    const off = (e) => {
      const el = e.target.closest?.('.tilt');
      if (el && !el.contains(e.relatedTarget)) { el.style.setProperty('--rx', '0deg'); el.style.setProperty('--ry', '0deg'); }
    };
    window.addEventListener('pointermove', on, { passive: true });
    window.addEventListener('pointerout', off, { passive: true });
    return () => { window.removeEventListener('pointermove', on); window.removeEventListener('pointerout', off); };
  }, []);
}

/** Adds .in to .reveal elements as they scroll into view. */
export function useReveal(deps = []) {
  useEffect(() => {
    const els = document.querySelectorAll('.reveal:not(.in)');
    if (reducedMotion()) { els.forEach((e) => e.classList.add('in')); return undefined; }
    const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && e.target.classList.add('in')), { threshold: 0.15 });
    els.forEach((e) => io.observe(e));
    return () => io.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}

/** Index of the story step currently in the middle of the screen. */
export function useActiveStep(count) {
  const refs = useRef([]);
  const [active, setActive] = useState(0);
  useEffect(() => {
    const io = new IntersectionObserver((es) => {
      es.forEach((e) => { if (e.isIntersecting) setActive(Number(e.target.dataset.step)); });
    }, { rootMargin: '-45% 0px -45% 0px' });
    refs.current.slice(0, count).forEach((el) => el && io.observe(el));
    return () => io.disconnect();
  }, [count]);
  return [active, (i) => (el) => { refs.current[i] = el; }];
}

/** Animated number that eases to its target. */
export function useCountUp(to, ms = 1400) {
  const [v, setV] = useState(0);
  useEffect(() => {
    if (to == null) return undefined;
    if (reducedMotion()) { setV(to); return undefined; }
    const t0 = performance.now();
    let raf;
    const tick = (t) => { const p = Math.min(1, (t - t0) / ms); setV(to * (1 - (1 - p) ** 3)); if (p < 1) raf = requestAnimationFrame(tick); };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [to, ms]);
  return v;
}
