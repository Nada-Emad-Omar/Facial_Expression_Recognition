# -*- coding: utf-8 -*-
"""Yet another copy of ProjectNoteBook.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1MvSPut1Yq9YcXlyjZX-oBkdJxAnMXGvz
"""

!mkdir -p ~/.kaggle
!mv kaggle.json ~/.kaggle/
!chmod 600 ~/.kaggle/kaggle.json

!kaggle datasets download -d jonathanoheix/face-expression-recognition-dataset

!unzip /content/face-expression-recognition-dataset.zip

import os
import cv2
import numpy as np

def load_images_and_labels(directory):
  images = []
  labels = []
  for label in os.listdir(directory):
    label_directory = os.path.join(directory, label)
    if os.path.isdir(label_directory):
      for filename in os.listdir(label_directory):
        img_path = os.path.join(label_directory, filename)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
          images.append(img)
          labels.append(label)
  return np.array(images), np.array(labels)


train_images, train_labels = load_images_and_labels('/content/images/images/train')
validation_images, validation_labels = load_images_and_labels('/content/images/images/validation')

print("Train images shape:", train_images.shape)
print("Train labels shape:", train_labels.shape)
print("Validation images shape:", validation_images.shape)
print("Validation labels shape:", validation_labels.shape)

import matplotlib.pyplot as plt

unique_labels, label_counts = np.unique(train_labels, return_counts=True)

plt.figure(figsize=(10, 5))
plt.bar(unique_labels, label_counts)
plt.xlabel("Emotion Class")
plt.ylabel("Number of Images")
plt.title("Distribution of Emotion Classes in Training Data")
plt.show()

num_images_per_class = 3

# Create a dictionary to store images for each class
images_by_class = {}

# Iterate through the training data and store images for each class
for i in range(len(train_images)):
  label = train_labels[i]
  if label not in images_by_class:
    images_by_class[label] = []
  if len(images_by_class[label]) < num_images_per_class:
    images_by_class[label].append(train_images[i])


# Create a figure and subplots for displaying the images
plt.figure(figsize=(15, 10))
subplot_index = 1

# Iterate through the classes and display the selected images
for label, images in images_by_class.items():
  for image in images:
    plt.subplot(len(images_by_class), num_images_per_class, subplot_index)
    plt.imshow(image, cmap='gray')
    plt.title(label)
    plt.axis('off')
    subplot_index += 1

plt.tight_layout()
plt.show()

unique_labels = np.unique(train_labels)
label_to_numeric = {label: i for i, label in enumerate(unique_labels)}

print("Label to Numeric Mapping:")
for label, numeric_value in label_to_numeric.items():
  print(f"{label}: {numeric_value}")

train_labels_numeric = [label_to_numeric[label] for label in train_labels]
validation_labels_numeric = [label_to_numeric[label] for label in validation_labels]

def resize_images(images, size=(48, 48)):
  resized_images = []
  for image in images:
    resized_image = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
    resized_images.append(resized_image)
  return np.array(resized_images)

train_images_resized = resize_images(train_images)
validation_images_resized = resize_images(validation_images)

print("Resized Train images shape:", train_images_resized.shape)
print("Resized Validation images shape:", validation_images_resized.shape)

train_images_normalized = train_images_resized / 255.0


print("Normalized Train images shape:", train_images_normalized.shape)

from imblearn.over_sampling import RandomOverSampler
from collections import Counter

ros = RandomOverSampler(random_state=42)
train_images_balanced, train_labels_balanced = ros.fit_resample(
    train_images_normalized.reshape(-1, 48 * 48), np.array(train_labels_numeric)
)

train_images_balanced = train_images_balanced.reshape(-1, 48, 48, 1)

print("Balanced Train images shape:", train_images_balanced.shape)
print("Balanced Train labels shape:", train_labels_balanced.shape)

numeric_label_counts_balanced = Counter(train_labels_balanced)

print("Balanced Numeric Label Counts:")
for label, count in numeric_label_counts_balanced.items():
  print(f"Label {label}: {count} images")

plt.figure(figsize=(10, 5))
plt.bar(numeric_label_counts_balanced.keys(), numeric_label_counts_balanced.values())
plt.xlabel("Emotion Class (Numeric)")
plt.ylabel("Number of Images")
plt.title("Distribution of Emotion Classes in Balanced Training Data")
plt.show()

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

#one-hot encode your labels:
num_classes = 7  # Number of classes (0-6)
train_labels_balanced = to_categorical(train_labels_balanced, num_classes)

from sklearn.model_selection import train_test_split

X_train, X_val, y_train, y_val = train_test_split(train_images_balanced, train_labels_balanced, test_size=0.2, random_state=42)

from tensorflow.keras.layers import BatchNormalization

