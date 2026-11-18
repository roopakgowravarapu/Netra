export type Language = 'en' | 'te' | 'hi';

export interface TranslationDictionary {
  appName: string;
  tagline: string;
  navHome: string;
  navScreening: string;
  navDashboard: string;
  navDoctor: string;
  navDocs: string;
  navLanguage: string;
  
  // Connectivity
  online: string;
  lowConnectivity: string;
  offline: string;
  retryUpload: string;
  offlineBanner: string;

  // Screening Intake Form
  patientDetailsTitle: string;
  patientId: string;
  patientName: string;
  age: string;
  gender: string;
  male: string;
  female: string;
  other: string;
  diabetesType: string;
  type1: string;
  type2: string;
  gestational: string;
  none: string;
  diabetesDuration: string;
  years: string;
  eyeExamined: string;
  rightEyeOD: string;
  leftEyeOS: string;
  informedConsentLabel: string;
  informedConsentRequired: string;
  uploadFundusScan: string;
  dragDropHint: string;
  startScreening: string;
  screeningInProgress: string;

  // Quality Assessment
  qualityTitle: string;
  gradable: string;
  borderline: string;
  ungradable: string;
  sharpness: string;
  illumination: string;
  fovCoverage: string;
  retakeRecommended: string;
  claheEnhanced: string;

  // DR Grades
  grade0: string;
  grade1: string;
  grade2: string;
  grade3: string;
  grade4: string;

  // Results & Triage
  screeningResultsTitle: string;
  referableDR: string;
  nonReferableDR: string;
  confidence: string;
  uncertaintyWarning: string;
  specialistReviewAdvised: string;
  recommendation: string;
  maculaRiskIndicator: string;
  maculaRiskDesc: string;

  // Explainability Panels
  originalScan: string;
  gradcamHeatmap: string;
  gradcamNotice: string;
  lesionMap: string;
  retinalPlacesMap: string;
  vesselNetwork: string;
  compositeView: string;

  // Dashboard & Longitudinal
  specialistQueue: string;
  patientHistory: string;
  longitudinalTracking: string;
  progressionComparison: string;
  baselineVisit: string;
  currentVisit: string;
  stableFinding: string;
  longitudinalDisclaimer: string;
  clinicalNotes: string;
  confirmGrade: string;
  overrideGrade: string;
  requestRecapture: string;
  auditTrail: string;

  // Clinical Safety Disclaimer
  clinicalDisclaimer: string;
}

