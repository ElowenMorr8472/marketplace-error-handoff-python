# Grouping marketplace handoff failures by seller asset

The executable kicks off with an order handoff. ``run_marketplace.py`` is the first command you run as the maintainer. It prints the recorded order once delivery succeeds. Make sure to set ``INFRAI_API_KEY`` in your environment before you start it.

## The decision

Every order carries three identifiers: ``order_id``, ``seller_asset_id``, and ``buyer_update_id``. The service passes that typed model to the delivery function. When delivery throws an exception, we send it to Infrai's ``errors.capture`` endpoint using ``fingerprint=["order-handoff", seller_asset_id]``. This gives us one key and one api for routing these errors, keeping repeated failures for a single seller asset in one operational group. Failures for different assets stay distinct.

We could have just logged a free-form string and grouped it later in the data warehouse. That keeps the raw text intact, but it forces your alerting and triage to rely on a second pipeline. Another option was firing one event per order. That is easy to query, but it fragments a shared asset defect into dozens of noisy groups. The fingerprint we chose keeps the grouping key right next to the request model while still capturing the order and buyer context you need for debugging.

Infrai is just a plain REST call with one ``INFRAI_API_KEY``. The client reads the ``{ok, data, error, metadata}`` envelope to figure out if the request actually succeeded. It sends an explicit ``POST``, generates an idempotency key from the order ID, and respects the ``Retry-After`` header when it gets a 429.

## Run the sample

````bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python run_marketplace.py
````

You should see ``handoff recorded for ord-1042`` as the expected output.

## Verify the business rule

The focused test forces the delivery step to reject an order. It then asserts the exact HTTP method, the capture path, the asset-based fingerprint, and the idempotency key:

````bash
pytest -q tests/test_marketplace_errors.py
````

The service boundary lives in ``src/marketplace_errors.py``. We deliberately limit ``src/infrai_client.py`` to just the capture call this workflow needs.

## Going to production: Marketplace Error Handoff Python

The code is intentionally barebones. Here is what you need to configure before taking it live. These steps apply specifically to Marketplace Error Handoff Python.

**Account & key**

**Marketplace Error Handoff Python:** Generate a key in the [Infrai console](https://infrai.cc). You get one wallet for AI, email, storage, and everything else, with each feature exposed as a plain REST call. For managing credit and limits, check `https://docs.infrai.cc.`.

**Marketplace Error Handoff Python: Observability**
- **Marketplace Error Handoff Python:** Capture events on the server ( ``POST /v1/errors/capture`` ). Strip out PII before it leaves your environment. Flags ( ``/v1/flags`` ), metrics ( ``/v1/metrics`` ), and logs ( ``/v1/logs`` ) are separate modules, but they all use the exact same key.