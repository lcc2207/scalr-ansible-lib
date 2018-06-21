#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import base64
import hmac
import datetime
import logging
import pytz
import requests
import urllib
import hashlib
import os
import collections
import json
import yaml

from ansible.module_utils.basic import *

logging.basicConfig(level=logging.INFO)

actions = {
    'create-farm': {
        'method': 'post',
        'url': '/api/v1beta0/user/{envId}/farms/'
    },
    'delete-farm': {
        'method': 'delete',
        'url': '/api/v1beta0/user/{envId}/farms/'
    },
    'launch-farm': {
        'method': 'post',
        'url': '/api/v1beta0/user/{envId}/farms/'
    },
    'terminate-farm': {
        'method': 'post',
        'url': '/api/v1beta0/user/{envId}/farms/'
    }
}

class ScalrApiClient(object):
    def __init__(self, api_url, key_id, key_secret):
        self.api_url = api_url
        self.key_id = key_id
        self.key_secret = key_secret
        self.logger = logging.getLogger("api[{0}]".format(self.api_url))
        self.session = ScalrApiSession(self)

    def list(self, path, **kwargs):
        data = []
        while path is not None:
            body = self.session.get(path, **kwargs).json()
            data.extend(body["data"])
            path = body["pagination"]["next"]
        return data

    def create(self, *args, **kwargs):
        return self.session.post(*args, **kwargs).json().get("data")

    def fetch(self, *args, **kwargs):
        return self.session.get(*args, **kwargs).json()["data"]

    def delete(self, *args, **kwargs):
        self.session.delete(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.session.post(*args, **kwargs).json()["data"]

class ScalrApiSession(requests.Session):
    def __init__(self, client):
        self.client = client
        super(ScalrApiSession, self).__init__()

    def prepare_request(self, request):
        if not request.url.startswith(self.client.api_url):
            request.url = "".join([self.client.api_url, request.url])
        request = super(ScalrApiSession, self).prepare_request(request)

        now = datetime.datetime.now(tz=pytz.timezone(os.environ.get("TZ", "UTC")))
        date_header = now.isoformat()

        url = urllib.parse.urlparse(request.url)

        # TODO - Spec isn't clear on whether the sorting should happen prior or after encoding
        if url.query:
            pairs = urllib.parse.parse_qsl(url.query, keep_blank_values=True, strict_parsing=True)
            pairs = [list(map(urllib.parse.quote, pair)) for pair in pairs]
            pairs.sort(key=lambda pair: pair[0])
            canon_qs = "&".join("=".join(pair) for pair in pairs)
        else:
            canon_qs = ""

        # Authorize
        sts = b"\n".join([
            request.method.encode('utf-8'),
            date_header.encode('utf-8'),
            url.path.encode('utf-8'),
            canon_qs.encode('utf-8'),
            request.body if request.body is not None else b""
        ])

        sig = " ".join([
            "V1-HMAC-SHA256",
            base64.b64encode(hmac.new(self.client.key_secret.encode('utf-8'), sts, hashlib.sha256).digest()).decode('utf-8')
        ])

        request.headers.update({
            "X-Scalr-Key-Id": self.client.key_id,
            "X-Scalr-Signature": sig,
            "X-Scalr-Date": date_header
        })

        self.client.logger.debug("URL: %s", request.url)
        self.client.logger.debug("StringToSign: %s", repr(sts))
        self.client.logger.debug("Signature: %s", repr(sig))

        return request

    def request(self, *args, **kwargs):
        res = super(ScalrApiSession, self).request(*args, **kwargs)
        self.client.logger.info("%s - %s", " ".join(args), res.status_code)
        self.client.logger.debug("Received response: %s", res.text)
        return res

def process_step(client, stepaction, envid, farmname, projectid):
    body = {
      "name": farmname,
      "project": {
        "id": projectid
      },
    }
    action = actions[stepaction]
    params = {'envId': envid}
    url = action['url'].format(**params)
    query = {'name':farmname}
    full_url = url + '?' + urllib.parse.urlencode(query)

    data = client.list(full_url)
    if len(data) == 1:
        farmid = str(data[0]["id"])
        if stepaction == "delete-farm":
            delete_url = url + farmid
            data = client.delete(delete_url)
        elif stepaction == "launch-farm":
            launch_url = url + farmid + '/actions/launch/'
            data = client.post(launch_url)
        elif stepaction == "terminate-farm":
            terminate_url = url + farmid + '/actions/terminate/'
            data = client.post(terminate_url)
    elif len(data) != 1:
        if stepaction == "create-farm":
            data = client.post(full_url, json=body)

    return data

def main():
    module = AnsibleModule(
        argument_spec = dict(
            scalr_url         = dict(required=True, type='str'),
            farmname          = dict(required=True, type='str'),
            envid             = dict(required=True, type='str'),
            key_id            = dict(required=True, type='str'),
            key_secret        = dict(required=True, type='str'),
            projectid         = dict(required=True, type='str'),
            action            = dict(required=True, type='str'),
            )
        )

    url = module.params['scalr_url']
    key_id = module.params['key_id']
    key_secret = module.params['key_secret']
    action = module.params['action']
    envid = module.params['envid']
    farmname = module.params['farmname']
    projectid = module.params['projectid']

    client = ScalrApiClient(url, key_id, key_secret)
    r = process_step(client, action, envid, farmname, projectid)

    response = {"output": r }
    module.exit_json(changed=False, meta=response)



if __name__ == '__main__':
    main()
