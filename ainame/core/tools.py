import asyncio
import re
from dataclasses import dataclass


DOMAIN_QUERY_UNAVAILABLE = "域名查询暂不可用"
DOMAIN_QUERY_TIMEOUT = "域名查询超时，请稍后重试"
DOMAIN_AVAILABLE = "未注册（可购买）"
DOMAIN_TAKEN = "已注册"
DOMAIN_INVALID = "域名格式不正确"
DOMAIN_SUFFIX_UNSUPPORTED = "仅支持 .com 域名校验"

_DOMAIN_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


@dataclass(frozen=True)
class DomainCheckResult:
    domain: str | None
    status: str


def normalize_com_domain(raw_domain: str | None) -> DomainCheckResult:
    """Normalize AI-generated domain text before querying whois."""
    if not raw_domain:
        return DomainCheckResult(None, DOMAIN_INVALID)

    domain = str(raw_domain).strip().lower()
    domain = re.sub(r"\s+", "", domain)
    domain = re.sub(r"^https?://", "", domain)
    domain = re.sub(r"^www\.", "", domain)
    domain = domain.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0].strip(".")

    if not domain:
        return DomainCheckResult(None, DOMAIN_INVALID)
    if "." not in domain:
        domain = f"{domain}.com"
    elif not domain.endswith(".com"):
        return DomainCheckResult(domain, DOMAIN_SUFFIX_UNSUPPORTED)

    labels = domain.split(".")
    if labels[-1] != "com" or len(labels) < 2 or len(domain) > 253:
        return DomainCheckResult(domain, DOMAIN_INVALID)
    if any(not _DOMAIN_LABEL_RE.match(label) for label in labels[:-1]):
        return DomainCheckResult(domain, DOMAIN_INVALID)

    return DomainCheckResult(domain, "pending")


async def check_com_domain(domain: str | None) -> DomainCheckResult:
    normalized = normalize_com_domain(domain)
    if normalized.status != "pending" or not normalized.domain:
        return normalized

    writer = None
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection("whois.verisign-grs.com", 43),
            timeout=3.0,
        )
        writer.write((normalized.domain + "\r\n").encode("utf-8"))
        await writer.drain()

        response = await asyncio.wait_for(reader.read(), timeout=5.0)
        result = response.decode("utf-8", errors="ignore")

        if "No match for" in result:
            return DomainCheckResult(normalized.domain, DOMAIN_AVAILABLE)
        return DomainCheckResult(normalized.domain, DOMAIN_TAKEN)

    except asyncio.TimeoutError:
        return DomainCheckResult(normalized.domain, DOMAIN_QUERY_TIMEOUT)
    except Exception:
        return DomainCheckResult(normalized.domain, DOMAIN_QUERY_UNAVAILABLE)
    finally:
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
