import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.tools import (
    DOMAIN_AVAILABLE,
    DOMAIN_INVALID,
    DOMAIN_QUERY_TIMEOUT,
    DOMAIN_QUERY_UNAVAILABLE,
    DOMAIN_SUFFIX_UNSUPPORTED,
    DOMAIN_TAKEN,
    check_com_domain,
    normalize_com_domain,
)


class DomainNormalizeTest(unittest.TestCase):
    def test_normalize_strips_spaces_lowercases_and_adds_com(self):
        result = normalize_com_domain("  Qing Lan  ")

        self.assertEqual(result.domain, "qinglan.com")
        self.assertEqual(result.status, "pending")

    def test_normalize_url_and_www_prefix(self):
        result = normalize_com_domain("https://www.QingLan.com/path?q=1")

        self.assertEqual(result.domain, "qinglan.com")
        self.assertEqual(result.status, "pending")

    def test_rejects_non_com_suffix(self):
        result = normalize_com_domain("qinglan.cn")

        self.assertEqual(result.domain, "qinglan.cn")
        self.assertEqual(result.status, DOMAIN_SUFFIX_UNSUPPORTED)

    def test_rejects_invalid_domain(self):
        result = normalize_com_domain("-bad-.com")

        self.assertEqual(result.domain, "-bad-.com")
        self.assertEqual(result.status, DOMAIN_INVALID)


class _FakeWriter:
    def write(self, data):
        self.data = data

    async def drain(self):
        return None

    def close(self):
        return None

    async def wait_closed(self):
        return None


class DomainCheckTest(unittest.IsolatedAsyncioTestCase):
    async def test_available_domain(self):
        reader = AsyncMock()
        reader.read.return_value = b"No match for \"QINGLAN.COM\""

        with patch("asyncio.open_connection", new=AsyncMock(return_value=(reader, _FakeWriter()))):
            result = await check_com_domain("qinglan.com")

        self.assertEqual(result.domain, "qinglan.com")
        self.assertEqual(result.status, DOMAIN_AVAILABLE)

    async def test_taken_domain(self):
        reader = AsyncMock()
        reader.read.return_value = b"Domain Name: QINGLAN.COM"

        with patch("asyncio.open_connection", new=AsyncMock(return_value=(reader, _FakeWriter()))):
            result = await check_com_domain("qinglan.com")

        self.assertEqual(result.domain, "qinglan.com")
        self.assertEqual(result.status, DOMAIN_TAKEN)

    async def test_timeout_status(self):
        with patch("asyncio.open_connection", new=AsyncMock(side_effect=asyncio.TimeoutError)):
            result = await check_com_domain("qinglan.com")

        self.assertEqual(result.domain, "qinglan.com")
        self.assertEqual(result.status, DOMAIN_QUERY_TIMEOUT)

    async def test_network_error_status(self):
        with patch("asyncio.open_connection", new=AsyncMock(side_effect=OSError("offline"))):
            result = await check_com_domain("qinglan.com")

        self.assertEqual(result.domain, "qinglan.com")
        self.assertEqual(result.status, DOMAIN_QUERY_UNAVAILABLE)

    async def test_invalid_domain_skips_network(self):
        with patch("asyncio.open_connection", new=AsyncMock()) as open_connection:
            result = await check_com_domain("bad_domain.com")

        open_connection.assert_not_called()
        self.assertEqual(result.status, DOMAIN_INVALID)


class WorkflowDomainLimitTest(unittest.TestCase):
    def test_company_workflow_limits_domain_checks_to_five(self):
        workflow_source = (Path(__file__).resolve().parents[1] / "core" / "workflow.py").read_text(encoding="utf-8")

        self.assertIn("max_checks: int = 5", workflow_source)
        self.assertIn("[:max_checks]", workflow_source)
        self.assertIn("await _check_company_domains(response)", workflow_source)


if __name__ == "__main__":
    unittest.main()
