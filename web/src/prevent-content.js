// Prevention content for the Prevent page, in English and Hindi.
// Scam advice follows I4C / cybercrime.gov.in and RBI guidance; actions follow the evidence
// summarised in the CrimeWatch Prevent plan (hot-spot patrols, lighting, guardianship, fast reporting).

export const HELPLINES = [
  { n: '112', en: 'Emergency (police, fire, ambulance)', hi: 'आपातकाल (पुलिस, अग्निशमन, एम्बुलेंस)' },
  { n: '1930', en: 'Cyber fraud: call within the first hour', hi: 'साइबर धोखाधड़ी: पहले घंटे में कॉल करें' },
  { n: '181', en: 'Women helpline', hi: 'महिला हेल्पलाइन' },
  { n: '1098', en: 'Childline', hi: 'चाइल्डलाइन' },
];

// key = scam type name produced by src/crimewatch/prevent.py
export const SCAMS = {
  'Digital arrest': {
    icon: '⚖',
    en: {
      how: 'A caller posing as CBI, ED, police or customs says your name is in a crime, keeps you on a video call for hours and demands money to “clear” you.',
      flags: ['No real agency arrests anyone on a video call', 'They forbid you to hang up or tell family', 'They ask you to move money to a “safe” or “RBI” account'],
      act: 'Hang up. Tell someone you trust. Call 1930 or report at cybercrime.gov.in.',
    },
    hi: {
      how: 'CBI, ED, पुलिस या कस्टम अधिकारी बनकर कोई कहता है कि आपका नाम किसी अपराध में है, घंटों वीडियो कॉल पर रखता है और “बचाने” के लिए पैसे माँगता है।',
      flags: ['कोई असली एजेंसी वीडियो कॉल पर गिरफ़्तारी नहीं करती', 'वे फ़ोन काटने या परिवार को बताने से मना करते हैं', 'वे पैसे “सुरक्षित” या “RBI” खाते में भेजने को कहते हैं'],
      act: 'फ़ोन काटें। किसी भरोसेमंद व्यक्ति को बताएँ। 1930 पर कॉल करें या cybercrime.gov.in पर शिकायत करें।',
    },
  },
  'Investment and trading': {
    icon: '📈',
    en: {
      how: 'A WhatsApp or Telegram group shows huge “profits” from stocks, IPOs or crypto, then gets you to invest through a fake app that never lets you withdraw.',
      flags: ['Guaranteed or very high returns', 'An app not listed with SEBI or a link sent in chat', 'Fees demanded before you can withdraw'],
      act: 'Only invest through SEBI-registered brokers. Stop paying, save the chats, call 1930.',
    },
    hi: {
      how: 'WhatsApp या Telegram ग्रुप शेयर, IPO या क्रिप्टो में भारी “मुनाफ़ा” दिखाता है, फिर नकली ऐप में निवेश करवाता है जिससे पैसे कभी नहीं निकलते।',
      flags: ['पक्का या बहुत ऊँचा मुनाफ़ा', 'ऐसा ऐप जो SEBI में दर्ज नहीं या चैट में भेजा लिंक', 'पैसे निकालने से पहले शुल्क की माँग'],
      act: 'केवल SEBI-पंजीकृत ब्रोकर से निवेश करें। भुगतान रोकें, चैट सहेजें, 1930 पर कॉल करें।',
    },
  },
  'Job and task': {
    icon: '💼',
    en: {
      how: 'You are paid small amounts to like videos or rate hotels, then asked to “invest” in bigger tasks. The money disappears.',
      flags: ['A job offer you never applied for', 'You have to pay to earn', 'Pressure to finish “tasks” quickly'],
      act: 'Real employers never ask you to pay. Block, report at cybercrime.gov.in, call 1930.',
    },
    hi: {
      how: 'वीडियो लाइक करने या होटल रेटिंग के लिए थोड़े पैसे मिलते हैं, फिर बड़े “टास्क” में निवेश को कहा जाता है। पैसा गायब हो जाता है।',
      flags: ['ऐसी नौकरी जिसके लिए आपने आवेदन नहीं किया', 'कमाने के लिए पहले भुगतान', 'जल्दी “टास्क” पूरा करने का दबाव'],
      act: 'असली नियोक्ता कभी पैसे नहीं माँगते। ब्लॉक करें, cybercrime.gov.in पर शिकायत करें, 1930 पर कॉल करें।',
    },
  },
  'Cyber slavery abroad': {
    icon: '✈',
    en: {
      how: 'Well-paid “data entry” or IT jobs in Thailand, Myanmar, Cambodia or Laos turn out to be scam compounds where people are held and forced to defraud others.',
      flags: ['Visa on arrival or tourist visa for a job', 'Agent not registered on the eMigrate portal', 'Flight to one country, then road travel across a border'],
      act: 'Check the agent on emigrate.gov.in. If someone is trapped, contact the Indian embassy or MADAD.',
    },
    hi: {
      how: 'थाईलैंड, म्यांमार, कंबोडिया या लाओस में अच्छी तनख़्वाह वाली “डेटा एंट्री” या IT नौकरी असल में ठगी के अड्डे निकलती है जहाँ लोगों को बंधक बनाकर दूसरों को ठगने पर मजबूर किया जाता है।',
      flags: ['नौकरी के लिए पर्यटक वीज़ा या वीज़ा-ऑन-अराइवल', 'एजेंट eMigrate पोर्टल पर दर्ज नहीं', 'एक देश की उड़ान, फिर सड़क से सीमा पार'],
      act: 'emigrate.gov.in पर एजेंट जाँचें। कोई फँसा हो तो भारतीय दूतावास या MADAD से संपर्क करें।',
    },
  },
  Sextortion: {
    icon: '📵',
    en: {
      how: 'A stranger starts a video call, records it with obscene content and threatens to send it to your contacts unless you pay.',
      flags: ['Unknown video calls, often late at night', 'A new friend who quickly moves to video', 'Threats with a deadline'],
      act: 'Do not pay: it never stops. Keep the evidence, report at cybercrime.gov.in or 1930.',
    },
    hi: {
      how: 'कोई अजनबी वीडियो कॉल करता है, अश्लील सामग्री के साथ रिकॉर्ड करता है और पैसे न देने पर आपके संपर्कों को भेजने की धमकी देता है।',
      flags: ['अनजान वीडियो कॉल, अक्सर देर रात', 'नया दोस्त जो जल्दी वीडियो कॉल पर आ जाए', 'समय-सीमा के साथ धमकी'],
      act: 'पैसे न दें: यह कभी नहीं रुकता। सबूत रखें, cybercrime.gov.in या 1930 पर शिकायत करें।',
    },
  },
  'Loan app': {
    icon: '💸',
    en: {
      how: 'An instant-loan app copies your contacts and photos, charges huge fees and harasses your family with morphed pictures.',
      flags: ['App asks for contacts and gallery access', 'Lender not linked to an RBI-regulated bank or NBFC', 'Repayment demanded within days'],
      act: 'Check the lender on the RBI site. Report the app on sachet.rbi.org.in and cybercrime.gov.in.',
    },
    hi: {
      how: 'तुरंत लोन ऐप आपके संपर्क और फ़ोटो ले लेता है, भारी शुल्क लेता है और बदली हुई तस्वीरों से परिवार को परेशान करता है।',
      flags: ['ऐप संपर्क और गैलरी की अनुमति माँगता है', 'ऋणदाता RBI-विनियमित बैंक या NBFC से जुड़ा नहीं', 'कुछ ही दिनों में भुगतान की माँग'],
      act: 'RBI साइट पर ऋणदाता जाँचें। ऐप की शिकायत sachet.rbi.org.in और cybercrime.gov.in पर करें।',
    },
  },
  'Bank, KYC and OTP': {
    icon: '🔐',
    en: {
      how: 'A message says your account or card will be blocked unless you update KYC through a link, or share an OTP or approve a UPI request.',
      flags: ['Links in SMS claiming to be your bank', 'Anyone asking for an OTP, PIN or CVV', 'A UPI “collect” request when you expect to receive money'],
      act: 'Banks never ask for OTPs. Call your bank on the number on your card, then 1930.',
    },
    hi: {
      how: 'संदेश आता है कि लिंक से KYC अपडेट न करने पर खाता या कार्ड बंद होगा, या OTP बताने या UPI अनुरोध स्वीकार करने को कहा जाता है।',
      flags: ['बैंक के नाम पर SMS में लिंक', 'OTP, PIN या CVV माँगने वाला कोई भी', 'पैसा पाने के बदले UPI “कलेक्ट” अनुरोध'],
      act: 'बैंक कभी OTP नहीं माँगते। कार्ड पर लिखे नंबर पर बैंक को कॉल करें, फिर 1930।',
    },
  },
  'Courier and parcel': {
    icon: '📦',
    en: {
      how: 'A “courier company” says a parcel in your name holds drugs or passports, then transfers you to fake police. Often the start of a digital arrest.',
      flags: ['A parcel you never sent', 'Call transferred to “police” or “narcotics”', 'Requests to verify your Aadhaar or bank details'],
      act: 'Hang up and call the courier company yourself. Report at 1930.',
    },
    hi: {
      how: '“कूरियर कंपनी” कहती है कि आपके नाम के पार्सल में ड्रग्स या पासपोर्ट हैं, फिर नकली पुलिस से जोड़ देती है। अक्सर डिजिटल अरेस्ट की शुरुआत।',
      flags: ['ऐसा पार्सल जो आपने भेजा ही नहीं', 'कॉल “पुलिस” या “नारकोटिक्स” को ट्रांसफ़र', 'आधार या बैंक विवरण की जाँच की माँग'],
      act: 'फ़ोन काटें और ख़ुद कूरियर कंपनी को कॉल करें। 1930 पर शिकायत करें।',
    },
  },
  'Matrimonial and romance': {
    icon: '💔',
    en: {
      how: 'A match on a dating or matrimonial site builds trust, then needs money for an emergency, customs fee or a “gift” stuck at the airport.',
      flags: ['Profile lives abroad and never meets', 'Avoids video calls', 'Sudden emergencies that need money'],
      act: 'Never send money to someone you have not met. Report the profile and call 1930.',
    },
    hi: {
      how: 'डेटिंग या वैवाहिक साइट पर मिला व्यक्ति भरोसा बनाता है, फिर आपात स्थिति, कस्टम शुल्क या हवाई अड्डे पर अटके “तोहफ़े” के लिए पैसे माँगता है।',
      flags: ['विदेश में रहता है और कभी मिलता नहीं', 'वीडियो कॉल से बचता है', 'अचानक पैसों की ज़रूरत'],
      act: 'जिससे कभी मिले नहीं उसे पैसे न भेजें। प्रोफ़ाइल की शिकायत करें और 1930 पर कॉल करें।',
    },
  },
  'Lottery and prize': {
    icon: '🎟',
    en: {
      how: 'You have “won” KBC, a lottery or a lucky draw, and must pay tax or processing fees to collect.',
      flags: ['A prize for a contest you never entered', 'Fees before payout', 'Personal bank account for the “company”'],
      act: 'Real prizes never charge fees. Ignore, block and report at 1930.',
    },
    hi: {
      how: 'आपने KBC, लॉटरी या लकी ड्रॉ “जीता” है और इनाम पाने के लिए टैक्स या प्रोसेसिंग शुल्क देना होगा।',
      flags: ['ऐसी प्रतियोगिता का इनाम जिसमें आपने भाग नहीं लिया', 'भुगतान से पहले शुल्क', '“कंपनी” का निजी बैंक खाता'],
      act: 'असली इनाम में कभी शुल्क नहीं लगता। अनदेखा करें, ब्लॉक करें और 1930 पर शिकायत करें।',
    },
  },
  'Fake government scheme': {
    icon: '🏛',
    en: {
      how: 'Messages promise PM-Kisan money, subsidies, free laptops or jobs under a government scheme for a registration fee.',
      flags: ['Links not ending in .gov.in or .nic.in', 'Registration fee for a free scheme', 'Urgency: “last date today”'],
      act: 'Check on the official scheme website or myScheme.gov.in. Report fake sites at 1930.',
    },
    hi: {
      how: 'संदेश पंजीकरण शुल्क के बदले PM-किसान राशि, सब्सिडी, मुफ़्त लैपटॉप या सरकारी योजना में नौकरी का वादा करते हैं।',
      flags: ['ऐसे लिंक जो .gov.in या .nic.in पर ख़त्म नहीं होते', 'मुफ़्त योजना के लिए पंजीकरण शुल्क', 'जल्दबाज़ी: “आज आख़िरी तारीख़”'],
      act: 'आधिकारिक योजना वेबसाइट या myScheme.gov.in पर जाँचें। नकली साइट की शिकायत 1930 पर करें।',
    },
  },
};

