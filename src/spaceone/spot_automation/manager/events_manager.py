import logging

from spaceone.core.manager import BaseManager
from spaceone.spot_automation.connector.events_connector import EventsConnector

_LOGGER = logging.getLogger(__name__)


class EventsManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events_connector: EventsConnector = self.locator.get_connector('EventsConnector')

    def set_client(self, secret_data):
        self.events_connector.set_client(secret_data)

    def putRule(self, rule_name, event_pattern):
        response = self.events_connector.put_rule(rule_name, event_pattern)
        return response

    def putTargets(self, rule_name, targets):
        response = self.events_connector.put_targets(rule_name, targets)
        return response