def get_order_entries(client, order_id: str) -> list[dict]:
    payload = client.get(f"/orders/{order_id}/entries")
    return payload.get("data", [])
