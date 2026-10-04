"""Deterministic synthetic API examples; no external providers or clocks."""

import json
import re
import socket
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
API_TEXT = (ROOT / "API.md").read_text(encoding="utf-8")
SYNTHETIC_STATEMENT = " ".join(["Synthetic applicant statement for schema validation only."] * 25)


def catalog_examples():
    catalog = API_TEXT.split("## Response DTO catalog")[1].split("## Endpoint index")[0]
    examples = {}
    for section in re.split(r"(?=^### )", catalog, flags=re.M)[1:]:
        name = section.splitlines()[0].removeprefix("### ")
        payload = json.loads(re.search(r"```json\n(.*?)\n```", section, re.S).group(1))
        # The contract explicitly calls its examples illustrative, not relational fixtures.
        # Repair display-only offsets and abbreviated prose in these test inputs only.
        if name == "Evidence":
            payload["end"] = payload["start"] + len(payload["quote"])
        if name == "Source":
            for span in payload["spans"]:
                span["end"] = span["start"] + len(span["quote"])
        if name == "Draft":
            payload["text"] = SYNTHETIC_STATEMENT
        examples[name] = payload
    return examples


@pytest.fixture
def examples():
    return catalog_examples()


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Domain validation must not access the network")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
