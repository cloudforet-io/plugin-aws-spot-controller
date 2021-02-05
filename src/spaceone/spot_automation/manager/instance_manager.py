import logging

from spaceone.core.manager import BaseManager
from spaceone.spot_automation.connector.ec2_connector import EC2Connector

_LOGGER = logging.getLogger(__name__)


class InstanceManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ec2_connector: EC2Connector = self.locator.get_connector('EC2Connector')

    def set_client(self, secret_data):
        self.ec2_connector.set_client(secret_data)

    def get_ec2_instance(self, resource_id):
        return self.ec2_connector.get_ec2_instance(resource_id)

    def isCreatedSpotInstance(self, instance_id):
        instanceState = self.ec2_connector.get_ec2_instance_status(instance_id)
        if instanceState == 'running':
            return True
        return False

    def run_instances(self, input):
        return self.ec2_connector.run_instances(input)

    def terminateOdInstance(self, instance_id):
        self.ec2_connector.terminate_instances(instance_id)