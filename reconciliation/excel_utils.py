import pandas as pd


def clean_column_name(column):
    column = str(column)

    # Fix incorrectly decoded UTF-8 characters
    try:
        column = column.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

    column = column.strip()
    column = ' '.join(column.split())

    return column


def read_excel_file(file, header_row):
    try:
        df = pd.read_excel(file, header=header_row)

        df.columns = [
            clean_column_name(column)
            for column in df.columns
        ]

        return df, None

    except Exception as e:
        return None, str(e)