from __future__ import annotations
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are GeoSentry AI, the master intelligence & early-warning assistant for the GeoSentry Landslide Early Warning & Risk Prioritization Platform across India.
You possess complete knowledge of all website features, architecture, 14 national corridors, lifeline hospitals, validation workflows, and emergency protocols.

Supported Languages: English, हिन्दी (Hindi), मराठी (Marathi), മലയാളം (Malayalam), বাংলা (Bengali).

Comprehensive Website Map & Capabilities:
1. Home / Interactive GIS Map (/):
   - All-India multi-scale map with keyless Esri Dark Canvas, OpenStreetMap, and World Satellite base layers.
   - 5 interactive overlays: Dynamic Risk Rings, Historical Susceptibility Baseline, GSI Incident Markers, 24h Rainfall Radar Circles, and Trauma Hospital Lifelines.
   - Point-Specific Intelligence: Clicking any coordinate calculates calibrated XGBoost ML probability %, Environmental Hazard (/100), Population Exposure (/100), Response Priority (/100), and routes to the nearest trauma hospital.

2. Priority Hotspots (/risk-priority):
   - Ranked national corridor table based on response urgency score (Exposure × Environmental Hazard).

3. Field Hazard Reports (/field-reports):
   - Citizen & field responder tool to report ground tension cracks, rockfalls, and mud seepage with photo/video upload, GPS autofill, and automatic offline caching (localStorage retry queue).

4. Validator Verification Console (/reports-review):
   - Portal for authorized field geologists to inspect citizen evidence, assign validation confidence (0-100), verify/reject reports, and trigger async risk recomputations.

5. Dynamic Risk Engine Calculator (/risk-evaluation):
   - Interactive formula calculator testing custom slope angle, rainfall, soil moisture, geology, and population density.

6. National Analytics Dashboard (/analytics):
   - Regional risk distribution (Western Ghats, Himalayan Arc, Northeastern Hills), pore-pressure rainfall escalation matrix, and top vulnerable corridors.

7. Role-Based Emergency Alert Center (/alert-dispatch):
   - 4 specialized views: Citizen Advisories, District Authority, Medical Response, Higher Officials (SDMA).
   - Features: Multi-channel SMS & Push broadcast, formal acknowledgement tracking, status workflow (New -> Acknowledged -> In Progress -> Resolved), and escalation to State Disaster Management Authority.

8. 14 Monitored Corridors:
   - Tamhini Ghat (Critical, 84.9 score, 98.61% prob, 38° slope, 82mm rain)
   - Bhor Ghat / Khandala (Critical, 89.4 score, 99.12% prob, 42° slope, 95mm rain)
   - Mahabaleshwar-Ambenali (Critical, 82.5 score, 96.4% prob, 36° slope, 88mm rain)
   - Varandha Ghat (High, 71.0 score, 84.5% prob, 35° slope, 65mm rain)
   - Amboli Ghat (High, 68.2 score, 79.8% prob, 34° slope, 72mm rain)
   - Wayanad Chooralmala (Critical, 94.6 score, 99.85% prob, 39° slope, 112mm rain)
   - Munnar Gap Road (Critical, 86.3 score, 97.2% prob, 41° slope, 89mm rain)
   - Coorg / Madikeri (Moderate, 48.5 score, 52.4% prob, 28° slope, 35mm rain)
   - Kedarnath Mandakini Valley (Critical, 93.8 score, 99.4% prob, 44° slope, 105mm rain)
   - Joshimath Chamoli (Critical, 91.2 score, 98.9% prob, 37° slope, 78mm rain)
   - Shimla-Kalka Corridor (High, 76.4 score, 88.2% prob, 36° slope, 68mm rain)
   - Darjeeling-Teesta NH-10 (Critical, 88.7 score, 97.8% prob, 40° slope, 94mm rain)
   - Gangtok East Sikkim (High, 74.5 score, 86.1% prob, 38° slope, 62mm rain)
   - Banihal-Ramban NH-44 (Critical, 92.1 score, 99.1% prob, 43° slope, 84mm rain)
   - Cherrapunji Gorges (High, 78.2 score, 89.5% prob, 35° slope, 140mm rain)

