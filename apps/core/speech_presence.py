"""Small deterministic PCM guard, not a VAD model or production speech guarantee."""
import io, math, struct, wave
from .storage import SafeError

def speech_presence(data):
    try:
        with wave.open(io.BytesIO(data)) as w:
            if w.getnchannels()!=1 or w.getsampwidth()!=2:raise ValueError()
            rate=w.getframerate();raw=w.readframes(w.getnframes())
        samples=struct.unpack('<'+'h'*(len(raw)//2),raw)
        if not samples:raise ValueError()
        rms=math.sqrt(sum(v*v for v in samples)/len(samples))/32768
        if rms<.0003:return {'state':'NO_SPEECH','reason':'NEAR_SILENCE','rms':round(rms,6),'version':'PCM_SIGNAL_V1'}
        frames=[samples[i:i+rate//50] for i in range(0,len(samples),rate//50)]
        energies=[math.sqrt(sum(x*x for x in f)/len(f))/32768 for f in frames if f]
        active=[f for f,e in zip(frames,energies) if e>max(.0004,rms*.15)]
        crossings=sum(sum((a>=0)!=(b>=0) for a,b in zip(f,f[1:])) for f in active)/max(1,sum(len(f)-1 for f in active))
        variation=(max(energies)-min(energies))/max(rms,.00001)
        # Seeded white noise has high crossing rate and flat energy; speech-like modulation
        # is only a review aid. Tones/complex noise can remain uncertain or false positives.
        if crossings>.32 and variation<.8:state,reason='NO_SPEECH','FLAT_BROADBAND_NOISE'
        elif rms<.003 or len(active)<8 or crossings>.28 or variation<.25:state,reason='UNCERTAIN','LOW_OR_AMBIGUOUS_SIGNAL'
        else:state,reason='SPEECH_DETECTED','MODULATED_SIGNAL'
        return {'state':state,'reason':reason,'rms':round(rms,6),'crossing_rate':round(crossings,4),'energy_variation':round(variation,4),'version':'PCM_SIGNAL_V1'}
    except (wave.Error,ValueError,EOFError,struct.error):raise SafeError('AUDIO_MALFORMED') from None
