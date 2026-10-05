"""MS-004 synthetic browser checks. Run against a local Vite server with Playwright."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def verify(base_url: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route(
            "**/api/v1/capabilities",
            lambda route: route.fulfill(
                status=503,
                content_type="application/problem+json",
                body=json.dumps(
                    {
                        "type": "urn:benefitbridge:problem:service-unavailable",
                        "title": "Service unavailable",
                        "detail": "Synthetic service unavailable.",
                        "status": 503,
                        "code": "SERVICE_UNAVAILABLE",
                        "retryable": True,
                        "errors": [],
                        "request_id": "synthetic-response",
                    }
                ),
                headers={"X-Request-ID": "synthetic-response"},
            ),
        )
        page.goto(base_url)
        page.get_by_role("heading", name="Build a clearer path to opportunity").wait_for()
        page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement.textContent") == "Skip to content"
        page.keyboard.press("Enter")
        assert page.evaluate("document.activeElement.id") == "main-content"
        page.get_by_role("link", name="Settings", exact=True).click()
        page.get_by_role("heading", name="Your service connection").wait_for()
        assert page.evaluate("document.activeElement.tagName") == "H1"
        assert (
            page.get_by_role("link", name="Settings", exact=True).get_attribute("aria-current")
            == "page"
        )
        page.go_back()
        page.get_by_role("heading", name="Build a clearer path to opportunity").wait_for()
        page.get_by_role("link", name="Settings", exact=True).click()
        page.get_by_role("alert").wait_for()
        assert "synthetic-response" in page.get_by_role("alert").inner_text()
        page.get_by_role("button", name="Try again").click()
        page.get_by_role("alert").wait_for()
        page.goto(base_url + "/missing-route")
        page.get_by_role("heading", name="We couldn’t find this page").wait_for()
        for width in [1440, 390]:
            page.set_viewport_size({"width": width, "height": 1000})
            page.goto(base_url)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            artifact = Path(".pytest_cache") / f"ms004-shell-{width}.png"
            artifact.parent.mkdir(exist_ok=True)
            page.screenshot(path=str(artifact), full_page=True)
        page.goto(base_url + "/tests/fixture.html")
        for state in [
            "empty",
            "loading",
            "unknown",
            "partial",
            "stale",
            "unavailable",
            "cancelled",
        ]:
            page.get_by_role("heading", name=f"{state} result", exact=True).wait_for()
        assert page.get_by_role("alert").count() == 1
        assert page.locator("img").count() == 0
        assert page.locator(".plain-text").inner_text().startswith("<img src=x")
        assert page.evaluate("window.syntheticInjection === undefined")
        assert page.locator("[aria-busy=true]").count() == 1
        # A fresh context avoids cached data from the earlier error scenario.
        pending = browser.new_page()
        pending.add_init_script("""
            window.syntheticMethods = [];
            const originalFetch = window.fetch;
            window.fetch = (request) => {
              if (!(request instanceof Request) || !request.url.includes('/api/v1/')) {
                return originalFetch(request);
              }
              window.syntheticMethods.push(request.method);
              return new Promise((resolve, reject) => {
                request.signal.addEventListener('abort',
                  () => reject(request.signal.reason), {once: true});
                if (request.signal.aborted) reject(request.signal.reason);
              });
            };
        """)
        pending.goto(base_url + "/settings")
        pending.get_by_role("button", name="Stop this request").click()
        pending.get_by_role("heading", name="The browser request was stopped").wait_for()
        methods = pending.evaluate("window.syntheticMethods")
        assert methods and all(method == "GET" for method in methods), methods
        assert pending.get_by_role("button", name="Check again").count() == 1
        pending.close()
        assert not errors, errors
        browser.close()
    print(
        "PASS: keyboard, route focus/history, error/retry, cancellation without server mutation, "
        "unknown/empty/partial/stale, escaped model text, desktop/mobile overflow"
    )


if __name__ == "__main__":
    verify(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5173")
