"""Render the automatically created AWS resources as a layered resource graph.

Reads dependency/template.json (the same dependency templates the deployer uses
for plan analysis) and writes a self-contained SVG. Resources are grouped into
functional units, units are placed in the paper's five layers, and an edge
A -> B means "a resource of B is created after a resource of A".

Usage:
  python scripts/resource_graph_figure.py [--input PATH] [--output PATH]
Convert for the paper with: inkscape resource_graph.svg --export-type=pdf
"""
from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path
from xml.sax.saxutils import escape

DEFAULT_INPUT = Path("dependency") / "template.json"
DEFAULT_OUTPUT = Path("docs") / "figures" / "resource_graph.svg"

# Template id prefix (after "<group>:<layer>:") -> functional unit. Longest prefix wins.
UNIT_PREFIXES = {
  "dispatcher": "dispatcher",
  "iot_": "iot_device",
  "init_value": "init_values",
  "hot_dynamodb": "hot_storage",
  "hot_cold_mover": "hot_cold_mover",
  "hot_reader": "hot_reader",
  "cold_s3": "cold_storage",
  "cold_archive_mover": "cold_archive_mover",
  "archive_s3": "archive_storage",
  "persister": "persister",
  "processor": "processor",
  "event_checker": "event_checker",
  "event_feedback": "event_feedback",
  "lambda_chain": "lambda_chain",
  "event_action": "event_action",
  "twinmaker_workspace": "twinmaker_workspace",
  "twinmaker_s3": "twinmaker_workspace",
  "twinmaker_iam": "twinmaker_workspace",
  "device_component_type": "component_type",
  "twinmaker_hierarchy": "hierarchy",
  "twinmaker_entity": "hierarchy",
  "twinmaker_component": "hierarchy",
  "grafana": "grafana",
}

# Names that would otherwise fall into a longer-lived prefix group.
EXACT_UNITS = {
  "iot_policy": "iot_policy",
  "iot_policy_version": "iot_policy",
}

# unit -> (title, column, multiplicity note)
UNITS = OrderedDict([
  ("dispatcher", ("Dispatcher", 0, "")),
  ("iot_policy", ("Shared IoT policy", 0, "once per twin")),
  ("iot_device", ("IoT device identity", 0, "per device (D)")),
  ("init_values", ("Initial values", 0, "per device (V)")),
  ("hot_storage", ("Hot storage", 1, "")),
  ("hot_cold_mover", ("Hot-to-Cold Mover", 1, "")),
  ("cold_storage", ("Cold storage", 1, "")),
  ("cold_archive_mover", ("Cold-to-Archive Mover", 1, "")),
  ("archive_storage", ("Archive storage", 1, "")),
  ("hot_reader", ("Hot Reader", 1, "")),
  ("processor", ("Device processor", 2, "per device (D)")),
  ("persister", ("Persister", 2, "")),
  ("event_checker", ("Event Checker", 2, "")),
  ("event_feedback", ("Event Feedback", 2, "")),
  ("lambda_chain", ("Lambda Chain", 2, "")),
  ("event_action", ("Event action", 2, "per internal action (A)")),
  ("twinmaker_workspace", ("TwinMaker workspace", 3, "")),
  ("component_type", ("Device component type", 3, "per distinct type (T \u2264 D)")),
  ("hierarchy", ("Entity hierarchy", 3, "per entity / component (H, C)")),
  ("grafana", ("Grafana workspace", 4, "optional (G): DEPLOY_MANAGED_GRAFANA")),
])

COLUMNS = [
  "Layer 1\nData Acquisition",
  "Layer 2\nData Storage",
  "Layer 3\nData Processing",
  "Layer 4\nTwin Management",
  "Layer 5\nVisualization",
]

