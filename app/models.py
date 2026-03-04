from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date


# =====================================
# 🏢 Company Model
# =====================================

class Company(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    category = db.Column(db.String(100))
    password_hash = db.Column(db.String(200), nullable=False)

    theme = db.Column(db.String(20), default="default")

    enable_2fa = db.Column(db.Boolean, default=False)
    ai_alerts = db.Column(db.Boolean, default=False)
    auto_block = db.Column(db.Boolean, default=False)

    email_alerts = db.Column(db.Boolean, default=True)
    sms_alerts = db.Column(db.Boolean, default=True)

    daily_backup = db.Column(db.Boolean, default=False)

    # 🔥 Relationship

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)


# =====================================
# 📦 Product Model (OPTIONAL - if not using, you can remove fully)
# =====================================

class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100))

    company_id = db.Column(
        db.Integer,
        db.ForeignKey('company.id'),
        nullable=False
    )

    # ❌ NO relationship to ProductCode
    # because we removed product_id from ProductCode


# =====================================
# 🔐 ProductCode Model
# =====================================

class ProductCode(db.Model):
    __tablename__ = "product_code"

    id = db.Column(db.Integer, primary_key=True)

    product_code = db.Column(db.String(50), unique=True, nullable=False)

    manufacturing_date = db.Column(db.DateTime)
    expiry_date = db.Column(db.DateTime)

    lot_number = db.Column(db.String(100))
    serial_number = db.Column(db.String(100))

    scan_count = db.Column(db.Integer, default=0)
    is_deleted = db.Column(db.Boolean, default=False)

    # 🔥 SECURITY FIELDS
    is_flagged = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    risk_score = db.Column(db.Integer, default=0)

    last_scanned = db.Column(db.Date)
    last_scanned_ip = db.Column(db.String(100))

    company_id = db.Column(
        db.Integer,
        db.ForeignKey('company.id'),
        nullable=False
    )