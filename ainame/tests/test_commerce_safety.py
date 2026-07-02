import asyncio
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import settings
from core.resilience import CircuitBreaker, CircuitOpenError, with_timeout
from repository.commerce_repo import ORDER_PAID, OrderRepository
from repository.report_repo import REPORT_FAILED, ReportRepository
from repository.visual_repo import VISUAL_FAILED, VisualGenerationRepository


class FakeSession:
    def __init__(self, scalar_result=None):
        self.scalar_result = scalar_result
        self.scalar_calls = 0
        self.commit_calls = 0

    async def scalar(self, stmt):
        self.scalar_calls += 1
        return self.scalar_result

    async def commit(self):
        self.commit_calls += 1

    async def rollback(self):
        pass

    async def refresh(self, obj):
        pass


class SimpleOrder:
    pay_status = ORDER_PAID


class SimpleTask:
    def __init__(self, status, retry_count):
        self.id = 1
        self.user_id = 1
        self.record_id = 1
        self.candidate_id = None
        self.status = status
        self.retry_count = retry_count


class CommerceSafetyTest(unittest.IsolatedAsyncioTestCase):
    def test_jwt_secret_is_at_least_32_bytes(self):
        self.assertGreaterEqual(len(settings.JWT_SECRET_KEY.encode("utf-8")), 32)

    async def test_paid_order_does_not_grant_entitlement_again(self):
        session = FakeSession()
        order = SimpleOrder()

        result = await OrderRepository(session)._mark_locked_order_paid(
            order=order,
            provider="mock",
            trade_no=None,
            callback_data=None,
        )

        self.assertIs(result, order)
        self.assertEqual(session.scalar_calls, 0)
        self.assertEqual(session.commit_calls, 0)

    async def test_report_retry_limit_blocks_retry(self):
        task = SimpleTask(status=REPORT_FAILED, retry_count=settings.TASK_MAX_RETRIES)
        session = FakeSession(scalar_result=task)

        with self.assertRaises(ValueError):
            await ReportRepository(session).retry_user_task(user_id=1, task_id=1)

    async def test_visual_retry_limit_blocks_retry(self):
        task = SimpleTask(status=VISUAL_FAILED, retry_count=settings.TASK_MAX_RETRIES)
        session = FakeSession(scalar_result=task)

        with self.assertRaises(ValueError):
            await VisualGenerationRepository(session).retry_user_task(user_id=1, task_id=1)

    async def test_timeout_wrapper_raises_timeout(self):
        async def slow():
            await asyncio.sleep(0.05)

        with self.assertRaises(asyncio.TimeoutError):
            await with_timeout(slow(), timeout=0.001)

    async def test_circuit_breaker_opens_after_failures(self):
        breaker = CircuitBreaker(name="test", failure_threshold=2, reset_seconds=60)

        async def fail():
            raise RuntimeError("boom")

        for _ in range(2):
            with self.assertRaises(RuntimeError):
                await breaker.call(fail)

        with self.assertRaises(CircuitOpenError):
            await breaker.call(fail)
