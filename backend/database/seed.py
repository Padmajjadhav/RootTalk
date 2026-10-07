import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import Base, engine, SessionLocal
from app.models.models import LanguageVariety, Category, Contributor, Entry, VoiceRecording
from app.services.phonetic import devanagari_to_ipa
import datetime

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
    ("Standard Marathi", "Official standard variety of Marathi used across Maharashtra.", "Maharashtra State"),
    ("Malvani", "Coastal Marathi variety spoken in Sindhudurg and South Konkan.", "Konkan Region"),
    ("Varhadi", "Soft, expressive regional variety spoken across the Vidarbha region.", "Vidarbha Region"),
    ("Ahirani", "Khandesh regional variety blending ancient Marathi with Bhili phonetics.", "Khandesh Region"),
    ("Agri", "Coastal North Konkan regional variety spoken in Thane and Raigad.", "North Konkan"),
    ("Koli", "Maritime fishing community variety preserved across coastal ports.", "Coastal Belt"),
    ("Marathwadi", "Regional variety of central Maharashtra / Marathwada region.", "Marathwada Region")
]

DEMO_ENTRIES_DATA = {
    "Agriculture": [
        ("पेरणी", "Perani", "Sowing of crops", "Standard Marathi", "Prakriti", "Ahmednagar", "Akole", "पाऊस पडताच शेतकरी पेरणीला लागतात.", "/peːrəɳi/"),
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
        ("पाऊस", "Paaus", "Rainfall or monsoon rain", "Standard Marathi", "Statewide", "Ratnagiri", "Dapoli", "कोकणात मुसळधार पाऊस पडतो.", "/paːus/"),
        ("वारा", "Vaara", "Breeze or wind", "Standard Marathi", "Statewide", "Sindhudurg", "Vengurla", "समुद्रावरून थंड वारा वाहत आहे.", "/ʋaːraː/"),
        ("डोंगर", "Dongar", "Hill or mountain peak", "Standard Marathi", "Western Ghats", "Pune", "Bhor", "डोंगरावर हिरवेगार गवत उगवले आहे.", "/ɖoːŋɡər/"),
        ("नदी", "Nadi", "River or flowing stream", "Standard Marathi", "Statewide", "Nashik", "Niphad", "गोदावरी नदी महाराष्ट्राची जीवनदायिनी आहे.", "/nəd̪i/"),
        ("समुद्र", "Samudra", "Ocean or sea coast", "Malvani", "Konkan", "Raigad", "Shrivardhan", "अरबी समुद्र कोकण किनारपट्टीला भिडतो.", "/səmud̪rə/"),
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
    "Phrases": [
        ("काय रे ख़य चाललोस?", "Khay challos?", "Where are you going?", "Malvani", "Konkan Coast", "Sindhudurg", "Malvan", "बाबल्या, आज सकाळीच ख़य चाललोस?", "/kʰəj t͡saːlloːs/"),
        ("कसं काय भाऊ?", "Kasam kay bhau?", "How are things going, brother?", "Varhadi", "Vidarbha", "Amravati", "Akola", "अरे रामभाऊ, कसं काय भाऊ? शेतात पेरणी झाली का?", "/kəsəŋ kaːj bʱaːu/"),
        ("कशास तुले?", "Kashas tule?", "Why do you need it?", "Ahirani", "Khandesh", "Dhule", "Shirpur", "कशास तुले ते पुस्तक आज?", "/kəʃaːs tuleː/"),
        ("का हाल बा?", "Kahaal ba?", "How are you doing?", "Marathwadi", "Marathwada", "Nanded", "Deglur", "भावा, आज का हाल बा तुझं?", "/kaː haːl baː/"),
        ("येवा कोंकण आपलोच आसा!", "Yeva Konkan aploch asa!", "Welcome! Konkan belongs to all of us!", "Malvani", "Konkan", "Ratnagiri", "Rajapur", "येवा कोंकण आपलोच आसा, मासे खाऊक भेटतले!", "/jeːʋaː koːŋkəɳ aːpəloːt͡ʃ aːsaː/"),
        ("काय हालहवाल?", "Kay halhaval?", "What is the latest news/wellbeing?", "Standard Marathi", "Statewide", "Pune", "Haveli", "फार दिवसांनी भेटलो, सांग काय हालहवाल?", "/kaːj haːləhəʋaːl/"),
        ("काय चाललंय?", "Kay challay?", "What is going on?", "Standard Marathi", "Statewide", "Mumbai", "Thane", "अरे मित्रा, सध्या काय चाललंय?", "/kaːj t͡saːlləj/"),
        ("शुभ प्रभात", "Shubh Prabhat", "Good morning greeting", "Standard Marathi", "Statewide", "Nashik", "City", "सर्वांना आजच्या दिवसाच्या शुभ प्रभात!", "/šubʰə prəbʰaːt̪/"),
        ("काळजी घ्या", "Kalji ghya", "Take good care of yourself", "Standard Marathi", "Statewide", "Satara", "Karad", "प्रवासात सर्वांनी स्वतःची काळजी घ्या.", "/kaːɭəd͡ʒi ɡʰjaː/"),
        ("पुन्हा भेटा", "Punha bheta", "Visit again soon", "Standard Marathi", "Statewide", "Kolhapur", "Shirol", "आमच्या गावाला पुन्हा नक्की भेटा.", "/punəhaː bʰeːʈaː/")
    ],
    "Idioms": [
        ("कानाडोळा करणे", "Kanadola karne", "To intentionally ignore or turn a blind eye", "Standard Marathi", "Statewide", "Pune", "Haveli", "चुक कडे शिक्षकांनी कानाडोळा केला.", "/kaːnaːɖoːɭaː kərɳeː/"),
        ("हात मारणे", "Haat marne", "To make a big profit or plunder opportunities", "Standard Marathi", "Statewide", "Mumbai", "Suburbs", "व्यापाऱ्याने या मोसमात चांगला हात मारला.", "/haːt̪ maːrɳeː/"),
        ("डोळ्यात धूळ फेकणे", "Dolyat dhool phekne", "To deceive or hoodwink someone", "Standard Marathi", "Statewide", "Thane", "Kalyan", "चोराने पोलिसांच्या डोळ्यात धूळ फेकली.", "/ɖoːɭjaːt̪ dʰuːɭ pʰeːkɳeː/"),
        ("आकाशाला गवसणी घालणे", "Aakashala gavasani ghalne", "To achieve extraordinary greatness", "Standard Marathi", "Statewide", "Nagpur", "City", "वैज्ञानिक संशोधनाने आकाशाला गवसणी घातली.", "/aːkaːšaːlaː ɡəʋəsəɳi ɡʰaːlɳeː/"),
        ("जीव टांगणीला लागणे", "Jeev tangnila lagne", "To be in extreme anxiety or suspense", "Standard Marathi", "Statewide", "Satara", "Wai", "निकाल येईपर्यंत पालकांचा जीव टांगणीला लागला.", "/d͡ʒiːʋ t meː/"),
        ("पाणी पाजणे", "Paani pajne", "To defeat or teach a harsh lesson", "Standard Marathi", "Statewide", "Kolhapur", "Karvir", "मैदानावर भारतीय संघाने प्रतिस्पर्ध्याला पाणी पाजले.", "/paːɳi paːd͡ʒɳeː/"),
        ("उर भरून येणे", "Ur bharun yene", "To be overwhelmed with deep emotion/pride", "Standard Marathi", "Statewide", "Sangli", "Miraj", "मुलाचे यश पाहून आईचा उर भरून आला.", "/ur bʰəruːn yeːɳeː/"),
        ("पाय जमिनीवर असणे", "Paay jaminivar asne", "To remain humble despite great success", "Standard Marathi", "Statewide", "Nashik", "City", "मोठा उद्योगपती झाला तरी त्याचे पाय जमिनीवर आहेत.", "/paːj d͡ʒəmIniːʋər əsəɳeː/"),
        ("नाव कमवणे", "Naav kamavne", "To earn immense fame and respect", "Standard Marathi", "Statewide", "Aurangabad", "City", "खेळाडूने आंतरराष्ट्रीय स्तरावर नाव कमावले.", "/naːʋ kəməʋɳeː/"),
        ("नन्नाचा पाढा वाचणे", "Nannacha padha vachne", "To continuously plead inability or show empty hands", "Standard Marathi", "Statewide", "Solapur", "North", "मदत मागताच त्याने नन्नाचा पाढा वाचला.", "/nənnaːt͡saː paːɖʰaː ʋaːt͡sɳeː/")
    ],
    "Proverbs": [
        ("अती तेथे माती", "Ati tethe mati", "Excess of anything leads to ruin and disaster", "Standard Marathi", "Statewide", "Pune", "Haveli", "कोणत्याही गोष्टीचा अतिरेक वाईट, शेवटी अती तेथे माती होते.", "/ət̪i t̪eːt̪ʰeː maːt̪i/"),
        ("नाचता येईना अंगण वाकडे", "Nachtaa yeina angan vakade", "A bad workman blames his tools", "Standard Marathi", "Statewide", "Satara", "Wai", "स्वतःला काम येत नसताना इतरांना दोष देणे म्हणजे नाचता येईना अंगण वाकडे.", "/naːt͡sət̪aː jeːiːnaː əŋɡəɳ ʋaːkəɖeː/"),
        ("काखेत कळसा गावाला वळसा", "Kakhet kalasa gavala valasa", "Searching for something everywhere when it is right next to you", "Standard Marathi", "Statewide", "Kolhapur", "Karvir", "चष्मा कपाळावर असताना शोधत बसणे म्हणजे काखेत कळसा गावाला वळसा.", "/kaːkʰeːt̪ kəɭəsaː ɡaːʋaːlaː ʋəɭəsaː/"),
        ("गरज सरो आणि वैद्य मरो", "Garaj saro ani vaidya maro", "Forgetting the benefactor once the need is fulfilled", "Standard Marathi", "Statewide", "Nashik", "Sinnar", "काम झाल्यावर मदत करणाऱ्याला विसरणे म्हणजे गरज सरो आणि वैद्य मरो.", "/ɡərəd͡ʒ səroː aːɳi ʋəidjə məroː/"),
        ("दिव्याखाली अंधार", "Divyakhali andhar", "Darkness under the lamp (Unnoticed flaws near greatness)", "Standard Marathi", "Statewide", "Aurangabad", "Paithan", "प्रसिद्ध माणसाच्या घरातच समस्या असणे म्हणजे दिव्याखाली अंधार.", "/d̪iʋjaːkʰaːli əndʱaːr/"),
        ("झाकली मूठ सव्वा लाखाची", "Jhakali muth savva lakhachi", "Keeping matters confidential preserves honor and reputation", "Standard Marathi", "Statewide", "Solapur", "Barshi", "कौटुंबिक वाद बाहेर न सांगता झाकली मूठ सव्वा लाखाची ठेवावी.", "/d͡ʒʰaːkəli muːʈʰ səʋʋaː laːkʰaːt͡si/"),
        ("पेरावे तसे उगवते", "Perave tase ugavate", "As you sow, so shall you reap", "Standard Marathi", "Statewide", "Amravati", "Warud", "चांगले कर्म कराल तर चांगले फळ मिळेल, कारण पेरावे तसे उगवते.", "/peːraːʋeː t̪əseː ugəʋət̪eː/"),
        ("आयत्या बिळात नागोबा", "Aatyat bilat nagoba", "Taking unfair advantage of someone else's hard work", "Standard Marathi", "Statewide", "Latur", "Udgir", "दुसऱ्याने बांधलेल्या घरात ताबा मिळवणे म्हणजे आयत्या बिळात नागोबा.", "/aːjətjaː biɭaːt̪ naːɡoːbaː/"),
        ("उथळ पाण्याला खळखळाट मोठा", "Uthal panyala khalkhalat motha", "Empty vessels make the most noise", "Standard Marathi", "Statewide", "Nagpur", "City", "कमी ज्ञान असणारा माणूसच जास्त बढाया मारतो, उथळ पाण्याला खळखळाट मोठा.", "/ut̪ʰəɭ paːɳjaːlaː kʰəɭəkʰəɭaːʈ moːʈʰaː/"),
        ("चोराच्या उलट्या बोंबा", "Chorachya ultya bomba", "The guilty party making loud accusations to hide blame", "Standard Marathi", "Statewide", "Thane", "Kalyan", "स्वतः चूक करून समोरच्यालाच दोष देणे म्हणजे चोराच्या उलट्या बोंबा.", "/t͡soːraːt͡sjaː uləʈjaː boːmbaː/")
    ]
}

def seed_database(db: Session):
    print("Checking database seeding status...")

    # 1. Seed Categories
    for cat_name, cat_desc in ALL_CATEGORIES:
        existing = db.query(Category).filter(Category.name == cat_name).first()
        if not existing:
            db.add(Category(name=cat_name, description=cat_desc))
    db.commit()

    # 2. Seed Language Varieties
    for var_name, var_desc, var_reg in VARIETIES:
        existing = db.query(LanguageVariety).filter(LanguageVariety.name == var_name).first()
        if not existing:
            db.add(LanguageVariety(name=var_name, description=var_desc, region=var_reg))
    db.commit()

    # 3. Seed Team Contributors
    team_contributors = [
        ("Aaditya Jadhav", "Mumbai", "Mumbai Suburban", "Project Lead & Dialect Preserver", "Student preserver documenting Marathi regional dialects.", "assets/aaditya_jadhav.jpg"),
        ("Padmaj Jadhav", "Mumbai", "Mumbai City", "Linguistics Researcher", "Student researcher compiling Marathi folklore and vocabulary archive.", "assets/padmaj_jadhav.jpg"),
        ("Parth Kadam", "Mumbai", "Thane", "Technical Developer", "Student developer building BhashaLok digital repository APIs.", "assets/parth_kadam.jpg"),
        ("Dr. Rajesh Patil", "Pune", "Pune", "Senior Dialectologist", "Professor of Indic Linguistics and Marathi oral heritage auditor.", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=200&auto=format&fit=crop"),
        ("Sushila Tai", "Malvan", "Sindhudurg", "Native Speaker & Oral Folk Artist", "Coastal Konkan native storyteller and Dashavatara preserver.", "https://images.unsplash.com/photo-1544717305-2782549b5136?q=80&w=200&auto=format&fit=crop"),
        ("Ganpat Kaka", "Warud", "Amravati", "Farmer & Vidarbha Oral Historian", "Elder native speaker documenting traditional Vidarbha agricultural lore.", "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=200&auto=format&fit=crop")
    ]

    for name, loc, dist, role, bio, img in team_contributors:
        existing = db.query(Contributor).filter(Contributor.name == name).first()
        if not existing:
            db.add(Contributor(name=name, location=loc, district=dist, role=role, bio=bio, profile_image=img))
    db.commit()

    # 4. Seed Demo / Seed Entries across all 15 Categories
    default_contrib = db.query(Contributor).first()
    contrib_id = default_contrib.id if default_contrib else 1

    entries_added = 0
    for cat_name, entries in DEMO_ENTRIES_DATA.items():
        for item in entries:
            word, trans, meaning, variety, region, dist, taluka, sentence, ipa = item
            existing = db.query(Entry).filter(Entry.word == word, Entry.category == cat_name).first()
            if not existing:
                entry = Entry(
                    word=word,
                    transliteration=trans,
                    meaning=meaning,
                    language="Marathi",
                    variety=variety,
                    category=cat_name,
                    region=region,
                    district=dist,
                    taluka=taluka,
                    example_sentence=sentence,
                    pronunciation=ipa,
                    contributor_id=contrib_id,
                    source="Demo / Seed Data",
                    status="demo"
                )
                db.add(entry)
                entries_added += 1
    db.commit()

    print(f"Database successfully seeded! Added {entries_added} demo/seed entries covering all categories.")

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    db.close()
