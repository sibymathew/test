from common.db_models.common_models import SerializedDBModel


class Gateway(SerializedDBModel):
    meta = {
        "collection": "gateway",
        "indexes": [
            "#gateway_euid"
        ]
    }

    @classmethod
    def _return_serialized_data(cls, document, many=False):
        from common.db_models.gateway_serializers import GatewaySerializer
        gateway_obj = GatewaySerializer(data=document, many=many)
        gateway_obj.is_valid(raise_exception=True)
        return gateway_obj.data
