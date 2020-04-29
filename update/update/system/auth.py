# coding:utf8
from django.shortcuts import render, redirect,render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from ..forms import LoginForm
from django.contrib import auth
# from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template.context import RequestContext
import traceback
import time
import random
import sqlite3
from ..import conf_list,query_dsl
from ..models import User
import json
import hashlib
import datetime
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

__query__ = query_dsl.Query()
system_title = conf_list.title
user_table = "update_user"
code_version = conf_list.code_version

def hash_code(s, salt='D01'):# 加点盐
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())  # update方法只接收bytes类型
    return h.hexdigest()

# 登录界面
def login(request):
    access_ip = __query__.get_request_ip(request)
    next = request.GET.get('next', 'panels')
    if request.method == 'GET':
        return render(request, 'system/login.html',{"system_title":system_title,"next":next,
                                                    "version":code_version})
    elif request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                user = auth.authenticate(username=username,password=password)
                if user is not None and user.is_active:
                    auth.login(request,user)
                    ticket = ""
                    for i in range(15):
                        s = "abcdefghijklmnopqrstuvwxyz"
                        ticket += random.choice(s)
                    now_time = int(time.time())
                    ticket = "TK" + ticket + str(now_time)
                    request.session.set_expiry(600)
                    response = HttpResponseRedirect(next)
                    response.set_cookie("ticket",ticket,max_age=10000)
                    user.u_ticket = ticket
                    user.save()
                    __query__.write_audit_logs(username,"1","default","1",2,access_ip,"1","用户登录")
                    return response
                else:
                    __query__.write_audit_logs(username,"1","default","1",1,access_ip,"-1","用户登录")
                    return render(request, 'system/login.html',{"system_title":system_title,
                                                                "next":next,
                                                                "msg":"用户名或密码错误！",
                                                                "username":username,
                                                                "password":password,
                                                                "version":code_version
                                                                })
            except Exception,e:
                __query__.write_audit_logs(username,"1","default","1",1,access_ip,"-1","用户登录")
                print str(e)
                return render(request, 'system/login.html',{"system_title":system_title,
                                                            "next":next,
                                                            "msg":"用户名或密码错误！",
                                                            "username":username,
                                                            "password":password,
                                                            "version":code_version})
        else:
            __query__.write_audit_logs("","1","default","1",1,access_ip,"-1","用户登录")
            print "test"
            return render(request, 'system/login.html',{"system_title":system_title,
                                                        "next":next,"msg":"用户名或密码错误！",
                                                        "version":code_version})


def logout(request):
    ip = __query__.get_request_ip(request)
    username = request.user.username
    auth.logout(request)
    __query__.write_audit_logs(username,"1","default","1",2,ip,"1","退出登录")
    return HttpResponseRedirect("login")

# 通过cookie判断用户是否已登录
def index(request):
    # 提取浏览器中的cookie，如果不为空，表示已经登录
    username = request.COOKIES.get('ticket', '')
    if not username:
        return HttpResponseRedirect('/login/')
    return HttpResponseRedirect('/setting/')


# 用户设置界面
def users_management(request):
    access_ip = __query__.get_request_ip(request)
    is_superuser = __query__.is_superuser_status(request)
    request.session.set_expiry(600)
    username = request.user.username
    try:
        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()
        cursor = c.execute("select id,username,rolename,realname,email,telephone from %s" % user_table)
        forms = cursor.fetchall()
        cursor = c.execute("select count(*) from %s" % user_table)
        form = cursor.fetchone()
        ans = {}
        if (len(form) == 1):
            ans["num"] = form[0]
    except Exception,e:
        print "users query failed"
        print str(e)
        forms = []
        ans = {
            "num":0
        }
    return render(request, 'system/users_management.html', {
                                    'forms': forms,
                                    "system_title":system_title,
                                    "username":username,
                                    "ans": ans,
                                    "version":code_version,
                                    "html_tag":"users",
                                    "html_tag1":"permission_set",
                                    "html_tag2":"users",
                                    "is_superuser":is_superuser,
    }
                  )


# 添加用户

