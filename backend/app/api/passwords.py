from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import hash_password, verify_password
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.user import PasswordChange


class PasswordRoute(APIRoute):
    """Do not echo sensitive request input in FastAPI validation errors."""

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request):
            try:
                return await handler(request)
            except RequestValidationError:
                raise HTTPException(
                    status_code=422,
                    detail="Provide only old_password and new_password; new password must be 8–128 characters.",
                ) from None

        return safe_handler


router = APIRouter(route_class=PasswordRoute)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.old_password.get_secret_value(), current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    current_user.password_hash = hash_password(data.new_password.get_secret_value())
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
