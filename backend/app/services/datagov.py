import asyncio
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field
from app.config import settings

logger = logging.getLogger(__name__)

class DataGovError(Exception):
    """Base exception for data.gov.in service."""
    pass

class DataGovAPIError(DataGovError):
    """Exception for API HTTP or response payload errors."""
    def __init__(self, status_code: int, message: str):
        super().__init__(f"data.gov.in API error ({status_code}): {message}")
        self.status_code = status_code

class DataGovRateLimitError(DataGovError):
    """Exception raised when rate limit or quota is exceeded."""
    pass

class DataGovParseError(DataGovError):
    """Exception raised when records cannot be parsed."""
    pass

class DataGovRecord(BaseModel):
    state: str
    district: str
    market: str
    commodity: str
    variety: str = "Default"
    grade: str = "FAQ"
    arrival_date: date
    min_price: Optional[Decimal] = None
    modal_price: Decimal
    max_price: Optional[Decimal] = None

def parse_decimal(val: Any) -> Optional[Decimal]:
    if val is None:
        return None
    val_str = str(val).strip()
    if not val_str or val_str.upper() in ("NA", "N/A", "NULL", "NONE", "-"):
        return None
    try:
        # Remove commas if any, e.g. "2,500"
        sanitized = val_str.replace(",", "")
        d = Decimal(sanitized)
        return d if d > 0 else None
    except InvalidOperation:
        return None

def parse_arrival_date(val: Any) -> date:
    val_str = str(val).strip()
    # Format from data.gov.in: dd/mm/yyyy
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    raise DataGovParseError(f"Cannot parse arrival_date: {val_str}")

def parse_record(raw: Dict[str, Any]) -> Optional[DataGovRecord]:
    modal_price = parse_decimal(raw.get("modal_price"))
    if modal_price is None:
        # Cannot use record without a valid modal price
        return None

    state = str(raw.get("state") or "").strip()
    district = str(raw.get("district") or "").strip()
    market = str(raw.get("market") or "").strip()
    commodity = str(raw.get("commodity") or "").strip()

    if not (state and district and market and commodity):
        return None

    try:
        arrival_date = parse_arrival_date(raw.get("arrival_date"))
    except DataGovParseError:
        return None

    variety = str(raw.get("variety") or "Default").strip()
    grade = str(raw.get("grade") or "FAQ").strip()
    min_price = parse_decimal(raw.get("min_price"))
    max_price = parse_decimal(raw.get("max_price"))

    return DataGovRecord(
        state=state,
        district=district,
        market=market,
        commodity=commodity,
        variety=variety,
        grade=grade,
        arrival_date=arrival_date,
        min_price=min_price,
        modal_price=modal_price,
        max_price=max_price,
    )

class DataGovClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        resource_id: Optional[str] = None,
        timeout: float = 10.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key or settings.DATA_GOV_API_KEY
        self.resource_id = resource_id or settings.DATAGOV_RESOURCE_ID
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = f"https://api.data.gov.in/resource/{self.resource_id}"

    async def _make_request(
        self, client: httpx.AsyncClient, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = await client.get(
                    self.base_url,
                    params=params,
                    timeout=httpx.Timeout(self.timeout, connect=5.0),
                )
                if response.status_code == 429:
                    raise DataGovRateLimitError("data.gov.in rate limit exceeded")
                if response.status_code != 200:
                    raise DataGovAPIError(response.status_code, response.text[:300])

                try:
                    data = response.json()
                except Exception as e:
                    raise DataGovParseError(f"Response is not valid JSON: {e}")

                return data
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exception = exc
                wait_time = 0.5 * (2 ** attempt)
                logger.warning(
                    f"data.gov.in request attempt {attempt + 1} failed ({type(exc).__name__}). Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            except DataGovError:
                raise
            except Exception as exc:
                last_exception = exc
                break

        raise DataGovAPIError(
            504,
            f"Failed to fetch data from data.gov.in after {self.max_retries} attempts: {last_exception}",
        )

    async def fetch_page(
        self,
        client: httpx.AsyncClient,
        state: Optional[str] = None,
        commodity: Optional[str] = None,
        limit: int = 500,
        offset: int = 0,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "api-key": self.api_key,
            "format": "json",
            "limit": limit,
            "offset": offset,
        }
        if state:
            params["filters[state.keyword]"] = state
        if commodity:
            params["filters[commodity]"] = commodity

        return await self._make_request(client, params)

    async def fetch_records(
        self,
        state: Optional[str] = None,
        commodity: Optional[str] = None,
        page_size: int = 500,
        max_records: Optional[int] = None,
    ) -> List[DataGovRecord]:
        results: List[DataGovRecord] = []
        offset = 0

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MandiArbitrageAdvisor/0.01.00",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(headers=headers) as client:
            while True:
                data = await self.fetch_page(
                    client=client,
                    state=state,
                    commodity=commodity,
                    limit=page_size,
                    offset=offset,
                )
                raw_records = data.get("records", [])
                if not raw_records:
                    break

                for r in raw_records:
                    parsed = parse_record(r)
                    if parsed is not None:
                        results.append(parsed)
                        if max_records and len(results) >= max_records:
                            return results

                total = data.get("total", 0)
                offset += len(raw_records)
                if offset >= total or len(raw_records) < page_size:
                    break

        return results