# resource type (last template-id segment) -> (label, color)
TYPES = {
  "iam": ("IAM role", "#8a6d3b"),
  "iam_managed_policy_attachment": ("Managed policy attachment", "#c9a66b"),
  "iam_inline_policy": ("Inline policy", "#c9a66b"),
  "iam_trust_policy": ("Trust policy", "#c9a66b"),
  "lambda_function": ("Lambda function", "#e07b39"),
  "lambda_permission": ("Lambda invoke permission", "#f0b27a"),
  "iot_rule": ("IoT topic rule", "#2e8b57"),
  "iot_thing": ("IoT Thing", "#2e8b57"),
  "iot_certificate": ("IoT certificate", "#5fb98a"),
  "iot_certificate_attachment": ("Certificate attachment", "#5fb98a"),
  "iot_policy": ("IoT policy", "#5fb98a"),
  "iot_policy_version": ("IoT policy version", "#5fb98a"),
  "iot_policy_attachment": ("Policy attachment", "#5fb98a"),
  "local_auth_files": ("Local auth files", "#9aa5a0"),
  "iot_message": ("MQTT publish", "#2e8b57"),
  "init_value": ("Init value", "#9aa5a0"),
  "dynamodb_table": ("DynamoDB table", "#3b6fb6"),
  "dynamodb_backup": ("DynamoDB backup", "#7ba3d9"),
  "s3_bucket": ("S3 bucket", "#3f9d9d"),
  "s3_bucket_cors": ("S3 CORS config", "#7cc4c4"),
  "s3_bucket_policy": ("S3 bucket policy", "#7cc4c4"),
  "eventbridge_rule": ("EventBridge rule", "#b04a8f"),
  "eventbridge_target": ("EventBridge target", "#d68fbe"),
  "step_function": ("Step Functions state machine", "#8e5bb5"),
  "event_action": ("Event action", "#9aa5a0"),
  "twinmaker_workspace": ("TwinMaker workspace", "#c0392b"),
  "twinmaker_scene": ("TwinMaker scene cleanup", "#e6a199"),
  "twinmaker_entity": ("TwinMaker entities", "#d9665a"),
  "twinmaker_component_type": ("TwinMaker component type", "#d9665a"),
  "twinmaker_component": ("TwinMaker components", "#d9665a"),
  "twinmaker_hierarchy": ("TwinMaker hierarchy", "#d9665a"),
  "grafana_workspace": ("Managed Grafana workspace", "#c0392b"),
}

# Resource families: each has its own marker shape AND an Okabe-Ito color, so the
# figure stays readable for color-blind readers and in grayscale.
FAMILIES = OrderedDict([
  ("access", ("Access (IAM roles, policies)", "square", "#E69F00")),
  ("compute", ("Compute (Lambda, Step Functions)", "triangle", "#D55E00")),
  ("iot", ("IoT Core (rules, identities, messages)", "diamond", "#009E73")),
  ("data", ("Data stores (DynamoDB, S3)", "circle", "#0072B2")),
  ("schedule", ("Scheduling (EventBridge)", "cross", "#CC79A7")),
  ("twin", ("Twin and visualization (TwinMaker, Grafana)", "hexagon", "#56B4E9")),
  ("config", ("Configuration and local files", "pentagon", "#666666")),
])

FAMILY_OF = {
  "iam": "access", "iam_managed_policy_attachment": "access", "iam_inline_policy": "access",
  "iam_trust_policy": "access",
  "lambda_function": "compute", "lambda_permission": "compute", "step_function": "compute",
  "iot_rule": "iot", "iot_thing": "iot", "iot_certificate": "iot",
  "iot_certificate_attachment": "iot", "iot_policy": "iot", "iot_policy_version": "iot",
  "iot_policy_attachment": "iot", "iot_message": "iot",
  "dynamodb_table": "data", "dynamodb_backup": "data", "s3_bucket": "data", "s3_bucket_cors": "data",
  "s3_bucket_policy": "data",
  "eventbridge_rule": "schedule", "eventbridge_target": "schedule",
  "twinmaker_workspace": "twin", "twinmaker_scene": "twin", "twinmaker_entity": "twin",
  "twinmaker_component_type": "twin", "twinmaker_component": "twin", "twinmaker_hierarchy": "twin",
  "grafana_workspace": "twin",
  "local_auth_files": "config", "init_value": "config", "event_action": "config",
}


