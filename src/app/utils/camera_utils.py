import json

from app.db.Camera import Camera


def load_cameras_from_json(file_path):
    cameras = []
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            camera = Camera(
                item.get("sensor_size_w", None),
                item.get("sensor_size_h", None),
                item.get("sensor_px_w", None),
                item.get("sensor_px_h", None),
                item.get("url", None),
                item.get("image_url", None),
                item.get("brand", None),
                item.get("model", None),
                item.get("iso", None),
                item.get("also_known_as", None),
                item.get("year", None),
                item.get("max_aperture", None),
                item.get("crop_factor", None),
            )
            cameras.append(camera)

    return cameras
