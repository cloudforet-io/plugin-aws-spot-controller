from schematics.models import Model
from schematics.types import ListType, DictType, StringType
from schematics.types.compound import ModelType

__all__ = ['PluginInitResponse']

_SUPPORTED_RESOURCE_TYPE = [
    'inventory.Server',
    'inventory.CloudService'
]


class PluginMetadata(Model):
    supported_resource_type = ListType(StringType, default=_SUPPORTED_RESOURCE_TYPE)


class PluginInitResponse(Model):
    _metadata = ModelType(PluginMetadata, default=PluginMetadata, serialized_name='metadata')
