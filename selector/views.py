import hashlib
import random
from datetime import datetime
# from datetime import datetime
from io import BytesIO

from croniter import croniter
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponse
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.generic import ListView, DeleteView, CreateView
from rest_framework.response import Response
from rest_framework.views import APIView
from wand.image import Image

from selector.forms import AlbumForm
from selector.models import Picture, PictureGroup, Device


# Create your views here.

# def get_new_picture(picture_group) -> Picture:
#     never_played = list(
#         Picture.objects.filter(last_view_date__isnull=True, picture_group=picture_group).values_list('id', flat=True))
#     played = list(Picture.objects.filter(last_view_date__isnull=False, picture_group=picture_group).order_by(
#         '-last_view_date').values_list('id', flat=True))
#
#     weights = [len(played) + 1] * len(never_played) + list(range(len(played), 0, -1))
#     print(list(zip(never_played + played, weights)))
#     new_picture_id = random.choices(never_played + played, weights=weights, k=1)[0]
#     return Picture.objects.get(id=new_picture_id)
#
#
# def get_last_picture(picture_set) -> Picture:
#     print(picture_set.current_picture_valid_until, timezone.now())
#     print(picture_set.current_picture_valid_until > timezone.now())
#     if not picture_set.current_picture_valid_until or picture_set.current_picture_valid_until < timezone.now():
#         print("Getting new picture")
#         new_picture = get_new_picture(picture_set)
#         new_picture.last_view_date = timezone.now()
#         new_picture.save()
#
#         picture_set.current_picture = new_picture
#         picture_set.current_picture_valid_until = croniter(picture_set.schedule,
#                                                            timezone.localtime(timezone.now())).get_next(datetime)
#
#         picture_set.save()
#     return picture_set.current_picture


class DeviceTokenRequiredMixin:
    """Check device tokens and load device model"""
    device: Device = None

    def dispatch(self, request, *args, **kwargs):
        print(request.headers)
        token = request.headers.get('X-Device-Token')
        if not token:
            return HttpResponse('No token provided', status=403)
        if not Device.objects.filter(token=token).exists():
            return HttpResponse('Invalid token', status=403)

        self.device = Device.objects.get(token=token)
        if "X-Battery-Voltage" in request.headers:
            self.device.last_battery_level = float(request.headers.get("X-Battery-Voltage"))
        self.device.last_seen = timezone.now()
        self.device.last_seen_ip = request.META.get('REMOTE_ADDR')
        self.device.save()
        return super().dispatch(request, *args, **kwargs)


def login(request):
    return render(request, 'selector/login.html')


@login_required
def index(request):
    return render(request, 'selector/index.html')


def overview(request):
    return render(request, 'selector/index_new.html')


def base(request):
    return render(request, 'selector/base.html')


class DeviceListView(PermissionRequiredMixin, ListView):
    model = Device
    template_name = 'selector/devices.html'
    context_object_name = 'devices'
    permission_required = 'selector.view_device'

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user)


class DeviceDeleteView(PermissionRequiredMixin, DeleteView):
    model = Device
    success_url = '/devices'
    permission_required = 'selector.view_device'

    def get(self, request, *args, **kwargs):
        return HttpResponse('Methode not allowed', status=403)


class DeviceCreateView(PermissionRequiredMixin, CreateView):
    model = Device
    success_url = '/devices'
    fields = ['name']
    permission_required = 'selector.view_device'

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.token = hashlib.sha256(str(random.random()).encode('utf-8')).hexdigest()[:16]
        return super().form_valid(form)


class AlbumListView(LoginRequiredMixin, ListView):
    model = PictureGroup
    template_name = 'selector/albums.html'
    context_object_name = 'albums'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['AlbumForm'] = AlbumForm()
        return context

    def get_queryset(self):
        # groups = PictureGroup.objects.filter(users=self.request.user)

        return PictureGroup.objects.filter(users=self.request.user)


class AlbumCreateView(LoginRequiredMixin):

    def post(self, request):
        name = request.POST.get('name')
        schedule = request.POST.get('schedule')
        picture_group = PictureGroup(name=name, schedule=schedule)
        picture_group.save()
        picture_group.users.add(request.user)
        return HttpResponse('OK')


