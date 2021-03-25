import logging

from spaceone.core.manager import BaseManager
from spaceone.spot_automation.connector.pricing_connector import PricingConnector

_LOGGER = logging.getLogger(__name__)


class PricingManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pricing_connector: PricingConnector = self.locator.get_connector('PricingConnector')

    def set_client(self, secret_data):
        self.pricing_connector.set_client(secret_data)

    def getOndemandPrice(self, ondemand_instance_type, region):
        price_per_unit = self.pricing_connector.get_products(ondemand_instance_type, region)
        price_per_unit = float(price_per_unit)
        _LOGGER.debug(f'[getOndemandPrice] price_per_unit: {price_per_unit}')
        return price_per_unit
