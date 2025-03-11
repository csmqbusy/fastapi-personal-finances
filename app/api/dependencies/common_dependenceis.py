from fastapi import Query


def get_csv_params(
    in_csv: bool | None = Query(None, description="Get data in csv format"),
) -> bool:
    return bool(in_csv)
