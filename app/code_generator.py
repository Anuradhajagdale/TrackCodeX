import secrets
import string
import hashlib
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import TrackCode


# -------------------------------
# CHARACTER SET BUILDER
# -------------------------------
def get_charset(code_type):
    if code_type == "numeric":
        return string.digits
    elif code_type == "alphabet":
        return string.ascii_uppercase
    elif code_type == "alphanumeric":
        return string.ascii_uppercase + string.digits
    else:
        raise ValueError("Invalid code type")


# -------------------------------
# SECURE RANDOM CODE GENERATOR
# -------------------------------
def generate_single_code(length, charset):
    return ''.join(secrets.choice(charset) for _ in range(length))


# -------------------------------
# HASH GENERATOR (QR PROTECTION)
# -------------------------------
def generate_qr_hash(code):
    return hashlib.sha256(code.encode()).hexdigest()


# -------------------------------
# BULK GENERATOR (PRODUCTION SAFE)
# -------------------------------
def generate_bulk_codes(product_id, quantity, length, code_type):
    charset = get_charset(code_type)

    generated_codes = set()
    batch_objects = []

    while len(generated_codes) < quantity:
        code = generate_single_code(length, charset)

        if code in generated_codes:
            continue

        generated_codes.add(code)

    for code in generated_codes:
        qr_hash = generate_qr_hash(code)

        track_code = TrackCode(
            product_code=code,
            qr_hash=qr_hash,
            product_id=product_id
        )

        batch_objects.append(track_code)

    try:
        db.session.bulk_save_objects(batch_objects)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Exception("Duplicate collision detected. Retry.")

    return len(batch_objects)