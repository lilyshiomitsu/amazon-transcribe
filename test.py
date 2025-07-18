import asyncio
import sounddevice as sd
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

client = TranscribeStreamingClient(region="us-east-1")

class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            if result.alternatives:
                transcript = result.alternatives[0].transcript.strip()
                # Only print if different from last
                if transcript and transcript != self.last_transcript:
                    print(transcript)
                    self.last_transcript = transcript

async def mic_stream():
    # Open a stream to your microphone
    def callback(indata, frames, time, status):
        if status:
            print(status)
        loop.call_soon_threadsafe(q.put_nowait, bytes(indata))

    q = asyncio.Queue()
    loop = asyncio.get_running_loop()

    with sd.RawInputStream(samplerate=16000, blocksize=1024, dtype='int16',
                           channels=1, callback=callback):
        while True:
            yield await q.get()

async def main():
    stream = await client.start_stream_transcription(
        language_code="en-US",
        media_sample_rate_hz=16000,
        media_encoding="pcm"
    )

    handler = MyEventHandler(stream.output_stream)
    await asyncio.gather(mic_stream_to_input(stream.input_stream), handler.handle_events())

async def mic_stream_to_input(input_stream):
    async for chunk in mic_stream():
        await input_stream.send_audio_event(audio_chunk=chunk)
    await input_stream.end_stream()

asyncio.run(main())
