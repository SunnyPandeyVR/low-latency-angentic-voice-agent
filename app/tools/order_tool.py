import json
from pathlib import Path


ORDERS_FILE = Path(__file__).resolve().parents[2] / "data" / "orders.json"


def get_order_status(order_id: str) -> dict:
    """
    Retrieve order information.

    In production this would normally call an internal
    order-management API or database.
    """

    with open(ORDERS_FILE, "r", encoding="utf-8") as file:
        orders = json.load(file)

    for order in orders:
        if order["order_id"] == order_id:
            return {
                "found": True,
                "order": order,
            }

    return {
        "found": False,
        "order_id": order_id,
        "message": "Order not found.",
    }