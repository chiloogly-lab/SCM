from orders.service.importer import KaspiOrderProcessor


class EventDispatcher:
    processors = {
        "kaspi.order.import": KaspiOrderProcessor(),
    }

    def dispatch(self, event):
        processor = self.processors.get(event.type)
        if not processor:
            return

        processor.process(event)
