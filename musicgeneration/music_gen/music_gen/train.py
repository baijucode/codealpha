#Step 4: Train the model on the preprocessed dataset.
# argparse: read command-line settings like --epochs
import argparse
# os: for making directories and building file paths
import os
# pickle: to load the vocabulary info we saved during preprocessing
import pickle

# numpy: to load our saved training arrays
import numpy as np
# ModelCheckpoint: a Keras "callback" that automatically saves the model's
# weights to disk during training, whenever it improves
from tensorflow.keras.callbacks import ModelCheckpoint

# our own function from model.py that builds the LSTM architecture
from model import build_model


def main():
    # set up command-line argument parsing
    parser = argparse.ArgumentParser()
    # where to find the preprocessed data files (sequences.npz, notes.pkl)
    parser.add_argument("--data-dir", default="data")
    # where to save model weight checkpoints during training
    parser.add_argument("--checkpoint-dir", default="checkpoints")
    # how many full passes over the training data to run
    parser.add_argument("--epochs", type=int, default=100)
    # how many training examples to process at once before updating the model's weights
    parser.add_argument("--batch-size", type=int, default=64)
    # how many "memory units" each LSTM layer has (must match what generate.py uses later!)
    parser.add_argument("--lstm-units", type=int, default=256)
    # actually parse whatever the user passed on the command line
    args = parser.parse_args()

    # create the checkpoint folder if it doesn't already exist
    os.makedirs(args.checkpoint_dir, exist_ok=True)

    # load the training arrays we saved in preprocess.py
    data = np.load(os.path.join(args.data_dir, "sequences.npz"))
    # X = the input note sequences, y = the correct "next note" for each one
    X, y = data["X"], data["y"]

    # load the vocabulary metadata (list of unique notes, sequence length used, etc.)
    with open(os.path.join(args.data_dir, "notes.pkl"), "rb") as f:
        meta = pickle.load(f)
    # how many unique notes/chords exist — this sets the size of the model's output layer
    n_vocab = len(meta["pitch_names"])
    # how long each input window is — this must match the model's expected input shape
    sequence_length = meta["sequence_length"]

    # print a quick summary before training starts, so you can sanity-check the numbers
    print(f"Training on {len(X)} sequences, vocab size {n_vocab}, "
          f"sequence length {sequence_length}.")

    # build a fresh, untrained model with the right input/output sizes
    model = build_model(sequence_length, n_vocab, lstm_units=args.lstm_units)
    # print a text summary of the model's layers and parameter counts
    model.summary()

    # this is the file path where the BEST version of the model's weights will be saved
    checkpoint_path = os.path.join(args.checkpoint_dir, "best.weights.h5")
    # set up the checkpoint callback:
    callbacks = [
        ModelCheckpoint(
            checkpoint_path,       # save to this file
            monitor="loss",        # watch the training loss to decide "best"
            save_best_only=True,   # only overwrite the file when loss improves (don't save every epoch)
            save_weights_only=True,# save just the weights (smaller file, not the full model architecture)
            verbose=1,              # print a message each time it saves
        )
    ]

    # this is the actual training loop — Keras handles the epoch/batch looping internally
    model.fit(
        X,                        
        y,                        
        epochs=args.epochs,      
        batch_size=args.batch_size, 
        callbacks=callbacks,      
    )

    
    print(f"Training complete. Best weights saved to {checkpoint_path}")



if __name__ == "__main__":
    main()
