# coding:utf-8

from django.shortcuts import render,HttpResponse,HttpResponseRedirect
import json
import traceback
import re
import os
import time
import datetime
import logging
import sys
from .. import conf_list,query_dsl
reload(sys)
sys.setdefaultencoding("utf-8")


client = conf_list.client
version_index = conf_list.version_index
version_type = conf_list.version_type
product_index = conf_list.product_index
files_path = conf_list.files_path
status_path = conf_list.status_path
status_dir = status_path
system_title = conf_list.title
# status_dir = "././%s" % status_path
files_dir = "././%s/" % files_path
__query__ = query_dsl.Query()

def versionCompare(v1, v2):
    """
    版本号限制3段，对比思路就是将版本号通过.号切割成列表，里面每个元素就是小的版本号，如果
    长度不一致，在后面加0补齐，然后进行遍历对比，哪个大说明哪个版本高，都相等说明版本相同
    """
    v1_check = re.match("\d+(\.\d+){0,2}", v1)
    v2_check = re.match("\d+(\.\d+){0,2}", v2)
    if v1_check is None or v2_check is None or v1_check.group() != v1 or v2_check.group() != v2:
        print "版本号格式不对，正确的应该是x.x.x,只能有3段"
        return 2
    v1_list = v1.split(".")
    v2_list = v2.split(".")
    v1_len = len(v1_list)
    v2_len = len(v2_list)
    if v1_len > v2_len:
        for i in range(v1_len - v2_len):
            v2_list.append("0")
    elif v2_len > v1_len:
        for i in range(v2_len - v1_len):
            v1_list.append("0")
    else:
        pass
    for i in range(len(v1_list)):
        if int(v1_list[i]) > int(v2_list[i]):
            return 0
        if int(v1_list[i]) < int(v2_list[i]):
            return 2
    return 1


