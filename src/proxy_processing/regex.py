import re

# IP
ip_expr = r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"

# Supported formats:
# ip:port
# username:password@ip:port
# protocol://username:password@ip:port
# and combinations
proxy_expression = re.compile(
    r"""^((?P<protocol>(socks(4|5|5h))|http(s)?)://)?
    ((?P<username>.+):(?P<password>.+)@)?
    (?P<ip>(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])):
    (?P<port>\d{1,5})$""",
    re.IGNORECASE | re.VERBOSE
)
