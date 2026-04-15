import os
import pretty_midi
import json

def test_preview_mashup(midi_path):
    print(f"Testing {midi_path}...")
    pm = pretty_midi.PrettyMIDI(midi_path)
    
    all_notes = []
    for instrument in pm.instruments:
        if not instrument.is_drum:
            for note in instrument.notes:
                all_notes.append({
                    'pitch': note.pitch,
                    'start': note.start,
                    'end': note.end,
                    'velocity': note.velocity
                })
    
    if not all_notes:
        print("No notes found!")
        return
        
    all_notes.sort(key=lambda x: x['start'])
    first_note_start = all_notes[0]['start']
    
    notes_json = []
    for note in all_notes:
        if note['start'] < first_note_start + 30.0:
            end = min(note['end'], first_note_start + 30.0)
            notes_json.append({
                'pitch': int(note['pitch']),
                'start': note['start'] - first_note_start,
                'end': end - first_note_start,
                'velocity': int(note['velocity'])
            })
            
    print(f"Extracted {len(notes_json)} notes.")
    if notes_json:
        print(f"First note: {notes_json[0]}")
    return notes_json

if __name__ == "__main__":
    midi_dir = 'data/generated'
    files = [f for f in os.listdir(midi_dir) if f.startswith('mashup_') and f.endswith('.mid')]
    if files:
        test_preview_mashup(os.path.join(midi_dir, files[-1]))
    else:
        print("No mashup files found!")
