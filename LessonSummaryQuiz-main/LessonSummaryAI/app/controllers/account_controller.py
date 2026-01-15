from app.services.auth_service import AuthService
from flask_login import login_user, logout_user

class AccountController:
    def __init__(self):
        self.auth_service = AuthService()

    def login(self, email, password):
        # Sequence Diagram 6: authenticate
        user = self.auth_service.verify_credentials(email, password)
        if user:
            login_user(user)
            return True
        return False

    def register(self, email, password):
        success, message = self.auth_service.register_user(email, password)
        return success, message

    def logout(self):
        logout_user()