from cnct import R
from reports.utils import (
    convert_to_datetime,
    get_asset_parameter,
    get_value,
)



def warm_up_tcs(client, products):
    rql_filter = R()
    rql_filter &= R().product.id.oneof(products)
    tcs = client.ns('tier').configs.filter(rql_filter).all()
    for tc in tcs:
        if not awsmpn.get(f'{tc["account"]["id"]}_{tc["product"]["id"]}'):
            for param in tc['params']:
                if param['id'] == 'awsApnId':
                    awsmpn[f'{tc["account"]["id"]}_{tc["product"]["id"]}'] = param.get('value', '-')



def generate(client, parameters, progress_callback):
    warm_up_tcs(client, parameters['products']['choices'])
    subscriptions_rql = R()
    if not parameters.get("products") or len(parameters['products']['choices']) < 1:
        raise RuntimeError("AWS products was not selected")
    if parameters.get("date"):
        subscriptions_rql &= R().events.created.at.ge(parameters['date']['after'])
        subscriptions_rql &= R().events.created.at.le(parameters['date']['before'])
    subscriptions_rql &= R().product.id.oneof(parameters['products']['choices'])
    subscriptions_rql &= R().status.ne('draft')
    subscriptions = client.assets.filter(subscriptions_rql)
    total_subscriptions = subscriptions.count()
    progress = 0
    for subscription in subscriptions:
        yield (
            subscription['id'],
            subscription.get('external_id', "-"),
            subscription['status'],
            subscription['marketplace']['name'],
            subscription['product']['id'],
            convert_to_datetime(subscription['events']['created']['at']),
            get_asset_parameter(subscription, "vendor_subscription_id"),
            get_asset_parameter(subscription, "customer_purchase_order_number")
           
        )
        progress += 1
        progress_callback(progress, total_subscriptions)
