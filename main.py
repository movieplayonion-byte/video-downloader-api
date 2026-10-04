from fastapi import FastAPI, HTTPException
import yt_dlp

app = FastAPI(title="Media Stream Resolver API")

@app.get("/")
def home():
    return {"status": "running", "engine": "yt-dlp-mobile-client"}

@app.get("/extract")
def extract_stream(url: str, mode: str = "video", quality: str = "720"):
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL parameter")

    # YouTube Web bot-check bypass karne ke liye Mobile clients use karna
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'mweb'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'http_headers': {
            'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 14) gzip'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])

            if mode == "audio":
                audio_formats = [
                    f for f in formats 
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('url')
                ]
                if audio_formats:
                    return {"url": audio_formats[-1]['url'], "title": info.get('title')}
            else:
                # Progressive formats (combined video + audio MP4)
                mp4_formats = [
                    f for f in formats 
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4' and f.get('url')
                ]
                
                for f in mp4_formats:
                    h = str(f.get('height', ''))
                    if quality in h:
                        return {"url": f['url'], "title": info.get('title'), "quality": h}

                if mp4_formats:
                    best = mp4_formats[-1]
                    return {"url": best['url'], "title": info.get('title'), "quality": str(best.get('height'))}

            if formats and 'url' in formats[-1]:
                return {"url": formats[-1]['url'], "title": info.get('title')}

            raise HTTPException(status_code=404, detail="No suitable stream found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
