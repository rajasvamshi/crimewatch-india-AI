import { useEffect, useMemo, useState } from 'react';
import { ScatterplotLayer } from '@deck.gl/layers';
import MapView from '../components/MapView.jsx';
import { useJson, fmtIST } from '../data.js';
import { useLang, rgb } from '../i18n.js';
import { useReveal, useCountUp } from '../motion.js';
import { HELPLINES, SCAMS, AUDIT, playbook } from '../prevent-content.js';

const SCAM_HI = {
  'Digital arrest': 'डिजिटल अरेस्ट', 'Investment and trading': 'निवेश और ट्रेडिंग', 'Job and task': 'नौकरी और टास्क',
  'Cyber slavery abroad': 'विदेश में साइबर ग़ुलामी', Sextortion: 'सेक्सटॉर्शन', 'Loan app': 'लोन ऐप',
  'Bank, KYC and OTP': 'बैंक, KYC और OTP', 'Courier and parcel': 'कूरियर और पार्सल', 'Matrimonial and romance': 'वैवाहिक और रोमांस',
  'Lottery and prize': 'लॉटरी और इनाम', 'Fake government scheme': 'नकली सरकारी योजना',
};
const LEVEL_RGB = { high: [255, 59, 48], elevated: [255, 176, 32], normal: [77, 163, 255] };
const PREVENT_VIEW = { center: [80.5, 22.5], zoom: 3.9, pitch: 30, bearing: 0 };

const store = {
  get: (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
  set: (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } },
};
const Num = ({ to }) => { const v = useCountUp(to); return <>{to == null ? '–' : Math.round(v)}</>; };
const short = (name) => name.split(',')[0];

function ScamCard({ s, row, lang, t }) {
  const [open, setOpen] = useState(false);
  const c = SCAMS[s][lang === 'hi' ? 'hi' : 'en'];
  const live = row && row.this_week > 0;
  return (
    <article className={`scam spot${live ? ' live' : ''}${open ? ' open' : ''}`}>
      <header>
        <span className="scam-ic" aria-hidden="true">{SCAMS[s].icon}</span>
        <h4>{lang === 'hi' ? SCAM_HI[s] : s}</h4>
        {live ? <span className={`pill tr-${row.trend}`}>{t(`tr_${row.trend}`)}</span> : null}
      </header>
      <div className="scam-n">
        {live ? <><b className="mono">{row.this_week}</b> {t('pv_this_week')} <small>· {row.last_week} {t('pv_last_week')}</small></>
          : <small>{t('pv_quiet')}</small>}
      </div>
      <p>{c.how}</p>
      {open && (
        <div className="scam-more">
          <h5>{t('pv_flags')}</h5>
          <ul>{c.flags.map((f) => <li key={f}>{f}</li>)}</ul>
          {row?.examples?.length > 0 && <>
            <h5>{t('pv_seen')}</h5>
            <ul className="ex">{row.examples.map((e) => (
              <li key={e.url}><a href={e.url} target="_blank" rel="noopener noreferrer">{e.title}</a><small>{short(e.place)} · {fmtIST(e.ts)}</small></li>))}</ul></>}
        </div>)}
      <div className="scam-do"><b>{t('pv_do')}:</b> {c.act}</div>
      <button className="link" onClick={() => setOpen(!open)} aria-expanded={open}>{open ? t('pv_less') : t('pv_more')} {open ? '↑' : '↓'}</button>
    </article>
  );
}

function Audit({ lang, t }) {
  const [done, setDone] = useState(() => new Set());
  const [copied, setCopied] = useState(false);
  const all = AUDIT.flatMap((g) => g.items);
  const pct = Math.round((done.size / all.length) * 100);
  const hi = lang === 'hi';
  const todo = all.filter(([id]) => !done.has(id)).map(([, en, h]) => (hi ? h : en));
  const text = `${t('pv_todo')} (${pct}% ${t('pv_score')})\n${todo.map((x) => `☐ ${x}`).join('\n')}\n\n112 · 1930 · 181 · 1098\n${window.location.href.split('#')[0]}#/prevent`;
  const toggle = (id) => setDone((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n; });
  const copy = async () => {
    try { await navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1800); } catch { /* clipboard blocked */ }
  };
  const share = async () => { try { await navigator.share({ title: t('pv_todo'), text }); } catch { /* cancelled */ } };
  const R = 52, C = 2 * Math.PI * R;
  return (
    <div className="audit">
      <div className="audit-score">
        <svg viewBox="0 0 120 120" role="img" aria-label={`${pct}%`}>
          <circle cx="60" cy="60" r={R} className="track" />
          <circle cx="60" cy="60" r={R} className="val" strokeDasharray={C} strokeDashoffset={C * (1 - pct / 100)} />
          <text x="60" y="58" textAnchor="middle" className="n">{pct}%</text>
          <text x="60" y="78" textAnchor="middle" className="l">{t('pv_score')}</text>
        </svg>
        <div className="audit-actions">
          <button className="btn primary small" onClick={copy} disabled={!todo.length}>{copied ? `✓ ${t('pv_copied')}` : t('pv_copy')}</button>
          {typeof navigator !== 'undefined' && navigator.share && <button className="btn ghost small" onClick={share}>{t('pv_share')}</button>}
          {!todo.length && <p className="cap">{t('pv_all_done')}</p>}
        </div>
      </div>
      <div className="audit-groups">
        {AUDIT.map((g) => (
          <fieldset key={g.id}>
            <legend>{hi ? g.hi : g.en}</legend>
            {g.items.map(([id, en, h]) => (
              <label key={id} className={done.has(id) ? 'on' : ''}>
                <input type="checkbox" checked={done.has(id)} onChange={() => toggle(id)} />
                <span className="box" aria-hidden="true" />{hi ? h : en}
              </label>))}
          </fieldset>))}
      </div>
    </div>
  );
}

