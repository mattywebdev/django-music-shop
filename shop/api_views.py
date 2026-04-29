from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db.models import Q
from .models import Album, Track, Artist
from .serializers import AlbumSerializer, TrackSerializer
from django.core.paginator import Paginator, EmptyPage




class SmallPaginator(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100

@api_view(["GET"])
def albums_api(request):
    params = request.query_params if hasattr(request, "query_params") else request.GET

    qs = Album.objects.select_related("artist", "genre").all()

    # Filters
    q = (params.get("q") or "").strip()
    artist = params.get("artist")
    genre = params.get("genre")
    albums_id = params.get("album")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(artist__name__icontains=q))
    if artist and str(artist).isdigit():
        qs = qs.filter(artist_id=int(artist))
    if genre and str(genre).isdigit():
        qs = qs.filter(genre_id=int(genre))

    # Ordering (whitelist)
    ordering = params.get("ordering", "-release_date")
    allowed = {"title", "-title", "price", "-price", "release_date", "-release_date"}
    if ordering in allowed:
        qs = qs.order_by(ordering)

    # Decide if we should return a paginated shape
    should_paginate = any(k in params for k in ("page", "page_size", "ordering"))

    if should_paginate:
        paginator = SmallPaginator()
        page = paginator.paginate_queryset(qs, request)

        if page is None:  # no ?page= given (e.g. only ?ordering=-price)
            data = AlbumSerializer(qs[:paginator.page_size], many=True).data
            return Response({
                "count": qs.count(),
                "next": None,
                "previous": None,
                "results": data,
            })

        data = AlbumSerializer(page, many=True).data
        return paginator.get_paginated_response(data)

    # Legacy plain list for callers that expect a list
    return Response(AlbumSerializer(qs, many=True).data)

@api_view(["GET", "POST"])
def tracks_api(request):
    qs = Track.objects.select_related("artist", "album", "album__genre").all()

    q = request.GET.get("q")
    artist = request.GET.get("artist")
    album = request.GET.get("album")
    ordering = request.GET.get("ordering", "title")

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(artist__name__icontains=q))
    if artist:
        if artist.isdigit():
            qs = qs.filter(artist_id=int(artist))
        else:
            qs = qs.filter(artist__name__icontains=artist)

    if album:
        if album.isdigit():
            qs = qs.filter(album_id=int(album))
        else:
            qs = qs.filter(album__title__icontains=album)

    if ordering in {"title", "-title", "price", "-price"}:
        qs = qs.order_by(ordering)

    if request.GET.get("page"):
        paginator = SmallPaginator()
        page = paginator.paginate_queryset(qs, request)
        data = TrackSerializer(page, many=True).data
        return paginator.get_paginated_response(data)
    
    elif request.method == "POST":
        serializer = TrackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    return Response(TrackSerializer(qs, many=True).data)

@api_view(["GET"])
def search_suggest(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return Response({"artists": [], "albums": [], "tracks": []})

    # startswith for snappy, predictable suggestions
    artists = list(
        Artist.objects.filter(name__istartswith=q).order_by("name")[:5]
        .values("id", "name")
    )
    albums_qs = (
        Album.objects.select_related("artist")
        .filter(title__istartswith=q)
        .order_by("title")[:5]
    )
    albums = [{
        "id": a.id,
        "title": a.title,
        "artist": a.artist.name,
        "cover": (a.cover_image.url if getattr(a, "cover_image", None) else None),
    } for a in albums_qs]

    tracks_qs = (
        Track.objects.select_related("artist", "album")
        .filter(title__istartswith=q)
        .order_by("title")[:5]
    )
    tracks = [{
        "id": t.id,
        "title": t.title,
        "artist": t.artist.name,
        "album": (t.album.title if t.album_id else None),
        "cover": (t.album.cover_image.url if getattr(getattr(t, "album", None), "cover_image", None) else None),
    } for t in tracks_qs]

    # 🧢 NEW: merchandise
    from .models import Tshirt, Vinyl, Poster
    merch = []

    for m in Tshirt.objects.filter(artist__name__istartswith=q)[:3]:
        merch.append({
            "id": m.id,
            "title": f"{m.artist.name} T-shirt ({m.size}, {m.color})",
            "type": "T-shirt",
            "cover": m.image.url if m.image else None
        })
    for m in Vinyl.objects.filter(artist__name__istartswith=q)[:3]:
        merch.append({
            "id": m.id,
            "title": f"{m.artist.name} Vinyl ({m.edition})",
            "type": "Vinyl",
            "cover": m.image.url if m.image else None
        })
    for m in Poster.objects.filter(artist__name__istartswith=q)[:3]:
        merch.append({
            "id": m.id,
            "title": f"{m.artist.name} Poster ({m.dimensions})",
            "type": "Poster",
            "cover": m.image.url if m.image else None
        })

    return Response({
        "artists": artists,
        "albums": albums,
        "tracks": tracks,
        "merch": merch,   # ✅ added
    })
