__all__ = ['HistoryManager']

import logging
import re

from spaceone.core.manager import BaseManager
from spaceone.spot_automation.manager.auto_scaling_manager import AutoScalingManager
from spaceone.spot_automation.manager.instance_manager import InstanceManager

_LOGGER = logging.getLogger(__name__)

OD_INSTANCE = 'scheduled'
SPOT_INSTANCE = 'spot'


class HistoryManager(BaseManager):

    def __init__(self, transaction):
        super().__init__(transaction)
        self.auto_scaling_manager: AutoScalingManager = self.locator.get_manager('AutoScalingManager')
        self.instance_manager: InstanceManager = self.locator.get_manager('InstanceManager')

    def get(self, resource_id, secret_data):
        _LOGGER.debug(f'[get_instance_count_status] resource_id: {resource_id}')
        self.auto_scaling_manager.set_client(secret_data)
        self.instance_manager.set_client(secret_data)

        asg_name = self._parse_asg_name(resource_id)
        asg = self.auto_scaling_manager.getAutoScalingGroup(asg_name)

        ondemandCount = self._get_instance_count(asg, OD_INSTANCE)
        spotCount = self._get_instance_count(asg, SPOT_INSTANCE)
        total = ondemandCount + spotCount
        res = {}
        res['history_info'] = {
            'ondemandCount': ondemandCount,
            'spotCount': spotCount,
            'total': total
        }
        return res

    def _get_instance_count(self, asg, lifecycle):
        _LOGGER.debug(f'[_get_instance_count] asg: {asg}')
        if asg is None:
            return 0
        cnt = 0
        instanceLifeCycle = lifecycle

        for instance_info in asg['Instances']:
            instance_id = instance_info['InstanceId']
            instance = self.instance_manager.get_ec2_instance(instance_id)
            state = instance['State']['Name']
            if lifecycle == SPOT_INSTANCE:
                if 'InstanceLifecycle' in instance and instance['InstanceLifecycle'] == instanceLifeCycle and state == 'running':
                    cnt += 1
            else:
                if ('InstanceLifecycle' not in instance or instance['InstanceLifecycle'] == instanceLifeCycle) and state == 'running':
                    cnt += 1
        return cnt

    def _parse_asg_name(self, resource_id):
        """
        ASG example : arn:aws:autoscaling:ap-northeast-2:431645317804:autoScalingGroup:41d6f9ef-59e3-49ea-bb53-ad464d3b320b:autoScalingGroupName/eng-apne2-cluster-banana
        """
        parsed_resource_id = ''
        _LOGGER.debug(f'[_parse_asg_name] resource_id: {resource_id}')
        try:
            parsed_resource_id = (re.findall('autoScalingGroupName/(.+)', resource_id))[0]
            _LOGGER.debug(f'[_parse_asg_name] parsed_resource_id: {parsed_resource_id}')
        except AttributeError as e:
            raise e

        return parsed_resource_id
