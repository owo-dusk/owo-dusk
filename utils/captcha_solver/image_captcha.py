# This file is part of owo-dusk.
#
# Copyright (c) 2024-present EchoQuill
#
# Portions of this file are based on code by EchoQuill, licensed under the
# GNU General Public License v3.0 (GPL-3.0).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.


import onnxruntime
import numpy as np
import io
from PIL import Image

"""Configurations"""
ONNX_MODEL_PATH = "utils/captcha_solver/best.onnx"
IMG_SIZE = 384
CLASSES = "abcdefghijklmnopqrstuvwxyz"
CONF_THRES = 0.3

# Loads the model
onnx_session = onnxruntime.InferenceSession(
    ONNX_MODEL_PATH, providers=["CPUExecutionProvider"]
)

inputs = onnx_session.get_inputs()
input_name = inputs[0].name


def letterbox(img_array, new_size=384, color=(114, 114, 114)):
    img = Image.fromarray(img_array)

    w, h = img.size
    scale = min(new_size / w, new_size / h)

    nw, nh = int(w * scale), int(h * scale)
    img_resized = img.resize((nw, nh), Image.BILINEAR)

    # Create new square image with padding color
    new_img = Image.new("RGB", (new_size, new_size), color)

    # Paste resized image centered
    paste_x = (new_size - nw) // 2
    paste_y = (new_size - nh) // 2
    new_img.paste(img_resized, (paste_x, paste_y))

    return np.array(new_img)


async def solveImageCaptcha(captcha_url, letter_count, session):
    try:
        # get img, aiohttp session passed from main file
        # iam not making the mistake of making session each time lol.
        async with session.get(captcha_url) as resp:
            if resp.status == 200 and "image" in resp.headers.get("Content-Type", ""):
                large_image = Image.open(io.BytesIO(await resp.read())).convert("RGB")
                large_array = np.array(large_image)

            else:
                print("Failed to fetch a valid image.")
                return ""

    except Exception as e:
        print(f"Error fetching the captcha image: {e}")
        return ""

    img = large_array
    img = letterbox(img, IMG_SIZE)
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)

    # Actual detection part
    outputs = onnx_session.run(None, {input_name: img})[0]
    detections_raw = outputs[0]

    detections = []

    for det in detections_raw:
        x1, y1, x2, y2, conf, cls_id = det

        if conf < CONF_THRES:
            continue

        detections.append(
            {
                "char": CLASSES[int(cls_id)],
                "conf": float(conf),
                "cx": float((x1 + x2) / 2),
            }
        )

    # If too many characters detected
    if len(detections) > letter_count:
        detections.sort(key=lambda d: d["conf"], reverse=True)
        # Keep only the top ones
        detections = detections[:letter_count]

    # Sort based on ltr
    detections.sort(key=lambda d: d["cx"])

    captcha = "".join(d["char"] for d in detections)

    return captcha