def marker(shape: str, cx: float, cy: float, color: str, hollow: bool, r: float = 6) -> str:
  """SVG marker of the given shape centered at (cx, cy)."""
  fill = "#ffffff" if hollow else color
  style = f'fill="{fill}" stroke="{color}" stroke-width="1.6" stroke-linejoin="round"'
  if shape == "circle":
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" {style}/>'
  if shape == "square":
    return f'<rect x="{cx - r + 0.5}" y="{cy - r + 0.5}" width="{2 * r - 1}" height="{2 * r - 1}" {style}/>'
  if shape == "triangle":
    points = [(cx, cy - r - 0.5), (cx + r + 0.5, cy + r - 1), (cx - r - 0.5, cy + r - 1)]
  elif shape == "diamond":
    points = [(cx, cy - r - 1), (cx + r + 1, cy), (cx, cy + r + 1), (cx - r - 1, cy)]
  elif shape == "hexagon":
    points = [(cx - r, cy), (cx - r / 2, cy - r), (cx + r / 2, cy - r),
              (cx + r, cy), (cx + r / 2, cy + r), (cx - r / 2, cy + r)]
  elif shape == "pentagon":
    points = [(cx, cy - r - 0.5), (cx + r + 0.5, cy - 1), (cx + r - 1.5, cy + r),
              (cx - r + 1.5, cy + r), (cx - r - 0.5, cy - 1)]
  elif shape == "cross":
    t = r / 2.6
    points = [(cx - t, cy - r), (cx + t, cy - r), (cx + t, cy - t), (cx + r, cy - t),
              (cx + r, cy + t), (cx + t, cy + t), (cx + t, cy + r), (cx - t, cy + r),
              (cx - t, cy + t), (cx - r, cy + t), (cx - r, cy - t), (cx - t, cy - t)]
  else:
    raise ValueError(f"Unknown marker shape '{shape}'")
  joined = " ".join(f"{px:.1f},{py:.1f}" for px, py in points)
  return f'<polygon points="{joined}" {style}/>'


# Units that exist only when enabled, and single resources that exist only under a condition.
OPTIONAL_UNITS = {"grafana"}
CONDITIONAL_RESOURCES = {
  "core:l2:event_feedback_iam_inline_policy:iam_inline_policy": "if feedback (F)",
}

# Managed-policy attachments that attach two policies (read from the role deployers).
DOUBLE_ATTACHMENTS = {
  "dispatcher_iam_managed_policy_attachment",
  "lambda_chain_iam_managed_policy_attachment",
  "processor_iam_managed_policy_attachment",
}
# Entries that are not AWS resources counted in the resource formula.
NOT_COUNTED = {
  "local_auth_files": "local files",
  "init_value": "configuration",
  "iot_message": "message, not a resource",
  "event_action": "configuration",
  "dynamodb_backup": "setting",
  "iam_trust_policy": "part of the role",
  "iot_policy_version": "implicit child",
}

# Units whose incoming edges are runtime message paths, not configuration references.
RUNTIME_PATH_TARGETS = {"init_values"}

CARD_W = 214
ROW_H = 17
HEAD_H = 34
GAP = 22
COL_GAP = 120
MARGIN = 24
TOP = 70


def unit_of(template_id: str) -> str:
  name = template_id.split(":")[2]
  if name in EXACT_UNITS:
    return EXACT_UNITS[name]
  best = ""
  for prefix in UNIT_PREFIXES:
    if name.startswith(prefix) and len(prefix) > len(best):
      best = prefix
  if not best:
    raise ValueError(f"No unit mapping for template '{template_id}'")
  return UNIT_PREFIXES[best]


def type_of(template_id: str) -> str:
  key = template_id.split(":")[3]
  if key not in TYPES:
    raise ValueError(f"No type style for '{key}' in '{template_id}'")
  return key


def load(path: Path):
  templates = json.loads(path.read_text(encoding="utf-8"))["templates"]
  members: dict[str, list[dict]] = {u: [] for u in UNITS}
  for template in templates:
    unit = unit_of(template["id"])
    if unit not in members:
      raise ValueError(f"Unit '{unit}' missing from UNITS")
    members[unit].append(template)

  edges: OrderedDict[tuple[str, str], int] = OrderedDict()
  for template in templates:
    target = unit_of(template["id"])
    for dep in template["depends_on"]:
      source = unit_of(dep["id"])
      if source != target:
        edges[(source, target)] = edges.get((source, target), 0) + 1
  return templates, members, reduce_transitive(edges)