export default function Prevent({ go }) {
  const { t, cat, lang } = useLang();
  const [pv] = useJson('prevent.json');
  const [follow, setFollow] = useState(() => store.get('cw-follow', []));
  const [seen] = useState(() => store.get('cw-follow-seen', {}));
  const [sel, setSel] = useState(null);
  const [flyTo, setFlyTo] = useState(null);
  const [showAll, setShowAll] = useState(false);
  useReveal([!!pv]);

  const fc = pv?.forecast || [];
  const byName = useMemo(() => new Map(fc.map((r) => [r.name, r])), [fc]);
  const scamRows = useMemo(() => new Map((pv?.scams || []).map((r) => [r.type, r])), [pv]);
  const scamOrder = useMemo(() => Object.keys(SCAMS).sort((a, b) => (scamRows.get(b)?.this_week || 0) - (scamRows.get(a)?.this_week || 0)), [scamRows]);
  const place = sel || fc[0];
  const play = playbook(place?.top_category, lang);
  const highs = fc.filter((r) => r.level === 'high').length;
  const scamWeek = (pv?.scams || []).reduce((a, r) => a + r.this_week, 0);
  const histDays = pv?.method?.history_days ?? 30;

  // remember what the user has seen, so the next visit can flag new reports
  useEffect(() => {
    if (!pv) return;
    store.set('cw-follow-seen', Object.fromEntries(follow.map((n) => [n, byName.get(n)?.reports_7d ?? 0])));
  }, [pv, follow, byName]);
  const toggleFollow = (name) => setFollow((f) => { const n = f.includes(name) ? f.filter((x) => x !== name) : [...f, name]; store.set('cw-follow', n); return n; });
  const alerts = follow.map((n) => ({ name: n, r: byName.get(n), fresh: Math.max(0, (byName.get(n)?.reports_7d ?? 0) - (seen[n] ?? byName.get(n)?.reports_7d ?? 0)) }))
    .filter((a) => a.r && (a.r.level !== 'normal' || a.fresh > 0));

  const pick = (r) => { setSel(r); setFlyTo({ center: [r.lon, r.lat], zoom: 8.5, pitch: 50 }); };

  const layers = useMemo(() => {
    const maxE = Math.max(1, ...fc.map((r) => r.expected_7d));
    const size = (r) => 5 + Math.sqrt(r.expected_7d / maxE) * 30;
    return [
      new ScatterplotLayer({ id: 'risk-halo', data: fc.filter((r) => r.level !== 'normal'), getPosition: (r) => [r.lon, r.lat],
        radiusUnits: 'pixels', getRadius: (r) => size(r) * 1.9, getFillColor: (r) => [...LEVEL_RGB[r.level], 38], stroked: false }),
      new ScatterplotLayer({ id: 'risk', data: fc, getPosition: (r) => [r.lon, r.lat], radiusUnits: 'pixels', getRadius: size,
        getFillColor: (r) => [...LEVEL_RGB[r.level], r === place ? 255 : 190], stroked: true,
        getLineColor: (r) => (r === place ? [255, 255, 255, 255] : [0, 0, 0, 120]), lineWidthUnits: 'pixels', getLineWidth: (r) => (r === place ? 2.5 : 1),
        pickable: true, onClick: ({ object }) => object && pick(object), updateTriggers: { getFillColor: place?.name, getLineColor: place?.name, getLineWidth: place?.name } }),
    ];
  }, [fc, place]);

  const list = fc.filter((r) => showAll || r.level !== 'normal').slice(0, showAll ? 60 : 24);
  const rss = './data/alerts.xml';

  return (
    <main id="main" className="page prevent">
      <div className="eyebrow">{t('pv_eyebrow')}</div>
      <h1 className="display">{t('pv_title')}</h1>
      <p className="sub">{t('pv_sub')}</p>

      <section className="helplines reveal" aria-label={t('pv_help_t')}>
        {HELPLINES.map((h) => (
          <a key={h.n} href={`tel:${h.n}`} className="hl spot"><b className="mono">{h.n}</b><span>{lang === 'hi' ? h.hi : h.en}</span></a>))}
        <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer" className="hl spot"><b>cybercrime.gov.in</b><span>{lang === 'hi' ? 'ऑनलाइन शिकायत' : 'Report online'}</span></a>
      </section>

      {alerts.length > 0 && (
        <section className="my-alerts reveal" aria-live="polite">
          <h3>{t('pv_alert_t')}</h3>
          {alerts.map((a) => (
            <button key={a.name} className={`alert-row lv-${a.r.level}`} onClick={() => pick(a.r)}>
              <span className="dot" aria-hidden="true" /><b>{short(a.name)}</b>
              {a.r.level !== 'normal' && <span>{t(a.r.level === 'high' ? 'pv_alert_high' : 'pv_alert_el')}</span>}
              {a.fresh > 0 && <span className="mono">+{a.fresh} {t('pv_alert_new')}</span>}
            </button>))}
        </section>)}

      <div className="kpis reveal">
        <div className="kpi spot"><div className="n mono"><Num to={pv ? scamWeek : null} /></div><div className="l">{t('k_scams')}</div></div>
        <div className="kpi spot"><div className="n mono"><Num to={pv ? highs : null} /></div><div className="l">{t('k_high')}</div></div>
        <div className="kpi spot"><div className="n mono"><Num to={pv ? pv.spikes.length : null} /></div><div className="l">{t('k_spikes')}</div></div>
        <div className="kpi spot"><div className="n mono"><Num to={follow.length} /></div><div className="l">{t('k_follow')}</div></div>
      </div>

      {/* ---------- SCAM RADAR ---------- */}
      <section className="pv-sec reveal" aria-labelledby="scam-t">
        <div className="pv-head"><h2 id="scam-t" className="display">{t('pv_scam_t')}</h2><p className="sub">{t('pv_scam_s')}</p></div>
        <div className="scams">{scamOrder.map((s) => <ScamCard key={s} s={s} row={scamRows.get(s)} lang={lang} t={t} />)}</div>
      </section>

      {/* ---------- FORECAST ---------- */}
      <section className="pv-sec reveal" aria-labelledby="fc-t">
        <div className="pv-head">
          <h2 id="fc-t" className="display">{t('pv_fc_t')} <span className="badge hot">{t('pv_fc_badge')}</span></h2>
          <p className="sub">{t('pv_fc_s')}</p>
          {histDays < 7 && <p className="warn">{t('pv_fc_short').replace('{d}', Math.max(1, Math.round(histDays)))}</p>}
        </div>
        <div className="fc-grid">
          <div className="fc-map panel">
            <MapView layers={layers} view={PREVENT_VIEW} flyTo={flyTo} />
            <div className="fc-legend float">{['high', 'elevated', 'normal'].map((l) => (
              <span key={l}><i style={{ background: `rgb(${LEVEL_RGB[l].join(',')})` }} />{t(`lv_${l}`)}</span>))}</div>
          </div>
          <div className="fc-list panel">
            <ol>
              {list.map((r, k) => (
                <li key={r.name} className={r === place ? 'on' : ''}>
                  <button className="fc-row" onClick={() => pick(r)}>
                    <span className="rk mono">{String(k + 1).padStart(2, '0')}</span>
                    <span className="nm">{short(r.name)}<small>{r.state}</small></span>
                    <span className={`lvl lv-${r.level}`}>{t(`lv_${r.level}`)}</span>
                    <span className="ex mono">~{Math.round(r.expected_7d)}<small>{t('pv_7d')}</small></span>
                  </button>
                </li>))}
            </ol>
            <button className="link" onClick={() => setShowAll(!showAll)}>{showAll ? '↑' : `+ ${fc.length - list.length}`}</button>
          </div>
        </div>

        {place && (
          <div className="play panel spot" aria-live="polite">
            <header>
              <div>
                <div className="eyebrow">{t('pv_play_t')}</div>
                <h3>{short(place.name)} <small>{place.state}</small></h3>
                <div className="why">{place.reasons.map((x) => <span key={x}>{x}</span>)}</div>
              </div>
              <div className="play-tools">
                <span className={`lvl big lv-${place.level}`}>{t(`lv_${place.level}`)} · ~{Math.round(place.expected_7d)} {t('pv_7d')}</span>
                <button className={`btn small ${follow.includes(place.name) ? 'ghost' : 'primary'}`} onClick={() => toggleFollow(place.name)}>
                  {follow.includes(place.name) ? `✓ ${t('pv_following')}` : `+ ${t('pv_follow')}`}</button>
                <button className="btn ghost small" onClick={() => go('map', short(place.name))}>{t('open_map')} →</button>
              </div>
            </header>
            <div className="mixbar">{place.categories.map(([c, v]) => <i key={c} style={{ flex: v, background: rgb(c) }} title={`${cat(c)} ${v}`} />)}</div>
            <div className="play-cols">
              <div><h4>{t('pv_you')}</h4><ul>{play.you.map((x) => <li key={x}>{x}</li>)}</ul></div>
              <div><h4>{t('pv_gov')}</h4><ul>{play.gov.map((x) => <li key={x}>{x}</li>)}</ul></div>
            </div>
          </div>)}
      </section>

      {/* ---------- FOLLOW + ACCURACY ---------- */}
      <div className="intel-grid pv-sec">
        <section className="panel spot reveal">
          <header><h3>{t('pv_follow_t')}</h3><a className="badge" href={rss} target="_blank" rel="noopener noreferrer">RSS ↗</a></header>
          <p className="cap" style={{ marginTop: 0 }}>{t('pv_follow_s')}</p>
          {follow.length === 0 ? <p className="empty">{t('pv_follow_empty')}</p> : (
            <ul className="follow">
              {follow.map((n) => {
                const r = byName.get(n);
                return (
                  <li key={n}>
                    <button className="nm" onClick={() => r && pick(r)}>{short(n)}<small>{r ? `${r.reports_7d} · 7d` : '–'}</small></button>
                    {r && <span className={`lvl lv-${r.level}`}>{t(`lv_${r.level}`)}</span>}
                    <button className="link" onClick={() => toggleFollow(n)} aria-label={`${t('pv_remove')} ${n}`}>×</button>
                  </li>);
              })}
            </ul>)}
          <a className="link" href={rss} target="_blank" rel="noopener noreferrer">{t('pv_rss')} ↗</a>
        </section>

        <section className="panel spot reveal">
          <header><h3>{t('pv_acc_t')}</h3><span className="badge mono">top {pv?.method?.top_n ?? 20}</span></header>
          {pv?.accuracy?.status === 'ok' ? (
            <div className="acc">
              {[['pv_model', pv.accuracy.model_hit, true], ['pv_baseline', pv.accuracy.baseline_hit, false]].map(([k, v, m]) => (
                <div key={k} className="acc-row"><span>{t(k)}</span>
                  <span className="acc-bar"><i style={{ width: `${v * 100}%` }} className={m ? 'm' : ''} /></span>
                  <b className="mono">{Math.round(v * 100)}%</b></div>))}
              <p className="cap">{t('pv_acc_hit')}. {t(pv.accuracy.beats_baseline ? 'pv_acc_win' : 'pv_acc_lose')}</p>
            </div>
          ) : (
            <div className="acc building">
              <div className="acc-steps">{Array.from({ length: 7 }, (_, k) => {
                const first = pv?.accuracy?.first_forecast ? Date.parse(pv.accuracy.first_forecast) : Date.now();
                const d = (Date.now() - first) / 864e5;
                return <i key={k} className={k < d ? 'on' : ''} />;
              })}</div>
              <p>{t('pv_acc_building')}</p>
              {pv?.accuracy?.first_forecast && <p className="cap">{t('pv_acc_first')}: {fmtIST(pv.accuracy.first_forecast)}</p>}
            </div>)}
          <p className="cap">{t('pv_acc_s')}</p>
        </section>
      </div>

      {/* ---------- AUDIT ---------- */}
      <section className="pv-sec reveal" aria-labelledby="audit-t">
        <div className="pv-head"><h2 id="audit-t" className="display">{t('pv_audit_t')}</h2><p className="sub">{t('pv_audit_s')}</p></div>
        <Audit lang={lang} t={t} />
      </section>

      {/* ---------- GUARDRAILS ---------- */}
      <section className="panel reveal methods guard">
        <h3>{t('pv_guard_t')}</h3>
        <ul>{['g1', 'g2', 'g3', 'g4', 'g5'].map((g) => <li key={g}>{t(g)}</li>)}</ul>
      </section>
      {pv && <p className="muted" style={{ marginTop: 24 }}>{t('updated')} {fmtIST(pv.generated_at)} · {t('map_note')}</p>}
    </main>
  );
}
