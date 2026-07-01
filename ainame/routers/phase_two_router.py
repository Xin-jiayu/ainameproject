import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.auth import AuthHandler
from core.tools import check_com_domain
from dependencies import get_session
from repository.phase_two_repo import PhaseTwoRepository
from schemas.name_schemas import (
    CandidateScoreIn,
    DomainCheckOutSchema,
    NameCandidateOutSchema,
    OrderCreateIn,
    OrderOutSchema,
    SocialNameCheckOutSchema,
    TrademarkCheckOutSchema,
)


auth_handler = AuthHandler()
router = APIRouter(prefix="/phase2", tags=["phase2"])


@router.get("/records/{record_id}/candidates", response_model=list[NameCandidateOutSchema])
async def list_candidates(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    try:
        return await repository.list_candidates(user_id, record_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="record not found")


@router.post("/candidates/{candidate_id}/favorite", response_model=NameCandidateOutSchema)
async def favorite_candidate(
    candidate_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    candidate = await repository.set_candidate_favorite(user_id, candidate_id, True)
    if not candidate:
        raise HTTPException(status_code=404, detail="candidate not found")
    return candidate


@router.delete("/candidates/{candidate_id}/favorite", response_model=NameCandidateOutSchema)
async def unfavorite_candidate(
    candidate_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    candidate = await repository.set_candidate_favorite(user_id, candidate_id, False)
    if not candidate:
        raise HTTPException(status_code=404, detail="candidate not found")
    return candidate


@router.post("/candidates/{candidate_id}/select", response_model=NameCandidateOutSchema)
async def select_candidate(
    candidate_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    candidate = await repository.select_candidate(user_id, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="candidate not found")
    return candidate


@router.patch("/candidates/{candidate_id}/score", response_model=NameCandidateOutSchema)
async def update_candidate_score(
    candidate_id: int,
    data: CandidateScoreIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    candidate = await repository.update_candidate_score(user_id, candidate_id, data.score)
    if not candidate:
        raise HTTPException(status_code=404, detail="candidate not found")
    return candidate


@router.post("/records/{record_id}/domain-checks", response_model=list[DomainCheckOutSchema])
async def create_domain_checks(
    record_id: int,
    suffixes: list[str] | None = Query(default=None),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    suffixes = suffixes or ["com", "cn", "ai"]
    try:
        candidates = await repository.list_candidates(user_id, record_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="record not found")
    if not candidates:
        raise HTTPException(status_code=400, detail="no candidates for this record")

    checks = []
    for candidate in candidates:
        for suffix in suffixes:
            domain = _domain_for_suffix(candidate.domain or f"candidate-{candidate.id}", suffix)
            check_status = await _check_domain(domain, suffix)
            checks.append(
                {
                    "record_id": int(record_id),
                    "candidate_id": candidate.id,
                    "domain": domain,
                    "suffix": suffix,
                    "check_status": check_status,
                    "raw_result": {"provider": "whois" if suffix == "com" else "mock"},
                }
            )
    return await repository.save_domain_checks(user_id, record_id, checks)


@router.get("/records/{record_id}/domain-checks", response_model=list[DomainCheckOutSchema])
async def list_domain_checks(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    try:
        return await repository.list_domain_checks(user_id, record_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="record not found")


@router.post("/records/{record_id}/trademark-checks", response_model=list[TrademarkCheckOutSchema])
async def create_trademark_checks(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    try:
        return await repository.create_trademark_checks(user_id, record_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="record not found")


@router.get("/records/{record_id}/trademark-checks", response_model=list[TrademarkCheckOutSchema])
async def list_trademark_checks(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    try:
        return await repository.list_trademark_checks(user_id, record_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="record not found")


@router.post("/records/{record_id}/social-checks", response_model=list[SocialNameCheckOutSchema])
async def create_social_checks(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    try:
        return await repository.create_social_checks(user_id, record_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="record not found")


@router.get("/records/{record_id}/social-checks", response_model=list[SocialNameCheckOutSchema])
async def list_social_checks(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    try:
        return await repository.list_social_checks(user_id, record_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="record not found")


@router.post("/orders", response_model=OrderOutSchema)
async def create_order(
    data: OrderCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    return await repository.create_order(
        user_id=user_id,
        product_type=data.product_type,
        amount=data.amount,
        quota_delta=data.quota_delta,
        business_id=data.business_id,
        extra_data=data.extra_data,
    )


@router.get("/orders", response_model=list[OrderOutSchema])
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    return await repository.list_orders(user_id, skip=skip, limit=limit)


@router.get("/orders/{order_id}", response_model=OrderOutSchema)
async def get_order(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    order = await repository.get_order(user_id, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return order


@router.post("/orders/{order_id}/mock-pay", response_model=OrderOutSchema)
async def mock_pay_order(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = PhaseTwoRepository(session=session)
    order = await repository.mark_order_paid(user_id, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return order


def _domain_for_suffix(value: str, suffix: str) -> str:
    suffix = suffix.lstrip(".").lower()
    domain = (value or "").strip().lower().replace(" ", "")
    if not domain.isascii():
        domain = "ainame"
    if "." in domain:
        domain = domain.rsplit(".", 1)[0]
    if not domain:
        domain = "ainame"
    return f"{domain}.{suffix}"


async def _check_domain(domain: str, suffix: str) -> str:
    suffix = suffix.lstrip(".").lower()
    if suffix == "com":
        return await check_com_domain(domain)
    await asyncio.sleep(0)
    return "mock_pending_real_provider"
