from integrations.kaspi.importer import KaspiOrderImporter


def import_order_from_kaspi(raw_order: dict):
    """
    Единая точка импорта заказа Kaspi (реалтайм + backfill)
    """
    importer = KaspiOrderImporter()

    order, _ = importer.import_order(raw_order)

    if "entries" in raw_order:
        importer.import_items(order, raw_order["entries"])

    return order