// Actions by dominant crime type of a place. `you` = residents, `gov` = police and administration.
const PLAY = {
  'Sexual violence': {
    en: { you: ['Save 112 and 181 on speed dial; use the 112 India app SOS', 'Share live location when travelling at night', 'Report unlit stretches and broken streetlights to the municipality'],
      gov: ['Fix lighting on reported stretches (NYC trial: at least 36% less night-time outdoor crime)', 'Pink patrols and women help desks at peak hours', 'Fast-track forensic and court follow-up so offenders are not emboldened'] },
    hi: { you: ['112 और 181 स्पीड डायल पर रखें; 112 India ऐप का SOS इस्तेमाल करें', 'रात में यात्रा करते समय लाइव लोकेशन साझा करें', 'अंधेरी गलियाँ और ख़राब स्ट्रीटलाइट नगर निगम को बताएँ'],
      gov: ['रिपोर्ट किए गए हिस्सों में रोशनी ठीक करें (NYC प्रयोग: रात के बाहरी अपराध में कम से कम 36% कमी)', 'व्यस्त समय में पिंक पेट्रोल और महिला हेल्प डेस्क', 'फ़ॉरेंसिक और अदालती कार्रवाई तेज़ करें ताकि अपराधियों का हौसला न बढ़े'] },
  },
  Assault: {
    en: { you: ['Step away from escalating arguments; call 112 early', 'Note vehicle numbers and faces, not phone videos at close range', 'Join or start a neighbourhood watch group'],
      gov: ['Short, visible patrols at the hot spot during peak hours (hot-spot policing reduces crime without simply moving it)', 'Mediation for repeat local disputes', 'Check liquor-outlet hours and crowding near the spot'] },
    hi: { you: ['बढ़ते झगड़े से दूर रहें; जल्दी 112 पर कॉल करें', 'पास से वीडियो बनाने के बजाय वाहन नंबर और चेहरे याद रखें', 'मोहल्ला निगरानी समूह से जुड़ें या बनाएँ'],
      gov: ['व्यस्त समय में हॉटस्पॉट पर छोटी, दिखने वाली गश्त (हॉटस्पॉट पुलिसिंग अपराध घटाती है, केवल हटाती नहीं)', 'बार-बार होने वाले स्थानीय विवादों में मध्यस्थता', 'पास के शराब ठेकों का समय और भीड़ जाँचें'] },
  },
  Murder: {
    en: { you: ['Report threats and long-running feuds to the local police station in writing', 'Call 112 at the first sign of armed violence', 'Support victims’ families to file and follow complaints'],
      gov: ['Focused deterrence: meet the groups involved, offer help and state consequences', 'Seize illegal arms and track repeat locations', 'Witness protection to keep cases moving'] },
    hi: { you: ['धमकियों और पुरानी रंजिशों की लिखित शिकायत स्थानीय थाने में करें', 'हथियारबंद हिंसा के पहले संकेत पर 112 पर कॉल करें', 'पीड़ित परिवारों को शिकायत दर्ज कराने और उसका पालन करने में मदद करें'],
      gov: ['फ़ोकस्ड डिटरेंस: शामिल समूहों से मिलें, मदद दें और परिणाम बताएँ', 'अवैध हथियार ज़ब्त करें और बार-बार की जगहों पर नज़र रखें', 'मामले चलते रहें इसके लिए गवाह सुरक्षा'] },
  },
  Robbery: {
    en: { you: ['Keep phones and jewellery out of sight on known stretches', 'Use well-lit, busy routes; avoid isolated ATMs at night', 'Report every attempt, even small ones: patterns guide patrols'],
      gov: ['Patrols and pickets on reported stretches at reported hours', 'Lighting and CCTV at ATMs and bus stops on the hot spot', 'Track repeat-offender vehicles with number-plate checks'] },
    hi: { you: ['जानी-मानी जगहों पर फ़ोन और गहने छिपाकर रखें', 'रोशनी वाले, भीड़ वाले रास्ते लें; रात में सुनसान ATM से बचें', 'हर कोशिश की शिकायत करें, छोटी भी: पैटर्न से गश्त तय होती है'],
      gov: ['रिपोर्ट हुए हिस्सों पर उसी समय गश्त और पिकेट', 'हॉटस्पॉट के ATM और बस स्टॉप पर रोशनी और CCTV', 'नंबर-प्लेट जाँच से आदतन अपराधियों के वाहन पकड़ें'] },
  },
  Theft: {
    en: { you: ['Lock vehicles with a second lock; park in lit areas', 'Register phones on CEIR (sancharsaathi.gov.in) so stolen ones can be blocked', 'Mark and photograph valuables'],
      gov: ['Patrol markets and stations at peak hours', 'Crack down on stolen-goods resale points', 'Use CEIR to trace and return phones'] },
    hi: { you: ['वाहन में दूसरा ताला लगाएँ; रोशनी में पार्क करें', 'फ़ोन CEIR (sancharsaathi.gov.in) पर दर्ज करें ताकि चोरी होने पर ब्लॉक हो सके', 'क़ीमती सामान पर निशान लगाएँ और फ़ोटो रखें'],
      gov: ['व्यस्त समय में बाज़ार और स्टेशन पर गश्त', 'चोरी का माल बेचने वाली जगहों पर कार्रवाई', 'CEIR से फ़ोन खोजकर लौटाएँ'] },
  },
  Burglary: {
    en: { you: ['Tell trusted neighbours when the house is empty; avoid posting travel online', 'Fit door viewers, grills and a motion light', 'Verify domestic help and tenants with the police'],
      gov: ['Patrol locked houses on request (many states offer this)', 'Tenant and servant verification drives', 'Revisit nearby homes within days of a burglary: repeats are common'] },
    hi: { you: ['घर ख़ाली हो तो भरोसेमंद पड़ोसियों को बताएँ; यात्रा की पोस्ट ऑनलाइन न डालें', 'डोर व्यूअर, ग्रिल और मोशन लाइट लगाएँ', 'घरेलू सहायक और किरायेदार का पुलिस सत्यापन कराएँ'],
      gov: ['अनुरोध पर बंद घरों की गश्त (कई राज्यों में सुविधा)', 'किरायेदार और नौकर सत्यापन अभियान', 'सेंधमारी के कुछ दिनों में पास के घरों पर दोबारा जाएँ: दोहराव आम है'] },
  },
  'Cyber Crime': {
    en: { you: ['Call 1930 within the first hour: money can still be frozen', 'Never share OTPs; turn on two-step login for WhatsApp and email', 'Talk to elderly relatives about digital arrest and KYC calls'],
      gov: ['Share scam scripts in local languages via schools, RWAs and SMS', 'Fast freezing through the I4C citizen financial fraud system', 'Act on mule accounts and SIM cards linked to complaints'] },
    hi: { you: ['पहले घंटे में 1930 पर कॉल करें: पैसा अभी रोका जा सकता है', 'OTP कभी न बताएँ; WhatsApp और ईमेल पर दो-चरणीय लॉगिन चालू करें', 'बुज़ुर्ग परिजनों से डिजिटल अरेस्ट और KYC कॉल के बारे में बात करें'],
      gov: ['स्कूल, RWA और SMS से स्थानीय भाषाओं में ठगी के तरीके बताएँ', 'I4C नागरिक वित्तीय धोखाधड़ी प्रणाली से तेज़ी से रकम रोकें', 'शिकायतों से जुड़े म्यूल खातों और SIM पर कार्रवाई करें'] },
  },
  'Drug Offense': {
    en: { you: ['Report sale points anonymously on MANAS helpline 1933', 'Watch for changes in teenagers’ behaviour; talk early', 'Support de-addiction through Tele-MANAS 14416'],
      gov: ['Target supply points near schools and colleges', 'Pair enforcement with treatment referrals', 'Track repeat sale locations and courier routes'] },
    hi: { you: ['बिक्री की जगहों की गुप्त सूचना MANAS हेल्पलाइन 1933 पर दें', 'किशोरों के व्यवहार में बदलाव पर ध्यान दें; जल्दी बात करें', 'Tele-MANAS 14416 से नशा मुक्ति में मदद करें'],
      gov: ['स्कूल और कॉलेज के पास आपूर्ति ठिकानों पर कार्रवाई', 'कार्रवाई के साथ इलाज के लिए रेफ़रल', 'बार-बार बिक्री की जगहों और कूरियर रास्तों पर नज़र'] },
  },
  'Domestic Violence': {
    en: { you: ['Women helpline 181 and One Stop Centres give shelter, legal and medical help', 'If you hear violence next door, call 112', 'Keep important papers and a phone ready to leave'],
      gov: ['Protection officers under the DV Act in every district', 'Follow up repeat calls from the same address', 'Link survivors to One Stop Centres the same day'] },
    hi: { you: ['महिला हेल्पलाइन 181 और वन स्टॉप सेंटर आश्रय, क़ानूनी और चिकित्सा मदद देते हैं', 'पड़ोस में हिंसा सुनें तो 112 पर कॉल करें', 'ज़रूरी कागज़ और फ़ोन तैयार रखें'],
      gov: ['हर ज़िले में घरेलू हिंसा अधिनियम के संरक्षण अधिकारी', 'एक ही पते से बार-बार आने वाली कॉल पर कार्रवाई', 'पीड़ितों को उसी दिन वन स्टॉप सेंटर से जोड़ें'] },
  },
  Kidnapping: {
    en: { you: ['Teach children a family code word and your phone number', 'Report a missing child immediately: there is no 24-hour wait', 'Childline 1098 for children in danger'],
      gov: ['Register missing children on TrackChild and Khoya-Paya at once', 'Watch railway and bus stations on reported routes', 'Verify placement agencies and job agents'] },
    hi: { you: ['बच्चों को पारिवारिक कोड शब्द और अपना फ़ोन नंबर सिखाएँ', 'लापता बच्चे की तुरंत शिकायत करें: 24 घंटे इंतज़ार ज़रूरी नहीं', 'ख़तरे में बच्चों के लिए चाइल्डलाइन 1098'],
      gov: ['लापता बच्चों को तुरंत TrackChild और खोया-पाया पर दर्ज करें', 'रिपोर्ट हुए रास्तों पर रेलवे और बस स्टेशनों पर निगरानी', 'प्लेसमेंट एजेंसियों और नौकरी एजेंटों का सत्यापन'] },
  },
};
PLAY.Snatching = PLAY.Robbery;
PLAY.Fraud = PLAY['Cyber Crime'];
PLAY.Default = {
  en: { you: ['Save 112 and report incidents, even small ones', 'Know your beat officer and local police station number', 'Join a resident welfare or neighbourhood watch group'],
    gov: ['Short, visible patrols at the forecast hot spots', 'Fix lighting and blind spots found in safety audits', 'Publish what was done and check if reports fall'] },
  hi: { you: ['112 सहेजें और छोटी घटनाओं की भी शिकायत करें', 'अपने बीट अधिकारी और थाने का नंबर जानें', 'RWA या मोहल्ला निगरानी समूह से जुड़ें'],
    gov: ['पूर्वानुमानित हॉटस्पॉट पर छोटी, दिखने वाली गश्त', 'सुरक्षा ऑडिट में मिली अंधेरी जगहें ठीक करें', 'क्या किया गया यह प्रकाशित करें और देखें कि रिपोर्टें घटीं या नहीं'] },
};
export const playbook = (category, lang) => (PLAY[category] || PLAY.Default)[lang === 'hi' ? 'hi' : 'en'];

