from django.db import models
from django.contrib.postgres.fields import JSONField


class Profile(models.Model):
    membership_id = models.FloatField(null=True, blank=True)
    content = JSONField(null=True)

    date_create = models.DateTimeField(auto_now_add=True)
    date_update = models.DateTimeField(auto_now=True)


class Activity(models.Model):
    char_id = models.FloatField(null=True, blank=True)
    mode_id = models.IntegerField(null=True, blank=True)

    content = JSONField(null=True)

    date_create = models.DateTimeField(auto_now_add=True)
    date_update = models.DateTimeField(auto_now=True)


class Raid(models.Model):
    raid_id = models.FloatField(null=True, blank=True)
    content = JSONField(null=True)

    date_create = models.DateTimeField(auto_now_add=True)
    date_update = models.DateTimeField(auto_now=True)
