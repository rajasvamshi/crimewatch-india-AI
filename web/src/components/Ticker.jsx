import { useMemo } from 'react';
import { useLang, rgb } from '../i18n.js';
import { timeAgo } from '../data.js';

/** Endless news-wire strip of the latest reports with a headline. Hover or focus pauses it. */
export default function Ticker({ items, go }) {
  const { cat, lang, t } = useLang();
  const rows = useMemo(() => (items || []).filter((i) => i.title).sort((a, b) => b.ts.localeCompare(a.ts)).slice(0, 24), [items]);
  if (!rows.length) return null;
  const strip = (dup) => rows.map((i) => (
    <button key={(dup ? 'b' : 'a') + i.id} tabIndex={dup ? -1 : 0} aria-hidden={dup || undefined} onClick={() => go('map', i.place.split(',')[0])}>
      <i style={{ background: rgb(i.category) }} /><b>{cat(i.category)}</b><span>{i.title}</span><em>{i.place.split(',')[0]} · {timeAgo(i.ts, lang)}</em>
    </button>));
  return (
    <div className="ticker" role="region" aria-label={t('latest')}>
      <div className="ticker-label"><span className="pulse" />{t('wire')}</div>
      <div className="ticker-track"><div className="ticker-move">{strip(false)}{strip(true)}</div></div>
    </div>
  );
}
