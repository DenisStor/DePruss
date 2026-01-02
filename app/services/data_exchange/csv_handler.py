"""
CSV handling functions for data exchange.
"""
import csv
import io
from typing import List, Any, Iterator, Tuple, Dict


CSV_DELIMITER = ';'


def create_csv_content(headers: List[str], rows: List[List[Any]]) -> str:
    """
    Create CSV content with headers and rows.

    Args:
        headers: List of header names
        rows: List of row data

    Returns:
        CSV content as string
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=CSV_DELIMITER, quoting=csv.QUOTE_ALL)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def read_csv_rows(content: bytes) -> Iterator[Tuple[int, Dict[str, Any]]]:
    """
    Read rows from CSV file.

    Args:
        content: CSV file content as bytes

    Yields:
        Tuple of (row_number, row_dict) for each data row
    """
    text = content.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text), delimiter=CSV_DELIMITER)

    for row_num, row in enumerate(reader, 2):
        yield row_num, row


def create_csv_template(headers: List[str], example_row: List[Any]) -> str:
    """
    Create CSV template with headers and example row.

    Args:
        headers: List of header names
        example_row: Example row data

    Returns:
        CSV template as string
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=CSV_DELIMITER, quoting=csv.QUOTE_ALL)
    writer.writerow(headers)
    writer.writerow(example_row)
    return output.getvalue()
