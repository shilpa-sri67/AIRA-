import sounddevice as sd
import numpy as np
import time

MIC_DEVICE = 1
SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = 10

print("AIRA MICROPHONE TEST")
print("--------------------")

print("\nAvailable microphone:")
print(sd.query_devices(MIC_DEVICE))

print("\nSpeak normally for 10 seconds...")

audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=CHANNELS,
    dtype="int16",
    device=MIC_DEVICE
)

sd.wait()

audio = audio.flatten()

peak = np.max(np.abs(audio.astype(np.int32)))
rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))

print("\nRecording completed.")

print("Peak audio level:", peak)
print("Average audio level:", round(rms, 2))

if rms < 50:
    print("\nWARNING: Very low microphone input.")

else:
    print("\nSUCCESS: Microphone is capturing audio.")