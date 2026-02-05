def get_entry_product(client, entry_id: str) -> dict | None:
    payload = client.get(f"/orderentries/{entry_id}/product")
    return payload.get("data")
