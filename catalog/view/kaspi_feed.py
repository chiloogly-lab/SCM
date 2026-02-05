from django.http import HttpResponse
from django.utils.xmlutils import SimplerXMLGenerator
from catalog.models import Product


def kaspi_feed(request):
    products = Product.objects.filter(kaspi_enabled=True)

    response = HttpResponse(
        content_type="application/xml; charset=utf-8"
    )

    xml = SimplerXMLGenerator(response, "utf-8")
    xml.startDocument()

    xml.startElement("kaspi_catalog", {})

    xml.startElement("company", {})
    xml.characters("ТОО ВАША КОМПАНИЯ")
    xml.endElement("company")

    xml.startElement("merchantid", {})
    xml.characters("ВАШ_MERCHANT_ID")
    xml.endElement("merchantid")

    xml.startElement("offers", {})

    for product in products:
        xml.startElement("offer", {"sku": product.sku})

        xml.startElement("model", {})
        xml.characters(product.name)
        xml.endElement("model")

        xml.startElement("price", {})
        xml.characters(str(product.purchase_price))  # временно
        xml.endElement("price")

        quantity = product.stock.quantity if hasattr(product, "stock") else 0

        xml.startElement("quantity", {})
        xml.characters(str(quantity))
        xml.endElement("quantity")

        if product.category:
            xml.startElement("category", {})
            xml.characters(product.category)
            xml.endElement("category")

        xml.endElement("offer")

    xml.endElement("offers")
    xml.endElement("kaspi_catalog")
    xml.endDocument()

    return response
