#coding:utf-8

import json
import traceback
import datetime
import time
from util import license as license_server
from .. import conf_list,query_dsl
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect,FileResponse

license_index = conf_list.license_index
license_type = conf_list.license_type
client = conf_list.client
error_logger = conf_list.error_logger
system_title = conf_list.title
__query__ = query_dsl.Query()

class license():

    def license_management(self,request):
        """
        许可管理
        :param request:
        :return:
        """
        username = request.user.username
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
            res = client.search(index=license_index,
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
                hit_dict["timestamp"] = hit_dict.get("timestamp","").replace("T"," ").replace("+0800","")
                hit_dict["over_time"] = hit_dict.get("over_time","").replace("T"," ").replace("+0800","")
                hits.append(hit_dict)
            total = len(hits)
            product_list = __query__.get_product_list(product_id)
            return render(request,"license/license_management.html",{
                "hits": hits,
                "total": total,
                "username":username,
                "system_title":system_title,
                "html_tag":"product",
                "page_num":page_num,
                "current_page":page,
                "last_page":page-1,
                "next_page":page+1,
                "page_list":page_list,
                "product_list":product_list,
                "product_id":product_id,
            })
        except:
            error_logger.error("获取许可列表失败！")
            error_logger.error(traceback.format_exc())
        return render(request,"license/license_management.html",{
            "username":username,
            "system_title":system_title,
            "html_tag":"product",
            "hits": [],
            "total": 0,
            "page_num":0,
            "current_page":1,
            "last_page":0,
            "next_page":2,
            "page_list":[],
            "product_list":[],
        })

    def get_params_status(self):
        pass

    def get_encrypt_info(self,cpu_code,over_time):
        info = {
            "over_time": over_time
        }
        str_info = json.dumps(info)
        license1=license_server.License(cpu_code)   #以cpu序列号创建对象
        encrypt_info = license1.encryption(str_info) #加密
        return encrypt_info


    def new(self,request):
        if request.method == "GET":
            product_list = __query__.get_product_list()
            return render(request,"license/new.html",{
                "product_list":product_list
            })
        elif request.method == "POST":
            product_name = request.POST.get("product_name","")
            product_id = request.POST.get("product","")
            device_id = request.POST.get("device_id","")
            unit_name = request.POST.get("unit_name","")
            over_time = request.POST.get("over_time","")
            description = request.POST.get("description","")
            content = {
                "success":False
            }
            try:
                if product_name and product_id and device_id and over_time:
                    encrypt_info = self.get_encrypt_info(device_id,over_time)
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0800")
                    action = {
                        "product_name":product_name,
                        "product_id":product_id,
                        "device_id":device_id,
                        "unit_name":unit_name,
                        "over_time":over_time.replace(" ","T") + "+0800",
                        "description":description,
                        "encrypt_info":encrypt_info,
                        "timestamp":timestamp,
                    }
                    time.sleep(0.2)
                    client.index(index=license_index,doc_type=license_type,body=action)
                    content["success"] = True
                else:
                    content["msg"] = "请检查参数是否为空！"
            except:
                content["msg"] = "生成license失败！"
                traceback.print_exc()
            return HttpResponse(json.dumps(content,ensure_ascii=False))

    def delete(self,request):
        """
        删除用户
        :param request:
        :return:
        """
        if request.method == "GET":
            try:
                id = request.GET.get("id","")
                res = client.delete(index=license_index,
                                    doc_type=license_type,
                                    id=id
                                    )
                time.sleep(1)
                if res:
                    pass
                else:
                    print "删除许可失败！"
            except Exception,e:
                print "删除许可失败！"
                print str(e)
        return HttpResponseRedirect("../license_management")


    def download(self,request):
        """
        下载许可文件
        :param request:
        :return:
        """
        if request.method == "GET":
            id = request.GET.get("id","")
            status = False
            msg = ""
            try:
                res = client.get(index=license_index,doc_type=license_type,id=id)
                source = res.get("_source",{})
                if source:
                    encrypt_info = source.get("encrypt_info","")
                    if encrypt_info:
                        f = open("status/license","wb")
                        f.write(encrypt_info)
                        f.close()
                        status = True
                    else:
                        msg = "无许可信息，请检查该数据的正确性！"
                else:
                    msg = "无该条许可信息，请检查许可id是否正确！"
            except:
                print "获取许可信息失败！"
                traceback.print_exc()
            if status:
                f = open("status/license","rb")
                res = FileResponse(f)
                disposition = 'attachment;filename=license'
                res['Content-Disposition'] = disposition.encode("utf-8")
                return res
            else:
                return HttpResponse(msg)
















