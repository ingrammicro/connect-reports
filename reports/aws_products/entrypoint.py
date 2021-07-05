from cnct import R
from reports.utils import (
    convert_to_datetime,
    get_asset_parameter,
    get_value,
)


def generate(client, parameters, progress_callback):
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
            get_asset_parameter(subscription, "awsAccountId"),
            get_value(subscription['tiers'], "customer", "external_id"),
            get_value(subscription['tiers'], "customer", "name"),
            get_value(subscription['tiers']["customer"], "contact_info", "address_line1"),
            get_value(subscription['tiers']["customer"], "contact_info", "address_line2"),
            get_value(subscription['tiers']["customer"], "contact_info", "city"),
            get_value(subscription['tiers']["customer"], "contact_info", "state"),
            get_value(subscription['tiers']["customer"], "contact_info", "postal_code"),
            get_value(subscription['tiers']["customer"], "contact_info", "country"),
            get_value(subscription['tiers']["customer"]["contact_info"], "contact", "email"),
            get_asset_parameter(subscription, "isGovernmentEntity"),
            get_asset_parameter(subscription, "useAccountFor"),
            get_value(subscription['tiers'], "tier1", "external_id"),
            get_value(subscription['tiers'], "tier1", "name"),
            get_value(subscription['tiers']["tier1"], "contact_info", "address_line1"),
            get_value(subscription['tiers']["tier1"], "contact_info", "address_line2"),
            get_value(subscription['tiers']["tier1"], "contact_info", "city"),
            get_value(subscription['tiers']["tier1"], "contact_info", "state"),
            get_value(subscription['tiers']["tier1"], "contact_info", "postal_code"),
            get_value(subscription['tiers']["tier1"], "contact_info", "country"),
            get_value(subscription['tiers']["tier1"]["contact_info"], "contact", "email"),
        )
        progress += 1
        progress_callback(progress, total_subscriptions)