# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, CloudBlue
# All rights reserved.
#

from connect.client import R

from reports.utils import convert_to_datetime, get_basic_value, get_value

HEADERS = (
    "Billing request  ID", "From", "To", "Delta", "Uom", "Billing Cycle", "Item Id", "Item Name",
    "Item Type", "Item Unit Of measure", "Item MPN", "Item Period", "Quantity", "Customer ID",
    "Customer Name", "Customer External ID", "Tier 1 ID", "Tier 1 Name", "Tier 1 Exrternal ID",
    "Tier 2 ID", "Tier 2 Name", "Tier 2 Exrternal ID","Provider ID", "Provider Name",
    "Vendor ID", "Vendor Name", "Product ID", "Product Name", "Subscription ID",
    "Subscription External ID", "Subscription Status", "Subscription Type",
    "Hub ID", "Hub Name"
)

def generate(
        client=None,
        parameters=None,
        progress_callback=None,
        renderer_type=None,
        extra_context_callback=None,
):
    requests = _get_requests(client, parameters)

    progress = 0
    total = requests.count()

    if renderer_type == 'csv':
        yield HEADERS

    for request in requests:
        connection = request['asset']['connection']
        for item in request['items']:
            result = (
                request['id'],
                convert_to_datetime(request['period']['from']),
                convert_to_datetime(request['period']['to']),
                get_basic_value(request['period'], 'delta'),
                get_basic_value(request['period'], 'uom'),
                get_basic_value(item['billing'], 'cycle_number'),
                get_basic_value(item, 'global_id'),
                get_basic_value(item, 'display_name'),
                get_basic_value(item, 'item_type'),
                get_basic_value(item, 'type'),
                get_basic_value(item, 'mpn'),
                get_basic_value(item, 'period'),
                get_basic_value(item, 'quantity'),
                get_value(request['asset']['tiers'], 'customer', 'id'),
                get_value(request['asset']['tiers'], 'customer', 'name'),
                get_value(request['asset']['tiers'], 'customer', 'external_id'),
                get_value(request['asset']['tiers'], 'tier1', 'id'),
                get_value(request['asset']['tiers'], 'tier1', 'name'),
                get_value(request['asset']['tiers'], 'tier1', 'external_id'),
                get_value(request['asset']['tiers'], 'tier2', 'id'),
                get_value(request['asset']['tiers'], 'tier2', 'name'),
                get_value(request['asset']['tiers'], 'tier2', 'external_id'),
                get_value(request['asset']['connection'], 'provider', 'id'),
                get_value(request['asset']['connection'], 'provider', 'name'),
                get_value(request['asset']['connection'], 'vendor', 'id'),
                get_value(request['asset']['connection'], 'vendor', 'name'),
                get_value(request['asset'], 'product', 'id'),
                get_value(request['asset'], 'product', 'name'),
                get_value(request, 'asset', 'id'),
                get_value(request, 'asset', 'external_id'),
                get_value(request, 'asset', 'status'),
                get_value(request['asset'], 'connection', 'type'),
                get_value(connection, 'hub', 'id') if 'hub' in connection else '',
                get_value(connection, 'hub', 'name') if 'hub' in connection else '',
            )
        if renderer_type == 'json':
            yield {
                HEADERS[idx].replace(' ', '_').lower(): value
                for idx, value in enumerate(result)
            }
        else:
            yield result
        progress += 1
        progress_callback(progress, total)


def _get_requests(client, parameters):
    query = R()
    query &= R().events.created.at.ge(parameters['date']['after'])
    query &= R().events.created.at.le(parameters['date']['before'])
    query &= R().asset.connection.provider.id.ne('PA-239-689')

    if parameters.get('product') and parameters['product']['all'] is False:
        query &= R().asset.product.id.oneof(parameters['product']['choices'])
    if parameters.get('mkp') and parameters['mkp']['all'] is False:
        query &= R().asset.marketplace.id.oneof(parameters['mkp']['choices'])
    if parameters.get('hub') and parameters['hub']['all'] is False:
        query &= R().asset.connection.hub.id.oneof(parameters['hub']['choices'])

    return client.ns('subscriptions').requests.filter(query)
