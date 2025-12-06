"""
Train a neural network to classify word definitions by part of speech.
"""

import json, re
import numpy as np
import tensorflow as tf

from sklearn.model_selection import train_test_split


# Standardized POS labels
POS_PKU = {
    "a": "adjective",
    "b": "adjective",
    "c": "conjunction",
    "d": "adverb",
    "e": "interjection",
    "f": "postposition",
    "g": "other",
    "h": "other",
    "i": "idiom",
    "j": "other",
    "k": "other",
    "l": "idiom",
    "m": "numeral",
    "n": "noun",
    "o": "other",
    "p": "preposition",
    "q": "classifier",
    "r": "pronoun",
    "s": "noun",
    "t": "noun",
    "u": "particle",
    "v": "verb",
    "w": "other",
    "x": "other",
    "y": "particle",
    "z": "adjective",
}
POS_WIKTIONARY = {
    "adj": "adjective",
    "adv": "adverb",
    "conj": "conjunction",
    "classifier": "classifier",
    "det": "pronoun",
    "intj": "interjection",
    "noun": "noun",
    "num": "numeral",
    "particle": "particle",
    "phrase": "idiom",
    "postp": "postposition",
    "prep": "preposition",
    "pron": "pronoun",
    "proverb": "idiom",
    "verb": "verb",
}
POS_LABELS = sorted(set(POS_PKU.values()))


# Training parameters
TEST_SIZE = 0.5
MAX_TOKENS = 15000
EPOCHS = 5


def main():
    # Load training data
    try:
        with open("tagged/pos_training.json", "r", encoding="utf-8") as training_json:
            [definitions, labels] = json.load(training_json)
    except:
        (definitions, labels) = load_training_data()

    # Split training data into training and testing sets
    (x_train, x_test, y_train, y_test) = train_test_split(definitions, labels, test_size=TEST_SIZE)
    train_dataset = tf.data.Dataset.from_tensor_slices((x_train, y_train)).batch(32)
    test_dataset = tf.data.Dataset.from_tensor_slices((x_test, y_test)).batch(32)

    # Create neural network model
    model = create_model(x_train)

    # Train model
    model.fit(train_dataset, epochs=EPOCHS)

    # Evaluate model performance
    model.evaluate(test_dataset, verbose=2)

    # Export model
    model.save("pos.keras")


def load_training_data():
    """
    Load and format Kaikki Wiktionary dataset for training.
    
    The full database of words and definitions is used, regardless of HSK status.
    """
    definitions = []
    labels = []

    # Read word data from JSONL file
    with open("raw/words/kaikki_dictionary-Chinese.jsonl", "r", encoding="utf-8") as words_jsonl:
        for line in words_jsonl:
            # Read word data
            word_full = json.loads(line)

            # Extract POS label
            if word_full["pos"] not in POS_WIKTIONARY:
                continue
            word_pos = POS_WIKTIONARY[word_full["pos"]]

            # Extract definitions
            word_definitions = []
            for sense in word_full["senses"]:
                if "glosses" not in sense:
                    continue
                word_definitions.extend([
                    re.sub(r" \(Classifier: .*\)", "", gloss)
                    for gloss in sense["glosses"] if not(
                        gloss.lower().startswith(("alternative ", "synonym of", "short for", "erhua"))
                    )
                ])
            
            # Record definition-label pairs
            for definition in word_definitions:
                definitions.append(definition)
                labels.append(POS_LABELS.index(word_pos))
    
    # Export loaded data to JSON
    with open("tagged/pos_training.json", "w", encoding="utf-8") as training_json:
        json.dump([definitions, labels], training_json, ensure_ascii=False)

    return (definitions, labels)


def create_model(x_train):
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
            tf.keras.layers.Bidirectional(tf.keras.layers.GRU(64)),
            tf.keras.layers.Dense(100, activation="relu"),
            tf.keras.layers.Dropout(0.25),
            tf.keras.layers.Dense(len(POS_LABELS), activation="softmax")
        ]
    )

    # Compile model
    model.compile(loss="sparse_categorical_crossentropy", metrics=["accuracy"])

    return model


def predict_pos(definition_list):
    """
    Use trained neural network to predict POS labels for given dictionary definitions.
    """
    model = tf.keras.models.load_model("pos.keras")

    # Predict POS labels
    definition_dataset = tf.data.Dataset.from_tensor_slices(definition_list).batch(32)
    labels = model.predict(definition_dataset, verbose=2).tolist()
    labels = np.argmax(labels, axis=1)
    
    return [POS_LABELS[label] for label in labels]


if __name__ == "__main__":
    main()