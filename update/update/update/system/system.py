# coding:utf-8

from django.shortcuts import render,HttpResponse
from django.http import StreamingHttpResponse
import os
import json
import logging
import datetime
import tempfile
import re
from .. import conf_list

client = conf_list.client
version_index = conf_list.version_index
version_type = conf_list.version_type
logger = logging.getLogger('access_ip')
files_path = conf_list.files_path
status_path = conf_list.status_path
status_dir = status_path
# status_dir = "././%s" % status_path
files_dir = "././%s/" % files_path

class FileWrapper:
    """Wrapper to convert file-like objects to iterables"""

    def __init__(self, filelike, blksize=8192):
        self.filelike = filelike
        self.blksize = blksize
        if hasattr(filelike,'close'):
            self.close = filelike.close

    def __getitem__(self,key):
        data = self.filelike.read(self.blksize)
        if data:
            return data
        raise IndexError

    def __iter__(self):
        return self

    def next(self):
        data = self.filelike.read(self.blksize)
        if data:
            return data
        raise StopIteration

def compare(request):
    """
    版本更新对比，获取更新状态
    :param request:
    :return:
    """
    if request.method == "GET":
        try:
            code_version = request.GET.get("code_version","")
            poc_version = request.GET.get("poc_version","")
            rule_version = request.GET.get("rule_version","")
            mac = request.GET.get("mac","")
            if request.META.has_key('HTTP_X_FORWARDED_FOR'):
                ip =  request.META['HTTP_X_FORWARDED_FOR']
            else:
                ip = request.META['REMOTE_ADDR']
            str_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = "[%s]: action=版本对比 ip=%s mac=%s code_version=%s " \
                      "poc_version=%s rule_version=%s" \
                      "" % (str_time,ip,mac,code_version,poc_version,rule_version)
            logger.info(message)
            res = client.search(index=version_index,
                                doc_type=version_type,
                                body={
                                    "size":1,
                                    "query":{
                                        "bool":{
                                            "should":[
                                                {
                                                    "bool":{
                                                        "must":[
                                                            {
                                                                "term":{
                                                                    "version.keyword":code_version
                                                                }
                                                            },
                                                            {
                                                                "term":{
                                                                    "type.keyword":"code"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool":{
                                                        "must":[
                                                            {
                                                                "term":{
                                                                    "version.keyword":poc_version
                                                                }
                                                            },
                                                            {
                                                                "term":{
                                                                    "type.keyword":"poc"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool":{
                                                        "must":[
                                                            {
                                                                "term":{
                                                                    "version.keyword":rule_version
                                                                }
                                                            },
                                                            {
                                                                "term":{
                                                                    "type.keyword":"rule"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    },
                                    "sort":[
                                        {
                                            "timestamp":{
                                                "order":"desc"
                                            }
                                        }
                                    ]
                                }
                                )
            total = res["hits"]["total"]
            if total>0:
                hit = res["hits"]["hits"][0]
                next_version = hit["_source"].get("next_version","")
                next_type = hit["_source"].get("next_type","")
                if next_version == "" or next_type == "":
                    res_status = {
                        "success":True,
                        "is_update":0,
                        "msg":"已是最新版本！",
                        "type":hit["_source"].get("type","code")
                    }
                elif next_type not in ["code","poc","rule"]:
                    res_status = {
                        "success":True,
                        "is_update":0,
                        "msg":"软件包类型错误，当前仅有code、poc、rule三种类型软件包！"
                    }
                else:
                    res_status = {
                        "success":True,
                        "is_update":1,
                        "version":next_version,
                        "type":next_type,
                        "msg":""
                    }
            else:
                res_status = {
                    "success":False,
                    "is_update":0,
                    "msg":"无法查到相关的版本信息，请检查参数是否正确！"
                }
        except Exception,e:
            print str(e)
            res_status = {
                "success":False,
                "is_update":0,
                "version":"",
                "msg":"验证程序出错"
            }
        return HttpResponse(json.dumps(res_status,ensure_ascii=False))


def get_file(request):
    """
    供客户端请求更新包用
    :param request:
    :return:
    """
    if request.method == "GET":
        version = request.GET.get("version","")
        type = request.GET.get("type","poc")
        query = {
            "query":{
                "bool":{
                    "must":[
                        {
                            "term":{
                                "version.keyword":version
                            }
                        },
                        {
                            "term":{
                                "type.keyword":type
                            }
                        }
                    ]
                }
            }
        }
        res = client.search(index=version_index,
                            doc_type=version_type,
                            body=query
                            )
        hit = res["hits"]["hits"][0]
        the_file_name = hit["_source"].get("filename","")
        def file_iterator(file_name, chunk_size=512):
            with open(file_name) as f:
                while True:
                    c = f.read(chunk_size)
                    if c:
                        yield c
                    else:
                        break
        if ".zip" in the_file_name or ".tar" in the_file_name or ".rar" in the_file_name or ".pkg" in the_file_name:
            temp = open(files_dir+the_file_name,"rb")
            wrapper = FileWrapper(temp)
            res = HttpResponse(wrapper,content_type="application/zip")
            # res['Content-Length'] = temp.tell()
            # temp.seek(0)
        else:
            res = StreamingHttpResponse(file_iterator(files_dir+the_file_name))
            res['Content-Type'] = 'application/octet-stream'
        res['Content-Length'] = os.path.getsize(files_dir+the_file_name)
        out_filename = the_file_name
        res['Content-Disposition'] = 'attachment;filename=%s' % out_filename
        return res
