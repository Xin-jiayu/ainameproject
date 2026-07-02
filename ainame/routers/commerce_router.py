import hashlib
import hmac
import json
import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from dependencies import get_admin_user, get_current_user, get_session
from repository.admin_commercial_stats_repo import AdminCommercialStatsRepository
from repository.admin_operation_log_repo import AdminOperationLogRepository
from repository.commerce_repo import ORDER_STATUSES, OrderRepository, ProductRepository
from repository.entitlement_repo import EntitlementRepository
from repository.report_repo import REPORT_STATUSES, ReportRepository
from repository.visual_repo import VISUAL_STATUSES, VISUAL_TASK_TYPES, VisualGenerationRepository
from schemas.commerce_schemas import (
    AdminEntitlementAdjustIn,
    AdminCommercialFailureStatsOut,
    AlipaySandboxFailIn,
    AlipaySandboxSuccessIn,
    CommerceOrderListOut,
    CommerceOrderOut,
    EntitlementAccountOut,
    EntitlementRecordListOut,
    EntitlementRecordOut,
    OrderCloseIn,
    ProductCreateIn,
    ProductListOut,
    ProductOut,
    ProductStatusIn,
    ProductUpdateIn,
    ReportOut,
    ReportTaskCreateIn,
    ReportTaskListOut,
    ReportTaskOut,
    OrderCreateFromProductIn,
    OrderFailIn,
    VisualTaskCreateIn,
    VisualTaskListOut,
    VisualTaskOut,
)


router = APIRouter(tags=["commerce"])


async def log_admin_action(
    session: AsyncSession,
    admin_user,
    action: str,
    resource_type: str,
    resource_id: int | str | None = None,
    details: dict | None = None,
):
    await AdminOperationLogRepository(session=session).create_log(
        admin_user_id=admin_user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )


@router.get("/products", response_model=list[ProductOut])
async def list_active_products(session: AsyncSession = Depends(get_session)):
    return await ProductRepository(session=session).list_active_products()


@router.post("/orders", response_model=CommerceOrderOut)
async def create_order(
    data: OrderCreateFromProductIn,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    order = await OrderRepository(session=session).create_order_from_product(
        current_user.id,
        data.product_id,
        request_key=data.request_key,
    )
    if not order:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="套餐不存在或已下架")
    return order


@router.get("/orders", response_model=CommerceOrderListOut)
async def list_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    pay_status: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    if pay_status and pay_status not in ORDER_STATUSES:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="订单状态不合法")
    return await OrderRepository(session=session).list_user_orders(
        current_user.id,
        page=page,
        page_size=page_size,
        pay_status=pay_status,
    )


@router.get("/orders/{order_id}", response_model=CommerceOrderOut)
async def get_my_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    order = await OrderRepository(session=session).get_user_order(current_user.id, order_id)
    if not order:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="订单不存在")
    return order


@router.post("/orders/{order_id}/mock-pay-success", response_model=CommerceOrderOut)
async def mock_pay_order_success(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    try:
        order = await OrderRepository(session=session).mark_paid(current_user.id, order_id)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc))
    if not order:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="订单不存在")
    return order


@router.post("/orders/{order_id}/alipay-sandbox/success", response_model=CommerceOrderOut)
async def alipay_sandbox_pay_success(
    order_id: int,
    data: AlipaySandboxSuccessIn,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    try:
        order = await OrderRepository(session=session).mark_paid(
            current_user.id,
            order_id,
            provider="alipay_sandbox",
            trade_no=data.trade_no,
            callback_data=data.callback_data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc))
    if not order:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="订单不存在")
    return order


@router.post("/orders/{order_id}/mock-pay-fail", response_model=CommerceOrderOut)
async def mock_pay_order_fail(
    order_id: int,
    data: OrderFailIn,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    try:
        order = await OrderRepository(session=session).mark_failed(current_user.id, order_id, data.reason)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc))
    if not order:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="订单不存在")
    return order


