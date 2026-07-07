"""
Race photo albums for the Santa Fe Half Marathon MCP server.

Photos live in two places: RunSignup's RaceDay Photos galleries (public, by
event day) and the organizer's Google Drive folders. This module is a small
registry of album links so the `race_photos` tool and `race://photos` resource
can point runners and the website at them. It returns LINKS, not image bytes —
the server never proxies Drive auth or re-hosts photos.
"""

from __future__ import annotations

# RunSignup RaceDay Photos (race 83604). Albums are keyed by year; the value is
# the gallery URL. `raceEventDaysId` picks the album for that edition.
RUNSIGNUP_ALBUMS = {
    "all": "https://runsignup.com/Race/Photos/NM/SantaFe/SantaFeInternationalHalfMarathon",
    "start_line": "https://runsignup.com/Race/Photos/Location/StartLine2/NM/SantaFe/SantaFeInternationalHalfMarathon",
    2025: "https://runsignup.com/Race/Photos/NM/SantaFe/SantaFeInternationalHalfMarathon?raceEventDaysId=322663",
    2022: "https://runsignup.com/Race/Photos/NM/SantaFe/SantaFeInternationalHalfMarathon?raceEventDaysId=204445",
    2020: "https://runsignup.com/Race/Photos/NM/SantaFe/SantaFeInternationalHalfMarathon?raceEventDaysId=142450",
}

# Google Drive photo folders (organizer archive + curated website gallery).
DRIVE_ALBUMS = {
    "website_gallery": "https://drive.google.com/drive/folders/10nod96Yb4hhBc23SpF1Rgk2HknRRXZvN",
    "marathon_archive": "https://drive.google.com/drive/folders/18T9yO8u-4QG9k3pEY9GmHvEgMDtOOV2Y",
}

# OneDrive shared albums (professional photographer sets).
ONEDRIVE_ALBUMS = {
    "2025_pro": "https://1drv.ms/f/c/e871014f27325bae/ElQomfBWl1dPg0eIlpRRgMsBoFZdxX-HCI5_xl_DTGZKRw?e=42Ebf1",
}


def get_photos(year=None) -> dict:
    """Return photo-album links. If `year` matches a RunSignup album, highlight it."""
    runsignup = {
        "all_albums": RUNSIGNUP_ALBUMS["all"],
        "start_line": RUNSIGNUP_ALBUMS["start_line"],
        "by_year": {str(y): url for y, url in RUNSIGNUP_ALBUMS.items()
                    if isinstance(y, int)},
    }
    out = {"runsignup": runsignup, "google_drive": dict(DRIVE_ALBUMS),
           "onedrive": dict(ONEDRIVE_ALBUMS)}
    if year is not None:
        album = RUNSIGNUP_ALBUMS.get(year)
        out["requested_year"] = year
        out["requested_album"] = album or "no RunSignup album for that year"
    return out
