"""Make a short ORIGINAL LinkedIn-ready MP4 teaser from verified publisher screenshots.

This does not download, reproduce, or repost the publisher's promotional video.
Uses captured UI screenshots only for editorial illustration, with attribution.
Manual publishing remains separate. Requires Pillow + imageio-ffmpeg.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from source_visuals import ensure_source_images

ROOT = Path(__file__).resolve().parents[1]
SIZE = (1080, 1350)
INK = (8, 15, 44)
BLUE = (25, 81, 253)
WHITE = (249, 251, 255)


def _font(px: int, bold: bool = False):
    candidates = ([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ] if bold else [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ])
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, px)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    lines = []
    for para in text.splitlines():
        words = para.split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if line and draw.textbbox((0,0), candidate, font=font)[2] > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
    return lines


def _frame(shot: Path, title: str, subtitle: str, source: str, index: int) -> Image.Image:
    canvas = Image.new("RGB", SIZE, WHITE if index % 2 else INK)
    d = ImageDraw.Draw(canvas)
    dark = index % 2 == 0
    fg = WHITE if dark else INK
    accent = (107,177,255) if dark else BLUE
    d.rectangle((0,0,1080,24), fill=accent)
    d.text((72,74), "FIELD NOTES   /   AI + COMMERCE", font=_font(23,True), fill=accent)
    y = 158
    font = _font(64 if index else 76,True)
    for line in _wrap(d,title,font,925)[:4]:
        d.text((70,y),line,font=font,fill=fg)
        y += 87 if index == 0 else 76
    image = Image.open(shot).convert("RGB")
    # Source image stays a photographic screenshot: no fabricated UI elements.
    crop = ImageOps.fit(image,(936,590),method=Image.Resampling.LANCZOS,
                        centering=(0.5,0.12))
    top = max(y+44,505)
    top = min(top,650)
    d.rectangle((64,top-7,1016,top+603), fill=accent)
    canvas.paste(crop,(72,top))
    d.text((72,top+631),"ORIGINAL SOURCE VISUAL  ·  " + source.upper()[:40],
           font=_font(19,True), fill=accent)
    sf = _font(31)
    for line_no,line in enumerate(_wrap(d,subtitle,sf,917)[:2]):
        d.text((72,top+687+42*line_no),line,font=sf,fill=fg)
    d.rectangle((72,1262,1010,1265),fill=accent)
    d.text((72,1281),"WAJAHAT NAQVI",font=_font(20,True),fill=fg)
    d.text((880,1281),f"{index+1:02d} / 03",font=_font(18),fill=fg)
    return canvas


def render_teaser(post: dict, output: Path) -> Path | None:
    carousel=(post.get("document") or {}).get("carousel") or {}
    source=carousel.get("source_visuals") or {}
    if not source.get("enabled"):
        return None
    shots=ensure_source_images(carousel)
    if len(shots)<3:
        return None
    slides=carousel.get("slides") or []
    title=str(slides[0].get("title") or post.get("topic") or "Developer update")
    captions=[
        (title, "What this launch changes for developers"),
        (str(slides[1].get("title") or "What's new"),"A look at the original announcement"),
        (str(slides[-1].get("title") or "The developer question"),
         str(slides[-1].get("subtitle") or "What would you build differently?")),
    ]
    frames=output.parent / f".{output.stem}-frames"
    frames.mkdir(parents=True,exist_ok=True)
    for i,((head, sub),shot) in enumerate(zip(captions,shots)):
        _frame(Path(shot),head,sub,source.get("attribution","official source"),i).save(
            frames/f"frame-{i:02d}.png",optimize=True)
    import imageio_ffmpeg
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    output.parent.mkdir(parents=True,exist_ok=True)
    # Original 12 second teaser: gentle camera push on each slide, no source
    # video or audio borrowed, no copyrighted music. Posting is still manual.
    command=[
        ffmpeg,"-hide_banner","-loglevel","error","-y",
        "-framerate","1/4","-i",str(frames/"frame-%02d.png"),
        "-vf","zoompan=z='min(zoom+0.00045,1.065)':d=100:s=1080x1350:fps=25,format=yuv420p",
        "-c:v","libx264","-preset","veryfast","-crf","23",
        "-movflags","+faststart","-r","25",str(output),
    ]
    subprocess.run(command,check=True,timeout=160)
    return output


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--post-id",default="")
    p.add_argument("--output",default="")
    args=p.parse_args()
    from post_store import load_post
    post,_=load_post(args.post_id)
    path=Path(args.output) if args.output else ROOT/"generated"/f"{post['id']}-motion.mp4"
    result=render_teaser(post,path)
    print("MOTION TEASER: "+(str(result) if result else "No source visuals; not generated."))


if __name__=="__main__":
    main()
