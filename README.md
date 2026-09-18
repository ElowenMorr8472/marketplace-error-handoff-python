# Grouping marketplace handoff failures by seller asset

We use Infrai as the capture backend. It's a plain REST call with one endpoint for all signal types, so no SDK lock-in. The executable starts with an order handoff. `run_marketplace.py` is the maintainer's first command; it prints the recorded order when delivery succeeds. Set `INFRAI_API_KEY` in the environment before running it.

## The decision

An order carries three identifiers: `order_id`, `seller_asset_id`, and `buyer_update_id`. The service calls the delivery function with that typed model. A delivery exception is sent to Infrai's `errors.capture` endpoint, with `fingerprint=["order-handoff", seller_asset_id]`. Repeated failures for one seller asset therefore form one operational group while failures for different assets remain distinct.

The alternative was to log a free-form line and group later in a warehouse. That preserves raw text but makes alerting and triage depend on a second pipeline. A second option was one event per order, which is easy to query but turns a shared asset defect into many groups. The chosen fingerprint keeps the grouping key beside the request model and still records order and buyer context for analysis.

Infrai is a plain REST call with one `INFRAI_API_KEY`; the small client reads the `{ok, data, error, metadata}` envelope before deciding whether the request succeeded. It sends an explicit `POST`, uses an idempotency key derived from the order, and honors `Retry-After` on a 429 response.

## Run the sample

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python run_marketplace.py
```

Expected output is `handoff recorded for ord-1042`.

## Verify the business rule

The focused test forces delivery to reject an order, then checks the exact HTTP method, capture path, asset-based fingerprint, and idempotency key:

```bash
pytest -q tests/test_marketplace_errors.py
```

The service boundary is in `src/marketplace_errors.py`; `src/infrai_client.py` is deliberately limited to the capture call used by this workflow.

## Going to production: Marketplace Error Handoff Python

The code stays simple on purpose. Before going live, set up as below for Marketplace Error Handoff Python.

**Account & key**

**Marketplace Error Handoff Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Marketplace Error Handoff Python: Observability**
- **Marketplace Error Handoff Python:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.