@router.post("/orders/{order_id}/alipay-sandbox/fail", response_model=CommerceOrderOut)
async def alipay_sandbox_pay_fail(
    order_id: int,
    data: AlipaySandboxFailIn,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    try:
        order = await OrderRepository(session=session).mark_failed(
            current_user.id,
            order_id,
            reason=data.reason or "alipay sandbox payment failed",
            provider="alipay_sandbox",
            trade_no=data.trade_no,
            callback_data=data.callback_data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc))
    if not order:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="订单不存在")
    return order


@router.post("/orders/{order_id}/close", response_model=CommerceOrderOut)
async def close_my_order(
    order_id: int,
    data: OrderCloseIn,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    try:
        order = await OrderRepository(session=session).close_order(current_user.id, order_id, data.reason)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc))
    if not order:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="订单不存在")
    return order


@router.get("/entitlements/accounts", response_model=list[EntitlementAccountOut])
async def list_my_entitlement_accounts(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    return await EntitlementRepository(session=session).list_accounts(current_user.id)


@router.get("/entitlements/records", response_model=EntitlementRecordListOut)
async def list_my_entitlement_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entitlement_type: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    return await EntitlementRepository(session=session).list_records(
        page=page,
        page_size=page_size,
        user_id=current_user.id,
        entitlement_type=entitlement_type,
    )


@router.post("/reports/tasks", response_model=ReportTaskOut)
async def create_report_task(
    data: ReportTaskCreateIn,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    task = await ReportRepository(session=session).create_report_task(
        user_id=current_user.id,
        record_id=data.record_id,
        candidate_id=data.candidate_id,
        report_version=data.report_version,
    )
    if not task:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="起名记录或候选名字不存在")
    return task


@router.get("/reports/tasks", response_model=ReportTaskListOut)
async def list_my_report_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    if status and status not in REPORT_STATUSES:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="报告任务状态不合法")
    return await ReportRepository(session=session).list_user_tasks(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
    )


@router.get("/reports/tasks/{task_id}", response_model=ReportTaskOut)
async def get_my_report_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    task = await ReportRepository(session=session).get_user_task(current_user.id, task_id)
    if not task:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="报告任务不存在")
    return task


@router.get("/reports/tasks/{task_id}/report", response_model=ReportOut)
async def get_my_report_detail(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    report = await ReportRepository(session=session).get_user_report(current_user.id, task_id)
    if not report:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="报告不存在或尚未生成")
    return report


@router.post("/reports/tasks/{task_id}/retry", response_model=ReportTaskOut)
async def retry_my_report_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    try:
        task = await ReportRepository(session=session).retry_user_task(current_user.id, task_id)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc))
    if not task:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="报告任务不存在")
    return task


@router.post("/visual/tasks", response_model=VisualTaskOut)
async def create_visual_task(
    data: VisualTaskCreateIn,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    if data.task_type not in VISUAL_TASK_TYPES:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="视觉任务类型不合法")
    task = await VisualGenerationRepository(session=session).create_task(
        user_id=current_user.id,
        record_id=data.record_id,
        candidate_id=data.candidate_id,
        task_type=data.task_type,
        prompt=data.prompt,
        provider=data.provider,
    )
    if not task:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="起名记录或候选名字不存在")
    return task


@router.get("/visual/tasks", response_model=VisualTaskListOut)
async def list_my_visual_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    if status and status not in VISUAL_STATUSES:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="视觉任务状态不合法")
    return await VisualGenerationRepository(session=session).list_user_tasks(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
    )


@router.get("/visual/tasks/{task_id}", response_model=VisualTaskOut)
async def get_my_visual_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    task = await VisualGenerationRepository(session=session).get_user_task(current_user.id, task_id)
    if not task:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="视觉任务不存在")
    return task


@router.post("/visual/tasks/{task_id}/retry", response_model=VisualTaskOut)
async def retry_my_visual_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    try:
        task = await VisualGenerationRepository(session=session).retry_user_task(current_user.id, task_id)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc))
    if not task:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="视觉任务不存在")
    return task


