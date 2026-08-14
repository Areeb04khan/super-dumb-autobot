# -*- coding: utf-8 -*-
"""
Super Dumb Heroes Bot v2.0 (Multi-Tier AI, Image & TTS Failover Engine)
- Text AI Chain: OpenRouter -> Groq -> NVIDIA NIM
- TTS Engine: Edge-TTS
- Image AI Chain: Hugging Face (FLUX) <-> Pollinations AI (Flux)
- Video Compositor: Magic Hour API / MoviePy Dynamic Motion
- Instagram Publisher: Meta Graph API (Reels)
"""
BOT_VERSION = "v1.0"

import os
import sys
import time
import json
import random
import requests
import asyncio
from datetime import datetime
from openai import OpenAI
from PIL import Image

sys.stdout.reconfigure(line_buffering=True)

# ============================================================
# CONFIGURATION & ENVIRONMENT
# ============================================================
OPENROUTER_API_KEY     = os.environ.get("OPENROUTER_API_KEY", "")
GROQ_API_KEY           = os.environ.get("GROQ_API_KEY", "")
NVIDIA_API_KEY         = os.environ.get("NVIDIA_API_KEY", "")
HF_TOKEN               = os.environ.get("HF_TOKEN", "")
POLLINATIONS_API_KEY   = os.environ.get("POLLINATIONS_API_KEY", "")
MAGIC_HOUR_API_KEY     = os.environ.get("MAGIC_HOUR_API_KEY", "")
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_USER_ID      = os.environ.get("INSTAGRAM_USER_ID", "")

IG_HANDLE = "@Super_dumb_heroes"

REQUIRED_ENV_VARS = ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_USER_ID"]

def validate_environment():
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        print(f"❌ FATAL: Missing required secret(s): {', '.join(missing)}")
        sys.exit(1)
    if not any([OPENROUTER_API_KEY, GROQ_API_KEY, NVIDIA_API_KEY]):
        print("❌ FATAL: At least one Text AI API key (OpenRouter, Groq, or NVIDIA) must be provided!")
        sys.exit(1)
    if not any([HF_TOKEN, POLLINATIONS_API_KEY]):
        print("❌ FATAL: At least one Image API key (HF_TOKEN or POLLINATIONS_API_KEY) must be provided!")
        sys.exit(1)

