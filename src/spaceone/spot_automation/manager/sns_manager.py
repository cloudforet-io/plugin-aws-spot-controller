import logging

from spaceone.core.manager import BaseManager
from spaceone.spot_automation.connector.sns_connector import SNSConnector

_LOGGER = logging.getLogger(__name__)


class SNSManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sns_connector: SNSConnector = self.locator.get_connector('SNSConnector')

    def set_client(self, secret_data):
        self.sns_connector.set_client(secret_data)

    def createTopic(self, topic_name):
        response = self.sns_connector.create_topic(topic_name)
        return response

    def subscribe(self, topic_arn, protocol, endpoint):
        response = self.sns_connector.subscribe(topic_arn, protocol, endpoint)
        return response