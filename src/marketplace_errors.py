from dataclasses import dataclass
from typing import Any, Callable
import traceback

from infrai_client import InfraiClient


@dataclass(frozen=True)
class OrderHandoff:
    order_id: str
    seller_asset_id: str
    buyer_update_id: str


def handoff(order: OrderHandoff, deliver: Callable[[OrderHandoff], Any], client: InfraiClient) -> Any:
    """Deliver an order and capture failures grouped by seller asset."""
    try:
        return deliver(order)
    except Exception as exc:
        client.capture(
            {
                "title": "order handoff failed",
                "message": str(exc),
                "level": "error",
                "fingerprint": ["order-handoff", order.seller_asset_id],
                "exception": traceback.format_exc(),
                "context": {
                    "order_id": order.order_id,
                    "seller_asset_id": order.seller_asset_id,
                    "buyer_update_id": order.buyer_update_id,
                },
            },
            request_id=f"handoff:{order.order_id}",
        )
        raise
