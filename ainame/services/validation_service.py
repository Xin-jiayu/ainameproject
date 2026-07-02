import asyncio

from fastapi import HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.tools import check_com_domain
from repository.phase_two_repo import PhaseTwoRepository


class ValidationService:
    """Candidate, domain, trademark, and social validation use cases."""

    def __init__(self, session: AsyncSession):
        self.repository = PhaseTwoRepository(session=session)

    async def create_candidates_from_result(self, record_id: int, result_data: dict):
        return await self.repository.create_candidates_from_result(record_id, result_data)

    async def replace_candidates_from_result(self, record_id: int, result_data: dict):
        return await self.repository.replace_candidates_from_result(record_id, result_data)

    async def list_candidates(self, user_id: int, record_id: int):
        try:
            return await self.repository.list_candidates(user_id, record_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="record not found")

    async def favorite_candidate(self, user_id: int, candidate_id: int):
        candidate = await self.repository.set_candidate_favorite(user_id, candidate_id, True)
        if not candidate:
            raise HTTPException(status_code=404, detail="candidate not found")
        return candidate

    async def unfavorite_candidate(self, user_id: int, candidate_id: int):
        candidate = await self.repository.set_candidate_favorite(user_id, candidate_id, False)
        if not candidate:
            raise HTTPException(status_code=404, detail="candidate not found")
        return candidate

    async def select_candidate(self, user_id: int, candidate_id: int):
        candidate = await self.repository.select_candidate(user_id, candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="candidate not found")
        return candidate

    async def update_candidate_score(
        self,
        user_id: int,
        candidate_id: int,
        score: int,
        score_detail: dict | None,
        score_reason: str | None,
    ):
        candidate = await self.repository.update_candidate_score(
            user_id,
            candidate_id,
            score,
            score_detail,
            score_reason,
        )
        if not candidate:
            raise HTTPException(status_code=404, detail="candidate not found")
        return candidate

    async def create_domain_checks(self, user_id: int, record_id: int, suffixes: list[str] | None = None):
        suffixes = suffixes or ["com", "cn", "ai"]
        candidates = await self.list_candidates(user_id, record_id)
        if not candidates:
            raise HTTPException(status_code=400, detail="no candidates for this record")

        checks = []
        for candidate in candidates:
            for suffix in suffixes:
                domain = self.domain_for_suffix(candidate.domain or f"candidate-{candidate.id}", suffix)
                checked_domain, check_status = await self.check_domain(domain, suffix)
                checks.append(
                    {
                        "record_id": int(record_id),
                        "candidate_id": candidate.id,
                        "domain": checked_domain or domain,
                        "suffix": suffix.lstrip(".").lower(),
                        "check_status": check_status,
                        "raw_result": {"provider": "whois" if suffix.lstrip(".").lower() == "com" else "mock"},
                    }
                )
        return await self.repository.save_domain_checks(user_id, record_id, checks)

    async def list_domain_checks(self, user_id: int, record_id: int):
        try:
            return await self.repository.list_domain_checks(user_id, record_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="record not found")

    async def create_trademark_checks(self, user_id: int, record_id: int):
        try:
            return await self.repository.create_trademark_checks(user_id, record_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="record not found")

    async def list_trademark_checks(self, user_id: int, record_id: int):
        try:
            return await self.repository.list_trademark_checks(user_id, record_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="record not found")

    async def create_social_checks(self, user_id: int, record_id: int):
        try:
            return await self.repository.create_social_checks(user_id, record_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="record not found")

    async def list_social_checks(self, user_id: int, record_id: int):
        try:
            return await self.repository.list_social_checks(user_id, record_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="record not found")

    def domain_for_suffix(self, value: str, suffix: str) -> str:
        suffix = suffix.lstrip(".").lower()
        domain = (value or "").strip().lower().replace(" ", "")
        if not domain.isascii():
            domain = "ainame"
        if "." in domain:
            domain = domain.rsplit(".", 1)[0]
        if not domain:
            domain = "ainame"
        return f"{domain}.{suffix}"

    async def check_domain(self, domain: str, suffix: str) -> tuple[str | None, str]:
        suffix = suffix.lstrip(".").lower()
        if suffix == "com":
            result = await check_com_domain(domain)
            return result.domain, result.status
        await asyncio.sleep(0)
        return domain, "mock_pending_real_provider"
