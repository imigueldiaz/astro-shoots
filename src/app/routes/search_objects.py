import json
from flask import Blueprint, request, jsonify

from app.search.dsosearcher import DsoSearcher


def create_search_objects_blueprint(
    ROUTE,
):
    search_objects_bp = Blueprint("search_objects", __name__)

    @search_objects_bp.route(f"{ROUTE}/search_objects", methods=["GET", "POST"])
    def search_objects():
        query = request.args.get("query")
        if len(query) < 3:
            return jsonify([])

        # Using DsoSearcher to perform the search (returns JSON strings)
        results = DsoSearcher.search(partial_name=query)
        if not results:  # Handling the case where no results are found
            return jsonify([])

        # Parsing the JSON strings into dictionaries
        parsed_results = [json.loads(result) for result in results]

        # Constructing the suggestions in the same structure as before
        suggestions = []
        for obj in parsed_results:
            other_identifiers = obj.get("other identifiers", {})
            common_names = other_identifiers.get("common names")
            if common_names:
                common_name = common_names[0]
            else:
                common_name = obj["type"]

            suggestions.append(
                {
                    "name": f"{obj['name']} ({common_name})",
                    "id": obj["name"],
                }
            )

        return jsonify(suggestions)

    return search_objects_bp