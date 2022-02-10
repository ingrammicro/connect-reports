from cnct import R
from reports.utils import (
    convert_to_datetime,
    Progress,
    delta,
    get_parameter,
    get_ta_parameter,
)
from concurrent import futures


def generate(client, parameters, progress_callback):
    subscriptions_rql = R()
    if not parameters.get("products") or len(parameters['products']['choices']) < 1:
        raise RuntimeError("Microsoft products was not selected")

    if parameters.get("date"):
        subscriptions_rql &= R().events.created.at.ge(parameters['date']['after'])
        subscriptions_rql &= R().events.created.at.le(parameters['date']['before'])
    subscriptions_rql &= R().status.eq("approved")
    subscriptions_rql &= R().type.eq("vendor")
    subscriptions_rql &= R().asset.product.id.oneof(parameters['products']['choices'])

    subscriptions = (
        client.ns('subscriptions')
        .collection('requests')
        .filter(subscriptions_rql)
        .order_by("-events.created.at")
    )
    total_subscriptions = subscriptions.count()

    request_types = ["purchase", "change", "cancel"]
    requests_rql = R()
    if parameters.get("date"):
        requests_rql &= R().created.ge(parameters['date']['after'])
        requests_rql &= R().created.le(parameters['date']['before'])
    requests_rql &= R().status.eq("approved")
    requests_rql &= R().asset.connection.type.eq('production')
    requests_rql &= R().asset.product.id.oneof(parameters['products']['choices'])
    requests_rql &= R().type.oneof(request_types)
    requests = client.requests.filter(requests_rql).order_by("-created")

    total_requests = requests.count()

    progress = Progress(progress_callback, total_subscriptions + total_requests)

    ex = futures.ThreadPoolExecutor()

    wait_for = []
    for request in requests:
        wait_for.append(
            ex.submit(
                get_request_record,
                client,
                request,
                progress,
            )
        )
        progress.increment()

    for future in futures.as_completed(wait_for):
        results = future.result()
        for result in results:
            yield result

    wait_for = []
    for subscription in subscriptions:
        wait_for.append(
            ex.submit(
                get_subscription_record,
                client,
                subscription,
                progress,
            )
        )

    for future in futures.as_completed(wait_for):
        results = future.result()
        for result in results:
            yield result


def get_request_record(client, request, progress):
    param_values = get_product_specifics(request, client)
    output = []
    for item in request["asset"]["items"]:
        try:
            if item["quantity"] == "0" and item["old_quantity"] == "0":
                continue
            output.append(
                [
                    request["type"].capitalize(),
                    request["id"],
                    request["asset"]["product"]["id"],
                    request["asset"]["product"]["name"],
                    request["asset"]["connection"]["vendor"]['id'],
                    request["asset"]["connection"]["vendor"]["name"],
                    convert_to_datetime(request["created"]),
                    convert_to_datetime(request["asset"]["events"]["created"]["at"]),
                    request["asset"]["id"],
                    request["asset"]["status"],
                    request["asset"]["external_id"],
                    request["asset"]["tiers"]["customer"]["name"],
                    (
                        request["asset"]["tiers"]["customer"]["external_id"]
                        if "external_id" in request["asset"]["tiers"]["customer"]
                        else request["asset"]["tiers"]["customer"]["external_uid"]
                    ),
                    request["asset"]["tiers"]["customer"]["contact_info"]["country"],
                    request["asset"]["tiers"]["tier1"]["name"],
                    (
                        request["asset"]["tiers"]["tier1"]["external_id"]
                        if "external_id" in request["asset"]["tiers"]["tier1"]
                        else request["asset"]["tiers"]["tier1"]["external_uid"]
                    ),
                    request["asset"]["tiers"]["tier1"]["contact_info"]["country"],
                    (
                        request["asset"]["tiers"]["tier2"]["name"]
                        if "name" in request["asset"]["tiers"]["tier2"]
                        else "-"
                    ),
                    (
                        request["asset"]["tiers"]["tier2"]["external_id"]
                        if "external_id" in request["asset"]["tiers"]["tier2"]
                        else "-"
                    ),
                    (
                        request["asset"]["tiers"]["tier2"]["contact_info"]["country"]
                        if request["asset"]["tiers"]["tier2"]
                           and "country" in request["asset"]["tiers"]["tier2"]["contact_info"]
                        else "-"
                    ),
                    item["global_id"],
                    item["mpn"],
                    item["display_name"],
                    item.get("period", item.get("item_type")),
                    item["old_quantity"],
                    item["quantity"],
                    delta(item["old_quantity"], item["quantity"]),
                    request["asset"]["connection"]["provider"]["id"],
                    request["asset"]["connection"]["provider"]["name"],
                    request["asset"]["marketplace"]["id"],
                    request["asset"]["marketplace"]["name"],
                    request["asset"]["contract"].get("type", "distribution").capitalize(),
                    param_values["microsoft_domain"],
                    param_values["subscription_id"],
                    param_values["ms_customer_id"],
                    param_values["microsoft_order_id"],
                    param_values["microsoft_plan_subscription_id"],
                    param_values["microsoft_tier1_mpn"],
                ]
            )
        except Exception:
            pass
    progress.increment()
    return output


