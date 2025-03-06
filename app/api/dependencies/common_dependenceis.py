from fastapi import Query


def get_csv_params(
    in_csv: bool = Query(False, description="Get data in csv format"),
) -> bool:
    return in_csv
