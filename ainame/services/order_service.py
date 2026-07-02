from fastapi import HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession

from repository.phase_two_repo import PhaseTwoRepository
from schemas.name_schemas import OrderCreateIn


class OrderService:
    """Order creation and payment state transitions."""

    def __init__(self, session: AsyncSession):
        self.repository = PhaseTwoRepository(session=session)

    async def create_order(self, user_id: int, data: OrderCreateIn):
        return await self.repository.create_order(
            user_id=user_id,
            product_type=data.product_type,
            amount=data.amount,
            quota_delta=data.quota_delta,
            business_id=data.business_id,
            extra_data=data.extra_data,
        )

    async def list_orders(self, user_id: int, skip: int = 0, limit: int = 20):
        return await self.repository.list_orders(user_id, skip=skip, limit=limit)

    async def get_order(self, user_id: int, order_id: int):
        order = await self.repository.get_order(user_id, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="order not found")
        return order

    async def mock_pay_order(self, user_id: int, order_id: int):
        order = await self.repository.mark_order_paid(user_id, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="order not found")
        return order
