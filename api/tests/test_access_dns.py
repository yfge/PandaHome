import json
from types import SimpleNamespace

import pytest
from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest

from src.app.schemas.domains import DomainRecord
from src.app.services.access.dns import DnsConflict, DnsSync
from src.app.services.aliyun_dns import AliyunDNSError, AliyunDNSErrorCode, AliyunDNSService


def record(record_id="record-1", *, rr="home", record_type="A", value="8.8.8.8", line="default"):
    return DomainRecord(
        RecordId=record_id,
        RR=rr,
        Type=record_type,
        Value=value,
        TTL=600,
        Line=line,
        Status="ENABLE",
        Locked=False,
        DomainName="example.com",
        CreateTimestamp=1_700_000_000,
    )


class DnsProvider:
    """Small in-memory DNS provider that preserves unrelated records."""

    def __init__(self, records=()):
        self.records = list(records)
        self.writes = []
        self.reads = []

    def get_domain_records(self, domain):
        self.reads.append(domain)
        return list(self.records)

    def add_domain_record(self, domain, payload):
        self.writes.append(("add", domain, payload))
        self.records.append(
            record(
                f"new-{len(self.records)}",
                rr=payload.rr,
                record_type=payload.type,
                value=payload.value,
                line=payload.line,
            )
        )

    def update_domain_record(self, domain, record_id, payload):
        self.writes.append(("update", domain, record_id, payload))
        current = next(item for item in self.records if item.RecordId == record_id)
        current.Type = payload.type
        current.Value = payload.value


def service(*, domain="example.com", rr="home"):
    return SimpleNamespace(domain=domain, rr=rr)


@pytest.mark.asyncio
async def test_unconfigured_dns_does_not_create_provider():
    def unexpected_provider():
        raise AssertionError("DNS provider must not be used without a configured domain")

    assert await DnsSync(unexpected_provider).sync(service(domain=""), "8.8.8.8") == "not_configured"


@pytest.mark.asyncio
async def test_first_publish_creates_once_and_reconciliation_is_idempotent():
    provider = DnsProvider([record("unrelated", rr="mail", value="1.1.1.1")])
    sync = DnsSync(lambda: provider)
    await sync.sync(service(), "8.8.8.8")
    await sync.sync(service(), "8.8.8.8")
    assert len(provider.writes) == 1
    operation, zone, payload = provider.writes[0]
    assert operation == "add"
    assert zone == "example.com"
    assert payload.rr == "home"
    assert payload.type == "A"
    assert payload.value == "8.8.8.8"
    assert payload.line == "default"
    assert provider.records[0].Value == "1.1.1.1"


@pytest.mark.asyncio
async def test_public_ip_change_updates_existing_record_and_then_converges():
    provider = DnsProvider([record(value="8.8.8.8")])
    sync = DnsSync(lambda: provider)
    await sync.sync(service(), "1.1.1.1")
    await sync.sync(service(), "1.1.1.1")
    assert len(provider.writes) == 1
    operation, zone, record_id, payload = provider.writes[0]
    assert (operation, zone, record_id) == ("update", "example.com", "record-1")
    assert payload.type == "A"
    assert payload.value == "1.1.1.1"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "old_type,old_value,target,new_type,new_value",
    [
        ("A", "8.8.8.8", "1.1.1.1", "A", "1.1.1.1"),
        ("AAAA", "2606:4700:4700::1111", "2606:4700:4700::1001", "AAAA", "2606:4700:4700::1001"),
        ("CNAME", "old-relay.example.net", "New-Relay.EXAMPLE.NET.", "CNAME", "new-relay.example.net"),
        ("A", "8.8.8.8", "relay.example.net", "CNAME", "relay.example.net"),
        ("CNAME", "relay.example.net", "1.1.1.1", "A", "1.1.1.1"),
    ],
    ids=["ipv4-change", "ipv6-change", "relay-change", "direct-to-relay", "relay-to-direct"],
)
async def test_ddns_sdk_update_includes_required_fields_and_skips_repeated_write(
    monkeypatch, old_type, old_value, target, new_type, new_value
):
    rr = "media.nas"
    current = record("existing-record", rr=rr, record_type=old_type, value=old_value).model_dump()
    requests = []

    def sdk_transport(request):
        requests.append(request)
        if isinstance(request, DescribeDomainRecordsRequest):
            return json.dumps({"DomainRecords": {"Record": [current]}, "TotalCount": 1}).encode()
        assert isinstance(request, UpdateDomainRecordRequest), "DDNS must reuse the official SDK update operation"
        params = request.get_query_params()
        current.update({key: params[key] for key in ("RR", "Type", "Value") if key in params})
        return json.dumps({"RecordId": current["RecordId"], "RequestId": "test-request"}).encode()

    provider = AliyunDNSService()
    monkeypatch.setattr(provider, "_require_client", lambda: SimpleNamespace(do_action_with_exception=sdk_transport))
    sync = DnsSync(lambda: provider)
    await sync.sync(service(rr=rr), target)
    updates = [request for request in requests if isinstance(request, UpdateDomainRecordRequest)]
    assert len(updates) == 1
    params = updates[0].get_query_params()
    assert {key: params.get(key) for key in ("RecordId", "RR", "Type", "Value")} == {
        "RecordId": "existing-record",
        "RR": rr,
        "Type": new_type,
        "Value": new_value,
    }
    await sync.sync(service(rr=rr), target)
    assert [request for request in requests if isinstance(request, UpdateDomainRecordRequest)] == updates


