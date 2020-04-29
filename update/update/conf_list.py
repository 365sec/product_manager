# coding:utf-8

import ConfigParser
import os
import json
import logging
from elasticsearch import Elasticsearch

update_logger = logging.getLogger("update")
audit_logger = logging.getLogger("audit")
error_logger = logging.getLogger("error")
conf = ConfigParser.ConfigParser()
conf.read(os.path.join(os.path.dirname(__file__),"","conf"))

files_path = conf.get("system","files_path")
status_path = conf.get("system","status_path")
str_es_hosts = conf.get("elasticsearch", "hosts")
es_hosts = json.loads(str_es_hosts)
es_timeout = int(conf.get("elasticsearch", "timeout"))
client = Elasticsearch(hosts=es_hosts,timeout=es_timeout)
version_index = conf.get("elasticsearch", "version_index")
version_type = conf.get("elasticsearch", "version_type")
license_index = conf.get("elasticsearch", "license_index")
license_type = conf.get("elasticsearch", "license_type")
product_index = conf.get("elasticsearch", "product_index")
product_type = conf.get("elasticsearch", "product_type")
audit_index = conf.get("elasticsearch", "audit_index")
audit_type = conf.get("elasticsearch", "audit_type")

title = conf.get("system","title")
code_version = conf.get("system","code_version")