def reduce_transitive(edges):
  """Drop A->C when C is also reachable from A through another unit."""
  successors: dict[str, set[str]] = {}
  for source, target in edges:
    successors.setdefault(source, set()).add(target)

  def reachable(start: str, skip: tuple[str, str]) -> set[str]:
    seen: set[str] = set()
    stack = [n for n in successors.get(start, ()) if (start, n) != skip]
    while stack:
      node = stack.pop()
      if node in seen:
        continue
      seen.add(node)
      stack.extend(successors.get(node, ()))
    return seen

  kept = OrderedDict()
  for (source, target), count in edges.items():
    if target not in reachable(source, (source, target)):
      kept[(source, target)] = count
  return kept


def layout(members):
  boxes = {}
  col_heights = []
  per_col: dict[int, list[str]] = {i: [] for i in range(len(COLUMNS))}
  for unit, (_, col, _) in UNITS.items():
    per_col[col].append(unit)

  for col, units in per_col.items():
    y = TOP
    for unit in units:
      h = HEAD_H + ROW_H * len(members[unit]) + 8
      x = MARGIN + col * (CARD_W + COL_GAP)
      boxes[unit] = [x, y, CARD_W, h]
      y += h + GAP
    col_heights.append(y)
  # center shorter columns vertically
  total = max(col_heights)
  for col, units in per_col.items():
    shift = (total - col_heights[col]) / 2
    for unit in units:
      boxes[unit][1] += shift
  width = MARGIN * 2 + len(COLUMNS) * CARD_W + (len(COLUMNS) - 1) * COL_GAP
  return boxes, width, total + 130


