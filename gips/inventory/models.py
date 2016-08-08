from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    shapefile = models.CharField(max_length=1000, primary_key=True)
    created = models.DateTimeField(editable=False, auto_now_add=True)
    modified = models.DateTimeField(editable=False, auto_now=True)
    owner = models.ForeignKey(User, null=True)

    def __unicode__(self):
        return self.shapefile

class FileAsset(models.Model):
    filepath = models.CharField(max_length=1000, primary_key=True)
    product = models.CharField(max_length=256, null=True, blank=True)
    sensor = models.CharField(max_length=256, null=True, blank=True)
    project = models.ForeignKey(Project, null=True)
    created = models.DateTimeField(editable=False, auto_now_add=True)
    modified = models.DateTimeField(editable=False, auto_now=True)

    def __unicode__(self):
        return self.filepath


class Command(models.Model):
    user = models.ForeignKey(User, null=True)
    command = models.TextField(primary_key=True)
    created = models.DateTimeField(editable=False, auto_now_add=True)

    def __unicode__(self):
        return self.command