@pytest.mark.asyncio
async def test_direct_to_relay_and_back_reuses_record_without_duplicates():
    provider = DnsProvider([record()])
    sync = DnsSync(lambda: provider)
    await sync.sync(service(), "Relay.EXAMPLE.NET.")
    await sync.sync(service(), "relay.example.net")
    assert len(provider.writes) == 1
    assert provider.records[0].Type == "CNAME"
    assert provider.records[0].Value == "relay.example.net"
    await sync.sync(service(), "1.1.1.1")
    assert len(provider.writes) == 2
    assert provider.records[0].Type == "A"
    assert provider.records[0].Value == "1.1.1.1"
    assert len(provider.records) == 1
    assert {write[2] for write in provider.writes} == {"record-1"}


@pytest.mark.asyncio
async def test_equivalent_cname_case_and_absolute_name_are_unchanged():
    provider = DnsProvider([record(record_type="CNAME", value="Relay.EXAMPLE.NET.")])
    await DnsSync(lambda: provider).sync(service(), "relay.example.net")
    assert not provider.writes


@pytest.mark.asyncio
async def test_ipv6_records_are_canonical_and_preserve_existing_ipv4():
    provider = DnsProvider([record()])
    sync = DnsSync(lambda: provider)
    await sync.sync(service(), "2606:4700:4700:0:0:0:0:1111")
    await sync.sync(service(), "2606:4700:4700::1111")
    assert len(provider.writes) == 1
    assert provider.records[0].Type == "A"
    assert provider.records[0].Value == "8.8.8.8"
    assert provider.records[1].Type == "AAAA"
    assert provider.records[1].Value == "2606:4700:4700::1111"


@pytest.mark.asyncio
async def test_other_hostnames_and_nondefault_lines_are_preserved():
    others = [record("other", rr="mail"), record("regional", value="9.9.9.9", line="telecom")]
    provider = DnsProvider(others + [record(value="8.8.8.8")])
    await DnsSync(lambda: provider).sync(service(), "1.1.1.1")
    assert [(item.RecordId, item.Value) for item in provider.records[:2]] == [
        ("other", "8.8.8.8"),
        ("regional", "9.9.9.9"),
    ]
    assert provider.writes[0][2] == "record-1"


@pytest.mark.asyncio
async def test_direct_dns_preserves_same_hostname_txt_record():
    provider = DnsProvider([record("txt", record_type="TXT", value="ownership-verification"), record()])
    await DnsSync(lambda: provider).sync(service(), "1.1.1.1")
    assert provider.records[0].Type == "TXT"
    assert provider.records[0].Value == "ownership-verification"
    assert provider.writes[0][2] == "record-1"


@pytest.mark.asyncio
async def test_disabled_dns_record_does_not_claim_synchronization():
    existing = record()
    existing.Status = "DISABLE"
    provider = DnsProvider([existing])
    with pytest.raises(DnsConflict, match="disabled"):
        await DnsSync(lambda: provider).sync(service(), "8.8.8.8")
    assert not provider.writes


@pytest.mark.asyncio
async def test_locked_record_with_correct_value_is_usable_but_cannot_be_changed():
    existing = record()
    existing.Locked = True
    provider = DnsProvider([existing])
    sync = DnsSync(lambda: provider)
    await sync.sync(service(), "8.8.8.8")
    with pytest.raises(DnsConflict, match="locked"):
        await sync.sync(service(), "1.1.1.1")
    assert not provider.writes


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "records, target",
    [
        ([record("a-1"), record("a-2", value="1.1.1.1")], "9.9.9.9"),
        ([record("a"), record("cname", record_type="CNAME", value="relay.example.net")], "9.9.9.9"),
        ([record("a"), record("aaaa", record_type="AAAA", value="2606:4700:4700::1111")], "relay.example.net"),
        ([record("txt", record_type="TXT", value="ownership-verification")], "relay.example.net"),
        ([record("mx", record_type="MX", value="mail.example.com")], "relay.example.net"),
    ],
)
async def test_ambiguous_or_cname_incompatible_records_require_explicit_resolution(records, target):
    provider = DnsProvider(records)
    with pytest.raises(DnsConflict):
        await DnsSync(lambda: provider).sync(service(), target)
    assert not provider.writes


