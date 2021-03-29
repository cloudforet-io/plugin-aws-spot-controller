__all__ = ['InterruptManager']

import logging
import time

from spaceone.core.manager import BaseManager
from spaceone.spot_automation.manager.events_manager import EventsManager
from spaceone.spot_automation.manager.sns_manager import SNSManager

_LOGGER = logging.getLogger(__name__)


class InterruptManager(BaseManager):

    def __init__(self, transaction):
        super().__init__(transaction)
        self.events_manager: EventsManager = self.locator.get_manager('EventsManager')
        self.sns_manager: SNSManager = self.locator.get_manager('SNSManager')

    def setup(self, endpoint, secret_data):
        _LOGGER.debug(f'[setup] endpoint: {endpoint}')
        _LOGGER.debug(f'[setup] secret_data: {secret_data}')

        self.events_manager.set_client(secret_data)
        self.sns_manager.set_client(secret_data)

        token = endpoint.split('/')[-1]
        topic_name = 'spaceone-interrupt-sns-' + token
        rule_name = 'spaceone-interrupt-event-' + token
        event_pattern = '{"source":["aws.ec2"], "detail-type":["EC2 Spot Instance Interruption Warning"]}'
        protocol = endpoint.split(':')[0]

        response = self.events_manager.putRule(rule_name, event_pattern)

        response = self.sns_manager.createTopic(topic_name)

        topic_arn = response['TopicArn']

        targets = [{
            'Id': str(int(time.time())),
            'Arn': topic_arn
        }]

        response = self.events_manager.putTargets(rule_name, targets)

        response = self.sns_manager.subscribe(topic_arn, protocol, endpoint)

        res = {}
        return res

    def confirm(self, data, secret_data):
        # TODO implementation
        _LOGGER.debug(f'[confirm] data: {data},secret_data: {secret_data}')
        res = {}
        return res

    def handle(self, data, secret_data):
        # TODO implementation
        _LOGGER.debug(f'[handle] data: {data},secret_data: {secret_data}')
        res = {}
        return res
