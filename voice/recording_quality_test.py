import sounddevice as sd
import numpy as np
import wave
from pathlib import Path

DEVICE = 1
SAMPLE_RATE = 44100
DURATION = 5

OUTPUT = Path(__file__).parent / "test_mic.wav"

print("Recording for 5 seconds...")
print("Speak normally.")

audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="int16",
    device=DEVICE
)

sd.wait()

audio = audio.flatten()

with wave.open(str(OUTPUT), "wb") as file:

    file.setnchannels(1)
    file.setsampwidth(2)
    file.setframerate(SAMPLE_RATE)

    file.writeframes(audio.tobytes())

print("\nRecording saved:", OUTPUT)

print("Peak:", np.max(np.abs(audio.astype(np.int32))))
print("RMS:", round(np.sqrt(np.mean(audio.astype(np.float64) ** 2)), 2))

print("\nOpening recording...")

import os
os.startfile(str(OUTPUT))
