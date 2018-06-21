- hosts: localhost
  gather_facts: no
  tasks:
    - name: Scalr Ceate Farm
      scalr_farm:
        scalr_url: 'https://demo.xxx.club'
        farmname: 'test1'
        envid: 1
        key_id: 'xxxx'
        key_secret: 'xxxxx'
        projectid: 'xxxx'
        action: 'create-farm'
        # action: 'delete-farm'
        # action: 'launch-farm'
        # action: 'terminate-farm'
      register: result
    - debug: var=result
