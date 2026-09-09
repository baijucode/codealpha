#Step 1-2: Collect MIDI data (user-supplied) and preprocess it into note/chord sequences suitable for training an LSTM.

# argparse lets us read settings (like --midi-dir) from the command line
import argparse
# glob lets us search folders for files matching a pattern, e.g. "*.mid"
import glob
# os gives us file/folder utilities (joining paths, making directories)
import os
# pickle lets us save a Python object (like a dictionary) to a file, and load it back later
import pickle

# numpy is the standard library for working with arrays of numbers
import numpy as np
# chord/note = represent musical chords and notes, converter = reads MIDI files,
# instrument = lets us split a MIDI file into its separate instrument tracks
from music21 import chord, converter, instrument, note
# tqdm just draws a nice progress bar while we loop over files
from tqdm import tqdm

def extract_notes_from_file(path):

    # this list will hold every note/chord we find, in the order they play
    tokens = []
    try:
        # ask music21 to open and parse the MIDI file at this path
        midi = converter.parse(path)
    except Exception as e:
       #skip corrupted file
        print(f"  [skip] failed to parse {path}: {e}")
        return tokens

    parts = instrument.partitionByInstrument(midi)
    # if the file has separate instrument parts, take the first one and walk through all its notes/chords in order (recurse digs into nested containers);
    # if there's no instrument split (e.g. a single-track file), just grab all notes directly
    stream = parts.parts[0].recurse() if parts else midi.flat.notes

    # go through every musical event in that stream, one at a time, in playback order
    for element in stream:
        # if this event is a single note (like a middle C)...
        if isinstance(element, note.Note):
            # ...store it as a simple string like "C4" (pitch name + octave)
            tokens.append(str(element.pitch))
        # if instead it's a chord (multiple notes played together)...
        elif isinstance(element, chord.Chord):
            # ...encode it as its pitch-class numbers joined by dots, e.g. "4.8.11"
            # (normalOrder gives a consistent numeric fingerprint for the chord shape)
            tokens.append(".".join(str(n) for n in element.normalOrder))
        # (anything that's not a Note or Chord — like a Rest — is silently ignored)

    # hand back the full ordered list of note/chord tokens from this one file
    return tokens


def collect_all_notes(midi_dir):
    # find every file ending in .mid anywhere inside midi_dir (recursive=True searches subfolders too)
    files = glob.glob(os.path.join(midi_dir, "**", "*.mid"), recursive=True)
    # also find files ending in .midi (some tools use this longer extension) and add them to the list
    files += glob.glob(os.path.join(midi_dir, "**", "*.midi"), recursive=True)

    # if we found zero files, there's nothing to train on — stop the program early
    # with a helpful message instead of continuing and crashing somewhere confusing later
    if not files:
        raise SystemExit(
            f"No .mid/.midi files found under '{midi_dir}'. "
            "Add some MIDI files there first (see README.md for sources)."
        )

    # let the user know how many files we're about to process
    print(f"Found {len(files)} MIDI files.")
    # this will accumulate the note/chord tokens from every file, all in one long list
    all_notes = []
    # loop over each file path, showing a progress bar as we go (tqdm wraps the list for that)
    for f in tqdm(files, desc="Parsing MIDI"):
        # parse this one file into tokens, and append them all onto our master list
        all_notes.extend(extract_notes_from_file(f))
    # return the combined list of every note/chord event across all files
    return all_notes


def build_sequences(all_notes, sequence_length):
    # get the list of every UNIQUE note/chord we saw, sorted alphabetically —this becomes our "vocabulary", like the vocabulary of words in a language model
    pitch_names = sorted(set(all_notes))
    # build a lookup dictionary: note name -> integer id (e.g. "C4" -> 0, "D4" -> 1, ...)
    # neural networks need numbers, not strings, so this is our translation table
    note_to_int = {n: i for i, n in enumerate(pitch_names)}

    # this will hold the "input" side of training examples: chunks of sequence_length notes
    network_input = []
    # this will hold the "output" side: the single note that comes right after each chunk
    network_output = []
    # slide a window of size sequence_length across the whole song(s), one step at a time
    for i in range(len(all_notes) - sequence_length):
        # take sequence_length notes in a row — this is what the model will "see"
        seq_in = all_notes[i : i + sequence_length]
        # take the very next note after that window — this is what the model must "predict"
        seq_out = all_notes[i + sequence_length]
        # convert the input window from note names to integers, and store it
        network_input.append([note_to_int[n] for n in seq_in])
        # convert the target note to its integer id too, and store it
        network_output.append(note_to_int[seq_out])

    # how many unique notes/chords exist in total — this sizes the model's output layer later
    n_vocab = len(pitch_names)
    # reshape the input into the 3D shape Keras/TensorFlow LSTMs expect:
    # (number of examples, sequence_length, 1 feature per timestep)
    X = np.reshape(network_input, (len(network_input), sequence_length, 1))
    # scale all the integer ids down into the 0-1 range — neural nets train more
    # smoothly on small, normalized numbers rather than large raw integers
    X = X / float(max(n_vocab - 1, 1))  # normalize to [0, 1]
    # convert the output list into a plain numpy array of integers (the target labels)
    y = np.array(network_output)

    # hand back everything the training script will need
    return X, y, pitch_names, note_to_int


def main():
    # set up the command-line argument parser
    parser = argparse.ArgumentParser()
    # --midi-dir: where to look for input MIDI files (defaults to data/midi)
    parser.add_argument("--midi-dir", default="data/midi")
    # --sequence-length: how many notes the model looks at before predicting the next one
    parser.add_argument("--sequence-length", type=int, default=50)
    # --out-dir: where to save the processed data files
    parser.add_argument("--out-dir", default="data")
    # actually read whatever the user typed on the command line
    args = parser.parse_args()

    # make sure the output folder exists (does nothing if it's already there)
    os.makedirs(args.out_dir, exist_ok=True)

    # step 1: read every MIDI file in midi_dir and turn them into one long note list
    all_notes = collect_all_notes(args.midi_dir)
    # print a quick summary so the user can eyeball whether this looks reasonable
    print(f"Extracted {len(all_notes)} note/chord events, "
          f"{len(set(all_notes))} unique tokens.")

    # step 2: slice that note list into (input window -> next note) training pairs
    X, y, pitch_names, note_to_int = build_sequences(all_notes, args.sequence_length)
    print(f"Built {len(X)} training sequences of length {args.sequence_length}.")

    # save the numeric training arrays to disk in a compressed .npz file
    np.savez(os.path.join(args.out_dir, "sequences.npz"), X=X, y=y)
    # also save the vocabulary info we'll need later (to decode predictions back to notes)
    with open(os.path.join(args.out_dir, "notes.pkl"), "wb") as f:
        pickle.dump(
            {
                "pitch_names": pitch_names,      # the list of unique notes/chords
                "note_to_int": note_to_int,      # the note-name -> id lookup table
                "sequence_length": args.sequence_length,  # so later scripts know the window size used
            },
            f,
        )

    # final confirmation message so the user knows preprocessing finished successfully
    print(f"Saved data/sequences.npz and data/notes.pkl "
          f"(vocab size = {len(pitch_names)}).")


# this is the standard Python idiom meaning "only run main() if this file is executed directly" (as opposed to being imported by another script)
if __name__ == "__main__":
    main()
