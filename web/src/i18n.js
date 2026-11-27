import { createContext, useContext } from 'react';

export const STRINGS = {
  en: {
    gov: 'A public-safety information service · Data from NCRB, police and news reports',
    nav_home: 'Home', nav_map: 'Live map', nav_trends: 'Trends', nav_about: 'About the data',
    updated: 'Updated',
    hero_eyebrow: 'India · reported today',
    hero_title_1: 'See where crime is', hero_title_2: 'being reported', hero_title_3: 'across India.',
    hero_lead: 'A live 3D map of incidents reported by police and news in the last 24 hours, next to the official national crime statistics.',
    c_24h: 'incidents reported in the last 24 hours', c_states: 'states and UTs', c_30d: 'reports in the last 30 days',
    search_ph: 'Search a city, district or state', open_map: 'Open live map', explore: 'Scroll to explore',
    facts_eyebrow: 'The official picture', facts_title: 'What the latest national statistics say.',
    facts_sub: 'NCRB publishes Crime in India once a year. These are the newest official figures.',
    f_total: 'cognizable crimes recorded in India in 2024', f_rate: 'crimes per lakh people in 2024', f_metro: 'crimes in the 19 largest cities in 2024',
    vs: 'vs', how_eyebrow: 'How it works', how_title: 'From a report to a point on the map.',
    s1t: 'Collect', s1: 'Every hour we read Indian news in English and regional languages, and Delhi Police press releases.',
    s2t: 'Understand', s2: 'Each report is tagged with a crime type and the place it names: a city, district or police station.',
    s3t: 'Protect', s3: 'No names, addresses or FIR details are stored. Sexual-violence reports show only the category.',
    s4t: 'Show', s4: 'Points land at the named locality, never a house. Each one links back to its original source.',
    layers: 'View', points: 'Points', columns: '3D columns', heat: 'Heat',
    period: 'Time', h24: '24 hours', d7: '7 days', d30: '30 days',
    types: 'Crime type', all: 'All', sources: 'Source', news: 'News', police: 'Police',
    shown: 'shown', places: 'places', play: 'Play', pause: 'Pause',
    map_note: 'Reported incidents, not total crime. One incident can appear in several reports; automatic tagging can make mistakes.',
    what: 'What', when: 'When', where: 'Where', source: 'Source', precision: 'Accuracy',
    read: 'Read the original report', nearby: 'Other reports here', no_title: 'Details withheld to protect the people involved.',
    p_city: 'City centre', p_state: 'State centre', p_district: 'Police district centre',
    o_news: 'News report', 'o_news-translated': 'News report (Indian language)', o_police: 'Police press release',
    tiles_fail: 'Street map could not load. Showing state outlines only.',
    trends_title: 'Trends', trends_sub: 'Reported incidents over the last 30 days, and official yearly statistics from NCRB.',
    t_daily: 'Reported incidents per day', t_daily_cap: 'News and police reports, last 30 days',
    t_cats: 'By crime type', t_cats_cap: 'Last 30 days', t_states: 'By state', t_states_cap: 'Last 30 days, top 15',
    t_ncrb: 'Official crime rate by State/UT, 2023', t_ncrb_cap: 'Cognizable crimes per lakh population · NCRB Crime in India 2023',
    t_nat: 'All-India cognizable crimes', t_nat_cap: 'NCRB Crime in India 2024, Table 1.1',
    about_title: 'About the data', about_sub: 'Where every number on this site comes from, how fresh it is, and what it does not mean.',
    footer_1: 'CrimeWatch India · open source', footer_2: 'Not an emergency service. In an emergency dial 112.',
  },
  hi: {
    gov: 'एक सार्वजनिक सुरक्षा सूचना सेवा · आंकड़े NCRB, पुलिस और समाचार रिपोर्टों से',
    nav_home: 'होम', nav_map: 'लाइव मानचित्र', nav_trends: 'रुझान', nav_about: 'आंकड़ों के बारे में',
    updated: 'अपडेट',
    hero_eyebrow: 'भारत · आज की रिपोर्ट',
    hero_title_1: 'देखें भारत में', hero_title_2: 'अपराध कहाँ', hero_title_3: 'दर्ज हो रहे हैं।',
    hero_lead: 'पिछले 24 घंटों में पुलिस और समाचारों में दर्ज घटनाओं का लाइव 3D मानचित्र, आधिकारिक राष्ट्रीय अपराध आंकड़ों के साथ।',
    c_24h: 'पिछले 24 घंटों में दर्ज घटनाएँ', c_states: 'राज्य और केंद्र शासित प्रदेश', c_30d: 'पिछले 30 दिनों की रिपोर्टें',
    search_ph: 'शहर, ज़िला या राज्य खोजें', open_map: 'लाइव मानचित्र खोलें', explore: 'नीचे देखें',
    facts_eyebrow: 'आधिकारिक तस्वीर', facts_title: 'नवीनतम राष्ट्रीय आंकड़े क्या कहते हैं।',
    facts_sub: 'NCRB हर साल "भारत में अपराध" प्रकाशित करता है। ये सबसे नए आधिकारिक आंकड़े हैं।',
    f_total: '2024 में भारत में दर्ज संज्ञेय अपराध', f_rate: '2024 में प्रति लाख लोगों पर अपराध', f_metro: '2024 में 19 बड़े शहरों में अपराध',
    vs: 'बनाम', how_eyebrow: 'यह कैसे काम करता है', how_title: 'रिपोर्ट से मानचित्र के बिंदु तक।',
    s1t: 'संग्रह', s1: 'हर घंटे हम अंग्रेज़ी और भारतीय भाषाओं के समाचार और दिल्ली पुलिस की प्रेस विज्ञप्तियाँ पढ़ते हैं।',
    s2t: 'समझ', s2: 'हर रिपोर्ट को अपराध के प्रकार और उसमें बताए स्थान से जोड़ा जाता है।',
    s3t: 'सुरक्षा', s3: 'कोई नाम, पता या FIR विवरण नहीं रखा जाता। यौन हिंसा की रिपोर्ट में केवल श्रेणी दिखती है।',
    s4t: 'प्रदर्शन', s4: 'बिंदु इलाके पर दिखते हैं, किसी घर पर नहीं। हर बिंदु मूल स्रोत से जुड़ा है।',
    layers: 'दृश्य', points: 'बिंदु', columns: '3D स्तंभ', heat: 'हीट',
    period: 'समय', h24: '24 घंटे', d7: '7 दिन', d30: '30 दिन',
    types: 'अपराध का प्रकार', all: 'सभी', sources: 'स्रोत', news: 'समाचार', police: 'पुलिस',
    shown: 'दिखाई गईं', places: 'स्थान', play: 'चलाएँ', pause: 'रोकें',
    map_note: 'ये दर्ज घटनाएँ हैं, कुल अपराध नहीं। एक घटना कई रिपोर्टों में आ सकती है; स्वचालित वर्गीकरण में गलती हो सकती है।',
    what: 'क्या', when: 'कब', where: 'कहाँ', source: 'स्रोत', precision: 'सटीकता',
    read: 'मूल रिपोर्ट पढ़ें', nearby: 'यहाँ की अन्य रिपोर्टें', no_title: 'संबंधित लोगों की सुरक्षा के लिए विवरण नहीं दिखाया गया।',
    p_city: 'शहर का केंद्र', p_state: 'राज्य का केंद्र', p_district: 'पुलिस ज़िले का केंद्र',
    o_news: 'समाचार रिपोर्ट', 'o_news-translated': 'समाचार रिपोर्ट (भारतीय भाषा)', o_police: 'पुलिस प्रेस विज्ञप्ति',
    tiles_fail: 'सड़क मानचित्र लोड नहीं हो सका। केवल राज्यों की सीमाएँ दिख रही हैं।',
    trends_title: 'रुझान', trends_sub: 'पिछले 30 दिनों की दर्ज घटनाएँ, और NCRB के आधिकारिक वार्षिक आंकड़े।',
    t_daily: 'प्रतिदिन दर्ज घटनाएँ', t_daily_cap: 'समाचार और पुलिस रिपोर्टें, पिछले 30 दिन',
    t_cats: 'अपराध के प्रकार के अनुसार', t_cats_cap: 'पिछले 30 दिन', t_states: 'राज्य के अनुसार', t_states_cap: 'पिछले 30 दिन, शीर्ष 15',
    t_ncrb: 'राज्य/केंद्र शासित प्रदेश अनुसार अपराध दर, 2023', t_ncrb_cap: 'प्रति लाख जनसंख्या संज्ञेय अपराध · NCRB 2023',
    t_nat: 'अखिल भारतीय संज्ञेय अपराध', t_nat_cap: 'NCRB भारत में अपराध 2024, तालिका 1.1',
    about_title: 'आंकड़ों के बारे में', about_sub: 'इस साइट का हर आंकड़ा कहाँ से आता है, कितना ताज़ा है, और उसका क्या अर्थ नहीं है।',
    footer_1: 'CrimeWatch India · ओपन सोर्स', footer_2: 'यह आपातकालीन सेवा नहीं है। आपात स्थिति में 112 डायल करें।',
  },
};

