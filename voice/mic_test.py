import sounddevice as sd
from scipy.io.wavfile import write

SAMPLE_RATE = 16000
DURATION = 5
MICROPHONE_ID = 1

print("AIRA is getting ready...")
sd.sleep(2000)

print("Speak now! Recording for 5 seconds.")

audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="int16",
    device=MICROPHONE_ID
)

sd.wait()

write("test_audio.wav", SAMPLE_RATE, audio)

print("Recording completed!")
print("Audio saved successfully!")