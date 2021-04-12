__all__ = ['CostSavingManager']

import logging
import re

from spaceone.core.manager import BaseManager
from spaceone.core.error import *
from spaceone.spot_automation.manager.auto_scaling_manager import AutoScalingManager
from spaceone.spot_automation.manager.instance_manager import InstanceManager

_LOGGER = logging.getLogger(__name__)

OD_INSTANCE = 'scheduled'
SPOT_INSTANCE = 'spot'


class CostSavingManager(BaseManager):

    def __init__(self, transaction):
        super().__init__(transaction)
        self.auto_scaling_manager: AutoScalingManager = self.locator.get_manager('AutoScalingManager')
        self.instance_manager: InstanceManager = self.locator.get_manager('InstanceManager')

    def get(self, resource_id, secret_data):
        _LOGGER.debug(f'[get] resource_id: {resource_id}')
        self.auto_scaling_manager.set_client(secret_data)
        self.instance_manager.set_client(secret_data)

        asg_name = self._parse_asg_name(resource_id)
        asg = self.auto_scaling_manager.getAutoScalingGroup(asg_name)

        # Original ASG info
        originalInstanceType = ''
        desiredCapacity = asg['DesiredCapacity']
        if 'LaunchConfigurationName' in asg:
            lcName = asg['LaunchConfigurationName']
            lc = self.auto_scaling_manager.getLaunchConfiguration(lcName)
            originalInstanceType = lc['InstanceType']
        elif 'LaunchTemplate' in asg:
            ltId = asg['LaunchTemplate']['LaunchTemplateId']
            ltVer = asg['LaunchTemplate']['Version']
            lt = self.instance_manager.getLaunchTemplate(ltId, ltVer)
            originalInstanceType = lt['LaunchTemplateData']['InstanceType']
        normal = [
            {
                'type': originalInstanceType,
                'count': desiredCapacity
            }
        ]

        # Current ASG info
        saving = []
        spot_saving_infos = []
        od_saving_infos = []
        for instance_info in asg['Instances']:
            instance_id = instance_info['InstanceId']
            instance = self.instance_manager.get_ec2_instance(instance_id)
            instance_state = instance['State']['Name']
            instance_type = instance['InstanceType']
            if instance_state == 'running':
                # In case of spot instance
                if 'InstanceLifecycle' in instance and instance['InstanceLifecycle'] == SPOT_INSTANCE:
                    isDuplicate = self._countDuplicateInstanceType(spot_saving_infos, instance_type)
                    if isDuplicate:
                        continue

                    az = instance['Placement']['AvailabilityZone']
                    spotPriceInfos = self.instance_manager.sortCandidateInfosByPrice([instance_type], az)
                    cheapestSpotPrice = self._getCheapestSpotPrice(spotPriceInfos)

                    spot_saving_info = {
                        'type': instance_type,
                        'count': 1,
                        'price_per_hour': cheapestSpotPrice
                    }
                    spot_saving_infos.append(spot_saving_info)
                # In case of on-demand instance 
                else:
                    isDuplicate = self._countDuplicateInstanceType(od_saving_infos, instance_type)
                    if isDuplicate:
                        continue
                    od_saving_info = {
                        'type': instance_type,
                        'count': 1
                    }
                    od_saving_infos.append(od_saving_info)
        saving.extend(spot_saving_infos)
        saving.extend(od_saving_infos)

        res = {}
        res['cost_saving_info'] = {
            'resource_id': resource_id,
            'calc_dimensions': {
                'normal': normal,
                'saving': saving
            }
        }
        return res

    ######################
    # Internal
    ######################

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

    def _countDuplicateInstanceType(self, saving_infos, instance_type):
        if len(saving_infos) == 0:
            return False

        for info in saving_infos:
            if info['type'] == instance_type:
                info['count'] = info['count'] + 1 
                return True

        return False

    def _getCheapestSpotPrice(self, spotPriceInfos):
        if len(spotPriceInfos) == 0:
            raise Exception('Empty ppot price on history')

        for spotPriceInfo in spotPriceInfos:
            return float(spotPriceInfo['SpotPrice'])
