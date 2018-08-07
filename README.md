## Example playbook

How to use this library:

In your playbook folder create a new folder name "library", copy "scarl.py" in to the library folder.

# Prequistes:
PIP installed locally

# Python requirements
pip install pytz

# Environment variables required:
key_id

key_secret

scalr_url

# Example run:
ansible-playbook -i localhost scalr.yml -e 'scalr_url=https://demo.scalr.com key_id=xxxxxx key_secret=xxxx'

Playbook Operations:

# Roles

Actions:
- create-role
- delete-role

Ex) to Create a role
```yaml
---
- hosts: all
  gather_facts: no
  vars:
    scalr_url:
    key_id:
    key_secret:
  tasks:
    - package: name={{item}}
      with_items:
        - python3-pip
    - pip: name={{item}} state=latest
      with_items:
        - requests
        - pytz
    - name: Scalr Ceate Farm Role
      scalr:
        envid: 1
        key_id: "{{ key_id }}"
        key_secret: "{{ key_secret }}"
        scalr_url: "{{ scalr_url }}"
        scope: 'environment'
        scalragentinstalled: 'true'
        role_name: 'testrole'
        scalr_os_type: 'ubuntu-16-04'
        action: 'create-role'
      register: result
    - debug: var=result
```
Ex) to Delete a role
```yaml
- hosts: localhost
  gather_facts: no
  tasks:
    - name: Scalr Ceate Farm Role
      scalr:
        envid: 1
        scope: 'environment'
        scalragentinstalled: 'true'
        role_name: 'testrole'
        scalr_os_type: 'ubuntu-16-04'
        action: 'delete-role'
      register: result
    - debug: var=result
```

# Images:

Actions:
- create-image
- delete-image

Ex) Create Image
```yaml
    - name: Scalr Image
      scalr:
        envid: 1
        scope: 'environment'
        cloud_region: 'us-west-1'
        cloud: 'ec2'
        scalragentinstalled: 'true'
        image_name: 'deleteme'
        cloud_img_id: 'ami-8d948ced'
        scalr_os_type: 'ubuntu-16-04'
        cloudinit: 'true'
        img_depricated: 'false'
        action: 'create-image'
      register: result
    - debug: var=result
```

Ex) Delete Image
```yaml
    - name: Scalr Image
      scalr:
        envid: 1
        scope: 'environment'
        cloud_region: 'us-west-1'
        cloud: 'ec2'
        scalragentinstalled: 'true'
        image_name: 'deleteme'
        cloud_img_id: 'ami-8d948ced'
        scalr_os_type: 'ubuntu-16-04'
        cloudinit: 'true'
        img_depricated: 'false'
        action: 'delete-image'
      register: result
    - debug: var=result

```

# Farms

Actions:
- create-farm
- delete-farm
- launch-farm
- terminate-farm

Ex) Create a Farm
```yaml
    - name: Scalr Ceate Farm
      scalr:
        farmname: 'test1'
        envid: 1
        projectid: '1682b63d-6d28-4b5f-8438-3cf058f89a6c'
        action: 'create-farm'
      register: result
    - debug: var=result

```

Ex) Launch Farm

```yaml
    - name: Scalr Ceate Farm
      scalr:
        farmname: 'test1'
        envid: 1
        projectid: '1682b63d-6d28-4b5f-8438-3cf058f89a6c'
        action: 'launch-farm'
      register: result
    - debug: var=result
```

# FarmRole

Actions:
- create-farm-role
- delete-farm-role

Ex) Create Farm Role.

***Note*** to add flexiblity

```yaml
    - template: src="./templates/farm_role.json" dest="./test_role.json"
      with_items:
        - { farmrolename: test-role, role_name: docker-centos7, role_id: 1, cloud: ec2, cloud_region: us-east-1, instanceType: t2.small, network_id: vpc-xxx, awssubnet: subnet-6xxx, cloud_feat_role: AwsCloudFeatures, aws_sg: sg-xxxx }
    - name: Scalr Ceate FarmRole
      scalr:
        farmname: 'vmware-test1'
        envid: 6
        farmrolename: test-role
        farm_role_template: ./junk.json
        # action: 'create-farm-role'
        action: 'delete-farm-role'
      register: result
    - debug: var=result
```
Example teample for Farm-roles
```json
{
    "alias": "{{ item.farmrolename }}",
    "role": {
      "name": "{{ item.role_name }}",
      "deprecated": {},
      "id": "{{ item.role_id }}"
    },
    "cloudPlatform": "{{ item.cloud }}",
    "cloudLocation":"{{ item.cloud_region }}",
    "instanceType": {
      "id": "{{ item.instanceType }}"
    },
    "networking": {
      "networks": [{
        "id": "{{ item.network_id }}"
      }],
      "subnets": [{
        "id": "{{ item.awssubnet }}"
      }]
    },
    "cloudFeatures": {
      "type": "{{ item.cloud_feat_role }}",
      "ebsOptimized": "false"
    },
    "security": {
      "securityGroups": [{
        "id": "{{ item.aws_sg }}"
      }]
    }
}

```
