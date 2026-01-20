"""Export utilities for CSV and Excel"""

import pandas as pd
import io
from datetime import datetime
from typing import Optional


def export_to_csv(df: pd.DataFrame) -> bytes:
    """
    Export DataFrame to CSV bytes.

    Args:
        df: DataFrame to export

    Returns:
        CSV file as bytes
    """
    return df.to_csv(index=False).encode('utf-8')


def export_to_excel(df: pd.DataFrame, sheet_name: str = "Squeeze Scanner") -> bytes:
    """
    Export DataFrame to Excel bytes with formatting.

    Args:
        df: DataFrame to export
        sheet_name: Excel sheet name

    Returns:
        Excel file as bytes
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter

            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass

            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    return output.getvalue()


def get_export_filename(prefix: str = "squeeze_scanner", extension: str = "csv") -> str:
    """
    Generate export filename with timestamp.

    Args:
        prefix: Filename prefix
        extension: File extension

    Returns:
        Filename string
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{timestamp}.{extension}"


def format_scan_results_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format scan results DataFrame for export.

    Args:
        df: Raw scan results DataFrame

    Returns:
        Formatted DataFrame
    """
    if df.empty:
        return df

    export_df = df.copy()

    # Rename columns for better readability
    column_mapping = {
        'symbol': 'Symbol',
        'company_name': 'Company',
        'current_price': 'Price (₹)',
        'price_change_pct': 'Change (%)',
        'squeeze_on': 'Squeeze Active',
        'squeeze_fire': 'Squeeze Fired',
        'squeeze_duration': 'Squeeze Days',
        'momentum': 'Momentum',
        'momentum_direction': 'Direction',
        'bb_width': 'BB Width (%)',
        'volume': 'Volume'
    }

    export_df = export_df.rename(columns=column_mapping)

    # Format boolean columns
    if 'Squeeze Active' in export_df.columns:
        export_df['Squeeze Active'] = export_df['Squeeze Active'].map({True: 'Yes', False: 'No'})
    if 'Squeeze Fired' in export_df.columns:
        export_df['Squeeze Fired'] = export_df['Squeeze Fired'].map({True: 'Yes', False: 'No'})

    return export_df
