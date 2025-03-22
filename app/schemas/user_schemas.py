from pydantic import BaseModel, ConfigDict, EmailStr


class SUserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str


class SUserSignIn(SUserBase):
    password: bytes


class SUserSignUp(SUserSignIn):
    email: EmailStr
    active: bool = True

    model_config = {
        "json_schema_extra": {
            "examples":
                [
                    {
                        "username": "username",
                        "password": "password",
                        "email": "mail@example.com",
                    }
                ]
        }
    }


class SUserShortInfo(SUserBase):
    email: EmailStr
