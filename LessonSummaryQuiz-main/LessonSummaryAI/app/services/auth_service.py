from app.models.user import User
from app import db

class AuthService:
    def register_user(self, email, password):
        # Kullanıcı var mı kontrol et
        if User.query.filter_by(email=email).first():
            return False, "User already exists"
        
        new_user = User(email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return True, "User created"

    def verify_credentials(self, email, password):
        # Sequence Diagram 6: verifyCredentials
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user
        return None