model2 = models.Sequential([
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(48, 48, 1)),
    layers.BatchNormalization(),
    layers.MaxPooling2D((2, 2)),
    layers.Dropout(0.25),

    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.BatchNormalization(),
    layers.MaxPooling2D((2, 2)),
    layers.Dropout(0.25),

    layers.Conv2D(128, (3, 3), activation='relu'),
    layers.BatchNormalization(),
    layers.MaxPooling2D((2, 2)),
    layers.Dropout(0.25),

    layers.Conv2D(256, (3, 3), activation='relu'),
    layers.BatchNormalization(),
    layers.MaxPooling2D((2, 2)),
    layers.Dropout(0.25),

    layers.Flatten(),
    layers.Dense(128, activation='relu'),
    layers.BatchNormalization(),
    layers.Dropout(0.5),
    layers.Dense(num_classes, activation='softmax')
])

model2.summary()

from tensorflow.keras.callbacks import EarlyStopping

early_stopping = EarlyStopping(
    monitor='val_loss',      # Monitor validation loss
    patience=5,              # Number of epochs with no improvement to wait before stopping
    restore_best_weights=True # Restore model weights from the epoch with the best validation loss
)
reduce_lr = ReduceLROnPlateau(
    monitor='val_loss',      # Monitor validation loss
    factor=0.2,              # Factor by which the learning rate will be reduced
    patience=3,              # Number of epochs with no improvement to wait before reducing learning rate
    min_lr=1e-6              # Lower bound on the learning rate
)

model2.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])

history2 = model2.fit(X_train, y_train, epochs=50, batch_size=32,
                    validation_data=(X_val, y_val),
                    callbacks=[early_stopping, reduce_lr])

plt.figure(figsize=(12, 6))

# Plot training & validation loss values
plt.subplot(1, 2, 1)
plt.plot(history2.history['loss'], label='Train Loss')
plt.plot(history2.history['val_loss'], label='Validation Loss')
plt.title('Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

# Plot training & validation accuracy values
plt.subplot(1, 2, 2)
plt.plot(history2.history['accuracy'], label='Train Accuracy')
plt.plot(history2.history['val_accuracy'], label='Validation Accuracy')
plt.title('Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()

plt.tight_layout()
plt.show()

from sklearn.metrics import classification_report

# Make predictions on the validation set
y_pred_prob = model2.predict(X_val)
y_pred = np.argmax(y_pred_prob, axis=1)
y_true = np.argmax(y_val, axis=1)

# Print the classification report
print(classification_report(y_true, y_pred))

# prompt: true vs predict images

import matplotlib.pyplot as plt

# Get the predicted labels for the validation set
y_pred_prob = model2.predict(X_val)
y_pred = np.argmax(y_pred_prob, axis=1)
y_true = np.argmax(y_val, axis=1)

# Create a figure to display the images
plt.figure(figsize=(15, 10))

# Iterate through a few examples from the validation set
num_examples_to_show = 10  # You can change this to show more or fewer examples
for i in range(num_examples_to_show):
    plt.subplot(2, 5, i + 1)
    plt.imshow(X_val[i].reshape(48, 48), cmap='gray')
    plt.title(f"True: {y_true[i]}, Pred: {y_pred[i]}")
    plt.axis('off')

plt.tight_layout()
plt.show()

import numpy as np
test_images, test_labels = load_images_and_labels('/content/images/validation')
test_images_resized = resize_images(test_images)
test_images_normalized = test_images_resized / 255.0
test_labels_numeric = [label_to_numeric[label] for label in test_labels]
test_labels_categorical = to_categorical(test_labels_numeric, num_classes)

# Evaluate the model on the test set
loss, accuracy = model2.evaluate(test_images_normalized.reshape(-1, 48, 48, 1), test_labels_categorical, verbose=0)
print("Test Loss:", loss)
print("Test Accuracy:", accuracy)

# Make predictions on the test set
y_pred_prob = model2.predict(test_images_normalized.reshape(-1, 48, 48, 1))
y_pred = np.argmax(y_pred_prob, axis=1)
y_true = np.argmax(test_labels_categorical, axis=1)

# Print the classification report
print(classification_report(y_true, y_pred))

# Get the predicted labels for the test set
y_pred_prob = model2.predict(test_images_normalized.reshape(-1, 48, 48, 1))
y_pred = np.argmax(y_pred_prob, axis=1)
y_true = np.argmax(test_labels_categorical, axis=1)

# Create a figure to display the images
plt.figure(figsize=(15, 10))

# Iterate through a few examples from the test set
num_examples_to_show = 10  # You can change this to show more or fewer examples
for i in range(num_examples_to_show):
    plt.subplot(2, 5, i + 1)
    plt.imshow(test_images_normalized[i].reshape(48, 48), cmap='gray')
    plt.title(f"True: {y_true[i]}, Pred: {y_pred[i]}")
    plt.axis('off')

plt.tight_layout()
plt.show()