def add_user(request):
    action_username = request.user.username
    access_ip = __query__.get_request_ip(request)
    is_superuser = __query__.is_superuser_status(request)
    if request.method == 'GET':
        return render(request, 'system/add_user.html')
    elif request.method == 'POST':
        content = {
            "success":False,
            "msg":"这是默认返回内容！"
        }
        try:
            if is_superuser:
                username = request.POST.get('user[username]')
                if User.objects.filter(username=username).count():
                    content["msg"] = "用户%s已存在" % username
                else:
                    rolename = request.POST.get('user[role_name]')
                    realname = request.POST.get('user[realname]', )
                    email = request.POST.get('user[email]')
                    password = request.POST.get('user[password]')
                    tel = request.POST.get('user[tel]')
                    conn = sqlite3.connect('db.sqlite3')
                    is_superuser = 1 if rolename == "超级管理员" else 0
                    is_staff = 1 if rolename == "超级管理员" else 0
                    is_active = 1
                    date_joined = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if is_superuser == 1:
                        if tel:
                            registAdd = User.objects.create_superuser(username=username,
                                                                      password=password,
                                                                      rolename=rolename,
                                                                      realname=realname,
                                                                      email=email,
                                                                      telephone=tel
                                                                      )
                        else:
                            registAdd = User.objects.create_superuser(username=username,
                                                                      password=password,
                                                                      rolename=rolename,
                                                                      realname=realname,
                                                                      email=email
                                                                      )
                    else:
                        if tel:
                            registAdd = User.objects.create_user(username=username,
                                                                 password=password,
                                                                 rolename=rolename,
                                                                 realname=realname,
                                                                 email=email,
                                                                 telephone=tel)
                        else:
                            registAdd = User.objects.create_user(username=username,
                                                                      password=password,
                                                                      rolename=rolename,
                                                                      realname=realname,
                                                                      email=email
                                                                      )
                    if registAdd == False:
                        content = {
                            "success":False,
                            "msg":"添加新用户失败"
                        }
                    else:
                        content = {
                            "success": True
                        }
            else:
                content["msg"] = "普通用户无创建用户权限！"
        except Exception as e:
            print(str(e))
            content = {
                "success": False,
                "msg": "用户添加失败"
            }
        success = content.get("success",False)
        if success:
            __query__.write_audit_logs(action_username,"11","1","1","2",access_ip,"1","添加用户")
        else:
            __query__.write_audit_logs(action_username,"11","1","1","1",access_ip,"-1","添加用户")
        return HttpResponse(json.dumps(content, ensure_ascii=False))


# 修改信息

def update_user(request):
    access_ip = __query__.get_request_ip(request)
    action_username = request.user.username
    is_superuser = __query__.is_superuser_status(request)
    if request.method == 'GET':
        userid = request.GET.get("user_id")
        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()
        cursor = c.execute("select id,username,rolename,realname,email,telephone from %s where id = %s" % (user_table,userid,))
        form = cursor.fetchall()
        userinfo = {}
        if (len(form) == 1):
            userinfo["id"] = form[0][0]
            userinfo["username"] = form[0][1]
            userinfo["rolename"] = form[0][2]
            userinfo["realname"] = form[0][3] if form[0][3] != None else ""
            userinfo["email"] = form[0][4]
            userinfo["telephone"] = form[0][5] if form[0][5] != None else ""
        return render(request, 'system/update_user.html', {'userinfo': userinfo})
    elif request.method == 'POST':
        try:
            past_username = request.POST.get("past_username")
            rolename = request.POST.get('user[role_name]')
            realname = request.POST.get('user[realname]', )
            email = request.POST.get('user[email]')
            tel = request.POST.get('user[tel]' )
            if is_superuser or past_username == action_username:
                user = User.objects.get_by_natural_key(username=past_username)
                user.username = past_username
                user.rolename = rolename
                user.realname = realname
                user.email = email
                user.telephone = tel
                user.save()
                content = {
                    "success": True
                }
            else:
                content = {
                    "success":False,
                    "msg": "普通用户无权限修改其他用户信息！"
                }
        except Exception as e:
            traceback.print_exc()
            content = {
                "success": False,
                "msg": "用户信息更新失败"
            }
        success = content.get("success",False)
        if success:
            __query__.write_audit_logs(action_username,"11","1","3","2",access_ip,"1","修改用户信息")
        else:
            __query__.write_audit_logs(action_username,"11","1","3","1",access_ip,"-1","修改用户信息")
        return HttpResponse(json.dumps(content, ensure_ascii=False))


