from flask import render_template, url_for, flash, redirect, request, jsonify, abort, send_from_directory, g
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import logging
import uuid

from app import app, db
from models import User, Product, Discount, Cart, CartItem, Order, OrderItem
from forms import (LoginForm, RegistrationForm, ProductForm, DiscountForm, CartItemForm, 
                   CheckoutForm, ChangePasswordForm, UpdateOrderStatusForm, LogoUploadForm)


# Set up global variables that will be available in all templates
@app.before_request
def setup_globals():
    # Check for logo files
    logo_path = None
    logo_folder = app.config['UPLOAD_FOLDER_LOGO']
    if os.path.exists(logo_folder):
        logo_files = [f for f in os.listdir(logo_folder) 
                     if f.startswith('logo') and 
                     (f.endswith('.jpg') or f.endswith('.jpeg') or 
                      f.endswith('.png') or f.endswith('.svg'))]
        if logo_files:
            logo_path = 'uploads/logo/' + logo_files[0]
    
    # Add the logo path to the global context
    g.logo_path = logo_path


@app.route('/')
def index():
    products = Product.query.order_by(Product.created_at.desc()).limit(4).all()
    return render_template('index.html', products=products)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            
            # If user is admin, redirect to admin dashboard
            if user.is_admin:
                return redirect(next_page or url_for('admin_dashboard'))
            
            return redirect(next_page or url_for('index'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            full_name=form.full_name.data,
            phone=form.phone.data,
            address=form.address.data,
            governorate=form.governorate.data,
            location_lat=form.location_lat.data,
            location_lng=form.location_lng.data
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create an empty cart for the user
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.commit()
        
        flash('تم إنشاء الحساب بنجاح! يمكنك تسجيل الدخول الآن.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)


@app.route('/products')
def product_list():
    products = Product.query.all()
    return render_template('product_list.html', products=products)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    form = CartItemForm(product_id=product.id)
    return render_template('product_detail.html', product=product, form=form)


@app.route('/cart')
@login_required
def view_cart():
    # Get or create cart for the user
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    
    items = CartItem.query.filter_by(cart_id=cart.id).all()
    total = 0
    
    for item in items:
        if item.is_carton and item.product.carton_price:
            total += item.product.carton_price * item.quantity
        else:
            total += item.product.unit_price * item.quantity
    
    return render_template('cart.html', items=items, total=total)


@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    form = CartItemForm()
    if form.validate_on_submit():
        product_id = form.product_id.data
        quantity = form.quantity.data
        is_carton = form.is_carton.data
        
        # Get or create cart for the user
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if not cart:
            cart = Cart(user_id=current_user.id)
            db.session.add(cart)
            db.session.commit()
        
        # Check if product exists in cart
        cart_item = CartItem.query.filter_by(
            cart_id=cart.id, 
            product_id=product_id, 
            is_carton=is_carton
        ).first()
        
        if cart_item:
            # Update existing item
            cart_item.quantity += quantity
        else:
            # Add new item
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                is_carton=is_carton
            )
            db.session.add(cart_item)
        
        db.session.commit()
        flash('تمت إضافة المنتج إلى السلة', 'success')
        
        # Redirect back to the referring page
        return redirect(request.referrer or url_for('product_list'))
    
    # If form validation fails
    flash('حدث خطأ أثناء إضافة المنتج إلى السلة', 'danger')
    return redirect(request.referrer or url_for('product_list'))


@app.route('/update_cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    quantity = int(request.form.get('quantity', 1))
    
    # Make sure the cart item belongs to the current user
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        flash('لم يتم العثور على السلة', 'danger')
        return redirect(url_for('view_cart'))
    
    cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not cart_item:
        flash('لم يتم العثور على المنتج في السلة', 'danger')
        return redirect(url_for('view_cart'))
    
    if quantity <= 0:
        # Remove item if quantity is 0 or less
        db.session.delete(cart_item)
        flash('تم حذف المنتج من السلة', 'success')
    else:
        # Update quantity
        cart_item.quantity = quantity
        flash('تم تحديث الكمية', 'success')
    
    db.session.commit()
    return redirect(url_for('view_cart'))


@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    # Make sure the cart item belongs to the current user
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        flash('لم يتم العثور على السلة', 'danger')
        return redirect(url_for('view_cart'))
    
    cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not cart_item:
        flash('لم يتم العثور على المنتج في السلة', 'danger')
        return redirect(url_for('view_cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    
    flash('تم حذف المنتج من السلة', 'success')
    return redirect(url_for('view_cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    # Get user's cart
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        flash('سلة التسوق فارغة', 'info')
        return redirect(url_for('product_list'))
    
    items = CartItem.query.filter_by(cart_id=cart.id).all()
    if not items:
        flash('سلة التسوق فارغة', 'info')
        return redirect(url_for('product_list'))
    
    # Calculate total
    total = 0
    for item in items:
        if item.is_carton and item.product.carton_price:
            total += item.product.carton_price * item.quantity
        else:
            total += item.product.unit_price * item.quantity
    
    # Initialize form with user's shipping details
    form = CheckoutForm(
        shipping_address=current_user.address,
        shipping_governorate=current_user.governorate,
        shipping_phone=current_user.phone,
        location_lat=current_user.location_lat,
        location_lng=current_user.location_lng
    )
    
    if form.validate_on_submit():
        # Check for discount code
        discount_amount = 0
        discount = None
        
        if form.discount_code.data:
            discount = Discount.query.filter_by(code=form.discount_code.data, is_active=True).first()
            
            if discount:
                # Check if discount is still valid
                now = datetime.utcnow()
                if (discount.valid_from <= now and 
                    (not discount.valid_until or discount.valid_until >= now) and
                    (not discount.max_uses or discount.used_count < discount.max_uses)):
                    
                    # Apply discount
                    if discount.discount_type == 'percentage':
                        discount_amount = total * (discount.value / 100)
                    else:  # fixed amount
                        discount_amount = discount.value
                    
                    if discount_amount > total:
                        discount_amount = total
                    
                    # Increment used count
                    discount.used_count += 1
                else:
                    discount = None
                    flash('كود الخصم غير صالح أو منتهي الصلاحية', 'warning')
            else:
                flash('كود الخصم غير صحيح', 'warning')
        
        # Create order
        order = Order(
            user_id=current_user.id,
            status='جاري التحضير',
            total_amount=total - discount_amount,
            shipping_address=form.shipping_address.data,
            shipping_governorate=form.shipping_governorate.data,
            shipping_phone=form.shipping_phone.data,
            location_lat=form.location_lat.data,
            location_lng=form.location_lng.data,
            discount_id=discount.id if discount else None,
            discount_amount=discount_amount
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Add order items
        for item in items:
            product = item.product
            price = product.carton_price if item.is_carton and product.carton_price else product.unit_price
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                name=product.name,
                price=price,
                quantity=item.quantity,
                is_carton=item.is_carton,
                subtotal=price * item.quantity
            )
            
            db.session.add(order_item)
        
        # Clear cart
        for item in items:
            db.session.delete(item)
        
        db.session.commit()
        
        flash('تم تقديم طلبك بنجاح!', 'success')
        return redirect(url_for('order_tracking', order_id=order.id))
    
    return render_template('checkout.html', form=form, items=items, total=total)


@app.route('/orders')
@login_required
def order_list():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('order_tracking.html', orders=orders)


@app.route('/order/<int:order_id>')
@login_required
def order_tracking(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Make sure the order belongs to the current user or the user is an admin
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى هذا الطلب', 'danger')
        return redirect(url_for('order_list'))
    
    return render_template('order_tracking.html', order=order)


# Admin routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى لوحة التحكم', 'danger')
        return redirect(url_for('index'))
    
    # Get counts for dashboard
    products_count = Product.query.count()
    orders_count = Order.query.count()
    users_count = User.query.filter_by(is_admin=False).count()
    pending_orders = Order.query.filter_by(status='جاري التحضير').count()
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                           products_count=products_count,
                           orders_count=orders_count,
                           users_count=users_count,
                           pending_orders=pending_orders,
                           recent_orders=recent_orders)


@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى لوحة التحكم', 'danger')
        return redirect(url_for('index'))
    
    products = Product.query.all()
    return render_template('admin/products.html', products=products)


@app.route('/admin/product/add', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى لوحة التحكم', 'danger')
        return redirect(url_for('index'))
    
    form = ProductForm()
    if form.validate_on_submit():
        # Create product without image first
        product = Product(
            name=form.name.data,
            description=form.description.data,
            image_url=form.image_url.data if not form.image.data else None,
            unit_price=form.unit_price.data,
            carton_price=form.carton_price.data,
            carton_quantity=form.carton_quantity.data
        )
        
        db.session.add(product)
        db.session.commit()
        
        # Handle image upload if provided
        if form.image.data:
            # Check if uploads directory exists, create if not
            upload_folder = app.config['UPLOAD_FOLDER_PRODUCTS']
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generate unique filename
            file_ext = os.path.splitext(form.image.data.filename)[1]
            filename = f"product_{product.id}_{uuid.uuid4().hex}{file_ext}"
            
            # Save file
            form.image.data.save(os.path.join(upload_folder, filename))
            
            # Update product with image filename
            product.image_file = filename
            db.session.commit()
        
        flash('تم إضافة المنتج بنجاح', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/add_product.html', form=form)


@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى لوحة التحكم', 'danger')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        
        # Only update image_url if no new image uploaded and url is provided
        if not form.image.data and form.image_url.data:
            product.image_url = form.image_url.data
        elif form.image.data:
            # If a new image is uploaded, clear the URL
            product.image_url = None
        
        product.unit_price = form.unit_price.data
        product.carton_price = form.carton_price.data
        product.carton_quantity = form.carton_quantity.data
        product.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Handle image upload if provided
        if form.image.data:
            # Check if uploads directory exists, create if not
            upload_folder = app.config['UPLOAD_FOLDER_PRODUCTS']
            os.makedirs(upload_folder, exist_ok=True)
            
            # Delete old image if exists
            if product.image_file:
                old_file_path = os.path.join(upload_folder, product.image_file)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            # Generate unique filename
            file_ext = os.path.splitext(form.image.data.filename)[1]
            filename = f"product_{product.id}_{uuid.uuid4().hex}{file_ext}"
            
            # Save file
            form.image.data.save(os.path.join(upload_folder, filename))
            
            # Update product with image filename
            product.image_file = filename
            db.session.commit()
        
        flash('تم تحديث المنتج بنجاح', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/edit_product.html', form=form, product=product)


@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@login_required
def admin_delete_product(product_id):
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى لوحة التحكم', 'danger')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    db.session.delete(product)
    db.session.commit()
    
    flash('تم حذف المنتج بنجاح', 'success')
    return redirect(url_for('admin_products'))


@app.route('/admin/discounts')
@login_required
def admin_discounts():
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى لوحة التحكم', 'danger')
        return redirect(url_for('index'))
    
    discounts = Discount.query.all()
    return render_template('admin/discounts.html', discounts=discounts)


@app.route('/admin/discount/add', methods=['GET', 'POST'])
@login_required
def admin_add_discount():
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى لوحة التحكم', 'danger')
        return redirect(url_for('index'))
    
    form = DiscountForm()
    if form.validate_on_submit():
        try:
            valid_from = datetime.strptime(form.valid_from.data, '%Y-%m-%d')
            valid_until = datetime.strptime(form.valid_until.data, '%Y-%m-%d') if form.valid_until.data else None
            
            discount = Discount(
                code=form.code.data,
                discount_type=form.discount_type.data,
                value=form.value.data,
                valid_from=valid_from,
                valid_until=valid_until,
                max_uses=form.max_uses.data,
                is_active=form.is_active.data
            )
            
            db.session.add(discount)
            db.session.commit()
            
            flash('تم إضافة كود الخصم بنجاح', 'success')
            return redirect(url_for('admin_discounts'))
        except ValueError:
            flash('صيغة التاريخ غير صحيحة. يرجى استخدام YYYY-MM-DD', 'danger')
    
    return render_template('admin/discounts.html', form=form, action='add')


@app.route('/admin/discount/edit/<int:discount_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_discount(discount_id):
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى لوحة التحكم', 'danger')
        return redirect(url_for('index'))
    
    discount = Discount.query.get_or_404(discount_id)
    
    form = DiscountForm(obj=discount)
    if form.validate_on_submit():
        try:
            valid_from = datetime.strptime(form.valid_from.data, '%Y-%m-%d')
            valid_until = datetime.strptime(form.valid_until.data, '%Y-%m-%d') if form.valid_until.data else None
            
            discount.code = form.code.data
            discount.discount_type = form.discount_type.data
            discount.value = form.value.data
            discount.valid_from = valid_from
            discount.valid_until = valid_until
            discount.max_uses = form.max_uses.data
            discount.is_active = form.is_active.data
            
            db.session.commit()
            
            flash('تم تحديث كود الخصم بنجاح', 'success')
            return redirect(url_for('admin_discounts'))
        except ValueError:
            flash('صيغة التاريخ غير صحيحة. يرجى استخدام YYYY-MM-DD', 'danger')
    else:
        # Format dates for form display
        if discount.valid_from:
            form.valid_from.data = discount.valid_from.strftime('%Y-%m-%d')
        if discount.valid_until:
            form.valid_until.data = discount.valid_until.strftime('%Y-%m-%d')
    
    return render_template('admin/discounts.html', form=form, discount=discount, action='edit')


@app.route('/admin/discount/delete/<int:discount_id>', methods=['POST'])
@login_required
def admin_delete_discount(discount_id):
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى لوحة التحكم', 'danger')
        return redirect(url_for('index'))
    
    discount = Discount.query.get_or_404(discount_id)
    
    db.session.delete(discount)
    db.session.commit()
    
    flash('تم حذف كود الخصم بنجاح', 'success')
    return redirect(url_for('admin_discounts'))


@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى لوحة التحكم', 'danger')
        return redirect(url_for('index'))
    
    status_filter = request.args.get('status', '')
    
    # Filter orders by status if provided
    if status_filter:
        orders = Order.query.filter_by(status=status_filter).order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.order_by(Order.created_at.desc()).all()
    
    return render_template('admin/orders.html', orders=orders, current_filter=status_filter)


@app.route('/admin/order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def admin_order_detail(order_id):
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى لوحة التحكم', 'danger')
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    customer = User.query.get(order.user_id)
    
    form = UpdateOrderStatusForm(status=order.status)
    
    if form.validate_on_submit():
        order.status = form.status.data
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('تم تحديث حالة الطلب بنجاح', 'success')
        return redirect(url_for('admin_order_detail', order_id=order.id))
    
    return render_template('admin/orders.html', order=order, customer=customer, form=form, action='detail')


@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى لوحة التحكم', 'danger')
        return redirect(url_for('index'))
    
    password_form = ChangePasswordForm()
    logo_form = LogoUploadForm()
    
    # Password change handling
    if password_form.submit.data and password_form.validate():
        # Check if current password is correct
        if check_password_hash(current_user.password_hash, password_form.current_password.data):
            # Update password
            current_user.password_hash = generate_password_hash(password_form.new_password.data)
            db.session.commit()
            
            flash('تم تغيير كلمة المرور بنجاح', 'success')
            return redirect(url_for('admin_settings'))
        else:
            flash('كلمة المرور الحالية غير صحيحة', 'danger')
    
    # Logo upload handling
    if logo_form.submit.data and logo_form.validate():
        # Check if uploads directory exists, create if not
        logo_folder = app.config['UPLOAD_FOLDER_LOGO']
        os.makedirs(logo_folder, exist_ok=True)
        
        # Delete existing logo files
        for filename in os.listdir(logo_folder):
            if filename.startswith("logo") and (filename.endswith('.jpg') or 
                                               filename.endswith('.jpeg') or 
                                               filename.endswith('.png') or 
                                               filename.endswith('.svg')):
                os.remove(os.path.join(logo_folder, filename))
        
        # Save the new logo
        logo_file = logo_form.logo.data
        # Generate a filename with original extension but make it logo.ext
        filename = secure_filename("logo" + os.path.splitext(logo_file.filename)[1])
        logo_file.save(os.path.join(logo_folder, filename))
        
        flash('تم تحديث شعار الموقع بنجاح', 'success')
        return redirect(url_for('admin_settings'))
    
    # Check if logo exists and provide a variable for the template
    logo_path = None
    logo_folder = app.config['UPLOAD_FOLDER_LOGO']
    if os.path.exists(logo_folder):
        for filename in os.listdir(logo_folder):
            if filename.startswith("logo") and (filename.endswith('.jpg') or 
                                              filename.endswith('.jpeg') or 
                                              filename.endswith('.png') or 
                                              filename.endswith('.svg')):
                logo_path = os.path.join('uploads/logo', filename)
                break
    
    return render_template('admin/settings.html', 
                          password_form=password_form, 
                          logo_form=logo_form,
                          logo_path=logo_path)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
