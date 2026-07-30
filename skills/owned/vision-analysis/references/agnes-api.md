# Agnes Vision Backend

## Request Contract

The current backend uses:

```text
POST https://apihub.agnes-ai.com/v1/chat/completions
Authorization: Bearer $AGNES_API_KEY
Content-Type: application/json
```

The user message contains one text part followed by one `image_url` part per image. Local images are converted in memory to MIME-qualified data URLs. Public HTTPS inputs remain URLs. Neither form is written to disk by the script.

## Retry Contract

- HTTP 429: retry indefinitely until success or process cancellation. Honor `Retry-After`; otherwise use exponential waits capped at 60 seconds.
- Network failure, per-request timeout, HTTP 408, or HTTP 5xx: retry three times after the initial failure with 1s, 2s, and 4s waits.
- HTTP 400, 401, 403, 404, 409, 422, and other non-429 4xx: fail immediately.
- Malformed successful response: fail immediately because repeating an accepted request does not establish correctness.

Each retry emits a sanitized progress event to stderr. Rate-limit waits have no fixed total duration.

## Evidence Contract

The result records:

- provider and model;
- sanitized API origin;
- local basename or URL origin/path without query and fragment;
- MIME, byte count when local, and SHA-256;
- total attempts, rate-limit events, and transient retries;
- response analysis and usage metadata.

The result never records:

- API key or authorization header;
- local absolute path;
- URL user information, query, or fragment;
- base64 or original image bytes;
- unbounded raw provider error bodies.

## Downstream Reasoning

When OpenCode must continue the task, append the JSON report as controller-provided visual evidence and run OpenCode as text reasoning. DeepSeek remains the primary reasoning model; explicit usage-limit evidence may switch that text run to Agnes.
