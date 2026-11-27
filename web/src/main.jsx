import { StrictMode, useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import { LangContext, makeLang } from './i18n.js';
import { useJson, timeAgo } from './data.js';
import Home from './pages/Home.jsx';
import LiveMap from './pages/LiveMap.jsx';
import Trends from './pages/Trends.jsx';
import About from './pages/About.jsx';
import Intel from './pages/Intel.jsx';
import Intro from './components/Intro.jsx';
import { useSpotlight } from './motion.js';

const ROUTES = ['home', 'map', 'intel', 'trends', 'about'];
const parse = () => {
  const [r, q] = window.location.hash.replace(/^#\/?/, '').split('?q=');
  return { route: ROUTES.includes(r) ? r : 'home', q: q ? decodeURIComponent(q) : '' };
};

function App() {
  const [{ route, q }, setLoc] = useState(parse);
  const [lang, setLang] = useState(() => { try { return localStorage.getItem('cw-lang') || 'en'; } catch { return 'en'; } });
  const L = useMemo(() => makeLang(lang), [lang]);
  const [meta] = useJson('meta.json');
  const [sum] = useJson('summary.json');
  const [scrolled, setScrolled] = useState(false);
  useSpotlight();
  useEffect(() => { const on = () => setScrolled(window.scrollY > 40); on(); window.addEventListener('scroll', on, { passive: true }); return () => window.removeEventListener('scroll', on); }, []);

  useEffect(() => { const on = () => setLoc(parse()); window.addEventListener('hashchange', on); return () => window.removeEventListener('hashchange', on); }, []);
  useEffect(() => { document.documentElement.lang = lang; try { localStorage.setItem('cw-lang', lang); } catch { /* private mode */ } }, [lang]);
  useEffect(() => { window.scrollTo(0, 0); }, [route]);

  const go = (r, query) => { window.location.hash = `/${r}${query ? `?q=${encodeURIComponent(query)}` : ''}`; };

  return (
    <LangContext.Provider value={L}>
      <Intro meta={meta} summary={sum} lang={lang} />
      <div className="gov-strip">
        <span><span className="flag" aria-hidden="true" />{L.t('gov')}</span>
        <span className="tools" role="group" aria-label="Language">
          <button aria-pressed={lang === 'en'} onClick={() => setLang('en')}>English</button>
          <button aria-pressed={lang === 'hi'} onClick={() => setLang('hi')} lang="hi">हिन्दी</button>
        </span>
      </div>
      <header className={`header${route === 'home' && !scrolled ? ' clear' : ''}`}>
        <a className="brand" href="#/home"><span className="dot" aria-hidden="true" />CRIMEWATCH<b>INDIA</b></a>
        <nav className="nav" aria-label="Main">
          {ROUTES.map((r) => (
            <a key={r} href={`#/${r}`} aria-current={route === r ? 'page' : undefined}>{L.t(`nav_${r}`)}</a>))}
        </nav>
        {meta && <span className="live"><span className="pulse" aria-hidden="true" />{L.t('updated')} {timeAgo(meta.generated_at, lang)}</span>}
      </header>
      {route === 'home' && <main id="main"><Home go={go} /></main>}
      {route === 'map' && <main id="main"><LiveMap key={q} query={q} /></main>}
      {route === 'intel' && <Intel go={go} />}
      {route === 'trends' && <Trends />}
      {route === 'about' && <About />}
      {route !== 'map' && (
        <footer className="footer"><span>{L.t('footer_1')}</span><span>{L.t('footer_2')}</span></footer>)}
    </LangContext.Provider>
  );
}

createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>);
