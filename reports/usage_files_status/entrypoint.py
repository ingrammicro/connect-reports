# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, CloudBlue
# All rights reserved.
#

from connect.client import R
from reports.utils import convert_to_datetime, get_value
from datetime import datetime

HEADERS = (
    'id',
    'vendor id',
    'vendor',
    'product id',
    'product',
    'provider id',
    'provider name',
    'marketplace id',
    'marketplace',
    'records uploaded',
    'records pending',
    'records accepted',
    'records closed',
    'created at',
    'accepted at',
    'closed at',
    'status',
)


def generate(
    client=None,
    parameters=None,
    progress_callback=None,
    renderer_type=None,
    extra_context_callback=None,
):
    usage_files = _get_uf(client, parameters)
    total = usage_files.count()
    progress = 0
    now = datetime.now()
    if renderer_type == 'csv':
        yield HEADERS
        total += 1
        progress += 1
        progress_callback(progress, total)
    for uf in usage_files:
        hours, rest = divmod((now - datetime.strptime(get_value(uf['events'], 'created', 'at'), '%Y-%m-%dT%H:%M:%S+00:00')).total_seconds(), 3600)
        if int(hours) <= 24:
            continue
        if renderer_type == 'json':
            yield {
                HEADERS[idx].replace(' ', '_').lower(): value
                for idx, value in enumerate(_process_line(uf))
            }
        else:
            yield _process_line(uf)
        progress += 1
        progress_callback(progress, total)


def _process_line(usage_file):
    return (
        usage_file['id'],
        usage_file['vendor']['id'],
        usage_file['vendor']['name'],
        usage_file['product']['id'],
        usage_file['product']['name'],
        usage_file['provider']['id'],
        usage_file['provider']['name'],
        usage_file['marketplace']['id'],
        usage_file['marketplace']['name'],
        usage_file['stats'].get('uploaded', 0),
        usage_file['stats'].get('pending', 0),
        usage_file['stats'].get('accepted', 0),
        usage_file['stats'].get('closed', 0),
        convert_to_datetime(get_value(usage_file['events'], 'created', 'at')),
        convert_to_datetime(get_value(usage_file['events'], 'accepted', 'at')),
        convert_to_datetime(get_value(usage_file['events'], 'closed', 'at')),
        usage_file['status'],
    )


def _get_uf(client, parameters):
    rql = R()
    rql &= R().status.oneof(['pending', 'accepted'])
    return client.ns('usage').collection('files').filter(rql).order_by('-created.at')