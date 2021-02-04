__all__ = ['ControllerManager']

import time
import logging
import json

from spaceone.core.manager import BaseManager
from spaceone.spot_automation.manager.auto_scailing_manager import AutoScailingManager
from spaceone.spot_automation.manager.instance_manager import InstanceManager


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
        self.auto_scailing_manager: AutoScailingManager = self.locator.get_manager('AutoScailingManager')
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
        self.auto_scailing_manage.set_client(secret_data)

        if action == GET_ANY_UNPROTECTED_OD_INSTANCE:
            target_asg = command['resource_id']
            spot_group_option = command['spot_group_option']

            onDemand_info = self.auto_scailing_manager.getAnyUnprotectedOndemandInstance(target_asg, spot_group_option)
            res['instance_info'] = onDemand_info
            res['common_info'] = {
                'target_asg': target_asg,
                'ondemand_instance_id': onDemand_info['InstanceId']
            }
            return res

        elif action == CREATE_SPOT_INSTANCE:
            based_instance_id = command['common_info']['ondemand_instance_id']
            target_asg = command['common_info']['target_asg']
            candidate_instance_types_info = command['candidate_instance_types_info']
            price = command['price']

            spot_info = self.instance_manager.createSpotInstance(based_instance_id, target_asg, candidate_instance_types_info, price)
            res['response'] = spot_info
            res['common_info'] = {
                'spot_instance_id': spot_info['InstanceId']
            }
            return res

        elif action == IS_CREATED_SPOT_INSTANCE:
            spot_instance_id = command['common_info']['spot_instance_id']

            result = self.instance_manager.isCreatedSpotInstance(spot_instance_id)
            res['response'] = result
            return res

        elif action == DETACH_OD_INSTANCE:
            ondemand_instance_id = command['common_info']['ondemand_instance_id']
            target_asg = command['common_info']['target_asg']
            self.auto_scailing_manager.detachOdInstance(ondemand_instance_id, target_asg)

        elif action == ATTACH_SPOT_INSTANCE:
            spot_instance_id = command['common_info']['spot_instance_id']
            target_asg = command['common_info']['target_asg']
            self.auto_scailing_manager.attachSpotInstance(spot_instance_id, target_asg)

        elif action == TERMINATE_OD_INSTANCE:
            ondemand_instance_id = command['common_info']['ondemand_instance_id']
            self.instance_manager.terminateOdInstance(ondemand_instance_id)

        else:
            raise ERROR_NOT_FOUND(key='action', value=action)

        return res
