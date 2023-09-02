from flask import Blueprint, jsonify, request

from app.utils.logger import log_exceptions


def create_camera_blueprint(app, route, cameras):
    camera_bp = Blueprint("camera", __name__)

    @log_exceptions(app)
    @camera_bp.route(f"{route}/cameras", methods=["GET"])
    def cameras_list():
        query = request.args.get("q", "").lower()

        if len(query) < 3:
            return jsonify([])

        filtered_cameras = [
            {
                "brand": camera.brand,
                "model": camera.model,
                "also_known_as": camera.also_known_as,
                "url": camera.url,
                "image_url": camera.image_url,
                "sensor_width_mm": camera.sensor_size_w,
                "sensor_height_mm": camera.sensor_size_h,
                "number_of_pixels_in_width": camera.sensor_px_w,
                "number_of_pixels_in_height": camera.sensor_px_h,
                "text": f"<strong>{camera.model}</strong> ({camera.brand})",
                "value": camera.model,
            }
            for camera in cameras
            if query in (camera.brand if camera.brand else "").lower()
            or query in (camera.model if camera.model else "").lower()
            or query in (camera.also_known_as if camera.also_known_as else "").lower()
        ]

        return jsonify(filtered_cameras)

    return camera_bp
