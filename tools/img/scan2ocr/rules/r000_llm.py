#!/usr/bin/env python3
"""
The one place scan2ocr talks to a model.

Two transports, chosen automatically:

  API  the Anthropic SDK, when credentials exist (ANTHROPIC_API_KEY, or an
       `ant auth login` profile that the zero-arg client picks up on its own).
       Preferred: real rate-limit handling with backoff, prompt caching across
       pages, and no dependency on an interactive session.
  CLI  `claude -p`, otherwise.  It inherits the Claude Code session's OAuth,
       which is what made this work with no key at all -- and also what made a
       token-refresh race take out pages 84-176 of one overnight run, since
       four concurrent processes share one credential file.

Both return plain text, so callers do not care which ran.

Prompt caching matters here out of proportion to its complexity: stage B sends
the SAME ~2 KB of instructions 176 times per sweep, once per page, and the
sweep has been re-run a dozen times while tuning.  Marking that block cached
bills it at roughly a tenth of the input rate after the first call.  The cache
is a PREFIX match, so the instructions must come first and the per-page digest
after -- putting the digest first would change the prefix on every page and
cache nothing.
"""

import base64
import io
import os
import subprocess
import time

from PIL import Image

# ---------------------------------------------------------------------------
# CONSTANTS  (no CLI knobs, no env knobs -- see CLAUDE.md)
# ---------------------------------------------------------------------------

# Claude Opus 5.  The classification is a judgement call about page layout that
# the cheaper tiers get wrong often enough to matter, and the whole issue is
# only ~350 calls per sweep.
MODEL = "claude-opus-5"
MAX_TOKENS = 8000

# The SDK already retries 429 and 5xx with exponential backoff; this raises its
# default of 2 because a sweep is 176 calls deep and a single give-up costs a
# whole page.
API_MAX_RETRIES = 6
API_TIMEOUT = 600.0

# Pages are 4960x7015 at 600 dpi -- far larger than any model reads.  Claude
# Opus 5 takes up to 2576 px on the long edge, so that is what is sent: the
# task is reading small print off a magazine page, and this is the most detail
# the model will accept.
IMAGE_LONG_EDGE = 2576
IMAGE_FORMAT = "PNG"

CLAUDE = "claude"
CLAUDE_TIMEOUT = 600

# Replies that mean "the service did not answer", never "the page says this".
SERVICE_ERRORS = ("session limit", "usage limit", "rate limit",
                  "Please run /login", "Invalid API key",
                  "Failed to authenticate", "OAuth session expired",
                  "credit balance", "Overloaded")
# ...of which these self-heal and are worth waiting out.  See RETRIES below.
TRANSIENT_ERRORS = ("Failed to authenticate", "OAuth session expired", "Overloaded")
RETRIES = 3
RETRY_WAIT = 45


class ServiceUnavailable(RuntimeError):
    """The service did not answer.  Distinct from a bad answer, because only
    one of the two is worth retrying or investigating per page."""


_client = None
_have_api = None


def api_available():
    """True when the SDK can authenticate.  An unset ANTHROPIC_API_KEY does not
    settle it -- the zero-arg client also picks up an `ant auth login` profile
    -- so this constructs a client and lets the SDK resolve credentials."""
    global _client, _have_api
    if _have_api is not None:
        return _have_api
    try:
        import anthropic
        _client = anthropic.Anthropic(max_retries=API_MAX_RETRIES, timeout=API_TIMEOUT)
        _have_api = bool(
            os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_AUTH_TOKEN")
            or os.path.exists(os.path.expanduser("~/.config/anthropic"))
        )
    except Exception:
        _have_api = False
    return _have_api


def _encode_image(path):
    """Downscale to what the model actually reads, and return base64 PNG."""
    im = Image.open(path)
    scale = IMAGE_LONG_EDGE / max(im.size)
    if scale < 1:
        im = im.resize((round(im.size[0] * scale), round(im.size[1] * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format=IMAGE_FORMAT)
    return base64.standard_b64encode(buf.getvalue()).decode("ascii")


def _call_api(instructions, payload, image_path):
    content = []
    if image_path:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png",
                       "data": _encode_image(image_path)},
        })
    content.append({"type": "text", "text": payload})

    r = _client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        # The instructions are identical on every page, so they are the cache
        # prefix; the per-page image and digest follow and are never cached.
        system=[{"type": "text", "text": instructions,
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": content}],
    )
    return "".join(b.text for b in r.content if b.type == "text").strip()


def _call_cli(instructions, payload, image_path, cwd):
    # The CLI reads the image off disk itself, so it is told the path instead of
    # being sent the bytes.  Kept out of the shared instructions so the API path
    # never sees a file path it cannot open.
    prompt = instructions
    if image_path:
        prompt += f"\n\nRead the image at {image_path} with the Read tool first."
    prompt += "\n\n" + payload
    # The CLI only reads inside its working directory, and this project's
    # scans and OCR working files live outside the repo (the issue descriptor
    # points at /Users/mist/DNB/<ISSUE>/tmp).  Without this the classify pass
    # fails on every page with "outside working dir, permission not granted"
    # and falls back to judging the digest with no picture at all.
    argv = [CLAUDE, "-p", prompt, "--output-format", "text"]
    if image_path:
        argv[1:1] = ["--add-dir", str(os.path.dirname(os.path.abspath(image_path)))]
    for attempt in range(RETRIES):
        r = subprocess.run(argv,
                           capture_output=True, text=True,
                           timeout=CLAUDE_TIMEOUT, cwd=cwd)
        out = r.stdout.strip()
        if not any(m in out for m in TRANSIENT_ERRORS) or attempt == RETRIES - 1:
            break
        time.sleep(RETRY_WAIT)
    for m in SERVICE_ERRORS:
        if m in out:
            raise ServiceUnavailable(out[:160])
    return out


def call(instructions, payload, image_path=None, cwd=None):
    """Ask the model.  `instructions` is the fixed part and is cached; `payload`
    is the per-page part.  Returns the reply as text."""
    if api_available():
        return _call_api(instructions, payload, image_path)
    return _call_cli(instructions, payload, image_path, cwd)


def transport():
    return "api" if api_available() else "cli"


if __name__ == "__main__":
    print(f"transport: {transport()}  model: {MODEL}")
