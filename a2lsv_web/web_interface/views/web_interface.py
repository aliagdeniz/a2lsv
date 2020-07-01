from django.shortcuts import redirect, render
from django.views.generic import TemplateView


class SignUpView(TemplateView):
    template_name = 'registration/signup.html'


def home(request):
    if request.user.is_authenticated:
        if request.user.is_manager:
            return redirect('manager:listDatasets')
        else:
            return redirect('labeler:listAudios')
    return render(request, 'web_interface/home.html')
