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
            return 'Success'
        return 'Fail'

    def run_instances(self, input):
        return self.ec2_connector.run_instances(input)

    def terminateOdInstance(self, instance_id):
        self.ec2_connector.terminate_instances(instance_id)

    def sortCandidateInfosByPrice(self, candidate_instance_types_info, az):
        candidateInfos = candidate_instance_types_info
        instance_types = []
        for candidate in candidate_instance_types_info:
            instance_types.append(candidate['type'])
        spotPriceHistory = self.ec2_connector.describe_spot_price_history(instance_types, az)
        spotPriceHistory.sort(key=lambda x: x['SpotPrice'], reverse=True)
        _LOGGER.debug(f'[sortCandidateInfosByPrice] spotPriceHistory: {spotPriceHistory}')

        for candidateInfo in candidateInfos:
            for spotInfo in spotPriceHistory:
                if spotInfo['InstanceType'] == candidateInfo['type']:
                    candidateInfo['spotPrice'] = spotInfo['SpotPrice']
        candidateInfos.sort(key=lambda x: x['spotPrice'])
        _LOGGER.debug(f'[sortCandidateInfosByPrice] candidateInfos: {candidateInfos}')

        return candidateInfos

    def getNetworkInterfaces(self, lt_id, ver):
        lt = self.ec2_connector.describe_launch_template_versions(lt_id, ver)
        if lt is not None and 'NetworkInterfaces' in lt['LaunchTemplateData']:
            nis = lt['LaunchTemplateData']['NetworkInterfaces']
            if len(nis) > 0:
                return True, nis

        return False, None