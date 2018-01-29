from a_service import ThreadHandler as superClass


class Service(superClass):
    def initialize(self, module, stopevent):
        self.module = module
        self.stopevent = stopevent
        self.module.add_event_listener('SUBSCRIBED_TO_RASPBOARD', self.share_services)
        self.module.add_event_listener('SERVICE_REGISTRY', self.add_remote_services)

    def share_services(self, event):
        if(event.origin_host != self.module.ip_address):
            return
        services = self.module.get_services('.*')
        serialized = []
        for service in services:
            s = service.copy()
            s.pop('handler', None)
            serialized.append(s)
        self.module.dispatch_event('SERVICE_REGISTRY', serialized)

    def add_remote_services(self, event):
        if(event.origin_host == self.module.ip_address):
            return
        for config in event.data:
            self.module.add_service(config)


config = {
    "service_name": "builtin/service_registry_share",
    "handler": Service,
    "service_type": "thread",
    "service_category": "system",
    "dependencies": [
    ]
}
