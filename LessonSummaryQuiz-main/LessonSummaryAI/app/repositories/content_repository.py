from app.models.content import Content
from app import db
import json

class ContentRepository:
    def save_content(self, text, summary, length, quiz_data):
        
        new_content = Content(
            original_text=text,
            summary_text=summary,
            length_pref=length,
            quiz_data_json=json.dumps(quiz_data)
        )
        db.session.add(new_content)
        db.session.commit()
        return new_content.id

    def get_content_by_id(self, content_id):
        
        return Content.query.get(content_id)
        
    def get_all_contents(self):
       
        return Content.query.order_by(Content.created_at.desc()).all()