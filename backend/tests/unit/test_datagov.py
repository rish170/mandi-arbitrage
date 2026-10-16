from datetime import date
from decimal import Decimal
import pytest
import respx
import httpx

from app.services.datagov import (
    DataGovAPIError,
    DataGovClient,
    DataGovParseError,
    DataGovRateLimitError,
    parse_arrival_date,
    parse_decimal,
    parse_record,
)

def test_parse_decimal():
    assert parse_decimal("2500") == Decimal("2500")
    assert parse_decimal("2,500.50") == Decimal("2500.50")
    assert parse_decimal("NA") is None
    assert parse_decimal("N/A") is None
    assert parse_decimal("-") is None
    assert parse_decimal("") is None
    assert parse_decimal(None) is None
    assert parse_decimal("0") is None  # Prices should be positive

def test_parse_arrival_date():
    assert parse_arrival_date("16/10/2026") == date(2026, 10, 16)
    assert parse_arrival_date("2026-10-16") == date(2026, 10, 16)
    assert parse_arrival_date("16-10-2026") == date(2026, 10, 16)
    with pytest.raises(DataGovParseError):
        parse_arrival_date("invalid-date")

def test_parse_valid_record():
    raw = {
        "state": "Maharashtra",
        "district": "Pune",
        "market": "Pune APMC",
        "commodity": "Wheat",
        "variety": "Lokwan",
        "grade": "FAQ",
        "arrival_date": "16/10/2026",
        "min_price": "2400",
        "modal_price": "2550",
        "max_price": "2700",
    }
    rec = parse_record(raw)
    assert rec is not None
    assert rec.state == "Maharashtra"
    assert rec.district == "Pune"
    assert rec.market == "Pune APMC"
    assert rec.commodity == "Wheat"
    assert rec.variety == "Lokwan"
    assert rec.modal_price == Decimal("2550")
    assert rec.min_price == Decimal("2400")
    assert rec.max_price == Decimal("2700")
    assert rec.arrival_date == date(2026, 10, 16)

def test_parse_record_missing_modal_price():
    raw = {
        "state": "Maharashtra",
        "district": "Pune",
        "market": "Pune APMC",
        "commodity": "Wheat",
        "arrival_date": "16/10/2026",
        "modal_price": "NA",
    }
    assert parse_record(raw) is None

def test_parse_record_missing_required_fields():
    raw = {
        "state": "",
        "district": "Pune",
        "market": "Pune APMC",
        "commodity": "Wheat",
        "modal_price": "2500",
        "arrival_date": "16/10/2026",
    }
    assert parse_record(raw) is None

@pytest.mark.asyncio
@respx.mock
async def test_datagov_client_successful_fetch():
    client = DataGovClient(api_key="mock_key", resource_id="mock_res", timeout=5.0)
    mock_payload = {
        "total": 1,
        "count": 1,
        "records": [
            {
                "state": "Maharashtra",
                "district": "Pune",
                "market": "Pune",
                "commodity": "Wheat",
                "variety": "Other",
                "grade": "FAQ",
                "arrival_date": "16/10/2026",
                "modal_price": 2500,
            }
        ],
    }
    respx.get("https://api.data.gov.in/resource/mock_res").mock(
        return_value=httpx.Response(200, json=mock_payload)
    )

    records = await client.fetch_records(state="Maharashtra", commodity="Wheat")
    assert len(records) == 1
    assert records[0].commodity == "Wheat"
    assert records[0].modal_price == Decimal("2500")

@pytest.mark.asyncio
@respx.mock
async def test_datagov_client_rate_limit():
    client = DataGovClient(api_key="mock_key", resource_id="mock_res", timeout=2.0, max_retries=1)
    respx.get("https://api.data.gov.in/resource/mock_res").mock(
        return_value=httpx.Response(429, text="Rate limit exceeded")
    )
    with pytest.raises(DataGovRateLimitError):
        await client.fetch_records(state="Maharashtra")

@pytest.mark.asyncio
@respx.mock
async def test_datagov_client_http_error():
    client = DataGovClient(api_key="mock_key", resource_id="mock_res", timeout=2.0, max_retries=1)
    respx.get("https://api.data.gov.in/resource/mock_res").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    with pytest.raises(DataGovAPIError) as exc_info:
        await client.fetch_records(state="Maharashtra")
    assert exc_info.value.status_code == 500
