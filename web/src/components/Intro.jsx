import { useEffect, useState } from 'react';
import { reducedMotion } from '../motion.js';

/*
 * Short opening sequence (about 2.6 s), shown once per browser session. It reads the real
 * numbers from this hour's data, so it doubles as a status check. Skippable with any key,
 * click or tap, and never shown to people who ask for reduced motion.
 */
export default function Intro({ meta, summary, lang }) {
  const seen = (() => { try { return sessionStorage.getItem('cw-intro') === '1'; } catch { return false; } })();
  const [show, setShow] = useState(!seen && !reducedMotion());
  const [step, setStep] = useState(0);
  const [leaving, setLeaving] = useState(false);

  const hi = lang === 'hi';
  const lines = [
    [hi ? 'समाचार स्रोत' : 'NEWS GRAPH', hi ? 'GDELT 2.0 · 65 भाषाएँ' : 'GDELT 2.0 · 65 LANGUAGES'],
    [hi ? 'पुलिस विज्ञप्तियाँ' : 'POLICE RELEASES', 'DELHI POLICE · DAILY'],
    [hi ? 'आधिकारिक आंकड़े' : 'OFFICIAL BASELINE', 'NCRB CRIME IN INDIA 2024'],
    [hi ? 'रिपोर्टें अनुक्रमित' : 'REPORTS INDEXED', summary ? summary.total.toLocaleString('en-IN') : '…'],
    [hi ? 'पिछले 24 घंटे' : 'LAST 24 HOURS', summary ? `${summary.last_24h} · ${summary.states_last_24h} ${hi ? 'राज्य' : 'STATES'}` : '…'],
  ];

  const close = () => {
    try { sessionStorage.setItem('cw-intro', '1'); } catch { /* private mode */ }
    setLeaving(true);
    setTimeout(() => setShow(false), 700);
  };

  useEffect(() => {
    if (!show) return undefined;
    const ids = lines.map((_, i) => setTimeout(() => setStep(i + 1), 350 + i * 360));
    const end = setTimeout(close, 350 + lines.length * 360 + 1000);
    const skip = () => close();
    window.addEventListener('keydown', skip);
    return () => { ids.forEach(clearTimeout); clearTimeout(end); window.removeEventListener('keydown', skip); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show]);

  if (!show) return null;
  return (
    <div className={`intro${leaving ? ' out' : ''}`} onClick={close} role="presentation">
      <div className="intro-grid" aria-hidden="true" />
      <div className="intro-scan" aria-hidden="true" />
      <div className="intro-inner">
        <div className="intro-logo"><span className="dot" />CRIMEWATCH<b>INDIA</b></div>
        <ul className="intro-lines" aria-hidden="true">
          {lines.map(([k, v], i) => (
            <li key={k} className={i < step ? 'on' : ''}><span>{k}</span><i /><b>{i < step ? v : ''}</b><em>{i < step ? 'OK' : ''}</em></li>))}
        </ul>
        <div className="intro-bar"><span style={{ width: `${(step / lines.length) * 100}%` }} /></div>
        <div className="intro-skip">{meta ? `SYNC ${new Date(meta.generated_at).toISOString().slice(0, 16).replace('T', ' ')} UTC · ` : ''}{hi ? 'छोड़ने के लिए टैप करें' : 'TAP TO SKIP'}</div>
      </div>
    </div>
  );
}
