#Step 3: Build a deep learning model (stacked LSTM) to learn music patterns.

# import the individual layer types we'll stack together to build the network
from tensorflow.keras.layers import (
    LSTM,              # the "memory" layer that learns patterns over a sequence of notes
    BatchNormalization, # keeps values well-scaled between layers, which helps training stability
    Dense,              # a standard fully-connected layer
    Dropout,            # randomly "turns off" some neurons during training to prevent overfitting
    Input,              # defines the shape of data coming into the model
)
# Sequential is the simplest way to build a model: just stack layers one after another
from tensorflow.keras.models import Sequential


def build_model(sequence_length, n_vocab, lstm_units=256):
    """Stacked LSTM classifier: given a sequence of past notes, predict the
    next note/chord token. This is the standard architecture used in
    symbolic music generation (e.g. the classic 'Classical Piano Composer'
    approach)."""
    # build the network as a straight stack of layers, top to bottom
    model = Sequential(
        [
            # tells the model to expect input shaped like (sequence_length, 1) — i.e. a sequence of `sequence_length` numbers, one number per timestep
            Input(shape=(sequence_length, 1)),

            # first LSTM layer: reads the sequence and outputs a value at EVERY timestep (return_sequences=True) so the next LSTM layer also gets a full sequence
            LSTM(lstm_units, return_sequences=True),
            # randomly zero out 30% of connections here during training — this forces the model to not over-rely on any single neuron, reducing overfitting
            Dropout(0.3),

            # second LSTM layer: digs deeper into the patterns found by the first one, again outputting a full sequence for the next layer to use
            LSTM(lstm_units, return_sequences=True),
            Dropout(0.3),

            # third LSTM layer: this time we do NOT return sequences (default return_sequences=False), so it outputs just ONE summary vector for
            # the whole input sequence — a compressed "understanding" of what came before
            LSTM(lstm_units),

            # a regular fully-connected layer that mixes that summary vector together; relu activation lets it learn non-linear combinations of features
            Dense(lstm_units // 2, activation="relu"),
            # normalize the outputs of that layer to keep training stable and fast
            BatchNormalization(),
            # another round of dropout for extra regularization before the final decision
            Dropout(0.3),

            # the output layer: one neuron per possible note/chord in our vocabulary.
            Dense(n_vocab, activation="softmax"),
        ]
    )

    model.compile(loss="sparse_categorical_crossentropy", optimizer="adam")
    # hand back the fully assembled, ready-to-train model
    return model
