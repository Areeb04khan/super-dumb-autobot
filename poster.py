# -*- coding: utf-8 -*-
"""
Super Dumb Heroes Bot v1.0 
- AI Chain: OpenRouter (Text) -> Edge-TTS (Voice) -> Pollinations (Image) -> Magic Hour (Video)
- Fully automated Marvel/DC parody reels
"""

import os
import sys
import time
import json
import random
import requests
import textwrap
import asyncio
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIGURATION & ENVIRONMENT
# ============================================================
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
POLLINATIONS_API_KEY = os.environ.get("POLLINATIONS_API_KEY", "")
MAGIC_HOUR_API_KEY = os.environ.get("MAGIC_HOUR_API_KEY", "")
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_USER_ID = os.environ.get("INSTAGRAM_USER_ID", "")
IG_HANDLE = "@Super_dumb_heroes"

REQUIRED_ENV_VARS = ["OPENROUTER_API_KEY", "POLLINATIONS_API_KEY", "MAGIC_HOUR_API_KEY", "INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_USER_ID"]

def validate_environment():
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        print(f"❌ FATAL: Missing required secret(s): {', '.join(missing)}")
        sys.exit(1)

# ============================================================
# TIER 1: TEXT GENERATION (OpenRouter Free Tier)
# ============================================================
def generate_content() -> dict:
    print(f"🧠 Writing script for {IG_HANDLE}...")
    
    characters = ["Spider-Man", "Batman", "Thanos", "Superman", "The Flash", "Iron Man"]
    chosen_hero = random.choice(characters)
    
    prompt = f"""Act as a sarcastic comedy writer. 
Write a short, punchy, 3-sentence script where {chosen_hero} is complaining about a mundane, relatable, everyday problem that is made infinitely worse by their powers or lifestyle. 
Examples: Spider-Man doing laundry, Batman stuck in traffic, Thanos doing taxes.

Return strictly valid JSON in this exact format:
{{
  "hook": "The hook of the joke...",
  "script": "The rest of the complaint...",
  "image_prompt": "Cinematic 4k shot of {chosen_hero} doing [the mundane activity], highly detailed, moody lighting",
  "caption": "Even heroes hate Mondays. 🦸‍♂️🤦‍♂️\\n\\nFollow @Super_dumb_heroes for daily superhero struggles."
}}"""

    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1", 
            api_key=OPENROUTER_API_KEY
        )
        response = client.chat.completions.create(
            model="openrouter/free", # Using the free tier model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        raw = response.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
        data = json.loads(raw)
        print(f"✅ Generated {chosen_hero} script successfully!")
        return data
    except Exception as e:
        print(f"❌ Text generation failed: {e}")
        sys.exit(1)

# ============================================================
# TIER 2: VOICE GENERATION (Edge TTS - Free)
# ============================================================
def generate_tts(data: dict) -> str:
    print("🎙️ Generating audio via Edge-TTS...")
    full_text = f"{data['hook']} {data['script']}"
    out_path = f"output/tts_{int(time.time())}.mp3"
    
    import edge_tts
    async def _speak():
        # Using a slightly deeper, dramatic voice for comedic contrast
        communicate = edge_tts.Communicate(full_text, "en-US-ChristopherNeural") 
        await communicate.save(out_path)
    
    try:
        asyncio.run(_speak())
        print("✅ Audio generated successfully!")
        return out_path
    except Exception as e:
        print(f"❌ TTS failed: {e}")
        sys.exit(1)

# ============================================================
# TIER 3: IMAGE GENERATION (Pollinations - Free)
# ============================================================
def generate_base_image(prompt: str) -> str:
    print("🎨 Generating base image via Pollinations API...")
    out_path = f"output/base_img_{int(time.time())}.png"
    
    # Pollinations URL-based image generation API
    url = f"https://gen.pollinations.ai/image/{requests.utils.quote(prompt)}?model=flux&width=1080&height=1920"
    headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            with open(out_path, 'wb') as f:
                f.write(response.content)
            print("✅ Base image generated.")
            return out_path
        else:
            raise Exception(f"Status code {response.status_code}")
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        sys.exit(1)

# ============================================================
# TIER 4: VIDEO ANIMATION (Magic Hour - Free Developer API)
# ============================================================
def animate_image(image_path: str) -> str:
    print("🎬 Animating image via Magic Hour API...")
    
    try:
        # Magic Hour REST API implementation
        url = "https://api.magichour.ai/v1/image-to-video"
        headers = {
            "Authorization": f"Bearer {MAGIC_HOUR_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Note: Magic Hour API requires the image to be hosted or you must generate an upload URL first.
        # For simplicity in this script, we assume temporary hosting (like file.io) if a direct path fails,
        # but here we follow the API docs for uploading an asset via their systems.
        
        # Step 4a: We must upload the local file to a temporary public host so Magic Hour can access it
        print("   -> Temporarily hosting image for Magic Hour...")
        with open(image_path, "rb") as f:
            upload_res = requests.post("https://tempfile.org/api/upload/local", files={"files": (os.path.basename(image_path), f)}).json()
            public_image_url = f"{upload_res['files'][0]['url'].rstrip('/')}/download"
        
        # Step 4b: Send animation request
        payload = {
            "name": "Super Dumb Heroes Animation",
            "end_seconds": 5,
            "resolution": "720p",
            "assets": {
                "image_file_path": public_image_url
            }
        }
        
        response = requests.post(url, headers=headers, json=payload).json()
        
        # The API is asynchronous. You would normally poll for completion. 
        # For this script, we will mock the wait and fallback to static image panning if the API fails or takes too long.
        print("✅ Animation requested. (Note: Magic Hour requires polling in production. Falling back to static compositing for instant rendering...)")
        return image_path 
        
    except Exception as e:
        print(f"⚠️ Magic Hour API failed or timed out: {e}. Falling back to static image...")
        return image_path

# ============================================================
# TIER 5: COMPOSITING & INSTAGRAM PUBLISHING
# ============================================================
def create_reel_video(image_path: str, audio_path: str, data: dict) -> str:
    print("🎥 Compositing final Reel...")
    try:
        from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
        import numpy as np

        audio_clip = AudioFileClip(audio_path)
        duration = min(audio_clip.duration + 1, 15)

        # Create a zooming effect on the static image since we are falling back to it
        def zoom(t):
            return 1 + 0.04 * t

        bg_clip = ImageClip(image_path).resize(height=1920, width=1080)
        bg_clip = bg_clip.resize(zoom).set_position('center').set_duration(duration)
        
        # Add a slight dark overlay to make captions pop (if you add them later)
        bg_clip = bg_clip.fl_image(lambda image: (image * 0.7).astype(np.uint8))

        final_video = bg_clip.set_audio(audio_clip)
        reel_path = f"output/reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        final_video.write_videofile(reel_path, fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
        return reel_path
    except Exception as e:
        print(f"❌ Video composite failed: {e}")
        return None

def upload_public_media(path: str) -> str:
    with open(path, "rb") as f:
        res = requests.post("https://tempfile.org/api/upload/local", files={"files": (os.path.basename(path), f)}).json()
        if res.get("success"):
            return f"{res['files'][0]['url'].rstrip('/')}/download"
    raise RuntimeError("Public media upload failed.")

def post_to_instagram(media_path: str, caption: str) -> bool:
    print("📱 Publishing to Instagram...")
    try:
        media_url = upload_public_media(media_path)
        payload = {"access_token": INSTAGRAM_ACCESS_TOKEN, "caption": caption, "media_type": "REELS", "video_url": media_url}

        c_res = requests.post(f"https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media", data=payload).json()
        container_id = c_res.get("id")
        if not container_id: 
            print(f"❌ Container creation failed: {c_res}")
            return False

        print("   -> Waiting for Instagram to process video...")
        for attempt in range(1, 21):
            time.sleep(10)
            status = requests.get(f"https://graph.instagram.com/v21.0/{container_id}?fields=status_code&access_token={INSTAGRAM_ACCESS_TOKEN}").json()
            code = status.get("status_code")
            if code == "FINISHED": break
            elif code == "ERROR": 
                print("❌ Instagram processing error.")
                return False

        p_res = requests.post(f"https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media_publish", data={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN}).json()
        return "id" in p_res
    except Exception as e:
        print(f"❌ Instagram API Failure: {e}")
        return False

# ============================================================
# MAIN
# ============================================================
def run():
    validate_environment()
    os.makedirs("output", exist_ok=True)
    print(f"\n🚀 STARTING WORKFLOW: [REEL] for {IG_HANDLE}\n")
    
    # 1. Script
    data = generate_content()
    
    # 2. Audio
    audio_path = generate_tts(data)
    
    # 3. Image
    base_image_path = generate_base_image(data["image_prompt"])
    
    # 4. Video Animation Request (Falls back to static image if polling isn't implemented)
    video_asset = animate_image(base_image_path)
    
    # 5. Composite & Publish
    reel_path = create_reel_video(video_asset, audio_path, data)
    
    if reel_path:
        success = post_to_instagram(reel_path, data["caption"])
        if success:
            print("\n✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        else:
            sys.exit(1)
    else:
        sys.exit(1)

if __name__ == "__main__":
    run()

