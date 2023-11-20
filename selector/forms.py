import hashlib
import random

from croniter import croniter
from django import forms
from django.db.models import Q

from selector.models import PictureGroup, Device


class AlbumForm(forms.ModelForm):
    class Meta:
        model = PictureGroup
        fields = ["name", "schedule", "users"]
        widgets = {
            'users': forms.SelectMultiple(attrs={'class': 'form-control'}),
            "schedule": forms.TextInput(
                attrs={'placeholder': '0 0 * * *', "class": "form-control", "value": "0 0 * * *"}),
            # 0 0 * * * = every day at midnight
            "name": forms.TextInput(attrs={'placeholder': 'Album name', "class": "form-control"}),
        }

    def clean_schedule(self):
        schedule = self.cleaned_data['schedule']

        if not croniter.is_valid(schedule):
            raise forms.ValidationError("Schedule must be a valid cron expression.")
        return schedule


class AlbumFormUpdate(forms.ModelForm):
    class Meta:
        model = PictureGroup
        fields = ["name", "schedule", "users", "admins"]
        widgets = {
            'users': forms.SelectMultiple(attrs={'class': 'form-control'}),
            "schedule": forms.TextInput(
                attrs={'placeholder': '0 0 * * *', "class": "form-control", "value": "0 0 * * *"}),
            # 0 0 * * * = every day at midnight
            "name": forms.TextInput(attrs={'placeholder': 'Album name', "class": "form-control"}),
            'admins': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def clean_schedule(self):
        schedule = self.cleaned_data['schedule']

        if not croniter.is_valid(schedule):
            raise forms.ValidationError("Schedule must be a valid cron expression.")
        return schedule


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ["name", "picture_group"]
        exclude = ("token", "user",)
        widgets = {
            "name": forms.TextInput(attrs={'placeholder': 'Device name', "class": "form-control"}),
            'picture_group': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, user, *args, **kwargs):
        # user = kwargs.pop('user', None)
        super(DeviceForm, self).__init__(*args, **kwargs)
        self.fields['picture_group'].queryset = PictureGroup.objects.filter(Q(users=user) | Q(admins=user)).distinct()
