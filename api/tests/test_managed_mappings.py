from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call

import pytest
from async_upnp_client.exceptions import UpnpActionError

from src.app.models.published_service import PublishedService
from src.app.services.access.mappings import ManagedMappings, MappingConflict


@pytest.fixture()
def row() -> PublishedService:
    return PublishedService(
        local_ip="192.168.1.10",
        local_port=8080,
        public_port=18080,
        protocol="TCP",
        lease_duration=3600,
        owner_token="unique-owner-token",
    )


@pytest.fixture()
def spec() -> dict:
    return {
        "external_port": 18080,
        "internal_port": 8080,
        "local_ip": "192.168.1.10",
        "protocol": "TCP",
        "description": "PandaHome:unique-owner-token",
    }


@pytest.fixture()
def existing() -> dict:
    return {
        "NewInternalPort": 8080,
        "NewInternalClient": "192.168.1.10",
        "NewEnabled": True,
        "NewPortMappingDescription": "PandaHome:unique-owner-token",
        "NewLeaseDuration": 3600,
    }


@pytest.fixture()
def upnp():
    return SimpleNamespace(
        gateway_service=AsyncMock(return_value=SimpleNamespace(async_call_action=AsyncMock())),
        invalidate_mappings_cache=Mock(),
        get_port_mappings=AsyncMock(side_effect=AssertionError("Must not enumerate mappings")),
    )


def query_call(action: str) -> call:
    return call(action, NewRemoteHost="", NewExternalPort=18080, NewProtocol="TCP")


@pytest.mark.asyncio
@pytest.mark.parametrize("missing_code", [713, 714])
async def test_creates_absent_mapping_without_enumeration(upnp, row: PublishedService, spec: dict, missing_code: int):
    wan = upnp.gateway_service.return_value
    wan.async_call_action.side_effect = [UpnpActionError(error_code=missing_code), {}]

    assert await ManagedMappings(upnp).ensure(row) == spec
    assert wan.async_call_action.await_args_list == [
        query_call("GetSpecificPortMappingEntry"),
        call(
            "AddPortMapping",
            NewRemoteHost="",
            NewExternalPort=18080,
            NewProtocol="TCP",
            NewInternalPort=8080,
            NewInternalClient="192.168.1.10",
            NewEnabled=True,
            NewPortMappingDescription="PandaHome:unique-owner-token",
            NewLeaseDuration=3600,
        ),
    ]
    upnp.get_port_mappings.assert_not_called()
    upnp.invalidate_mappings_cache.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [True, False])
async def test_renews_owned_mapping_even_when_disabled(upnp, row, spec, existing, enabled):
    existing["NewEnabled"] = enabled
    existing["NewInternalPort"] = "8080"
    wan = upnp.gateway_service.return_value
    wan.async_call_action.side_effect = [existing, {}]

    assert await ManagedMappings(upnp).ensure(row) == spec
    assert [args.args[0] for args in wan.async_call_action.await_args_list] == [
        "GetSpecificPortMappingEntry",
        "AddPortMapping",
    ]
    assert wan.async_call_action.await_args.kwargs["NewEnabled"] is True
    assert wan.async_call_action.await_args.kwargs["NewLeaseDuration"] == 3600


@pytest.mark.asyncio
async def test_recreates_mapping_after_gateway_reboot(upnp, row):
    wan = upnp.gateway_service.return_value
    wan.async_call_action.side_effect = [UpnpActionError(error_code=714), {}, UpnpActionError(error_code=714), {}]
    mappings = ManagedMappings(upnp)

    await mappings.ensure(row)
    await mappings.ensure(row)

    assert [args.args[0] for args in wan.async_call_action.await_args_list] == [
        "GetSpecificPortMappingEntry",
        "AddPortMapping",
        "GetSpecificPortMappingEntry",
        "AddPortMapping",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change",
    [
        {"NewPortMappingDescription": "other application"},
        {"NewPortMappingDescription": "PandaHome:different-owner"},
        {"NewInternalClient": "192.168.1.11"},
        {"NewInternalPort": 8081},
        {"NewInternalPort": "invalid"},
    ],
)
async def test_conflicting_mapping_is_never_modified(upnp, row, existing, change):
    existing.update(change)
    wan = upnp.gateway_service.return_value
    wan.async_call_action.return_value = existing

    with pytest.raises(MappingConflict):
        await ManagedMappings(upnp).ensure(row)

    wan.async_call_action.assert_awaited_once_with(
        "GetSpecificPortMappingEntry", NewRemoteHost="", NewExternalPort=18080, NewProtocol="TCP"
    )
    upnp.invalidate_mappings_cache.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("result", [None, [], {}])
async def test_unverifiable_lookup_never_becomes_permission_to_add(upnp, row, result):
    wan = upnp.gateway_service.return_value
    wan.async_call_action.return_value = result

    with pytest.raises(MappingConflict):
        await ManagedMappings(upnp).ensure(row)

    assert wan.async_call_action.await_count == 1