// Safety self-audit. Each item is a yes/no; nothing is stored or sent.
export const AUDIT = [
  { id: 'home', en: 'Home', hi: 'घर', items: [
    ['lock', 'Doors have a second lock or grill', 'दरवाज़ों पर दूसरा ताला या ग्रिल है'],
    ['light', 'Entrance and parking are lit at night', 'रात में प्रवेश और पार्किंग में रोशनी है'],
    ['verify', 'Domestic help and tenants are police-verified', 'घरेलू सहायक और किरायेदार का पुलिस सत्यापन हुआ है'],
    ['neigh', 'You know at least two neighbours by name', 'आप कम से कम दो पड़ोसियों को नाम से जानते हैं'],
  ] },
  { id: 'phone', en: 'Phone and money', hi: 'फ़ोन और पैसा', items: [
    ['2fa', 'Two-step login is on for WhatsApp and email', 'WhatsApp और ईमेल पर दो-चरणीय लॉगिन चालू है'],
    ['otp', 'Everyone at home knows never to share an OTP', 'घर में सबको पता है कि OTP कभी नहीं बताना'],
    ['1930', '1930 is saved in your contacts', '1930 आपके संपर्कों में सहेजा है'],
    ['ceir', 'Your phone IMEI is noted for CEIR blocking', 'CEIR ब्लॉकिंग के लिए फ़ोन का IMEI लिखा है'],
    ['elders', 'Elderly relatives know about digital arrest calls', 'बुज़ुर्ग परिजन डिजिटल अरेस्ट कॉल के बारे में जानते हैं'],
  ] },
  { id: 'street', en: 'Street and travel', hi: 'सड़क और यात्रा', items: [
    ['route', 'Your daily route avoids unlit, empty stretches', 'आपका रोज़ का रास्ता अंधेरी, सुनसान जगहों से बचता है'],
    ['share', 'You share live location on late trips', 'देर की यात्रा में आप लाइव लोकेशन साझा करते हैं'],
    ['112app', 'The 112 India app is installed', '112 India ऐप इंस्टॉल है'],
    ['station', 'You know your local police station’s number', 'आपको अपने थाने का नंबर पता है'],
  ] },
  { id: 'kids', en: 'Children', hi: 'बच्चे', items: [
    ['code', 'Children know a family code word', 'बच्चे पारिवारिक कोड शब्द जानते हैं'],
    ['number', 'Children know a parent’s phone number by heart', 'बच्चों को माता-पिता का फ़ोन नंबर याद है'],
    ['online', 'You know which apps and games your child uses', 'आप जानते हैं बच्चा कौन से ऐप और गेम इस्तेमाल करता है'],
  ] },
];
