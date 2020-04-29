# coding:utf-8


from django.http import HttpResponseRedirect
from django.shortcuts import render,HttpResponse
import json
import traceback
from .. import conf_list,query_dsl
from ..models import User
import sqlite3
import time
import datetime

client = conf_list.client
product_index = conf_list.product_index
product_type = conf_list.product_type
version_index = conf_list.version_index
license_index = conf_list.license_index
system_title = conf_list.title
__query__ = query_dsl.Query()

class Product():

    def __init__(self):
        self.user_table = "update_user"

    def get_product_num_info(self,product_id):
        """
        根据产品id获取其相应的版本数及许可数
        :param product_id:
        :return:
        """
        version_num = 0
        license_num = 0
        try:
            version_res = client.count(index=version_index,
                                       body={
                                          "query":{
                                              "term":{
                                                  "product_id.keyword": product_id
                                              }
                                          }
                                       }
                                       )
            version_num = version_res.get("count",0)
        except:
            print "获取产品的发布版本数失败"
            traceback.print_exc()
        try:
            license_res = client.count(index=license_index,
                                       body={
                                           "query":{
                                               "term":{
                                                   "product_id.keyword": product_id
                                               }
                                           }
                                       }
                                       )
            license_num = license_res.get("count",0)
        except:
            print "获取产品的发布版本数失败"
            traceback.print_exc()
        product_num_info = {
            "version_num": version_num,
            "license_num": license_num
        }
        return product_num_info


    def product_management(self,request):
        """
        产品管理页面
        :param request:
        :return:
        """
        username = request.user.username
        if request.method == "GET":
            try:
                page = int(request.GET.get("page",1))
                res = client.search(index=product_index,
                                    doc_type=product_type,
                                    body={
                                        "from":(page-1)*15,
                                        "size":15,
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
                    hit_dict["timestamp"] = hit_dict.get("timestamp","").replace("T"," ").replace("+0800","")
                    product_num_info = self.get_product_num_info(hit["_id"])
                    hit_dict["version_num"] = product_num_info.get("version_num",0)
                    hit_dict["license_num"] = product_num_info.get("license_num",0)
                    hits.append(hit_dict)
                total = len(hits)
                return render(request,"product/product_management.html",{
                    "hits": hits,
                    "total": total,
                    "page_num":page_num,
                    "current_page":page,
                    "last_page":page-1,
                    "next_page":page+1,
                    "page_list":page_list,
                    "system_title":system_title,
                    "username":username,
                    "html_tag":"product"
                })
            except:
                traceback.print_exc()
        return render(request,"product/product_management.html",{
            "hits": [],
            "total": 0,
            "page_num":0,
            "current_page":1,
            "last_page":0,
            "next_page":2,
            "page_list":[],
            "system_title":system_title,
            "username":username,
            "html_tag":"product",
        })

    def get_user_status(self,realname,username):
        """
        根据真名获取用户状态
        :param realname:
        :return:
        """
        user = User.objects.get_by_natural_key(username=username)
        user_realname = user.realname
        status = True if realname == user_realname else False
        return status

    def get_user_list(self,username,is_superuser):
        """
        获取用户列表，用于新增产品用
        :return:
        """
        user_list = []
        try:
            if is_superuser:
                sql = "select id,username,realname from %s;" % self.user_table
            else:
                sql = "select id,username,realname from %s " \
                      "where username='%s';" % (self.user_table,username)
            conn = sqlite3.connect("db.sqlite3")
            c = conn.cursor()
            c.execute(sql)
            res = c.fetchall()
            for row in res:
                user_info = {
                    "id": row[0],
                    "username": row[1],
                    "realname": row[2],
                    "selected": True if username == row[1] else False
                }
                user_list.append(user_info)
        except:
            traceback.print_exc()
        return user_list


    def new_product(self,request):
        """
        新增产品
        :param request:
        :return:
        """
        action_username = request.user.username
        is_superuser = __query__.is_superuser_status(request)
        if request.method == "GET":
            user_list = self.get_user_list(action_username,is_superuser)
            return render(request,"product/new_product.html",{
                "user_list":user_list,
            })
        elif request.method == "POST":
            content = {
                "success":False,
                "msg":"新建产品失败！"
            }
            try:
                name = request.POST.get("name","")
                username = request.POST.get("leader","")
                action_permission = __query__.get_user_status(username,is_superuser,action_username)
                if action_permission:
                    description = request.POST.get("description","")
                    action = {
                        "name":name,
                        "leader":username,
                        "description":description,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0800")
                    }
                    client.index(index=product_index,
                                 doc_type=product_type,
                                 body=action
                                 )
                    time.sleep(0.3)
                    content["success"] = True
                    content["msg"] = ""
                else:
                    content = {
                        "success":False,
                        "msg":"当前用户无权操作！"
                    }
            except:
                traceback.print_exc()
                content = {
                    "success":False,
                    "msg":"新建产品失败，程序执行出错！"
                }
            return HttpResponse(json.dumps(content,ensure_ascii=False))

    def delete_product(self,request):
        """
        删除用户
        :param request:
        :return:
        """
        if request.method == "GET":
            try:
                id = request.GET.get("id","")
                res = client.delete(index=product_index,
                                 doc_type=product_type,
                                 id=id
                                 )
                time.sleep(1)
                if res:
                    pass
                else:
                    print "删除版本记录失败！"
            except Exception,e:
                print "删除版本记录失败！"
                print str(e)
        return HttpResponseRedirect("../products")


    def edit_product(self,request):
        """
        修改产品信息（名称及描述）
        :param request:
        :return:
        """
        action_username = request.user.username
        is_superuser = __query__.is_superuser_status(request)
        if request.method == "GET":
            id = request.GET.get("id","")
            hit = {}
            user_list = []
            try:
                res = client.get(index=product_index,
                                    doc_type=product_type,
                                    id=id
                                    )
                hit = res["_source"]
                leader = hit.get("leader","")
                user_list = self.get_user_list(leader,is_superuser)
            except:
                print "获取产品信息失败！"
                traceback.print_exc()
            return render(request,"product/edit_product.html",{
                "hit":hit,
                "user_list":user_list,
                "id":id
            })
        elif request.method == "POST":
            content = {
                "success":False,
                "msg":"修改产品信息失败！"
            }
            try:
                name = request.POST.get("name","")
                username = request.POST.get("leader","")
                id = request.POST.get("id","")
                action_permission = __query__.get_user_status(username,is_superuser,action_username)
                if action_permission:
                    description = request.POST.get("description","")
                    action = {
                        "name":name,
                        "leader":username,
                        "description":description,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0800")
                    }
                    client.index(index=product_index,
                                 doc_type=product_type,
                                 id=id,
                                 body=action
                                 )
                    time.sleep(1)
                    content["success"] = True
                    content["msg"] = ""
                else:
                    content = {
                        "success":False,
                        "msg":"当前用户无权操作！"
                    }
            except:
                traceback.print_exc()
                content = {
                    "success":False,
                    "msg":"修改产品信息失败，程序执行出错！"
                }
            return HttpResponse(json.dumps(content,ensure_ascii=False))


