from app import db
from app.models.content import Content
from app.services.content_service import ContentService
from app.services.file_service import FileService # Yeni eklendi
from flask_login import current_user
import json

class ContentController:
    def generate_summary(self, text, file, length_pref, language='English'):
        # Eğer dosya varsa, önce dosyadan metni çıkar
        if file and file.filename != '':
            extracted_text = FileService().extract_text(file)
            if extracted_text and len(extracted_text) > 10:
                text = extracted_text # Dosya metnini kullan
        
        # Eğer hala metin yoksa işlem yapma
        if not text or len(text.strip()) < 10:
            return None

        # Buradan sonrası aynı (Özetle, Quiz yap, Kaydet)
        service = ContentService()
        result_data = service.process_content(text, length_pref, language)
        
        new_content = Content(
            user_id=current_user.id,
            original_text=text, # Dosyadan çıkan metni kaydediyoruz
            summary_text=result_data['summary'],
            quiz_data_json=json.dumps(result_data['quiz']),
            length_pref=length_pref
        )
        
        db.session.add(new_content)
        db.session.commit()
        
        result_data['id'] = new_content.id
        return result_data

    def get_history(self):
        return Content.query.filter_by(user_id=current_user.id).order_by(Content.created_at.desc()).all()

    def get_content(self, content_id):
        return Content.query.get(content_id)