import time
import logging
from typing import Optional
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

from src.resume_job_matcher.processors.application_logger import (
    ApplicationLogger,
    STATUS_APPLIED,
    STATUS_FAILED,
    STATUS_MANUAL,
    STATUS_CAPTCHA,
)
from src.resume_job_matcher.chains.cover_letter_generator import generate_cover_letter

logger = logging.getLogger(__name__)

#  Timeouts 

NAV_TIMEOUT    = 20000   # page navigation
ELEMENT_WAIT   = 8000    # wait for element to appear
SUBMIT_WAIT    = 5000    # wait after submit click


#  Helpers 

def _get_board(url: str) -> str:
    domain = urlparse(url).netloc.replace("www.", "").lower()
    if "linkedin.com"  in domain: return "linkedin"
    if "indeed.com"    in domain: return "indeed"
    if "rozee.pk"      in domain: return "rozee"
    return "generic"


def _safe_fill(page: Page, selector: str, value: str, timeout: int = ELEMENT_WAIT) -> bool:
    """Fill a field safely. Returns True if filled, False if not found."""
    try:
        el = page.wait_for_selector(selector, timeout=timeout)
        if el:
            el.fill(value)
            return True
    except Exception:
        pass
    return False


def _safe_click(page: Page, selector: str, timeout: int = ELEMENT_WAIT) -> bool:
    try:
        el = page.wait_for_selector(selector, timeout=timeout)
        if el:
            el.click()
            return True
    except Exception:
        pass
    return False


def _has_captcha(page: Page) -> bool:
    content = page.content().lower()
    return any(x in content for x in [
        "captcha", "recaptcha", "i'm not a robot",
        "verify you are human", "security check",
    ])


def _attach_resume(page: Page, resume_path: str, selector: str) -> bool:
    try:
        el = page.query_selector(selector)
        if el:
            el.set_input_files(resume_path)
            return True
    except Exception:
        pass
    return False


#  LinkedIn Easy Apply 

def _apply_linkedin(page: Page, job: dict, profile: dict, cover_letter: str, resume_path: str) -> str:
    """
    Handle LinkedIn Easy Apply multi-step modal.
    Returns status string.
    """
    try:
        # Click Easy Apply button
        applied = _safe_click(page, "button.jobs-apply-button, button[data-control-name='jobdetails_topcard_inapply']")
        if not applied:
            return STATUS_MANUAL  # no Easy Apply button = external application

        time.sleep(2)

        if _has_captcha(page):
            return STATUS_CAPTCHA

        # Step through modal pages (LinkedIn has multi-step forms)
        for step in range(8):  # max 8 steps
            time.sleep(1.5)

            # Fill phone if field exists
            _safe_fill(page, "input[id*='phoneNumber'], input[name*='phone']", profile.get("phone", ""), timeout=2000)

            # Fill email
            _safe_fill(page, "input[id*='email'], input[name*='email']", profile.get("email", ""), timeout=2000)

            # Fill years of experience fields
            for sel in ["input[id*='experience'], input[id*='years']"]:
                _safe_fill(page, sel, str(profile.get("years_exp", "")), timeout=2000)

            # Attach resume if upload field appears
            _attach_resume(page, resume_path, "input[type='file']")

            # Fill cover letter textarea if it appears
            try:
                cl_area = page.query_selector("textarea[id*='cover'], textarea[name*='cover'], textarea[id*='message']")
                if cl_area:
                    cl_area.fill(cover_letter)
            except Exception:
                pass

            # Check for Submit button
            submit = page.query_selector("button[aria-label='Submit application'], button:has-text('Submit application')")
            if submit:
                submit.click()
                time.sleep(3)
                # Check for confirmation
                content = page.content().lower()
                if any(x in content for x in ["application submitted", "you've applied", "applied successfully"]):
                    return STATUS_APPLIED
                return STATUS_APPLIED  # assume applied if no error

            # Check for Next / Review button
            next_btn = page.query_selector("button[aria-label='Continue to next step'], button:has-text('Next'), button:has-text('Review')")
            if next_btn:
                next_btn.click()
                continue

            # No next, no submit — might be done or stuck
            break

        return STATUS_MANUAL

    except PlaywrightTimeout:
        return STATUS_FAILED
    except Exception as e:
        logger.warning(f"LinkedIn apply error: {e}")
        return STATUS_FAILED


