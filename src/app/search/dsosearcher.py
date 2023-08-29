from typing import List

from pyongc.ongc import Dso, _queryFetchMany, _queryFetchOne


class DsoSearcher:
    @staticmethod
    def search(partial_name: str) -> list[str]:
        """
        Searches for Dso objects based on a partial name.

        Args:
            partial_name (str): The partial name to search for.

        Returns:
            List[Dso]: A list of Dso objects that match the partial name.
        """

        # Convert partial_name to uppercase to handle 'm' or 'ngc' in lowercase
        partial_name = partial_name.upper()

        # Define the columns, tables, and parameters for the query
        cols = "*"
        tables = "objects"
        params = f'(name LIKE "%{partial_name}%" OR commonnames LIKE "%{partial_name}%") AND type != "Dup"'

        # If the partial name starts with "M" or "NGC" followed by digits
        if partial_name.startswith("M") and partial_name[1:].isdigit():
            messier_number = partial_name[1:].zfill(3)
            params += f' OR (messier="{messier_number}" AND type != "Dup")'
        elif partial_name.startswith("NGC") and partial_name[3:].isdigit():
            ngc_number = partial_name[3:].zfill(4)
            params += f' OR ((name LIKE "NGC{ngc_number}%" OR ngc LIKE "{ngc_number}%") AND type != "Dup")'

        # Use the _queryFetchMany function to execute the query
        results = _queryFetchMany(cols, tables, params)

        # Convert the results into a list of Dso objects
        dso_objects = [Dso(name=result[1]).to_json() for result in results]

        return dso_objects

    @staticmethod
    def count_objects(omit_dupes: bool = True) -> int:
        """
        Counts the number of objects in the 'objects' table.

        Args:
            omit_dupes (bool): Indicates if duplicates should be omitted

        Returns:
            int: The count of objects.

        Raises:
            None
        """
        # Define the columns, tables, and parameters for the query
        cols = "COUNT(*)"
        tables = "objects"
        params = (
            'type != "Dup"' if omit_dupes else "1 = 1"
        )  # ! We omit Duplicates if needed

        # Use the _queryFetchOne function to execute the query
        count = _queryFetchOne(cols, tables, params)

        # Return the count (the first element of the result)
        return count[0]

    @staticmethod
    def get(object_id) -> str:
        """
        Retrieves a Dso object based on the provided `object_id`.

        Args:
            object_id (str): The identifier of the object.

        Returns:
            Dso: The Dso object corresponding to the given `object_id`.
        """
        return Dso(name=object_id).to_json()
