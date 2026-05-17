from ninja import Schema


class LoginIn(Schema):
    username: str
    password: str


class TokenOut(Schema):
    access_token: str
    token_type: str = "bearer"


class LoginOut(TokenOut):
    username: str
