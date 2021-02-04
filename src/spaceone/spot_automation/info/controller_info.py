
__all__ = ['PluginInfo', 'ResourceInfo', 'ControllerVerifyInfo', 'RetryResourceStatusInfo', 'UpdateInfo', 'ResponseInfo']

import functools

from spaceone.api.spot_automation.plugin import controller_pb2
from spaceone.core.pygrpc.message_type import *

def ResourceInfo(resource_dict):
    return controller_pb2.ResourceInfo(**resource_dict)

def PluginInfo(result):
    result['metadata'] = change_struct_type(result['metadata'])
    return controller_pb2.PluginInfo(**result)

def ResponseInfo(result):
    result['data'] = change_struct_type(result['data'])
    return controller_pb2.ResponseInfo(**result)

def UpdateInfo(resource_dict):
    return controller_pb2.UpdateInfo(**resource_dict)

def RetryResourceStatusInfo(resource_dict):
    return controller_pb2.RetryResourceStatusInfo(**resource_dict)

def ControllerVerifyInfo(result):
    """ result
    {
     'options': {
        'a': 'b',
        ...
        'auth_type': 'google_oauth2'
    }
    """
    result['options'] = change_struct_type(result['options'])
    return controller_pb2.ControllerVerifyInfo(**result)
