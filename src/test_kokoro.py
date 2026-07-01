from kokoro import KPipeline
import soundfile as sf

pipeline = KPipeline(lang_code="a")

text = """
Halo Alfred. Saya JARVIS. Mulai sekarang saya akan berbicara dengan suara yang lebih natural.
Visual Studio Code sudah siap. Sistem utama berjalan normal.
"""

voices = [
    "am_adam",
    "bm_george",
    "af_heart"
]

for voice in voices:
    generator = pipeline(
        text,
        voice=voice,
        speed=0.95
    )

    for index, (_, _, audio) in enumerate(generator):
        filename = f"kokoro_test_{voice}.wav"
        sf.write(filename, audio, 24000)
        print(f"Created: {filename}")
        break