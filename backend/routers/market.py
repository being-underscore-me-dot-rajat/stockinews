from fastapi import APIRouter, Depends
from services.auth_utils import get_current_user
from services.market_service import get_market_overview

router = APIRouter()


@router.get("/marketwatch")
def market_watch(user=Depends(get_current_user)):
    return {"market": get_market_overview()}
