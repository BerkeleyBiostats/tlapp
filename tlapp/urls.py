"""tlapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
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
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView
from tlapp import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', RedirectView.as_view(url='/jobs/', permanent=False)),
    url(r'^jobs/(?P<job_id>[0-9]+)/download/$', views.job_output_download, name='job_output_download'),
    url(r'^jobs/(?P<job_id>[0-9]+)/download_url_token/$', views.job_download_url_token, name='job_download_url_token'),
    url(r'^jobs/(?P<job_id>[0-9]+)/output/$', views.job_output, name='job_output'),
    url(r'^jobs/(?P<job_id>[0-9]+)/logs/$', views.job_logs, name='job_logs'),
    url(r'^jobs/(?P<job_id>[0-9]+)/logs_token/$', views.job_logs_token, name='job_logs_token'),
    url(r'^jobs/(?P<job_id>[0-9]+)/status_token/$', views.job_status_token, name='job_status_token'),
    url(r'^jobs/(?P<job_id>[0-9]+)/view_logs/$', views.job_view_logs, name='job_view_logs'),
    url(r'^jobs/(?P<job_id>[0-9]+)/$', views.job_detail, name='job_detail'),
    url(r'^jobs/(?P<job_id>[0-9]+)/append_log/$', views.append_log_token, name='job_append_log_token'),
    url(r'^jobs/(?P<job_id>[0-9]+)/finish/$', views.finish_job, name='job_finish'),
    url(r'^jobs/(?P<job_id>[0-9]+)/restart/$', views.restart_job, name='job_restart'),
    url(r'^jobs/', views.jobs, name='jobs'),
    url(r'^jobs_oneoff/', views.jobs_oneoff, name='jobs_oneoff'),
    url(r'^templates/', views.templates, name='templates'),    
    url(r'^token/', views.token, name='token'),
    url(r'^submit_job/', views.submit_job, name='submit_job'),
    url(r'^submit_job_token/', views.submit_job_token, name='submit_job_token'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
]
