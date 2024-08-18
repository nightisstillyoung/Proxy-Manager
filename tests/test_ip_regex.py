import pytest
import re

from src.proxy_processing.regex import ip_expr

########################################################
# tests ip regex that is used for /search ip validation
# see /proxy/search
########################################################

ip_pattern = re.compile(ip_expr)

valid_ips = [
    "103.36.8.55",
    "69.60.116.241",
    "184.170.249.65",
    "255.255.255.255",
    "0.0.0.0"
]

invalid_ips = [
    "255.255.256.255",
    "69.60.012.241",
    "1.1.0.0.0",
]


@pytest.mark.parametrize("address", valid_ips)
def test_valid_addresses(address: str):
    assert bool(ip_pattern.match(address)) is True


@pytest.mark.parametrize("address", invalid_ips)
def test_invalid_addresses(address: str):
    assert bool(ip_pattern.match(address)) is False



