/**
 * GeoSentry Standardized Localization Engine (Translation Keys)
 * Supports English, Hindi, Marathi, Malayalam, and Bengali
 */

const I18N_DICTIONARY = {
  en: {
    // Navigation
    "nav.brand": "GeoSentry",
    "nav.tagline": "AI Landslide Early Warning & Emergency Risk Prioritization",
    "nav.map": "GIS Risk Map",
    "nav.priority": "Priority Hotspots",
    "nav.report": "Report Hazard",
    "nav.engine": "Risk Engine",
    "nav.validator": "Validator Console",
    "nav.alerts": "Alert Center",
    "nav.analytics": "Analytics & Trends",
    "nav.health": "Health",
    "nav.signin": "Stakeholder Sign In",

    // Risk Levels & Trends
    "risk.low": "LOW RISK",
    "risk.moderate": "MODERATE RISK",
    "risk.high": "HIGH RISK",
    "risk.critical": "CRITICAL RISK",
    "risk.trend.increasing": "Trend: Increasing",
    "risk.trend.stable": "Trend: Stable",
    "risk.trend.decreasing": "Trend: Decreasing",

    // 4 Metrics
    "metric.probability": "Landslide Probability",
    "metric.hazard": "Environmental Hazard",
    "metric.exposure": "Human & Asset Exposure",
    "metric.priority": "Response Priority",

    // Environmental Headers
    "env.title": "Environmental Conditions",
    "env.temp": "Temperature",
    "env.rain24": "24-Hour Rainfall",
    "env.rain7d": "7-Day Accum. Rain",
    "env.slope": "Slope Gradient",
    "env.soil": "Soil Moisture Saturation",
    "env.elevation": "Elevation",
    "env.geology": "Terrain Geology",

    // Historical
    "hist.title": "Historical Pattern & Response",
    "hist.incidents": "Recorded Past Incidents",
    "hist.susceptibility": "Baseline Susceptibility",
    "hist.last": "Last Major Occurrence",
    "hist.peak": "Peak Vulnerability Period",
    "hist.rule": "Historical Rainfall Response:",

    // Impact & Actions
    "impact.title": "Impact & Trauma Lifelines",
    "impact.road": "Critical Road Corridor",
    "impact.exposure": "Population & Asset Exposure",
    "impact.hospital": "Nearest Emergency Hospital",
    "impact.action": "Recommended Action:",

    // Buttons
    "btn.inspect": "Inspect Risk Engine",
    "btn.report": "Report Hazard",
    "btn.dispatch": "Dispatch Alert",
    "btn.gps": "Use My Current Location (GPS)",
    "btn.search": "Search",
    "btn.verify": "Verify (+12pts)",
    "btn.reject": "Reject",
    "btn.escalate": "Escalate Alert",
  },
  hi: {
    "nav.brand": "जियोसेंट्री",
    "nav.tagline": "एआई भूस्खलन पूर्व चेतावनी एवं आपातकालीन जोखिम प्राथमिकता",
    "nav.map": "जीआईएस जोखिम मानचित्र",
    "nav.priority": "प्राथमिकता हॉटस्पॉट",
    "nav.report": "खतरा दर्ज करें",
    "nav.engine": "जोखिम इंजन",
    "nav.validator": "सत्यापनकर्ता कंसोल",
    "nav.alerts": "चेतावनी केंद्र",
    "nav.analytics": "विश्लेषण एवं रुझान",
    "nav.health": "स्वास्थ्य",
    "nav.signin": "हितधारक लॉगिन",

    "risk.low": "निम्न जोखिम",
    "risk.moderate": "मध्यम जोखिम",
    "risk.high": "उच्च जोखिम",
    "risk.critical": "अति गंभीर जोखिम",
    "risk.trend.increasing": "रुझान: बढ़ रहा है",
    "risk.trend.stable": "रुझान: स्थिर",
    "risk.trend.decreasing": "रुझान: घट रहा है",

    "metric.probability": "भूस्खलन संभावना",
    "metric.hazard": "पर्यावरणीय खतरा",
    "metric.exposure": "जनसंख्या एवं संपत्ति जोखिम",
    "metric.priority": "प्रतिक्रिया प्राथमिकता",

    "env.title": "पर्यावरणीय स्थितियां",
    "env.temp": "तापमान",
    "env.rain24": "24 घंटे की वर्षा",
    "env.rain7d": "7 दिनों की संचयी वर्षा",
    "env.slope": "ढलान प्रवणता",
    "env.soil": "मिट्टी की नमी संतृप्ति",
    "env.elevation": "ऊंचाई",
    "env.geology": "भूगर्भीय संरचना",

    "hist.title": "ऐतिहासिक पैटर्न एवं प्रतिक्रिया",
    "hist.incidents": "दर्ज पूर्व घटनाएं",
    "hist.susceptibility": "आधारभूत संवेदनशीलता",
    "hist.last": "अंतिम प्रमुख घटना",
    "hist.peak": "चरम जोखिम अवधि",
    "hist.rule": "ऐतिहासिक वर्षा प्रतिक्रिया:",

    "impact.title": "प्रभाव एवं ट्रॉमा जीवनरेखा",
    "impact.road": "महत्वपूर्ण सड़क मार्ग",
    "impact.exposure": "जनसंख्या एवं संपत्ति प्रभाव",
    "impact.hospital": "निकटतम आपातकालीन अस्पताल",
    "impact.action": "अनुशंसित कार्रवाई:",

    "btn.inspect": "जोखिम इंजन देखें",
    "btn.report": "खतरा दर्ज करें",
    "btn.dispatch": "चेतावनी भेजें",
    "btn.gps": "मेरा जीपीएस स्थान उपयोग करें",
    "btn.search": "खोजें",
    "btn.verify": "सत्यापित करें (+12 अंक)",
    "btn.reject": "अस्वीकार करें",
    "btn.escalate": "चेतावनी बढ़ाएं",
  },
  mr: {
    "nav.brand": "जिओसेंट्री",
    "nav.tagline": "एआय दरड पूर्वसूचना व आपत्कालीन जोखीम प्राधान्यक्रम",
    "nav.map": "जीआयएस नकाशा",
    "nav.priority": "अतिधोकादायक क्षेत्रे",
    "nav.report": "धोका नोंदवा",
    "nav.engine": "जोखीम गणक",
    "nav.validator": "भूवैज्ञानिक पडताळणी",
    "nav.alerts": "इशारा केंद्र",
    "nav.analytics": "विश्लेषण व कल",
    "nav.health": "प्रणाली आरोग्य",
    "nav.signin": "प्रवेश करा",

    "risk.low": "कमी जोखीम",
    "risk.moderate": "मध्यम जोखीम",
    "risk.high": "उच्च जोखीम",
    "risk.critical": "अतिगंभीर जोखीम",
    "risk.trend.increasing": "कल: वाढता",
    "risk.trend.stable": "कल: स्थिर",
    "risk.trend.decreasing": "कल: घटता",

    "metric.probability": "दरड संभाव्यता",
    "metric.hazard": "पर्यावरणीय धोका",
    "metric.exposure": "लोकसंख्या व मालमत्ता प्रभाव",
    "metric.priority": "प्रतिसाद प्राधान्य",

    "env.title": "पर्यावरणीय परिस्थिती",
    "env.temp": "तापमान",
    "env.rain24": "२४ तासांचा पाऊस",
    "env.rain7d": "७ दिवसांचा एकूण पाऊस",
    "env.slope": "उताराचा कोन",
    "env.soil": "मातीतील ओलावा",
    "env.elevation": "उंची",
    "env.geology": "भूरचना",

    "hist.title": "ऐतिहासिक नोंदी व प्रतिसाद",
    "hist.incidents": "मागील घटना",
    "hist.susceptibility": "मूळ संवेदनशीलता",
    "hist.last": "शेवटची मोठी घटना",
    "hist.peak": "तीव्र धोका कालावधी",
    "hist.rule": "पावसावरील ऐतिहासिक प्रतिसाद:",

    "impact.title": "प्रभाव व आपत्कालीन सुविधा",
    "impact.road": "महत्त्वाचा रस्ता",
    "impact.exposure": "नागरी वस्त्या प्रभाव",
    "impact.hospital": "जवळचे ट्रॉमा रुग्णालय",
    "impact.action": "शिफारस केलेली कृती:",

    "btn.inspect": "जोखीम तपासा",
    "btn.report": "धोका नोंदवा",
    "btn.dispatch": "इशारा पाठवा",
    "btn.gps": "माझे स्थान वापरा (GPS)",
    "btn.search": "शोधा",
    "btn.verify": "पडताळणी करा (+12 गुण)",
    "btn.reject": "नाकारा",
    "btn.escalate": "इशारा वाढवा",
  },
  ml: {
    "nav.brand": "ജിയോസെൻട്രി",
    "nav.tagline": "എഐ ഉരുൾപൊട്ടൽ മുൻകൂർ മുന്നറിയിപ്പും അടിയന്തര മുൻഗണനയും",
    "nav.map": "ജിഐഎസ് മാപ്പ്",
    "nav.priority": "തീവ്ര ദുരന്ത മേഖലകൾ",
    "nav.report": "അപകടം റിപ്പോർട്ട് ചെയ്യുക",
    "nav.engine": "റിസ്ക് എഞ്ചിൻ",
    "nav.validator": "പരിശോധനാ കൺസോൾ",
    "nav.alerts": "മുന്നറിയിപ്പ് കേന്ദ്രം",
    "nav.analytics": "അനലിറ്റിക്സ്",
    "nav.health": "സിസ്റ്റം ഹെൽത്ത്",
    "nav.signin": "ലോഗിൻ",

    "risk.low": "കുറഞ്ഞ സാധ്യത",
    "risk.moderate": "മിതമായ സാധ്യത",
    "risk.high": "ഉയർന്ന സാധ്യത",
    "risk.critical": "അതിതീവ്ര സാധ്യത",
    "risk.trend.increasing": "വർദ്ധിക്കുന്നു",
    "risk.trend.stable": "സ്ഥിരമാണ്",
    "risk.trend.decreasing": "കുറയുന്നു",

    "metric.probability": "ഉരുൾപൊട്ടൽ സാധ്യത",
    "metric.hazard": "പാരിസ്ഥിതിക അപകടം",
    "metric.exposure": "ജനസംഖ്യാ സാന്ദ്രത",
    "metric.priority": "രക്ഷാപ്രവർത്തന മുൻഗണന",

    "env.title": "പാരിസ്ഥിതിക അവസ്ഥകൾ",
    "env.temp": "താപനില",
    "env.rain24": "24 മണിക്കൂർ മഴ",
    "env.rain7d": "7 ദിവസത്തെ ആകെ മഴ",
    "env.slope": "ചെരിവ്",
    "env.soil": "മണ്ണിലെ ഈർപ്പം",
    "env.elevation": "ഉയരം",
    "env.geology": "ഭൂപ്രകൃതി",

    "hist.title": "ചരിത്രപരമായ വിവരങ്ങൾ",
    "hist.incidents": "മുൻകാല സംഭവങ്ങൾ",
    "hist.susceptibility": "സാധ്യത സൂചിക",
    "hist.last": "അവസാന സംഭവം",
    "hist.peak": "കൂടുതൽ അപകട സാധ്യതയുള്ള മാസം",
    "hist.rule": "മഴയും ഉരുൾപൊട്ടലും തമ്മിലുള്ള ബന്ധം:",

    "impact.title": "ആശുപത്രികളും റോഡുകളും",
    "impact.road": "പ്രധാന റോഡ്",
    "impact.exposure": "ജനവാസ മേഖലകൾ",
    "impact.hospital": "അടുത്തുള്ള ട്രോമ ആശുപത്രി",
    "impact.action": "ശുപാർശ ചെയ്യുന്ന നടപടി:",

    "btn.inspect": "റിസ്ക് പരിശോധിക്കുക",
    "btn.report": "റിപ്പോർട്ട് ചെയ്യുക",
    "btn.dispatch": "മുന്നറിയിപ്പ് നൽകുക",
    "btn.gps": "എന്റെ ലൊക്കേഷൻ ഉപയോഗിക്കുക (GPS)",
    "btn.search": "തിരയുക",
    "btn.verify": "സ്ഥിരീകരിക്കുക (+12 pts)",
    "btn.reject": "നിരസിക്കുക",
    "btn.escalate": "അടിയന്തര മുന്നറിയിപ്പ്",
  },
  bn: {
    "nav.brand": "জিওসেন্ট্রি",
    "nav.tagline": "এআই ভূমিধস আগাম সতর্কতা ও জরুরি প্রতিক্রিয়া ব্যবস্থা",
    "nav.map": "জিআইএস মানচিত্র",
    "nav.priority": "উচ্চ ঝুঁকি এলাকা",
    "nav.report": "বিপদ রিপোর্ট করুন",
    "nav.engine": "ঝুঁকি ক্যালকুলেটর",
    "nav.validator": "যাচাইকারী কনসোল",
    "nav.alerts": "সতর্কতা কেন্দ্র",
    "nav.analytics": "বিশ্লেষণ ও প্রবণতা",
    "nav.health": "সিস্টেম স্বাস্থ্য",
    "nav.signin": "লগইন",

    "risk.low": "কম ঝুঁকি",
    "risk.moderate": "মাঝারি ঝুঁকি",
    "risk.high": "উচ্চ ঝুঁকি",
    "risk.critical": "মারাত্মক ঝুঁকি",
    "risk.trend.increasing": "প্রবণতা: বৃদ্ধি পাচ্ছে",
    "risk.trend.stable": "প্রবণতা: স্থিতিশীল",
    "risk.trend.decreasing": "প্রবণতা: হ্রাস পাচ্ছে",

    "metric.probability": "ভূমিধসের সম্ভাবনা",
    "metric.hazard": "পরিবেশগত বিপদ",
    "metric.exposure": "জনসংখ্যা ও সম্পদের ঝুঁকি",
    "metric.priority": "প্রতিক্রিয়া অগ্রাধিকার",

    "env.title": "পরিবেশগত পরিস্থিতি",
    "env.temp": "তাপমাত্রা",
    "env.rain24": "২৪ ঘণ্টার বৃষ্টিপাত",
    "env.rain7d": "৭ দিনের মোট বৃষ্টিপাত",
    "env.slope": "ঢালের কোণ",
    "env.soil": "মাটির আর্দ্রতা",
    "env.elevation": "উচ্চতা",
    "env.geology": "ভূতাত্ত্বিক গঠন",

    "hist.title": "ঐতিহাসিক তথ্য ও প্রতিক্রিয়া",
    "hist.incidents": "অতীতের ঘটনা",
    "hist.susceptibility": "মূল সংবেদনশীলতা",
    "hist.last": "সর্বশেষ বড় ঘটনা",
    "hist.peak": "সর্বোচ্চ ঝুঁকিপূর্ণ সময়",
    "hist.rule": "বৃষ্টিপাত ও ভূমিধসের সম্পর্ক:",

    "impact.title": "জরুরি হাসপাতাল ও রাস্তাঘাট",
    "impact.road": "গুরুত্বপূর্ণ সড়ক",
    "impact.exposure": "জনবসতি প্রভাব",
    "impact.hospital": "নিকটতম ট্রমা হাসপাতাল",
    "impact.action": "প্রয়োজনীয় ব্যবস্থা:",

    "btn.inspect": "ঝুঁকি দেখুন",
    "btn.report": "রিপোর্ট জমা দিন",
    "btn.dispatch": "সতর্কতা পাঠান",
    "btn.gps": "বর্তমান অবস্থান (GPS)",
    "btn.search": "অনুসন্ধান",
    "btn.verify": "যাচাই করুন (+12)",
    "btn.reject": "প্রত্যাখ্যান",
    "btn.escalate": "সতর্কতা বৃদ্ধি",
  },
};

function setAppLanguage(langCode) {
  if (!I18N_DICTIONARY[langCode]) langCode = 'en';
  localStorage.setItem('geosentry_lang', langCode);
  applyTranslations(langCode);
}

function applyTranslations(langCode) {
  const dict = I18N_DICTIONARY[langCode] || I18N_DICTIONARY['en'];
  const elements = document.querySelectorAll('[data-i18n]');
  
  elements.forEach((el) => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) {
      if (el.tagName === 'INPUT' && el.getAttribute('placeholder')) {
        el.setAttribute('placeholder', dict[key]);
      } else {
        el.innerText = dict[key];
      }
    }
  });

  const selector = document.getElementById('global-lang-selector');
  if (selector) selector.value = langCode;
}

document.addEventListener('DOMContentLoaded', () => {
  const savedLang = localStorage.getItem('geosentry_lang') || 'en';
  applyTranslations(savedLang);
});
