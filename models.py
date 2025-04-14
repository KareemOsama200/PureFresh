from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import os


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(256), nullable=False)
    governorate = db.Column(db.String(64), nullable=False)
    location_lat = db.Column(db.String(20), nullable=True)
    location_lng = db.Column(db.String(20), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(256), nullable=True)
    image_file = db.Column(db.String(256), nullable=True)  # Uploaded image filename
    unit_price = db.Column(db.Float, nullable=False)  # Price for single unit
    carton_price = db.Column(db.Float, nullable=True)  # Price for carton
    carton_quantity = db.Column(db.Integer, nullable=True)  # How many units in a carton
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    cart_items = db.relationship('CartItem', backref='product', lazy=True)


class Discount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage' or 'fixed'
    value = db.Column(db.Float, nullable=False)  # percentage or fixed amount
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_until = db.Column(db.DateTime, nullable=True)
    max_uses = db.Column(db.Integer, nullable=True)
    used_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='discount', lazy=True)


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('cart', uselist=False, lazy=True))
    items = db.relationship('CartItem', backref='cart', cascade='all, delete-orphan', lazy=True)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    is_carton = db.Column(db.Boolean, default=False)  # True if buying carton, False if individual units
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='جاري التحضير')  # 'جاري التحضير', 'تم الشحن', 'في الطريق', 'تم التوصيل', 'مرفوض', 'تم الإلغاء'
    total_amount = db.Column(db.Float, nullable=False)
    shipping_address = db.Column(db.String(256), nullable=False)
    shipping_governorate = db.Column(db.String(64), nullable=False)
    shipping_phone = db.Column(db.String(20), nullable=False)
    location_lat = db.Column(db.String(20), nullable=True)
    location_lng = db.Column(db.String(20), nullable=True)
    discount_id = db.Column(db.Integer, db.ForeignKey('discount.id'), nullable=True)
    discount_amount = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan', lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)  # Store product name at time of order
    price = db.Column(db.Float, nullable=False)  # Store price at time of order
    quantity = db.Column(db.Integer, nullable=False)
    is_carton = db.Column(db.Boolean, default=False)  # True if buying carton, False if individual units
    subtotal = db.Column(db.Float, nullable=False)  # price * quantity
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
