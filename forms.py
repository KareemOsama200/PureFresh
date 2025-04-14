from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FloatField, IntegerField, SelectField, HiddenField, DateTimeField, DecimalField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional, NumberRange
from models import User


class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(message='يرجى إدخال اسم المستخدم')])
    password = PasswordField('كلمة المرور', validators=[DataRequired(message='يرجى إدخال كلمة المرور')])
    remember_me = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')


class RegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(message='يرجى إدخال اسم المستخدم'), Length(min=4, max=64, message='اسم المستخدم يجب أن يكون بين 4 و 64 حرفًا')])
    full_name = StringField('الاسم بالكامل', validators=[DataRequired(message='يرجى إدخال الاسم بالكامل')])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(message='يرجى إدخال البريد الإلكتروني'), Email(message='بريد إلكتروني غير صالح')])
    phone = StringField('رقم الهاتف', validators=[DataRequired(message='يرجى إدخال رقم الهاتف')])
    address = TextAreaField('العنوان بالتفصيل', validators=[DataRequired(message='يرجى إدخال العنوان بالتفصيل')])
    governorate = SelectField('المحافظة', choices=[
        ('القاهرة', 'القاهرة'),
        ('الجيزة', 'الجيزة'),
        ('الإسكندرية', 'الإسكندرية'),
        ('الدقهلية', 'الدقهلية'),
        ('البحيرة', 'البحيرة'),
        ('الشرقية', 'الشرقية'),
        ('القليوبية', 'القليوبية'),
        ('كفر الشيخ', 'كفر الشيخ'),
        ('الغربية', 'الغربية'),
        ('المنوفية', 'المنوفية'),
        ('المنيا', 'المنيا'),
        ('أسيوط', 'أسيوط'),
        ('سوهاج', 'سوهاج'),
        ('الفيوم', 'الفيوم'),
        ('بني سويف', 'بني سويف'),
        ('أسوان', 'أسوان'),
        ('الأقصر', 'الأقصر'),
        ('قنا', 'قنا'),
        ('دمياط', 'دمياط'),
        ('الإسماعيلية', 'الإسماعيلية'),
        ('بورسعيد', 'بورسعيد'),
        ('السويس', 'السويس'),
        ('مطروح', 'مطروح'),
        ('شمال سيناء', 'شمال سيناء'),
        ('جنوب سيناء', 'جنوب سيناء'),
        ('البحر الأحمر', 'البحر الأحمر'),
        ('الوادي الجديد', 'الوادي الجديد')
    ], validators=[DataRequired(message='يرجى اختيار المحافظة')])
    location_lat = HiddenField('خط العرض')
    location_lng = HiddenField('خط الطول')
    password = PasswordField('كلمة المرور', validators=[DataRequired(message='يرجى إدخال كلمة المرور'), Length(min=6, message='كلمة المرور يجب أن تكون 6 أحرف على الأقل')])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(message='يرجى تأكيد كلمة المرور'), EqualTo('password', message='كلمة المرور غير متطابقة')])
    submit = SubmitField('تسجيل')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('اسم المستخدم مُستخدم بالفعل. يرجى اختيار اسم آخر.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('البريد الإلكتروني مُستخدم بالفعل. يرجى استخدام بريد آخر.')


class ProductForm(FlaskForm):
    name = StringField('اسم المنتج', validators=[DataRequired(message='يرجى إدخال اسم المنتج')])
    description = TextAreaField('وصف المنتج', validators=[DataRequired(message='يرجى إدخال وصف المنتج')])
    image = FileField('صورة المنتج', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'يُسمح فقط بملفات الصور (jpg, jpeg, png, webp)!')
    ])
    image_url = StringField('رابط الصورة (اختياري)', validators=[Optional()])
    unit_price = FloatField('سعر الوحدة (جنيه)', validators=[DataRequired(message='يرجى إدخال سعر الوحدة')])
    carton_price = FloatField('سعر الكرتونة (جنيه)', validators=[Optional()])
    carton_quantity = IntegerField('عدد الوحدات في الكرتونة', validators=[Optional()])
    submit = SubmitField('حفظ')


class DiscountForm(FlaskForm):
    code = StringField('كود الخصم', validators=[DataRequired(message='يرجى إدخال كود الخصم')])
    discount_type = SelectField('نوع الخصم', choices=[('percentage', 'نسبة مئوية'), ('fixed', 'مبلغ ثابت')], validators=[DataRequired(message='يرجى اختيار نوع الخصم')])
    value = FloatField('قيمة الخصم', validators=[DataRequired(message='يرجى إدخال قيمة الخصم'), NumberRange(min=0, message='يجب أن تكون قيمة الخصم موجبة')])
    valid_from = StringField('صالح من تاريخ', validators=[DataRequired(message='يرجى إدخال تاريخ بداية الصلاحية')])
    valid_until = StringField('صالح حتى تاريخ', validators=[Optional()])
    max_uses = IntegerField('الحد الأقصى للاستخدام', validators=[Optional()])
    is_active = BooleanField('نشط', default=True)
    submit = SubmitField('حفظ')