def render(templates, members, edges) -> str:
  boxes, width, height = layout(members)
  out: list[str] = []
  add = out.append
  add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
      f'viewBox="0 0 {width} {height}" font-family="Helvetica, Arial, sans-serif">')
  add('<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
      'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#555"/></marker></defs>')
  add(f'<rect width="{width}" height="{height}" fill="#ffffff"/>')

  # column headers and lanes
  for i, label in enumerate(COLUMNS):
    x = MARGIN + i * (CARD_W + COL_GAP)
    add(f'<rect x="{x - 10}" y="8" width="{CARD_W + 20}" height="{height - 16}" rx="8" '
        f'fill="#f5f6f8" stroke="#dde0e5"/>')
    first, second = label.split("\n")
    add(f'<text x="{x + CARD_W / 2}" y="30" text-anchor="middle" font-size="13" font-weight="700" fill="#333">{escape(first)}</text>')
    add(f'<text x="{x + CARD_W / 2}" y="46" text-anchor="middle" font-size="12" fill="#555">{escape(second)}</text>')

  # edges (behind cards)
  slots: dict[tuple[str, str], int] = {}
  for (source, target), _count in edges.items():
    sx, sy, sw, sh = boxes[source]
    tx, ty, tw, th = boxes[target]
    scol, tcol = UNITS[source][1], UNITS[target][1]
    n_out = slots.get((source, "out"), 0)
    n_in = slots.get((target, "in"), 0)
    slots[(source, "out")] = n_out + 1
    slots[(target, "in")] = n_in + 1
    if scol < tcol:
      x1, x2 = sx + sw, tx
    elif scol > tcol:
      x1, x2 = sx, tx + tw
    else:
      x1, x2 = sx + sw, tx + tw
    y1 = sy + 14 + (n_out % 6) * 7
    y2 = ty + 14 + (n_in % 6) * 7
    if scol == tcol:
      bulge = 36 + 6 * (n_out % 3)
      d = f"M{x1},{y1} C{x1 + bulge},{y1} {x2 + bulge},{y2} {x2},{y2}"
    else:
      dx = (x2 - x1) / 2
      d = f"M{x1},{y1} C{x1 + dx},{y1} {x2 - dx},{y2} {x2},{y2}"
    runtime = ' stroke-dasharray="5,3"' if target in RUNTIME_PATH_TARGETS else ""
    add(f'<path d="{d}" fill="none" stroke="#555" stroke-opacity="0.55" stroke-width="1.2"{runtime} marker-end="url(#arrow)"/>')

  # cards
  used_types: OrderedDict[str, None] = OrderedDict()
  for unit, (title, _col, note) in UNITS.items():
    x, y, w, h = boxes[unit]
    dashed = ' stroke-dasharray="5,3"' if unit in OPTIONAL_UNITS else ""
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#ffffff" stroke="#7a8190" stroke-width="1.2"{dashed}/>')
    add(f'<text x="{x + 10}" y="{y + 16}" font-size="12.5" font-weight="700" fill="#222">{escape(title)}</text>')
    if note:
      add(f'<text x="{x + 10}" y="{y + 29}" font-size="9.5" font-style="italic" fill="#666">{escape(note)}</text>')
    for i, template in enumerate(members[unit]):
      key = type_of(template["id"])
      label = TYPES[key][0]
      _family_label, shape_name, color = FAMILIES[FAMILY_OF[key]]
      used_types[key] = None
      cy = y + HEAD_H + ROW_H * i + 9
      lifecycle = template.get("lifecycle_artifact")
      add(marker(shape_name, x + 15, cy, color, bool(lifecycle)))
      name = template["id"].split(":")[2]
      note_text = ""
      if name in DOUBLE_ATTACHMENTS:
        label += " \u00d72"
      if "cleanup" in name:
        note_text = "destroy only"
      elif key in NOT_COUNTED:
        note_text = "not counted"
      text = label
      if template["id"] in CONDITIONAL_RESOURCES:
        text += f" \u2013 {CONDITIONAL_RESOURCES[template['id']]}"
      if note_text:
        add(f'<text x="{x + 27}" y="{cy + 4}" font-size="10.5" fill="#333">{escape(text)} '
            f'<tspan fill="#777" font-style="italic" font-size="9">({escape(note_text)})</tspan></text>')
      else:
        add(f'<text x="{x + 27}" y="{cy + 4}" font-size="10.5" fill="#333">{escape(text)}</text>')

  # legend: one entry per family (shape + color), then the arrow / hollow notes
  lx = MARGIN
  ly = height - 78
  add(f'<text x="{lx}" y="{ly}" font-size="10" font-weight="700" fill="#333">Resource family</text>')
  cursor = lx + 100
  for label, shape_name, color in FAMILIES.values():
    add(marker(shape_name, cursor + 6, ly - 3, color, False, 5))
    add(f'<text x="{cursor + 17}" y="{ly}" font-size="10" fill="#333">{escape(label)}</text>')
    cursor += 17 + len(label) * 5.4 + 22
  add(marker("circle", lx + 6, ly + 20, "#444444", True, 5))
  add(f'<text x="{lx + 17}" y="{ly + 23}" font-size="10" fill="#333">Hollow marker: lifecycle artifact '
      f'(invoke permission, backup, cleanup, publish).  '
      f'Dashed card: optional.</text>')
  add(f'<text x="{lx}" y="{ly + 40}" font-size="10" fill="#333">Italic note: not counted in the resource total '
      f'(local file, configuration, message, implicit child) or created only at destroy time.</text>')
  add(f'<text x="{lx + 520}" y="{ly + 23}" font-size="10" fill="#333">Arrow A \u2192 B: B refers to a resource of A and is created after it (dashed: runtime message path).</text>')
  return "\n".join(out) + "\n</svg>\n"


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  parser.add_argument("--input", default=str(DEFAULT_INPUT))
  parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
  args = parser.parse_args()

  templates, members, edges = load(Path(args.input))
  svg = render(templates, members, edges)
  output = Path(args.output)
  output.parent.mkdir(parents=True, exist_ok=True)
  output.write_text(svg, encoding="utf-8")
  print(f"{len(templates)} resource templates, {len(edges)} unit dependencies -> {output}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
