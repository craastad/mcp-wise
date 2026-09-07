"""Tests for profile resolution and the list_profiles summary."""

import pytest

from tests.conftest import make_response
from wise_mcp.api.types import WiseProfileSummary
from wise_mcp.api.wise_client_helper import init_wise_client

PERSONAL = {"id": 100, "type": "PERSONAL", "firstName": "Ada", "lastName": "Lovelace", "fullName": "Ada Lovelace"}
BUSINESS = {"id": 200, "type": "BUSINESS", "businessName": "Acme LLC", "fullName": "Ada Lovelace"}
V1_PERSONAL = {"id": 300, "type": "personal", "details": {"firstName": "Ada", "lastName": "Lovelace"}}
V1_BUSINESS = {"id": 400, "type": "business", "details": {"name": "Acme LLC", "companyType": "LIMITED_LIABILITY_COMPANY"}}


@pytest.fixture
def no_default_profile(monkeypatch):
    monkeypatch.delenv("WISE_PROFILE_ID", raising=False)


def test_explicit_profile_id_skips_profiles_call(mock_request, no_default_profile):
    ctx = init_wise_client("personal", profile_id="555")

    assert ctx.profile.profile_id == "555"
    mock_request.assert_not_called()


def test_env_profile_id_used_when_no_arg(monkeypatch, mock_request):
    monkeypatch.setenv("WISE_PROFILE_ID", "200")

    ctx = init_wise_client("personal")

    assert ctx.profile.profile_id == "200"
    mock_request.assert_not_called()


def test_explicit_profile_id_wins_over_env(monkeypatch, mock_request):
    monkeypatch.setenv("WISE_PROFILE_ID", "200")

    assert init_wise_client(profile_id="100").profile.profile_id == "100"


def test_profile_type_match_is_case_insensitive(mock_request, no_default_profile):
    mock_request.return_value = make_response(200, [PERSONAL, BUSINESS])

    ctx = init_wise_client("business")

    assert ctx.profile.profile_id == "200"
    args, _ = mock_request.call_args
    assert args[0] == "GET"
    assert args[1].endswith("/v2/profiles")


def test_no_matching_type_lists_available_profiles(mock_request, no_default_profile):
    mock_request.return_value = make_response(200, [PERSONAL])

    with pytest.raises(Exception, match=r"100 \(PERSONAL, Ada Lovelace\)") as excinfo:
        init_wise_client("business")

    assert "WISE_PROFILE_ID" in str(excinfo.value)


def test_summary_from_business_profile():
    summary = WiseProfileSummary.from_api(BUSINESS, default_profile_id="200")

    assert summary == WiseProfileSummary(profile_id="200", type="BUSINESS", name="Acme LLC", is_default=True)


def test_summary_from_personal_profile():
    summary = WiseProfileSummary.from_api(PERSONAL, default_profile_id="200")

    assert summary == WiseProfileSummary(profile_id="100", type="PERSONAL", name="Ada Lovelace", is_default=False)


def test_summary_falls_back_to_first_and_last_name():
    summary = WiseProfileSummary.from_api({"id": 1, "type": "personal", "firstName": "Ada", "lastName": "Lovelace"})

    assert summary.name == "Ada Lovelace"
    assert summary.type == "PERSONAL"


def test_from_api_reads_v1_nested_details():
    personal = WiseProfileSummary.from_api(V1_PERSONAL)
    business = WiseProfileSummary.from_api(V1_BUSINESS)
    assert (personal.type, personal.name) == ("PERSONAL", "Ada Lovelace")
    assert (business.type, business.name) == ("BUSINESS", "Acme LLC")
