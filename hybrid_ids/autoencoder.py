import os

import matplotlib.pyplot as plt
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam

from hybrid_ids.config import (
    BATCH_SIZE,
    EPOCHS,
    LEARNING_RATE,
    MODEL_FOLDER,
)


def build_autoencoder(input_dimension):
    """Build the autoencoder model (encoder 128→64→32, decoder 32→64→128)."""
    print("\n")
    print("=" * 70)
    print("STAGE 1: AUTOENCODER")
    print("=" * 70)
    print("\nInput features:", input_dimension)

    input_layer = Input(shape=(input_dimension,), name="input")

    encoder_1 = Dense(128, activation="relu", name="encoder_128")(input_layer)
    encoder_2 = Dense(64, activation="relu", name="encoder_64")(encoder_1)
    bottleneck = Dense(32, activation="relu", name="bottleneck")(encoder_2)

    decoder_1 = Dense(64, activation="relu", name="decoder_64")(bottleneck)
    decoder_2 = Dense(128, activation="relu", name="decoder_128")(decoder_1)
    output_layer = Dense(input_dimension, activation="linear", name="output")(decoder_2)

    autoencoder = Model(input_layer, output_layer, name="CICIDS2018_Autoencoder")
    return autoencoder


def compile_autoencoder(autoencoder):
    """Compile the autoencoder with Adam optimizer and MSE loss."""
    autoencoder.compile(
        optimizer=Adam(learning_rate=LEARNING_RATE),
        loss="mse",
        metrics=["mae"],
    )
    print("\nAutoencoder architecture:")
    autoencoder.summary()


def train_autoencoder(autoencoder, X_normal_np):
    """Train the autoencoder on normal traffic only."""
    early_stopping = EarlyStopping(
        monitor="val_loss",
        patience=7,
        restore_best_weights=True,
    )

    print("\nTraining Autoencoder...")
    history = autoencoder.fit(
        X_normal_np,
        X_normal_np,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_split=0.15,
        callbacks=[early_stopping],
        shuffle=True,
        verbose=1,
    )
    return history


def save_autoencoder(autoencoder):
    """Persist the trained autoencoder to disk."""
    autoencoder.save(os.path.join(MODEL_FOLDER, "autoencoder.keras"))
    print("\nAutoencoder saved.")


def plot_autoencoder_loss(history):
    """Plot and save training/validation loss curves."""
    plt.figure(figsize=(10, 6))
    plt.plot(history.history["loss"], label="Training Loss")
    plt.plot(history.history["val_loss"], label="Validation Loss")
    plt.xlabel("Epoch")
    plt.ylabel("MSE Loss")
    plt.title("Autoencoder Training and Validation Loss")
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        os.path.join(MODEL_FOLDER, "autoencoder_loss.png"),
        dpi=300,
    )
    plt.close()
