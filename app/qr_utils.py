import io
import zipfile
import qrcode
from flask import send_file

def generate_qr_zip(codes):

    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:

        for code in codes:
            verification_url = f"http://127.0.0.1:5000/verify/{code.product_code}"
            qr = qrcode.make(verification_url)

            img_io = io.BytesIO()
            qr.save(img_io, format='PNG')
            img_io.seek(0)

            zf.writestr(f"{code.product_code}.png", img_io.read())

    memory_file.seek(0)

    return send_file(
        memory_file,
        download_name="qr_codes.zip",
        as_attachment=True
    )