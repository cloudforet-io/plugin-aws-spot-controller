import logging

from spaceone.core.manager import BaseManager
from spaceone.spot_automation.connector.auto_scaling_connector import AutoScalingConnector
from spaceone.spot_automation.manager.instance_manager import InstanceManager

_LOGGER = logging.getLogger(__name__)


class AutoScailingManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto_scaling_connector: AutoScalingConnector = self.locator.get_manager('AutoScalingConnector')
        self.instance_manager: InstanceManager = self.locator.get_manager('InstanceManager')

    def set_client(self, secret_data):
        self.auto_scaling_connector.set_client(secret_data)

    def getAnyUnprotectedOndemandInstance(self, resource_id, spot_group_option):
        asg = self.getAutoScailingGroup(resource_id)
        for instance_info in asg['Instances']:
            isProtectedFromScaleIn = instance_info['ProtectedFromScaleIn']
            if isProtectedFromScaleIn:
                continue

            instance_id = instance_info['InstanceId']
            instance = instance_manager.get_ec2_instance(instance_id)
            lifeCycle = instance['InstanceLifecycle']
            if lifeCycle == 'spot':
                continue

            #[TODO] Add ondemand instance count check logic with spot_group_option
            
            return instance_info

        return {}

    def getAutoScailingGroup(self, resource_id):
        autoScailingGroup = self.auto_scaling_connector.get_asg(resource_id)
        return autoScailingGroup

    def getAsgInstance(self, resource_id):
        instance = self.auto_scaling_connector.get_asg_instances(resource_id)
        return instance

    def detachOdInstance(self, instance_id, target_asg):
        self.auto_scaling_connector.detach_instances(instance_id, target_asg)

    def attachSpotInstance(self, instance_id, target_asg):
        self.auto_scaling_connector.attach_instances(instance_id, target_asg)