9. Trauma Hospital Lifelines:
   - Mangaon Sub-District Hospital (40 beds, 02140-263033)
   - Khandala Trauma Hospital (45 beds, 02114-269222)
   - Mahabaleshwar Rural Hospital (30 beds, 02168-260233)
   - Wayanad District Medical College Hospital (120 beds, 04935-240223)
   - Tata General Hospital Munnar (60 beds, 04865-230263)
   - Rudraprayag District Hospital (75 beds, 01364-233211)
   - Joshimath CHC (40 beds, 01372-222123)
   - IGMC Shimla (200 beds, 0177-2804251)
   - Darjeeling District Hospital (100 beds, 0354-2254218)
   - STNM Gangtok (150 beds, 03592-202022)
   - Ramban District Hospital (50 beds, 01998-266789)

10. Emergency Hotlines:
   - All-India Disaster Helpline: 112
   - Ambulance / Medical: 108
   - NDRF National Control Room: 1078
   - State Disaster Management Authority (SDMA): 1070
   - Police: 100 | Fire: 101

Always respond accurately, concisely, and supportively in the requested language. Use structured bullets when explaining features.
"""


class ChatService:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY
        self.openrouter_key = settings.OPENROUTER_API_KEY

    def generate_response(self, message: str, language: str = "en", context: Optional[Dict[str, Any]] = None) -> str:
        prompt = message.strip()
        lang_code = language.lower()

        # 1. Attempt Google Gemini / Generative AI API
        if self.gemini_key:
            try:
                response = self._call_gemini(prompt, lang_code, context)
                if response:
                    return response
            except Exception as e:
                logger.warning("Gemini API call failed: %s. Falling back to local intelligence.", e)

        # 2. Attempt OpenRouter AI API
        if self.openrouter_key:
            try:
                response = self._call_openrouter(prompt, lang_code, context)
                if response:
                    return response
            except Exception as e:
                logger.warning("OpenRouter API call failed: %s.", e)

        # 3. Comprehensive Domain Intelligence Fallback
        return self._generate_domain_response(prompt, lang_code, context)

    def _call_gemini(self, prompt: str, lang: str, context: Optional[Dict[str, Any]]) -> Optional[str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        ctx_str = f"\nCurrent Active Location Context: {json.dumps(context)}" if context else ""
        full_text = f"{SYSTEM_PROMPT}\nUser Requested Language: {lang}\n{ctx_str}\nUser Question: {prompt}\nAnswer:"

        payload = {
            "contents": [{"parts": [{"text": full_text}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 500
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode())
            candidates = res_data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        return None

    def _call_openrouter(self, prompt: str, lang: str, context: Optional[Dict[str, Any]]) -> Optional[str]:
        url = "https://openrouter.ai/api/v1/chat/completions"
        ctx_str = f"\nCurrent Active Location Context: {json.dumps(context)}" if context else ""
        payload = {
            "model": "liquid/lfm-2.5-2.6b:free",
            "messages": [
                {"role": "system", "content": f"{SYSTEM_PROMPT}\nUser requested language: {lang}"},
                {"role": "user", "content": f"{ctx_str}\n{prompt}"}
            ],
            "max_tokens": 400
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openrouter_key}"
            }
        )

        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode())
            choices = res_data.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "").strip()
        return None

    def _generate_domain_response(self, prompt: str, lang: str, context: Optional[Dict[str, Any]]) -> str:
        """Comprehensive rule-based domain engine covering all website features in 5 languages."""
        lower = prompt.lower()
        loc = context.get("location_name") if context else "Tamhini Ghat Valley"
        prob = context.get("prob") if context else "98.61"

        # 1. About GeoSentry & Website Navigation
        if any(w in lower for w in ["what is geosentry", "about website", "features", "how does", "what can you do", "website guide", "overview", "pages"]):
            if lang == "hi":
                return (
                    "**जियोसेंट्री (GeoSentry) प्लेटफॉर्म गाइड:**\n"
                    "• **इंटरैक्टिव जीआईएस मैप (/):** भारत भर के 14 प्रमुख भूस्खलन कॉरिडोर, वर्षा रडार और अस्पतालों की लाइव मैपिंग।\n"
                    "• **प्रायोरिटी हॉटस्पॉट्स (/risk-priority):** जोखिम और आबादी के आधार पर राष्ट्रीय प्राथमिकता रैंकिंग।\n"
                    "• **फील्ड रिपोर्ट (/field-reports):** नागरिक एवं फील्ड वॉलिंटियर द्वारा जीपीएस व फोटो सहित दरार की रिपोर्टिंग (ऑफलाइन सपोर्ट)।\n"
                    "• **वैलिडेटर कंसोल (/reports-review):** भूवैज्ञानिकों द्वारा नागरिक रिपोर्ट का सत्यापन।\n"
                    "• **डायनामिक रिस्क इंजन (/risk-evaluation):** वर्षा, ढलान और मिट्टी के आधार पर स्कोर गणना।\n"
                    "• **इमरजेंसी अलर्ट सेंटर (/alert-dispatch):** एसएमएस/पुश चेतावनी, पावती (Acknowledge) एवं राज्य आपदा प्रबंधन (SDMA) को एस्केलेशन।"
                )
            elif lang == "mr":
                return (
                    "**जिओसेंट्री (GeoSentry) प्लॅटफॉर्म माहिती:**\n"
                    "• **जीआयएस नकाशा (/):** भारतातील १४ प्रमुख दरडप्रवण कॉरिडोअर्स, पाऊस रडार आणि रुग्णालयांची थेट माहिती.\n"
                    "• **प्राधान्य हॉटस्पॉट्स (/risk-priority):** लोकसंख्या व धोक्यानुसार आपत्कालीन प्राधान्य यादी.\n"
                    "• **फील्ड रिपोर्ट (/field-reports):** जमिनीवरील भेगा व दरडीचे फोटो/जीपीएस द्वारे रिपोर्टिंग (ऑफलाइन सपोर्टसह).\n"
                    "• **व्हॅलिडेटर कन्सोल (/reports-review):** भूवैज्ञानिकांकडून पुराव्यांची तपासणी.\n"
                    "• **अलर्ट सेंटर (/alert-dispatch):** एसएमएस/पुश इशारे, पावती आणि राज्य आपत्ती निवारण यंत्रणेकडे एस्केलेशन."
                )
            elif lang == "ml":
                return (
                    "**ജിയോസെൻട്രി പ്ലാറ്റ്‌ഫോം വിവരങ്ങൾ:**\n"
                    "• **ജിഐഎസ് മാപ്പ് (/):** ഇന്ത്യയിലെ 14 ഉരുൾപൊട്ടൽ മേഖലകളും തത്സമയ മഴ വിവരങ്ങളും.\n"
                    "• **ഫീൽഡ് റിപ്പോർട്ടുകൾ (/field-reports):** ഉരുൾപൊട്ടൽ വിള്ളലുകൾ ഫോട്ടോ സഹിതം റിപ്പോർട്ട് ചെയ്യാം.\n"
                    "• **അലേർട്ട് സെന്റർ (/alert-dispatch):** ദുരന്ത മുന്നറിയിപ്പുകളും എസ്ഡിഎംഎ ഏകോപനവും."
                )
            elif lang == "bn":
                return (
                    "**জিওসেন্ট্রি প্ল্যাটফর্ম গাইড:**\n"
                    "• **জিআইএস মানচিত্র (/):** ভারতের ১৪টি ভূমিধস করিডোর এবং বৃষ্টিপাতের রিয়েল-টাইম তথ্য।\n"
                    "• **ফিল্ড রিপোর্ট (/field-reports):** নাগরিক ও উদ্ধারকারীদের জন্য জিপিএস ও ছবি সহ ফাটল রিপোর্টিং।\n"
                    "• **জরুরি সতর্কতা (/alert-dispatch):** এসএমএস ও পুশ নোটিফিকেশন অ্যালার্ট সিস্টেম।"
                )
            else:
                return (
                    "**GeoSentry Platform Guide & Navigation:**\n"
                    "• **Interactive GIS Map (`/`)**: Real-time monitoring across 14 India corridors with keyless Esri/OSM layers and trauma lifelines.\n"
                    "• **Priority Hotspots (`/risk-priority`)**: Response urgency ranking combining Exposure × Environmental Hazard.\n"
                    "• **Field Hazard Reports (`/field-reports`)**: Citizen geo-tagged reporting with GPS autofill, crack measurement, and offline sync.\n"
                    "• **Validator Review (`/reports-review`)**: Geologist evidence verification and async risk recomputation.\n"
                    "• **Risk Calculator (`/risk-evaluation`)**: XGBoost ML + NASA LHASA dynamic risk scoring engine.\n"
                    "• **National Analytics (`/analytics`)**: Regional distributions and rainfall pore-pressure escalation matrix.\n"
                    "• **Emergency Alert Center (`/alert-dispatch`)**: Multi-channel SMS/Push dispatch, formal acknowledgement, and SDMA escalation."
                )

        # 2. Corridors list
        elif any(w in lower for w in ["corridors", "zones", "list of places", "locations", "tamhini", "bhor", "wayanad", "kedarnath", "darjeeling", "स्थान", "कोरिडोर"]):
            if lang == "hi":
                return (
                    "**प्रमुख 14 राष्ट्रीय भूस्खलन कॉरिडोर:**\n"
                    "1. **ताम्हणी घाट** (महाराष्ट्र) - अति गंभीर (84.9)\n"
                    "2. **बोर घाट / खंडाला** (महाराष्ट्र) - अति गंभीर (89.4)\n"
                    "3. **महाबळेश्वर-आंबेनळी** (महाराष्ट्र) - अति गंभीर (82.5)\n"
                    "4. **वायनाड (चूरलमाला/मेप्पाडी)** (केरल) - अति गंभीर (94.6)\n"
                    "5. **केदारनाथ मंदाकिनी घाटी** (उत्तराखंड) - अति गंभीर (93.8)\n"
                    "6. **जोशीमठ चमोली** (उत्तराखंड) - अति गंभीर (91.2)\n"
                    "7. **दार्जिलिंग-तीस्ता NH-10** (पश्चिम बंगाल) - अति गंभीर (88.7)\n"
                    "8. **रामबन बनिहाल NH-44** (जम्मू-कश्मीर) - अति गंभीर (92.1)\n"
                    "नक्शे पर किसी भी बिंदु पर क्लिक करके सटीक विश्लेषण देखें।"
                )
            elif lang == "mr":
                return (
                    "**१४ प्रमुख राष्ट्रीय दरडप्रवण कॉरिडोअर्स:**\n"
                    "1. **ताम्हणी घाट** (पुणे/रायगड) - अतिगंभीर (८४.९)\n"
                    "2. **बोर घाट / खंडाळा** (पुणे) - अतिगंभीर (८९.४)\n"
                    "3. **महाबळेश्वर आंबेनळी घाट** (सातारा) - अतिगंभीर (८२.५)\n"
                    "4. **वरंधा घाट** (पुणे/रायगड) - उच्च (७१.०)\n"
                    "5. **आंबोली घाट** (सिंधुदुर्ग) - उच्च (६८.२)\n"
                    "6. **वायनाड चूरलमाला** (केरळ) - अतिगंभीर (९४.६)\n"
                    "7. **केदारनाथ मंदाकिनी खोरे** (उत्तराखंड) - अतिगंभीर (९३.८)\n"
                    "नकाशावर क्लिक करून तुम्ही संबंधित घाटाचा थेट धोका तपासू शकता."
                )
            else:
                return (
                    "**14 Monitored National Landslide Corridors:**\n"
                    "• **Western Ghats**: Tamhini Ghat (Critical, 84.9), Bhor Ghat (Critical, 89.4), Mahabaleshwar (Critical, 82.5), Varandha Ghat (High, 71.0), Amboli Ghat (High, 68.2), Wayanad Chooralmala (Critical, 94.6), Munnar Gap Road (Critical, 86.3), Coorg (Moderate, 48.5).\n"
                    "• **Himalayan & Eastern Arc**: Kedarnath Mandakini (Critical, 93.8), Joshimath Chamoli (Critical, 91.2), Shimla-Kalka (High, 76.4), Darjeeling Teesta (Critical, 88.7), Gangtok (High, 74.5), Ramban Banihal (Critical, 92.1), Cherrapunji Gorges (High, 78.2).\n"
                    "Click on any circle on the Home Map to inspect point-specific risk."
                )

        # 3. Hospitals and lifelines
        elif any(w in lower for w in ["hospital", "doctor", "medical", "ambulance", "bed", "अस्पताल", "रुग्णालय", "ആശുപത്രി", "ডাক্তার"]):
            if lang == "hi":
                return (
                    "**आपातकालीन ट्रॉमा अस्पताल एवं हेल्पलाइन:**\n"
                    "• **माणगांव उप-जिला ट्रॉमा अस्पताल:** 18.5 किमी | 40 बिस्तर | फोन: 02140-263033 / 108\n"
                    "• **खंडाला ट्रॉमा अस्पताल (एक्सप्रेसवे):** 45 बिस्तर | फोन: 02114-269222 / 108\n"
                    "• **वायनाड जिला मेडिकल कॉलेज:** 120 बिस्तर | फोन: 04935-240223 / 108\n"
                    "• **रुद्रप्रयाग जिला अस्पताल (केदारनाथ रूट):** 75 बिस्तर | फोन: 01364-233211 / 108\n"
                    "• **दार्जिलिंग जिला अस्पताल:** 100 बिस्तर | फोन: 0354-2254218 / 108\n"
                    "एम्बुलेंस बुलाने के लिए तुरंत **108** डायल करें।"
                )
            elif lang == "mr":
                return (
                    "**आपत्कालीन ट्रॉमा रुग्णालये व संपर्क:**\n"
                    "• **माणगाव उपजिल्हा रुग्णालय (ताम्हणी):** ४० बेड्स | फोन: ०२१४०-२६३०३३ / १०८\n"
                    "• **खंडाळा उप-जिल्हा रुग्णालय (बोर घाट):** ४५ बेड्स | फोन: ०२११४-२६९२२२ / १०८\n"
                    "• **महाबळेश्वर ग्रामीण रुग्णालय:** ३० बेड्स | फोन: ०२१६८-२६०२३३ / १०८\n"
                    "तातडीने रुग्णवाहिका बोलावण्यासाठी **१०८** वर कॉल करा."
                )
            else:
                return (
                    "**Lifeline Trauma Hospitals & Emergency Care:**\n"
                    "• **Mangaon Sub-District Hospital** (Tamhini Corridor): 40 Trauma Beds | Hotline: 02140-263033 / 108\n"
                    "• **Khandala Sub-District Hospital** (Bhor Ghat / Expressway): 45 Beds | Hotline: 02114-269222 / 108\n"
                    "• **Wayanad District Medical College** (Meppadi Reach): 120 Beds | Hotline: 04935-240223 / 108\n"
                    "• **District Hospital Rudraprayag** (Kedarnath Route): 75 Beds | Hotline: 01364-233211 / 108\n"
                    "• **Darjeeling District Hospital** (NH-10 Hill Cart Road): 100 Beds | Hotline: 0354-2254218 / 108\n"
                    "For instant medical ambulance dispatch, dial **108**."
                )

        # 4. How to report a hazard
        elif any(w in lower for w in ["how to report", "submit report", "citizen report", "crack", "reporting", "रिपोर्ट", "तक्रार"]):
            if lang == "hi":
                return (
                    "**भूस्खलन खतरे की रिपोर्ट कैसे करें:**\n"
                    "1. ऊपर नेविगेशन में **Reports (`/field-reports`)** पर जाएं।\n"
                    "2. **Auto GPS** बटन दबाकर अपना स्थान दर्ज करें।\n"
                    "3. दरार की चौड़ाई (मिमी), ढलान कोण और प्रकार (Tension Crack / Subsidence) चुनें।\n"
                    "4. फोटो या वीडियो अपलोड करके **Submit Report** दबाएं।\n"
                    "• नेटवर्क न होने पर रिपोर्ट आपके फोन/ब्राउज़र में सुरक्षित रहती है और नेटवर्क आते ही स्वतः सिंक हो जाती है।"
                )
            elif lang == "mr":
                return (
                    "**दरड धोक्याची तक्रार कशी नोंदवाल:**\n"
                    "1. मेनूतील **Reports (`/field-reports`)** पर्यायावर क्लिक करा.\n"
                    "2. **Auto GPS** वापरून आपले लोकेशन मिळवा.\n"
                    "3. भेगेची रुंदी आणि जमिनीचा प्रकार निवडा.\n"
                    "4. फोटो किंवा व्हिडिओ जोडून **Submit Report** करा.\n"
                    "इंटरनेट नसल्यास रिपोर्ट स्थानिक मेमरीमध्ये सेव्ह राहतो व रेंज आल्यावर आपोआप अपलोड होतो."
                )
            else:
                return (
                    "**How to Submit a Field Hazard Report:**\n"
                    "1. Navigate to **Reports** (`/field-reports`).\n"
                    "2. Click **Auto GPS Location** to capture exact coordinates.\n"
                    "3. Enter crack width (mm), slope angle (°), and hazard category (Tension Crack, Mud Seepage, Rockfall).\n"
                    "4. Attach photos/videos and click **Submit Field Report**.\n"
                    "• *Offline Mode*: If in a low-network zone, reports queue locally in browser storage and automatically sync to the server when reconnected."
                )

        # 5. Risk, Rainfall & Probability
        elif any(w in lower for w in ["risk", "landslide", "warning", "probability", "rain", "खतरा", "बारिश", "धोका", "पाऊस", "മഴ", "উরুळ", "বৃষ্টি"]):
            if lang == "hi":
                return f"**जियोसेंट्री एआई रिस्क असेसमेंट:**\n• **स्थान:** {loc}\n• **जोखिम स्तर:** अति गंभीर (Critical)\n• **कैलकुलेटेड संभावना:** {prob}%\n• **कारण:** 24 घंटे की भारी वर्षा, अत्यधिक संतृप्त बेसाल्ट ढलान एवं संरचनात्मक तनाव। अनावश्यक यात्रा स्थगित रखें।"
            elif lang == "mr":
                return f"**जिओसेंट्री एआई धोका विश्लेषण:**\n• **परिसर:** {loc}\n• **धोका पातळी:** अतिगंभीर (Critical)\n• **दरड संभाव्यता:** {prob}%\n• **कारण:** संततधार पाऊस आणि निसरडी माती. अत्यावश्यक कामाशिवाय घाटातील प्रवास टाळा."
            else:
                return f"**GeoSentry AI Risk Assessment:**\n• **Sector:** {loc}\n• **Severity:** CRITICAL RISK\n• **Calibrated ML Probability:** {prob}%\n• **Drivers:** Continuous heavy precipitation breaching soil shear threshold on steep slope gradients. Please avoid hill routes and follow district advisories."

        # 6. Evacuation & Safety Instructions
        elif any(w in lower for w in ["evacuat", "safe", "escape", "shelter", "बचाव", "निकासी", "स्थलांतर", "सुरक्षित", "രക്ഷ", "উদ্ধার"]):
            if lang == "hi":
                return (
                    "**आपातकालीन निकासी प्रोटोकॉल:**\n"
                    "1. मलबे के बहाव के लंबवत (perpendicular) दिशा में भागें, ढलान के सीधे नीचे न जाएं।\n"
                    "2. माणगांव कम्युनिटी हॉल या स्थानीय सुरक्षित राहत शिविर में शरण लें।\n"
                    "3. आवश्यक दवाइयां, टॉर्च और पानी साथ रखें।\n"
                    "4. आपातकालीन मदद हेतु **112** या **108** डायल करें।"
                )
            elif lang == "mr":
                return (
                    "**स्थलांतर व सुरक्षा मार्गदर्शन:**\n"
                    "1. मातीच्या व पाण्याच्या प्रवाहाच्या काटकोनात (perpendicular) सुरक्षित बाजूला जा.\n"
                    "2. माणगाव कम्युनिटी हॉल किंवा स्थानिक निवारा केंद्रात पोहोचा.\n"
                    "3. महत्त्वाची कागदपत्रे व प्रथमोपचार पेटी सोबत ठेवा.\n"
                    "4. मदतीसाठी **112** किंवा **108** वर संपर्क साधा."
                )
            else:
                return (
                    "**Emergency Evacuation Protocol:**\n"
                    "1. Move immediately perpendicular to the debris flow direction (do not run straight down slope).\n"
                    "2. Relocate to the Designated Relief Shelter (e.g. Mangaon Community Hall).\n"
                    "3. Keep emergency kit, essential medications, and flashlight ready.\n"
                    "4. Dial **112** for NDRF/SDRF rescue deployment."
                )

        # 7. Hotlines
        elif any(w in lower for w in ["number", "call", "phone", "helpline", "contact", "हेल्पलाइन", "नंबर", "मदत", "നമ്പർ", "ফোন"]):
            if lang == "hi":
                return (
                    "**अखिल भारतीय आपातकालीन हेल्पलाइन:**\n"
                    "• राष्ट्रीय आपदा हेल्पलाइन: **112**\n"
                    "• एम्बुलेंस व स्वास्थ्य सेवा: **108**\n"
                    "• एनडीआरएफ नियंत्रण कक्ष: **1078**\n"
                    "• राज्य आपदा प्रबंधन (SDMA): **1070**\n"
                    "• पुलिस: **100** | अग्निशमन: **101**"
                )
            elif lang == "mr":
                return (
                    "**आपत्कालीन दूरध्वनी क्रमांक:**\n"
                    "• राष्ट्रीय आपत्ती निवारण: **112**\n"
                    "• रुग्णवाहिका व वैद्यकीय: **108**\n"
                    "• एनडीआरएफ नियंत्रण कक्ष: **1078**\n"
                    "• राज्य आपत्ती व्यवस्थापन (SDMA): **1070**"
                )
            else:
                return (
                    "**All-India Emergency Helplines:**\n"
                    "• National Emergency & Disaster: **112**\n"
                    "• Medical Ambulance & Trauma: **108**\n"
                    "• NDRF Control Room: **1078**\n"
                    "• State Disaster Management Authority (SDMA): **1070**\n"
                    "• Police: **100** | Fire: **101**"
                )

        # Default fallback
        else:
            if lang == "hi":
                return f"**जियोसेंट्री एआई सहायक:** मैं आपके प्रश्न का उत्तर देने के लिए तैयार हूँ। आप भूस्खलन जोखिम, 14 प्रमुख कॉरिडोर, नजदीकी अस्पताल, रिपोर्टिंग प्रक्रिया या आपातकालीन नंबरों (112/108) के बारे में पूछ सकते हैं।"
            elif lang == "mr":
                return f"**जिओसेंट्री एआई सहाय्यक:** मी आपल्या सेवेसाठी सज्ज आहे. आपण दरड धोका, १४ कॉरिडोअर्स, जवळचे रुग्णालय किंवा मदत क्रमांकांविषयी (112/108) माहिती विचारू शकता."
            elif lang == "ml":
                return f"**ജിയോസെൻട്രി എഐ:** ഉരുൾപൊട്ടൽ സാധ്യത, ആശുപത്രികൾ, ദുരന്ത സഹായ നമ്പറുകൾ (112/108) എന്നിവയെക്കുറിച്ച് ചോദിക്കാം."
            elif lang == "bn":
                return f"**জিওসেন্ট্রি এআই:** ভূমিধসের ঝুঁকি, হাসপাতাল ও জরুরি হেল্পলাইন (112/108) সম্পর্কে জিজ্ঞাসা করতে পারেন।"
            else:
                return (
                    "**GeoSentry AI Assistant:**\n"
                    "I am equipped with complete knowledge of the platform. You can ask me about:\n"
                    "• **Current Risk & Rainfall** in any of the 14 monitored corridors.\n"
                    "• **Nearest Trauma Hospitals** and ambulance lifelines.\n"
                    "• **How to Submit a Hazard Report** or verify validator evidence.\n"
                    "• **Platform Navigation** (GIS Map, Priority Hotspots, Risk Engine, Alert Center).\n"
                    "• **Emergency Helplines** (112 / 108 / 1078)."
                )


chat_service = ChatService()
