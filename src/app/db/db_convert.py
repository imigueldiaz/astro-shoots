import csv
import json
import re
from html import unescape

"""
Converts a CSV file to a JSON file.

Args:
    csv_file_path (str): The path to the CSV file.
    json_file_path (str): The path to the JSON file.

Returns:
    None
"""


def csv_to_json(csv_file_path, json_file_path):
    json_data = []

    with open(csv_file_path, mode="r", encoding="utf-8") as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=";")

        fieldnames = [field.lower().replace(" ", "_") for field in csvreader.fieldnames]

        for row in csvreader:
            new_row = {}

            for i, (key, value) in enumerate(row.items()):
                new_key = fieldnames[i]
                new_value = unescape(value.strip()) if value else None
                new_row[new_key] = new_value

            focal_length = row.get("focal_length_(35mm_equiv.)")
            if focal_length:
                new_row["focal_length_35"] = focal_length
                del new_row["focal_length_(35mm_equiv.)"]

            max_aperture = row.get("max._aperture_(35mm_equiv.)")
            if max_aperture:
                new_row["max_aperture_35"] = max_aperture
                del new_row["max._aperture_(35mm_equiv.)"]

            sensor_size = new_row.get("sensor_size")
            if sensor_size:
                sensor_size_match = re.search(r"([\d.]+) x ([\d.]+)", sensor_size)
                if sensor_size_match:
                    new_row["sensor_size_w"] = float(sensor_size_match.group(1))
                    new_row["sensor_size_h"] = float(sensor_size_match.group(2))

            sensor_resolution = new_row.get("sensor_resolution")
            if sensor_resolution:
                # Extract numeric values from the string using regular expressions
                matches = re.findall(r"\d+\.\d+|\d+", sensor_resolution)
                if len(matches) > 1:
                    new_row["sensor_px_w"] = int(matches[0])
                    new_row["sensor_px_h"] = int(matches[1])

            iso = new_row.get("iso")
            if iso:
                new_row["iso"] = [x.strip() for x in iso.split(",")]

            for key, value in new_row.items():
                if value == "Yes" or value == "yes":
                    new_row[key] = True
                elif value == "No" or value == "no":
                    new_row[key] = False

            json_data.append(new_row)

    with open(json_file_path, "w", encoding="utf-8") as jsonfile:
        json.dump(json_data, jsonfile, ensure_ascii=False, indent=4)


# Example usage
csv_to_json("cameras-all.csv", "cameras-all.json")
