"""
Classify word definitions by part of speech.
"""

import tensorflow as tf

from sklearn.model_selection import train_test_split


# Training parameters
TEST_SIZE = 0.1
MAX_TOKENS = 10000
EPOCHS = 5


def tag_definition_pos(data, reference, POS_PKU):
    """
    Classify word definitions by part of speech.
    """

    train_model(reference, POS_PKU)
    
    return data


def train_model(reference, POS_PKU):
    """
    Train a neural network for labeling word definitions by part of speech.

    The reference dataset is used as training data.
    """
    # Prepare training data
    POS_LABELS = sorted(set(POS_PKU.values()))
    (definitions, labels) = prepare_pos_labels(reference, POS_LABELS)

    # Split training data into training and testing sets
    (x_train, x_test, y_train, y_test) = train_test_split(definitions, labels, test_size=TEST_SIZE)
    train_dataset = tf.data.Dataset.from_tensor_slices((x_train, y_train)).batch(8)
    test_dataset = tf.data.Dataset.from_tensor_slices((x_test, y_test)).batch(8)

    # Create neural network model
    model = create_model(x_train, POS_LABELS)

    # Train model
    model.fit(train_dataset, epochs=EPOCHS)

    # Evaluate model performance
    model.evaluate(test_dataset, verbose=2)

    # Export model
    model.save("pos_tagger.keras")


def prepare_pos_labels(reference, POS_LABELS):
    """
    Format reference dataset for training.
    
    Return a tuple of two lists of definitions and corresponding POS labels (as integers).
    """
    definitions = []
    labels = []

    for word in reference:
        for entry in reference[word]:
            entry_pos_label = POS_LABELS.index(entry["pos"])
            entry_definitions = entry["definitions"].split(" | ")

            for definition in entry_definitions:
                definitions.append(definition)
                labels.append(entry_pos_label)
    
    return (definitions, labels)


def create_model(x_train, POS_LABELS):
    """
    Create and compile a neural network model.
    """
    # Create text vectorization layer
    text_vectorization = tf.keras.layers.TextVectorization(max_tokens=MAX_TOKENS)
    text_vectorization.adapt(x_train)

    # Create model
    model = tf.keras.Sequential(
        [
            tf.keras.Input(dtype="string", shape=()),
            text_vectorization,
            tf.keras.layers.Embedding(MAX_TOKENS, 64),
            tf.keras.layers.Bidirectional(tf.keras.layers.GRU(16)),
            tf.keras.layers.Dense(25, activation="relu"),
            tf.keras.layers.Dense(len(POS_LABELS), activation="softmax")
        ]
    )

    # Compile model
    model.compile(loss="sparse_categorical_crossentropy", metrics=["accuracy"])

    return model