__all__ = ['ControllerManager']

import time
import logging
import json

from spaceone.core.manager import BaseManager
from spaceone.spot_automation.manager.auto_scaling_manager import AutoScalingManager
from spaceone.spot_automation.manager.instance_manager import InstanceManager

from spaceone.core.error import ERROR_NOT_FOUND


_LOGGER = logging.getLogger(__name__)

DEFAULT_REGION = 'us-east-1'

# Action list
GET_ANY_UNPROTECTED_OD_INSTANCE = "getAnyUnprotectedOndemandInstance"
CREATE_SPOT_INSTANCE = "createSpotInstance"
IS_CREATED_SPOT_INSTANCE = "IsCreatedSpotInstance"
DETACH_OD_INSTANCE= "detachOndemandInstance"
ATTACH_SPOT_INSTANCE= "attachSpotInstance"
TERMINATE_OD_INSTANCE= "terminateOnDemandInstance"

class ControllerManager(BaseManager):

    def __init__(self, transaction):
        super().__init__(transaction)
        self.auto_scaling_manager: AutoScalingManager = self.locator.get_manager('AutoScalingManager')
        self.instance_manager: InstanceManager = self.locator.get_manager('InstanceManager')

    def verify(self, secret_data, region_name):
        """ Check connection
        """
        ec2_connector = self.locator.get_connector('EC2Connector')
        r = ec2_connector.verify(secret_data, region_name)
        # ACTIVE/UNKNOWN
        return r

    def patch(self, secret_data, action, command):
        _LOGGER.debug(f'[patch] action: {action}')
        _LOGGER.debug(f'[patch] command: {command}')
        res = {}
        if 'common_info' in command:
            target_asg = ''
            ondemand_instance_id = ''
            spot_instance_id = ''
            if 'target_asg' in command['common_info']:
                target_asg = command['common_info']['target_asg']
            if 'ondemand_instance_id' in command['common_info']:
                ondemand_instance_id = command['common_info']['ondemand_instance_id']
            if 'spot_instance_id' in command['common_info']:
                spot_instance_id = command['common_info']['spot_instance_id']
            res = {
                'common_info': {
                    'target_asg': target_asg,
                    'ondemand_instance_id': ondemand_instance_id,
                    'spot_instance_id': spot_instance_id
                }
            }
        self.instance_manager.set_client(secret_data)
        self.auto_scaling_manager.set_client(secret_data)

        if action == GET_ANY_UNPROTECTED_OD_INSTANCE:
            asg_name = command['resource_id']
            spot_group_option = command['spot_group_option']

            onDemand_info = self._getAnyUnprotectedOndemandInstance(asg_name, spot_group_option)
            _LOGGER.debug(f'[patch] onDemand_info: {onDemand_info}')
            if onDemand_info == None:
                return None
            res['instance_info'] = onDemand_info
            res['common_info'] = {
                'target_asg': asg_name,
                'ondemand_instance_id': onDemand_info['InstanceId']
            }

        elif action == CREATE_SPOT_INSTANCE:
            based_instance_id = command['common_info']['ondemand_instance_id']
            target_asg = command['common_info']['target_asg']
            candidate_instance_types_info = command['candidate_instance_types_info']

            spot_info = self._createSpotInstance(based_instance_id, target_asg, candidate_instance_types_info)
            res['response'] = spot_info
            res['common_info'] = {
                'spot_instance_id': spot_info['InstanceId']
            }

        elif action == IS_CREATED_SPOT_INSTANCE:
            spot_instance_id = command['common_info']['spot_instance_id']

            result = self.instance_manager.isCreatedSpotInstance(spot_instance_id)
            res['response'] = result

        elif action == DETACH_OD_INSTANCE:
            ondemand_instance_id = command['common_info']['ondemand_instance_id']
            target_asg = command['common_info']['target_asg']
            self.auto_scaling_manager.detachOdInstance(ondemand_instance_id, target_asg)

        elif action == ATTACH_SPOT_INSTANCE:
            spot_instance_id = command['common_info']['spot_instance_id']
            target_asg = command['common_info']['target_asg']
            self.auto_scaling_manager.attachSpotInstance(spot_instance_id, target_asg)

        elif action == TERMINATE_OD_INSTANCE:
            ondemand_instance_id = command['common_info']['ondemand_instance_id']
            self.instance_manager.terminateOdInstance(ondemand_instance_id)

        else:
            raise ERROR_NOT_FOUND(key='action', value=action)

        return res

    ######################
    # Internal
    ######################

    def _getAnyUnprotectedOndemandInstance(self, asg_name, spot_group_option):
        asg = self.auto_scaling_manager.getAutoScalingGroup(asg_name)
        _LOGGER.debug(f'[_getAnyUnprotectedOndemandInstance] asg: {asg}')
        if asg == None:
            return None
        for instance_info in asg['Instances']:
            isProtectedFromScaleIn = instance_info['ProtectedFromScaleIn']
            if isProtectedFromScaleIn:
                continue

            instance_id = instance_info['InstanceId']
            instance = self.instance_manager.get_ec2_instance(instance_id)
            _LOGGER.debug(f'[_getAnyUnprotectedOndemandInstance] instance: {instance}')
            if 'InstanceLifecycle' in instance and instance['InstanceLifecycle'] == 'spot':
                continue

            #[TODO] Add ondemand instance count check logic with spot_group_option
            
            return instance_info

        return None

    def _createSpotInstance(self, based_instance_id, target_asg, candidate_instance_types_info):
        based_info = self.instance_manager.get_ec2_instance(based_instance_id)
        _LOGGER.debug(f'[_createSpotInstance] based_info: {based_info}')

        for candidate_type_info in candidate_instance_types_info:
            candidate_type = candidate_type_info['type']
            price = candidate_type_info['price']

            # Request input from based ondemand instance
            securityGroupIds = self._convertSecurityGroups(based_info['SecurityGroups'])
            tagList = self._generateTagsList(based_info['Tags'], target_asg)
            subnetId = ''
            if 'SubnetId' in based_info:
                subnetId = based_info['SubnetId']
            input_request = {
                'EbsOptimized': based_info['EbsOptimized'],

                'InstanceMarketOptions': {
                    'MarketType': 'spot',
                    'SpotOptions': {
                        'MaxPrice': price,
                    },
                },

                'InstanceType': candidate_type,
                'MaxCount': 1,
                'MinCount': 1,

                'Placement': based_info['Placement'],

                'SecurityGroupIds': securityGroupIds,

                'SubnetId': subnetId,
                'TagSpecifications': tagList
            }
            
            instance = self.auto_scaling_manager.getAsgInstance(based_instance_id)
            _LOGGER.debug(f'[_createSpotInstance] instance: {instance}')
            if 'LaunchTemplate' in instance:
                #[TODO] Add input from launch template (ec2)
                launchTemplate = instance['LaunchTemplate']
                launchTemplateId = launchTemplate['LaunchTemplateId']
                launchTemplateName = launchTemplate['LaunchTemplateName']
                launchTemplateVersion = launchTemplate['Version']
                input_request['LaunchTemplate'] = {
                    'LaunchTemplateId': launchTemplateId,
                    'Version': launchTemplateVersion
                }

            elif 'LaunchConfigurationName' in instance:
                #[TODO] Add input from launch configuration (asg)
                launchConfiguration = instance['LaunchConfigurationName']

            # Run instance with input
            _LOGGER.debug(f'[_createSpotInstance] input_request: {input_request}')
            spot_info = self.instance_manager.run_instances(input_request)

        return spot_info

    def _convertSecurityGroups(self, security_groups):
        groupIDs = []
        for sg in security_groups:
            groupId = sg['GroupId']
            groupIDs.append(groupId)
        return groupIDs

    def _generateTagsList(self, pre_tags, asg_name):
        tags = {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'launched-by-alivespot',
                    'Value': 'true',
                },
                {
                    'Key': 'launched-for-asg',
                    'Value': asg_name,
                }
            ]
        }
        #[TODO] Check tag info from launch template or launch configuration

        for tag in pre_tags:
            if tag['Key'] != 'launched-by-alivespot' and tag['Key'] != "launched-for-asg":
                tags['Tags'].append(tag)
        return tags