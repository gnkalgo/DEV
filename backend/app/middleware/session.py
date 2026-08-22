"""Copy the opaque session cookie onto request.state. Lookup happens in get_current_user."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SessionCookieMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        settings = request.app.state.settings
        request.state.session_token = request.cookies.get(settings.session_cookie_name)
        request.state.user_id = None
        return await call_next(request)