@pytest.mark.asyncio
async def test_permanent_only_gateway_retries_zero_lease(upnp, row, existing):
    wan = upnp.gateway_service.return_value
    wan.async_call_action.side_effect = [existing, UpnpActionError(error_code=725), {}]

    await ManagedMappings(upnp).ensure(row)

    leases = [args.kwargs["NewLeaseDuration"] for args in wan.async_call_action.await_args_list[1:]]
    assert leases == [3600, 0]
    upnp.invalidate_mappings_cache.assert_called_once()


@pytest.mark.asyncio
async def test_zero_lease_error_is_not_retried_forever(upnp, row, existing):
    row.lease_duration = 0
    wan = upnp.gateway_service.return_value
    wan.async_call_action.side_effect = [existing, UpnpActionError(error_code=725)]

    with pytest.raises(UpnpActionError):
        await ManagedMappings(upnp).ensure(row)

    assert wan.async_call_action.await_count == 2
    upnp.invalidate_mappings_cache.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("error_code", [401, 501, 718])
async def test_unrecognized_lookup_error_propagates_without_mutation(upnp, row, error_code):
    wan = upnp.gateway_service.return_value
    wan.async_call_action.side_effect = UpnpActionError(error_code=error_code)

    with pytest.raises(UpnpActionError) as caught:
        await ManagedMappings(upnp).ensure(row)

    assert caught.value.error_code == error_code
    assert wan.async_call_action.await_count == 1
    upnp.invalidate_mappings_cache.assert_not_called()


@pytest.mark.asyncio
async def test_add_failure_propagates_without_deleting_existing(upnp, row, existing):
    wan = upnp.gateway_service.return_value
    wan.async_call_action.side_effect = [existing, TimeoutError()]

    with pytest.raises(TimeoutError):
        await ManagedMappings(upnp).ensure(row)

    assert [args.args[0] for args in wan.async_call_action.await_args_list] == [
        "GetSpecificPortMappingEntry",
        "AddPortMapping",
    ]


@pytest.mark.asyncio
async def test_remove_verifies_owner_and_target_before_deleting(upnp, spec, existing):
    wan = upnp.gateway_service.return_value
    wan.async_call_action.side_effect = [existing, {}]

    await ManagedMappings(upnp).remove(spec)

    assert wan.async_call_action.await_args_list == [
        query_call("GetSpecificPortMappingEntry"),
        query_call("DeletePortMapping"),
    ]
    upnp.invalidate_mappings_cache.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change",
    [
        {"NewPortMappingDescription": "other application"},
        {"NewPortMappingDescription": "PandaHome:different-owner"},
        {"NewInternalClient": "192.168.1.11"},
        {"NewInternalPort": 9090},
    ],
)
async def test_remove_preserves_replaced_or_unrelated_mapping(upnp, spec, existing, change):
    existing.update(change)
    wan = upnp.gateway_service.return_value
    wan.async_call_action.return_value = existing

    await ManagedMappings(upnp).remove(spec)

    assert wan.async_call_action.await_args_list == [query_call("GetSpecificPortMappingEntry")]
    upnp.invalidate_mappings_cache.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("missing_code", [713, 714])
async def test_remove_absent_mapping_is_noop(upnp, spec, missing_code):
    wan = upnp.gateway_service.return_value
    wan.async_call_action.side_effect = UpnpActionError(error_code=missing_code)

    await ManagedMappings(upnp).remove(spec)

    assert wan.async_call_action.await_args_list == [query_call("GetSpecificPortMappingEntry")]


@pytest.mark.asyncio
async def test_remove_tolerates_expiry_between_lookup_and_delete(upnp, spec, existing):
    wan = upnp.gateway_service.return_value
    wan.async_call_action.side_effect = [existing, UpnpActionError(error_code=714)]

    await ManagedMappings(upnp).remove(spec)

    upnp.invalidate_mappings_cache.assert_called_once()


@pytest.mark.asyncio
async def test_remove_failure_propagates(upnp, spec, existing):
    wan = upnp.gateway_service.return_value
    wan.async_call_action.side_effect = [existing, UpnpActionError(error_code=501)]

    with pytest.raises(UpnpActionError):
        await ManagedMappings(upnp).remove(spec)

    upnp.invalidate_mappings_cache.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("description", [None, "", "other application", "PandaHome:"])
async def test_remove_refuses_specs_without_owner_token(upnp, spec, description):
    spec["description"] = description

    await ManagedMappings(upnp).remove(spec)

    upnp.gateway_service.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_requires_persisted_owner_token(upnp, row):
    row.owner_token = None

    with pytest.raises(ValueError, match="owner token"):
        await ManagedMappings(upnp).ensure(row)

    upnp.gateway_service.assert_not_called()
