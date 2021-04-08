__all__ = ['InterruptManager']

import logging
import time
import json
import requests

from spaceone.core.manager import BaseManager
from spaceone.spot_automation.manager.events_manager import EventsManager
from spaceone.spot_automation.manager.sns_manager import SNSManager
from spaceone.spot_automation.manager.auto_scaling_manager import AutoScalingManager
from spaceone.spot_automation.manager.instance_manager import InstanceManager

_LOGGER = logging.getLogger(__name__)


class InterruptManager(BaseManager):

    def __init__(self, transaction):
        super().__init__(transaction)
        self.events_manager: EventsManager = self.locator.get_manager('EventsManager')
        self.sns_manager: SNSManager = self.locator.get_manager('SNSManager')
        self.auto_scaling_manager: AutoScalingManager = self.locator.get_manager('AutoScalingManager')
        self.instance_manager: InstanceManager = self.locator.get_manager('InstanceManager')

    def setup(self, endpoint, secret_data):
        _LOGGER.debug(f'[setup] endpoint: {endpoint}')
        _LOGGER.debug(f'[setup] secret_data: {secret_data}')

        self.events_manager.set_client(secret_data)
        self.sns_manager.set_client(secret_data)

        token = endpoint.split('/')[-1]
        topic_name = 'spaceone-interrupt-sns-' + token[:20]
        rule_name = 'spaceone-interrupt-event-' + token[:20]
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
        _LOGGER.debug(f'[confirm] data: {data},secret_data: {secret_data}')

        data = json.loads(data)

        url = data['SubscribeURL']

        requests.get(url)

        res = {}
        return res

    def handle(self, data, secret_data):
        data = json.loads(json.loads(data)['Message'])
        # secret_data['region_name'] = data['region']
        _LOGGER.debug(f'[handle] data: {data},secret_data: {secret_data}')

        self.instance_manager.set_client(secret_data)
        self.auto_scaling_manager.set_client(secret_data)

        instance_id = data['detail']['instance-id']
        asg_name = self.instance_manager.getAutoScalingGroupNameFromTag(instance_id)

        if self.auto_scaling_manager.hasTerminationLifecycleHook(asg_name):
            self.auto_scaling_manager.terminateInstanceInAutoScalingGroup(instance_id)
        else:
            self.auto_scaling_manager.detachInstance(instance_id, asg_name)

        asg = self.auto_scaling_manager.getAutoScalingGroup(asg_name)
        instance = self.instance_manager.get_ec2_instance(instance_id)

        res = {
            'spot_group_resource_id': asg['AutoScalingGroupARN'],
            'resource_id': instance['InstanceId'],
            'type': instance['InstanceType']
        }

        return res
