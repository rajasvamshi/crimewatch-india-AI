import { useJson, fmtIST } from '../data.js';
import { useLang } from '../i18n.js';

const SOURCES = [
  {
    name: 'News reports (GDELT 2.0)', fresh: 'Every hour (GDELT updates every 15 minutes)', cover: 'All India, English and Indian-language outlets',
    where: 'City or state centre named in the report', url: 'https://www.gdeltproject.org/',
    means: 'A crime was reported in the news. One crime can appear in several outlets; automatic tagging can be wrong.',
  },
  {
    name: 'Delhi Police press releases', fresh: 'Daily', cover: 'Delhi', where: 'Police district centre',
    url: 'https://delhipolice.gov.in/newpressrelease',
    means: 'Cases the police chose to publicise, mostly arrests and recoveries. Not all crime in Delhi.',
  },
  {
    name: 'NCRB Crime in India', fresh: 'Yearly; 2024 edition released May 2026', cover: 'All India, 36 States/UTs, 19 metro cities',
    where: 'State and city totals', url: 'https://www.ncrb.gov.in/',
    means: 'Official count of cognizable crimes registered by police. The trusted baseline for comparisons.',
  },
];

export default function About() {
  const { t } = useLang();
  const [meta] = useJson('meta.json');
  const [sum] = useJson('summary.json');
  return (
    <main id="main" className="page">
      <div className="eyebrow">CrimeWatch India</div>
      <h1>{t('about_title')}</h1>
      <p style={{ color: 'var(--muted)', fontSize: 18, maxWidth: 720 }}>{t('about_sub')}</p>
      {meta && <p style={{ color: 'var(--faint)' }}>Last refresh: {fmtIST(meta.generated_at)} · {sum?.total ?? 0} reports from the last {meta.kept_days} days.</p>}
      <div className="callout">
        No public source in India publishes every crime as it happens. Police systems (CCTNS, Dial 112) are available only to
        police. This site therefore shows <b>reported incidents</b> from news and police releases for the last 30 days, and
        <b> official totals</b> from NCRB for comparisons. Never read the map as a crime rate.
      </div>
      <div className="card" style={{ marginTop: 24, overflowX: 'auto' }}>
        <table className="data">
          <thead><tr><th>Source</th><th>How fresh</th><th>Coverage</th><th>Location shown</th><th>What it means</th></tr></thead>
          <tbody>{SOURCES.map((s) => (
            <tr key={s.name}><td><a href={s.url} target="_blank" rel="noopener noreferrer">{s.name}</a></td><td>{s.fresh}</td><td>{s.cover}</td><td>{s.where}</td><td>{s.means}</td></tr>))}
          </tbody>
        </table>
      </div>
      <div className="grid2">
        <div className="card"><h3>Privacy</h3>
          <ul style={{ color: 'var(--muted)', paddingLeft: 18 }}>
            <li>No names of victims or accused, addresses, phone numbers or FIR numbers are stored.</li>
            <li>Sexual-violence reports and reports about children show only the crime type, never the headline.</li>
            <li>Points are placed at the city, police district or state centre the report names, never at a house.</li>
            <li>No cameras, CCTV or personal devices are connected to this site.</li>
          </ul></div>
        <div className="card"><h3>How a report is classified</h3>
          <p style={{ color: 'var(--muted)' }}>The headline is checked for crime words (murder, robbery, snatching, cyber fraud, drugs and others). Headlines about films,
            sport, elections or opinion are skipped. Indian-language reports are classified from GDELT's topic tags. The article must lead with a place in India.</p>
          <p style={{ color: 'var(--muted)' }}>Map boundaries: state outlines follow the official depiction of India; street data © OpenStreetMap contributors via OpenFreeMap.</p></div>
      </div>
    </main>
  );
}
