from flask import render_template, request, redirect, url_for, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Company, Product, ProductCode
from . import auth
import random
import string
from datetime import date
from io import BytesIO
import zipfile
import qrcode


# =====================================================
# GENERATE CODE FUNCTION
# =====================================================
def generate_code(code_type, length):

    if code_type == "numeric":
        characters = string.digits
    elif code_type == "alphabet":
        characters = string.ascii_uppercase
    else:
        characters = string.ascii_uppercase + string.digits

    return ''.join(random.choices(characters, k=length))


# =====================================================
# LOGIN
# =====================================================
@auth.route('/', methods=['GET', 'POST'])
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = Company.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('auth.dashboard'))
        else:
            flash("Invalid Email or Password", "danger")

    return render_template("login.html")


# =====================================================
# REGISTER
# =====================================================
@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("company_name")   # 🔥 IMPORTANT CHANGE
        email = request.form.get("email")
        category = request.form.get("category")
        password = request.form.get("password")

        if not name or not email or not password:
            flash("All fields are required", "danger")
            return redirect(url_for("auth.register"))

        # Check duplicate email
        existing_user = Company.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered", "danger")
            return redirect(url_for("auth.register"))

        company = Company(
            name=name,
            email=email,
            category=category
        )

        company.set_password(password)

        db.session.add(company)
        db.session.commit()

        flash("Registration Successful!", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")
# =====================================================
# LOGOUT
# =====================================================
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))



@auth.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():

    from datetime import datetime, date
    from sqlalchemy import func
    import random
    import string

    def generate_code(code_type, length):
        if code_type == "numeric":
            chars = string.digits
        elif code_type == "alphabet":
            chars = string.ascii_uppercase
        else:
            chars = string.ascii_uppercase + string.digits

        return ''.join(random.choices(chars, k=length))

    # ==============================
    # 🔹 CODE GENERATION SECTION
    # ==============================
    if request.method == "POST":

        try:
            quantity = int(request.form.get("quantity"))
            length = int(request.form.get("length"))
            code_type = request.form.get("code_type")

            mfg_date = datetime.strptime(request.form.get("mfg_date"), "%Y-%m-%d")
            exp_date = datetime.strptime(request.form.get("exp_date"), "%Y-%m-%d")

            lot_number = request.form.get("lot_number")
            serial_number = request.form.get("serial_number")

            if quantity > 50000:
                flash("Maximum 50,000 codes allowed!", "danger")
                return redirect(url_for("auth.dashboard"))

            new_codes = []
            generated_set = set()

            while len(generated_set) < quantity:
                generated_set.add(generate_code(code_type, length))

            for code_value in generated_set:
                new_codes.append(
                    ProductCode(
                        product_code=code_value,
                        manufacturing_date=mfg_date,
                        expiry_date=exp_date,
                        lot_number=lot_number,
                        serial_number=serial_number,
                        company_id=current_user.id
                    )
                )

            db.session.bulk_save_objects(new_codes)
            db.session.commit()

            flash(f"{quantity} Codes Generated Successfully!", "success")
            return redirect(url_for("auth.dashboard"))

        except Exception as e:
            db.session.rollback()
            print("ERROR:", e)
            flash("Error while generating codes!", "danger")
            return redirect(url_for("auth.dashboard"))

    # ==============================
    # 🔹 DASHBOARD STATS SECTION
    # ==============================

    # ✅ Total Codes
    total_codes = ProductCode.query.filter_by(
        company_id=current_user.id,
        is_deleted=False
    ).count()

    # ✅ Active Codes (not deleted & not blocked)
    active_codes = ProductCode.query.filter_by(
        company_id=current_user.id,
        is_deleted=False,
        is_blocked=False
    ).count()

    # ✅ Scans Today
    today = date.today()
    scans_today = ProductCode.query.filter_by(
        company_id=current_user.id,
        last_scanned=today
    ).count()

    # ✅ Total Scans (sum of all scan_count)
    total_scans = db.session.query(
        func.sum(ProductCode.scan_count)
    ).filter_by(
        company_id=current_user.id
    ).scalar() or 0

    # ✅ Recent Codes
    recent_codes = ProductCode.query.filter_by(
        company_id=current_user.id
    ).order_by(ProductCode.id.desc()).limit(10).all()

    return render_template(
        "dashboard.html",
        total_codes=total_codes,
        active_codes=active_codes,
        scans_today=scans_today,
        total_scans=total_scans,
        recent_codes=recent_codes
    )
# =====================================================
# DOWNLOAD QR ZIP
# =====================================================
@auth.route('/download-zip')
@login_required
def download_zip():

    memory_file = BytesIO()

    codes = ProductCode.query.filter_by(
        company_id=current_user.id,
        is_deleted=False
    ).all()

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for code in codes:
            qr = qrcode.make(code.product_code)
            img_io = BytesIO()
            qr.save(img_io, 'PNG')
            img_io.seek(0)
            zipf.writestr(f"{code.product_code}.png", img_io.read())

    memory_file.seek(0)

    return send_file(memory_file, download_name="qr_codes.zip", as_attachment=True)


