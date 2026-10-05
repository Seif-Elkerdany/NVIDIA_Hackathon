"""MS-009 real SDK/browser checks with intercepted synthetic auth and account HTTP.

Run Vite with the four synthetic VITE_* values documented in auth/handoff.md,
then run this script with Playwright and local Edge. No live provider is used.
"""

import base64
import json
import sys
from datetime import UTC, datetime
from urllib.parse import urlparse

from playwright.sync_api import Page, Route, expect, sync_playwright

NOW = datetime(2026, 10, 5, tzinfo=UTC)
SUBJECT = "00000000-0000-4000-8000-000000000001"
VERSION = "2026-10-01"
AUTH_ORIGIN = "https://synthetic.supabase.invalid"
NOTICE = "Synthetic processing notice. <script>private()</script>"
ACCOUNT = {
    "id": SUBJECT,
    "status": "ACTIVE",
    "display_name": "Synthetic applicant",
    "timezone": "UTC",
    "is_demo": False,
    "created_at": "2026-10-01T00:00:00Z",
    "consent": None,
}
USER = {
    "id": SUBJECT,
    "aud": "authenticated",
    "role": "authenticated",
    "email": "synthetic@example.invalid",
    "app_metadata": {"provider": "email", "providers": ["email"]},
    "user_metadata": {},
    "created_at": "2026-10-01T00:00:00Z",
    "email_confirmed_at": "2026-10-01T00:00:00Z",
}


def encoded(value: object) -> str:
    return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")


def session(seconds: int = 3600) -> dict[str, object]:
    expiry = int(NOW.timestamp()) + seconds
    token = ".".join(
        [
            encoded({"alg": "HS256", "typ": "JWT"}),
            encoded({"sub": SUBJECT, "exp": expiry}),
            "synthetic-signature",
        ]
    )
    return {
        "access_token": token,
        "refresh_token": "synthetic-refresh-secret",
        "token_type": "bearer",
        "expires_in": seconds,
        "expires_at": expiry,
        "user": USER,
    }


class SyntheticHttp:
    def __init__(self) -> None:
        self.account = dict(ACCOUNT)
        self.api_calls: list[tuple[str, str | None, object]] = []
        self.auth_calls: list[tuple[str, str, object]] = []
        self.unauthorized = False
        self.reject_consent = False
        self.hold_consent = False
        self.pending_consent: Route | None = None
        self.seconds = 3600

    @staticmethod
    def fulfill(route: Route, data: object, status: int = 200) -> None:
        route.fulfill(status=status, content_type="application/json", body=json.dumps(data))

    def auth(self, route: Route) -> None:
        request = route.request
        path = urlparse(request.url).path
        body = request.post_data_json if request.post_data else None
        self.auth_calls.append((request.method, path, body))
        if path.endswith("/token") or path.endswith("/verify"):
            self.fulfill(route, session(self.seconds))
        elif path.endswith("/signup"):
            self.fulfill(route, USER)
        elif path.endswith("/user"):
            self.fulfill(route, USER)
        elif path.endswith("/recover") or path.endswith("/logout"):
            self.fulfill(route, {})
        else:
            raise AssertionError(f"Unexpected synthetic auth operation: {path}")

    def api(self, route: Route) -> None:
        request = route.request
        path = urlparse(request.url).path
        if path.endswith("/capabilities"):
            self.fulfill(
                route,
                {
                    "data": {
                        "api_version": "1",
                        "watch": False,
                        "demo_reset": False,
                        "inference_available": False,
                        "deep_available": False,
                        "max_document_bytes": 1024,
                        "max_document_pages": 1,
                        "supported_lanes": ["SCHOLARSHIP_PROGRAM"],
                        "supported_document_types": ["application/pdf"],
                    },
                    "request_id": "synthetic-browser",
                },
            )
            return
        assert path == "/api/v1/me", path
        body = request.post_data_json if request.post_data else None
        self.api_calls.append((request.method, request.headers.get("authorization"), body))
        assert (
            request.headers.get("authorization")
            == f"Bearer {session(self.seconds)['access_token']}"
        )
        if self.unauthorized or (request.method == "PATCH" and self.reject_consent):
            status = 401 if self.unauthorized else 422
            route.fulfill(
                status=status,
                content_type="application/problem+json",
                body=json.dumps(
                    {
                        "type": "urn:benefitbridge:problem:validation-error",
                        "title": "Request rejected",
                        "detail": "Synthetic request rejected.",
                        "status": status,
                        "code": "UNAUTHORIZED" if status == 401 else "VALIDATION_ERROR",
                        "request_id": "synthetic-browser",
                        "retryable": False,
                        "errors": [],
                    }
                ),
            )
            return
        if request.method == "PATCH":
            assert body == {"consent_version": VERSION}
            if self.hold_consent:
                self.pending_consent = route
                return
            self.account = {
                **self.account,
                "consent": {
                    "version": VERSION,
                    "accepted_at": "2026-10-05T00:00:00Z",
                },
            }
        self.fulfill(route, {"data": self.account, "request_id": "synthetic-browser"})


