import pytest

from src.proxy_processing.utils import parse_proxy_dict_from_string

#####################################################################
# two tests for critical function that parses proxy data from string
# it must work perfect or can cause problems
#####################################################################


# (data, expected result)
good_test_data = [
    ('socks4://127.0.0.1:9050', {'protocol': 'socks4', 'ip': '127.0.0.1', 'port': '9050', 'socks4': True}),
    ('1.2.3.5:1234', {'ip': '1.2.3.5', 'port': '1234'}),

    ('socks5://admin:secret@5.6.90.20:9060',
     {'protocol': 'socks5', 'username': 'admin', 'password': 'secret', 'ip': '5.6.90.20', 'port': '9060',
      'socks5': True})
]

bad_test_data = [
    ('invalid', 'invalid'),
    ('001.2.3.4:9050', '001.2.3.4:9050'),
    ('wrng://127.0.0.1:9050', 'wrng://127.0.0.1:9050'),
    ('socks4://127.0.0.1:90500000', 'socks4://127.0.0.1:90500000'),
    ('socks4://127.0.0.1:str', 'socks4://127.0.0.1:str'),
    (1, '1'),
    (True, 'True'),
    (1.23, '1.23'),
]


@pytest.mark.dependency()
@pytest.mark.parametrize("raw_string, expected", good_test_data)
def test_parse_proxy_dict_from_string_good(raw_string: str, expected: dict | str):
    assert expected == parse_proxy_dict_from_string(raw_string)


@pytest.mark.parametrize("raw_string, expected", bad_test_data)
def test_parse_proxy_dict_from_string_bad(raw_string: str, expected: dict | str):
    assert expected == parse_proxy_dict_from_string(raw_string)
