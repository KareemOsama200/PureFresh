import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

# قاعدة البيانات الأساسية (Base)
class Base(DeclarativeBase):
    pass

# إعداد SQLAlchemy
db = SQLAlchemy(model_class=Base)

# إنشاء التطبيق
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# تكوين قاعدة البيانات (يتم أخذ الرابط من متغير البيئة DATABASE_URL)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///purefresh.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# إعدادات مجلدات التحميل
app.config["UPLOAD_FOLDER_PRODUCTS"] = "static/uploads/products"
app.config["UPLOAD_FOLDER_LOGO"] = "static/uploads/logo"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

# إعدادات مدير تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'

# تهيئة التطبيق مع SQLAlchemy
db.init_app(app)

with app.app_context():
    # التأكد من استيراد الموديلات هنا لكي يتم إنشاء الجداول
    import models  # noqa: F401

    db.create_all()

    # تهيئة المستخدم الإداري إذا لم يكن موجودًا
    from models import User
    
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@purefresh.com',
            password_hash=generate_password_hash('admin123'),
            full_name='مدير النظام',
            phone='01000000000',
            address='عنوان الإدارة',
            governorate='القاهرة',
            location_lat="30.0444",
            location_lng="31.2357",
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

# استيراد المسارات بعد تهيئة التطبيق لتجنب الاستيراد الدائري
from routes import *
