"""Tests for the funding status message shared by send_money and fund_transfer."""

from wise_mcp.api.types import WiseFundResponse, WiseFundWithScaResponse, WiseScaResponse
from wise_mcp.resources.transfers import describe_fund_result


def test_completed_funding():
    result = WiseFundWithScaResponse(fund_response=WiseFundResponse(type="BALANCE", status="COMPLETED"))

    assert describe_fund_result("1", result) == "Transfer 1 successfully sent"


def test_sca_challenge_reports_token():
    result = WiseFundWithScaResponse(sca_response=WiseScaResponse(one_time_token="ott-9"))

    assert "requires SCA" in describe_fund_result("1", result)
    assert "ott-9" in describe_fund_result("1", result)


def test_rejected_funding_reports_error_code():
    result = WiseFundWithScaResponse(
        fund_response=WiseFundResponse(type="BALANCE", status="REJECTED", error_code="balance.insufficient")
    )

    assert describe_fund_result("1", result) == "Transfer 1 failed due to balance.insufficient"
