import logging

from spaceone.core.manager import BaseManager
from spaceone.spot_automation.connector.auto_scaling_connector import AutoScalingConnector
from spaceone.spot_automation.connector.ec2_connector import EC2Connector

_LOGGER = logging.getLogger(__name__)


class InstanceManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ec2_connector: EC2Connector = self.locator.get_connector('EC2Connector')
        self.auto_scaling_connector: AutoScalingConnector = self.locator.get_connector('AutoScalingConnector')

    def set_client(self, secret_data):
        self.ec2_connector.set_client(secret_data)
        self.auto_scaling_connector.set_client(secret_data)

    def get_ec2_instance(self, resource_id):
        return self.ec2_connector.get_ec2_instance(resource_id)

    def createSpotInstance(self, based_instance_id, target_asg, candidate_instance_types_info):
        based_info = self.get_ec2_instance(based_instance_id)
        _LOGGER.debug(f'[createSpotInstance] based_info: {based_info}')

        for candidate_type_info in candidate_instance_types_info:
            candidate_type = candidate_type_info['type']
            price = candidate_type_info['price']

            # Request input from based ondemand instance
            securityGroupIds = self._convertSecurityGroups(based_info['SecurityGroups'])
            tagList = self._generateTagsList(based_info['Tags'], target_asg)
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

                'SubnetId': based_info['SubnetId'],
                'TagSpecifications': tagList
            }

            
            instance = self.auto_scaling_connector.get_asg_instances(based_instance_id)
            if 'LaunchTemplate' in instance:
                #[TODO] Add input from launch template (ec2)
                launchTemplateId = instance['LaunchTemplateId']
                launchTemplateName = instance['LaunchTemplateName']
                launchTemplateVersion = instance['Version']
                input_request['LaunchTemplate'] = {
                    'LaunchTemplateId': launchTemplateId,
                    'Version': launchTemplateVersion
                }

            elif 'LaunchConfigurationName' in instance:
                #[TODO] Add input from launch configuration (asg)
                launchConfiguration = instance['LaunchConfigurationName']

            # Run instance with input
            spot_info = self.ec2_connector.run_instances(**input_request)

        return spot_info

    def isCreatedSpotInstance(self, instance_id):
        instanceState = self.ec2_connector.get_ec2_instance_status(instance_id)
        if instanceState == 'running':
            return True
        return False

    def terminateOdInstance(self, instance_id):
        self.ec2_connector.terminate_instances(instance_id)
        

    ######################
    # Internal
    ######################

    def _convertSecurityGroups(self, security_groups):
        groupIDs = []
        for sg in security_groups:
            groupIDs = append(groupIDs, sg.GroupId)
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
            if tag.Key != 'launched-by-alivespot' & tag.Key != "launched-for-asg":
                tags.Tags = append(tags.Tags, tag)
        return tags