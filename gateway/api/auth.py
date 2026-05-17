from django.contrib.auth import authenticate
from ninja import Router
from ninja.errors import HttpError

from gateway.api.auth_jwt import create_access_token
from gateway.schemas.auth import LoginIn, LoginOut

router = Router(tags=["Auth"])


@router.post("/login", response=LoginOut, auth=None)
def login(request, payload: LoginIn):
    user = authenticate(username=payload.username, password=payload.password)
    if user is None or not user.is_active:
        raise HttpError(401, "Invalid credentials")
    token = create_access_token(user.username)
    return LoginOut(access_token=token, username=user.username)
