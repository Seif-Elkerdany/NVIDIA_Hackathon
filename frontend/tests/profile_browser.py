"""MS-018 deterministic UI checks in local Edge; fixture adapters never call providers."""

import re
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def verify(base_url: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route(
            "**/*",
            lambda route: (
                route.continue_() if route.request.url.startswith(base_url) else route.abort()
            ),
        )
        target = base_url + "/tests/profile.html"
        page.goto(target)
        expect(page.get_by_role("heading", name="Your background, in your words")).to_be_visible()
        expect(page.get_by_text("3.50 / 5.00", exact=False)).to_be_visible()
        assert page.locator("img").count() == 0
        assert page.evaluate("window.syntheticInjection") is None
        authorization = page.locator("fieldset").filter(
            has=page.locator("#profile-work_authorization-countries-action")
        )
        expect(authorization.locator(".profile-current")).to_be_visible()
        expect(page.get_by_role("button", name="Save profile changes")).to_be_disabled()
        page.get_by_label("Update gpa", exact=True).focus()
        assert page.evaluate("document.activeElement.id") == "profile-education-gpa-action"
        assert (
            page.get_by_label("Update gpa", exact=True).evaluate(
                "e=>getComputedStyle(e).outlineStyle"
            )
            != "none"
        )
        artifact = Path(".pytest_cache/ms018-profile-desktop.png")
        artifact.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(artifact), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=".pytest_cache/ms018-profile-mobile.png", full_page=True)
        page.set_viewport_size({"width": 1280, "height": 1000})

        def enter_gpa(number: str) -> None:
            page.get_by_label("Update gpa", exact=True).select_option("known")
            page.get_by_label("GPA number", exact=True).fill(number)
            expect(page.get_by_label("Original scale maximum", exact=True)).to_have_value("5.00")
            page.get_by_label("I confirm the changes I entered.").check()

        enter_gpa("3.70")
        page.get_by_role("button", name="Save profile changes").click()
        expect(page.get_by_text("Profile saved as a new version", exact=False)).to_be_visible()
        calls = page.evaluate("window.profileTest.calls")
        assert calls[-1]["body"]["changes"] == [
            {
                "attribute": "education.gpa",
                "value": {"type": "GPA", "number": "3.70", "scale_max": "5.00"},
                "evidence_ids": [],
            }
        ]
        page.get_by_role("button", name="View version history").click()
        page.get_by_role("button", name="Load older versions").click()
        expect(page.locator("summary").filter(has_text="Version 1")).to_be_visible()

        page.evaluate("window.profileTest.failure='conflict'")
        enter_gpa("3.80")
        page.get_by_role("button", name="Save profile changes").click()
        expect(
            page.get_by_role("heading", name="Your profile changed while you were editing")
        ).to_be_visible()
        expect(page.get_by_label("GPA number", exact=True)).to_have_value("3.80")
        expect(page.get_by_role("button", name="Save profile changes")).to_be_disabled()
        assert page.evaluate("document.activeElement.className") == "profile-feedback"
        page.evaluate("window.profileTest.reloadFailure=true")
        page.get_by_role("button", name="Reload current profile").click()
        expect(
            page.get_by_role("heading", name="We couldn’t complete this request")
        ).to_be_visible()
        expect(page.get_by_label("GPA number", exact=True)).to_have_value("3.80")
        page.evaluate("window.profileTest.reloadFailure=false")
        page.get_by_role("button", name="Reload current profile").click()
        expect(page.get_by_text("Editing version 3", exact=True)).to_be_visible()
        expect(page.get_by_label("Update gpa", exact=True)).to_have_value("unchanged")
        expect(page.get_by_label("GPA number", exact=True)).to_have_count(0)

        page.evaluate("window.profileTest.failure='timeout'")
        enter_gpa("3.90")
        page.get_by_role("button", name="Save profile changes").click()
        expect(page.get_by_text("The request timed out. Try again.", exact=True)).to_be_visible()
        page.get_by_role("button", name="Save profile changes").click()
        expect(page.get_by_text("Profile saved as a new version", exact=False)).to_be_visible()
        calls = page.evaluate("window.profileTest.calls")
        assert calls[-1]["key"] == calls[-2]["key"]
        assert calls[-1]["body"] == calls[-2]["body"]

        page.evaluate("window.profileTest.failure='defer'")
        enter_gpa("4.00")
        page.get_by_role("button", name="Save profile changes").click()
        page.wait_for_function("window.profileTest.releaseSave !== null")
        page.evaluate("window.profileTest.switchIdentity()")
        expect(page.get_by_text("No facts have been provided yet.", exact=False)).to_be_visible()
        page.evaluate("window.profileTest.releaseSave()")
        expect(page.get_by_text("Profile saved as a new version", exact=False)).to_have_count(0)
        expect(page.get_by_text("No facts have been provided yet.", exact=False)).to_be_visible()
        page.goto(target + "?mode=loading")
        expect(page.get_by_role("heading", name="Loading your profile")).to_be_visible()
        page.get_by_role("button", name="Stop this request").click()
        expect(page.get_by_role("heading", name="Profile request stopped")).to_be_visible()
        page.goto(target + "?mode=error")
        expect(
            page.get_by_role("heading", name=re.compile(r"We couldn.t complete this request"))
        ).to_be_visible()
        page.evaluate("window.profileTest.reloadFailure=false")
        page.get_by_role("button", name="Try again", exact=True).click()
        expect(page.get_by_role("heading", name="Education", exact=True)).to_be_visible()
        page.get_by_label("Update language tests", exact=True).select_option("known")
        page.get_by_role("button", name="Add language test", exact=True).click()
        page.get_by_label("Test name", exact=True).fill("Synthetic exam")
        page.get_by_label("Total score", exact=True).fill("8.50")
        page.get_by_label("Date taken", exact=True).fill("2026-09-01")
        components = page.get_by_label("Component scores", exact=False)
        components.press_sequentially("reading: 8.50")
        expect(components).to_have_value("reading: 8.50")
        components.fill("reading: 8.50\nreading: 7.00")
        page.get_by_label("I confirm the changes I entered.").check()
        page.get_by_role("button", name="Save profile changes").click()
        expect(
            page.get_by_text("Check language tests before saving.", exact=True).first
        ).to_be_visible()
        assert page.evaluate("window.profileTest.calls.length") == 0
        assert not errors, errors
        browser.close()
        print(
            "PASS: GPA, unknowns, keyboard focus, mobile, history, "
            "conflict/reload, replay and identity fencing"
        )


if __name__ == "__main__":
    verify(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5173")
