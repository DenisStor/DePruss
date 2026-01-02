"""Authentication routes for admin panel."""
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.services.auth import authenticate_admin, create_access_token
from app.services.rate_limiter import login_limiter
from .dependencies import templates

router = APIRouter()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, considering proxies."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    client_ip = get_client_ip(request)

    # Check rate limit before authentication
    is_limited, remaining = login_limiter.is_rate_limited(client_ip)
    if is_limited:
        retry_after = login_limiter.get_retry_after(client_ip)
        minutes = retry_after // 60 + 1
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "error": f"Слишком много попыток. Попробуйте через {minutes} мин."
            }
        )

    user = await authenticate_admin(db, username, password)
    if not user:
        # Record failed attempt
        login_limiter.record_attempt(client_ip)
        _, remaining = login_limiter.is_rate_limited(client_ip)

        error_msg = "Неверный логин или пароль"
        if remaining > 0:
            error_msg += f" (осталось {remaining} попыток)"

        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": error_msg}
        )

    # Successful login - reset rate limit
    login_limiter.reset(client_ip)

    # Update last login time
    user.last_login = datetime.utcnow()
    await db.commit()

    # Create token and set cookie
    token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/admin", status_code=302)

    # Determine secure flag based on request protocol
    is_secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400,  # 24 hours
        samesite="lax",
        secure=is_secure
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("access_token")
    return response