export const translations: Record<Language, TranslationDictionary> = {
  en: {
    appName: "Netra",
    tagline: "Explainable AI Platform for Retinal Screening & Decision Support",
    navHome: "Home",
    navScreening: "New Screening",
    navDashboard: "Specialist Dashboard",
    navDoctor: "Doctor Portal",
    navDocs: "Documentation",
    navLanguage: "Language",

    online: "Online",
    lowConnectivity: "Low Connectivity",
    offline: "Offline Mode",
    retryUpload: "Retry Upload",
    offlineBanner: "You are currently offline. Screening requires an active connection or sync. Ready to retry when connectivity resumes.",

    patientDetailsTitle: "Patient Demographics & Clinical Intake",
    patientId: "Patient ID",
    patientName: "Patient Full Name",
    age: "Age (Years)",
    gender: "Gender",
    male: "Male",
    female: "Female",
    other: "Other / Unspecified",
    diabetesType: "Diabetes Classification",
    type1: "Type 1 Diabetes",
    type2: "Type 2 Diabetes",
    gestational: "Gestational Diabetes",
    none: "None / Pre-diabetic",
    diabetesDuration: "Duration of Diabetes (Years)",
    years: "years",
    eyeExamined: "Eye Examined",
    rightEyeOD: "OD – Right Eye (Oculus Dexter)",
    leftEyeOS: "OS – Left Eye (Oculus Sinister)",
    informedConsentLabel: "Patient has provided informed consent for AI-assisted retinal screening.",
    informedConsentRequired: "Informed consent is mandatory prior to diagnostic screening.",
    uploadFundusScan: "Upload Color Fundus Photograph",
    dragDropHint: "Drag and drop a 45° macula-centered or optic disc fundus photograph (PNG, JPEG up to 10MB)",
    startScreening: "Analyze Retinal Scan",
    screeningInProgress: "Running 4x-TTA Inference, Quality Gate & Explainability...",

    qualityTitle: "Image Quality Assessment (IQA)",
    gradable: "Gradable Quality",
    borderline: "Borderline (Enhanced)",
    ungradable: "Ungradable Quality",
    sharpness: "Sharpness / Focus",
    illumination: "Illumination / Exposure",
    fovCoverage: "Retinal Field of View",
    retakeRecommended: "Retake Recommended",
    claheEnhanced: "Adaptive CLAHE Contrast Enhancement Applied",

    grade0: "Grade 0 – No Diabetic Retinopathy",
    grade1: "Grade 1 – Mild Non-Proliferative DR",
    grade2: "Grade 2 – Moderate Non-Proliferative DR",
    grade3: "Grade 3 – Severe Non-Proliferative DR",
    grade4: "Grade 4 – Proliferative Diabetic Retinopathy",

    screeningResultsTitle: "AI Retinal Screening Report",
    referableDR: "Referable DR (Specialist Evaluation Required)",
    nonReferableDR: "Non-Referable (Routine Annual Monitoring)",
    confidence: "Calibrated Confidence",
    uncertaintyWarning: "Borderline Confidence / Elevated Uncertainty",
    specialistReviewAdvised: "Prediction uncertainty is elevated. Specialist ophthalmological review is recommended rather than relying strictly on the automated grade.",
    recommendation: "Clinical Recommendation",
    maculaRiskIndicator: "Macular Threat Risk Indicator",
    maculaRiskDesc: "Observational indicator based on microaneurysms or exudates located within 1 disc diameter of the fovea. Autonomous DME diagnosis requires Optical Coherence Tomography (OCT).",

    originalScan: "Original Scan",
    gradcamHeatmap: "Grad-CAM Saliency",
    gradcamNotice: "Visualizes deep neural network activation attention driving classification; distinct from segmented retinal lesions.",
    lesionMap: "Segmented Lesions",
    retinalPlacesMap: "Retinal Anatomical Places",
    vesselNetwork: "Vascular Network",
    compositeView: "Composite Clinical View",

    specialistQueue: "Telemedicine Review Queue",
    patientHistory: "Patient Records & History",
    longitudinalTracking: "Longitudinal Retinal Tracking",
    progressionComparison: "Visit-to-Visit Comparison",
    baselineVisit: "Baseline Visit",
    currentVisit: "Current Visit",
    stableFinding: "Stable DR Grade Across Screening Interval",
    longitudinalDisclaimer: "Comparative alignment provides observational tracking between clinical visits. It does not replace serial fundus fluorescein angiography or specialist biomicroscopy.",
    clinicalNotes: "Specialist Clinical Notes",
    confirmGrade: "Confirm AI Assessment",
    overrideGrade: "Override DR Grade",
    requestRecapture: "Request Image Recapture",
    auditTrail: "Clinical Audit Trail",

    clinicalDisclaimer: "Netra is an AI-assisted retinal screening and clinical decision-support platform. It does not replace a qualified ophthalmologist or constitute an autonomous medical diagnosis.",
  },

  te: {
    appName: "నేత్ర (Netra)",
    tagline: "డయాబెటిక్ రెటినోపతి స్క్రీనింగ్ మరియు ఎక్స్‌ప్లెయినబుల్ AI ప్లాట్‌ఫారమ్",
    navHome: "హోమ్",
    navScreening: "కొత్త స్క్రీనింగ్",
    navDashboard: "స్పెషలిస్ట్ డ్యాష్‌బోర్డ్",
    navDoctor: "డాక్టర్ పోర్టల్",
    navDocs: "డాక్యుమెంటేషన్",
    navLanguage: "భాష",

    online: "ఆన్‌లైన్",
    lowConnectivity: "తక్కువ కనెక్టివిటీ",
    offline: "ఆఫ్‌లైన్ మోడ్",
    retryUpload: "మళ్ళీ అప్‌లోడ్ చేయండి",
    offlineBanner: "మీరు ప్రస్తుతం ఆఫ్‌లైన్‌లో ఉన్నారు. ఇంటర్నెట్ పునరుద్ధరించబడినప్పుడు స్వయంచాలకంగా తిరిగి ప్రయత్నించవచ్చు.",

    patientDetailsTitle: "రోగి వివరాలు మరియు నమోదు",
    patientId: "రోగి సంఖ్య (Patient ID)",
    patientName: "రోగి పూర్తి పేరు",
    age: "వయస్సు (సంవత్సరాలు)",
    gender: "లింగం",
    male: "పురుషుడు",
    female: "స్త్రీ",
    other: "ఇతర",
    diabetesType: "డయాబెటిస్ రకం",
    type1: "టైప్ 1 డయాబెటిస్",
    type2: "టైప్ 2 డయాబెటిస్",
    gestational: "గర్భధారణ మధుమేహం",
    none: "లేదు / ప్రీ-డయాబెటిక్",
    diabetesDuration: "డయాబెటిస్ కాలవ్యవధి (సంవత్సరాలు)",
    years: "సంవత్సరాలు",
    eyeExamined: "పరీక్షించిన కన్ను",
    rightEyeOD: "OD – కుడి కన్ను",
    leftEyeOS: "OS – ఎడమ కన్ను",
    informedConsentLabel: "AI స్క్రీనింగ్ కోసం రోగి యొక్క సమ్మతి పొందబడింది.",
    informedConsentRequired: "స్క్రీనింగ్ ప్రారంభించడానికి రోగి సమ్మతి తప్పనిసరి.",
    uploadFundusScan: "రెటీనా ఫోటోను అప్‌లోడ్ చేయండి",
    dragDropHint: "45° ఫండస్ ఫోటోగ్రాఫ్ (PNG, JPEG - గరిష్టంగా 10MB) ఇక్కడ ఉంచండి",
    startScreening: "స్క్రీనింగ్ ప్రారంభించండి",
    screeningInProgress: "AI విశ్లేషణ మరియు నాణ్యత తనిఖీ జరుగుతోంది...",

    qualityTitle: "ఇమేజ్ నాణ్యత అంచనా (IQA)",
    gradable: "తగినంత నాణ్యత ఉంది (Gradable)",
    borderline: "మెరుగుపరచబడింది (Borderline)",
    ungradable: "నాణ్యత సరిపోదు (Ungradable)",
    sharpness: "స్పష్టత / ఫోకస్",
    illumination: "వెలుతురు / ఎక్స్‌పోజర్",
    fovCoverage: "రెటీనా ఫీల్డ్ ఆఫ్ వ్యూ",
    retakeRecommended: "మరలా ఫోటో తీయడం మంచిది",
    claheEnhanced: "అడాప్టివ్ కాంట్రాస్ట్ మెరుగుపరచబడింది",

    grade0: "గ్రేడ్ 0 – డయాబెటిక్ రెటినోపతి లేదు",
    grade1: "గ్రేడ్ 1 – మైల్డ్ నాన్-ప్రొలిఫెరేటివ్ DR",
    grade2: "గ్రేడ్ 2 – మోడరేట్ నాన్-ప్రొలిఫెరేటివ్ DR",
    grade3: "గ్రేడ్ 3 – తీవ్రమైన నాన్-ప్రొలిఫెరేటివ్ DR",
    grade4: "గ్రేడ్ 4 – ప్రొలిఫెరేటివ్ రెటినోపతి (PDR)",

    screeningResultsTitle: "AI స్క్రీనింగ్ ఫలితాలు",
    referableDR: "నిపుణుల పరిశీలన అవసరం (Referable)",
    nonReferableDR: "సాధారణ వార్షిక తనిఖీ (Non-Referable)",
    confidence: "విశ్వసనీయత స్కోర్",
    uncertaintyWarning: "అనిశ్చిత ఫలితం గుర్తించబడింది",
    specialistReviewAdvised: "మోడల్ విశ్వసనీయత తక్కువగా ఉన్నందున, కంటి వైద్య నిపుణుడి ప్రత్యక్ష పరిశీలన అవసరం.",
    recommendation: "వైద్య సలహా",
    maculaRiskIndicator: "మ్యాక్యులర్ ముప్పు సూచిక",
    maculaRiskDesc: "ఫోవియా ప్రాంతానికి సమీపంలో లీషన్లు గుర్తించబడినాయి. ఖచ్చితమైన DME నిర్ధారణకు OCT పరీక్ష అవసరం.",

    originalScan: "అసలు ఫోటో",
    gradcamHeatmap: "Grad-CAM దృష్టి పటం",
    gradcamNotice: "AI మోడల్ ఏ ప్రాంతాల ఆధారంగా నిర్ణయం తీసుకుందో చూపుతుంది.",
    lesionMap: "గుర్తించిన లీషన్లు",
    retinalPlacesMap: "రెటీనా శరీర నిర్మాణ పటం",
    vesselNetwork: "రక్తనాళాల నెట్‌వర్క్",
    compositeView: "సమగ్ర నివేదిక",

    specialistQueue: "వైద్యుల సమీక్ష జాబితా",
    patientHistory: "రోగి చరిత్ర & మునుపటి నివేదికలు",
    longitudinalTracking: "సమయక్రమ మార్పుల పరిశీలన",
    progressionComparison: "మునుపటి మరియు ప్రస్తుత పరీక్షల పోలిక",
    baselineVisit: "మొదటి పరీక్ష",
    currentVisit: "ప్రస్తుత పరీక్ష",
    stableFinding: "మార్పు లేకుండా స్థిరంగా ఉంది",
    longitudinalDisclaimer: "ఈ పోలిక కేవలం ప్రాథమిక పరిశీలన కోసం మాత్రమే. నిపుణుడైన నేత్ర వైద్యుని పరిశీలన తప్పనిసరి.",
    clinicalNotes: "స్పెషలిస్ట్ క్లినికల్ నోట్స్",
    confirmGrade: "ధృవీకరించండి",
    overrideGrade: "గ్రేడ్ మార్చండి",
    requestRecapture: "మరలా ఫోటో అభ్యర్థించండి",
    auditTrail: "ఆడిట్ రికార్డులు",

    clinicalDisclaimer: "నేత్ర అనేది AI ఆధారిత స్క్రీనింగ్ మరియు నిర్ణయ మద్దతు వ్యవస్థ. ఇది అర్హత కలిగిన నేత్ర వైద్యుడి స్థానాన్ని భర్తీ చేయదు.",
  },

  hi: {
    appName: "नेत्रा (Netra)",
    tagline: "डायबिटिक रेटिनोपैथी स्क्रीनिंग एवं व्याख्यात्मक AI प्लेटफॉर्म",
    navHome: "होम",
    navScreening: "नई स्क्रीनिंग",
    navDashboard: "विशेषज्ञ डैशबोर्ड",
    navDoctor: "डॉक्टर पोर्टल",
    navDocs: "दस्तावेज़",
    navLanguage: "भाषा",

    online: "ऑनलाइन",
    lowConnectivity: "धीमा नेटवर्क",
    offline: "ऑफ़लाइन मोड",
    retryUpload: "पुनः अपलोड करें",
    offlineBanner: "आप वर्तमान में ऑफ़लाइन हैं। इंटरनेट जुड़ते ही आप दोबारा अपलोड कर सकते हैं।",

    patientDetailsTitle: "मरीज़ का विवरण एवं पंजीकरण",
    patientId: "मरीज़ आईडी (Patient ID)",
    patientName: "मरीज़ का पूरा नाम",
    age: "आयु (वर्ष)",
    gender: "लिंग",
    male: "पुरुष",
    female: "महिला",
    other: "अन्य",
    diabetesType: "मधुमेह का प्रकार",
    type1: "टाइप 1 मधुमेह",
    type2: "टाइप 2 मधुमेह",
    gestational: "गर्भकालीन मधुमेह",
    none: "कोई नहीं / पूर्व-मधुमेह",
    diabetesDuration: "मधुमेह की अवधि (वर्ष)",
    years: "वर्ष",
    eyeExamined: "जांची गई आँख",
    rightEyeOD: "OD – दाईं आँख",
    leftEyeOS: "OS – बाईं आँख",
    informedConsentLabel: "AI स्क्रीनिंग हेतु मरीज़ की सहमति प्राप्त की गई है।",
    informedConsentRequired: "स्क्रीनिंग से पूर्व मरीज़ की सहमति अनिवार्य है।",
    uploadFundusScan: "रेटिना की तस्वीर अपलोड करें",
    dragDropHint: "45° फंडस तस्वीर (PNG, JPEG - अधिकतम 10MB) यहाँ खींचें या चुनें",
    startScreening: "स्क्रीनिंग विश्लेषण करें",
    screeningInProgress: "AI विश्लेषण एवं गुणवत्ता जांच जारी है...",

    qualityTitle: "छवि गुणवत्ता मूल्यांकन (IQA)",
    gradable: "उपयुक्त गुणवत्ता (Gradable)",
    borderline: "सुधार किया गया (Borderline)",
    ungradable: "अनुपयुक्त गुणवत्ता (Ungradable)",
    sharpness: "स्पष्टता / फ़ोकस",
    illumination: "रोशनी / एक्सपोज़र",
    fovCoverage: "रेटिना दृश्य क्षेत्र (FOV)",
    retakeRecommended: "पुनः फोटो खींचने की सलाह",
    claheEnhanced: "अनुकूली कंट्रास्ट संवर्धन लागू",

    grade0: "ग्रेड 0 – कोई डायबिटिक रेटिनोपैथी नहीं",
    grade1: "ग्रेड 1 – प्रारंभिक गैर-प्रोलिफेरेटिव DR",
    grade2: "ग्रेड 2 – मध्यम गैर-प्रोलिफेरेटिव DR",
    grade3: "ग्रेड 3 – गंभीर गैर-प्रोलिफेरेटिव DR",
    grade4: "ग्रेड 4 – प्रोलिफेरेटिव डायबिटिक रेटिनोपैथी",

    screeningResultsTitle: "AI रेटिना स्क्रीनिंग रिपोर्ट",
    referableDR: "नेत्र विशेषज्ञ का परामर्श आवश्यक (Referable)",
    nonReferableDR: "गैर-संदर्भित (वार्षिक सामान्य जांच)",
    confidence: "कैलिब्रेटेड आत्मविश्वास",
    uncertaintyWarning: "अनिश्चित परिणाम संज्ञान",
    specialistReviewAdvised: "मॉडल की अनिश्चितता अधिक है। केवल स्वचालित ग्रेड पर निर्भर न रहकर योग्य नेत्र रोग विशेषज्ञ से जांच कराएं।",
    recommendation: "चिकित्सीय अनुशंसा",
    maculaRiskIndicator: "मैकुलर जोखिम संकेतक",
    maculaRiskDesc: "फोविया के निकट घाव पाए जाने पर संकेतक। DME के निश्चित निदान के लिए OCT परीक्षण अनिवार्य है।",

    originalScan: "मूल तस्वीर",
    gradcamHeatmap: "Grad-CAM ध्यान क्षेत्र",
    gradcamNotice: "यह दर्शाता है कि AI मॉडल ने किन क्षेत्रों पर ध्यान देकर निर्णय लिया।",
    lesionMap: "पहचाने गए घाव (Lesions)",
    retinalPlacesMap: "रेटिना शारीरिक रचना मानचित्र",
    vesselNetwork: "रक्त वाहिका नेटवर्क",
    compositeView: "समग्र चिकित्सीय दृश्य",

    specialistQueue: "विशेषज्ञ समीक्षा कतार",
    patientHistory: "मरीज़ का इतिहास एवं पूर्व रिपोर्ट",
    longitudinalTracking: "दीर्घकालिक रेटिना ट्रैकिंग",
    progressionComparison: "पूर्व एवं वर्तमान जांच तुलना",
    baselineVisit: "प्रारंभिक जांच",
    currentVisit: "वर्तमान जांच",
    stableFinding: "जांच अंतराल में स्थिति स्थिर पाई गई",
    longitudinalDisclaimer: "यह तुलना केवल अवलोकन हेतु है। यह विशेषज्ञ द्वारा बायोमाइक्रोस्कोपी का विकल्प नहीं है।",
    clinicalNotes: "विशेषज्ञ क्लिनिकल नोट्स",
    confirmGrade: "ग्रेड की पुष्टि करें",
    overrideGrade: "ग्रेड बदलें",
    requestRecapture: "पुनः फोटो का अनुरोध करें",
    auditTrail: "क्लिनिकल ऑडिट ट्रेल",

    clinicalDisclaimer: "नेत्रा एक AI-सहायक रेटिना स्क्रीनिंग एवं नैदानिक निर्णय-सहायक मंच है। यह योग्य नेत्र रोग विशेषज्ञ का स्थान नहीं लेता है।",
  },
};
