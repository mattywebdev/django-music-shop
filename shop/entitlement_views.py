from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render

from .models import Album, DigitalEntitlement, Track


def _entitled_tracks(entitlement):
    tracks = Track.objects.select_related("album").exclude(download_file="")
    if entitlement.product_type == "album":
        return tracks.filter(album_id=entitlement.product_id)
    if entitlement.product_type == "track":
        return tracks.filter(pk=entitlement.product_id)
    return tracks.none()


@login_required(login_url="login")
def purchase_library(request):
    entitlements = (
        DigitalEntitlement.objects
        .filter(user=request.user, is_active=True, order__status="paid")
        .select_related("order", "order_item")
    )
    purchases = []
    for entitlement in entitlements:
        if entitlement.product_type == "album":
            product = Album.objects.filter(pk=entitlement.product_id).first()
        else:
            product = Track.objects.select_related("album").filter(
                pk=entitlement.product_id
            ).first()
        purchases.append({
            "entitlement": entitlement,
            "title": getattr(product, "title", entitlement.order_item.title),
            "tracks": _entitled_tracks(entitlement),
        })
    return render(request, "shop/account/purchases.html", {"purchases": purchases})


@login_required(login_url="login")
def download_track(request, entitlement_id, track_id):
    entitlement = get_object_or_404(
        DigitalEntitlement.objects.select_related("order"),
        public_id=entitlement_id,
        user=request.user,
        is_active=True,
        order__status="paid",
    )
    track = get_object_or_404(_entitled_tracks(entitlement), pk=track_id)
    try:
        file_handle = track.download_file.open("rb")
    except (FileNotFoundError, OSError, ValueError) as exc:
        raise Http404("Download file is unavailable.") from exc

    filename = Path(track.download_file.name).name
    return FileResponse(file_handle, as_attachment=True, filename=filename)