@router.delete("/visual/tasks/{task_id}")
async def delete_my_visual_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    deleted = await VisualGenerationRepository(session=session).delete_user_task(current_user.id, task_id)
    if not deleted:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="视觉任务不存在")
    return {"message": "视觉任务已删除"}


@router.get("/admin/products", response_model=ProductListOut)
async def admin_list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None),
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    return await ProductRepository(session=session).list_products(
        page=page,
        page_size=page_size,
        is_active=is_active,
    )


@router.get("/admin/orders", response_model=CommerceOrderListOut)
async def admin_list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    pay_status: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    if pay_status and pay_status not in ORDER_STATUSES:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="订单状态不合法")
    return await OrderRepository(session=session).list_all_orders(
        page=page,
        page_size=page_size,
        pay_status=pay_status,
    )


@router.get("/admin/commercial/stats", response_model=AdminCommercialFailureStatsOut)
async def admin_get_commercial_failure_stats(
    recent_limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    return await AdminCommercialStatsRepository(session=session).get_failure_stats(recent_limit=recent_limit)


@router.get("/admin/visual/tasks", response_model=VisualTaskListOut)
async def admin_list_visual_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    if status and status not in VISUAL_STATUSES:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="视觉任务状态不合法")
    return await VisualGenerationRepository(session=session).list_all_tasks(page=page, page_size=page_size, status=status)


@router.get("/admin/visual/tasks/{task_id}", response_model=VisualTaskOut)
async def admin_get_visual_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    task = await VisualGenerationRepository(session=session).get_task(task_id)
    if not task:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="视觉任务不存在")
    return task


@router.get("/admin/reports/tasks", response_model=ReportTaskListOut)
async def admin_list_report_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    if status and status not in REPORT_STATUSES:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="报告任务状态不合法")
    return await ReportRepository(session=session).list_all_tasks(page=page, page_size=page_size, status=status)


@router.get("/admin/reports/tasks/{task_id}", response_model=ReportTaskOut)
async def admin_get_report_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    task = await ReportRepository(session=session).get_task(task_id)
    if not task:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="报告任务不存在")
    return task


@router.get("/admin/reports/tasks/{task_id}/report", response_model=ReportOut)
async def admin_get_report_detail(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    report = await ReportRepository(session=session).get_report(task_id)
    if not report:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="报告不存在或尚未生成")
    return report


@router.get("/admin/entitlements/accounts", response_model=list[EntitlementAccountOut])
async def admin_list_entitlement_accounts(
    user_id: int = Query(..., ge=1),
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    return await EntitlementRepository(session=session).list_accounts(user_id)


@router.get("/admin/entitlements/records", response_model=EntitlementRecordListOut)
async def admin_list_entitlement_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int | None = Query(None, ge=1),
    entitlement_type: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    return await EntitlementRepository(session=session).list_records(
        page=page,
        page_size=page_size,
        user_id=user_id,
        entitlement_type=entitlement_type,
    )


@router.post("/admin/entitlements/adjust", response_model=EntitlementRecordOut)
async def admin_adjust_entitlement(
    data: AdminEntitlementAdjustIn,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    record = await EntitlementRepository(session=session).admin_adjust(
        user_id=data.user_id,
        entitlement_type=data.entitlement_type,
        amount=data.change_amount,
        valid_days=data.valid_days,
        remark=data.remark,
    )
    if not record:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="权益调整失败，余额不足或调整数量为0")
    await log_admin_action(
        session,
        admin_user,
        action="adjust_entitlement",
        resource_type="entitlement",
        resource_id=record.id,
        details={
            "user_id": data.user_id,
            "entitlement_type": data.entitlement_type,
            "change_amount": data.change_amount,
            "valid_days": data.valid_days,
        },
    )
    return record


@router.post("/admin/orders/close-expired")
async def admin_close_expired_orders(
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    count = await OrderRepository(session=session).close_expired_orders()
    await log_admin_action(
        session,
        admin_user,
        action="close_expired_orders",
        resource_type="order",
        details={"count": count},
    )
    return {"message": "过期订单已关闭", "count": count}


@router.get("/admin/orders/{order_id}", response_model=CommerceOrderOut)
async def admin_get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    order = await OrderRepository(session=session).get_order(order_id)
    if not order:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="订单不存在")
    return order


@router.post("/admin/products", response_model=ProductOut)
async def admin_create_product(
    data: ProductCreateIn,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    repository = ProductRepository(session=session)
    if await repository.code_exists(data.code):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="套餐编码已存在")
    product = await repository.create_product(data.model_dump())
    await log_admin_action(
        session,
        admin_user,
        action="create_product",
        resource_type="product",
        resource_id=product.id,
        details={"code": product.code, "name": product.name},
    )
    return product


@router.patch("/admin/products/{product_id}", response_model=ProductOut)
async def admin_update_product(
    product_id: int,
    data: ProductUpdateIn,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="没有需要修改的字段")

    repository = ProductRepository(session=session)
    if "code" in update_data and await repository.code_exists(update_data["code"], exclude_product_id=product_id):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="套餐编码已存在")

    product = await repository.update_product(product_id, update_data)
    if not product:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="套餐不存在")
    await log_admin_action(
        session,
        admin_user,
        action="update_product",
        resource_type="product",
        resource_id=product_id,
        details={"fields": sorted(update_data.keys())},
    )
    return product


