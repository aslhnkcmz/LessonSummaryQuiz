from gtts import gTTS
from io import BytesIO

class AudioService:
    def generate_audio(self, text, lang='en'):
        # Basit dil algılama (Varsayılan İngilizce)
        # Eğer metinde Türkçe karakterler çoksa Türkçe oku
        turkish_chars = ['ı', 'ğ', 'ü', 'ş', 'ö', 'ç', 'İ', 'Ğ', 'Ü', 'Ş', 'Ö', 'Ç']
        count = sum(1 for char in text if char in turkish_chars)
        
        selected_lang = 'tr' if count > 2 else 'en'
        
        try:
            tts = gTTS(text=text, lang=selected_lang, slow=False)
            mp3_fp = BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            return mp3_fp
        except Exception as e:
            print(f"TTS Error: {e}")
            return None