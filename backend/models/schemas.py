from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class ResetPasswordRequest(BaseModel):
    email: str
    password: str


class StockTransaction(BaseModel):
    ticker: str
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)
    action: str


class SellRequest(BaseModel):
    ticker: str
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)


class WatchlistAdd(BaseModel):
    symbol: str
