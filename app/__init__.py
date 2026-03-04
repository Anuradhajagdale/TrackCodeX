from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from app.models import Company
    return Company.query.get(int(user_id))


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "your_secret_key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trackcodex.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # ✅ Just import models file (important)
    from app import models

    with app.app_context():
        db.create_all()

    from app.auth import auth
    app.register_blueprint(auth)

    from flask_login import current_user

    @app.context_processor
    def inject_company():
        if current_user.is_authenticated:
            return dict(company=current_user)
        return dict(company=None)

    return app