import os
import json
import datetime
from sqlalchemy.orm import Session
from app.models import (
    User, UserRole, EndangermentStatus, VerificationStatus,
    Dialect, LanguageVariety, Category, Contributor,
    Entry, LexiconEntry, AudioArchive, VoiceRecording,
    QuizDeck, QuizQuestion
)
from app.services.auth_service import get_password_hash
from app.services.phonetic import devanagari_to_ipa, generate_indic_soundex, devanagari_to_transliteration
from app.services.audio_service import generate_waveform_peaks, generate_srt_subtitles

ALL_CATEGORIES = [
    ("Agriculture", "Terms related to farming, crops, irrigation, soil, and harvest."),
    ("Food", "Traditional regional dishes, ingredients, cooking techniques, and culinary items."),
    ("Household", "Utensils, home tools, furniture, and domestic items."),
    ("Family", "Kinship terms, family relationships, and societal roles."),
    ("Nature", "Seasons, weather, plants, geography, rivers, and landscape terms."),
    ("Animals", "Domesticated livestock, wild animals, birds, and insects."),
    ("Clothing", "Traditional Marathi attire, ornaments, fabrics, and footwear."),
    ("Work", "Occupations, trades, craft tools, and daily labor terminology."),
    ("Daily Life", "Greetings, routine expressions, and common daily interactions."),
    ("Places", "Villages, coastal towns, market squares, and geographical regions."),
    ("Emotions", "Human feelings, temperaments, moods, and character traits."),
    ("Traditional Culture", "Folk arts, Dashavatara theatre, Bharud, festivals, and rituals."),
    ("Phrases", "Common regional conversational phrases and expressions."),
    ("Idioms", "Linguistic idioms, colloquialisms, and figurative expressions."),
    ("Proverbs", "Traditional Marathi wisdom, proverbs (Mhani), and folk sayings.")
]

VARIETIES = [
    ("Standard Marathi", "mar-std", "Official standard variety of Marathi used across Maharashtra.", "Maharashtra State", "Statewide", 18.5204, 73.8567, EndangermentStatus.SAFE, 83000000, "Official administrative and literary medium across Maharashtra."),
    ("Malvani", "mar-mal", "Coastal Marathi variety spoken in Sindhudurg and South Konkan.", "Konkan Coast", "Sindhudurg, Ratnagiri, Goa Border", 16.0500, 73.4667, EndangermentStatus.VULNERABLE, 1800000, "Preserves Dashavatara folk theatre scripts, maritime folk songs, and fishing vocabulary."),
    ("Varhadi", "mar-var", "Soft, expressive regional variety spoken across the Vidarbha region.", "Vidarbha", "Amravati, Akola, Buldhana, Yavatmal, Washim, Wardha", 20.9333, 77.7500, EndangermentStatus.VULNERABLE, 12000000, "Home to Marathi saint literature, Bharud folk songs, and agrarian traditions."),
    ("Ahirani", "mar-ahi", "Khandesh regional variety blending ancient Marathi with Bhili phonetics.", "Khandesh", "Dhule, Jalgaon, Nandurbar, Nashik", 20.9000, 74.7833, EndangermentStatus.DEFINITELY_ENDANGERED, 3000000, "Renowned for Kanbai festival songs, oral storytelling, and Tapi valley expressions."),
    ("Agri", "mar-agr", "Coastal North Konkan regional variety spoken in Thane and Raigad.", "North Konkan", "Thane, Raigad, Navi Mumbai", 19.2183, 72.9781, EndangermentStatus.VULNERABLE, 1500000, "Spoken by indigenous coastal communities preserving salt-pan and maritime terms."),
    ("Koli", "mar-kol", "Maritime fishing community variety preserved across coastal ports.", "Coastal Belt", "Mumbai Coast, Palghar, Raigad", 18.9690, 72.8258, EndangermentStatus.VULNERABLE, 800000, "Vibrant fishing terminology, seafaring lore, and coastal deity songs."),
    ("Marathwadi", "mar-mwd", "Regional variety of central Maharashtra / Marathwada region.", "Marathwada", "Chhatrapati Sambhajinagar, Nanded, Latur, Beed, Jalna", 19.8762, 75.3433, EndangermentStatus.VULNERABLE, 7500000, "Rich historical vocabulary, Sufi-Bhakti confluence, and traditional folk dialect.")
]