# 重置密码

def update_password(request):
    access_ip = __query__.get_request_ip(request)
    action_username = request.user.username
    is_superuser = __query__.is_superuser_status(request)
    if request.method == 'GET':
        userid = request.GET.get("user_id")
        userinfo = {}
        if userid:
            conn = sqlite3.connect('db.sqlite3')
            c = conn.cursor()
            cursor = c.execute("select id,username,email from %s where id = %s" % (user_table,userid,))
            form = cursor.fetchall()
            if (len(form) == 1):
                userinfo["id"] = form[0][0]
                userinfo["username"] = form[0][1]
            else:
                pass
        else:
            username = request.user.username
            userinfo["username"] = username
        return render(request, 'system/update_password.html', {'userinfo': userinfo})
    elif request.method == 'POST':
        try:
            username = request.POST.get('username')
            past_password = request.POST.get('past_password')
            password = request.POST.get('password')
            if is_superuser or username == action_username:
                user_auth = auth.authenticate(username=username,password=past_password)
                if user_auth:
                    user = User.objects.get_by_natural_key(username=username)
                    user.set_password(password)
                    user.save()
                    content = {
                        "success": True
                    }
                else:
                    content = {
                        "success": False,
                        "msg": "原密码输入错误！"
                    }
            else:
                content = {
                    "success": False,
                    "msg":"普通用户无权限修改其他用户密码！"
                }
        except Exception as e:
            print(str(e))
            content = {
                "success": False,
                "msg": "密码修改失败！"
            }
        success = content.get("success",False)
        if success:
            __query__.write_audit_logs(action_username,"11","1","4","2",access_ip,"1","重置密码")
        else:
            __query__.write_audit_logs(action_username,"11","1","4","1",access_ip,"-1","重置密码")
        return HttpResponse(json.dumps(content, ensure_ascii=False))

def get_username(user_id):
    """
    根据用户id获取用户名
    :param user_id:
    :return:
    """
    username = ""
    try:
        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()
        sql = "select username from %s where id = %s" % (user_table,id)
        c.execute(sql)
        res = c.fetchall()
        username = res[0][0] if res else username
    except:
        print "获取用户名失败"
    return username


# 删除用户

def del_user(request):
    id = request.GET.get("user_id","")
    ip = __query__.get_request_ip(request)
    username = request.user.username
    is_superuser = __query__.is_superuser_status(request)
    if request.method == 'GET':
        return render(request, 'setting.html')
    elif request.method == 'POST':
        success = False
        try:
            if id in ["1",1]:
                print "you can not delete admin"
            else:
                if is_superuser:
                    conn = sqlite3.connect('db.sqlite3')
                    c = conn.cursor()
                    sql = "delete from %s where id = %s" % (user_table,id)
                    c.execute(sql)
                    conn.commit()
                    success = True
                else:
                    msg = ""
                    delete_username = get_username(id)
                    if delete_username:
                        if delete_username == username:
                            conn = sqlite3.connect('db.sqlite3')
                            c = conn.cursor()
                            sql = "delete from %s where id = %s" % (user_table,id)
                            c.execute(sql)
                            conn.commit()
                            success = True
                        else:
                            msg = "普通用户%s删除其他用户被拦截！" % request.user.username
                    else:
                        msg = "普通用户%s删除请求的用户id错误！" % request.user.username
                    if msg:
                        print msg
                        __query__.write_logs("3","del_user",ip,msg=msg)
                    else:
                        pass
        except Exception,e:
            print "delete_user failed"
            traceback.print_exc()
        if success:
            __query__.write_audit_logs(username,"11","1","2","2",ip,"1","删除用户")
        else:
            __query__.write_audit_logs(username,"11","1","2","1",ip,"-1","删除用户")
        return HttpResponseRedirect('/users')
