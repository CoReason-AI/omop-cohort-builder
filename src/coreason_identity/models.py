from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class UserContext(BaseModel):
    """
    Standardized User Context object to be available throughout the middleware stack.
    """

    sub: str
    email: EmailStr
    project_context: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
