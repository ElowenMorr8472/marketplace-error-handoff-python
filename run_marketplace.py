import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from marketplace_errors import InfraiClient, OrderHandoff, handoff


def deliver(order: OrderHandoff) -> str:
    raise RuntimeError(f"carrier rejected handoff for {order.order_id}")


if __name__ == "__main__":
    order = OrderHandoff("ord-1042", "asset-77", "buyer-update-9")
    print(handoff(order, deliver, InfraiClient()))