def get_subscription_record(client, subscription, progress):
    param_values = get_product_specifics(subscription, client)
    output = []
    try:
        for item in subscription["items"]:
            output.append(
                [
                    subscription["type"].capitalize() + " Billing",
                    subscription["id"],
                    subscription["asset"]["product"]["id"],
                    subscription["asset"]["product"]["name"],
                    subscription["asset"]["connection"]["vendor"]['id'],
                    subscription["asset"]["connection"]["vendor"]["name"],
                    convert_to_datetime(subscription["events"]["created"]["at"]),
                    convert_to_datetime(subscription["asset"]["events"]["created"]["at"]),
                    subscription["asset"]["id"],
                    subscription["asset"]["status"],
                    subscription["asset"]["external_id"],
                    subscription["asset"]["tiers"]["customer"]["name"],
                    (
                        subscription["asset"]["tiers"]["customer"]["external_id"]
                        if "external_id" in subscription["asset"]["tiers"]["customer"]
                        else subscription["asset"]["tiers"]["customer"]["external_uid"]
                    ),
                    subscription["asset"]["tiers"]["customer"]["contact_info"]["country"],
                    subscription["asset"]["tiers"]["tier1"]["name"],
                    (
                        subscription["asset"]["tiers"]["tier1"]["external_id"]
                        if "external_id" in subscription["asset"]["tiers"]["tier1"]
                        else subscription["asset"]["tiers"]["tier1"]["external_uid"]
                    ),
                    subscription["asset"]["tiers"]["tier1"]["contact_info"]["country"],
                    (
                        subscription["asset"]["tiers"]["tier2"]["name"]
                        if "tier2" in subscription["asset"]["tiers"]
                        else "-"
                    ),
                    (
                        subscription["asset"]["tiers"]["tier2"]["external_id"]
                        if "tier2" in subscription["asset"]["tiers"]
                        else "-"
                    ),
                    (
                        subscription["asset"]["tiers"]["tier2"]["contact_info"]["country"]
                        if "tier2" in subscription["asset"]["tiers"]
                        else "-"
                    ),
                    item["global_id"],
                    item["mpn"],
                    item["display_name"],
                    item.get("period", item.get("item_type")),
                    0,
                    (
                        "unlimited" if item["quantity"] == -1 else item["quantity"]
                    ),
                    (
                        "unlimited" if item["quantity"] == -1 else item["quantity"]
                    ),
                    subscription["asset"]["connection"]["provider"]["id"],
                    subscription["asset"]["connection"]["provider"]["name"],
                    subscription["asset"]["marketplace"]["id"],
                    subscription["asset"]["marketplace"]["name"],
                    (
                        "Syndication"
                        if "CRU" in subscription["asset"]["contract"]["id"]
                        else "Distribution"
                    ),
                    param_values["microsoft_domain"],
                    param_values["subscription_id"],
                    param_values["ms_customer_id"],
                    param_values["microsoft_order_id"],
                    param_values["microsoft_plan_subscription_id"],
                    param_values["microsoft_tier1_mpn"],
                ]
            )
    except Exception:
        pass
    progress.increment()
    return output


def get_product_specifics(request, client):
    values = {
        "microsoft_domain": "-",
        "subscription_id": "-",
        "ms_customer_id": "-",
        "microsoft_order_id": "-",
        "microsoft_plan_subscription_id": "-",
        "microsoft_tier1_mpn": "-",
    }
    if request["asset"]["connection"]["vendor"]["id"] == "VA-888-104":
        values["microsoft_domain"] = get_parameter(request, "microsoft_domain")
        sub_id = get_parameter(request, "subscription_id")
        if sub_id == "-":
            sub_id = get_parameter(request, "microsoft_subscription_id")
        values["subscription_id"] = sub_id
        cust_id = get_parameter(request, "ms_customer_id")
        if cust_id == "-":
            cust_id = get_parameter(request, "customer_id")
        values["ms_customer_id"] = cust_id
        order_id = get_parameter(request, "microsoft_order_id")
        if order_id == "-":
            order_id = get_parameter(request, "csp_order_id")
        values["microsoft_plan_subscription_id"] = get_parameter(
            request,
            "microsoft_plan_subscription_id",
        )
        values["microsoft_order_id"] = order_id
        values["microsoft_tier1_mpn"] = get_ta_parameter(request, "tier1", "tier1_mpn", client)
    return values