#  Indeed Apply 

def _apply_indeed(page: Page, job: dict, profile: dict, cover_letter: str, resume_path: str) -> str:
    try:
        # Click Apply button
        applied = _safe_click(page, "button#indeedApplyButton, a.ia-IndeedApplyButton, button:has-text('Apply now')")
        if not applied:
            return STATUS_MANUAL

        time.sleep(2)

        if _has_captcha(page):
            return STATUS_CAPTCHA

        # Fill fields across steps
        for step in range(6):
            time.sleep(1.5)

            _safe_fill(page, "input[name='applicant.name'], input[id*='name']", profile.get("full_name", ""), timeout=2000)
            _safe_fill(page, "input[name='applicant.email'], input[id*='email']", profile.get("email", ""), timeout=2000)
            _safe_fill(page, "input[name='applicant.phoneNumber'], input[id*='phone']", profile.get("phone", ""), timeout=2000)

            _attach_resume(page, resume_path, "input[type='file']")

            try:
                cl_area = page.query_selector("textarea[name*='cover'], textarea[id*='cover']")
                if cl_area:
                    cl_area.fill(cover_letter)
            except Exception:
                pass

            # Submit
            submit = page.query_selector("button[type='submit']:has-text('Submit'), button:has-text('Submit your application')")
            if submit:
                submit.click()
                time.sleep(3)
                return STATUS_APPLIED

            # Next
            next_btn = page.query_selector("button:has-text('Continue'), button:has-text('Next')")
            if next_btn:
                next_btn.click()
                continue

            break

        return STATUS_MANUAL

    except PlaywrightTimeout:
        return STATUS_FAILED
    except Exception as e:
        logger.warning(f"Indeed apply error: {e}")
        return STATUS_FAILED


#  Rozee.pk Apply 

def _apply_rozee(page: Page, job: dict, profile: dict, cover_letter: str, resume_path: str) -> str:
    try:
        # Click Apply button
        applied = _safe_click(page, "a.apply-btn, button.apply-btn, a:has-text('Apply'), button:has-text('Apply Now')")
        if not applied:
            return STATUS_MANUAL

        time.sleep(2)

        if _has_captcha(page):
            return STATUS_CAPTCHA

        _safe_fill(page, "input[name='name'], input[id*='name']", profile.get("full_name", ""), timeout=3000)
        _safe_fill(page, "input[name='email'], input[id*='email']", profile.get("email", ""), timeout=3000)
        _safe_fill(page, "input[name='phone'], input[id*='phone']", profile.get("phone", ""), timeout=3000)

        _attach_resume(page, resume_path, "input[type='file']")

        try:
            cl_area = page.query_selector("textarea[name*='cover'], textarea[name*='message'], textarea")
            if cl_area:
                cl_area.fill(cover_letter)
        except Exception:
            pass

        submit = page.query_selector("button[type='submit'], input[type='submit'], button:has-text('Submit')")
        if submit:
            submit.click()
            time.sleep(3)
            return STATUS_APPLIED

        return STATUS_MANUAL

    except PlaywrightTimeout:
        return STATUS_FAILED
    except Exception as e:
        logger.warning(f"Rozee apply error: {e}")
        return STATUS_FAILED


#  Generic Form Apply 