# =====================================================
# COMPANY PROFILE
# =====================================================
@auth.route('/company-profile')
@login_required
def company_profile():

    products = Product.query.filter_by(company_id=current_user.id).all()

    return render_template(
        "company_profile.html",
        company=current_user,
        products=products
    )


# =====================================================
# REGISTER PRODUCT
# =====================================================
@auth.route('/register-product', methods=['GET', 'POST'])
@login_required
def register_product():

    if request.method == 'POST':
        name = request.form.get('product_name')

        if not name:
            flash("Product name is required", "danger")
            return redirect(url_for('auth.register_product'))

        new_product = Product(
            product_name=name,
            company_id=current_user.id
        )

        db.session.add(new_product)
        db.session.commit()

        flash("Product Registered Successfully", "success")
        return redirect(url_for('auth.dashboard'))

    return render_template("register_product.html")



# =====================================================
# HISTORY
# =====================================================
@auth.route('/history')
@login_required
def history():
    
    codes = ProductCode.query.filter_by(
        company_id=current_user.id
    ).order_by(ProductCode.id.desc()).all()

    return render_template("history.html", codes=codes)

@auth.route('/delete-code/<int:id>')
@login_required
def delete_code(id):

    code = ProductCode.query.get_or_404(id)

    # security check
    if code.company_id != current_user.id:
        return redirect(url_for('auth.dashboard'))

    code.is_deleted = True
    db.session.commit()

    return redirect(url_for('auth.history'))

# =====================================================
# RECYCLE BIN
# =====================================================
@auth.route('/recycle-bin')
@login_required
def recycle_bin():
    deleted_codes = ProductCode.query.filter_by(
        company_id=current_user.id,
        is_deleted=True
    ).all()

    return render_template("recycle_bin.html", deleted_codes=deleted_codes)

@auth.route('/restore-code/<int:id>')
@login_required
def restore_code(id):

    code = ProductCode.query.get_or_404(id)

    # security check
    if code.company_id != current_user.id:
        return redirect(url_for('auth.dashboard'))

    code.is_deleted = False
    db.session.commit()

    return redirect(url_for('auth.recycle_bin'))


@auth.route('/verify-product', methods=['GET', 'POST'])
def public_verify():

    code = request.args.get("code") or request.form.get("code")

    if code:

        product = ProductCode.query.filter_by(
            product_code=code,
            is_deleted=False
        ).first()

        if not product:
            return render_template("verify_result.html", valid=False)

        # 🚫 If already blocked
        if product.is_blocked:
            return render_template(
                "verify_result.html",
                product=product,
                blocked=True
            )

        # ✅ Increase scan count
        product.scan_count += 1

        # 📅 Save last scanned date
        from datetime import date
        product.last_scanned = date.today()

        # 🌍 Save IP
        product.last_scanned_ip = request.remote_addr

        # 🔥 Suspicious Detection Logic (Improved)
        if product.scan_count > 20:
            product.is_blocked = True
            product.is_flagged = True
            product.risk_score = 100

        elif product.scan_count > 10:
            product.is_flagged = True
            product.risk_score = 80

        db.session.commit()

        return render_template(
            "verify_result.html",
            product=product,
            valid=True
        )

    return render_template("public_verify.html")
@auth.route('/ai-security')
@login_required
def ai_security():

    total_codes = ProductCode.query.filter_by(
        company_id=current_user.id
    ).count()

    flagged_codes = ProductCode.query.filter_by(
        company_id=current_user.id,
        is_flagged=True
    ).count()

    deleted_codes = ProductCode.query.filter_by(
        company_id=current_user.id,
        is_deleted=True
    ).count()

    # 🔥 Suspicious Codes Fetch
    suspicious_codes = ProductCode.query.filter(
        ProductCode.company_id == current_user.id,
        (ProductCode.is_flagged == True) |
        (ProductCode.is_blocked == True)
    ).all()

    return render_template(
        "ai_security.html",
        total_codes=total_codes,
        flagged_codes=flagged_codes,
        deleted_codes=deleted_codes,
        suspicious_codes=suspicious_codes
    )




@auth.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    company = Company.query.get(current_user.id)

    if request.method == "POST":

        company.name = request.form.get("company_name")
        company.email = request.form.get("company_email")
        company.category = request.form.get("company_category")

        company.theme = request.form.get("theme")

        db.session.commit()
        flash("Settings Saved Successfully!", "success")

        return redirect(url_for("auth.settings"))

    return render_template("settings.html", company=company)