TEAM_CONTRIBUTORS = [
    ("Aaditya Jadhav", "Mumbai", "Mumbai Suburban", "Project Lead & Dialect Preserver", "Student preserver documenting Marathi regional dialects.", "assets/aaditya_jadhav.jpg"),
    ("Padmaj Jadhav", "Mumbai", "Mumbai City", "Linguistics Researcher", "Student researcher compiling Marathi folklore and vocabulary archive.", "assets/padmaj_jadhav.jpg"),
    ("Parth Kadam", "Mumbai", "Thane", "Technical Developer", "Student developer building BhashaLok digital repository APIs.", "assets/parth_kadam.jpg"),
    ("Dr. Rajesh Patil", "Pune", "Pune", "Senior Dialectologist", "Professor of Indic Linguistics and Marathi oral heritage auditor.", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=200&auto=format&fit=crop"),
    ("Sushila Tai", "Malvan", "Sindhudurg", "Native Speaker & Oral Folk Artist", "Coastal Konkan native storyteller and Dashavatara preserver.", "https://images.unsplash.com/photo-1544717305-2782549b5136?q=80&w=200&auto=format&fit=crop"),
    ("Ganpat Kaka", "Warud", "Amravati", "Farmer & Vidarbha Oral Historian", "Elder native speaker documenting traditional Vidarbha agricultural lore.", "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=200&auto=format&fit=crop")
]

DEMO_ENTRIES_DATA = {
    "Agriculture": [
        ("पेरणी", "Perani", "Sowing of seeds in prepared soil", "Standard Marathi", "Prakriti", "Ahmednagar", "Akole", "पाऊस पडताच शेतकरी पेरणीला लागतात.", "/peːrəɳi/"),
        ("कापणी", "Kapani", "Harvesting of mature crops", "Varhadi", "Vidarbha", "Amravati", "Warud", "शेतात सोयाबीनची कापणी सुरु झाली आहे.", "/kaːpəɳi/"),
        ("नांगरणी", "Nangarani", "Ploughing the farm soil", "Ahirani", "Khandesh", "Dhule", "Shirpur", "वावरात बैलांनी नांगरणी सुरु केली.", "/naːŋɡərəɳi/"),
        ("शेततळे", "Shettale", "Farm pond for rainwater harvesting", "Marathwadi", "Marathwada", "Beed", "Ambajogai", "शेततळ्यात मुबलक पाणी साचले आहे.", "/šeːt̪ət̪əḷeː/"),
        ("रास", "Raas", "Threshed heap of grain", "Malvani", "Konkan", "Sindhudurg", "Malvan", "खळ्यात धान्याची मोठी रास लावली आहे.", "/raːs/"),
        ("मळणी", "Malani", "Threshing of harvested grain", "Standard Marathi", "Desh", "Pune", "Junnar", "सोयाबीनची मळणी यंत्राने केली जाते.", "/məɭəɳi/"),
        ("अवजार", "Avjaar", "Farming tools and implements", "Agri", "North Konkan", "Thane", "Murbad", "शेतीची सर्व अवजारे लाकडी असतात.", "/əʋət͡saːr/"),
        ("खत", "Khat", "Organic or chemical fertilizer", "Standard Marathi", "Desh", "Satara", "Khatav", "शेणखतामुळे जमिनीची सुपीकता वाढते.", "/kʰət̪/"),
        ("ओलिताखाली", "Olitakhali", "Irrigated agricultural land", "Varhadi", "Vidarbha", "Akola", "Akola", "हे शेत विहिरीच्या ओलिताखाली आहे.", "/oːlit̪aːkʰaːli/"),
        ("वावर", "Vaavar", "Agricultural field or farm land", "Ahirani", "Khandesh", "Jalgaon", "Chopda", "आज दुपारी वावरात काम करायचे आहे.", "/ʋaːʋər/")
    ],
    "Food": [
        ("आंबा", "Amba", "Sweet Alphonso Mango", "Malvani", "Konkan", "Ratnagiri", "Ratnagiri", "देवगडचा हापूस आंबा खूप गोड असतो.", "/aːmbaː/"),
        ("भात", "Bhaat", "Steamed cooked rice", "Standard Marathi", "Statewide", "Mumbai", "City", "गरम भात आणि आमटी मस्त लागते.", "/bʰaːt̪/"),
        ("पिठले", "Pithale", "Gram flour curry (Zunka/Pithale)", "Varhadi", "Vidarbha", "Nagpur", "Ramtek", "गरमागरम पिठले भाकरी आणि कांदा एकत्र खातात.", "/piʈʰleː/"),
        ("पोळी", "Poli", "Traditional unleavened flatbread", "Standard Marathi", "Desh", "Pune", "Haveli", "गव्हाची मऊ पोळी आरोग्यासाठी उत्तम असते.", "/poːɭi/"),
        ("सोलकढी", "Solkadhi", "Kokum coconut milk digestive drink", "Malvani", "Konkan", "Sindhudurg", "Kudal", "जेवणानंतर थंड सोलकढी पिण्याची प्रथा आहे.", "/soːləkəɖʰi/"),
        ("भाकरी", "Bhakari", "Jowar or Bajra flatbread", "Marathwadi", "Marathwada", "Latur", "Udgir", "गरम ज्वारीची भाकरी आणि ठेचा उत्तम आहार आहे.", "/bʰaːkəri/"),
        ("ठेचा", "Thecha", "Spiced green chili & garlic chutney", "Standard Marathi", "Desh", "Kolhapur", "Karvir", "कोल्हापुरी मिरचीचा ठेचा खूप तिखट असतो.", "/ʈʰeːt͡saː/"),
        ("उकडीचे मोदक", "Ukadiche Modak", "Steamed rice flour sweet dumplings", "Standard Marathi", "Konkan", "Raigad", "Alibag", "गणपती बाप्पाला उकडीचे मोदक आवडतात.", "/ukəɖičeː moːd̪ək/"),
        ("कढी", "Kadhi", "Spiced buttermilk curry", "Ahirani", "Khandesh", "Nandurbar", "Shahada", "ताकाची कढी पचनासाठी गुणकारी असते.", "/kəɖʰi/"),
        ("खांडवी", "Khandvi", "Savory rolled gram flour snack", "Standard Marathi", "Statewide", "Nashik", "Malegaon", "खांडवीवर कोथिंबीर आणि खोबरे पेरतात.", "/kʰaːɳɖəʋi/")
    ],
    "Household": [
        ("तवा", "Tava", "Iron griddle for baking bread", "Standard Marathi", "Statewide", "Pune", "Haveli", "लोखंडी तव्यावर भाकरी चांगली भाजते.", "/t̪əʋaː/"),
        ("हंडी", "Handi", "Deep brass cooking pot", "Varhadi", "Vidarbha", "Wardha", "Seloo", "तांब्याच्या हंडीत पाणी ठेवले जाते.", "/həɳɖi/"),
        ("कढई", "Kadhai", "Wok for frying and curries", "Standard Marathi", "Statewide", "Satara", "Wai", "कढईमध्ये भजी तळून घेतली.", "/kəɖʰəi/"),
        ("पुलपात्र", "Phulpatra", "Small brass water tumbler", "Standard Marathi", "Statewide", "Kolhapur", "Kagal", "तांब्याच्या फुलपात्रातून पाणी प्यावे.", "/pʰuləpaːt̪rə/"),
        ("झाडू", "Jhadu", "Broom for cleaning floors", "Standard Marathi", "Statewide", "Jalgaon", "Yawal", "सकाळी उठून घराचा झाडू मारला.", "/d͡ʒʰaːɖu/"),
        ("उखळ", "Ukhal", "Wooden mortar for pounding grain", "Malvani", "Konkan", "Sindhudurg", "Sawantwadi", "पूर्वी उखळात भात कांडला जायचा.", "/ukʰəɭ/"),
        ("मुसळ", "Musal", "Heavy pestle used with mortar", "Standard Marathi", "Desh", "Sangli", "Shirala", "लाकडी मुसळाने धान्य कुटले जाते.", "/musəɭ/"),
        ("समई", "Samai", "Traditional tall brass oil lamp", "Standard Marathi", "Statewide", "Solapur", "Barshi", "देवापुढे पितळी समई प्रज्वलित केली.", "/səməi/"),
        ("ताट", "Taat", "Large metal dining plate", "Standard Marathi", "Statewide", "Nashik", "Trimbak", "जेवणाचे ताट सुशोभित केले आहे.", "/t̪aːʈ/"),
        ("पेला", "Pela", "Drinking glass or cup", "Standard Marathi", "Statewide", "Osmanabad", "Omerga", "दुधाचा एक पेला पिऊन झोपले पाहिजे.", "/peːlaː/")
    ],
    "Family": [
        ("आजी", "Aaji", "Paternal or maternal grandmother", "Standard Marathi", "Statewide", "Pune", "Haveli", "आजी रात्री सुरस गोष्टी सांगते.", "/aːd͡ʒi/"),
        ("आजोबा", "Ajoba", "Paternal or maternal grandfather", "Standard Marathi", "Statewide", "Satara", "Patan", "आजोबा रोज सकाळी बागेत फिरतात.", "/aːd͡ʒoːbaː/"),
        ("भाऊ", "Bhau", "Brother or close male cousin", "Standard Marathi", "Statewide", "Solapur", "Sangole", "माझा मोठा भाऊ शहरात शिकतो.", "/bʱaːu/"),
        ("बहीण", "Bahin", "Sister or female cousin", "Standard Marathi", "Statewide", "Nagpur", "Umred", "बहिणीने भावाच्या हातावर राखी बांधली.", "/bəhiːɳ/"),
        ("मामा", "Mama", "Maternal uncle (Mother's brother)", "Standard Marathi", "Statewide", "Latur", "Nilanga", "उन्हाळ्याच्या सुट्टीत मामाच्या गावाला गेलो.", "/maːmaː/"),
        ("मावशी", "Mavashi", "Maternal aunt (Mother's sister)", "Standard Marathi", "Statewide", "Beed", "Georai", "मावशीने सुट्टीत चविष्ट मिठाई पाठवली.", "/maːʋəši/"),
        ("काका", "Kaka", "Paternal uncle (Father's brother)", "Standard Marathi", "Statewide", "Dhule", "Sakri", "काका शेतीच्या कामात मदत करतात.", "/kaːkaː/"),
        ("काकू", "Kaku", "Paternal aunt (Father's brother's wife)", "Standard Marathi", "Statewide", "Jalna", "Partur", "काकूने छान पुरणपोळी बनवली.", "/kaːku/"),
        ("नातू", "Natu", "Grandson", "Standard Marathi", "Statewide", "Parbhani", "Palam", "आजोबा नातवाला पाठीवर खेळवतात.", "/naːt̪u/"),
        ("नातवंड", "Natvand", "Grandchildren", "Standard Marathi", "Statewide", "Amravati", "Daryapur", "घर नातवंडांच्या हसण्याने फुलून जाते.", "/naːt̪əʋəɳɖ/")
    ],
    "Nature": [
        ("पाऊस", "Paaus", "Rainfall or monsoon shower", "Standard Marathi", "Statewide", "Ratnagiri", "Dapoli", "कोकणात मुसळधार पाऊस पडतो.", "/paːus/"),
        ("वारा", "Vaara", "Breeze or wind", "Standard Marathi", "Statewide", "Sindhudurg", "Vengurla", "समुद्रावरून थंड वारा वाहत आहे.", "/ʋaːraː/"),
        ("डोंगर", "Dongar", "Hill or mountain peak", "Standard Marathi", "Western Ghats", "Pune", "Bhor", "डोंगरावर हिरवेगार गवत उगवले आहे.", "/ɖoːŋɡər/"),
        ("नदी", "Nadi", "River or flowing stream", "Standard Marathi", "Statewide", "Nashik", "Niphad", "गोदावरी नदी महाराष्ट्राची जीवनदायिनी आहे.", "/nəd̪i/"),
        ("समुद्र", "Samudra", "Ocean or coastal sea", "Malvani", "Konkan", "Raigad", "Shrivardhan", "अरबी समुद्र कोकण किनारपट्टीला भिडतो.", "/səmud̪rə/"),
        ("जंगल", "Jangal", "Forest or woodland density", "Varhadi", "Vidarbha", "Gadchiroli", "Aheri", "ताडोबाच्या जंगलात वाघ पाहायला मिळतात.", "/d͡ʒəŋɡəl/"),
        ("आकाश", "Aakash", "Sky or firmament", "Standard Marathi", "Statewide", "Aurangabad", "Paithan", "रात्रीच्या वेळी आकाशात चांदण्या चमकतात.", "/aːkaːš/"),
        ("चांदणे", "Chandane", "Moonlight night brightness", "Standard Marathi", "Statewide", "Solapur", "Akkalkot", "पौर्णिमेचे चांदणे खूप सुंदर दिसते.", "/t͡saːnd̪əɳeː/"),
        ("उन्हाळा", "Unhala", "Summer season heat", "Standard Marathi", "Statewide", "Nanded", "Mukhed", "उन्हाळ्यात विहिरींचे पाणी आटते.", "/unhaːɭaː/"),
        ("पावसाळा", "Pavasala", "Monsoon rainy season", "Standard Marathi", "Statewide", "Thane", "Shahapur", "पावसाळ्यात निसर्ग हिरवागार होतो.", "/paːʋəsaːɭaː/")
    ],
    "Animals": [
        ("गाय", "Gaay", "Domesticated Cow", "Standard Marathi", "Statewide", "Kolhapur", "Radhanagari", "गाय आपल्याला गोड दूध देते.", "/ɡaːj/"),
        ("बैल", "Bail", "Bullock or farm draft ox", "Standard Marathi", "Statewide", "Ahmednagar", "Rahuri", "पोळ्याच्या सणाला बैलांची पूजा केली जाते.", "/bəil/"),
        ("म्हैस", "Mhais", "Water Buffalo", "Standard Marathi", "Statewide", "Sangli", "Miraj", "म्हशीचे दूध घट्ट आणि पौष्टिक असते.", "/mhəis/"),
        ("शेळी", "Sheli", "Domestic Goat", "Standard Marathi", "Statewide", "Beed", "Kaij", "डोंगरावर शेळ्या चरायला गेल्या आहेत.", "/šeːɭi/"),
        ("कुत्रा", "Kutra", "Domestic Dog", "Standard Marathi", "Statewide", "Pune", "Haveli", "कुत्रा हा घराचा इमानी रखवालदार आहे.", "/kut̪raː/"),
        ("मांजरी", "Manjari", "Cat", "Standard Marathi", "Statewide", "Nashik", "Sinnar", "मांजरीने दुधाचे पातेले सांडले.", "/maːnd͡ʒəri/"),
        ("घोडा", "Ghoda", "Horse", "Standard Marathi", "Statewide", "Satara", "Wai", "शर्यतीत घोडा वेगाने पळाला.", "/ɡʰoːɖaː/"),
        ("वाघ", "Vaagh", "Royal Bengal Tiger", "Standard Marathi", "Vidarbha", "Chandrapur", "Brahmapuri", "वाघ हा भारताचा राष्ट्रीय प्राणी आहे.", "/ʋaːɡʰ/"),
        ("हत्ती", "Hatti", "Elephant", "Standard Marathi", "Statewide", "Kolhapur", "Chandgad", "मंदिराच्या मिरवणुकीत हत्ती पुढे होता.", "/hət̪t̪i/"),
        ("पोपट", "Popat", "Parrot bird", "Standard Marathi", "Statewide", "Nagpur", "Kalmeshwar", "पिंजऱ्यातील पोपट गोड बोलतो.", "/poːpəʈ/")
    ],
    "Clothing": [
        ("धोतर", "Dhotar", "Traditional men's wrapped lower garment", "Standard Marathi", "Desh", "Pune", "Haveli", "समारंभात आजोबा धवल धोतर नेसतात.", "/d̪ʰoːt̪ər/"),
        ("नऊवारी साडी", "Nauvari Sadi", "Traditional nine-yard Maharashtrian sari", "Standard Marathi", "Statewide", "Kolhapur", "Karvir", "सणासुदीला स्त्रिया नऊवारी साडी परिधान करतात.", "/nəuʋaːri saːɖi/"),
        ("फेटा", "Pheta", "Traditional ceremonial turban", "Varhadi", "Vidarbha", "Amravati", "Achalpur", "वारकरी आणि पाहुण्यांचे फेटा बांधून स्वागत केले जाते.", "/pʰeːʈaː/"),
        ("चोळी", "Choli", "Traditional fitted bodice or blouse", "Standard Marathi", "Statewide", "Satara", "Wai", "खणाची चोळी खूप लोकप्रिय आहे.", "/t͡soːɭi/"),
        ("कोल्हापुरी चप्पल", "Kolhapuri Chappal", "Handcrafted leather sandals", "Standard Marathi", "Desh", "Kolhapur", "Kagal", "कोल्हापुरी चप्पल जगप्रसिद्ध आहे.", "/koːlhaːpuri t͡ʃəppəl/"),
        ("पैठणी", "Paithani", "Handwoven pure silk gold zari sari", "Standard Marathi", "Marathwada", "Aurangabad", "Paithan", "पैठणी साडी महाराष्ट्राचे वैभव मानली जाते.", "/pəit̪ʰəɳi/"),
        ("कुर्ता", "Kurta", "Loose collarless cotton shirt", "Standard Marathi", "Statewide", "Nashik", "Sinnar", "सणाच्या दिवशी खादीचा कुर्ता घालतात.", "/kurt̪aː/"),
        ("शेला", "Shela", "Ceremonial silk shoulder sash", "Standard Marathi", "Statewide", "Pune", "Baramati", "वर-वधूच्या खांद्यावर भरजरी शेला टाकला जातो.", "/šeːlaː/"),
        ("तोडा", "Toda", "Heavy silver anklet worn by rural women", "Ahirani", "Khandesh", "Dhule", "Sakri", "खान्देशात स्त्रिया पायात चांदीचा तोडा घालतात.", "/t̪oːɖaː/"),
        ("नथ", "Nath", "Traditional pearl crescent nose ornament", "Standard Marathi", "Statewide", "Mumbai", "Dadar", "पारंपरिक वेषात नथ चेहऱ्याचे सौंदर्य वाढवते.", "/nət̪ʰ/")
    ],
    "Work": [
        ("सुतार", "Sutar", "Carpenter crafting wooden implements", "Standard Marathi", "Statewide", "Pune", "Shirur", "सुताराने शेतीचा नवीन नांगर तयार केला.", "/sut̪aːr/"),
        ("लोहार", "Lohar", "Blacksmith forging sickles and iron tools", "Varhadi", "Vidarbha", "Buldhana", "Khamgaon", "लोहाराच्या भात्यातून ठिणग्या उडत होत्या.", "/loːhaːr/"),
        ("कुंभार", "Kumbhar", "Potter shaping earthen vessels and diyas", "Standard Marathi", "Statewide", "Nashik", "Niphad", "दिवाळीसाठी कुंभार मातीचे दिवे बनवतो.", "/kumbʱaːr/"),
        ("विणकर", "Vinkar", "Traditional handloom textile weaver", "Marathwadi", "Marathwada", "Nanded", "Mukhed", "विणकर हातमागावर सुंदर साडी विणतो.", "/ʋiɳəkər/"),
        ("चांभार", "Chambhar", "Leather artisan crafting durable goods", "Standard Marathi", "Statewide", "Kolhapur", "Karvir", "चांभाराने चामड्याचे पादत्राण शिवले.", "/t͡saːmbʱaːr/"),
        ("माळी", "Mali", "Gardener and horticulturist cultivating blooms", "Standard Marathi", "Statewide", "Satara", "Mahabaleshwar", "माळ्याने बागेत गुलाबाची सुंदर रोपे लावली.", "/maːɭi/"),
        ("कोळी", "Koli", "Fisherman navigating coastal waters", "Koli", "Coastal Belt", "Raigad", "Alibag", "पहाटे कोळी बांधव जाळे घेऊन समुद्रात गेले.", "/koːɭi/"),
        ("गवंडी", "Gavandi", "Mason building stone walls and rural structures", "Standard Marathi", "Statewide", "Thane", "Shahapur", "गवंड्याने दगडी घराचे बांधकाम पूर्ण केले.", "/ɡəʋəɳɖi/"),
        ("गुरखी", "Gurakhi", "Cowherd tending livestock on pastures", "Standard Marathi", "Western Ghats", "Sangli", "Shirala", "डोंगरावर गुरखी बासरी वाजवत गायी चारत होता.", "/ɡurəkʰi/"),
        ("बलुतेदार", "Balutedar", "Traditional village artisan service community", "Standard Marathi", "Statewide", "Ahmednagar", "Sangamner", "पूर्वीच्या खेड्यात बारा बलुतेदार पद्धत होती.", "/bəlut̪eːd̪aːr/")
    ],
    "Daily Life": [
        ("दळणवळण", "Dalanvalan", "Transportation and travel connectivity", "Standard Marathi", "Statewide", "Pune", "City", "रस्त्यांमुळे खेड्यांचे दळणवळण सुलभ झाले.", "/d̪əɭəɳəʋəɭəɳ/"),
        ("सडा-रांगोळी", "Sada-Rangoli", "Morning doorstep sweeping and rangoli ritual", "Standard Marathi", "Statewide", "Satara", "Patan", "सकाळी अंगणात सडा-रांगोळी घातली जाते.", "/səɖaː raːŋɡoːɭi/"),
        ("बाजारहाट", "Bajarhaat", "Weekly local village market shopping", "Varhadi", "Vidarbha", "Yavatmal", "Pusad", "शनिवारी सर्व गावकरी बाजारहाट करायला जातात.", "/baːd͡ʒaːrəhaːʈ/"),
        ("पाहुणचार", "Pahunachar", "Warm hospitality towards guests", "Malvani", "Konkan", "Sindhudurg", "Malvan", "कोकणातील लोकांचा पाहुणचार खूप आपुलकीचा असतो.", "/paːhuɳət͡saːr/"),
        ("गप्पागोष्टी", "Gappagoshti", "Evening chitchat on the village veranda", "Standard Marathi", "Statewide", "Solapur", "Pandharpur", "चावडीवर संध्याकाळी म्हातारे गप्पागोष्टी करतात.", "/ɡəppaːɡoːšʈi/"),
        ("चावडी", "Chavadi", "Village community gathering hall", "Marathwadi", "Marathwada", "Latur", "Ausa", "गावातील तंट्यांचा निकाल चावडीवर लागत असे.", "/t͡saːʋəɖi/"),
        ("ओटा", "Ota", "Raised open veranda outside house", "Ahirani", "Khandesh", "Jalgaon", "Bhusawal", "दुपारच्या वेळी आजोबा ओट्यावर विश्रांती घेतात.", "/oːʈaː/"),
        ("शिदोरी", "Shidori", "Packed food carried for farm work", "Standard Marathi", "Desh", "Kolhapur", "Shirol", "कामावर जाताना भाकरीची शिदोरी सोबत घेतली.", "/šid̪oːri/"),
        ("आंघोळ", "Anghol", "Daily bathing and purification routine", "Standard Marathi", "Statewide", "Nashik", "Trimbak", "सकाळी गरम पाण्याने आंघोळ केली.", "/aːŋɡʱoːɭ/"),
        ("झोपडी", "Jhopadi", "Thatch-roofed farm dwelling", "Standard Marathi", "Statewide", "Beed", "Ashti", "शेताच्या कडेला शेतकऱ्याची झोपडी आहे.", "/d͡ʒʰoːpəɖi/")
    ],
    "Places": [
        ("गावठाण", "Gavthan", "Residential inhabited core of village", "Standard Marathi", "Statewide", "Pune", "Haveli", "गावठाणात जुनी पारंपरिक घरे पाहायला मिळतात.", "/ɡaːʋət̪ʰaːɳ/"),
        ("खळे", "Khale", "Threshing ground for harvested crop processing", "Varhadi", "Vidarbha", "Amravati", "Morshi", "खळ्यात धान्याची पोती भरली जात आहेत.", "/kʰəɭeː/"),
        ("वाडगा", "Vadga", "Small rural hamlet or settlement", "Marathwadi", "Marathwada", "Osmanabad", "Tuljapur", "डोंगराच्या पायथ्याशी एक लहान वाडगा आहे.", "/ʋaːɖəɡaː/"),
        ("माळरान", "Malran", "Expansive open grassland meadow", "Standard Marathi", "Desh", "Satara", "Man", "माळरानावर मेंढपाळ मेंढ्या चारत आहेत.", "/maːɭəraːn/"),
        ("घाटमाथा", "Ghatmatha", "Crestline of the Western Ghats mountain range", "Standard Marathi", "Western Ghats", "Ratnagiri", "Chiplun", "घाटमाथ्यावर पावसाळ्यात ढग दाटून येतात.", "/ɡʱaːʈəmaːt̪ʰaː/"),
        ("बंदर", "Bandar", "Coastal harbor or jetty for boats", "Malvani", "Konkan", "Sindhudurg", "Devgad", "देवगडच्या बंदरावर मासेमारी बोटी उभ्या आहेत.", "/bənd̪ər/"),
        ("वाडा", "Wada", "Traditional historic courtyard mansion", "Standard Marathi", "Desh", "Pune", "City", "पुण्यातील शनिवारवाडा हा ऐतिहासिक वास्तू आहे.", "/ʋaːɖaː/"),
        ("विहीर", "Vihir", "Stone-lined freshwater well", "Standard Marathi", "Statewide", "Jalna", "Ambad", "विहिरीला बारमाही गोड पाणी असते.", "/ʋihiːr/"),
        ("पाणवठा", "Panvatha", "Community water source along lake or river", "Standard Marathi", "Statewide", "Nanded", "Hadgaon", "गावातील पाणवठ्यावर गुरांना पाणी पाजले जाते.", "/paːɳəʋət̪ʰaː/"),
        ("देऊळ", "Deool", "Sacred village temple or shrine", "Standard Marathi", "Statewide", "Solapur", "Karmala", "गावाच्या मध्यभागी मारुतीचे पुरातन देऊळ आहे.", "/d̪eːuɭ/")
    ],
    "Emotions": [
        ("माया", "Maya", "Tender maternal affection and caring love", "Malvani", "Konkan", "Sindhudurg", "Vengurla", "आईची माया जगात कशानेही तोलली जाऊ शकत नाही.", "/maːjaː/"),
        ("आपुलकी", "Apulki", "Warm sense of closeness, belonging, and cordiality", "Standard Marathi", "Statewide", "Pune", "Haveli", "त्यांच्या बोलण्यातून मनापासून आपुलकी जाणवते.", "/aːpuləki/"),
        ("कौतुक", "Kautuk", "Affectionate praise and admiring delight", "Standard Marathi", "Statewide", "Satara", "Karad", "मुलाच्या यशाचे सर्वांनी मनापासून कौतुक केले.", "/kəut̪uk/"),
        ("हुरहूर", "Hurhur", "Wistful anticipation or poignant longing", "Varhadi", "Vidarbha", "Wardha", "Hinganghat", "घराबाहेर पडताना मनात कसलीशी हुरहूर लागली होती.", "/hurəhur/"),
        ("अभिमान", "Abhiman", "Dignified cultural pride and self-worth", "Standard Marathi", "Statewide", "Kolhapur", "Karvir", "आपल्या भाषेचा आणि संस्कृतीचा सर्वांना अभिमान असावा.", "/əbʱimaːn/"),
        ("राग", "Raag", "Sudden anger or righteous indignation", "Standard Marathi", "Statewide", "Nashik", "City", "अन्याय पाहताच त्याचा राग अनावर झाला.", "/raːɡ/"),
        ("आनंद", "Aanand", "Deep joy, happiness and inner celebration", "Standard Marathi", "Statewide", "Thane", "Kalyan", "सण साजरा करताना सर्वांच्या चेहऱ्यावर आनंद ओसंडून वाहत होता.", "/aːnənd̪/"),
        ("धीर", "Dheer", "Patience, courage and steady fortitude", "Marathwadi", "Marathwada", "Beed", "Majalgaon", "संकटाच्या काळात धीर सोडता कामा नये.", "/d̪ʱiːr/"),
        ("उत्साह", "Utsaah", "Vibrant enthusiasm and keen energy", "Standard Marathi", "Statewide", "Sangli", "Miraj", "तरुणांनी समाजकार्यात मोठा उत्साह दाखवला.", "/ut̪saːh/"),
        ("दुःख", "Duhkh", "Grief, sorrow, and empathetic pain", "Standard Marathi", "Statewide", "Aurangabad", "City", "दुसऱ्याचे दुःख समजून घेणे हीच खरी माणुसकी आहे.", "/d̪ukʰ/")
    ],
    "Traditional Culture": [
        ("दशावतार", "Dashavatara", "Traditional coastal folk theatre of Konkan", "Malvani", "Konkan", "Sindhudurg", "Kudal", "कोकणातील जत्रेत दशावतार नाटक रात्रभर चालते.", "/d̪əšaːʋət̪aːr/"),
        ("भारुड", "Bharud", "Metaphorical devotional folk discourse by Saint Eknath", "Varhadi", "Vidarbha", "Amravati", "Warud", "भारुडातून समाजाला नैतिक मूल्यांची शिकवण दिली जाते.", "/bʱaːruːɖ/"),
        ("गोंधळ", "Gondhal", "Traditional ritual invocation of Goddess Bhavani", "Standard Marathi", "Statewide", "Kolhapur", "Karvir", "लग्नानंतर कुलदेवतेचा गोंधळ घालण्याची रीत आहे.", "/ɡoːnd̪ʰəɭ/"),
        ("लावणी", "Lavani", "Expressive rhythmic dance of Maharashtra with dholki", "Standard Marathi", "Statewide", "Pune", "Haveli", "लावणी ही महाराष्ट्राची प्रसिद्ध लोककला आहे.", "/laːʋəɳi/"),
        ("पोवाडा", "Povada", "Heroic ballad honoring Chhatrapati Shivaji Maharaj", "Standard Marathi", "Statewide", "Satara", "Jawali", "शाहीर शिवरायांच्या पराक्रमाचा पोवाडा गातात.", "/poːʋaːɖaː/"),
        ("कीर्तन", "Kirtan", "Devotional musical discourse on philosophy", "Standard Marathi", "Statewide", "Nashik", "Trimbak", "मंदिरात वारकरी महाराजांचे सुंदर कीर्तन झाले.", "/kiːrt̪ən/"),
        ("वारकरी", "Varkari", "Centuries-old pilgrimage tradition to Pandharpur", "Standard Marathi", "Desh", "Solapur", "Pandharpur", "वारकरी गळ्यात तुळशीची माळ आणि हाती टाळ घेतात.", "/ʋaːrəkəri/"),
        ("दिंडी", "Dindi", "Procession of walking pilgrims with saffron flags", "Standard Marathi", "Statewide", "Pune", "Alandi", "आषाढी एकादशीला आळंदीवरून दिंडी निघते.", "/d̪iɳɖi/"),
        ("लेझीम", "Lezim", "Rhythmic fitness folk dance with metal jingles", "Standard Marathi", "Statewide", "Kolhapur", "Shirol", "गणेशोत्सवाच्या मिरवणुकीत लेझीम पथक पुढे असते.", "/leːd͡ʒʰiːm/"),
        ("फुगडी", "Fugdi", "Joyous circular spinning folk dance of women", "Standard Marathi", "Statewide", "Raigad", "Roha", "मंगळागौरीच्या रात्री स्त्रिया फुगडी खेळतात.", "/pʰuɡəɖi/")
    ],
    "Phrases": [
        ("काय रे ख़य चाललोस?", "Khay challos?", "Where are you going?", "Malvani", "Konkan Coast", "Sindhudurg", "Malvan", "बाबल्या, आज सकाळीच ख़य चाललोस?", "/kʰəj t͡saːlloːs/"),
        ("कसं काय भाऊ?", "Kasam kay bhau?", "How are things going, brother?", "Varhadi", "Vidarbha", "Amravati", "Akola", "अरे रामभाऊ, कसं काय भाऊ? शेतात पेरणी झाली का?", "/kəsəŋ kaːj bʱaːu/"),
        ("कशास तुले?", "Kashas tule?", "Why do you need it?", "Ahirani", "Khandesh", "Dhule", "Shirpur", "कशास तुले ते पुस्तक आज?", "/kəʃaːs tuleː/"),
        ("का हाल बा?", "Kahaal ba?", "How are you doing?", "Marathwadi", "Marathwada", "Nanded", "Deglur", "भावा, आज का हाल बा तुझं?", "/kaː haːl baː/"),
        ("येवा कोंकण आपलोच आसा!", "Yeva Konkan aploch asa!", "Welcome! Konkan belongs to all of us!", "Malvani", "Konkan", "Ratnagiri", "Rajapur", "येवा कोंकण आपलोच आसा, मासे खाऊक भेटतले!", "/jeːʋaː koːŋkəɳ aːpəloːt͡ʃ aːsaː/"),
        ("काय हालहवाल?", "Kay halhaval?", "What is the latest news and wellbeing?", "Standard Marathi", "Statewide", "Pune", "Haveli", "फार दिवसांनी भेटलो, सांग काय हालहवाल?", "/kaːj haːləhəʋaːl/"),
        ("काय चाललंय?", "Kay challay?", "What is happening nowadays?", "Standard Marathi", "Statewide", "Mumbai", "Thane", "अरे मित्रा, सध्या काय चाललंय?", "/kaːj t͡saːlləj/"),
        ("शुभ प्रभात", "Shubh Prabhat", "Good morning greeting", "Standard Marathi", "Statewide", "Nashik", "City", "सर्वांना आजच्या दिवसाच्या शुभ प्रभात!", "/šubʰə prəbʰaːt̪/"),
        ("काळजी घ्या", "Kalji ghya", "Take good care of yourself", "Standard Marathi", "Statewide", "Satara", "Karad", "प्रवासात सर्वांनी स्वतःची काळजी घ्या.", "/kaːɭəd͡ʒi ɡʰjaː/"),
        ("पुन्हा भेटा", "Punha bheta", "Visit again soon", "Standard Marathi", "Statewide", "Kolhapur", "Shirol", "आमच्या गावाला पुन्हा नक्की भेटा.", "/punəhaː bʰeːʈaː/")
    ],
    "Idioms": [
        ("कानाडोळा करणे", "Kanadola karne", "To intentionally ignore or turn a blind eye", "Standard Marathi", "Statewide", "Pune", "Haveli", "चुक कडे शिक्षकांनी कानाडोळा केला.", "/kaːnaːɖoːɭaː kərɳeː/"),
        ("हात मारणे", "Haat marne", "To seize an opportunity or make a large profit", "Standard Marathi", "Statewide", "Mumbai", "Suburbs", "व्यापाऱ्याने या मोसमात चांगला हात मारला.", "/haːt̪ maːrɳeː/"),
        ("डोळ्यात धूळ फेकणे", "Dolyat dhool phekne", "To deceive or hoodwink someone cleverly", "Standard Marathi", "Statewide", "Thane", "Kalyan", "चोराने पोलिसांच्या डोळ्यात धूळ फेकली.", "/ɖoːɭjaːt̪ dʰuːɭ pʰeːkɳeː/"),
        ("आकाशाला गवसणी घालणे", "Aakashala gavasani ghalne", "To achieve extraordinary greatness", "Standard Marathi", "Statewide", "Nagpur", "City", "वैज्ञानिक संशोधनाने आकाशाला गवसणी घातली.", "/aːkaːšaːlaː ɡəʋəsəɳi ɡʰaːlɳeː/"),
        ("जीव टांगणीला लागणे", "Jeev tangnila lagne", "To be in extreme anxiety or suspense", "Standard Marathi", "Statewide", "Satara", "Wai", "निकाल येईपर्यंत पालकांचा जीव टांगणीला लागला.", "/d͡ʒiːʋ t meː/"),
        ("पाणी पाजणे", "Paani pajne", "To thoroughly defeat a competitor", "Standard Marathi", "Statewide", "Kolhapur", "Karvir", "मैदानावर भारतीय संघाने प्रतिस्पर्ध्याला पाणी पाजले.", "/paːɳi paːd͡ʒɳeː/"),
        ("उर भरून येणे", "Ur bharun yene", "To be overwhelmed with deep pride and emotion", "Standard Marathi", "Statewide", "Sangli", "Miraj", "मुलाचे यश पाहून आईचा उर भरून आला.", "/ur bʰəruːn yeːɳeː/"),
        ("पाय जमिनीवर असणे", "Paay jaminivar asne", "To stay humble and grounded despite success", "Standard Marathi", "Statewide", "Nashik", "City", "मोठा उद्योगपती झाला तरी त्याचे पाय जमिनीवर आहेत.", "/paːj d͡ʒəmIniːʋər əsəɳeː/"),
        ("नाव कमवणे", "Naav kamavne", "To earn widespread fame and honor", "Standard Marathi", "Statewide", "Aurangabad", "City", "खेळाडूने आंतरराष्ट्रीय स्तरावर नाव कमावले.", "/naːʋ kəməʋɳeː/"),
        ("नन्नाचा पाढा वाचणे", "Nannacha padha vachne", "To continuously plead helplessness or refusal", "Standard Marathi", "Statewide", "Solapur", "North", "मदत मागताच त्याने नन्नाचा पाढा वाचला.", "/nənnaːt͡saː paːɖʰaː ʋaːt͡sɳeː/")
    ],
    "Proverbs": [
        ("अती तेथे माती", "Ati tethe mati", "Excess of anything leads to ruin and disaster", "Standard Marathi", "Statewide", "Pune", "Haveli", "कोणत्याही गोष्टीचा अतिरेक वाईट, शेवटी अती तेथे माती होते.", "/ət̪i t̪eːt̪ʰeː maːt̪i/"),
        ("नाचता येईना अंगण वाकडे", "Nachtaa yeina angan vakade", "A bad workman blames his tools", "Standard Marathi", "Statewide", "Satara", "Wai", "स्वतःला काम येत नसताना इतरांना दोष देणे म्हणजे नाचता येईना अंगण वाकडे.", "/naːt͡sət̪aː jeːiːnaː əŋɡəɳ ʋaːkəɖeː/"),
        ("काखेत कळसा गावाला वळसा", "Kakhet kalasa gavala valasa", "Searching for something everywhere when it is right next to you", "Standard Marathi", "Statewide", "Kolhapur", "Karvir", "चष्मा कपाळावर असताना शोधत बसणे म्हणजे काखेत कळसा गावाला वळसा.", "/kaːkʰeːt̪ kəɭəsaː ɡaːʋaːlaː ʋəɭəsaː/"),
        ("गरज सरो आणि वैद्य मरो", "Garaj saro ani vaidya maro", "Forgetting the benefactor once the need is fulfilled", "Standard Marathi", "Statewide", "Nashik", "Sinnar", "काम झाल्यावर मदत करणाऱ्याला विसरणे म्हणजे गरज सरो आणि वैद्य मरो.", "/ɡərəd͡ʒ səroː aːɳi ʋəidjə məroː/"),
        ("दिव्याखाली अंधार", "Divyakhali andhar", "Darkness under the lamp (Flaws near greatness)", "Standard Marathi", "Statewide", "Aurangabad", "Paithan", "प्रसिद्ध माणसाच्या घरातच समस्या असणे म्हणजे दिव्याखाली अंधार.", "/d̪iʋjaːkʰaːli əndʱaːr/"),
        ("झाकली मूठ सव्वा लाखाची", "Jhakali muth savva lakhachi", "Keeping matters confidential preserves honor", "Standard Marathi", "Statewide", "Solapur", "Barshi", "कौटुंबिक वाद बाहेर न सांगता झाकली मूठ सव्वा लाखाची ठेवावी.", "/d͡ʒʰaːkəli muːʈʰ səʋʋaː laːkʰaːt͡si/"),
        ("पेरावे तसे उगवते", "Perave tase ugavate", "As you sow, so shall you reap", "Standard Marathi", "Statewide", "Amravati", "Warud", "चांगले कर्म कराल तर चांगले फळ मिळेल, कारण पेरावे तसे उगवते.", "/peːraːʋeː t̪əseː ugəʋət̪eː/"),
        ("आयत्या बिळात नागोबा", "Aatyat bilat nagoba", "Taking unfair advantage of someone else's hard work", "Standard Marathi", "Statewide", "Latur", "Udgir", "दुसऱ्याने बांधलेल्या घरात ताबा मिळवणे म्हणजे आयत्या बिळात नागोबा.", "/aːjətjaː biɭaːt̪ naːɡoːbaː/"),
        ("उथळ पाण्याला खळखळाट मोठा", "Uthal panyala khalkhalat motha", "Empty vessels make the most noise", "Standard Marathi", "Statewide", "Nagpur", "City", "कमी ज्ञान असणारा माणूसच जास्त बढाया मारतो, उथळ पाण्याला खळखळाट मोठा.", "/ut̪ʰəɭ paːɳjaːlaː kʰəɭəkʰəɭaːʈ moːʈʰaː/"),
        ("चोराच्या उलट्या बोंबा", "Chorachya ultya bomba", "The guilty party loudly blaming others to hide their fault", "Standard Marathi", "Statewide", "Thane", "Kalyan", "स्वतः चूक करून समोरच्यालाच दोष देणे म्हणजे चोराच्या उलट्या बोंबा.", "/t͡soːraːt͡sjaː uləʈjaː boːmbaː/")
    ]
}

AUDIO_STORIES_DATA = [
    ("Ahmednagar", "Akole", "Brahmanwada", 19.343, 74.034, "Janabai Deshmukh (F60+)", "https://sdml.ac.in/story/Brahmanwada/1/fullstory.wav", "Traditional Farming and Monsoon Lore", "Agriculture"),
    ("Sindhudurg", "Malvan", "Katta", 16.147, 73.536, "Sushila Tai (F50)", "https://sdml.ac.in/story/Katta/1/fullstory.wav", "Festival Memories & Dashavatara Lore", "Traditional Culture"),
    ("Sindhudurg", "Malvan", "Dandi", 16.0514, 73.4592, "Ramesh Patil (M35)", "https://sdml.ac.in/story/Dandi/2/fullstory.wav", "Life in the Konkan Fishing Village", "Daily Life"),
    ("Amravati", "Warud", "Gadegaon", 21.361, 78.256, "Ganpat Kaka (M75)", "https://sdml.ac.in/story/Gadegaon/2/fullstory.wav", "Vidarbha Cotton Soil and Folklore", "Agriculture"),
    ("Raigad", "Alibag", "Mandwa", 18.7953, 72.892, "Vimal Koli (F52)", "https://sdml.ac.in/story/Mandwa/1/fullstory.wav", "Songs of the Konkan Coastal Tide", "Traditional Culture"),
    ("Dhule", "Shirpur", "Ambe", 21.429, 75.113, "Sarala Patil (F55)", "https://sdml.ac.in/story/Ambe/1/fullstory.wav", "Kanbai Folk Tales of Tapi River", "Traditional Culture"),
    ("Satara", "Patan", "Helwak", 17.373, 73.722, "Ananda Shinde (M68)", "https://sdml.ac.in/story/Helwak/2/fullstory.wav", "Koyna Valley Oral History", "Nature"),
    ("Nagpur", "Ramtek", "Navegaon", 21.398, 79.327, "Bapurao Uike (M62)", "https://sdml.ac.in/story/Maregaon/1/fullstory.wav", "Forest Traditions of Vidarbha", "Nature")
]

QUIZ_DECKS_DATA = [
    {
        "dialect_name": "Malvani",
        "title": "Malvani Dialect Vocabulary Challenge",
        "description": "Test your knowledge of authentic coastal Malvani words, idioms, and daily greetings.",
        "difficulty": "Beginner",
        "questions": [
            {
                "question": "In Malvani dialect, what does 'ख़य चाललोस?' mean?",
                "a": "What are you eating?",
                "b": "Where are you going?",
                "c": "Who is calling you?",
                "d": "When will you return?",
                "correct": "B",
                "explanation": "'ख़य' is the coastal Malvani equivalent of standard Marathi 'कुठे' (where)."
            },
            {
                "question": "What is the meaning of the coastal term 'चेडू' in Malvani?",
                "a": "Young girl or daughter",
                "b": "Small fishing boat",
                "c": "Sweet mango fruit",
                "d": "Morning tea",
                "correct": "A",
                "explanation": "'चेडू' is an affectionate Malvani term for a young girl or daughter."
            },
            {
                "question": "Which traditional theatre art form is deeply preserved in the Malvan Konkan coast?",
                "a": "Nautanki",
                "b": "Dashavatara",
                "c": "Kathakali",
                "d": "Yakshagana",
                "correct": "B",
                "explanation": "Dashavatara is the iconic 800-year-old folk theatre tradition of Sindhudurg and South Konkan."
            }
        ]
    },
    {
        "dialect_name": "Varhadi",
        "title": "Varhadi Vidarbha Expressions",
        "description": "Explore the colorful agrarian dialect of Vidarbha and its friendly colloquialisms.",
        "difficulty": "Intermediate",
        "questions": [
            {
                "question": "What does the common Varhadi greeting 'कसं काय भाऊ?' mean?",
                "a": "Where is your brother?",
                "b": "How are things going, brother?",
                "c": "What are you buying?",
                "d": "Why are you late?",
                "correct": "B",
                "explanation": "'कसं काय भाऊ?' is the warmest friendly greeting heard across Vidarbha."
            },
            {
                "question": "In Vidarbha, harvested cotton fields and farmland are often called:",
                "a": "वावर (Vaavar)",
                "b": "खाडी (Khadi)",
                "c": "डोंगर (Dongar)",
                "d": "ओटा (Ota)",
                "correct": "A",
                "explanation": "'वावर' is the beloved Vidarbha and Khandesh term for one's agricultural field."
            }
        ]
    },
    {
        "dialect_name": "Ahirani",
        "title": "Ahirani & Khandesh Regional Heritage",
        "description": "Discover words from the Tapi river basin blending ancient Marathi roots.",
        "difficulty": "Beginner",
        "questions": [
            {
                "question": "In Ahirani dialect, what does 'कशास तुले?' convey?",
                "a": "Why do you need it?",
                "b": "Where are you staying?",
                "c": "What time is it?",
                "d": "How is the harvest?",
                "correct": "A",
                "explanation": "'कशास तुले?' translates to 'तुला कशाला हवे?' in standard Marathi."
            }
        ]
    }
]

def seed_database(db: Session):
    print("Initializing comprehensive BhashaLok database seeding...")

    # 1. Seed Users
    if not db.query(User).filter(User.username == "admin").first():
        admin_user = User(
            username="admin",
            email="admin@bhashalok.org",
            hashed_password=get_password_hash("Admin123!"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            reputation_points=1000,
            badge_title="Grand Preserver"
        )
        linguist_user = User(
            username="dr_patil",
            email="patil@linguistics.ac.in",
            hashed_password=get_password_hash("Linguist123!"),
            full_name="Dr. Rajesh Patil (PhD Linguistics)",
            role=UserRole.LINGUIST,
            reputation_points=500,
            badge_title="Senior Dialectologist"
        )
        contributor_user = User(
            username="konkan_preserver",
            email="suhas@konkan.org",
            hashed_password=get_password_hash("User123!"),
            full_name="Suhas Sawant",
            role=UserRole.CONTRIBUTOR,
            reputation_points=120,
            badge_title="Cultural Explorer"
        )
        db.add_all([admin_user, linguist_user, contributor_user])
        db.commit()
    extra_users = [
        ("dr_chitnis", "chitnis@linguistics.ac.in", "chitnis_secret", "Dr. Chitnis", UserRole.LINGUIST, 450, "Dialectologist"),
        ("parth_kadam", "parth@bhashalok.org", "parthpassword123", "Parth Kadam", UserRole.CONTRIBUTOR, 350, "Lead Contributor")
    ]
    for uname, uemail, upass, ufull, urole, urep, ubadge in extra_users:
        if not db.query(User).filter(User.username == uname).first():
            db.add(User(
                username=uname,
                email=uemail,
                hashed_password=get_password_hash(upass),
                full_name=ufull,
                role=urole,
                reputation_points=urep,
                badge_title=ubadge
            ))
    db.commit()


    # 2. Seed Categories (All 15 Canonical Semantic Categories)
    for cat_name, cat_desc in ALL_CATEGORIES:
        if not db.query(Category).filter(Category.name == cat_name).first():
            db.add(Category(name=cat_name, description=cat_desc))
    db.commit()

    # 3. Seed Regional Varieties & Dialects
    dialect_map = {}
    for name, code, desc, reg_name, dists, lat, lon, status, speakers, notes in VARIETIES:
        d = db.query(Dialect).filter(Dialect.code == code).first()
        if not d:
            d = Dialect(
                name=name,
                code=code,
                description=desc,
                region=reg_name,
                region_name=reg_name,
                parent_language="Marathi",
                state="Maharashtra",
                districts=dists,
                latitude=lat,
                longitude=lon,
                endangerment_status=status,
                estimated_speakers=speakers,
                cultural_notes=notes
            )
            db.add(d)
            db.commit()
            db.refresh(d)
        dialect_map[name] = d

    # 4. Seed Contributors
    for name, loc, dist, role, bio, img in TEAM_CONTRIBUTORS:
        if not db.query(Contributor).filter(Contributor.name == name).first():
            db.add(Contributor(name=name, location=loc, district=dist, role=role, bio=bio, profile_image=img))
    db.commit()

    default_contributor = db.query(Contributor).first()
    contrib_id = default_contributor.id if default_contributor else 1

    # 5. Seed Vocabulary Entries across all 15 Categories
    entries_count = 0
    for cat_name, items in DEMO_ENTRIES_DATA.items():
        for item in items:
            word, trans, meaning, variety, region, dist, taluka, sentence, ipa = item
            existing = db.query(Entry).filter(Entry.word == word, Entry.category == cat_name).first()
            if not existing:
                d_obj = dialect_map.get(variety) or dialect_map.get("Standard Marathi")
                d_id = d_obj.id if d_obj else 1
                phonetic_code = generate_indic_soundex(word)
                entry = Entry(
                    word=word,
                    transliteration=trans,
                    meaning=meaning,
                    meaning_standard_lang=meaning,
                    language="Marathi",
                    variety=variety,
                    dialect_id=d_id,
                    category=cat_name,
                    region=region,
                    district=dist,
                    taluka=taluka,
                    example_sentence=sentence,
                    example_sentence_translation=meaning,
                    ipa_transcription=ipa,
                    phonetic_code=phonetic_code,
                    pronunciation=ipa,
                    contributor_id=contrib_id,
                    source="Field Preservation Survey",
                    status="published",
                    verification_status=VerificationStatus.VERIFIED,
                    upvotes=15
                )
                db.add(entry)
                entries_count += 1
    db.commit()

    # 6. Seed Fieldwork Audio Recordings
    for dist, tal, vil, lat, lon, spk, url, title, genre in AUDIO_STORIES_DATA:
        if not db.query(AudioArchive).filter(AudioArchive.title == title).first():
            d_obj = dialect_map.get("Malvani") if "Malvan" in dist else (dialect_map.get("Varhadi") if "Amravati" in dist else dialect_map.get("Standard Marathi"))
            d_id = d_obj.id if d_obj else 1
            transcript = f"Recorded oral narrative '{title}' preserved in {vil}, {dist} district. Speakers share heritage tales of their community."
            srt_text = generate_srt_subtitles(transcript, 120.0)
            rec = AudioArchive(
                dialect_id=d_id,
                title=title,
                genre=genre,
                speaker_name=spk,
                locality=f"{vil}, {dist}",
                audio_file_path=url,
                duration_seconds=120.0,
                waveform_json=json.dumps(generate_waveform_peaks(50)),
                transcript_text=transcript,
                transcript_translation_en=f"English narrative translation of {title}.",
                transcript_translation_standard=f"{title} - स्थानिक मराठी बोली संकलन.",
                srt_subtitles=srt_text,
                verification_status=VerificationStatus.VERIFIED,
                views_count=150
            )
            db.add(rec)
    db.commit()

    # 7. Seed Quiz Decks & Questions
    for d_info in QUIZ_DECKS_DATA:
        if not db.query(QuizDeck).filter(QuizDeck.title == d_info["title"]).first():
            d_obj = dialect_map.get(d_info["dialect_name"]) or dialect_map.get("Malvani")
            d_id = d_obj.id if d_obj else 1
            deck = QuizDeck(
                dialect_id=d_id,
                title=d_info["title"],
                description=d_info["description"],
                difficulty=d_info["difficulty"]
            )
            db.add(deck)
            db.commit()
            db.refresh(deck)

            for q in d_info["questions"]:
                question = QuizQuestion(
                    deck_id=deck.id,
                    question_text=q["question"],
                    option_a=q["a"],
                    option_b=q["b"],
                    option_c=q["c"],
                    option_d=q["d"],
                    correct_option=q["correct"],
                    explanation=q["explanation"]
                )
                db.add(question)
            db.commit()

    print(f"Database successfully populated with all 15 categories, 7 dialects, team contributors, {entries_count} entries, audio stories, and quizzes!")
