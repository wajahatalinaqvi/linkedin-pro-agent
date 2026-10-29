"""Original kinetic, source-led LinkedIn teaser (silent, 1080x1350).
Screenshots are authentic and attributed; scene graphics are original.
"""
from __future__ import annotations
import argparse, math, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from source_visuals import ensure_source_images

ROOT=Path(__file__).resolve().parents[1]
W,H=1080,1350
FPS=20
DURATION=12
NAVY=(6,13,43)
BLUE=(30,75,245)
PALE=(248,247,240)
CYAN=(91,217,237)

def font(size,bold=False):
    variants=(["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]
              if bold else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"])
    for path in variants:
        if Path(path).exists():
            return ImageFont.truetype(path,size)
    return ImageFont.load_default()

def ease(t):
    t=max(0,min(1,t))
    return 1-(1-t)**3

def wrap(draw,text,f,maxwidth,limit=4):
    lines=[]; line=""
    for word in str(text).split():
        candidate=(line+" "+word).strip()
        if line and draw.textbbox((0,0),candidate,font=f)[2]>maxwidth:
            lines.append(line);line=word
        else: line=candidate
    if line: lines.append(line)
    return lines[:limit]

def draw_lines(draw,lines,x,y,f,color,leading,progress=1):
    for i,line in enumerate(lines):
        alpha=ease((progress*1.6-i*.17))
        if alpha<=0:continue
        shift=int((1-alpha)*48)
        draw.text((x,y+i*leading+shift),line,font=f,fill=color)

def network(draw,t,color,origin=(860,420)):
    ox,oy=origin
    for i in range(26):
        angle=i*2.399+math.sin(t*.8)*.13
        radius=165+(i%6)*45+math.sin(t*1.4+i)*13
        ex=int(ox+math.cos(angle)*radius)
        ey=int(oy+math.sin(angle)*radius)
        draw.line((ox,oy,ex,ey),fill=color,width=2 if i%4 else 4)
        rr=3+(i%3);draw.ellipse((ex-rr,ey-rr,ex+rr,ey+rr),fill=color)
    draw.ellipse((ox-14,oy-14,ox+14,oy+14),fill=CYAN)

def screenshot(img,area,scale,dx,dy):
    x,y,w,h=area
    actual=(int(w*scale),int(h*scale))
    zoomed=ImageOps.fit(img,actual,method=Image.Resampling.LANCZOS,centering=(.5,.3))
    crop=Image.new("RGB",(w,h),NAVY)
    crop.paste(zoomed,(int((w-actual[0])/2+dx),int((h-actual[1])/2+dy)))
    return crop

def render_frame(shots,post,t):
    scene=min(3,int(t//3))
    local=(t-scene*3)/3
    slide=(post.get("document") or {}).get("carousel",{}).get("slides",[])
    title=str(slide[0].get("title") or post.get("topic") or "Shopify updates")
    second=str(slide[1].get("title") or "What changed for developers")
    third=str(slide[3].get("title") or "What developers should know")
    closer=str(slide[-1].get("title") or "What would you build differently?")
    bg=NAVY if scene in (0,2,3) else PALE
    im=Image.new("RGB",(W,H),bg);d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,13),fill=CYAN if scene%2==0 else BLUE)
    d.text((65,45),"SHOPIFY EDITIONS  /  DEVELOPER NOTES",font=font(23,True),
           fill=CYAN if bg==NAVY else BLUE)
    d.text((65,1262),"ORIGINAL SCREENSHOTS · SHOPIFY.COM",font=font(17,True),
           fill=(165,199,215) if bg==NAVY else (53,79,101))
    d.text((913,1260),f"{scene+1:02d} / 04",font=font(21,True),
           fill=CYAN if bg==NAVY else BLUE)
    if scene==0:
        network(d,t,(38,77,137),(875,660))
        f=font(74,True)
        lines=wrap(d,title,f,900,4)
        draw_lines(d,lines,65,365,f,(255,255,255),91,local*2.2)
        accent=ease((local-.23)*2)
        d.rectangle((65,875,65+int(750*accent),888),fill=(255,107,72))
        if local>.42:
            d.text((68,927),"THE DEVELOPER IMPACT",font=font(31,True),fill=CYAN)
    elif scene==1:
        f=font(60,True);draw_lines(d,wrap(d,second,f,940,3),65,165,f,NAVY,78,local*2)
        p=ease(local*2.1)
        x=65+int((1-p)*260);y=460
        card=screenshot(shots[0],(0,0,930,600),1.045+local*.065,-local*34,0)
        im.paste(card,(x,y))
        d=ImageDraw.Draw(im)
        d.rectangle((x,y,x+930,y+600),outline=BLUE,width=7)
        d.rectangle((65,1111,1015,1120),fill=BLUE)
        d.text((65,1140),"SOURCE INTERFACE  /  REAL SCREENSHOT",font=font(22,True),fill=BLUE)
    elif scene==2:
        network(d,t,(30,82,164),(550,680))
        f=font(57,True);draw_lines(d,wrap(d,third,f,935,3),65,130,f,(255,255,255),70,local*2)
        p=ease(local*1.8)
        for i,shot in enumerate(shots[:3]):
            w,h=710,390
            yy=395+i*205
            xx=210+(-1 if i%2 else 1)*int((1-p)*500)
            pic=screenshot(shot,(0,0,w,h),1.04+local*.05,(-1 if i%2 else 1)*local*17,0)
            im.paste(pic,(xx,yy))
            d=ImageDraw.Draw(im)
            d.rectangle((xx,yy,xx+w,yy+h),outline=CYAN if i==1 else (102,136,235),width=5)
    else:
        network(d,t,(29,67,117),(840,290))
        f=font(73,True);draw_lines(d,wrap(d,closer,f,910,5),65,360,f,(255,255,255),93,local*2)
        p=ease((local-.18)*2)
        d.rectangle((65,985,65+int(940*p),1004),fill=CYAN)
        if local>.4:
            d.text((65,1055),"WHAT'S YOUR TAKE?",font=font(40,True),fill=CYAN)
    # Real scene transition: 0.25 sec masked directional wipe to next color.
    remaining=3-(t%3)
    if scene<3 and remaining<.24:
        amount=ease(1-remaining/.24)
        w=int(W*amount)
        d=ImageDraw.Draw(im)
        transition=NAVY if scene==1 else PALE if scene==0 else NAVY
        d.rectangle((0,0,w,H),fill=transition)
    return im

def render_teaser(post,output):
    carousel=(post.get("document") or {}).get("carousel") or {}
    if not (carousel.get("source_visuals") or {}).get("enabled"):return None
    paths=ensure_source_images(carousel)
    if len(paths)<3:return None
    shots=[Image.open(p).convert("RGB") for p in paths[:3]]
    import imageio_ffmpeg
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    command=[ffmpeg,"-hide_banner","-loglevel","error","-y",
             "-f","rawvideo","-vcodec","rawvideo","-pix_fmt","rgb24",
             "-s",f"{W}x{H}","-r",str(FPS),"-i","-",
             "-c:v","libx264","-preset","ultrafast","-crf","27",
             "-pix_fmt","yuv420p","-movflags","+faststart",str(output)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for index in range(FPS*DURATION):
            frame=render_frame(shots,post,index/FPS)
            process.stdin.write(frame.tobytes())
        process.stdin.close()
        stderr=process.stderr.read().decode(errors="replace")
        if process.wait(timeout=90)!=0:raise RuntimeError("FFmpeg teaser error: "+stderr[-900:])
    except Exception:
        process.kill();process.wait()
        raise
    finally:
        for shot in shots:shot.close()
    return output

def main():
    p=argparse.ArgumentParser();p.add_argument("--post-id",default="");p.add_argument("--output",default="")
    args=p.parse_args()
    from post_store import load_post
    post,_=load_post(args.post_id)
    output=Path(args.output) if args.output else ROOT/"generated"/f"{post['id']}-motion.mp4"
    result=render_teaser(post,output)
    print("KINETIC MOTION TEASER: "+(str(result) if result else "Source visuals unavailable"))
if __name__=="__main__":main()