class CartItemForm(FlaskForm):
    product_id = HiddenField('رقم المنتج', validators=[DataRequired(message='يجب تحديد المنتج')])
    quantity = IntegerField('الكمية', validators=[DataRequired(message='يرجى إدخال الكمية'), NumberRange(min=1, message='يجب أن تكون الكمية 1 على الأقل')])
    is_carton = BooleanField('كرتونة')
    submit = SubmitField('إضافة إلى السلة')


class CheckoutForm(FlaskForm):
    shipping_address = TextAreaField('عنوان التوصيل', validators=[DataRequired(message='يرجى إدخال عنوان التوصيل')])
    shipping_governorate = SelectField('المحافظة', choices=[
        ('القاهرة', 'القاهرة'),
        ('الجيزة', 'الجيزة'),
        ('الإسكندرية', 'الإسكندرية'),
        ('الدقهلية', 'الدقهلية'),
        ('البحيرة', 'البحيرة'),
        ('الشرقية', 'الشرقية'),
        ('القليوبية', 'القليوبية'),
        ('كفر الشيخ', 'كفر الشيخ'),
        ('الغربية', 'الغربية'),
        ('المنوفية', 'المنوفية'),
        ('المنيا', 'المنيا'),
        ('أسيوط', 'أسيوط'),
        ('سوهاج', 'سوهاج'),
        ('الفيوم', 'الفيوم'),
        ('بني سويف', 'بني سويف'),
        ('أسوان', 'أسوان'),
        ('الأقصر', 'الأقصر'),
        ('قنا', 'قنا'),
        ('دمياط', 'دمياط'),
        ('الإسماعيلية', 'الإسماعيلية'),
        ('بورسعيد', 'بورسعيد'),
        ('السويس', 'السويس'),
        ('مطروح', 'مطروح'),
        ('شمال سيناء', 'شمال سيناء'),
        ('جنوب سيناء', 'جنوب سيناء'),
        ('البحر الأحمر', 'البحر الأحمر'),
        ('الوادي الجديد', 'الوادي الجديد')
    ], validators=[DataRequired(message='يرجى اختيار المحافظة')])
    shipping_phone = StringField('رقم الهاتف للتوصيل', validators=[DataRequired(message='يرجى إدخال رقم الهاتف للتوصيل')])
    location_lat = HiddenField('خط العرض')
    location_lng = HiddenField('خط الطول')
    discount_code = StringField('كود الخصم', validators=[Optional()])
    submit = SubmitField('إتمام الطلب')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('كلمة المرور الحالية', validators=[DataRequired(message='يرجى إدخال كلمة المرور الحالية')])
    new_password = PasswordField('كلمة المرور الجديدة', validators=[DataRequired(message='يرجى إدخال كلمة المرور الجديدة'), Length(min=6, message='كلمة المرور يجب أن تكون 6 أحرف على الأقل')])
    confirm_password = PasswordField('تأكيد كلمة المرور الجديدة', validators=[DataRequired(message='يرجى تأكيد كلمة المرور الجديدة'), EqualTo('new_password', message='كلمة المرور غير متطابقة')])
    submit = SubmitField('تغيير كلمة المرور')


class LogoUploadForm(FlaskForm):
    logo = FileField('اللوجو', validators=[
        FileRequired(message='يرجى اختيار ملف اللوجو'),
        FileAllowed(['jpg', 'jpeg', 'png', 'svg'], 'يُسمح فقط بملفات الصور (jpg, jpeg, png, svg)!')
    ])
    submit = SubmitField('تحديث اللوجو')


class UpdateOrderStatusForm(FlaskForm):
    status = SelectField('حالة الطلب', choices=[
        ('جاري التحضير', 'جاري التحضير ✅'),
        ('تم الشحن', 'تم الشحن 🚚'),
        ('في الطريق', 'في الطريق 🛵'),
        ('تم التوصيل', 'تم التوصيل 📦'),
        ('مرفوض', 'مرفوض ❌'),
        ('تم الإلغاء', 'تم الإلغاء')
    ], validators=[DataRequired(message='يرجى اختيار حالة الطلب')])
    submit = SubmitField('تحديث')
