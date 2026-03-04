from flask import Blueprint
from flask_login import login_required

company_bp = Blueprint("company", __name__, url_prefix="/company")



@company_bp.route("/dashboard")
@login_required
def dashboard():
    return "Company Dashboard Working"