def management(request):
    username = request.user.username
    if request.method == "GET":
        try:
            page = int(request.GET.get("page",1))
            product_id = request.GET.get("product_id","")
            if product_id:
                query = {
                        "term":{
                            "product_id.keyword": product_id
                        }
                }
            else:
                query = {}
            res = client.search(index=version_index,
                                body={
                                    "from":(page-1)*15,
                                    "size":15,
                                    "query":query,
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
            page_num = total/15 if total % 15 == 0 else total/15 +1
            page_list = [
                i for i in range(page-4,page+5) if i >0 and i <= page_num
            ]
            hits = []
            for hit in res["hits"]["hits"]:
                hit_dict = hit["_source"]
                hit_dict["id"] = hit["_id"]
                hits.append(hit_dict)
            total = len(hits)
            product_list = __query__.get_product_list(product_id)
            return render(request,"version/version_management.html",{
                "hits": hits,
                "total": total,
                "page_num":page_num,
                "current_page":page,
                "last_page":page-1,
                "next_page":page+1,
                "page_list":page_list,
                "username":username,
                "system_title":system_title,
                "product_list":product_list,
                "product_id":product_id,
            })
        except:
            traceback.print_exc()
        return render(request,"version/version_management.html",{
            "hits": [],
            "total": 0,
            "page_num":0,
            "current_page":1,
            "last_page":0,
            "next_page":2,
            "page_list":[],
            "username":username,
            "system_title":system_title,
            "html_tag":"product",
            "product_list": []
        })


def version_compare_2(v1,v2):
    """
    poc及rule版本对比
    :param v1:
    :param v2:
    :return:
    """
    v1_check = re.match("\d{8}", v1)
    v2_check = re.match("\d{8}", v2)
    if v1_check is None or v2_check is None or v1_check.group() != v1 or v2_check.group() != v2:
        print "版本号格式不对，正确的应该是20190121"
        return 2
    if int(v1) > int(v2):
        return 0
    else:
        return 2






def get_version_status(version,type):
    """
    获取版本是否合规,主要比较版本格式是否大于当前最新版本，如大于，则置True，否则状态置为False
    :param version:
    :param type:
    :return:
    """
    try:
        res = client.search(index=version_index,
                            doc_type=version_type,
                            body={
                                "size":1,
                                "query":{
                                    "term":{
                                        "type.keyword":type
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
        if total >0:
            hit = res["hits"]["hits"][0]
            last_version = hit["_source"].get("version","")
            if type == "code":
                version_status = versionCompare(version,last_version)
            else:
                version_status = version_compare_2(version,last_version)
            if version_status == 0:
                status = True
            else:
                status = False
        else:
            status = True
    except Exception,e:
        print str(e)
        status = False
    return status

def update_next_version(version,type):
    """
    更新之前最新版本记录的next_version以及next_type
    :param version:
    :param type:
    :return:
    """
    try:
        res = client.search(index=version_index,
                            doc_type=version_type,
                            body={
                                "size":1,
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
        if total >0:
            hit = res["hits"]["hits"][0]
            id = hit["_id"]
            doc = {
                "next_version":version,
                "next_type":type
            }
            client.update(index=version_index,
                          doc_type=version_type,
                          id=id,
                          body={
                              "doc":doc
                          }
                          )
        else:
            pass
        status = True
    except Exception,e:
        print "更新next_version失败"
        print str(e)
        status = False
    return status

def new(request):
    if request.method == "GET":
        product_list = __query__.get_product_list()
        return render(request,"version/new.html",{
            "product_list":product_list
        })
    elif request.method == "POST":
        try:
            version = request.POST.get("version","")
            type = request.POST.get("type","")
            product_id = request.POST.get("product","")
            product_name = request.POST.get("product_name","")
            version_status = get_version_status(version,type)
            if version_status:
                description = request.POST.get("description","")
                obj = request.FILES.get("file")
                filename = obj.name
                f = open(files_dir+filename,"wb")
                for chunk in obj.chunks():
                    f.write(chunk)
                f.close()
                update_next_version_status = update_next_version(version,type)
                if update_next_version_status:
                    action = {
                        "version":version,
                        "type":type,
                        "description":description,
                        "filename":filename,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "product_id": product_id,
                        "product_name": product_name,
                    }
                    client.index(index=version_index,
                                 doc_type=version_type,
                                 body=action
                                 )
                    content = {
                        "success":True
                    }
                    time.sleep(1)
                else:
                    content = {
                        "success":False,
                        "msg":"更新版本关系失败"
                    }
            else:
                content = {
                    "success":False,
                    "msg":"版本格式错误，请检查版本格式是否合规或版本号是否大于当前最新版本号"
                }
        except Exception,e:
            print str(e)
            print traceback.print_exc()
            content = {
                "success":False,
                "msg":"上传失败"
            }
        return HttpResponse(json.dumps(content,ensure_ascii=False))

def remove_next():
    try:
        res = client.search(index=version_index,
                            doc_type=version_type,
                            body={
                                "size":1,
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
            id = hit["_id"]
            source = hit["_source"]
            if "next_version" in source.keys():
                del source["next_version"]
            if "next_type" in source.keys():
                del source["next_type"]
            client.index(index=version_index,
                          doc_type=version_type,
                          id=id,
                          body=source
                          )
        else:
            pass
    except Exception,e:
        print "移除最新版本的next_version失败"
        print str(e)

def delete_version(timestamp):
    try:
        res = client.search(index=version_index,
                                     doc_type=version_type,
                                     body={
                                         "size":1000,
                                         "_source":["filename"],
                                         "query":{
                                             "range":{
                                                 "timestamp":{
                                                     "gte":timestamp
                                                 }
                                             }
                                         }
                                     }
                                     )
        filename_list = []
        for hit in res["hits"]["hits"]:
            name = hit["_source"].get("filename","")
            if name != "":
                filename_list.append(name)
        client.delete_by_query(index=version_index,
                               doc_type=version_type,
                               body={
                                   "query":{
                                       "range":{
                                           "timestamp":{
                                               "gte":timestamp
                                           }
                                       }
                                   }
                               }
                               )
        status = True
        try:
            for filename in filename_list:
                if filename != "":
                    if os.path.exists(files_dir+filename):
                        os.remove(files_dir+filename)
                    else:
                        pass
                else:
                    pass
        except Exception,e:
            print "删除更新包文件失败！"
    except Exception,e:
        print "删除失败"
        status = False
    return status

def delete(request):
    """
    删除当前版本同时也会删除之前的版本
    同时需要更新上一版本的next_version及next_type内容
    :param request:
    :return:
    """
    if request.method == "GET":
        try:
            id = request.GET.get("id","")
            res = client.get(index=version_index,
                             doc_type=version_type,
                             id=id
                             )
            timestamp = res["_source"].get("timestamp","")
            status = delete_version(timestamp)
            if status:
                time.sleep(1)
                remove_next()
            else:
                print "删除版本记录失败！"
        except Exception,e:
            print "删除版本记录失败！"
            print str(e)
        return HttpResponseRedirect("../")
