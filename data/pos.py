"""
Train a neural network to classify CC-CEDICT word definitions by part of speech.
"""

import hanlp, json, re
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
TEST_SIZE = 0.2
BATCH_SIZE = 16
MAX_TOKENS = 10000
EPOCHS = 5


def main():
    # Load training data
    try:
        with open("working/pos_training.json", "r", encoding="utf-8") as training_json:
            [labeled, unlabeled] = json.load(training_json)
    except:
        (labeled, unlabeled) = sort_raw_data()
    
    headwords = [item[0] for item in labeled]
    definitions = [item[1] for item in labeled]
    labels = [POS_LABELS.index(item[2]) for item in labeled]

    # Split training data into training and testing sets
    (xh_train, xh_test, xd_train, xd_test, y_train, y_test) = train_test_split(headwords, definitions, labels, test_size=TEST_SIZE)
    train_dataset = tf.data.Dataset.from_tensor_slices(({"headword": xh_train, "definition": xd_train}, y_train)).batch(BATCH_SIZE)
    test_dataset = tf.data.Dataset.from_tensor_slices(({"headword": xh_test, "definition": xd_test}, y_test)).batch(BATCH_SIZE)

    # Create neural network model
    model = create_model(xh_train, xd_train)

    # Train model
    model.fit(train_dataset, epochs=EPOCHS)

    # Evaluate model performance
    model.evaluate(test_dataset, verbose=2)

    # Export model
    model.save("working/pos_model.keras")


def sort_raw_data():
    """
    Load raw dataset and isolate labeled items for training.
    
    Words tagged with only one POS (based on the sentence corpus) are labeled accordingly for training.
    Words with multiple POS tags are set aside to later be labeled by the trained model.
    """
    labeled = []
    unlabeled = []

    # Comb sentence corpus to collate all POS tags for each word
    tags = {}
    with open("../export/json/sentences.json", "r", encoding="utf-8") as sentences_json:
        sentences = json.load(sentences_json)

    for sentence in sentences:
        for [word, pos] in sentences[sentence]["tags"]:
            if word not in tags:
                tags[word] = {pos}
            else:
                tags[word].add(pos)
    
    # Load raw drkameleon word set with definitions
    with open("raw/words/drkameleon_hsk-vocabulary-complete.json", "r", encoding="utf-8") as words_json:
        word_entries = json.load(words_json)

    for word_entry in word_entries:
        # Extract headword
        word = word_entry["simplified"]

        # Discard proper noun forms
        word_forms = [form for form in word_entry["forms"] if (not re.search(r"[A-Z]", form["transcriptions"]["numeric"])) or len(word_entry["forms"]) == 1]
        
        # Discard Taiwan-specific or trivial definitions
        word_meanings = [
            re.sub(r" \(Taiwan pr\. .*\)", "", meaning)
            for form in word_forms for meaning in form["meanings"] if not (
                meaning.startswith(("Taiwan", "(Taiwan", "Beijing pr. ", "also ", "used in ", "(used ", "equivalent ", "(indicates ", "abbr. ", "see ", "Kangxi radical ")) or
                any(substring in meaning for substring in ["(Tw)", "(Taiwan)", "variant of"])
            )
        ]
        if len(word_meanings) == 0:
            continue
            
        # If word only has one POS tag, add word and all its definitions to labeled set
        if len(tags.get(word, set())) == 1:
            pos = tags[word].pop()
            for definition in word_meanings:
                labeled.append((word, definition, pos))
        
        # Otherwise, add word and all its definitions to unlabeled set
        else:
            for definition in word_meanings:
                unlabeled.append((word, definition))

    # Export sorted data to JSON
    with open("working/pos_training.json", "w", encoding="utf-8") as training_json:
        json.dump([labeled, unlabeled], training_json, ensure_ascii=False)

    return (labeled, unlabeled)


def create_model(xh_train, xd_train):
    """
    Create and compile a neural network model.
    """
    # Model inputs
    input_head = tf.keras.Input(dtype="string", shape=(), name="headword")
    input_def = tf.keras.Input(dtype="string", shape=(), name="definition")

    # Text vectorization & embedding
    vectorization_head = tf.keras.layers.TextVectorization(max_tokens=MAX_TOKENS, output_sequence_length=64, split="character")
    vectorization_def = tf.keras.layers.TextVectorization(max_tokens=MAX_TOKENS, output_sequence_length=64, ngrams=2)

    vectorization_head.adapt(xh_train)
    vectorization_def.adapt(xd_train)

    embed_head = tf.keras.layers.Embedding(
        len(vectorization_head.get_vocabulary()),
        100,
        embeddings_initializer=tf.keras.initializers.Constant(
            create_embedding_matrix(
                hanlp.load(hanlp.pretrained.word2vec.RADICAL_CHAR_EMBEDDING_100),
                100,
                vectorization_head.get_vocabulary()
            )
        ),
        trainable=False
    )(vectorization_head(input_head))
    embed_def = tf.keras.layers.Embedding(
        len(vectorization_def.get_vocabulary()),
        50,
        embeddings_initializer=tf.keras.initializers.Constant(
            create_embedding_matrix(
                hanlp.load(hanlp.pretrained.glove.GLOVE_6B_50D),
                50,
                vectorization_def.get_vocabulary()
            )
        ),
        trainable=False
    )(vectorization_def(input_def))
    
    # Model layers
    x = tf.keras.layers.Concatenate()([embed_head, embed_def])
    x = tf.keras.layers.Bidirectional(tf.keras.layers.GRU(32))(x)
    x = tf.keras.layers.Dense(25, activation="relu")(x)
    output = tf.keras.layers.Dense(len(POS_LABELS), activation="softmax")(x)

    # Create model
    model = tf.keras.Model(inputs=[input_head, input_def], outputs=output)

    # Compile model
    model.compile(loss="sparse_categorical_crossentropy", metrics=["accuracy"])

    return model


def create_embedding_matrix(embedding, dim, vocab):
    """
    Build embedding matrix from pretrained embedding
    """
    embedding_matrix = np.zeros((len(vocab), dim), dtype='float32')
    for (index, word) in enumerate(vocab):
        try:
            embedding_matrix[index] = embedding(word)
        except KeyError:
            pass
    return embedding_matrix


def predict_pos(input):
    """
    Use trained neural network to predict POS labels for given dictionary definitions.
    """
    model = tf.keras.models.load_model("working/pos_model.keras")

    headword_list = [item[0] for item in input]
    definition_list = [item[1] for item in input]

    # Predict POS labels
    data = tf.data.Dataset.from_tensor_slices({"headword": headword_list, "definition": definition_list}).batch(32)
    labels = model.predict(data, verbose=2).tolist()
    labels = np.argmax(labels, axis=1)
    
    return [POS_LABELS[label] for label in labels]


if __name__ == "__main__":
    main()