from extensions import db
from app import create_app
from models import Maqam, MaqamAudio
import json

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # === DEFINE MAQAMET HERE ===

    maqam_AL_DHAIL = Maqam(
        name_ar="الذيل",
        name_en="Al Dhail",
        emotion="cheerful",
        emotion_ar="مرح",
        usage="Malouf",
        usage_ar="مالوف",
        ajnas_json=json.dumps([
            {
                "name": {"ar": "ذيل راست", "en": "Dhail Rast"},
                "notes": {"ar": ["صول", "فا", "مي نصف مخفوضة", "ري", "دو"],
                          "en": ["G", "F", "E-half-flat", "D", "C"]}
            },
            {
                "name": {"ar": "محير عراق نوا", "en": "Mhayer Iraq Nawa"},
                "notes": {"ar": ["دو", "سي نصف مخفوضة", "لا", "صول"],
                          "en": ["C", "B-half-flat", "A", "G"]}
            }
        ]),
        regions_json=json.dumps(["tunis", "sahel"]),       
        regions_ar_json=json.dumps(["تونس", "الساحل"]),    
        description_ar=(
            "مقام الذيل ذو طابع مرح وسريع الإيقاع، يُستعمل في المالوف "
            "أمثلة أغاني: ليالي السعود، خمرة الحب أسكرتني (تراث) "
            "(المناطق تقديرية: تونس/الساحل)"
        ),
        description_en=(
            "Al Dhail is a cheerful, fast-paced maqam used in Malouf. "
            "Song examples: Layali Essooud and Khamrat El Hob Askaretni (traditional). "
            "(Regions guessed: Tunis/Sahel)"
        ),
        related_json=json.dumps([]),
        difficulty_index=0.5,
        difficulty_label="intermediate",
        difficulty_label_ar="متوسط",
        emotion_weights_json=json.dumps({"cheerful": 1.0}),
        historical_periods_json=json.dumps(["1950s_radio", "modern_malouf"]),
        historical_periods_ar_json=json.dumps(["إذاعة الخمسينيات", "مالوف حديث"]),
        seasonal_usage_json=json.dumps(["no specific seasonal usage"]),
        seasonal_usage_ar_json=json.dumps(["لا يوجد استخدام موسمي محدد"]),
        rarity_level="common",
        rarity_level_ar="شائع",
    )

    maqam_AL_MAYA = Maqam(
        name_ar="الماية",
        name_en="Al Maya",
        emotion="romantic",
        emotion_ar="رومانسي",
        usage="Malouf",
        usage_ar="مالوف",
        ajnas_json=json.dumps([
            {
                "name": {"ar": "صابة راست", "en": "Saba Rast"},
                "notes": {"ar": ["فا", "مي نصف مخفوضة", "ري", "دو"],
                          "en": ["F", "E-half-flat", "D", "C"]}
            },
            {
                "name": {"ar": "سعداوي جهاركاه", "en": "Saadawi Jahar Kah"},
                "notes": {"ar": ["سي نصف مخفوضة", "لا", "صول", "فا"],
                          "en": ["B-half-flat", "A", "G", "F"]}
            }
        ]),
        regions_json=json.dumps(["tunis"]),           
        regions_ar_json=json.dumps(["تونس"]),         
        description_ar=(
            "مقام الماية ذو طابع رومانسي مريح وشاعري، يُستعمل في المالوف "
            "أمثؤلة أغاني: غيّبتشي عنك الصفا "
            "(المناطق تقديرية: تونس)"
        ),
        description_en=(
            "Al Maya is a romantic, soothing and poetic maqam used in Malouf. "
            "Song example: Ghaibtchi A'nak Essafa. "
            "(Regions guessed: Tunis)"
        ),
        related_json=json.dumps([]),
        difficulty_index=0.5,
        difficulty_label="intermediate",
        difficulty_label_ar="متوسط",
        emotion_weights_json=json.dumps({"romantic": 1.0}),
        historical_periods_json=json.dumps(["1960s_radio"]),
        historical_periods_ar_json=json.dumps(["إذاعة الستينيات"]),
        seasonal_usage_json=json.dumps(["no specific seasonal usage"]),
        seasonal_usage_ar_json=json.dumps(["لا يوجد استخدام موسمي محدد"]),
        rarity_level="common",
        rarity_level_ar="شائع",
    )

    maqam_SIKA = Maqam(
        name_ar="سيكاه",
        name_en="Sika",
        emotion="sad",
        emotion_ar="حزين",
        usage="Malouf",
        usage_ar="مالوف",
        ajnas_json=json.dumps([
            {
                "name": {"ar": "سيكاه على السيكاه", "en": "Sika on Sika"},
                "notes": {"ar": ["صول", "فا", "مي نصف مخفوضة"],
                          "en": ["G", "F", "E-half-flat"]}
            },
            {
                "name": {"ar": "محير عراق نوا", "en": "Mhayer Iraq Nawa"},
                "notes": {"ar": ["دو", "سي نصف مخفوضة", "لا", "صول"],
                          "en": ["C", "B-half-flat", "A", "G"]}
            }
        ]),
        regions_json=json.dumps(["tunis"]),         
        regions_ar_json=json.dumps(["تونس"]),       
        description_ar=(
            "مقام السيكاه ذو طابع عاطفي تأملي، يُستعمل في المالوف "
            "أمثلة أغاني: املأ واسقيني ياأهيف "
            "(المناطق تقديرية: تونس)"
        ),
        description_en=(
            "Sika is an emotional, contemplative maqam used in Malouf. "
            "Song example: Amla Wasqini Ya Ahif. "
            "(Regions guessed: Tunis)"
        ),
        related_json=json.dumps([]),
        difficulty_index=0.2,
        difficulty_label="beginner",
        difficulty_label_ar="مبتدئ",
        emotion_weights_json=json.dumps({"sad": 0.6, "emotional": 0.4}),
        historical_periods_json=json.dumps(["traditional_malouf"]),
        historical_periods_ar_json=json.dumps(["مالوف تقليدي"]),
        seasonal_usage_json=json.dumps(["no specific seasonal usage"]),
        seasonal_usage_ar_json=json.dumps(["لا يوجد استخدام موسمي محدد"]),
        rarity_level="common",
        rarity_level_ar="شائع",
    )

    # --- NEW MAQAM: الحسين ---
    maqam_AL_HSIN = Maqam(
        name_ar="الحسين",
        name_en="Al Hsin",
        emotion="spiritual",
        emotion_ar="الروحانية والإحساس الصوفي ",
        usage="Malouf,weddings",
        usage_ar="مالوف,أفراح",
        ajnas_json=json.dumps([
            {
                "name": {"ar": "حسين دوكاه", "en": "Hsin Dukah"},
                "notes": {"ar": ["ري نصف مخفوضة", "مي نصف مخفوضة", "فا", "صول"],
                          "en": ["D-half-flat", "E-half-flat", "F", "G"]}
            },
            {
                "name": {"ar": "حسين حسيني", "en": "Hsin Hsini"},
                "notes": {"ar": ["لا", "سي نصف مخفوضة", "دو", "ري"],
                          "en": ["A", "B-half-flat", "C", "D"]}
            }
        ]),
        regions_json=json.dumps(["sahel", "tunis"]),         
        regions_ar_json=json.dumps(["الساحل", "تونس"]),      
        description_ar=(
            "مقام الحسين بطابع حنين روحي عميق مع وقار وإحساس صوفي يُستعمل في المالوف والأفراح "
            "أمثلة أغاني: يا ناس جراتي غرايب، رفقا ملك الحسن "
            "(المناطق تقديرية: الساحل/تونس)"
        ),
        description_en=(
            "Al Hsin has a soulful, spiritual yearning character with dignity; used in Malouf and weddings. "
            "Song examples: Ya Nas Jaratli Gharayeb, Refkan Malek El Hosn. "
            "(Regions guessed: Sahel/Tunis)"
        ),
        related_json=json.dumps([]),
        difficulty_index=0.5,                     
        difficulty_label="intermediate",          
        difficulty_label_ar="متوسط",             
        emotion_weights_json=json.dumps({
            "spiritual": 0.6,
            "nostalgic": 0.4
        }),                                       
        historical_periods_json=json.dumps(["1940s_radio"]),        
        historical_periods_ar_json=json.dumps(["إذاعة الأربعينيات"]),   
        seasonal_usage_json=json.dumps(["no specific seasonal usage"]),
        seasonal_usage_ar_json=json.dumps(["لا يوجد استخدام موسمي محدد"]),
        rarity_level="common",                    
        rarity_level_ar="شائع",                  
    )

    # --- NEW MAQAM: العراق ---
    maqam_AL_IRAQ = Maqam(
        name_ar="العراق",
        name_en="Al Iraq",
        emotion="longing",
        emotion_ar="حب لهفة وشوق",
        usage="Malouf,religious_chant",
        usage_ar="مالوف,انشاد ديني",
        ajnas_json=json.dumps([
            {
                "name": {"ar": "عراق دوكاه", "en": "Iraq Dukah"},
                "notes": {"ar": ["ري", "ري نصف مخفوضة", "مي نصف مخفوضة", "فا", "صول"],
                          "en": ["D", "D-half-flat", "E-half-flat", "F", "G"]}
            },
            {
                "name": {"ar": "حسين حسيني", "en": "Hussein Husseini"},
                "notes": {"ar": ["لا", "سي نصف مخفوضة", "دو", "ري"],
                          "en": ["A", "B-half-flat", "C", "D"]}
            }
        ]),
        regions_json=json.dumps(["tunis", "sahel", "kairouan"]),    
        regions_ar_json=json.dumps(["تونس", "الساحل", "القيروان"]),  
        description_ar=(
            "مقام العراق بطابع حب ولهفة وشوق، يُستعمل في المالوف والإنشاد الديني "
            "أمثلة أغاني: ليعتني بشدالهوى يا دوجة "
            "(المناطق تقديرية: تونس/الساحل/القيروان)"
        ),
        description_en=(
            "Al Iraq conveys longing and yearning; used in Malouf and religious chant. "
            "Song example: Liatni Beshad El Hawa Ya Douja. "
            "(Regions guessed: Tunis/Sahel/Kairouan)"
        ),
        related_json=json.dumps([]),
        difficulty_index=0.5,                     
        difficulty_label="intermediate",          
        difficulty_label_ar="متوسط",             
        emotion_weights_json=json.dumps({
            "longing": 0.7,
            "love": 0.3
        }),                                       
        historical_periods_json=json.dumps(["1960s_radio"]),        
        historical_periods_ar_json=json.dumps(["إذاعة الستينيات"]),   
        seasonal_usage_json=json.dumps(["ramadan_evenings"]),       
        seasonal_usage_ar_json=json.dumps(["سهرات رمضان"]),         
        rarity_level="common",                    
        rarity_level_ar="شائع",                  
    )

    # --- NEW MAQAM: العرضاوي ---
    maqam_AL_ARDHAWI = Maqam(
        name_ar="العرضاوي",
        name_en="Al Ardhawi",
        emotion="joyful",
        emotion_ar="فرح",
        usage="folk_wedding,celebration",
        usage_ar="أفراح شعبي",
        ajnas_json=json.dumps([
            {
                "name": {"ar": "عرضاوي راست", "en": "Ardhawi Rast"},
                "notes": {"ar": ["دو", "ري", "مي نصف مخفوضة", "فا", "صول"],
                          "en": ["C", "D", "E-half-flat", "F", "G"]}
            },
            {
                "name": {"ar": "سعداوي جهاركاه", "en": "Saadawi Jaharkah"},
                "notes": {"ar": ["فا", "صول", "لا", "سي نصف مخفوضة"],
                          "en": ["F", "G", "A", "B-half-flat"]}
            }
        ]),
        regions_json=json.dumps(["sahel", "south"]),         
        regions_ar_json=json.dumps(["الساحل", "الجنوب"]),    
        description_ar=(
            "مقام العرضاوي بطابع فرح شعبي، يُستعمل في الأفراح الشعبية "
            "أمثلة أغاني: نا وجمال فريدة "
            "(المناطق تقديرية: الساحل/الجنوب)"
        ),
        description_en=(
            "Al Ardhawi has a joyful folk character, used in popular weddings. "
            "Song example: Ana We Jamal Farida. "
            "(Regions guessed: Sahel/South)"
        ),
        related_json=json.dumps([]),
        difficulty_index=0.3,                  
        difficulty_label="beginner",           
        difficulty_label_ar="مبتدئ",          
        emotion_weights_json=json.dumps({
            "joyful": 0.8,
            "festive": 0.2
        }),                                    
        historical_periods_json=json.dumps(["folk_festivals"]),
        historical_periods_ar_json=json.dumps(["مهرجانات شعبية"]),
        seasonal_usage_json=json.dumps(["weddings_spring_summer"]),    
        seasonal_usage_ar_json=json.dumps(["أعراس الربيع والصيف"]),    
        rarity_level="locally_rare",           
        rarity_level_ar="نادر محليًا",        
    )


    # Add audio files using MaqamAudio (one-to-many)
    audios = [
        MaqamAudio(maqam=maqam_AL_DHAIL, url="http://localhost:8000/static/audio/ALDHAIL.mp3"),
        MaqamAudio(maqam=maqam_AL_MAYA, url="http://localhost:8000/static/audio/AL_MAYA.mp3"),
        MaqamAudio(maqam=maqam_SIKA, url="http://localhost:8000/static/audio/SIKA.mp3"),
        MaqamAudio(maqam=maqam_AL_HSIN, url="http://localhost:8000/static/audio/AL_HSIN.mp3"),
        MaqamAudio(maqam=maqam_AL_IRAQ, url="http://localhost:8000/static/audio/AL_IRAQ.mp3"),
        MaqamAudio(maqam=maqam_AL_ARDHAWI, url="http://localhost:8000/static/audio/AL_ARDHAOUI.mp3"),
    ]






    db.session.add_all([
        maqam_AL_DHAIL,
        maqam_AL_MAYA,
        maqam_SIKA,
        maqam_AL_HSIN,
        maqam_AL_IRAQ,
        maqam_AL_ARDHAWI,
    ] + audios)
    db.session.commit()
    print("Seeded database with 6 maqamet (Al Dhail, Al Maya, Sika, Al Hsin, Al Iraq, Al Ardhawi).")
