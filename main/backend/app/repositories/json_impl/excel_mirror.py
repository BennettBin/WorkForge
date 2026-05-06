from pathlib import Path
import json


class ExcelMirrorStore:
    """
    Writes JSON repository snapshots into an Excel workbook.
    This keeps the MVP requirement of JSON + Excel storage strategy.
    """

    def __init__(self, output_file: Path):
        self.output_file = output_file
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

    def write_snapshot(self, sheets: dict[str, list[dict]]) -> None:
        try:
            from openpyxl import Workbook
        except ImportError:
            fallback = self.output_file.with_suffix(".json")
            fallback.write_text(json.dumps(sheets, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            return

        wb = Workbook()
        default_ws = wb.active
        wb.remove(default_ws)

        for sheet_name, rows in sheets.items():
            ws = wb.create_sheet(title=sheet_name[:31] if sheet_name else "Sheet")
            if not rows:
                ws.append(["empty"])
                continue

            headers = list(rows[0].keys())
            ws.append(headers)
            for row in rows:
                ws.append([row.get(h) for h in headers])

        wb.save(self.output_file)
