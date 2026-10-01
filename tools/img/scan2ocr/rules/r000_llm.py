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
#
# The same number happens to be right for the local GLM-5.3-Flash on oMLX, for a
# different reason.  MEASURED on 8611 p99, prompt tokens billed for one image:
#
#     452x640     0.3 Mpx    408
#     910x1288    1.2 Mpx   1535
#    1821x2576    4.7 Mpx   3865     <- the cap
#    3642x5152   18.8 Mpx   3865     4x the pixels, same cost and same detail
#    2480x7016   17.4 Mpx   1941     a TALL strip gets LESS budget, not more
#
# So the image is capped at ~3865 tokens and 2576 px on the long edge already sits
# at the cap: sending more pixels buys nothing, and cropping to a long thin strip
# buys less than nothing.  To give a model more detail on a small region, crop so
# the REGION fills a roughly page-shaped frame.  Do not raise this constant
# expecting to read finer print.
IMAGE_LONG_EDGE = 2576
IMAGE_FORMAT = "PNG"

# WHAT A LOCAL MODEL IS AND IS NOT GOOD FOR.  GLM-5.3-Flash (oQ4e, multimodal,
# served by oMLX, no credentials) was measured against Opus on real pages, and the
# answer differs per TASK, not per model:
#
#   Transcribing what is printed -- TRUSTWORTHY.  8611 p99's frequency table
#   misprints the G# row: 485 is 0x1E5, so Lo-Hex should be E5 / 229, and the
#   magazine prints E3 / 227.  GLM returned E3 / 227 in 4 runs of 4, at both
#   efforts and both framings -- it read the paper instead of doing the
#   arithmetic, which is the whole requirement.  tesseract's text for that page
#   contains NEITHER value, so the answer came from the image alone.
#
#   Classifying page layout (step 020) -- NOT a substitute.  90.4% of block
#   labels, with the misses concentrated in toc, standalone listings and
#   page_kind.  See r020_classify.md.
#
#   reasoning_effort is an HONESTY dial, not a quality dial.  Asked for that same
#   G# row against p94, where the table stops at F# above a printed "Fortsetzung
#   auf Seite 99", `low` answered "Lo-Hex=F2 Lo-Dez=242" -- fabricated, plausible,
#   unhedged -- while `high` quoted the continuation note and declined.  Given a
#   crop of an unrelated article, `high` described what was actually in frame and
#   refused.  So: `low` for work whose answer is certainly in the image and is
#   checked by a script; `high` whenever "it is not here" is a possible answer.

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
