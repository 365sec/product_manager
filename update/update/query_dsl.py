# -*- coding:utf-8 -*-

import json
import re
import conf_list
import datetime
import time
import traceback
import requests
from bson import ObjectId
import os
import hashlib
from models import User

logger = conf_list.update_logger
audit_logger = conf_list.audit_logger
error_logger = conf_list.error_logger
client = conf_list.client
audit_log_index = conf_list.audit_index
audit_log_type = conf_list.audit_type
product_index = conf_list.product_index

class Query():

    def __init__(self):
        self.parentheses="()"
        self.field = "_all"
        self.field_dict = {
            "country" : "location.country",
            "province" : "location.province",
            "city" : "location.city",
            "asset_province":"province",
            "asset_city":"city",
            "title" : "data.title",
            "header": "data.header",
            "组件" : "component",
            "开发语言":"language",
            "Web应用":"cms",
            "端口协议":"protocols",
            "body":"data.body",
            "asset_os":"os",
            "vul_name":"vulnerability.name",
            "asset_title":"titles.title"
        }
        self.field_dict = json.loads(json.dumps(self.field_dict))
        self.replace_dict = {}

    def get_user_status(self,username,is_superuser,action_username):
        """
        获取用户权限问题
        :param username:
        :param is_superuser:
        :return:
        """
        status = True if is_superuser else False
        if status:
            pass
        else:
             status = True if action_username == username else False
        return status

    def get_str_time(self,timestamp):
        str_time = None
        try:
            str_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except:
            print traceback.format_exc()
            self.write_logs("error","get_str_time","")
        return str_time

    def get_product_list(self,product_id=""):
        """
        获取版本列表中产品列表
        :param product_id:
        :return:
        """
        product_list = []
        try:
            res = client.search(index=product_index)
            for hit in res["hits"]["hits"]:
                id = hit["_id"]
                name = hit["_source"].get("name","")
                hit_dict = {
                    "id": id,
                    "name": name,
                    "selected": True if product_id == id else False
                }
                product_list.append(hit_dict)
        except:
            print "获取产品列表失败！"
            traceback.print_exc()
        return product_list

    def get_timestamp(self,str_time):
        timestamp = None
        try:
            timestamp = datetime.datetime.strptime(str_time,"%Y-%m-%d %H:%M:%S")
        except:
            print traceback.format_exc()
            self.write_logs("error","get_str_time","")
        return timestamp

    def is_superuser_status(self,request):
        """
        判断用户是否是超级用户
        :param request:
        :return:
        """
        return 1 if request.user.is_superuser else 0

    def get_request_ip(self,request):
        try:
            if request.META.has_key('HTTP_X_FORWARDED_FOR'):
                ip =  request.META['HTTP_X_FORWARDED_FOR']
            else:
                ip = request.META['REMOTE_ADDR']
        except:
            ip = ""
        return ip


    def write_audit_logs(self,username,type1,type2,action,level,ip,result,content):
        """
        写入审计日志
        :param type1: 主分类
        :param type2: 子分类
        :param action: 具体操作
        :param level: 日志级别
        :param ip: 操作ip
        :param result: 操作结果
        :param content: 操作具体内容
        :return:
        """
        timestamp = self.get_time_stamp()
        timestamp = "%s+0800" % timestamp
        message = "%s %s %s %s %s " \
                  "%s %s %s %s" % (timestamp,type1,type2,action,str(level),ip,username,result,content)
        audit_logger.info(msg=message)
        log_info = {
            "timestamp":timestamp,
            "type1":type1,
            "type2":type2,
            "action":action,
            "level":level,
            "ip":ip,
            "result":result,
            "content":content,
            "username":username
        }
        client.index(index=audit_log_index,doc_type=audit_log_type,
                     body=log_info
                     )
        #审计日志模块待完善




    def write_logs(self,way,module,ip,msg="",search_content=""):
        timestamp = self.get_time_stamp()
        timestamp = "%s+0800" % timestamp
        if way == "1":  #access
            message = "[%s] [access]: %s %s" % (timestamp,ip,module)
            logger.info(message)
        elif way == "2":  #search
            message = "[%s] [search]: %s %s '%s'" % (timestamp,ip,module,search_content)
            logger.info(message)
        elif way == "4":  #action
            message = "[%s] [action]: %s %s %s" % (timestamp,ip,module,msg)
            logger.info(message)
        elif way == "warning":
            message = "[%s] [action]: %s %s %s" % (timestamp,ip,module,msg)
            logger.warning(message)
        else:  # 错误日志
            message = "[%s] [error]: %s %s %s" % (timestamp,ip,module,msg)
            error_logger.error(message)

    def get_time_stamp(self):
        ct = time.time()
        local_time = time.localtime(ct)
        data_head = time.strftime("%Y-%m-%dT%H:%M:%S", local_time)
        data_secs = (ct - long(ct)) * 1000
        time_stamp = "%s.%03d" % (data_head, data_secs)
        return time_stamp

    def get_new_id_list(self,id_list,int_status=True):
        new_id_list = []
        for id in id_list:
            if int_status:
                new_id_list.append(int(id))
            else:
                new_id_list.append(ObjectId(id))
        return new_id_list

    def get_nday_list(self,n): #获取今天之前指定天数的日期
        before_n_days = []
        for i in range(1, n + 1)[::-1]:
            before_n_days.append((datetime.date.today() - datetime.timedelta(days=i)).strftime('%m-%d'))
        return before_n_days



    def group(self,n, sep = ','):   #对数字，进行千位分割
        s = str(abs(n))[::-1]
        groups = []
        i = 0
        while i < len(s):
            groups.append(s[i:i+3])
            i+=3
        retval = sep.join(groups)[::-1]
        if n < 0:
            return '-%s' % retval
        else:
            return retval








