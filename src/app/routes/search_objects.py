import json
from operator import itemgetter
from typing import Any

from flask import Blueprint, request, jsonify

from app.search.dsosearcher import DsoSearcher
from app.utils.logger import log_exceptions


def create_search_objects_blueprint(
    app,
    route,
):
    search_objects_bp = Blueprint("search_objects", __name__)

    @log_exceptions(app)
    @search_objects_bp.route(f"{route}/search_objects", methods=["GET", "POST"])
    def search_objects():
        query = request.args.get("q")
        if not query:
            return jsonify([])

        # Using DsoSearcher to perform the search (returns JSON strings)
        results = DsoSearcher.search(partial_name=query)
        if not results:  # Handling the case where no results are found
            return jsonify([])

        # Parsing the JSON strings into dictionaries
        result: str
        parsed_results: list[Any] = [json.loads(result) for result in results]

        # Constructing the suggestions in the same structure as before
        suggestions = []
        for obj in parsed_results:
            object_type = obj["type"]
            other_identifiers = obj.get("other identifiers", {})
            common_names = other_identifiers.get("common names")
            if common_names:
                common_name = f"{common_names[0]}"
            else:
                common_name = ""

            suggestions.append(
                {
                    "text": f"<strong>{obj['name']}</strong> - <em>{common_name}</em> <small>({object_type})</small>",
                    "value": obj["name"],
                    "type": object_type,
                }
            )

        # Sort filtered_cameras by type and name
        sorted_filtered_objects = sorted(suggestions, key=itemgetter("type", "value"))

        return jsonify(sorted_filtered_objects)

    return search_objects_bp
