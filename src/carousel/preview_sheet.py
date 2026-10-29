"""Reviewable overview of all PDF pages, saved next to preview artifact."""
from __future__ import annotations
import argparse
from pathlib import Path

def build_contact_sheet(path: Path, output: Path) -> Path:
    import fitz
    from PIL import Image, ImageDraw, ImageFont
    doc=fitz.open(str(path))
    if not len(doc):raise ValueError("Empty PDF preview.")
    col_width=420
    gap=30
    columns=3 if len(doc)>3 else len(doc)
    rows=(len(doc)+columns-1)//columns
    tile_h=560
    sheet=Image.new("RGB",(columns*col_width+(columns+1)*gap,rows*tile_h+(rows+1)*gap),(232,235,237))
    draw=ImageDraw.Draw(sheet)
    for n,page in enumerate(doc):
        pix=page.get_pixmap(matrix=fitz.Matrix(.62,.62),alpha=False)
        image=Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
        image.thumbnail((col_width,525),Image.Resampling.LANCZOS)
        x=gap+(n%columns)*(col_width+gap)+(col_width-image.width)//2
        y=gap+(n//columns)*(tile_h+gap)
        sheet.paste(image,(x,y))
        draw.text((x+8,y+image.height+9),f"PAGE {n+1:02d}",fill=(34,50,63))
    output.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(output,optimize=True)
    doc.close()
    return output

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--output",default="generated/carousel-overview.png")
    args=parser.parse_args()
    print("OVERVIEW:",build_contact_sheet(Path(args.pdf),Path(args.output)))
if __name__=="__main__":main()
