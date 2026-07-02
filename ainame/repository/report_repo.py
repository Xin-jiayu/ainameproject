from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio.session import AsyncSession

import settings
from models.business import NameCandidate, NameRecord, Report, ReportTask


REPORT_PENDING = "pending"
REPORT_PROCESSING = "processing"
REPORT_SUCCESS = "success"
REPORT_FAILED = "failed"
REPORT_STATUSES = {REPORT_PENDING, REPORT_PROCESSING, REPORT_SUCCESS, REPORT_FAILED}


class ReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_report_task(
        self,
        user_id: int,
        record_id: int,
        candidate_id: int | None = None,
        report_version: str = "v1",
    ):
        try:
            record = await self._get_user_record(user_id, record_id)
            if not record:
                return None
            candidate = None
            if candidate_id is not None:
                candidate = await self._get_record_candidate(record_id, candidate_id)
                if not candidate:
                    return None

            data_source = self._build_data_source(record, candidate)
            task = ReportTask(
                user_id=int(user_id),
                record_id=int(record_id),
                candidate_id=candidate.id if candidate else None,
                status=REPORT_PROCESSING,
                report_version=report_version,
                data_source=data_source,
            )
            self.session.add(task)
            await self.session.flush()

            report = Report(
                task_id=task.id,
                user_id=int(user_id),
                record_id=int(record_id),
                candidate_id=candidate.id if candidate else None,
                report_version=report_version,
                data_source=data_source,
                content=self._build_mock_report(record, candidate, report_version),
            )
            self.session.add(report)
            task.status = REPORT_SUCCESS
            task.generated_at = datetime.now()
            await self.session.commit()
            await self.session.refresh(task)
            return task
        except Exception:
            await self.session.rollback()
            raise

    async def list_user_tasks(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ):
        return await self._list_tasks(page=page, page_size=page_size, user_id=int(user_id), status=status)

    async def list_all_tasks(self, page: int = 1, page_size: int = 20, status: str | None = None):
        return await self._list_tasks(page=page, page_size=page_size, status=status)

    async def get_user_task(self, user_id: int, task_id: int):
        return await self.session.scalar(
            select(ReportTask).where(ReportTask.id == int(task_id), ReportTask.user_id == int(user_id))
        )

    async def get_task(self, task_id: int):
        return await self.session.scalar(select(ReportTask).where(ReportTask.id == int(task_id)))

    async def get_user_report(self, user_id: int, task_id: int):
        return await self.session.scalar(
            select(Report).where(Report.task_id == int(task_id), Report.user_id == int(user_id))
        )

    async def get_report(self, task_id: int):
        return await self.session.scalar(select(Report).where(Report.task_id == int(task_id)))

    async def retry_user_task(self, user_id: int, task_id: int):
        try:
            task = await self.session.scalar(
                select(ReportTask)
                .where(ReportTask.id == int(task_id), ReportTask.user_id == int(user_id))
                .with_for_update()
            )
            if not task:
                return None
            if task.status != REPORT_FAILED:
                return task
            if task.retry_count >= settings.TASK_MAX_RETRIES:
                raise ValueError("report task retry limit reached")

            record = await self._get_user_record(user_id, task.record_id)
            candidate = await self._get_record_candidate(task.record_id, task.candidate_id) if task.candidate_id else None
            task.status = REPORT_PROCESSING
            task.retry_count += 1
            task.error_message = None
            task.data_source = self._build_data_source(record, candidate)
            report = await self.session.scalar(select(Report).where(Report.task_id == task.id))
            if report:
                report.data_source = task.data_source
                report.content = self._build_mock_report(record, candidate, task.report_version)
                report.created_at = datetime.now()
            else:
                self.session.add(
                    Report(
                        task_id=task.id,
                        user_id=task.user_id,
                        record_id=task.record_id,
                        candidate_id=task.candidate_id,
                        report_version=task.report_version,
                        data_source=task.data_source,
                        content=self._build_mock_report(record, candidate, task.report_version),
                    )
                )
            task.status = REPORT_SUCCESS
            task.generated_at = datetime.now()
            await self.session.commit()
            await self.session.refresh(task)
            return task
        except Exception:
            await self.session.rollback()
            raise

    async def _list_tasks(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: int | None = None,
        status: str | None = None,
    ):
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        total_stmt = select(func.count()).select_from(ReportTask)
        list_stmt = select(ReportTask).order_by(desc(ReportTask.created_at), desc(ReportTask.id))
        if user_id is not None:
            total_stmt = total_stmt.where(ReportTask.user_id == int(user_id))
            list_stmt = list_stmt.where(ReportTask.user_id == int(user_id))
        if status:
            total_stmt = total_stmt.where(ReportTask.status == status)
            list_stmt = list_stmt.where(ReportTask.status == status)
        total = await self.session.scalar(total_stmt)
        result = await self.session.execute(list_stmt.offset((page - 1) * page_size).limit(page_size))
        return {
            "items": result.scalars().all(),
            "total": total or 0,
            "page": page,
            "page_size": page_size,
        }

    async def _get_user_record(self, user_id: int, record_id: int):
        return await self.session.scalar(
            select(NameRecord).where(
                NameRecord.id == int(record_id),
                NameRecord.user_id == int(user_id),
                NameRecord.is_deleted.is_(False),
            )
        )

    async def _get_record_candidate(self, record_id: int, candidate_id: int | None):
        if candidate_id is None:
            return None
        return await self.session.scalar(
            select(NameCandidate).where(
                NameCandidate.id == int(candidate_id),
                NameCandidate.record_id == int(record_id),
            )
        )

    def _build_data_source(self, record: NameRecord, candidate: NameCandidate | None):
        return {
            "mode": "mock_until_member_c_ready",
            "record_id": record.id,
            "candidate_id": candidate.id if candidate else None,
            "uses_final_ai_score": False,
            "uses_final_trademark_risk": False,
            "uses_final_social_risk": False,
            "generated_from": ["name_record", "name_candidate", "mock_report_template"],
        }

    def _build_mock_report(self, record: NameRecord, candidate: NameCandidate | None, report_version: str):
        candidate_name = candidate.name if candidate else self._pick_name_from_record(record)
        return {
            "report_version": report_version,
            "is_mock": True,
            "name": candidate_name,
            "summary": {
                "overall_score": 82,
                "conclusion": f"{candidate_name} 具备较好的传播基础，适合作为当前阶段的候选名称继续打磨。",
            },
            "sections": {
                "overall_evaluation": "名称简洁、识别度较好，后续需要结合最终校验矩阵确认风险。",
                "phonetic_analysis": "读音节奏较顺，便于口头传播。此项为 Mock 评估。",
                "cultural_meaning": candidate.moral if candidate and candidate.moral else "寓意积极，具体文化解释等待成员 C 最终结构补齐。",
                "requirement_match": "与用户输入需求具备中高匹配度。此处暂不依赖最终 AI 评分结构。",
                "domain_matrix": {"status": "mock", "items": []},
                "trademark_risk": {"risk_level": "unknown", "source": "mock"},
                "social_duplicate_risk": {"risk_level": "unknown", "source": "mock"},
                "usage_suggestions": ["保留为重点候选", "等待域名、商标、社媒最终校验后再定稿"],
            },
            "data_source_note": "成员 C 第二阶段未完成前，本报告为 Mock 数据，不作为最终商业决策依据。",
        }

    def _pick_name_from_record(self, record: NameRecord):
        names = (record.result_data or {}).get("names") or []
        if names and isinstance(names[0], dict) and names[0].get("name"):
            return names[0]["name"]
        return record.title or f"record-{record.id}"
