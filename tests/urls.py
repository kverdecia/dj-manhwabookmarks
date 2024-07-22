# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.urls import path, include, reverse_lazy
from django.contrib import admin
from django.views.generic import RedirectView

from allauth.account.decorators import secure_admin_login


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', RedirectView.as_view(url=reverse_lazy('admin:index'))),
    path('', include('djmanhwabookmarks.urls', namespace='djmanhwabookmarks')),
]

admin.autodiscover()
admin.site.login = secure_admin_login(admin.site.login)
