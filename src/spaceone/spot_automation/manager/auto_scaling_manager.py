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

    def getAutoScalingGroup(self, asg_name):
        autoScalingGroup = self.auto_scaling_connector.get_asg(asg_name)
        return autoScalingGroup

    def getAsgInstance(self, instance_id):
        instance = self.auto_scaling_connector.get_asg_instances(instance_id)
        return instance

    def replaceOnDemandInstanceWithSpot(self, ondemand_instance_id, spot_instance_id, target_asg):
        asgInfo = self.getAutoScalingGroup(target_asg)
        desiredCapacity = asgInfo['DesiredCapacity']
        maxSize = asgInfo['MaxSize']

        # Attach Spot instance
        if desiredCapacity == maxSize:
            self._setAutoScalingMaxSize(target_asg, maxSize+1)
        self.auto_scaling_connector.attach_instances(spot_instance_id, target_asg)

        # Detach OnDemand instance
        self.auto_scaling_connector.detach_instances(ondemand_instance_id, target_asg)
        if desiredCapacity == maxSize:
            self._setAutoScalingMaxSize(target_asg, maxSize)

    def getLaunchConfiguration(self, lc_name):
        lc = self.auto_scaling_connector.describe_launch_configurations(lc_name)
        return lc

    ######################
    # Internal
    ######################

    def _setAutoScalingMaxSize(self, target_asg, max_size):
        self.auto_scaling_connector.update_auto_scaling_group(target_asg, max_size)