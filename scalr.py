#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import base64
import hmac
import datetime
import logging
import urllib
import hashlib
import os
import requests
import pytz
import json
from ansible.module_utils.basic import AnsibleModule

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

def image(url, client, stepaction, scope, envid, accountid, image_name, cloud_img_id, cloud_region, cloud, scalragentinstalled, cloud_feat_type, scalr_os_type, cloudinit, img_depricated):
    body = {
          "architecture": "x86_64",
          "cloudFeatures": {
            "type": cloud_feat_type
          },
          "cloudImageId": cloud_img_id,
          "cloudInitInstalled": cloudinit,
          "cloudLocation": cloud_region,
          "cloudPlatform": cloud,
          "deprecated": img_depricated,
          "name": image_name,
          "os": {
            "id": scalr_os_type
          },
          "scalrAgentInstalled": scalragentinstalled,
          "size": 1,
          "type": ""
        }

    data = client.list(url + "?name=" + image_name)
    if (len(data) == 1) and (stepaction == "delete-image"):
        imgid = data[0]["id"]
        delete_url = url + imgid
        data = client.delete(delete_url)
    elif (len(data) != 1) and (stepaction == "create-image"):
        data = client.post(url, json=body)

    return data

def role(url, client, stepaction, scope, envid, accountid, role_name, scalragentinstalled, scalr_os_type):
    body = {
              "builtinAutomation": [
                "base"
              ],
              "category": {
                "id": 1
              },
              "description": role_name,
              "name": role_name,
              "os": {
                "id": scalr_os_type
              },
              "quickStart": 'false',
              "useScalrAgent": scalragentinstalled
            }

    data = client.list(url + "?name=" + role_name)
    if (len(data) == 1) and (stepaction == "delete-role"):
        roleid = str(data[0]["id"])
        delete_url = url + roleid
        data = client.delete(delete_url)
    elif (len(data) != 1) and (stepaction == "create-role"):
        data = client.post(url, json=body)

    return data

def role_img(url, client, stepaction, scope, envid, accountid, role_name, scalragentinstalled, scalr_os_type, image_name):
    data = client.list(url + "roles/?name=" + role_name)
    roleid = str(data[0]["id"])
    imageinfo = client.list(url + "images/?name=" + image_name)
    imageid = str(imageinfo[0]["id"])

    body = { "image": {
                "id": imageid
              },
              "role": {
                "id": roleid
              }
            }

    url = url + "roles/" + roleid + "/images/" #+ imageid + "/actions/replace/"

    data = client.list(url)

    if (len(data) == 1):
        imgdata = str(data[0]["image"]["id"])
        if imgdata == imageid:
            data = "ok"
    else:
        data = client.post(url, json=body)

    return data

def farms(url, client, stepaction, farmname, projectid):
    body = {
      "name": farmname,
      "project": {
        "id": projectid
      },
    }

    data = client.list(url + "?name=" + farmname)

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
            data = client.post(url, json=body)

    return data

def farm_role(url, client, stepaction, farmrolename, baseurl, farm_role_template):
    body = json.loads(open(farm_role_template, 'r').read())

    data = client.list(url + "?alias=" + farmrolename)

    if len(data) == 1 and stepaction == "delete-farm-role":
        farmroleid = str(data[0]["id"])
        delete_url = baseurl + 'farm-roles/' + farmroleid + "/"
        data = client.delete(delete_url)
    elif len(data) != 1 and stepaction == "create-farm-role":
        data = client.post(url, json=body)

    return data

def getfarmid(url, client, farmname):
    url = url + 'farms/'
    data = client.list(url + "?name=" + farmname)
    return data

