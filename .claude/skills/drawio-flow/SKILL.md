---
name: drawio-flow
description: Create, edit or read draw.io (.drawio, diagrams.net) diagrams, especially flow diagrams in the team's soft blue style on the standard A4 page. Use this whenever the user asks for a diagram in DrawIO or draw.io, wants an editable diagram file to open and rearrange, wants a Mermaid diagram converted to draw.io, or hands you a .drawio file to read or change, even if they do not name the skill.
---

# draw.io flow diagrams

Mermaid is the quick text sketch (see the `mermaid-preview` skill). A `.drawio` file is what colleagues open, rearrange and present. Both use the same look, so a sketch can become an editable diagram without being redrawn by hand.

## Workflow

1. Settle the boxes and connectors. If the diagram already exists as Mermaid, reuse its labels and order.
2. Write a spec file (JSON) in your scratchpad directory. `assets/example-spec.json` is a complete example: copy it and change it.
3. Run `python3 scripts/drawio_tool.py build spec.json out.drawio` from this skill folder. It writes the file with the team style and A4 page, and stops with an error if a connector points at a missing box or two boxes overlap. It also reports how many A4 pages the diagram spans.
4. Deliver the file with `SendUserFile`. Save it into the repo only when the user asks. Diagram sources go in `02.Diagramms/`. Ask if the repo uses a different folder, and do not invent one.
5. Say that you could not open it in draw.io. The script checks structure, not appearance, so ask the user to report connectors that route badly.

## Spec format

- `name`: the diagram's name, shown as the tab name in draw.io.
- `page`: optional `width` and `height`. Leave it out for the standard page (see below).
- `nodes`: each has `id`, `label`, `x`, `y`, optional `w` and `h` (default 200 by 60) and `dashed`. Use `<br>` for line breaks in labels.
- `edges`: each has `from` and `to`, and optionally `label`, `exit` and `entry` (where the connector leaves and enters a box, as `[x, y]` fractions with `[1, 0.5]` for the middle of the right side and `[0, 0.5]` for the middle of the left side), and `points` (waypoints for a connector that has to go around).

Do not hand-write style strings. The script applies the same style every time, and that consistency is why the team's diagrams look alike: soft blue rounded boxes with bold dark blue text, dashed pale boxes for gates, reviews and later items, and thin grey right-angle connectors with small arrowheads.

## Layout rules

- Flow left to right. Boxes are 180 to 200 wide and 60 high, with two-line labels.
- Leave 70 between boxes, and 110 where a connector carries a label, since the label needs room.
- Put a second row about 150 below the first. A box that receives from both rows sits between them.
- Two connectors into the same box should enter at different heights, for example `[0, 0.25]` and `[0, 0.75]`, so they do not merge.
- For a loop back, exit and enter at the bottom (`[0.5, 1]` for both) and add two waypoints about 60 below the lowest box in between.
- Use dashed boxes for approvals, gates, reviews and anything optional or planned for later.

## Page setup

Use draw.io's standard A4 portrait page, 827 by 1169. The diagram may be wider or taller than one page. Do not shrink the page or the diagram to make it fit. Use another size only when the user names it, such as A4 landscape (1169 by 827) or Letter (850 by 1100), and then set it under `page` in the spec.

## Reading and changing existing files

`python3 scripts/drawio_tool.py inspect file.drawio` lists the boxes and connectors, and it also reads files whose diagram data is compressed.

For a small change to an uncompressed file, edit the XML in place and keep the existing style strings. For a compressed file, or a larger change, inspect it, write a spec that reproduces it, build a new file next to the original, and say so. Never overwrite a file the user supplied unless they ask you to.

## Limits

- Nothing here can render draw.io, so layout and connector routing are unverified until the user opens the file.
- draw.io cannot round the border of an edge label, so labels are thin rectangles, not the pills used in the Mermaid version.
- The compressed-file reader follows draw.io's documented encoding but has been tested only on files encoded the same way, not on a real draw.io export.
