import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def get_image(id, text0, text1):
    """ Gets a captioned image's url """
    url = "https://api.imgflip.com/caption_image"
    response = requests.post(url, data={'template_id': str(id), 'username': 'imgflip.api.testing', 'password': 'Bg45tG8i', 'text0': text0, 'text1': text1, 'font': 'impact'}).json()

    if response["success"]:
        return response["data"]["url"]
    else:
        print("haha api go brrrr")
        return None

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
