# Portal-Specific Playwright Preparation Adapters (Phase 10)

## 1. Overview & Architecture

The **Portal Adapters Subsystem** extends the Phase 9 generic Playwright preparation engine with isolated, robust, portal-specific adapters. Rather than attempting to support hundreds of arbitrary web pages with brittle selectors, this subsystem focuses on **high-reliability automation for the most prevalent ATS portals** (Greenhouse, Lever, Ashby, Workday, and Generic HTML forms).

Each adapter implements the [`BasePortalPreparationAdapter`](../adapter_base.py) abstract interface, isolating DOM selectors, portal layouts, and custom question handling.

```
app/services/preparation/
├── adapter_base.py              # BasePortalPreparationAdapter & context schemas
├── safety_guard.py              # PlaywrightSafetyGuard (universal invariants)
├── adapter_registry.py          # PreparationAdapterRegistry
├── preparation_engine.py        # Core BrowserPreparationEngine
└── adapters/
    ├── __init__.py
    ├── generic_adapter.py       # Heuristic fallback adapter
    ├── greenhouse_adapter.py    # boards.greenhouse.io adapter
    ├── lever_adapter.py         # jobs.lever.co adapter
    ├── ashby_adapter.py         # jobs.ashbyhq.com adapter
    ├── workday_adapter.py       # myworkdayjobs.com adapter
    └── README.md                # Architecture & Extension Guide
```

---

## 2. Non-Negotiable Global Safety Rules

Every adapter inherits from `BasePortalPreparationAdapter` and is bound by the **Global Safety Layer**:

1. **NO Final Submission**:
   - No adapter is permitted to click `button[type="submit"]`, `input[type="submit"]`, or any button matching `/submit|apply|send/i`.
   - The engine strictly halts in the `staged` state and captures a full-page screenshot.
2. **NO CAPTCHA / Bot Bypass**:
   - If Cloudflare Turnstile, reCAPTCHA, hCaptcha, or bot challenges are detected, the adapter halts execution with `status="blocked_by_captcha"`.
3. **NO Authentication Defeat**:
   - If an SSO wall or login screen is detected (e.g. Workday candidate login), the adapter pauses with `status="blocked_by_auth"`.
4. **Layout Change Resilience**:
   - If a portal's structure changes or required form fields cannot be found, the adapter records `unsupported_layout` and safely hands control to the user (`paused_for_human_input`).
5. **Prompt Injection Shield**:
   - DOM contents are treated strictly as untrusted text. Page instructions cannot alter system policy.

---

## 3. Supported Adapters & DOM Specifics

### A. Greenhouse Adapter (`GreenhousePreparationAdapter`)
- **Supported Domains**: `boards.greenhouse.io`, `*.greenhouse.io`, `grnh.se`.
- **Target Form**: `#application_form`, `#apply_form`.
- **Key Selectors**:
  - Name: `#first_name`, `#last_name`
  - Email & Phone: `#email`, `#phone`
  - Location: `#job_application_location`
  - Resume Upload: `input[type="file"]#resume`
  - Cover Letter: `textarea#cover_letter_text`
  - Social Profiles: `#linkedin`, `#github`, `#website`
  - Custom Screening: `#work_auth_yes`, `#sponsorship_no`, `.field`
- **Failure Hand-off**: If `#application_form` or core inputs are missing, execution halts with a screenshot for user review.

### B. Lever Adapter (`LeverPreparationAdapter`)
- **Supported Domains**: `jobs.lever.co`, `*.lever.co`.
- **Target Form**: `#lever-form`, `.application-form`.
- **Key Selectors**:
  - Name: `input[name="name"]`
  - Email & Phone: `input[name="email"]`, `input[name="phone"]`
  - Organization: `input[name="org"]`
  - Social Links: `input[name="urls[LinkedIn]"]`, `input[name="urls[GitHub]"]`, `input[name="urls[Portfolio]"]`
  - Resume Upload: `input[name="resume"][type="file"]`
  - Comments / Notes: `textarea[name="comments"]`
- **Failure Hand-off**: Unmatched required fields are cataloged in `unresolved_fields` and pause execution.

### C. Ashby Adapter (`AshbyPreparationAdapter`)
- **Supported Domains**: `jobs.ashbyhq.com`, `*.ashby.io`.
- **Target Form**: Ashby React application container.
- **Key Selectors**:
  - Name: `input[name*="name"]`, `input[name="_system_field_name"]`
  - Email: `input[name*="email"]`, `input[name="_system_field_email"]`
  - Phone: `input[name*="phone"]`, `input[name="_system_field_phoneNumber"]`
  - Resume Upload: `input[type="file"]`
- **Failure Hand-off**: If the dynamic layout fails to mount, execution pauses gracefully.

### D. Workday Adapter (`WorkdayPreparationAdapter`)
- **Supported Domains**: `*.myworkdayjobs.com`, `*.workday.com`.
- **Target Form**: Workday multi-step application wizard.
- **Key Selectors**:
  - First Name: `input[data-automation-id="legalNameSection_firstName"]`
  - Last Name: `input[data-automation-id="legalNameSection_lastName"]`
  - Email & Phone: `input[data-automation-id="email"]`, `input[data-automation-id="phone-number"]`
  - Location: `input[data-automation-id="addressSection_city"]`
  - Resume Upload: `input[type="file"][data-automation-id*="file"]`
- **Auth Wall Detection**: Detects `div[data-automation-id="signInPage"]` or password inputs and pauses for user login.

### E. Generic Adapter (`GenericPortalPreparationAdapter`)
- **Target Form**: Standard HTML5 forms.
- **Heuristic Discovery**: Inspects `input[type=text]`, `input[type=email]`, `input[type=tel]`, `input[type=file]`, `textarea`, `select`, `input[type=radio]`.

---

## 4. Extension Guide: Adding a New Adapter

To add an adapter for a new portal:

1. Create a new module `app/services/preparation/adapters/<portal>_adapter.py`.
2. Inherit from `BasePortalPreparationAdapter`.
3. Implement `portal_name`, `can_handle(portal_type, url)`, and `prepare(page, context)`.
4. Call `await self.check_global_safety_guards(page, context, start_time)` first.
5. Populate portal-specific selectors and upload the approved resume.
6. Run `guard_triggered = await self.verify_submit_guard(page)`.
7. Capture the audit screenshot using `await self.capture_screenshot(...)`.
8. Register the adapter in `app/services/preparation/adapter_registry.py`.
9. Add controlled HTML test fixtures and unit/integration tests in `backend/tests/`.
