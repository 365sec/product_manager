# coding:utf-8

from django.contrib.auth.models import AbstractUser
from django.db import models



class User(AbstractUser):
    username = models.CharField(max_length=128, unique=True)
    password = models.CharField(max_length=256)
    rolename = models.CharField(default="超级管理员",max_length=512)
    realname = models.CharField(max_length=512)
    email = models.EmailField(max_length=128, unique=True)
    telephone = models.IntegerField()

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "用户名"
        verbose_name_plural = "用户名"
