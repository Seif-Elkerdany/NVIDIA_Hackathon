"""Offline by default; paid tests require explicit local selection and budget."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from tests.fakes.network import install_network_guard
from tests.fakes.providers import (
    FakeClock,
    FakeFetch,
    FakeSearch,
    ScriptedLLM,
    fixture_dependencies,
)

from benefitbridge.composition import Dependencies
from benefitbridge.config import Settings

_network_patch = pytest.MonkeyPatch()


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("benefitbridge")
    group.addoption(
        "--suite", choices=("offline", "unit", "integration", "live"), default="offline"
    )
    group.addoption("--allow-paid-live", action="store_true", default=False)
    group.addoption("--live-budget-microusd", type=int, default=0)


def pytest_configure(config: pytest.Config) -> None:
    for marker in ("integration: in-process/local integration", "live: paid provider execution"):
        config.addinivalue_line("markers", marker)
    live = config.getoption("suite") == "live"
    approved = config.getoption("allow_paid_live")
    budget = config.getoption("live_budget_microusd")
    if live or approved or budget:
        if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
            raise pytest.UsageError("Paid live tests are prohibited in ordinary CI")
        if not live or not approved or budget <= 0:
            raise pytest.UsageError(
                "Live tests require --suite live --allow-paid-live and a budget"
            )
    if not live:
        # Install before collection, when a mistakenly imported SDK could do I/O.
        install_network_guard(_network_patch)


def pytest_unconfigure(config: pytest.Config) -> None:
    _network_patch.undo()


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    suite = config.getoption("suite")
    selected: list[pytest.Item] = []
    excluded: list[pytest.Item] = []
    for item in items:
        relative = item.path.relative_to(config.rootpath).parts
        if relative[:2] == ("tests", "live"):
            item.add_marker("live")
        if relative[:2] == ("tests", "integration"):
            item.add_marker("integration")
        live = item.get_closest_marker("live") is not None
        integration = item.get_closest_marker("integration") is not None
        include = live if suite == "live" else not live
        if suite in {"unit", "integration"}:
            include = include and (integration == (suite == "integration"))
        (selected if include else excluded).append(item)
    items[:] = selected
    config.hook.pytest_deselected(items=excluded)


@pytest.fixture(autouse=True)
def synthetic_environment(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[None]:
    if request.config.getoption("suite") != "live":
        for name in tuple(os.environ):
            if name.lower() in Settings.model_fields:
                monkeypatch.delenv(name)
        # No developer .env is loaded into ordinary fixtures.
        monkeypatch.chdir(tmp_path)
    yield


@pytest.fixture
def fake_clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def fake_dependencies(fake_clock: FakeClock) -> Dependencies:
    return fixture_dependencies(fake_clock)


@pytest.fixture
def fake_llm(fake_dependencies: Dependencies) -> ScriptedLLM:
    assert isinstance(fake_dependencies.llm, ScriptedLLM)
    return fake_dependencies.llm


@pytest.fixture
def fake_search(fake_dependencies: Dependencies) -> FakeSearch:
    assert isinstance(fake_dependencies.search, FakeSearch)
    return fake_dependencies.search


@pytest.fixture
def fake_fetch(fake_dependencies: Dependencies) -> FakeFetch:
    assert isinstance(fake_dependencies.fetch, FakeFetch)
    return fake_dependencies.fetch


@pytest.fixture
def fixture_settings() -> Settings:
    return Settings(_env_file=None, app_env="test", provider_mode="fixture")


@pytest.fixture
def paid_live_budget_microusd(request: pytest.FixtureRequest) -> int:
    if request.config.getoption("suite") != "live":
        raise pytest.UsageError("Live budgets are unavailable to ordinary fixtures")
    return int(request.config.getoption("live_budget_microusd"))
