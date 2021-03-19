import logging

from spaceone.api.spot_automation.plugin import history_pb2, history_pb2_grpc
from spaceone.core.pygrpc import BaseAPI

_LOGGER = logging.getLogger(__name__)


class History(BaseAPI, history_pb2_grpc.HistoryServicer):

    pb2 = history_pb2
    pb2_grpc = history_pb2_grpc

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('HistoryService', metadata) as history_svc:
            result = history_svc.get(params)
            _LOGGER.debug(f'[get] result: {result}')
            return self.locator.get_info('HistoryInfo', result)