class PictureListView(LoginRequiredMixin, ListView):
    model = Picture
    template_name = 'selector/pictures.html'
    context_object_name = 'pictures'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['album_name'] = PictureGroup.objects.filter(id=self.kwargs['album_id']).first().name
        return context

    def get_queryset(self):
        return Picture.objects.filter(picture_group__users=self.request.user, picture_group__id=self.kwargs['album_id'])


class LastImage(DeviceTokenRequiredMixin, APIView):
    def get(self, request):
        picture_set: PictureGroup = self.device.picture_group
        if not picture_set:
            return HttpResponse('No picture set', status=404)

        last_image_file = picture_set.get_last_picture()
        return HttpResponse(last_image_file.image.read(), content_type='image/bmp')


class LastImageRaw(DeviceTokenRequiredMixin, APIView):
    def get(self, request):
        picture_set: PictureGroup = self.device.picture_group
        if not picture_set:
            return HttpResponse('No picture set', status=404)

        last_image_file = picture_set.get_last_picture()
        return HttpResponse(last_image_file.raw_image.read(), content_type='image/raw')


class NextWakeup(DeviceTokenRequiredMixin, APIView):

    def get(self, request):
        picture_set: PictureGroup = self.device.picture_group
        if not picture_set:
            return HttpResponse('No picture set', status=404)
        picture_set.get_last_picture()
        next_picture = picture_set.current_picture_valid_until
        sleep_in_seconds = int((next_picture - timezone.now()).total_seconds() + 10)
        return HttpResponse(str(sleep_in_seconds))


class CurrentImageId(DeviceTokenRequiredMixin, APIView):
    def get(self, request):
        picture_set: PictureGroup = self.device.picture_group
        if not picture_set:
            return HttpResponse('No picture set', status=404)
        return HttpResponse(str(picture_set.get_last_picture().id))

class Upload(APIView):

    def get(self, request, album_id, format=None):
        return TemplateResponse(request, 'selector/upload_image.html', {'album_id': album_id})

    def post(self, request, album_id, format=None):

        if 'image' not in request.data:
            return Response(status=400, data='No image file')
        image: InMemoryUploadedFile = request.data['image']
        image_data = image.read()
        with Image(blob=image_data) as img:
            with Image(filename="selector/color_map.bmp") as color_map:
                img.remap(affinity=color_map, method='floyd_steinberg')
                # img.type = 'truecolor'
                img.depth = 8
                width, height = img.size
                blob = img.make_blob(format='rgb')
                image_buffer = BytesIO(img.make_blob())
                proces_image = InMemoryUploadedFile(image_buffer, None, image.name, 'image/bmp', img.size, None)

                buffer = BytesIO()
                first_segment = None
                for cursor in range(0, len(blob), 3):
                    data = None
                    match blob[cursor], blob[cursor + 1], blob[cursor + 2]:
                        case (0, 0, 0):
                            data = '0000'
                        case (255, 255, 255):
                            data = '0001'
                        case (0, 255, 0):
                            data = '0010'
                        case (0, 0, 255):
                            data = '0011'
                        case (255, 0, 0):
                            data = '0100'
                        case (255, 255, 0):
                            data = '0101'
                        case (255, 128, 0):
                            data = '0110'
                    if first_segment:
                        buffer.write(int(first_segment + data, 2).to_bytes())
                        first_segment = None
                    else:
                        first_segment = data
                if first_segment:
                    buffer.write(int(first_segment + '0000', 2).to_bytes())

                    # print(f"r: {blob[cursor]}, g: {blob[cursor + 1]}, b: {blob[cursor + 2]}")
                    # unique_colors.add((blob[cursor], blob[cursor + 1], blob[cursor + 2]))

                # print(f"Unique colors: {unique_colors}")
                image = InMemoryUploadedFile(buffer, None, image.name, 'image/raw', img.size, None)
                picture_group = PictureGroup.objects.get(id=album_id)
                picture = Picture(image=proces_image, raw_image=image, name=image.name)
                picture.save()
                picture_group.pictures.add(picture)
                # picture_group.pictures.create(image=proces_image, raw_image=image, name=image.name).save()
                return Response(status=200, data=picture.image.url)

#
# def imageList(ListView):
#     return render(ListView, 'selector/imageList.html')
