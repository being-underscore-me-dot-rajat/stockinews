import logging
from fastapi import APIRouter, Depends, HTTPException
from models.schemas import LoginRequest, SignupRequest, ResetPasswordRequest
from services.supabase_client import supabase_admin, supabase_anon
from services.auth_utils import get_current_user

log = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login")
def login(body: LoginRequest):
    try:
        res = supabase_anon.auth.sign_in_with_password({"email": body.email, "password": body.password})
        return {
            "message": "Login successful",
            "token": res.session.access_token,
            "user": {
                "id": res.user.id,
                "email": res.user.email,
                "name": res.user.user_metadata.get("name", ""),
            },
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/signup", status_code=201)
def signup(body: SignupRequest):
    try:
        supabase_admin.auth.admin.create_user({
            "email": body.email,
            "password": body.password,
            "user_metadata": {"name": body.name},
            "email_confirm": True,
        })
        res = supabase_anon.auth.sign_in_with_password({"email": body.email, "password": body.password})
        return {"message": "User registered successfully", "token": res.session.access_token}
    except Exception as exc:
        err = str(exc).lower()
        if "already" in err or "exists" in err:
            raise HTTPException(status_code=400, detail="Email already exists")
        log.exception("Signup failed")
        raise HTTPException(status_code=400, detail="Registration failed")


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest):
    try:
        page = supabase_admin.auth.admin.list_users(page=1, per_page=1000)
        user = next((u for u in page if u.email == body.email), None)
        if not user:
            raise HTTPException(status_code=404, detail="No account found with that email")
        supabase_admin.auth.admin.update_user_by_id(str(user.id), {"password": body.password})
        return {"message": "Password reset successful. Please log in."}
    except HTTPException:
        raise
    except Exception:
        log.exception("Reset password failed")
        raise HTTPException(status_code=500, detail="Password reset failed")


@router.get("/me")
def get_me(user=Depends(get_current_user)):
    user_id = user.get("sub")
    try:
        u = supabase_admin.auth.admin.get_user_by_id(user_id).user
        return {"user": {"id": u.id, "email": u.email, "name": u.user_metadata.get("name", "")}}
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")
