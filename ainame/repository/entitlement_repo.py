from datetime import datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.business import EntitlementAccount, EntitlementRecord
from models.user import User


class EntitlementRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_accounts(self, user_id: int):
        result = await self.session.execute(
            select(EntitlementAccount)
            .where(EntitlementAccount.user_id == int(user_id))
            .order_by(EntitlementAccount.entitlement_type, EntitlementAccount.valid_until)
        )
        return result.scalars().all()

    async def list_records(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: int | None = None,
        entitlement_type: str | None = None,
    ):
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        total_stmt = select(func.count()).select_from(EntitlementRecord)
        list_stmt = select(EntitlementRecord).order_by(desc(EntitlementRecord.created_at), desc(EntitlementRecord.id))
        if user_id is not None:
            total_stmt = total_stmt.where(EntitlementRecord.user_id == int(user_id))
            list_stmt = list_stmt.where(EntitlementRecord.user_id == int(user_id))
        if entitlement_type:
            total_stmt = total_stmt.where(EntitlementRecord.entitlement_type == entitlement_type)
            list_stmt = list_stmt.where(EntitlementRecord.entitlement_type == entitlement_type)
        total = await self.session.scalar(total_stmt)
        result = await self.session.execute(list_stmt.offset((page - 1) * page_size).limit(page_size))
        return {
            "items": result.scalars().all(),
            "total": total or 0,
            "page": page,
            "page_size": page_size,
        }

    async def grant(
        self,
        user_id: int,
        entitlement_type: str,
        amount: int,
        source: str,
        order_id: int | None = None,
        valid_days: int | None = None,
        remark: str | None = None,
        commit: bool = True,
    ):
        if amount <= 0:
            return None
        valid_until = datetime.now() + timedelta(days=valid_days) if valid_days else None
        account = await self._get_or_create_account(user_id, entitlement_type, valid_until)
        before_balance = account.balance
        account.balance += amount
        if valid_until and (not account.valid_until or account.valid_until < valid_until):
            account.valid_until = valid_until
        record = self._create_record(
            account=account,
            order_id=order_id,
            source=source,
            change_type="grant",
            change_amount=amount,
            before_balance=before_balance,
            after_balance=account.balance,
            valid_until=account.valid_until,
            remark=remark,
        )
        await self._sync_user_quota_total(user_id, entitlement_type)
        if commit:
            await self.session.commit()
            await self.session.refresh(account)
            await self.session.refresh(record)
        return record

    async def consume(
        self,
        user_id: int,
        entitlement_type: str,
        amount: int,
        source: str,
        remark: str | None = None,
        commit: bool = True,
    ):
        if amount <= 0:
            return None
        account = await self._get_account_for_update(user_id, entitlement_type)
        if not account or account.balance < amount:
            return None
        before_balance = account.balance
        account.balance -= amount
        record = self._create_record(
            account=account,
            order_id=None,
            source=source,
            change_type="consume",
            change_amount=-amount,
            before_balance=before_balance,
            after_balance=account.balance,
            valid_until=account.valid_until,
            remark=remark,
        )
        await self._sync_user_quota_total(user_id, entitlement_type)
        if commit:
            await self.session.commit()
            await self.session.refresh(account)
            await self.session.refresh(record)
        return record

    async def refund(
        self,
        user_id: int,
        entitlement_type: str,
        amount: int,
        source: str,
        remark: str | None = None,
        commit: bool = True,
    ):
        if amount <= 0:
            return None
        account = await self._get_or_create_account(user_id, entitlement_type)
        before_balance = account.balance
        account.balance += amount
        record = self._create_record(
            account=account,
            order_id=None,
            source=source,
            change_type="refund",
            change_amount=amount,
            before_balance=before_balance,
            after_balance=account.balance,
            valid_until=account.valid_until,
            remark=remark,
        )
        await self._sync_user_quota_total(user_id, entitlement_type)
        if commit:
            await self.session.commit()
            await self.session.refresh(account)
            await self.session.refresh(record)
        return record

    async def admin_adjust(
        self,
        user_id: int,
        entitlement_type: str,
        amount: int,
        valid_days: int | None,
        remark: str | None,
    ):
        try:
            if amount > 0:
                record = await self.grant(
                    user_id=user_id,
                    entitlement_type=entitlement_type,
                    amount=amount,
                    source="admin_adjust",
                    valid_days=valid_days,
                    remark=remark,
                    commit=False,
                )
            elif amount < 0:
                record = await self.consume(
                    user_id=user_id,
                    entitlement_type=entitlement_type,
                    amount=abs(amount),
                    source="admin_adjust",
                    remark=remark,
                    commit=False,
                )
            else:
                return None
            if not record:
                return None
            await self.session.commit()
            await self.session.refresh(record)
            return record
        except Exception:
            await self.session.rollback()
            raise

    async def _get_account_for_update(self, user_id: int, entitlement_type: str):
        return await self.session.scalar(
            select(EntitlementAccount)
            .where(
                EntitlementAccount.user_id == int(user_id),
                EntitlementAccount.entitlement_type == entitlement_type,
            )
            .with_for_update()
        )

    async def _get_or_create_account(
        self,
        user_id: int,
        entitlement_type: str,
        valid_until: datetime | None = None,
    ):
        account = await self._get_account_for_update(user_id, entitlement_type)
        if account:
            return account
        account = EntitlementAccount(
            user_id=int(user_id),
            entitlement_type=entitlement_type,
            balance=0,
            valid_until=valid_until,
        )
        self.session.add(account)
        await self.session.flush()
        return account

    def _create_record(
        self,
        account: EntitlementAccount,
        order_id: int | None,
        source: str,
        change_type: str,
        change_amount: int,
        before_balance: int,
        after_balance: int,
        valid_until: datetime | None,
        remark: str | None,
    ):
        record = EntitlementRecord(
            user_id=account.user_id,
            account_id=account.id,
            order_id=order_id,
            entitlement_type=account.entitlement_type,
            source=source,
            change_type=change_type,
            change_amount=change_amount,
            before_balance=before_balance,
            after_balance=after_balance,
            valid_until=valid_until,
            remark=remark,
        )
        self.session.add(record)
        return record

    async def _sync_user_quota_total(self, user_id: int, entitlement_type: str):
        if entitlement_type not in {"free_quota", "quota"}:
            return
        total = await self.session.scalar(
            select(func.coalesce(func.sum(EntitlementAccount.balance), 0)).where(
                EntitlementAccount.user_id == int(user_id),
                EntitlementAccount.entitlement_type.in_(["free_quota", "quota"]),
            )
        )
        user = await self.session.scalar(select(User).where(User.id == int(user_id)).with_for_update())
        if user:
            user.free_quota = int(total or 0)
