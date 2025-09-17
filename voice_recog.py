from resemblyzer import VoiceEncoder
import numpy as np
import sounddevice as sd

encoder = VoiceEncoder()
stored_voices = {}  # name -> embedding

def record_voice(seconds=5):
    """Record audio from mic."""
    print(f"Recording {seconds} seconds...")
    wav = sd.rec(int(seconds * 16000), samplerate=16000, channels=1, dtype="float32")
    sd.wait()
    return wav.flatten()

def store_voice(name, seconds=5):
    """Store a speaker's voice by name."""
    wav = record_voice(seconds)
    embedding = encoder.embed_utterance(wav)
    stored_voices[name] = embedding
    print(f"✅ Stored voice for {name}")

def recognize_speaker(seconds=5):
    """Recognize which stored speaker is speaking."""
    if not stored_voices:
        print("⚠️ No voices stored yet!")
        return None

    wav = record_voice(seconds)
    embedding = encoder.embed_utterance(wav)
    scores = {name: float(np.dot(embedding, emb)) for name, emb in stored_voices.items()}
    speaker = max(scores, key=scores.get)
    print(f"🎤 This sounds like {speaker} (scores: {scores})")
    return speaker
