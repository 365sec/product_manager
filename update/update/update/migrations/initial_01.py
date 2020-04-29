# coding:utf-8

from __future__ import unicode_literals

from django.db import migrations,models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=128, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('rolename', models.CharField(default="超级管理员",max_length=128)),
                ('realname', models.CharField(max_length=128,null=True)),
                ('email', models.EmailField(max_length=128, unique=True)),
                ('last_login', models.DateTimeField(null=True)),
                ('is_superuser', models.BooleanField()),
                ('is_staff', models.BooleanField()),
                ('is_active', models.BooleanField()),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=30)),
                ('telephone', models.IntegerField(null=True)),
            ],
            options={
                'verbose_name': '用户',
                'verbose_name_plural': '用户',
            },
        ),
    ]