# ============================================================
# TIER 1: MULTI-TIER TEXT AI (Failover Chain)
# ============================================================
def generate_content() -> dict:
    print(f"🧠 Querying Text AI Chain for {IG_HANDLE}...")

    characters = ["Spider-Man", "Batman", "Thanos", "Superman", "The Flash", "Iron Man", "Deadpool", "Thor", "Wolverine"]
    chosen_hero = random.choice(characters)

    prompt = f"""Act as a sarcastic pop-culture comedy writer.
Write a short, punchy, 3-sentence script where {chosen_hero} is complaining about a mundane, relatable, everyday problem made absurd by their superhero status or lifestyle.
Examples: Spider-Man doing laundry at a public laundromat, Batman stuck in gridlock Gotham traffic in the Batmobile, Thanos having a dispute with HR over half-staffing.

Return strictly valid JSON:
{{
  "hero": "{chosen_hero}",
  "hook": "The punchy opening hook...",
  "script": "The rest of the comedic complaint...",
  "image_prompt": "Cinematic vertical 9:16 portrait photo of {chosen_hero} looking annoyed in a mundane everyday situation, highly detailed, dramatic lighting, photorealistic, 8k",
  "caption": "Even saving the multiverse doesn't exempt you from daily nonsense. 🦸‍♂️☕\\n\\nFollow @Super_dumb_heroes for daily superhero struggles."
}}"""

    fallbacks = [
        {
            "name": "OpenRouter",
            "api_key": OPENROUTER_API_KEY,
            "base_url": "https://openrouter.ai/api/v1",
            "model": "openrouter/free"
        },
        {
            "name": "Groq",
            "api_key": GROQ_API_KEY,
            "base_url": "https://api.groq.com/openai/v1",
            "model": "llama-3.3-70b-versatile"
        },
        {
            "name": "NVIDIA NIM",
            "api_key": NVIDIA_API_KEY,
            "base_url": "https://integrate.api.nvidia.com/v1",
            "model": "meta/llama-3.1-70b-instruct"
        }
    ]

    for index, provider in enumerate(fallbacks, start=1):
        if not provider["api_key"]:
            continue
        try:
            print(f"🔄 [{index}/3] Trying {provider['name']} for script generation...")
            client = OpenAI(base_url=provider["base_url"], api_key=provider["api_key"])
            response = client.chat.completions.create(
                model=provider["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            raw = response.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
            print(f"✅ Generated script for {data.get('hero', chosen_hero)} via {provider['name']}!")
            return data
        except Exception as err:
            print(f"⚠️ {provider['name']} failed: {err}")

    print("❌ FATAL: All Text AI providers failed.")
    sys.exit(1)

# ============================================================
# TIER 2: VOICE GENERATION (Edge TTS)
# ============================================================
def generate_tts(data: dict) -> str:
    print("🎙️ Generating narration via Edge-TTS...")
    full_text = f"{data['hook']} ... {data['script']}"
    out_path = f"output/tts_{int(time.time())}.mp3"

    import edge_tts
    async def _speak():
        # High clarity, sarcastic/dramatic tone
        communicate = edge_tts.Communicate(full_text, "en-US-ChristopherNeural", rate="+3%", pitch="-2Hz")
        await communicate.save(out_path)

    try:
        asyncio.run(_speak())
        print("✅ Edge-TTS Audio generated successfully!")
        return out_path
    except Exception as e:
        print(f"❌ FATAL: Edge-TTS failed: {e}")
        sys.exit(1)

# ============================================================
# TIER 3: MULTI-TIER IMAGE GENERATION (Hugging Face <-> Pollinations)
# ============================================================
def generate_image_hf(prompt: str, out_path: str) -> bool:
    if not HF_TOKEN:
        return False
    try:
        print("🎨 [1/2] Attempting Image Generation via Hugging Face (FLUX.1-schnell)...")
        from huggingface_hub import InferenceClient
        client = InferenceClient(token=HF_TOKEN)
        image = client.text_to_image(
            prompt,
            model="black-forest-labs/FLUX.1-schnell"
        )
        # Ensure 1080x1920 (9:16 vertical)
        image = image.resize((1080, 1920), Image.Resampling.LANCZOS)
        image.save(out_path)
        print("✅ Base image successfully generated via Hugging Face!")
        return True
    except Exception as e:
        print(f"⚠️ Hugging Face image generation failed: {e}")
        return False

def generate_image_pollinations(prompt: str, out_path: str) -> bool:
    try:
        print("🎨 [2/2] Attempting Image Generation via Pollinations AI...")
        url = f"https://gen.pollinations.ai/image/{requests.utils.quote(prompt)}?model=flux&width=1080&height=1920&nologo=true"
        headers = {}
        if POLLINATIONS_API_KEY:
            headers["Authorization"] = f"Bearer {POLLINATIONS_API_KEY}"

        res = requests.get(url, headers=headers, timeout=45)
        if res.status_code == 200 and len(res.content) > 5000:
            with open(out_path, "wb") as f:
                f.write(res.content)
            print("✅ Base image successfully generated via Pollinations AI!")
            return True
        else:
            print(f"⚠️ Pollinations returned status code {res.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ Pollinations AI failed: {e}")
        return False

def generate_base_image(prompt: str) -> str:
    out_path = f"output/base_img_{int(time.time())}.png"

    # Try Hugging Face first
    if generate_image_hf(prompt, out_path):
        return out_path

    # Fallback to Pollinations AI
    if generate_image_pollinations(prompt, out_path):
        return out_path

    print("❌ FATAL: All Image Generation providers failed.")
    sys.exit(1)

# ============================================================
# TIER 4: VIDEO COMPOSITOR (Magic Hour / MoviePy Dynamic Motion)
# ============================================================
def create_reel_video(image_path: str, audio_path: str, data: dict) -> str:
    print("🎬 Compositing 1080x1920 Reel Video with MoviePy...")
    try:
        from moviepy.editor import ImageClip, AudioFileClip
        import numpy as np

        audio_clip = AudioFileClip(audio_path)
        duration = min(audio_clip.duration + 1.2, 30.0)

        # Smooth dynamic zoom effect (Ken Burns motion)
        def zoom_transform(t):
            return 1.0 + 0.035 * t

        bg_clip = ImageClip(image_path).resize((1080, 1920))
        bg_clip = bg_clip.resize(zoom_transform).set_position('center').set_duration(duration)

        # Apply slight contrast grading
        bg_clip = bg_clip.fl_image(lambda frame: (frame * 0.95).astype(np.uint8))

        final_video = bg_clip.set_audio(audio_clip)
        reel_path = f"output/reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

        final_video.write_videofile(
            reel_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            verbose=False,
            logger=None
        )
        print("✅ Reel composited successfully!")
        return reel_path
    except Exception as e:
        print(f"❌ Video render failure: {e}")
        return None

# ============================================================
# TIER 5: INSTAGRAM PUBLISHER (Meta Graph API)
# ============================================================
def upload_public_media(path: str) -> str:
    print("🌐 Uploading media to temporary hosting for Instagram ingestion...")
    with open(path, "rb") as f:
        res = requests.post("https://tempfile.org/api/upload/local", files={"files": (os.path.basename(path), f)}).json()
        if res.get("success"):
            media_url = f"{res['files'][0]['url'].rstrip('/')}/download"
            print("✅ Media hosted successfully.")
            return media_url
    raise RuntimeError("Public media upload failed.")

def post_to_instagram(media_path: str, caption: str) -> bool:
    print(f"📱 Publishing Reel to {IG_HANDLE}...")
    try:
        media_url = upload_public_media(media_path)
        payload = {
            "access_token": INSTAGRAM_ACCESS_TOKEN,
            "caption": caption,
            "media_type": "REELS",
            "video_url": media_url
        }

        # Step 1: Create Video Container
        c_res = requests.post(f"https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media", data=payload).json()
        container_id = c_res.get("id")
        if not container_id:
            print(f"❌ Container creation failed: {c_res}")
            return False

        # Step 2: Poll Container Processing Status
        print("⏳ Waiting for Instagram video processing...")
        for attempt in range(1, 25):
            time.sleep(10)
            status = requests.get(f"https://graph.instagram.com/v21.0/{container_id}?fields=status_code&access_token={INSTAGRAM_ACCESS_TOKEN}").json()
            code = status.get("status_code")
            if code == "FINISHED":
                print("✅ Video processing finished by Meta.")
                break
            elif code == "ERROR":
                print(f"❌ Meta video processing failed: {status}")
                return False

        # Step 3: Publish Video Container
        p_res = requests.post(f"https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media_publish", data={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN}).json()
        return "id" in p_res
    except Exception as e:
        print(f"❌ Instagram API Failure: {e}")
        return False

# ============================================================
# MAIN WORKFLOW
# ============================================================
def run():
    print ( f"📦 Bot version: {BOT_VERSION}")
    validate_environment()
    os.makedirs("output", exist_ok=True)
    print(f"\n🚀 STARTING WORKFLOW: [PARODY REEL] for {IG_HANDLE}\n")

    # 1. Script Generation (OpenRouter -> Groq -> NVIDIA NIM)
    data = generate_content()
    caption = f"{data.get('caption', '')}\n\n#superheroes #marvel #dc #marvelmemes #dcmemes #superhero #relatable #humor #parody"

    # 2. Audio Synthesis (Edge-TTS)
    audio_path = generate_tts(data)

    # 3. Visual Creation (HF FLUX <-> Pollinations AI)
    base_image_path = generate_base_image(data["image_prompt"])

    # 4. Reel Video Compositing
    reel_path = create_reel_video(base_image_path, audio_path, data)

    # 5. Publishing to Instagram
    if reel_path:
        success = post_to_instagram(reel_path, caption)
        if success:
            print("\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
        else:
            sys.exit(1)
    else:
        sys.exit(1)

if __name__ == "__main__":
    run()
    
