from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from schemas.name_schemas import (
    CandidateScoreIn,
    DomainCheckOutSchema,
    NameCandidateOutSchema,
    OrderCreateIn,
    OrderOutSchema,
    SocialNameCheckOutSchema,
    TrademarkCheckOutSchema,
)
from services.order_service import OrderService
from services.validation_service import ValidationService


auth_handler = AuthHandler()
router = APIRouter(prefix="/phase2", tags=["phase2"])


@router.get("/records/{record_id}/candidates", response_model=list[NameCandidateOutSchema])
async def list_candidates(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await ValidationService(session=session).list_candidates(user_id, record_id)


@router.post("/candidates/{candidate_id}/favorite", response_model=NameCandidateOutSchema)
async def favorite_candidate(
    candidate_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await ValidationService(session=session).favorite_candidate(user_id, candidate_id)


@router.delete("/candidates/{candidate_id}/favorite", response_model=NameCandidateOutSchema)
async def unfavorite_candidate(
    candidate_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await ValidationService(session=session).unfavorite_candidate(user_id, candidate_id)


@router.post("/candidates/{candidate_id}/select", response_model=NameCandidateOutSchema)
async def select_candidate(
    candidate_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await ValidationService(session=session).select_candidate(user_id, candidate_id)


@router.patch("/candidates/{candidate_id}/score", response_model=NameCandidateOutSchema)
async def update_candidate_score(
    candidate_id: int,
    data: CandidateScoreIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await ValidationService(session=session).update_candidate_score(
        user_id,
        candidate_id,
        data.score,
        data.score_detail,
        data.score_reason,
    )


@router.post("/records/{record_id}/domain-checks", response_model=list[DomainCheckOutSchema])
async def create_domain_checks(
    record_id: int,
    suffixes: list[str] | None = Query(default=None),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await ValidationService(session=session).create_domain_checks(user_id, record_id, suffixes)


@router.get("/records/{record_id}/domain-checks", response_model=list[DomainCheckOutSchema])
async def list_domain_checks(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await ValidationService(session=session).list_domain_checks(user_id, record_id)


@router.post("/records/{record_id}/trademark-checks", response_model=list[TrademarkCheckOutSchema])
async def create_trademark_checks(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await ValidationService(session=session).create_trademark_checks(user_id, record_id)


@router.get("/records/{record_id}/trademark-checks", response_model=list[TrademarkCheckOutSchema])
async def list_trademark_checks(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await ValidationService(session=session).list_trademark_checks(user_id, record_id)


@router.post("/records/{record_id}/social-checks", response_model=list[SocialNameCheckOutSchema])
async def create_social_checks(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await ValidationService(session=session).create_social_checks(user_id, record_id)


@router.get("/records/{record_id}/social-checks", response_model=list[SocialNameCheckOutSchema])
async def list_social_checks(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await ValidationService(session=session).list_social_checks(user_id, record_id)


@router.post("/orders", response_model=OrderOutSchema)
async def create_order(
    data: OrderCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await OrderService(session=session).create_order(user_id, data)


@router.get("/orders", response_model=list[OrderOutSchema])
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await OrderService(session=session).list_orders(user_id, skip=skip, limit=limit)


@router.get("/orders/{order_id}", response_model=OrderOutSchema)
async def get_order(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await OrderService(session=session).get_order(user_id, order_id)


@router.post("/orders/{order_id}/mock-pay", response_model=OrderOutSchema)
async def mock_pay_order(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await OrderService(session=session).mock_pay_order(user_id, order_id)