def login(page: Page) -> None:
    page.get_by_label("Email", exact=True).fill("synthetic@example.invalid")
    page.get_by_label("Password", exact=True).fill("synthetic-password")
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page.get_by_role("heading", name="Welcome, Synthetic applicant")).to_be_visible()


def verify(base_url: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        errors: list[str] = []
        console: list[str] = []
        urls: list[str] = []

        def new_page(http: SyntheticHttp) -> Page:
            page = browser.new_page(viewport={"width": 390, "height": 1000})
            page.clock.install(time=NOW)
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda message: console.append(message.text))
            page.on("request", lambda request: urls.append(request.url))
            page.route(AUTH_ORIGIN + "/**", http.auth)
            page.route("**/api/v1/**", http.api)
            # SDK storage and the app must never touch persistent token storage.
            page.add_init_script("""
                for (const name of ['localStorage', 'sessionStorage']) {
                  Object.defineProperty(window, name, {get() {
                    throw new Error('Persistent storage was accessed');
                  }});
                }
            """)
            return page

        http = SyntheticHttp()
        page = new_page(http)
        page.goto(base_url + "/profile")
        expect(page.get_by_role("heading", name="Sign in to BenefitBridge")).to_be_visible()
        login(page)
        page.get_by_role("link", name="Review processing consent").click()
        expect(
            page.get_by_role("heading", name="Choose how your information is used")
        ).to_be_visible()
        expect(page.locator(".auth-notice")).to_have_text(NOTICE)
        assert page.locator(".auth-notice script").count() == 0
        assert page.evaluate("document.activeElement.tagName") == "H1"
        page.get_by_role("button", name="Decline", exact=True).click()
        page.get_by_role("link", name="Documents", exact=True).click()
        expect(page).to_have_url(base_url + "/consent")
        expect(
            page.get_by_text("You declined. Processing is blocked.", exact=False)
        ).to_be_visible()
        assert all(call[0] == "GET" for call in http.api_calls)
        page.get_by_role("checkbox").check()
        http.reject_consent = True
        page.get_by_role("button", name="Accept and continue").click()
        expect(page.get_by_role("alert")).to_contain_text("Synthetic request rejected.")
        assert page.get_by_role("link", name="Continue to your profile and goal").count() == 0
        http.reject_consent = False
        page.get_by_role("button", name="Accept and continue").click()
        page.get_by_role("link", name="Continue to your profile and goal").click()
        expect(page.get_by_role("heading", name="Your background and goal")).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.reload()
        expect(page.get_by_role("heading", name="Sign in to BenefitBridge")).to_be_visible()
        login(page)
        http.unauthorized = True
        page.get_by_role("link", name="Review processing consent").click()
        page.get_by_role("link", name="Profile", exact=True).click()
        expect(page.get_by_role("heading", name="Sign in to BenefitBridge")).to_be_visible()
        expect(page.get_by_text("Your session ended. Sign in again to continue.")).to_be_visible()
        page.close()

        http = SyntheticHttp()
        page = new_page(http)
        page.goto(base_url + "/account")
        login(page)
        page.get_by_role("link", name="Review processing consent").click()
        page.get_by_role("checkbox").check()
        http.hold_consent = True
        page.get_by_role("button", name="Accept and continue").click()
        expect(page.get_by_role("button", name="Recording consent…")).to_be_visible()
        page.get_by_role("link", name="Back to your account").click()
        page.get_by_role("button", name="Sign out", exact=True).click()
        expect(page.get_by_role("heading", name="Sign in to BenefitBridge")).to_be_visible()
        login(page)
        page.get_by_role("link", name="Review processing consent").click()
        page.get_by_role("button", name="Decline", exact=True).click()
        assert http.pending_consent is not None
        with page.expect_response(lambda response: response.request.method == "PATCH"):
            http.fulfill(
                http.pending_consent,
                {
                    "data": {
                        **ACCOUNT,
                        "consent": {"version": VERSION, "accepted_at": "2026-10-05T00:00:00Z"},
                    },
                    "request_id": "synthetic-browser",
                },
            )
        page.get_by_role("link", name="Profile", exact=True).click()
        expect(page).to_have_url(base_url + "/consent")
        expect(
            page.get_by_text("You declined. Processing is blocked.", exact=False)
        ).to_be_visible()
        page.close()

        http = SyntheticHttp()
        http.seconds = 5
        page = new_page(http)
        page.goto(base_url + "/account")
        login(page)
        page.get_by_role("link", name="Review processing consent").click()
        page.clock.run_for(6000)
        expect(page.get_by_role("heading", name="Sign in to BenefitBridge")).to_be_visible()
        page.close()

        http = SyntheticHttp()
        page = new_page(http)
        page.goto(base_url + "/account")
        page.get_by_role("button", name="Create account", exact=True).click()
        page.get_by_label("Email", exact=True).fill("synthetic@example.invalid")
        page.get_by_label("Password", exact=True).fill("synthetic-password")
        page.get_by_role("button", name="Create account", exact=True).click()
        expect(
            page.get_by_text("Check your inbox to confirm your email, then return to sign in.")
        ).to_be_visible()
        page.get_by_role("button", name="Forgot password?", exact=True).click()
        page.get_by_role("button", name="Send recovery email").click()
        expect(
            page.get_by_text("If an account can receive recovery email", exact=False)
        ).to_be_visible()
        page.goto(base_url + "/account/recovery#token_hash=synthetic_hash&type=recovery")
        expect(page.get_by_role("heading", name="Choose a new password")).to_be_visible()
        expect(page).to_have_url(base_url + "/account/recovery")
        assert page.evaluate("history.state") == {"idx": 0}
        assert not http.api_calls, "Recovery must not call application APIs with its bearer."
        page.get_by_label("New password", exact=True).fill("synthetic-new-password")
        page.get_by_role("button", name="Save new password").click()
        expect(page.get_by_role("heading", name="Sign in to BenefitBridge")).to_be_visible()
        expect(page).to_have_url(base_url + "/account")
        assert any(
            method == "PUT" and path.endswith("/user") for method, path, _ in http.auth_calls
        )
        page.goto(base_url + "/account/confirm#token_hash=synthetic_confirm&type=email")
        expect(page.get_by_role("heading", name="Your private account")).to_be_visible()
        expect(page).to_have_url(base_url + "/account/confirm")
        page.goto(
            base_url
            + "/account/recovery#access_token=synthetic-secret&refresh_token=synthetic-secret"
        )
        expect(page.get_by_role("alert")).to_contain_text("This email link is unavailable")
        expect(page).to_have_url(base_url + "/account/recovery")
        page.close()

        assert not errors, errors
        assert all(
            "synthetic-secret" not in message and "synthetic-refresh-secret" not in message
            for message in console
        ), console
        assert all(
            "access_token=" not in url and "refresh_token=" not in url and "token_hash=" not in url
            for url in urls
        ), urls
        browser.close()
    print(
        "PASS: real SDK login/signup/reset/recovery, consent decline/error/accept, "
        "bearer injection, stale consent isolation, "
        "401/expiry login, reload logout, callback sanitation, no persistent storage, mobile/focus"
    )


if __name__ == "__main__":
    verify(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5173")
