from __future__ import annotations

import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MATERIAL = ROOT / "clawathon_material"
DATA = ROOT / "data"
NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RELNS = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}


def main() -> None:
    DATA.mkdir(exist_ok=True)
    zones = read_ad_zones(MATERIAL / "Camp_Ads_Agent_Ad_Zones_CLEAN.xlsx")
    campaigns = read_campaign_data(MATERIAL / "Camp_Ads_Analytics_Templates_v3.html")
    summary = summarize(campaigns)

    write_json("ad_zones.json", zones)
    write_json("campaign_reports.json", campaigns)
    write_json("report_summary.json", summary)
    print(f"wrote {len(zones)} zones, {len(campaigns)} campaign rows, {summary['total']['reports']} reports")


def read_campaign_data(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"const DATA = (\[.*?\]);\s*\n", text, re.S)
    if not match:
        raise RuntimeError("Could not find const DATA in analytics template")
    return json.loads(match.group(1))


def read_ad_zones(path: Path) -> list[dict[str, Any]]:
    rows = read_xlsx_sheet(path, "Ad Zones")
    header = rows[0]
    items = []
    for row in rows[1:]:
        obj = dict(zip(header, row))
        if not obj.get("Zone ID"):
            continue
        items.append(
            {
                "index": int(float(obj["Index"])),
                "group": obj["Group"],
                "channel": obj["Channel"],
                "zone_id": obj["Zone ID"],
                "position": obj["Position"],
                "format": obj["Format"],
                "size": obj["Size"],
                "reach": int(float(obj["Reach"])),
                "vi_pct": float(obj["VI %"]),
                "ctr_pct": float(obj["CTR %"]),
                "cpm_vnd": int(float(obj["CPM VND"])),
                "objective": str(obj["Objective"]).lower(),
                "note": obj.get("Note", ""),
            }
        )
    return items


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    reports = sorted({r.get("Sheet") for r in records if r.get("Sheet")})
    verdict = {
        "good": sum(1 for r in records if r.get("Verdict") == "good"),
        "watch": sum(1 for r in records if r.get("Verdict") == "watch"),
        "bad": sum(1 for r in records if r.get("Verdict") == "bad"),
    }
    spend = sum(float(r.get("Spend VND") or 0) for r in records)
    revenue = sum(float(r.get("Revenue VND") or r.get("Revenue from Signup") or 0) for r in records)
    by_report = []
    for sheet in reports:
        rows = [r for r in records if r.get("Sheet") == sheet]
        row_spend = sum(float(r.get("Spend VND") or 0) for r in rows)
        row_revenue = sum(float(r.get("Revenue VND") or r.get("Revenue from Signup") or 0) for r in rows)
        by_report.append(
            {
                "sheet": sheet,
                "rows": len(rows),
                "good": sum(1 for r in rows if r.get("Verdict") == "good"),
                "watch": sum(1 for r in rows if r.get("Verdict") == "watch"),
                "bad": sum(1 for r in rows if r.get("Verdict") == "bad"),
                "spend_vnd": int(row_spend),
                "revenue_vnd": int(row_revenue),
                "roas": round(row_revenue / row_spend, 4) if row_spend else 0,
            }
        )
    return {
        "total": {
            "total_records": len(records),
            "reports": len(reports),
            "verdict": verdict,
            "total_spend_vnd": int(spend),
            "total_revenue_vnd": int(revenue),
            "total_roas": round(revenue / spend, 4) if spend else 0,
        },
        "reports": by_report,
    }


def read_xlsx_sheet(path: Path, sheet_name: str) -> list[list[str]]:
    with zipfile.ZipFile(path) as z:
        shared = read_shared_strings(z)
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rid_to_target = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("rel:Relationship", RELNS)}
        for sheet in workbook.findall(".//a:sheet", NS):
            if sheet.attrib["name"] != sheet_name:
                continue
            rid = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            return read_sheet_rows(z, normalize_target(rid_to_target[rid]), shared)
    raise RuntimeError(f"Sheet not found: {sheet_name}")


def read_shared_strings(z: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return [
        "".join((t.text or "") for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))
        for si in root.findall("a:si", NS)
    ]


def read_sheet_rows(z: zipfile.ZipFile, path: str, shared: list[str]) -> list[list[str]]:
    root = ET.fromstring(z.read(path))
    rows = []
    for row in root.findall(".//a:sheetData/a:row", NS):
        values: list[str] = []
        for cell in row.findall("a:c", NS):
            idx = col_idx(cell.attrib.get("r", "A"))
            while len(values) <= idx:
                values.append("")
            values[idx] = cell_value(cell, shared)
        while values and values[-1] == "":
            values.pop()
        if any(str(v).strip() for v in values):
            rows.append(values)
    return rows


def cell_value(cell: ET.Element, shared: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    value = cell.find("a:v", NS)
    if cell_type == "inlineStr":
        return "".join((t.text or "") for t in cell.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))
    if value is None:
        return ""
    raw = value.text or ""
    if cell_type == "s":
        return shared[int(raw)]
    return raw


def col_idx(ref: str) -> int:
    letters = "".join(ch for ch in ref if ch.isalpha())
    out = 0
    for ch in letters:
        out = out * 26 + ord(ch.upper()) - 64
    return max(out - 1, 0)


def normalize_target(target: str) -> str:
    target = target.lstrip("/")
    return target if target.startswith("xl/") else f"xl/{target}"


def write_json(name: str, payload: Any) -> None:
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
