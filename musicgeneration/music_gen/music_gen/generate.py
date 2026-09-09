#Step 5: Generate a new note sequence from the trained model and convert it to a playable MIDI file.

# argparse: read command-line settings like --length and --temperature
import argparse
# pickle: to load the saved vocabulary info from preprocessing
import pickle
# random: used to pick a random starting point in the training data
import random

# numpy: for array math
import numpy as np
# music21 pieces needed to build a MIDI file from note/chord tokens
from music21 import chord, instrument, note, stream

# our model-building function, so we can recreate the same architecture and then load the trained weights into it
from model import build_model


def sample_with_temperature(probabilities, temperature=1.0):
    # convert to a numpy array of high-precision floats for stable math
    probabilities = np.asarray(probabilities).astype("float64")
    # take the log of the probabilities (add a tiny number to avoid log(0) errors),
    # then divide by temperature — this is the standard "temperature sampling" trick:
    # temperature < 1 sharpens the distribution (safer, more repetitive picks),
    # temperature > 1 flattens it (more random, more surprising picks)
    probabilities = np.log(probabilities + 1e-9) / temperature
    # undo the log with exp, turning these back into (unnormalized) probability-like scores
    exp_probs = np.exp(probabilities)
    # normalize so all the values sum back up to exactly 1, forming a valid probability distribution
    probabilities = exp_probs / np.sum(exp_probs)
    # randomly draw ONE index, where each index's chance of being picked equals its probability
    return np.random.choice(len(probabilities), p=probabilities)


def generate_sequence(model, network_input, pitch_names, n_vocab, length, temperature):
    # build the reverse lookup: integer id -> note name (opposite of preprocessing's note_to_int)
    int_to_note = {i: n for i, n in enumerate(pitch_names)}

    # pick a random training sequence to use as our starting "seed" —
    # this gives the model a realistic musical context to continue from
    start = random.randint(0, len(network_input) - 1)
    # copy that seed sequence into a plain Python list we can grow/shift as we generate
    pattern = list(network_input[start])  # list of ints (already normalized? see main)

    # this will collect the actual note/chord tokens we generate, one per loop iteration
    generated = []
    # generate one new note at a time, `length` times total
    for _ in range(length):
        # how long the current input window is (should stay constant = sequence_length)
        seq_len = len(pattern)
        # reshape the pattern into the (1 example, seq_len timesteps, 1 feature) shape
        # the model expects — the leading 1 means "a single example," since Keras
        # always expects a batch dimension even when predicting one thing at a time
        input_arr = np.reshape(pattern, (1, seq_len, 1))
        # ask the model to predict probabilities for "what note comes next?"
        # verbose=0 just silences the default progress output for each call
        prediction = model.predict(input_arr, verbose=0)[0]

        # turn those probabilities into one chosen note id, with controllable randomness
        index = sample_with_temperature(prediction, temperature)
        # translate that id back into a readable note/chord string and save it
        generated.append(int_to_note[index])

        # slide the window forward: add the note we just generated (normalized,
        # same way preprocessing normalized inputs) onto the end of the pattern...
        pattern.append(index / float(max(n_vocab - 1, 1)))
        # ...and drop the oldest note off the front, keeping the window the same length.
        # This is how the model "remembers" recent context as it keeps composing.
        pattern = pattern[1:]

    # return the full list of newly generated note/chord tokens
    return generated


def tokens_to_midi(tokens, output_path, step_duration=0.5):
    """Convert generated note/chord tokens back into a MIDI file."""
    # create an empty music21 "Stream" — think of it as a blank sheet of music
    # we're about to place notes onto
    output_stream = stream.Stream()
    # tracks where in time (in quarter-note beats) the next note/chord should be placed
    offset = 0.0

    # go through every generated token in order
    for token in tokens:
        # a token represents a CHORD if it contains a "." (multiple pitch numbers joined),
        # or is a plain digit string (a single pitch-class number rather than a note name)
        if ("." in token) or token.isdigit():
            # split the token back into its individual pitch-class numbers
            notes_in_chord = token.split(".")
            # build a list of actual music21 Note objects, one per pitch in the chord
            chord_notes = []
            for n in notes_in_chord:
                # create a note from its numeric pitch value
                new_note = note.Note(int(n))
                # mark it as a piano note (affects playback sound/instrument choice)
                new_note.storedInstrument = instrument.Piano()
                chord_notes.append(new_note)
            # combine those individual notes into a single Chord object
            new_chord = chord.Chord(chord_notes)
            # place this chord at the current point in time
            new_chord.offset = offset
            # add it to our music sheet
            output_stream.append(new_chord)
        else:
            # otherwise it's a single note like "C4" — create it directly from that name
            new_note = note.Note(token)
            # place it at the current point in time
            new_note.offset = offset
            # mark it as a piano note
            new_note.storedInstrument = instrument.Piano()
            # add it to our music sheet
            output_stream.append(new_note)

        # move the "playhead" forward before placing the next note/chord
        offset += step_duration

    # write the finished sheet of music out to an actual .mid file on disk
    output_stream.write("midi", fp=output_path)


def main():
    # set up command-line argument parsing
    parser = argparse.ArgumentParser()
    # where to find the preprocessed data (needed to rebuild the vocabulary and get seed sequences)
    parser.add_argument("--data-dir", default="data")
    # path to the trained model weights saved by train.py
    parser.add_argument("--checkpoint", default="checkpoints/best.weights.h5")
    # how many new notes/chords to generate
    parser.add_argument("--length", type=int, default=200)
    # where to save the resulting MIDI file
    parser.add_argument("--output", default="output/generated.mid")
    # controls how "creative" vs "safe" the generated notes are (see sample_with_temperature)
    parser.add_argument("--temperature", type=float, default=1.0)
    # must match the lstm_units value used during training, or the saved
    # weights won't fit into the model's layers correctly
    parser.add_argument("--lstm-units", type=int, default=256)
    # read whatever the user typed on the command line
    args = parser.parse_args()

    # load the preprocessed training sequences — we'll reuse one as a starting seed
    data = np.load(f"{args.data_dir}/sequences.npz")
    X = data["X"]  # already normalized, shape (n, seq_len, 1)

    # load the vocabulary metadata saved during preprocessing
    with open(f"{args.data_dir}/notes.pkl", "rb") as f:
        meta = pickle.load(f)
    # the list of unique notes/chords the model knows about
    pitch_names = meta["pitch_names"]
    # how many unique notes/chords exist (needed to rebuild the model correctly)
    n_vocab = len(pitch_names)
    # the input window length the model was trained with
    sequence_length = meta["sequence_length"]

    # recreate the exact same model architecture used during training...
    model = build_model(sequence_length, n_vocab, lstm_units=args.lstm_units)
    # ...then load the trained weights into it (this is what makes it "smart"
    # rather than a randomly-initialized, untrained network)
    model.load_weights(args.checkpoint)

    # flatten each 3D input sequence (seq_len, 1) back down into a plain 1D
    # list of floats — this is the format generate_sequence() works with as it slides the window
    network_input = [seq.flatten().tolist() for seq in X]

    print(f"Generating {args.length} notes (temperature={args.temperature})...")
    tokens = generate_sequence(
        model, network_input, pitch_names, n_vocab, args.length, args.temperature
    )

 
    tokens_to_midi(tokens, args.output)

    print(f"Saved generated music to {args.output}")


if __name__ == "__main__":
    main()
