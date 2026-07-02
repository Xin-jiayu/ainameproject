from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import desc, exists, func, select, update
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.business import Order, Product
from models.user import User
from repository.entitlement_repo import EntitlementRepository


ORDER_PENDING = "pending"
ORDER_PAID = "paid"
ORDER_FAILED = "failed"
ORDER_CLOSED = "closed"
ORDER_REFUNDED = "refunded"
ORDER_STATUSES = {ORDER_PENDING, ORDER_PAID, ORDER_FAILED, ORDER_CLOSED, ORDER_REFUNDED}


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_active_products(self):
        result = await self.session.execute(
            select(Product)
            .where(Product.is_active.is_(True))
            .order_by(Product.sort_order, Product.id)
        )
        return result.scalars().all()

    async def list_products(self, page: int = 1, page_size: int = 20, is_active: bool | None = None):
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        total_stmt = select(func.count()).select_from(Product)
        list_stmt = select(Product).order_by(Product.sort_order, Product.id)
        if is_active is not None:
            total_stmt = total_stmt.where(Product.is_active.is_(is_active))
            list_stmt = list_stmt.where(Product.is_active.is_(is_active))

        total = await self.session.scalar(total_stmt)
        result = await self.session.execute(
            list_stmt.offset((page - 1) * page_size).limit(page_size)
        )
        return {
            "items": result.scalars().all(),
            "total": total or 0,
            "page": page,
            "page_size": page_size,
        }

    async def get_product(self, product_id: int):
        result = await self.session.execute(select(Product).where(Product.id == int(product_id)))
        return result.scalar_one_or_none()

    async def code_exists(self, code: str, exclude_product_id: int | None = None):
        condition = Product.code == code
        if exclude_product_id is not None:
            condition = condition & (Product.id != int(exclude_product_id))
        return await self.session.scalar(select(exists().where(condition)))

    async def create_product(self, data: dict):
        try:
            product = Product(**data)
            self.session.add(product)
            await self.session.commit()
            await self.session.refresh(product)
            return product
        except Exception:
            await self.session.rollback()
            raise

    async def update_product(self, product_id: int, data: dict):
        try:
            product = await self.session.scalar(
                select(Product).where(Product.id == int(product_id)).with_for_update()
            )
            if not product:
                return None
            for key, value in data.items():
                setattr(product, key, value)
            await self.session.commit()
            await self.session.refresh(product)
            return product
        except Exception:
            await self.session.rollback()
            raise

    async def set_product_active(self, product_id: int, is_active: bool):
        return await self.update_product(product_id, {"is_active": is_active})


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_order_from_product(self, user_id: int, product_id: int, request_key: str | None = None):
        try:
            if request_key:
                existing_order = await self.session.scalar(
                    select(Order).where(Order.user_id == int(user_id), Order.request_key == request_key)
                )
                if existing_order:
                    return existing_order

            product = await self.session.scalar(
                select(Product).where(Product.id == int(product_id), Product.is_active.is_(True))
            )
            if not product:
                return None

            quota_delta = product.entitlement_amount if product.entitlement_type in {"free_quota", "quota"} else 0
            order = Order(
                user_id=int(user_id),
                product_id=product.id,
                order_no=f"NO{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:8]}",
                request_key=request_key,
                product_type=product.code,
                amount=product.price,
                pay_status=ORDER_PENDING,
                business_id=product.id,
                quota_delta=quota_delta,
                extra_data={
                    "product_name": product.name,
                    "entitlement_type": product.entitlement_type,
                    "entitlement_amount": product.entitlement_amount,
                    "valid_days": product.valid_days,
                },
                expire_at=datetime.now() + timedelta(minutes=30),
            )
            self.session.add(order)
            await self.session.commit()
            await self.session.refresh(order)
            return order
        except Exception:
            await self.session.rollback()
            raise

    async def list_user_orders(self, user_id: int, page: int = 1, page_size: int = 20, pay_status: str | None = None):
        await self.close_expired_orders(user_id=int(user_id))
        return await self._list_orders(page=page, page_size=page_size, user_id=int(user_id), pay_status=pay_status)

    async def list_all_orders(self, page: int = 1, page_size: int = 20, pay_status: str | None = None):
        await self.close_expired_orders()
        return await self._list_orders(page=page, page_size=page_size, pay_status=pay_status)

    async def get_user_order(self, user_id: int, order_id: int):
        await self.close_expired_orders(user_id=int(user_id))
        return await self.session.scalar(
            select(Order).where(Order.id == int(order_id), Order.user_id == int(user_id))
        )

    async def get_order(self, order_id: int):
        await self.close_expired_orders()
        return await self.session.scalar(select(Order).where(Order.id == int(order_id)))

    async def mark_paid(
        self,
        user_id: int,
        order_id: int,
        provider: str | None = "mock",
        trade_no: str | None = None,
        callback_data: dict | None = None,
    ):
        try:
            await self.close_expired_orders(user_id=int(user_id), commit=False)
            order = await self.session.scalar(
                select(Order)
                .where(Order.id == int(order_id), Order.user_id == int(user_id))
                .with_for_update()
            )
            if not order:
                return None
            return await self._mark_locked_order_paid(order, provider, trade_no, callback_data)
        except Exception:
            await self.session.rollback()
            raise

    async def mark_failed(
        self,
        user_id: int,
        order_id: int,
        reason: str | None = None,
        provider: str | None = "mock",
        trade_no: str | None = None,
        callback_data: dict | None = None,
    ):
        return await self._change_pending_order_status(
            user_id=user_id,
            order_id=order_id,
            status=ORDER_FAILED,
            reason=reason,
            time_field="failed_at",
            provider=provider,
            trade_no=trade_no,
            callback_data=callback_data,
        )

    async def mark_paid_by_order_no(
        self,
        order_no: str,
        provider: str,
        trade_no: str | None = None,
        callback_data: dict | None = None,
    ):
        try:
            await self.close_expired_orders(commit=False)
            order = await self.session.scalar(
                select(Order).where(Order.order_no == order_no).with_for_update()
            )
            if not order:
                return None
            return await self._mark_locked_order_paid(order, provider, trade_no, callback_data)
        except Exception:
            await self.session.rollback()
            raise

    async def mark_failed_by_order_no(
        self,
        order_no: str,
        provider: str,
        reason: str | None = None,
        trade_no: str | None = None,
        callback_data: dict | None = None,
    ):
        try:
            await self.close_expired_orders(commit=False)
            order = await self.session.scalar(
                select(Order).where(Order.order_no == order_no).with_for_update()
            )
            if not order:
                return None
            if order.pay_status == ORDER_FAILED:
                return order
            if order.pay_status != ORDER_PENDING:
                raise ValueError(f"order status is {order.pay_status}, cannot mark failed")
            order.pay_status = ORDER_FAILED
            order.status_reason = reason
            order.payment_provider = provider
            order.payment_trade_no = trade_no
            order.payment_callback_data = callback_data
            order.payment_verified_at = datetime.now()
            order.failed_at = datetime.now()
            await self.session.commit()
            await self.session.refresh(order)
            return order
        except Exception:
            await self.session.rollback()
            raise

    async def close_order(self, user_id: int, order_id: int, reason: str | None = None):
        return await self._change_pending_order_status(
            user_id=user_id,
            order_id=order_id,
            status=ORDER_CLOSED,
            reason=reason or "user closed order",
            time_field="closed_at",
        )

    async def _change_pending_order_status(
        self,
        user_id: int,
        order_id: int,
        status: str,
        reason: str | None,
        time_field: str,
        provider: str | None = None,
        trade_no: str | None = None,
        callback_data: dict | None = None,
    ):
        try:
            await self.close_expired_orders(user_id=int(user_id), commit=False)
            order = await self.session.scalar(
                select(Order)
                .where(Order.id == int(order_id), Order.user_id == int(user_id))
                .with_for_update()
            )
            if not order:
                return None
            if order.pay_status == status:
                return order
            if order.pay_status != ORDER_PENDING:
                raise ValueError(f"order status is {order.pay_status}, cannot change to {status}")
            order.pay_status = status
            order.status_reason = reason
            if provider:
                order.payment_provider = provider
            if trade_no:
                order.payment_trade_no = trade_no
            if callback_data is not None:
                order.payment_callback_data = callback_data
                order.payment_verified_at = datetime.now()
            setattr(order, time_field, datetime.now())
            await self.session.commit()
            await self.session.refresh(order)
            return order
        except Exception:
            await self.session.rollback()
            raise

    async def close_expired_orders(self, user_id: int | None = None, commit: bool = True):
        now = datetime.now()
        stmt = (
            update(Order)
            .where(
                Order.pay_status == ORDER_PENDING,
                Order.expire_at.is_not(None),
                Order.expire_at <= now,
            )
            .values(
                pay_status=ORDER_CLOSED,
                status_reason="order expired",
                closed_at=now,
            )
        )
        if user_id is not None:
            stmt = stmt.where(Order.user_id == int(user_id))
        result = await self.session.execute(stmt)
        if commit:
            await self.session.commit()
        return result.rowcount or 0

    async def _mark_locked_order_paid(
        self,
        order: Order,
        provider: str | None,
        trade_no: str | None,
        callback_data: dict | None,
    ):
        if order.pay_status == ORDER_PAID:
            return order
        if order.pay_status != ORDER_PENDING:
            raise ValueError(f"order status is {order.pay_status}, cannot mark paid")

        user = await self.session.scalar(select(User).where(User.id == int(order.user_id)).with_for_update())
        if not user:
            return None
        entitlement_type = (order.extra_data or {}).get("entitlement_type") or "quota"
        entitlement_amount = int((order.extra_data or {}).get("entitlement_amount") or order.quota_delta or 0)
        valid_days = (order.extra_data or {}).get("valid_days")
        before_quota = user.free_quota
        if entitlement_amount > 0:
            record = await EntitlementRepository(self.session).grant(
                user_id=order.user_id,
                entitlement_type=entitlement_type,
                amount=entitlement_amount,
                source="order_paid",
                order_id=order.id,
                valid_days=valid_days,
                remark=f"order {order.order_no} paid",
                commit=False,
            )
            order.after_quota = user.free_quota
        else:
            order.after_quota = user.free_quota
        order.before_quota = before_quota
        order.pay_status = ORDER_PAID
        order.status_reason = None
        order.payment_provider = provider
        order.payment_trade_no = trade_no
        order.payment_callback_data = callback_data
        order.payment_verified_at = datetime.now()
        order.paid_at = datetime.now()
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def _list_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: int | None = None,
        pay_status: str | None = None,
    ):
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        total_stmt = select(func.count()).select_from(Order)
        list_stmt = select(Order).order_by(desc(Order.created_at), desc(Order.id))
        if user_id is not None:
            total_stmt = total_stmt.where(Order.user_id == int(user_id))
            list_stmt = list_stmt.where(Order.user_id == int(user_id))
        if pay_status:
            total_stmt = total_stmt.where(Order.pay_status == pay_status)
            list_stmt = list_stmt.where(Order.pay_status == pay_status)
        total = await self.session.scalar(total_stmt)
        result = await self.session.execute(list_stmt.offset((page - 1) * page_size).limit(page_size))
        return {
            "items": result.scalars().all(),
            "total": total or 0,
            "page": page,
            "page_size": page_size,
        }
