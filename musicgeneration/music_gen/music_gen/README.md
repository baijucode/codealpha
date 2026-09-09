# AI Music Generation with LSTM

A complete pipeline: collect MIDI → preprocess into note sequences → train an
LSTM → generate new sequences → convert back to a playable MIDI file.

## 1. Install dependencies

```bash
pip install -r requirements.txt --break-system-packages
```

## 2. Collect MIDI data

Put `.mid` / `.midi` files into `data/midi/`. Good free sources:

- **Classical piano**: [Classical Piano MIDI Page](http://www.piano-midi.de/)
- **Lakh MIDI Dataset** (huge, all genres): https://colinraffel.com/projects/lmd/
- **MAESTRO** (virtuosic piano performances): https://magenta.tensorflow.org/datasets/maestro
- **Jazz**: search "jazz midi collection" — many small curated packs exist.

Even 20–50 MIDI files of a single style (e.g. Chopin piano pieces) is enough
to get a model producing something musically coherent. More data = better
generalization but longer training.

## 3. Preprocess

```bash
python preprocess.py
```

This walks `data/midi/`, extracts notes and chords with `music21`, converts
them into integer-encoded sequences, and saves:
- `data/notes.pkl` — the raw vocabulary of notes/chords seen
- `data/sequences.npz` — the training input/output arrays

## 4. Train

```bash
python train.py --epochs 100 --batch-size 64
```

Checkpoints are saved to `checkpoints/` after each epoch that improves loss,
so you can stop and resume anytime.

## 5. Generate music

```bash
python generate.py --checkpoint checkpoints/best.weights.h5 --length 200 --output output/generated.mid
```

This produces a `.mid` file in `output/` that you can play in any media
player, DAW (Ableton, FL Studio, GarageBand), or online MIDI player.

## How it works (mapping to the task steps)

| Task step | File |
|---|---|
| Collect MIDI data | `data/midi/` (you supply files) |
| Preprocess into note sequences | `preprocess.py` |
| Build LSTM model | `model.py` |
| Train the model | `train.py` |
| Convert generated sequences to MIDI | `generate.py` |

## Notes on scale

- CPU training works but is slow; a GPU (Colab free tier is fine) speeds
  this up 10-50x.
- Start with `sequence_length=50`, `epochs=50-100` on a modest dataset
  before scaling up.
- If generated output sounds too repetitive, increase temperature in
  `generate.py` (`--temperature 1.0` or higher) or train longer.
