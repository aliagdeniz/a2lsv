from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django.urls import reverse_lazy

from ..decorators import manager_required
from ..forms import ManagerSignUpForm, LabelerSignUpForm, CreateAudioFetcherForm
from ..models import User, Datasets


from kafkaUtils import *

import sys
sys.path.append('../')
# from mongoDbUtils import *



@method_decorator([manager_required], name='dispatch')
class ManagerSignUpView(CreateView):
    model = User
    form_class = ManagerSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'manager'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('manager:listDatasets')

@method_decorator([login_required, manager_required], name='dispatch')
class LabelerSignUpView(CreateView):
    model = User
    form_class = LabelerSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'labeler'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('manager:listDatasets')

def listDatasets(request):
    if request.user.is_authenticated and request.user.is_manager:
        # db = getDB()
        # cursor = db.datasets.find({})
        cursor = Datasets.objects.all()
        datasets = []
        for i in cursor:
            datasets.append({
                'name':i.name,
                'lang':i.language,
                'countOfDownloadeds': i.countOfDownloadeds,
                'countOfDiarized': i.countOfDiarized,
                'countOfLabeleds': i.countOfLabeleds,
                })
        return render(request, 'web_interface/manager/dataset_list.html',
                      { 'datasets': datasets })
    else:
        return redirect('login')

def get_keyword(request):
    if request.user.is_authenticated and request.user.is_manager:
        if request.method == 'POST':
            form = CreateAudioFetcherForm(request.POST)
            if form.is_valid():
                dataset_id = request.POST.get('dataset_id')
                keyword = request.POST.get('keyword')
                obj = Datasets.objects.filter(id=dataset_id)[0]
                dataset_name, lang = obj.name, obj.language
                print("keyword to fetch video is added; dataset: {0}, lang:{1}, keyword:{2}".format(dataset_name, lang, keyword) )

                kafka_producer = connect_kafka_producer()
                publish_message(kafka_producer, 'searchByKeyword', 'infos', '{0};{1};{2}'.format(dataset_name, lang, keyword) )
                return redirect('manager:listDatasets')
        else:
            form = CreateAudioFetcherForm()
        return render(request, 'web_interface/manager/start_audio_fetcher_form.html', {'form': form})
    else:
        return redirect('login')
    
@method_decorator([login_required, manager_required], name='dispatch')
class DatasetCreateView(CreateView):
    model = Datasets
    fields = ('name', 'language')
    template_name = 'web_interface/manager/dataset_add_form.html'
    success_url = reverse_lazy('manager:listDatasets')

@method_decorator([login_required, manager_required], name='dispatch')
class DatasetUpdateView(UpdateView):
    model = Datasets
    fields = ('name', 'language')
    template_name = 'web_interface/manager/dataset_add_form.html'
    success_url = reverse_lazy('manager:listDatasets')
        
