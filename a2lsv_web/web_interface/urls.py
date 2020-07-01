from django.urls import include, path

from .views import web_interface, labeler, manager

from web_interface.forms import *

urlpatterns = [
    path('', web_interface.home, name='home'),

    path('labeler/', include(([
        path('', labeler.listAudios, name='listAudios'),
        path('labelAudio', labeler.labelAudio, name='labelAudio'),
        path('solveSpeakerDuplicate', labeler.solveSpeakerDuplicate, name='solveSpeakerDuplicate'),
    ], 'web_interface'), namespace='labeler')),

    path('manager/', include(([
        path('', manager.listDatasets, name='listDatasets'),
        path('dataset/add/', manager.DatasetCreateView.as_view(), name='dataset_add'),
        path('keyword/add/', manager.get_keyword, name='keyword_add'),
        
    ], 'web_interface'), namespace='manager')),
]
