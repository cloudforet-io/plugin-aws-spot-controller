from spaceone.core.service import *
from spaceone.spot_automation.manager.history_manager import HistoryManager


@authentication_handler
class HistoryService(BaseService):
    def __init__(self, metadata):
        super().__init__(metadata)
        self.history_manager: HistoryManager = self.locator.get_manager('HistoryManager')

    @transaction
    @check_required(['resource_id', 'secret_data'])
    def get(self, params):
        secret_data = params['secret_data']
        resource_id = params['resource_id']

        res = self.history_manager.get(resource_id, secret_data)
        return res