def main():
    module = AnsibleModule(
        argument_spec=dict(
            scalr_url=dict(required=False, type='str'),
            scope=dict(required=False, type='str', default='environment'),
            accountid=dict(required=False, type='str', default='0'),
            envid=dict(required=False, type='str', default='0'),
            key_id=dict(required=False, type='str'),
            key_secret=dict(required=False, type='str'),
            scalragentinstalled=dict(required=False, type='str'),
            role_name=dict(required=False, type='str'),
            scalr_os_type=dict(required=False, type='str'),
            action=dict(required=True, type='str'),
            image_name=dict(required=False, type='str'),
            cloud_region=dict(required=False, type='str'),
            cloud=dict(required=False, type='str'),
            cloud_img_id=dict(required=False, type='str'),
            cloudinit=dict(required=False, type='str'),
            img_depricated=dict(required=False, type='str', default='false'),
            farmname=dict(required=False, type='str'),
            projectid=dict(required=False, type='str'),
            instanceType=dict(required=False, type='str'),
            farmrolename=dict(required=False, type='str'),
            network_id=dict(required=False, type='str'),
            awssubnet=dict(required=False, type='str'),
            aws_sg=dict(required=False, type='str'),
            farm_role_template=dict(required=False, type='str'),
            )
        )

    try:
        url = module.params['scalr_url'] or os.environ['scalr_url']
    except KeyError as err:
        module.fail_json(msg='Unable to load %s' % err.message)

    try:
        key_id = module.params['key_id'] or os.environ['key_id']
    except KeyError as err:
        module.fail_json(msg='Unable to load %s' % err.message)

    try:
        key_secret = module.params['key_secret'] or os.environ['key_secret']
    except KeyError as err:
        module.fail_json(msg='Unable to load %s' % err.message)

    action = module.params['action']
    envid = module.params['envid']
    scope = module.params['scope']
    accountid = module.params['accountid']
    scalragentinstalled = module.params['scalragentinstalled']
    role_name = module.params['role_name']
    scalr_os_type = module.params['scalr_os_type']
    cloud_region = module.params['cloud_region']
    cloud = module.params['cloud']
    image_name = module.params['image_name']
    cloud_img_id = module.params['cloud_img_id']
    cloudinit = module.params['cloudinit']
    img_depricated = module.params['img_depricated']
    farmname = module.params['farmname']
    projectid = module.params['projectid']
    instanceType = module.params['instanceType']
    farmrolename = module.params['farmrolename']
    network_id = module.params['network_id']
    awssubnet = module.params['awssubnet']
    aws_sg = module.params['aws_sg']
    farm_role_template = module.params['farm_role_template']

    if cloud == "ec2":
        cloud_feat_type = "AwsImageCloudFeatures"
        cloud_feat_role = "AwsCloudFeatures"
    else:
        cloud_feat_type = "ImageCloudFeatures"

    # do the work
    client = ScalrApiClient(url, key_id, key_secret)

    if scope == 'global':
        url = '/api/v1beta0/global/'
    elif scope == 'account' and accountid != '':
        url = '/api/v1beta0/account/{accountId}/'
        params = {'accountId': accountid}
        url = url.format(**params)
    else:
        url = '/api/v1beta0/user/{envId}/'
        params = {'envId': envid}
        url = url.format(**params)

    if (action == "create-role") or (action == "delete-role"):
        url = url + 'roles/'
        res = role(url, client, action, scope, envid, accountid, role_name, scalragentinstalled, scalr_os_type)
    elif action == "role-add-image":
        res = role_img(url, client, action, scope, envid, accountid, role_name, scalragentinstalled, scalr_os_type, image_name)
    elif (action == "create-image") or (action == "delete-image"):
        url = url + 'images/'
        res = image(url, client, action, scope, envid, accountid, image_name, cloud_img_id, cloud_region, cloud, scalragentinstalled, cloud_feat_type, scalr_os_type, cloudinit, img_depricated)
    elif (action == "create-farm") or (action == "delete-farm") or (action == "launch-farm") or (action == "terminate-farm"):
        url = url + 'farms/'
        res = farms(url, client, action, farmname, projectid)
    elif (action == "create-farm-role") or (action == "delete-farm-role"):
        farmid = getfarmid(url, client, farmname)
        baseurl = url
        url = url + 'farms/{farmId}/farm-roles/'
        params = {'farmId': str(farmid[0]["id"])}
        url = url.format(**params)
        res = farm_role(url, client, action, farmrolename, baseurl, farm_role_template)

    response = {"output": res}
    module.exit_json(changed=False, meta=response)


if __name__ == '__main__':
    main()
