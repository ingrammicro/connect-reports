from datetime import datetime
from threading import Lock
from cnct import R
import math


def convert_to_datetime(param_value):
    if param_value == "" or param_value == "-":
        return "-"

    return datetime.strptime(
        param_value.replace("T", " ").replace("+00:00", ""),
        "%Y-%m-%d %H:%M:%S",
    )


def convert_to_datetime_subscription(param_value):
    return datetime.fromisoformat(param_value).strftime("%Y-%m-%d %H:%M:%S")

def get_basic_value(base, value):
    if base and value in base:
        return base[value]
    return '-'


def get_value(base, prop, value):
    if prop in base:
        return get_basic_value(base[prop], value)
    return '-'


def delta(a, b):
    if a == "unlimited" or b == "unlimited":
        if a == 0:
            return "disabled"
        return "enabled"

    a = int(a)
    b = int(b)

    if a == b:
        return 0
    elif (a < 0) and (b < 0) or (a > 0) and (b > 0):
        if a < b:
            return abs(abs(a) - abs(b))
        else:
            return -(abs(abs(a) - abs(b)))
    else:
        return math.copysign((abs(a) + abs(b)), b)


def get_parameter(request, param_id):
    for param in request["asset"]["params"]:
        if param["id"] == param_id:
            return param["value"]
    return "-"


def get_asset_parameter(asset, param_id):
    for param in asset["params"]:
        if param["id"] == param_id:
            return param["value"]
    return "-"


def get_ta_parameter(request, tier, param_id, client):
    try:
        rql = R().configuration.account.id.eq(request['asset']['tiers'][tier]['id'])
        rql &= R().status.eq('approved')
        rql &= R().product.id.eq(request['asset']['product']['id'])
        tc = client.ns('tier').collection("config-requests").filter(rql).order_by('-created').first()
        if 'params' not in tc:
            return "-"
        for param in tc['params']:
            if param["id"] == param_id:
                return param["value"]
    except Exception:
        pass
    return "-"


def today_str():
    return datetime.today().strftime('%Y-%m-%d %H:%M:%S')


class Progress:

    def __init__(self, callback, total):
        self.lock = Lock()
        self.current = 0
        self.total = total
        self.callback = callback

    def increment(self):
        self.lock.acquire()
        self.current += 1
        self.callback(self.current, self.total)
        self.lock.release()
