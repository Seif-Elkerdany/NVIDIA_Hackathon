"""Replay capabilities never persist or authenticate as plaintext."""

from dataclasses import replace
from datetime import timedelta
from uuid import UUID

import pytest
from cryptography.exceptions import InvalidTag
from tests.fakes.providers import FakeClock

from benefitbridge.db.jobs import ReplayIdentity, decrypt_replay, encrypt_replay
from benefitbridge.domain.dto import DeletionAccepted


def test_encrypted_receipt_round_trip_and_authenticated_context(fake_clock: FakeClock):
    body = DeletionAccepted(
        receipt_id=UUID(int=1),
        receipt_token="synthetic-secret-receipt-token",
        receipt_url="/api/v1/deletion-receipts/fixture",
        status="PENDING",
        expires_at=fake_clock.now() + timedelta(days=7),
    )
    identity = ReplayIdentity(UUID(int=2), "delete_account", "synthetic-key-0001", "a" * 64)
    key = b"s" * 32
    encrypted = encrypt_replay(body, identity, encryption_key=key)
    assert body.receipt_token.encode() not in encrypted
    assert (
        DeletionAccepted.model_validate_json(
            decrypt_replay(encrypted, identity, encryption_key=key)
        )
        == body
    )
    assert encrypt_replay(body, identity, encryption_key=key) != encrypted
    for other in (
        replace(identity, owner_id=UUID(int=3)),
        replace(identity, operation="start_discovery"),
        replace(identity, key="another-key-00001"),
        replace(identity, request_hash="b" * 64),
    ):
        with pytest.raises(InvalidTag):
            decrypt_replay(encrypted, other, encryption_key=key)
    with pytest.raises(InvalidTag):
        decrypt_replay(encrypted[:-1] + bytes([encrypted[-1] ^ 1]), identity, encryption_key=key)
    with pytest.raises(ValueError):
        encrypt_replay(body, identity, encryption_key=b"short")
    with pytest.raises(ValueError):
        decrypt_replay(body.model_dump_json().encode(), identity, encryption_key=key)
