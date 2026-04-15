import pretty_midi
import numpy as np

def gan_to_midi(gan_output, filename="generated.mid"):
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)

    # Normalize output
    values = np.array(gan_output)
    values = (values - values.min()) / (values.max() - values.min() + 1e-8)

    time = 0

    for v in values[:50]:  # use first 50 values
        pitch = int(60 + v * 24)  # MIDI range
        duration = 0.2 + v * 0.5

        note = pretty_midi.Note(
            velocity=80,
            pitch=pitch,
            start=time,
            end=time + duration
        )

        instrument.notes.append(note)
        time += duration

    midi.instruments.append(instrument)
    midi.write(filename)

    return filename