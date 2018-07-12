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
ansible-playbook -i localhost scalr.yml -e 'ansible_python_interpreter=/usr/local/bin/python3'


Playbook Operations:

# Roles

Actions:
- create-role
- delete-role

Ex) to Create a role
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

Ex) Create Farm Role

```yaml
    - name: Scalr Ceate FarmRole
      scalr:
        envid: 1
        farmid: 1
        farmrolename: test-role
        cloud: 'ec2'
        cloud_region: 'us-east-1'
        instanceType: t2.medium
        awsvpc: vpc-xxxx
        awssubnet: subnet-xxxx
        aws_sg: sg-xxxx
        role_name: testrole
        action: 'create-farm-role'
      register: result
    - debug: var=result
```