export const CATEGORY_HI = {
  Murder: 'हत्या', Assault: 'मारपीट', 'Sexual violence': 'यौन हिंसा', Kidnapping: 'अपहरण', Robbery: 'लूट',
  Snatching: 'झपटमारी', Theft: 'चोरी', Burglary: 'सेंधमारी', Fraud: 'धोखाधड़ी', 'Cyber Crime': 'साइबर अपराध',
  'Drug Offense': 'नशीले पदार्थ', 'Domestic Violence': 'घरेलू हिंसा', 'Arms Act': 'शस्त्र अधिनियम', Arson: 'आगज़नी',
  Gambling: 'जुआ', 'Other crime': 'अन्य अपराध',
};

// colour per category: violent = warm, property = amber, cyber/fraud = blue/violet, drugs = green
export const CATEGORY_COLOR = {
  Murder: [255, 59, 48], 'Sexual violence': [255, 45, 120], Assault: [255, 107, 61], Kidnapping: [255, 149, 0],
  Robbery: [255, 176, 32], Snatching: [255, 204, 0], Theft: [232, 214, 120], Burglary: [214, 190, 140],
  Fraud: [94, 92, 230], 'Cyber Crime': [77, 163, 255], 'Drug Offense': [47, 214, 160], 'Domestic Violence': [191, 90, 242],
  'Arms Act': [255, 120, 120], Arson: [255, 85, 0], Gambling: [160, 160, 170], 'Other crime': [150, 160, 175],
};
export const colorOf = (c) => CATEGORY_COLOR[c] || [150, 160, 175];
export const rgb = (c, a = 1) => `rgba(${colorOf(c).join(',')},${a})`;

export const LangContext = createContext({ lang: 'en', t: (k) => STRINGS.en[k] || k, cat: (c) => c });
export const useLang = () => useContext(LangContext);
export const makeLang = (lang) => ({
  lang,
  t: (k) => STRINGS[lang][k] ?? STRINGS.en[k] ?? k,
  cat: (c) => (lang === 'hi' ? CATEGORY_HI[c] || c : c),
  num: (n) => (n == null ? '–' : Number(n).toLocaleString('en-IN')),
});
