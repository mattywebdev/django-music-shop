from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageOps

import django


BASE_DIR = Path(__file__).resolve().parents[1]
MEDIA_DIR = BASE_DIR / "media"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


AUDIO_MAP = {
    "audio_previews/futility.mp3": "audio_previews/afterglow-transit-preview.mp3",
    "audio_previews/heeh.mp3": "audio_previews/city-lights-quiet-rooms-preview.mp3",
    "audio_previews/eciles.wav": "audio_previews/blue-hour-letters-preview.mp3",
    "audio_previews/recreantbass.mp3": "audio_previews/tides-beneath-glass-preview.mp3",
    "track_previews/doodle.mp3": "track_previews/midnight-sketch-preview.mp3",
    "track_previews/pisces.mp3": "track_previews/blue-hour-drift-preview.mp3",
    "track_previews/eciles.wav": "track_previews/glass-platform-preview.mp3",
    "track_previews/recreantbass.mp3": "track_previews/low-orbit-groove-preview.mp3",
    "ambient_previews/fireplace.mp3": "ambient_previews/fireside-room-tone-preview.mp3",
}

ALBUM_EXTRA_AUDIO = {
    "track_previews/doodle.mp3": "audio_previews/neon-weather-systems-preview.mp3",
}

IMAGE_MAP = {
    "album_covers/snow.jpg": "album_covers/afterglow-transit-cover.jpg",
    "album_covers/the_fall.jpg": "album_covers/city-lights-quiet-rooms-cover.jpg",
    "album_covers/the_forest.jpg": "album_covers/tides-beneath-glass-cover.jpg",
    "album_covers/Gehennas.png": "album_covers/neon-weather-systems-cover.jpg",
    "ambient_covers/fireplace.jpg": "ambient_covers/fireside-room-tone-cover.jpg",
    "merch_images/tshirt.jpg": "merch_images/artist-tshirt-black-cover.jpg",
    "merch_images/Free_Vinyl_Mockup_2.jpg": "merch_images/collectors-vinyl-mockup.jpg",
    "merch_images/dan-loftus-N4CnMbcZe70-unsplash.jpg": "merch_images/forest-lantern-poster.jpg",
    "merch_images/yan-lee-GnZyUqc5bv4-unsplash.jpg": "merch_images/autumn-lane-poster.jpg",
}

UNREFERENCED_MEDIA = [
    "eciles.wav",
    "futility.mp3",
    "heeh.mp3",
    "snow.jpg",
    "the fall.jpg",
    "the forest.jpg",
    "audio_previews/Volumes_-_Erased.mid",
]


def rel_path(path: str) -> Path:
    return MEDIA_DIR / path.replace("/", os.sep)


def run_ffmpeg(source: Path, target: Path, seconds: int = 35, bitrate: str = "96k") -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        FFMPEG,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-t",
        str(seconds),
        "-vn",
        "-ac",
        "2",
        "-ar",
        "44100",
        "-b:a",
        bitrate,
        str(target),
    ]
    subprocess.run(cmd, check=True)


def optimize_image(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((1400, 1400), Image.Resampling.LANCZOS)
        img.save(target, "JPEG", quality=78, optimize=True, progressive=True)


def convert_media() -> None:
    for old, new in AUDIO_MAP.items():
        run_ffmpeg(rel_path(old), rel_path(new))
    for old, new in ALBUM_EXTRA_AUDIO.items():
        run_ffmpeg(rel_path(old), rel_path(new))
    for old, new in IMAGE_MAP.items():
        optimize_image(rel_path(old), rel_path(new))


def update_database() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "music_shop.settings")
    django.setup()
    from shop.models import Album, Ambient, Poster, Track, Tshirt, Vinyl

    for album in Album.objects.all():
        cover = str(album.cover_image)
        preview = str(album.preview_clip)
        if cover in IMAGE_MAP:
            album.cover_image = IMAGE_MAP[cover]
        if preview in AUDIO_MAP:
            album.preview_clip = AUDIO_MAP[preview]
        if preview in ALBUM_EXTRA_AUDIO:
            album.preview_clip = ALBUM_EXTRA_AUDIO[preview]
        album.save(update_fields=["cover_image", "preview_clip"])

    for track in Track.objects.all():
        preview = str(track.preview_clip)
        if preview in AUDIO_MAP:
            track.preview_clip = AUDIO_MAP[preview]
            track.save(update_fields=["preview_clip"])

    for ambient in Ambient.objects.all():
        cover = str(ambient.cover_image)
        preview = str(ambient.preview_clip)
        changed = []
        if cover in IMAGE_MAP:
            ambient.cover_image = IMAGE_MAP[cover]
            changed.append("cover_image")
        if preview in AUDIO_MAP:
            ambient.preview_clip = AUDIO_MAP[preview]
            changed.append("preview_clip")
        if changed:
            ambient.save(update_fields=changed)

    for model in (Tshirt, Vinyl, Poster):
        for item in model.objects.all():
            image = str(item.image)
            if image in IMAGE_MAP:
                item.image = IMAGE_MAP[image]
                item.save(update_fields=["image"])


def update_fixtures() -> None:
    replacements = {}
    replacements.update(AUDIO_MAP)
    replacements.update(ALBUM_EXTRA_AUDIO)
    replacements.update(IMAGE_MAP)
    for fixture in (BASE_DIR / "demo_store_data_professional.json", BASE_DIR / "demo_store_data_final.json"):
        if not fixture.exists():
            continue
        data = fixture.read_text(encoding="utf-8")
        for old, new in replacements.items():
            data = data.replace(old, new)
        fixture.write_text(data, encoding="utf-8")


def remove_old_media() -> None:
    stale = set(AUDIO_MAP) | set(ALBUM_EXTRA_AUDIO) | set(IMAGE_MAP) | set(UNREFERENCED_MEDIA)
    for name in sorted(stale):
        path = rel_path(name)
        if path.exists():
            path.unlink()


def summarize() -> None:
    files = sorted([p for p in MEDIA_DIR.rglob("*") if p.is_file()], key=lambda p: p.stat().st_size, reverse=True)
    total = sum(p.stat().st_size for p in files)
    print(f"Media total: {total / (1024 * 1024):.2f} MB")
    for path in files[:20]:
        print(f"{path.relative_to(MEDIA_DIR).as_posix():55s} {path.stat().st_size / 1024:.1f} KB")


def main() -> None:
    before = sum(p.stat().st_size for p in MEDIA_DIR.rglob("*") if p.is_file())
    print(f"Before: {before / (1024 * 1024):.2f} MB")
    convert_media()
    update_database()
    update_fixtures()
    remove_old_media()
    summarize()


if __name__ == "__main__":
    main()
