from fastapi import FastAPI, HTTPException
import yt_dlp

app = FastAPI(title="Media Stream Resolver API")

@app.get("/")
def home():
    return {"status": "running", "engine": "yt-dlp"}

@app.get("/extract")
def extract_stream(url: str, mode: str = "video", quality: str = "720"):
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL parameter")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])

            if mode == "audio":
                # Best direct audio stream
                audio_formats = [
                    f for f in formats 
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('url')
                ]
                if audio_formats:
                    return {"url": audio_formats[-1]['url'], "title": info.get('title')}
            else:
                # Progressive formats (combined video + audio in MP4)
                mp4_formats = [
                    f for f in formats 
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4' and f.get('url')
                ]
                
                # Match quality if possible
                for f in mp4_formats:
                    h = str(f.get('height', ''))
                    if quality in h:
                        return {"url": f['url'], "title": info.get('title'), "quality": h}

                # Fallback to best progressive format
                if mp4_formats:
                    best = mp4_formats[-1]
                    return {"url": best['url'], "title": info.get('title'), "quality": str(best.get('height'))}

            # Ultimate fallback if no progressive format found
            if formats and 'url' in formats[-1]:
                return {"url": formats[-1]['url'], "title": info.get('title')}

            raise HTTPException(status_code=404, detail="No suitable stream found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
