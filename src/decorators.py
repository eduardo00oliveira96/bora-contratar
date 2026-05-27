import os
from functools import wraps
from flask import session, redirect, url_for, request, g
import jwt as pyjwt

JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "9f2c1b7e4a8d6f3c0e5b2a1d9c7e6f4b3a2c1d0e8f7a6b5c")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login", next=request.url))
        g.usuario = session["user"]
        return f(*args, **kwargs)
    return decorated_function

def role_required(*papeis_permitidos):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if g.usuario.get("papel") not in papeis_permitidos:
                return redirect(url_for("admin.dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def verificar_jwt(token):
    try:
        payload = pyjwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"require": ["sub", "exp"]}
        )
        return payload
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError as e:
        return None
