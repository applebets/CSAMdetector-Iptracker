# NSFW_Module.py

import tensorflow as tf
import tensorflow_hub
from PIL import Image
import numpy as np

# Load once when module is imported
model = tf.keras.models.load_model(
    "saved_model.h5",
    custom_objects={"KerasLayer": tensorflow_hub.KerasLayer}
)

# Preprocessing function
def load_image(path):
    img = Image.open(path).convert("RGB").resize((224, 224))
    img_array = np.array(img) / 255.0
    return np.expand_dims(img_array, axis=0)

# Exported function
def is_nsfw_image(image_path):
    try:
        image = load_image(image_path)
        predictions = model.predict(image)[0]
        nsfw_score = predictions[1] + predictions[3] + predictions[4]  # hentai + porn + sexy
        return nsfw_score >= 0.6
    except Exception as e:
        print(f"⚠️ Error processing image {image_path}: {e}")
        return False