@pytest.mark.asyncio
async def test_apex_cname_is_rejected_before_modifying_dns():
    provider = DnsProvider([record(rr="@")])
    with pytest.raises(DnsConflict, match="subdomain"):
        await DnsSync(lambda: provider).sync(service(rr="@"), "relay.example.net")
    assert not provider.writes


@pytest.mark.asyncio
async def test_provider_failure_is_propagated_for_orchestrator_status():
    error = AliyunDNSError(AliyunDNSErrorCode.AUTH_FAILED, "Credentials are invalid")

    class FailedProvider:
        def get_domain_records(self, domain):
            raise error

    with pytest.raises(AliyunDNSError) as caught:
        await DnsSync(FailedProvider).sync(service(), "8.8.8.8")
    assert caught.value is error


class PagedAliyunClient:
    def __init__(self, pages):
        self.pages = pages
        self.requests = []

    def do_action_with_exception(self, request):
        params = dict(request.get_query_params())
        self.requests.append(params)
        index = int(params["PageNumber"]) - 1
        assert index < len(self.pages), "Unexpected extra DNS page request"
        return json.dumps(self.pages[index]).encode()


def aliyun_with_pages(monkeypatch, pages):
    provider = AliyunDNSService()
    client = PagedAliyunClient(pages)
    monkeypatch.setattr(provider, "_require_client", lambda: client)
    return provider, client


def page_of_records(start, count):
    return [record(f"id-{index}", rr=f"other-{index}").model_dump() for index in range(start, start + count)]


@pytest.mark.asyncio
async def test_sync_finds_existing_record_beyond_first_provider_page(monkeypatch):
    target = record("existing-home").model_dump()
    provider, client = aliyun_with_pages(
        monkeypatch,
        [
            {"DomainRecords": {"Record": page_of_records(0, 500)}, "TotalCount": 501},
            {"DomainRecords": {"Record": [target]}, "TotalCount": 501},
        ],
    )

    def unexpected_write(*args):
        raise AssertionError("An unchanged DNS record on a later page must never be recreated or updated")

    monkeypatch.setattr(provider, "add_domain_record", unexpected_write)
    monkeypatch.setattr(provider, "update_domain_record", unexpected_write)
    await DnsSync(lambda: provider).sync(service(), "8.8.8.8")
    assert [request["PageNumber"] for request in client.requests] == [1, 2]
    assert all(request["PageSize"] == 500 for request in client.requests)
    assert all(request["DomainName"] == "example.com" for request in client.requests)


@pytest.mark.parametrize("last_page", [[record("last-home").model_dump()], []])
def test_missing_total_count_still_fetches_after_full_500_record_page(monkeypatch, last_page):
    provider, client = aliyun_with_pages(
        monkeypatch,
        [
            {"DomainRecords": {"Record": page_of_records(0, 500)}},
            {"DomainRecords": {"Record": last_page}},
        ],
    )
    records = provider.get_domain_records("example.com")
    assert len(records) == 500 + len(last_page)
    assert len(client.requests) == 2
    assert [request["PageNumber"] for request in client.requests] == [1, 2]


def test_single_record_object_payload_is_preserved(monkeypatch):
    provider, client = aliyun_with_pages(
        monkeypatch, [{"DomainRecords": {"Record": record("single-record").model_dump()}, "TotalCount": 1}]
    )
    records = provider.get_domain_records("example.com")
    assert [item.RecordId for item in records] == ["single-record"]
    assert len(client.requests) == 1


def test_known_total_requires_complete_listing_before_dns_mutation(monkeypatch):
    provider, client = aliyun_with_pages(
        monkeypatch,
        [
            {"DomainRecords": {"Record": page_of_records(0, 500)}, "TotalCount": 501},
            {"DomainRecords": {"Record": []}, "TotalCount": 501},
        ],
    )
    with pytest.raises(AliyunDNSError, match="incomplete") as caught:
        provider.get_domain_records("example.com")
    assert caught.value.code == AliyunDNSErrorCode.REQUEST_FAILED
    assert len(client.requests) == 2


def test_repeated_provider_page_fails_instead_of_looping_or_assuming_absence(monkeypatch):
    full_page = {"DomainRecords": {"Record": page_of_records(0, 500)}}
    provider, client = aliyun_with_pages(monkeypatch, [full_page, full_page])
    with pytest.raises(AliyunDNSError, match="changed"):
        provider.get_domain_records("example.com")
    assert len(client.requests) == 2
