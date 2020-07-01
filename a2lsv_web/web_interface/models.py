from django.contrib.auth.models import AbstractUser
from django.db import models

class Languages(models.Model):
    name = models.CharField(max_length=5)
    def __str__(self):
        return self.name

class User(AbstractUser):
    is_labeler = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    language = models.ForeignKey(Languages, on_delete=models.CASCADE)

    
class Datasets(models.Model):
    name = models.CharField(max_length=50)
    language = models.ForeignKey(Languages, on_delete=models.CASCADE)
    countOfDownloadeds = models.IntegerField(default=0)
    countOfDiarized = models.IntegerField(default=0)
    countOfLabeleds = models.IntegerField(default=0)

    def __str__(self):
        return self.name +" - " +self.language.name
