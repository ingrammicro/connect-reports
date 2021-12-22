from connect.client import R

def generate(
    client=None,
    parameters=None,
    progress_callback=None,
    renderer_type=None,
    extra_context_callback=None,
):
    syndication_group = 'PRG-5440-3996'
    products=client.ns(
        'catalog'
    ).collection(
        'groups'
    )[syndication_group].products.all().order_by('name')
    total_products = products.count()
    progress = 0
    for prod in products:
        product = client.products[prod['id']].get()
        output = {
            'id': product['id'],
            'name': product['name'],
            'vendor_id': product['owner']['id'],
            'vendor_name': product['owner']['name']
        }
        rql = R()
        rql &= R().product.id.eq(product['id'])
        rql &= R().status.eq('listed')
        listings = client.listings.filter(rql).all()
        marketplaces = []
        for listing in listings:
            marketplaces.append(
                {
                    'id': listing['contract']['marketplace']['id'],
                    'name': listing['contract']['marketplace']['name']
                }
            )
        output['marketplaces'] = marketplaces
        yield output
        progress += 1
        progress_callback(progress, total_products)
