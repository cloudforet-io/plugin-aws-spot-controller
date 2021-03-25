__all__ = ['ControllerManager']

import time
import logging
import json
import re

from spaceone.core.manager import BaseManager
from spaceone.spot_automation.manager.auto_scaling_manager import AutoScalingManager
from spaceone.spot_automation.manager.instance_manager import InstanceManager
from spaceone.spot_automation.manager.pricing_manager import PricingManager

from spaceone.core.error import ERROR_NOT_FOUND


_LOGGER = logging.getLogger(__name__)

OD_INSTANCE = 'scheduled'
SPOT_INSTANCE = 'spot'

# Action list
GET_ANY_UNPROTECTED_OD_INSTANCE = "getAnyUnprotectedOndemandInstance"
CREATE_SPOT_INSTANCE = "createSpotInstance"
IS_CREATED_SPOT_INSTANCE = "IsCreatedSpotInstance"
REPLACE_OD_INSTANCE_WITH_SPOT = "replaceOnDemandInstanceWithSpot"
TERMINATE_OD_INSTANCE = "terminateOnDemandInstance"

class ControllerManager(BaseManager):

    def __init__(self, transaction):
        super().__init__(transaction)
        self.auto_scaling_manager: AutoScalingManager = self.locator.get_manager('AutoScalingManager')
        self.instance_manager: InstanceManager = self.locator.get_manager('InstanceManager')
        self.pricing_manager: PricingManager = self.locator.get_manager('PricingManager')

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
        _LOGGER.debug(f'[patch] secret_data: {secret_data}')
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
        self.pricing_manager.set_client(secret_data)

        response = 'Success'

        if action == GET_ANY_UNPROTECTED_OD_INSTANCE:
            resource_id = command['resource_id']
            asg_name = self._parse_asg_name(resource_id)
            spot_group_option = None
            if 'spot_group_option' in command:
                spot_group_option = command['spot_group_option']

            onDemand_info = self._getAnyUnprotectedOndemandInstance(asg_name, spot_group_option)
            _LOGGER.debug(f'[patch] onDemand_info: {onDemand_info}')
            if onDemand_info == None:
                res['choice_response'] = 'Fail'
            else:
                res['choice_response'] = 'Success'
                res['instance_info'] = onDemand_info
                res['common_info'] = {
                    'target_asg': asg_name,
                    'ondemand_instance_id': onDemand_info['InstanceId']
                }

        elif action == CREATE_SPOT_INSTANCE:
            based_instance_id = command['common_info']['ondemand_instance_id']
            target_asg = command['common_info']['target_asg']
            candidate_types = command['candidate_types']
            spot_info = self._createSpotInstance(based_instance_id, target_asg, candidate_types, secret_data['region_name'])
            _LOGGER.debug(f'[patch] spot_info: {spot_info}')
            if spot_info != None:
                res['common_info'] = {
                    'target_asg': target_asg,
                    'ondemand_instance_id': based_instance_id,
                    'spot_instance_id': spot_info['InstanceId']
                }

        elif action == IS_CREATED_SPOT_INSTANCE:
            spot_instance_id = command['common_info']['spot_instance_id']

            response = self.instance_manager.isCreatedSpotInstance(spot_instance_id)

        elif action == REPLACE_OD_INSTANCE_WITH_SPOT:
            ondemand_instance_id = command['common_info']['ondemand_instance_id']
            spot_instance_id = command['common_info']['spot_instance_id']
            target_asg = command['common_info']['target_asg']
            self.auto_scaling_manager.replaceOnDemandInstanceWithSpot(ondemand_instance_id, spot_instance_id, target_asg)

        elif action == TERMINATE_OD_INSTANCE:
            ondemand_instance_id = command['common_info']['ondemand_instance_id']
            self.instance_manager.terminateOdInstance(ondemand_instance_id)

        else:
            raise ERROR_NOT_FOUND(key='action', value=action)

        res['response'] = response

        return res

    def get_instance_count_status(self, resource_id, secret_data):
        _LOGGER.debug(f'[get_instance_count_status] resource_id: {resource_id}')
        self.auto_scaling_manager.set_client(secret_data)
        self.instance_manager.set_client(secret_data)

        asg_name = self._parse_asg_name(resource_id)
        asg = self.auto_scaling_manager.getAutoScalingGroup(asg_name)

        ondemandCount = self._getInstanceCount(asg, OD_INSTANCE)
        spotCount = self._getInstanceCount(asg, SPOT_INSTANCE)
        total = ondemandCount + spotCount
        res = {}
        res['history_info'] = {
            'ondemandCount': ondemandCount,
            'spotCount': spotCount,
            'total': total
        }
        return res

    ######################
    # Internal
    ######################

    def _getAnyUnprotectedOndemandInstance(self, asg_name, spot_group_option):
        asg = self.auto_scaling_manager.getAutoScalingGroup(asg_name)
        _LOGGER.debug(f'[_getAnyUnprotectedOndemandInstance] asg: {asg}')
        if asg == None:
            return None

        # Check minimum ondemand instance count with spot_group_option
        # TODO: RATIO type should be considered here
        if spot_group_option and 'min_ondemand' in spot_group_option and spot_group_option['min_ondemand']['type'] == 'COUNT':
            ondemandCount = self._getInstanceCount(asg, OD_INSTANCE)
            if spot_group_option['min_ondemand']['value'] >= ondemandCount:
                _LOGGER.debug(f'[_getAnyUnprotectedOndemandInstance] minimum OD count is less than request, ondemandCount: {ondemandCount}')
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
            
            return instance_info

        return None

    def _getInstanceCount(self, asg, lifecycle):
        _LOGGER.debug(f'[_getInstanceCount] asg: {asg}')
        if asg is None:
            return 0
        odNum = 0
        instanceLifeCycle = lifecycle

        for instance_info in asg['Instances']:
            instance_id = instance_info['InstanceId']
            instance = self.instance_manager.get_ec2_instance(instance_id)
            state = instance['State']['Name']
            if instanceLifeCycle == SPOT_INSTANCE:
                if 'InstanceLifecycle' in instance and instance['InstanceLifecycle'] == instanceLifeCycle and \
                state == 'running':
                    odNum += 1
            if instanceLifeCycle == OD_INSTANCE:
                if state == 'running':
                    if ('InstanceLifecycle' not in instance) or ('InstanceLifecycle' in instance and instance['InstanceLifecycle'] == instanceLifeCycle):
                        odNum += 1
        return odNum

    def _createSpotInstance(self, based_instance_id, target_asg, candidate_types, region):
        based_info = self.instance_manager.get_ec2_instance(based_instance_id)
        _LOGGER.debug(f'[_createSpotInstance] based_info: {based_info}')

        if based_info is None:
            raise ERROR_NOT_FOUND(key='based_info', value=based_info)

        az = based_info['Placement']['AvailabilityZone']
        candidate_infos = self.instance_manager.sortCandidateInfosByPrice(candidate_types, az)
        originalODPrice = self.pricing_manager.getOndemandPrice(based_info['InstanceType'], region)

        for candidate_info in candidate_infos:
            candidate_type = candidate_info['type']
            spotPrice = candidate_info['spotPrice']
            if spotPrice > originalODPrice:
                return None

            # Request input from based ondemand instance
            securityGroupIds = self._convertSecurityGroups(based_info['SecurityGroups'])
            subnetId = ''
            if 'SubnetId' in based_info:
                subnetId = based_info['SubnetId']
            input_request = {
                'EbsOptimized': based_info['EbsOptimized'],

                'InstanceMarketOptions': {
                    'MarketType': 'spot',
                    'SpotOptions': {
                        'MaxPrice': str(spotPrice),
                    },
                },

                'InstanceType': candidate_type,
                'MaxCount': 1,
                'MinCount': 1,

                'Placement': based_info['Placement'],

                'SecurityGroupIds': securityGroupIds,

                'SubnetId': subnetId
            }
            
            instance = self.auto_scaling_manager.getAsgInstance(based_instance_id)
            _LOGGER.debug(f'[_createSpotInstance] instance: {instance}')
            if 'LaunchTemplate' in instance:
                # Add input from launch template
                launchTemplate = instance['LaunchTemplate']
                launchTemplateId = launchTemplate['LaunchTemplateId']
                launchTemplateName = launchTemplate['LaunchTemplateName']
                launchTemplateVersion = launchTemplate['Version']
                input_request['LaunchTemplate'] = {
                    'LaunchTemplateId': launchTemplateId,
                    'Version': launchTemplateVersion
                }
                having, nis = self.instance_manager.getNetworkInterfaces(launchTemplateId, launchTemplateVersion)
                if having:
                    networkInterfaces = []
                    for ni in nis:
                        networkInterface = {
                            'AssociatePublicIpAddress': ni['AssociatePublicIpAddress'],
                            'SubnetId': subnetId,
                            'DeviceIndex': ni['DeviceIndex'],
                            'Groups': securityGroupIds
                        }
                        networkInterfaces.append(networkInterface)
                    input_request['NetworkInterfaces'] = networkInterfaces
                    input_request['SecurityGroupIds'] = None
                    input_request['SubnetId'] = None

            elif 'LaunchConfigurationName' in instance:
                # Add input from launch configuration
                lcName = instance['LaunchConfigurationName']
                lc = self.auto_scaling_manager.getLaunchConfiguration(lcName)
                if 'KeyName' in lc and lc['KeyName'] is not None:
                    input_request['KeyName'] = lc['KeyName']

                if 'IamInstanceProfile' in lc:
                    if 'arn:aws:iam:' in lc['IamInstanceProfile']:
                        input_request['IamInstanceProfile'] = {
                            'Arn': lc['IamInstanceProfile']
                        }
                    else:
                        input_request['IamInstanceProfile'] = {
                            'Name': lc['IamInstanceProfile']
                        }
                input_request['ImageId'] = lc['ImageId']
                input_request['UserData'] = lc['UserData']

                BDMs = self._convertBlockDeviceMappings(lc)
                if len(BDMs) > 0:
                    input_request['BlockDeviceMappings'] = BDMs

                if 'InstanceMonitoring' in lc:
                    input_request['Monitoring'] = {
                        'Enabled': lc['InstanceMonitoring']['Enabled']
                    }

                if 'AssociatePublicIpAddress' in lc or subnetId != None:
                    # Instances are running in a VPC
                    input_request['NetworkInterfaces'] = {
                        'AssociatePublicIpAddress': lc['AssociatePublicIpAddress'],
                        'DeviceIndex': 0,
                        'SubnetId': subnetId,
                        'Groups': securityGroupIds,
                    }
                    input_request['SecurityGroupIds'] = None
                    input_request['SubnetId'] = None

            tagList = self._generateTagsList(based_info['Tags'], target_asg, instance)
            input_request['TagSpecifications'] = [tagList]

            # Run instance with input
            _LOGGER.debug(f'[_createSpotInstance] input_request: {input_request}')
            spot_info = self.instance_manager.run_instances(input_request)
            _LOGGER.debug(f'[_createSpotInstance] spot_info: {spot_info}')
            if spot_info is None:
                continue
            else:
                return spot_info
        return None

    def _convertBlockDeviceMappings(self, lc):
        bds = []
        if lc is None or 'BlockDeviceMappings' not in lc or len(lc['BlockDeviceMappings']) == 0:
            _LOGGER.debug(f'[_convertBlockDeviceMappings] Missing block device mappings')
            return bds

        for lcBDM in lc['BlockDeviceMappings']:
            ec2BDM = {
                'DeviceName': lcBDM['DeviceName'],
                'VirtualName': lcBDM['VirtualName']
            }

            if 'Ebs' in lcBDM:
                ec2BDM['Ebs'] = {
                    'DeleteOnTermination': lcBDM['Ebs']['DeleteOnTermination'],
                    'Encrypted': lcBDM['Ebs']['Encrypted'],
                    'Iops': lcBDM['Ebs']['Iops'],
                    'SnapshotId': lcBDM['Ebs']['SnapshotId'],
                    'VolumeSize': lcBDM['Ebs']['VolumeSize'],
                    'VolumeType': lcBDM['Ebs']['VolumeType']
                }

            # Handle the noDevice field directly by skipping the device if set to true
            if 'NoDevice' in lcBDM and lcBDM['NoDevice']:
                continue
            bds.append(ec2BDM)

        return bds

    def _convertSecurityGroups(self, security_groups):
        groupIDs = []
        for sg in security_groups:
            groupId = sg['GroupId']
            groupIDs.append(groupId)
        return groupIDs

    def _generateTagsList(self, pre_tags, asg_name, instance):
        tags = {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'launched-by-alivespot',
                    'Value': 'true'
                },
                {
                    'Key': 'launched-for-asg',
                    'Value': asg_name
                }
            ]
        }

        # Append tag info about launch template or launch configuration
        if 'LaunchTemplate' in instance:
            launchTemplate = instance['LaunchTemplate']
            lt_tags = [
                {
                    'Key': 'LaunchTemplateID',
                    'Value': launchTemplate['LaunchTemplateId']
                },
                {
                    'Key': 'LaunchTemplateVersion',
                    'Value': launchTemplate['Version']
                }
            ]
            for lt_tag in lt_tags:
                tags['Tags'].append(lt_tag)
        elif 'LaunchConfigurationName' in instance:
            lc_tag = {
                'Key': 'LaunchConfigurationName',
                'Value': instance['LaunchConfigurationName']
            }
            tags['Tags'].append(lc_tag)

        for tag in pre_tags:
            if 'aws:' not in tag['Key'] and tag['Key'] != 'launched-by-alivespot' and \
                tag['Key'] != "launched-for-asg" and tag['Key'] != "LaunchTemplateID" and \
                tag['Key'] != "LaunchTemplateVersion" and tag['Key'] != "LaunchConfiguationName":
                tags['Tags'].append(tag)
        return tags

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