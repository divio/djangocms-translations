# -*- coding: utf-8 -*-
import djclick as click

import json

from django.contrib.auth.models import User


from ...models import TranslationRequest


@click.command()
def command():
    with open('/app/addons-dev/djangocms-translations/fixture.json', 'r') as fh:
        content = json.load(fh)

    request = TranslationRequest.objects.create(
        user=User.objects.first(),
        provider_backend=TranslationRequest.PROVIDERS.SUPERTEXT,
        request_content=content,
    )

    quote = request.get_quote_from_provider()

    import ipdb
    ipdb.set_trace()

    # with open('request/headers.json', 'w') as fh:
    #     headers = dict(quote.request.headers.copy())
    #     headers['Authorization'] = u'Basic XXX'
    #     json.dump(headers, fh, indent=4, sort_keys=True)
    # with open('request/body.json', 'w') as fh:
    #     json.dump(json.loads(quote.request.body.decode('utf-8')), fh, indent=4, sort_keys=True)


#stefanie.weilenmann@divio.ch
#superdupertrans.12
