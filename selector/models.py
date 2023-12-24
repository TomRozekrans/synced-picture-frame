import random
from datetime import timedelta, datetime
from typing import Optional

from croniter import croniter
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


# Create your models here.


class User(AbstractUser):
   pass
    # class Meta:
    #     permissions = [
    #         ("view_users", "Can view users"),
    #
    #     ]


class BateryLevel(models.Model):
    level = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)
    device = models.ForeignKey('Device', on_delete=models.CASCADE, related_name='battery_levels')

    def __str__(self):
        return f'{self.level}V'


class Device(models.Model):
    token = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    last_seen = models.DateTimeField(null=True, blank=True)
    last_seen_ip = models.CharField(max_length=100, null=True, blank=True)
    last_battery_level = models.FloatField(null=True, blank=True)
    user = models.ForeignKey('User', on_delete=models.DO_NOTHING, related_name='devices')
    picture_group = models.ForeignKey('PictureGroup', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        permissions = [
            ("view_devices", "Can view devices"),
        ]

    def set_last_battery_level(self, level):
        self.last_battery_level = level
        self.save()
        BateryLevel.objects.create(level=level, device=self)

    @property
    def status(self):
        if self.last_seen is None:
            return 'offline'

        if timezone.now() - self.last_seen > timedelta(days=2):
            return 'offline'
        elif timezone.now() - self.last_seen > timedelta(days=1) or (
                self.last_battery_level < 3.4) if self.last_battery_level else False:
            return 'warning'
        else:
            return 'online'

    @property
    def status_message(self):
        status = ""

        if self.last_seen is None:
            return 'Device has never been seen.'
        elif timezone.now() - self.last_seen > timedelta(days=2):
            status = 'Device was last seen more than 2 days ago.'
        elif timezone.now() - self.last_seen > timedelta(days=1):
            status = 'Device was last seen more than 1 day ago.'

        if self.last_battery_level and self.last_battery_level < 3.4:
            status += '\n Battery level is low.'

        return status

    def __str__(self):
        return self.name


class Picture(models.Model):
    name = models.CharField(max_length=100)
    upload_data = models.DateTimeField(auto_now_add=True)
    last_view_date = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to='images/')
    raw_image = models.ImageField(upload_to='images_raw/')

    def delete(self, using=None, keep_parents=False):
        self.image.delete()
        self.raw_image.delete()
        super().delete(using=using, keep_parents=keep_parents)

    def __str__(self):
        return self.name


class PictureGroup(models.Model):
    name = models.CharField(max_length=100)
    schedule = models.CharField(max_length=100)
    pictures = models.ManyToManyField('Picture', blank=True, related_name='picture_group')
    current_picture = models.ForeignKey('Picture', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='current_picture_for_group')
    current_picture_valid_until = models.DateTimeField(null=True, blank=True)
    users = models.ManyToManyField('User', blank=True, related_name='picture_groups')
    admins = models.ManyToManyField('User', related_name='admin_picture_groups')

    def get_new_picture(self) -> Optional[Picture]:

        if self.pictures.count() == 1:
            return self.pictures.first()

        if self.pictures.count() == 0:
            return None

        never_played = list(
            Picture.objects.filter(last_view_date__isnull=True, picture_group=self).values_list('id',
                                                                                                flat=True))
        played = list(Picture.objects
                      .filter(last_view_date__isnull=False, picture_group=self)
                      .exclude(id=self.current_picture.id)
                      .order_by('last_view_date').values_list('id', flat=True))

        weights = [len(played) + 1] * len(never_played) + list(range(len(played), 0, -1))
        print(list(zip(never_played + played, weights)))
        new_picture_id = random.choices(never_played + played, weights=weights, k=1)[0]
        return Picture.objects.get(id=new_picture_id)

    def get_last_picture(self) -> Optional[Picture]:
        print(self.current_picture_valid_until, timezone.now())
        # print(self.current_picture_valid_until > timezone.now())
        if not self.current_picture_valid_until or self.current_picture_valid_until < timezone.now() or not self.current_picture:
            print("Getting new picture")
            new_picture = self.get_new_picture()
            if not new_picture:
                return None
            new_picture.last_view_date = timezone.now()
            new_picture.save()

            self.current_picture = new_picture
            self.current_picture_valid_until = croniter(self.schedule,
                                                        timezone.localtime(timezone.now())).get_next(datetime)

            self.save()
        return self.current_picture

    def __str__(self):
        return self.name
