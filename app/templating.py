from typing import Optional, Dict, Any
from fastapi.templating import Jinja2Templates
from fastapi import Request
import os

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)


def flash(request: Request, message: str, category: str = "info") -> None:
    """Store a flash message in the session."""
    flashes = request.session.setdefault("flashes", [])
    flashes.append({"message": message, "category": category})


def get_flashes(request: Request):
    """Pop and return all flash messages from session."""
    return request.session.pop("flashes", [])


def render(request: Request, template: str, context: Optional[Dict[str, Any]] = None, **kwargs):
    """Render a Jinja2 template with request, flashes, and current_user injected."""
    from app.database import get_db
    from app.models import User

    ctx: Dict[str, Any] = dict(context or {})
    ctx.update(kwargs)
    ctx["flashes"] = get_flashes(request)

    # Inject current_user from session
    user_id = request.session.get("user_id")
    current_user = None
    if user_id:
        db = next(get_db())
        try:
            current_user = db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()
    ctx["current_user"] = current_user

    return templates.TemplateResponse(
        name=template,
        request=request,
        context=ctx,
    )