@router.post("/payments/alipay/callback")
async def alipay_payment_callback(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    payload = await _read_callback_payload(request)
    if not _verify_alipay_callback_signature(request, payload):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="支付宝回调签名校验失败")

    order_no = payload.get("out_trade_no")
    if not order_no:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="缺少 out_trade_no")

    trade_status = payload.get("trade_status")
    trade_no = payload.get("trade_no")
    repository = OrderRepository(session=session)
    try:
        if trade_status in {"TRADE_SUCCESS", "TRADE_FINISHED"}:
            order = await repository.mark_paid_by_order_no(
                order_no=order_no,
                provider="alipay_sandbox",
                trade_no=trade_no,
                callback_data=payload,
            )
        elif trade_status in {"TRADE_CLOSED", "TRADE_FAILED"}:
            order = await repository.mark_failed_by_order_no(
                order_no=order_no,
                provider="alipay_sandbox",
                reason=f"alipay callback status: {trade_status}",
                trade_no=trade_no,
                callback_data=payload,
            )
        else:
            return {"message": "ignored", "trade_status": trade_status}
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc))

    if not order:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="订单不存在")
    return {"message": "success", "order_no": order.order_no, "pay_status": order.pay_status}


async def _read_callback_payload(request: Request) -> dict:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        data = await request.json()
        return dict(data)
    form = await request.form()
    return dict(form)


def _verify_alipay_callback_signature(request: Request, payload: dict) -> bool:
    expected_secret = os.getenv("ALIPAY_SANDBOX_CALLBACK_SECRET")
    if not expected_secret:
        return True
    provided_signature = request.headers.get("x-alipay-sandbox-signature") or payload.get("sign")
    if not provided_signature:
        return False
    if hmac.compare_digest(provided_signature, expected_secret):
        return True

    signing_payload = "&".join(
        f"{key}={json.dumps(payload[key], ensure_ascii=False, sort_keys=True) if isinstance(payload[key], (dict, list)) else payload[key]}"
        for key in sorted(payload)
        if key != "sign"
    )
    expected_signature = hmac.new(
        expected_secret.encode("utf-8"),
        signing_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(provided_signature, expected_signature)


@router.post("/admin/products/{product_id}/status", response_model=ProductOut)
async def admin_update_product_status(
    product_id: int,
    data: ProductStatusIn,
    session: AsyncSession = Depends(get_session),
    admin_user=Depends(get_admin_user),
):
    product = await ProductRepository(session=session).set_product_active(product_id, data.is_active)
    if not product:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="套餐不存在")
    await log_admin_action(
        session,
        admin_user,
        action="set_product_active" if data.is_active else "set_product_inactive",
        resource_type="product",
        resource_id=product_id,
        details={"is_active": data.is_active},
    )
    return product
