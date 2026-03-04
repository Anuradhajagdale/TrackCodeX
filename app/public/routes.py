from flask import Blueprint

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    return "Welcome to TrackCodeX 🚀"


@public_bp.route("/about")
def about():
    return "About Page"
