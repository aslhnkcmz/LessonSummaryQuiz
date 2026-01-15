from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Secret Key for Sessions and Flash Messages
    app.config['SECRET_KEY'] = 'seng321-project-secret-key-english'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lesson_ai.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login_page'
    
    # Import Models to ensure they are registered with SQLAlchemy
    from app.models.content import Content
    from app.models.user import User
    from app.models.feedback import Feedback
    from app.models.log import ActivityLog
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Database Creation and Admin Setup
    with app.app_context():
        db.create_all()
        
        # Check if Admin exists, if not, create one
        if not User.query.filter_by(email='admin@admin.com').first():
            try:
                admin = User(email='admin@admin.com', role='Admin')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print(">>> SYSTEM: Default Admin Account Created (admin@admin.com / admin123)")
            except Exception as e:
                print(f">>> SYSTEM: Error creating admin: {e}")
        
    return app