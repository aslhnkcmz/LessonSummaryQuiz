from app import db
from datetime import datetime
import json

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # --- İŞTE EKSİK OLAN VE HATAYI ÇÖZEN SATIR ---
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # ---------------------------------------------
    
    original_text = db.Column(db.Text, nullable=False)
    summary_text = db.Column(db.Text, nullable=False)
    quiz_data_json = db.Column(db.Text, nullable=False)
    length_pref = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_quiz_data(self):
        try:
            return json.loads(self.quiz_data_json)
        except:
            return []