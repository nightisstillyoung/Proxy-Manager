from typing import Any
import pytest
from proxy_processing.models import ProxyModel
from src.proxy_processing.utils import parse_proxy_dict_from_string

################################################
# tests that convert function works as expected
# ORM model -> pydantic model
################################################


@pytest.mark.dependency(depends=["test_parse_proxy_dict_from_string_good"])
def test_model_to_pydantic():
    proxy_dict: dict[str, Any] = parse_proxy_dict_from_string("socks5://127.0.0.1:9050")
    proxy_dict.pop("protocol")
    proxy_dict.pop("unique_index")

    proxy_model: ProxyModel = ProxyModel(**proxy_dict)

    assert proxy_model.port == proxy_dict["port"]
    assert proxy_model.socks5 is True
    assert proxy_model.ip == proxy_dict["ip"]

