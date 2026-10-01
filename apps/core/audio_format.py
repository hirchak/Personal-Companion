"""Bounded local PCM boundary. No external codecs, filenames or acoustic profiling."""
import io
import math
import struct
import wave
from .storage import SafeError

MAX_AUDIO = 8 * 1024 * 1024
CHUNK_SIZE = 256 * 1024
MAX_DURATION = 120

class PCMConverter:
    identity = 'python-wave-pcm16-v1'
    supported = ('audio/wav',)

    def normalize(self, data, mime):
        if mime != 'audio/wav':
            raise SafeError('AUDIO_FORMAT_UNSUPPORTED')
        if not data or len(data) > MAX_AUDIO:
            raise SafeError('AUDIO_SIZE_LIMIT')
        try:
            # Exact RIFF extent; wave alone accepts certain truncated/trailing containers.
            if data[:4] != b'RIFF' or data[8:12] != b'WAVE' or len(data) < 44 or struct.unpack('<I',data[4:8])[0]+8 != len(data):
                raise ValueError()
            with wave.open(io.BytesIO(data),'rb') as w:
                rate, channels, width, frames = w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getnframes()
                if rate not in {16000, 24000, 44100, 48000} or channels != 1 or width != 2 or w.getcomptype() != 'NONE':
                    raise SafeError('AUDIO_PCM_UNSUPPORTED')
                duration = frames/rate
                raw = w.readframes(frames)
                if len(raw) != frames*2 or not .25 <= duration <= MAX_DURATION:
                    raise SafeError('AUDIO_DURATION_OR_TRUNCATION')
            values = struct.unpack('<'+'h'*frames,raw)
            rms = math.sqrt(sum(v*v for v in values)/frames)/32768
            # Engineering heuristic only, not VAD or an inference about a person.
            return data, {'duration_seconds':duration,'sample_rate':rate,'channels':channels,
                          'signal':'LOW_ENERGY' if rms < .004 else 'REVIEW_REQUIRED'}
        except (wave.Error, EOFError, struct.error, ValueError, ZeroDivisionError):
            raise SafeError('AUDIO_MALFORMED') from None
