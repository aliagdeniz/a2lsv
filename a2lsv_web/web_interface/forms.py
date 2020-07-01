from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms.utils import ValidationError
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy

from web_interface.models import (User, Datasets, Languages)

class ManagerSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_manager = True
        if commit:
            user.save()
        return user

class LabelerSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'language',)

    # language = forms.ModelMultipleChoiceField(label="Language", queryset=Languages.objects.all(), required=True)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_labeler = True
        if commit:
            user.save()
        return user

class CreateAudioFetcherForm(forms.Form):
    keyword = forms.CharField(label='Search keyword', max_length=100, required=True)
    dataset_id = forms.ModelMultipleChoiceField(label="Dataset", queryset=Datasets.objects.all(), required=True)

# class DatasetCreateForm(forms.ModelForm):
#     class Meta:
#         model = Datasets
#         fields = ['name', 'language' ]

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['language'].queryset = Languages.objects.none()


