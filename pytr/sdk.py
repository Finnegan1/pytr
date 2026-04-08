"""SDK entry points for using pytr as a library.

This module exposes a non-interactive ``login()`` helper for SDK consumers.
Unlike :func:`pytr.account.login`, it never reads from stdin, never prompts
with ``getpass``, and never calls ``sys.exit``. The caller supplies all
credentials directly and provides a callback for retrieving the MFA code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, Union

from pytr.api import TradeRepublicApi

PathLike = Union[str, Path]


class LoginError(RuntimeError):
    """Raised when the SDK login helper cannot complete authentication."""


def login(
    phone_no: str,
    pin: str,
    *,
    get_mfa_code: Optional[Callable[[], str]] = None,
    web: bool = True,
    waf_token: Optional[str] = None,
    save_cookies: bool = False,
    cookies_file: Optional[PathLike] = None,
    keyfile: Optional[PathLike] = None,
    locale: str = "de",
) -> TradeRepublicApi:
    """Authenticate and return a ready-to-use :class:`TradeRepublicApi`.

    Performs no interactive I/O. The caller supplies credentials directly and
    provides a zero-arg callback that returns the MFA code as a string when web
    login requires one.

    Args:
        phone_no: Trade Republic phone number in international format
            (e.g. ``"+4912345678"``).
        pin: Trade Republic PIN.
        get_mfa_code: Zero-arg callback returning the 4-digit MFA code as a
            string. Required for web login when no resumable session exists.
        web: If ``True``, use web login (MFA via SMS/app). If ``False``, use app
            login (requires an existing device keyfile).
        waf_token: Optional pre-fetched AWS WAF token. If omitted, the
            underlying API will attempt to fetch one on construction.
        save_cookies: If ``True``, persist web session cookies between runs.
        cookies_file: Path used by ``save_cookies`` / ``resume_websession``. If
            ``None``, pytr's default (``~/.pytr/cookies.<phone>.txt``) is used.
        keyfile: Path to the device keyfile (.pem) used for app login.
        locale: API locale, defaults to ``"de"``.

    Returns:
        A logged-in :class:`TradeRepublicApi` instance. Callers use its async
        methods (``subscribe``/``recv``/``unsubscribe``/``close``) and can pass
        it to :class:`pytr.Timeline`.

    Raises:
        ValueError: web login needs an MFA code but ``get_mfa_code`` is
            ``None``, or the callback returned an empty string.
        LoginError: app login fails because no usable device keyfile is
            available.
    """
    tr = TradeRepublicApi(
        phone_no=phone_no,
        pin=pin,
        keyfile=str(keyfile) if keyfile else None,
        locale=locale,
        save_cookies=save_cookies,
        cookies_file=str(cookies_file) if cookies_file else None,
        waf_token=waf_token,
    )

    if web:
        # Try to resume an existing web session first when cookies are enabled.
        if save_cookies:
            try:
                if tr.resume_websession():
                    return tr
            except Exception:
                pass  # fall through to a fresh login

        tr.initiate_weblogin()  # raises ValueError on TR-side errors

        if get_mfa_code is None:
            raise ValueError(
                "Web login requires an MFA code; pass get_mfa_code=<callable> that returns the code as a string."
            )
        code = get_mfa_code()
        if not code:
            raise ValueError("get_mfa_code() returned an empty value.")
        tr.complete_weblogin(code)
        return tr

    # App login path: requires a device keyfile already on disk.
    try:
        tr.login()
    except (KeyError, AttributeError, FileNotFoundError) as e:
        raise LoginError(
            "App login failed: no usable device keyfile. Register this device "
            "by calling tr.initiate_device_reset() and then "
            "tr.complete_device_reset(token) with the SMS token yourself, "
            "then persist the generated keyfile."
        ) from e
    return tr
