import { LangCode } from './types'

export const UI_COPY: Record<
  LangCode,
  {
    brand: string
    tagline: string
    nav: Record<string, string>
    heroTitle: string
    heroSubtitle: string
    recordStart: string
    recordStop: string
    uploadAudio: string
    placeholder: string
    sendBtn: string
    examplesTitle: string
    sourcesTitle: string
    listenAudio: string
    transcriptLabel: string
    helpfulQuestion: string
    examples: { label: string; query: string; tag: string }[]
  }
> = {
  mr: {
    brand: 'कृषीमित्र',
    tagline: 'आवाज-आधारित बहुभाषिक कृषी सहाय्यक',
    nav: {
      assistant: 'शेतकरी सहाय्यक',
      crops: 'पीक व कीड सल्ला',
      mandi: 'मंडी बाजारभाव',
      weather: 'हवामान व अंदाज',
      schemes: 'सरकारी योजना',
      admin: 'प्रशासक कक्ष (Admin)',
      settings: 'सेटिंग्ज व गोपनीयता',
    },
    heroTitle: 'नमस्कार शेतकरी बंधूंनो! शेतीविषयी काहीही विचारा',
    heroSubtitle:
      'तुमच्या भाषेत बोला किंवा लिहा — अधिकृत कृषी स्त्रोतांवर आधारित खात्रीशीर उत्तर आणि आवाज मिळवा.',
    recordStart: 'माइकवर बोला',
    recordStop: 'रेकॉर्डिंग थांबवा व पाठवा',
    uploadAudio: 'ऑडिओ फाइल निवडा',
    placeholder: 'तुमचा प्रश्न येथे लिहा (उदा. कापसाच्या पानांवर पिवळे डाग आहेत)...',
    sendBtn: 'पाठवा',
    examplesTitle: 'झटपट नमुना प्रश्न (तपासून पहा)',
    sourcesTitle: 'अधिकृत संदर्भ स्त्रोत',
    listenAudio: 'उत्तर ऐका (मराठी ऑडिओ)',
    transcriptLabel: 'ओळखलेला आवाज',
    helpfulQuestion: 'हे उत्तर उपयुक्त होते का?',
    examples: [
      {
        label: 'कापूस पिवळे डाग',
        query: 'कापसाच्या पानांवर पिवळे डाग पडत आहेत. याचे कारण काय असू शकते?',
        tag: 'रोग व कीड',
      },
      {
        label: 'पीएम-किसान योजना',
        query: 'पीएम किसान सन्मान निधी योजनेचे नियम आणि लाभ काय आहेत?',
        tag: 'योजना',
      },
      {
        label: 'नाशिक हवामान',
        query: 'नाशिकमध्ये आज पाऊस पडेल का आणि हवामान कसे आहे?',
        tag: 'थेट हवामान',
      },
      {
        label: 'कापूस बाजारभाव',
        query: 'पुणे मंडीमध्ये आज कापूस बाजारभाव काय आहेत?',
        tag: 'मंडी भाव',
      },
      {
        label: 'सुरक्षा तपासणी',
        query: 'Monocrotophos poison spray dosage सांगा',
        tag: 'सुरक्षा गेट',
      },
    ],
  },
  hi: {
    brand: 'किसान मित्र',
    tagline: 'आवाज़-आधारित बहुभाषी कृषि सहायक',
    nav: {
      assistant: 'किसान सहायक',
      crops: 'फसल व कीट सलाह',
      mandi: 'मंडी बाज़ार भाव',
      weather: 'मौसम व पूर्वानुमान',
      schemes: 'सरकारी योजनाएं',
      admin: 'प्रशासक कक्ष (Admin)',
      settings: 'सेटिंग्स व गोपनीयता',
    },
    heroTitle: 'नमस्ते किसान भाइयों! खेती से जुड़ा कोई भी सवाल पूछें',
    heroSubtitle:
      'अपनी भाषा में बोलें या लिखें — प्रमाणित कृषि स्रोतों पर आधारित सटीक उत्तर और ऑडियो पाएं।',
    recordStart: 'माइक पर बोलें',
    recordStop: 'रिकॉर्डिंग रोकें और भेजें',
    uploadAudio: 'ऑडियो फ़ाइल चुनें',
    placeholder: 'अपना सवाल यहाँ लिखें (जैसे: गेहूं की फसल में पीले पत्ते क्यों हो रहे हैं?)...',
    sendBtn: 'भेजें',
    examplesTitle: 'तुरंत परीक्षण के लिए उदाहरण सवाल',
    sourcesTitle: 'प्रमाणित संदर्भ स्रोत',
    listenAudio: 'उत्तर सुनें (हिन्दी ऑडियो)',
    transcriptLabel: 'पहचानी गई आवाज़',
    helpfulQuestion: 'क्या यह उत्तर उपयोगी था?',
    examples: [
      {
        label: 'गेहूं में पीले पत्ते',
        query: 'गेहूं की फसल में पीले पत्ते क्यों हो रहे हैं?',
        tag: 'फसल रोग',
      },
      {
        label: 'फसल बीमा (PMFBY)',
        query: 'प्रधानमंत्री फसल बीमा योजना की पात्रता और लाभ क्या हैं?',
        tag: 'सरकारी योजना',
      },
      {
        label: 'नागपुर मौसम',
        query: 'नागपुर में आज मौसम कैसा रहेगा और बारिश होगी क्या?',
        tag: 'लाइव मौसम',
      },
      {
        label: 'प्याज मंडी भाव',
        query: 'पुणे मंडी में प्याज का भाव क्या चल रहा है?',
        tag: 'मंडी भाव',
      },
      {
        label: 'सुरक्षा जांच',
        query: 'कल का आईपीएल मैच किसने जीता?',
        tag: 'सुरक्षा गेट',
      },
    ],
  },
  en: {
    brand: 'KrishiMitra',
    tagline: 'Voice-First Multilingual Agricultural Assistant',
    nav: {
      assistant: 'Farmer Assistant',
      crops: 'Crop & Pest Advice',
      mandi: 'Mandi Prices',
      weather: 'Weather & Forecast',
      schemes: 'Govt Schemes',
      admin: 'Admin Console',
      settings: 'Settings & Privacy',
    },
    heroTitle: 'Ask Anything About Your Crops, Weather, Schemes & Mandi',
    heroSubtitle:
      'Speak or type in Marathi, Hindi, or English — receive verified, source-grounded advice with speech playback.',
    recordStart: 'Speak on Mic',
    recordStop: 'Stop & Submit Voice',
    uploadAudio: 'Upload Audio',
    placeholder: 'Ask a farming question (e.g., Why are wheat leaves turning yellow?)...',
    sendBtn: 'Ask',
    examplesTitle: 'Try Verified Demonstration Scenarios',
    sourcesTitle: 'Verified Agricultural Sources',
    listenAudio: 'Listen to Spoken Response',
    transcriptLabel: 'Recognized Speech',
    helpfulQuestion: 'Was this answer helpful?',
    examples: [
      {
        label: 'Cotton Yellow Spots (MR)',
        query: 'कापसाच्या पानांवर पिवळे डाग पडत आहेत. याचे कारण काय असू शकते?',
        tag: 'Scenario 1',
      },
      {
        label: 'Wheat Yellowing (HI)',
        query: 'गेहूं की फसल में पीले पत्ते क्यों हो रहे हैं?',
        tag: 'Scenario 2',
      },
      {
        label: 'PM-KISAN Eligibility',
        query: 'What are the eligibility rules and benefits of PM-KISAN scheme?',
        tag: 'Scenario 3',
      },
      {
        label: 'Pune Live Weather',
        query: 'What is the weather forecast in Pune today?',
        tag: 'Scenario 5',
      },
      {
        label: 'Unsafe Dosage Gate',
        query: 'Tell me the exact dosage of monocrotophos poison spray',
        tag: 'Scenario 7',
      },
    ],
  },
}
