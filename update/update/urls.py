"""update URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from system import system,auth
from version import management
from license import license_management
from product import product


license_1 = license_management.license()
product_1 = product.Product()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login$', auth.login),
    url(r'^logout$', auth.logout),
    url(r'^products$', login_required(product_1.product_management)),
    url(r'^products/new$', product_1.new_product),
    url(r'^products/edit$', product_1.edit_product),
    url(r'^products/delete$', product_1.delete_product),
    url(r'^version_management$', login_required(management.management)),
    url(r'^version/compare$', system.compare),
    url(r'^version/get_file$', system.get_file),
    url(r'^version_management/new$', management.new),
    url(r'^version_management/delete$', management.delete),
    url(r'^license_management$', login_required(license_1.license_management)),
    url(r'^license/new$', license_1.new),
    url(r'^license/delete$', license_1.delete),
    url(r'^license/download$', license_1.download),
    url(r'^users$', login_required(auth.users_management)),
    url(r'^users/add_user$', auth.add_user),
    url(r'^users/update_user$', auth.update_user),
    url(r'^users/update_password$', auth.update_password),
    url(r'^$', login_required(management.management)),
]