def _apply_generic(page: Page, job: dict, profile: dict, cover_letter: str, resume_path: str) -> str:
    """
    Best-effort generic form filler for unknown career pages.
    Looks for common field patterns.
    """
    try:
        time.sleep(2)

        if _has_captcha(page):
            return STATUS_CAPTCHA

        # Try common name fields
        for sel in ["input[name*='name']", "input[id*='name']", "input[placeholder*='name' i]"]:
            if _safe_fill(page, sel, profile.get("full_name", ""), timeout=2000):
                break

        # Email
        for sel in ["input[type='email']", "input[name*='email']", "input[id*='email']"]:
            if _safe_fill(page, sel, profile.get("email", ""), timeout=2000):
                break

        # Phone
        for sel in ["input[type='tel']", "input[name*='phone']", "input[id*='phone']"]:
            if _safe_fill(page, sel, profile.get("phone", ""), timeout=2000):
                break

        # Resume upload
        _attach_resume(page, resume_path, "input[type='file']")

        # Cover letter
        for sel in ["textarea[name*='cover']", "textarea[name*='message']", "textarea[id*='cover']", "textarea"]:
            try:
                el = page.query_selector(sel)
                if el:
                    el.fill(cover_letter)
                    break
            except Exception:
                continue

        # Submit
        for sel in ["button[type='submit']", "input[type='submit']", "button:has-text('Apply')", "button:has-text('Submit')"]:
            try:
                el = page.query_selector(sel)
                if el:
                    el.click()
                    time.sleep(3)
                    return STATUS_APPLIED
            except Exception:
                continue

        return STATUS_MANUAL

    except Exception as e:
        logger.warning(f"Generic apply error: {e}")
        return STATUS_MANUAL


#  Main Apply Agent 

BOARD_HANDLERS = {
    "linkedin": _apply_linkedin,
    "indeed":   _apply_indeed,
    "rozee":    _apply_rozee,
    "generic":  _apply_generic,
}


def run_auto_apply(
    selected_jobs: list,
    profile: dict,
    candidate: dict,
    resume_path: str,
    api_key: str,
    app_logger: ApplicationLogger,
    progress_callback=None,
) -> ApplicationLogger:
    """
    Run auto-apply on a list of selected jobs.

    Args:
        selected_jobs:     List of job dicts selected by user in UI.
        profile:           User profile dict from UI form.
        candidate:         Candidate dict from Phase 1 pipeline.
        resume_path:       Absolute path to resume PDF on disk (temp file).
        api_key:           Gemini API key for cover letter generation.
        app_logger:        ApplicationLogger instance to record results.
        progress_callback: Optional fn(current, total, message) for UI updates.

    Returns:
        Updated ApplicationLogger with all results.
    """
    total = len(selected_jobs)
    cb = progress_callback or (lambda a, b, c: None)

    with sync_playwright() as p:
        # Visible browser — not headless
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )

        for i, job in enumerate(selected_jobs, 1):
            title   = job.get("title", "Unknown")
            company = job.get("company", "Unknown")
            url     = job.get("job_url", "")
            board   = _get_board(url)

            cb(i, total, f"Applying to: {title} at {company}")
            logger.info(f"[{i}/{total}] Applying [{board}]: {title} @ {company}")

            if not url:
                app_logger.log(url, title, company, board, STATUS_FAILED, "No URL")
                continue

            # Generate cover letter
            cb(i, total, f"Generating cover letter for {company}...")
            cover_letter = generate_cover_letter(job, profile, candidate, api_key)

            # Open job page
            page = context.new_page()
            try:
                page.goto(url, timeout=NAV_TIMEOUT, wait_until="domcontentloaded")
                time.sleep(2)

                if _has_captcha(page):
                    app_logger.log(url, title, company, board, STATUS_CAPTCHA, "Captcha on job page")
                    page.close()
                    continue

                # Route to correct handler
                handler = BOARD_HANDLERS.get(board, _apply_generic)
                status = handler(page, job, profile, cover_letter, resume_path)

                note = ""
                if status == STATUS_MANUAL:
                    note = "Complex form — apply manually"
                elif status == STATUS_CAPTCHA:
                    note = "Captcha encountered"

                app_logger.log(url, title, company, board, status, note)
                logger.info(f"  → {status}")

            except Exception as e:
                logger.warning(f"  → Error: {e}")
                app_logger.log(url, title, company, board, STATUS_FAILED, str(e))
            finally:
                try:
                    page.close()
                except Exception:
                    pass

            # Pause between applications
            time.sleep(3)

        browser.close()

    return app_logger