__all__ = ['HistoryInfo']

from spaceone.api.spot_automation.plugin import history_pb2
from spaceone.core.pygrpc.message_type import *

def HistoryInfo(result):
    result['history_info'] = change_struct_type(result['history_info'])
    return history_pb2.HistoryInfo(**result)
