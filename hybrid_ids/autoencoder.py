import os

import matplotlib.pyplot as plt
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.layers import Dense, Dropout, Input
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam

import hybrid_ids.config as config


def build_autoencoder(input_dimension):
    """Build regularized autoencoder (128→64→32→16 bottleneck with dropout)."""
    print("\n")
    print("=" * 70)
    print("STAGE 1: AUTOENCODER")
    print("=" * 70)
    print("\nInput features:", input_dimension)
    print(f"Dropout rate: {config.DROPOUT_RATE}")

    input_layer = Input(shape=(input_dimension,), name="input")

    encoder_1 = Dense(128, activation="relu", name="encoder_128")(input_layer)
    encoder_1 = Dropout(config.DROPOUT_RATE, name="dropout_enc_128")(encoder_1)
    encoder_2 = Dense(64, activation="relu", name="encoder_64")(encoder_1)
    encoder_2 = Dropout(config.DROPOUT_RATE, name="dropout_enc_64")(encoder_2)
    encoder_3 = Dense(32, activation="relu", name="encoder_32")(encoder_2)
    bottleneck = Dense(16, activation="relu", name="bottleneck")(encoder_3)

    decoder_1 = Dense(32, activation="relu", name="decoder_32")(bottleneck)
    decoder_1 = Dropout(config.DROPOUT_RATE, name="dropout_dec_32")(decoder_1)
    decoder_2 = Dense(64, activation="relu", name="decoder_64")(decoder_1)
    decoder_2 = Dropout(config.DROPOUT_RATE, name="dropout_dec_64")(decoder_2)
    decoder_3 = Dense(128, activation="relu", name="decoder_128")(decoder_2)
    output_layer = Dense(input_dimension, activation="linear", name="output")(decoder_3)

    autoencoder = Model(input_layer, output_layer, name="CICIDS2018_Autoencoder")
    return autoencoder


def compile_autoencoder(autoencoder):
    """Compile the autoencoder with Adam optimizer and MSE loss."""
    autoencoder.compile(
        optimizer=Adam(learning_rate=config.LEARNING_RATE),
        loss="mse",
        metrics=["mae"],
    )
    print("\nAutoencoder architecture:")
    autoencoder.summary()


def train_autoencoder(autoencoder, X_normal_np):
    """Train the autoencoder on normal traffic only."""
    early_stopping = EarlyStopping(
        monitor="val_loss",
        patience=config.EARLY_STOPPING_PATIENCE,
        restore_best_weights=True,
        verbose=1,
    )
    reduce_lr = ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=5,
        min_lr=1e-6,
        verbose=1,
    )

    print("\nTraining Autoencoder...")
    history = autoencoder.fit(
        X_normal_np,
        X_normal_np,
        epochs=config.EPOCHS,
        batch_size=config.BATCH_SIZE,
        validation_split=0.15,
        callbacks=[early_stopping, reduce_lr],
        shuffle=True,
        verbose=1,
    )
    return history


def save_autoencoder(autoencoder):
    """Persist the trained autoencoder to disk."""
    autoencoder.save(os.path.join(config.MODEL_FOLDER, "autoencoder.keras"))
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
        os.path.join(config.MODEL_FOLDER, "autoencoder_loss.png"),
        dpi=300,
    )
    plt.close()
