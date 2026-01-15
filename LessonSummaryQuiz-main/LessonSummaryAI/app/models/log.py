from app import db

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(100)) # e.g. "Login", "Generated Content"
    details = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())