from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("overview/", views.overview, name="overview"),
    path("base/", views.base, name="base"),
    path("login/", auth_views.LoginView.as_view(template_name="selector/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("devices/", views.DeviceListView.as_view(), name="devices"),
    path("devices/<int:pk>/", views.DeviceDetailView.as_view(), name="device_detail"),
    path("devices/<int:pk>/delete/", views.DeviceDeleteView.as_view(), name="device_delete"),
    path("devices/<int:pk>/update/", views.DeviceUpdateView.as_view(), name="device_update"),
    path("devices/new/", views.DeviceCreateView.as_view(), name="device_new"),

    path("albums/", views.AlbumListView.as_view(), name="albums"),
    path("albums/new/", views.AlbumCreateView.as_view(), name="album_new"),
    path("albums/<int:album_id>/", views.PictureListView.as_view(), name="pictures"),
    path("albums/<int:pk>/update/", views.AlbumUpdateView.as_view(), name="album_update"),
    path("albums/<int:pk>/delete/", views.AlbumDeleteView.as_view(), name="album_delete"),

    path("albums/<int:album_id>/images/create", views.Upload.as_view(), name="upload_image"),



    # API
    path("last_image/", views.LastImage.as_view(), name="last_image"),
    path("last_image_raw/", views.LastImageRaw.as_view(), name="last_image_raw"),
    path("next_wakeup/", views.NextWakeup.as_view(), name="next_wakeup"),
    path("current_image_id/", views.CurrentImageId.as_view(), name="current_image_id"),
]
