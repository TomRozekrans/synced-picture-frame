from croniter import croniter
from django import forms

from selector.models import PictureGroup


class AlbumForm(forms.ModelForm):
    class Meta:
        model = PictureGroup
        fields = ["name", "schedule", "users"]
        widgets = {
            'users': forms.SelectMultiple(attrs={'class': 'form-control'}),
            "schedule": forms.TextInput(attrs={'placeholder': '0 0 * * *', "class": "form-control"}), # 0 0 * * * = every day at midnight
            "name": forms.TextInput(attrs={'placeholder': 'Album name', "class": "form-control"}),
        }


    def clean_schedule(self):
        schedule = self.cleaned_data['schedule']

        if not croniter.is_valid(schedule):
            raise forms.ValidationError("Schedule must be a valid cron expression.")
        return schedule
