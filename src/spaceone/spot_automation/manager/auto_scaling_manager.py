import logging

from spaceone.core.manager import BaseManager
from spaceone.spot_automation.connector.auto_scaling_connector import AutoScalingConnector

_LOGGER = logging.getLogger(__name__)


class AutoScalingManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto_scaling_connector: AutoScalingConnector = self.locator.get_connector('AutoScalingConnector')

    def set_client(self, secret_data):
        self.auto_scaling_connector.set_client(secret_data)

    def getAutoScalingGroup(self, resource_id):
        autoScalingGroup = self.auto_scaling_connector.get_asg(resource_id)
        return autoScalingGroup

    def getAsgInstance(self, resource_id):
        instance = self.auto_scaling_connector.get_asg_instances(resource_id)
        return instance

    def detachOdInstance(self, instance_id, target_asg):
        self.auto_scaling_connector.detach_instances(instance_id, target_asg)

    def attachSpotInstance(self, instance_id, target_asg):
        self.auto_scaling_connector.attach_instances(instance_id, target_asg)
