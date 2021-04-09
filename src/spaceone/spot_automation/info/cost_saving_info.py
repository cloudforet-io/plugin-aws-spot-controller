__all__ = ['CostSavingInfo']

from spaceone.api.spot_automation.plugin import cost_saving_pb2
from spaceone.core.pygrpc.message_type import *

def CostSavingInfo(result):
    result['cost_saving_info'] = change_struct_type(result['cost_saving_info'])
    return cost_saving_pb2.CostSavingInfo(**result)
