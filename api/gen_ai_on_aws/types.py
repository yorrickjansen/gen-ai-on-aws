from pydantic import BaseModel, Field


class LangFuseConfig(BaseModel):
    public_key: str = Field(description="The public key for LangFuse.")
    secret_key: str = Field(description="The secret key for LangFuse.")
    host: str = Field(description="The host for LangFuse.")
