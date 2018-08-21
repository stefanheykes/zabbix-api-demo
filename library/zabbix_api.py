#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, sysfive.com GmbH
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'none'}


DOCUMENTATION = '''
---
module: zabbix_api
short_description: Zabbix API Wrapper Module
description:
   - Call the Zabbix API
   - This is an ugly ansible module that does not follow the guide, but should work quickly as intended
   - For additional reference see Zabbix API Documentation: https://www.zabbix.com/documentation/3.4/manual/api
     and zabbix-api https://pypi.python.org/pypi/zabbix-api/0.5.3
version_added: "---"
author:
    - "Stefan Heykes"
requirements:
    - "python >= 2.6"
    - zabbix-api
options:
    api_object:
        description:
            - Zabbix Object Type (for example host, screen... see Zabbix API Documentation for reference)
        required: true
        default: "host"
        choices: see docs
    api_method:
        description:
            - Method that shall be executed (for example get, update... see API Docs)
        required: true
    api_options:
        description:
            - Method options - see API Docs for what is supported

extends_documentation_fragment:
    - zabbix

'''

EXAMPLES = '''
- hosts: all
  gather_facts: no
  tasks:
    - name: Download all templates
      local_action:
        module: zabbix_api
        server_url: "http://{{ zabbix_cluster_ip }}:9595/"
        login_user: "{{ zabbix_apiuser }}"
        login_password: "{{ zabbix_apipw }}"
        api_object: "template"
        api_method: "get"
        api_options: {"output": "extend"}
      register: templates_json
'''

try:
    from zabbix_api import ZabbixAPI, ZabbixAPISubClass
    from zabbix_api import Already_Exists

    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False

from ansible.module_utils.basic import AnsibleModule

def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            api_object=dict(type='str', required=True),
            api_method=dict(type='str', required=True),
            api_options=dict(type='dict', required=True),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=False
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing required zabbix-api module (check docs or install with: pip install zabbix-api)")

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    api_object = module.params['api_object']
    api_method = module.params['api_method']
    api_options = module.params['api_options']
    timeout = module.params['timeout']

    zbx = None

    # login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                        validate_certs=validate_certs)
        zbx.login(login_user, login_password)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    # select API Query based on parameters and execute it
    zbx_obj = getattr(zbx, api_object)
    zbx_method = getattr(zbx_obj, api_method)
    try:
        query_result = zbx_method(api_options)
        module.exit_json(changed=True, result=query_result)
    except Exception as e:
        module.fail_json(msg="Failed to execute api.%s.%s(): %s" % (api_object, api_method, e))

if __name__ == '__main__':
    main()
