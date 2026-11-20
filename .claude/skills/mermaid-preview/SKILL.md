---
name: mermaid-preview
description: Show a Mermaid diagram in the chat as an editable widget with Code and Preview buttons, so the user can tweak the diagram text and see it re-rendered on the spot. Use this whenever the user asks for a Mermaid diagram, flowchart, sequence diagram, architecture or process sketch, or wants to edit, adjust or iterate on a diagram interactively, even if they do not say "widget", "preview" or "editor". Also use it when the user pastes Mermaid code and asks what it looks like, or wants to see a diagram larger, full size or in full view.
---

# Mermaid preview and edit widget

Solution Architects iterate on diagrams constantly. A static render means every small change costs a round trip to the chat. This skill puts the diagram text and its rendered result side by side in one widget, so the user can change a label, switch Code and Preview, and only come back to the chat when they want something bigger.

## When to use it

- The user asks for a flowchart, sequence diagram, architecture sketch or any other Mermaid diagram.
- The user pastes Mermaid code and wants to see or adjust it.
- The user says they want to edit a diagram themselves.

Skip the widget when the user only wants Mermaid text to paste into a file and has no need to see it first. Then give the code as described under "Giving the code as plain text".

## How to build it

1. Write the Mermaid code first. Keep it valid for Mermaid 10 (see "Writing diagrams that render reliably").
2. Load the visualizer guidance with `mcp__visualize__read_me` (module `interactive`) before the first widget call. Do this silently, without mentioning it to the user.
3. Read `assets/widget-template.html` from this skill folder. Replace the placeholder `__MERMAID_CODE__` with the diagram code. The code goes inside a `<textarea>`, so replace `&` with `&amp;` and `<` with `&lt;` in the code. Nothing else needs escaping. Also replace the placeholder `__DIAGRAM_ID__` with the snake_case title from the next step. The Full view button quotes that id in its message, which is how you find the right diagram again.
4. Pass the result to `mcp__visualize__show_widget` as `widget_code`. Use a specific snake_case `title`, such as `solution_design_flow`, and use the same text as the `__DIAGRAM_ID__` above. Give each diagram its own id, since several can be in one conversation.
5. Write one short sentence before the widget, and put explanations, assumptions and open questions in normal chat text after it. Keep prose out of the widget itself.

Do not change the template's structure unless the user asks. The Code and Preview buttons, the error line and the "Send to chat" button are the whole point. Do not add comments inside the widget code, because they break streaming.

## What the widget does

- **Preview** renders the diagram with Mermaid 10.9.1, loaded from cdnjs, in the team's flow style (see "Diagram style"). Syntax errors appear as a red line under the diagram instead of a broken picture.
- **Code** shows the editable text. Edits take effect when the user switches back to Preview.
- **Full view** asks you to open the diagram in the full-size editor page (see the next section). The widget cannot grow beyond the chat's width, so a wide diagram would otherwise be cut off. If the user has not edited the code, the button sends only a short message with the diagram id, to keep the chat uncluttered. If the code was edited, it also includes the edited code, because that is the only way the edits can reach you. A widget can talk to the chat only through visible messages, so it cannot pass the code along silently.
- **Send to chat** posts the edited code back as a message. Treat that code as the current version of the diagram from then on. Never fall back to an earlier version you wrote yourself.

Edits made inside the widget exist only in the widget. They are lost if the chat redraws it, and they are never written to a file or repo on their own. If the user wants the diagram saved, they have to send it to the chat first, and then you commit it only when asked.

## Full-size editor page

When the user clicks Full view (the message starts "Open the full-size editor page for the diagram"), or asks to see a diagram larger, bigger or full screen, publish the diagram as a page of its own. A chat widget has a fixed width and cannot go full screen, so a wide diagram is cut off there, while a published page uses the whole browser window.

1. Find the code. If the message includes code (the user edited it), use that. Otherwise the message gives only a diagram id in quotes: take the code from the newest version of the diagram with that id, which is either the last widget you wrote with that title or code the user later sent with Send to chat, whichever is newer. If you cannot find the id, ask the user to send the code. Do not paste the code into your reply when you publish.
2. Read `assets/fullview-template.html`. Replace `__MERMAID_CODE__` with the code, escaped the same way as for the widget (`&` and `<`). Replace both occurrences of `__DIAGRAM_TITLE__` with a short, specific name for the diagram, two to four words, such as "SA AI Pipeline". Write the file to your scratchpad directory as `.html`.
3. Load the `artifact-design` skill, which the Artifact tool requires before a page is written, and then publish the file with the Artifact tool. Use the icon `flowchart` and a one-sentence description. To change the same diagram later, publish the same file path again so the link stays the same.
4. Tell the user in one sentence what the page is. The app shows a card with the link, so do not paste the URL.

The page has code and live preview side by side, zoom and fit controls, Copy code and Reset. Edits stay in the viewer's browser only. There is no Send to chat button, and downloads are blocked in published pages, so tell the user to paste edited code back into the chat, or ask you to save it, when it should reach you or the repo.

A published page is private by default but it is still hosted. If the diagram contains customer names or anything the user called confidential, ask before publishing. As an alternative, offer to save the filled-in template as an `.html` file in the repo, which opens locally in a browser and still loads Mermaid from cdnjs.

## Diagram style

The template styles every diagram as a clean, flat flow: soft blue rounded boxes with dark blue text, thin grey right-angle connectors, and white pill-shaped edge labels. The team chose this look because it reads well in documents and presentations, so write diagrams to suit it:

- Use `flowchart LR` by default. Use `TD` only when the flow is clearly vertical, such as a long approval chain.
- Draw steps as rounded boxes with quoted labels: `A1("Create repo")`. Break long labels with `<br/>` so boxes stay compact, for example `A1("Create GitHub repo<br/>and grant access")`. Remember the escaping in the textarea step above, so `<br/>` becomes `&lt;br/>`.
- Mark decisions, reviews and classification steps as dashed, paler boxes. Add these two lines at the bottom of the diagram, then list the node ids in the `class` line:

  ```
  classDef review fill:#F5FAFE,stroke:#B5D4F4,stroke-dasharray:4 3
  class A3 review
  ```

- Keep edge labels to one or two words, such as `Yes`, `No` or `Feedback`: `A3 -->|Feedback| B1`.
- Do not use `subgraph` swimlanes unless the user asks for lanes. Lane frames clash with the flat style, and the lane's owner can usually go into the box label instead.

The pill labels and rounded corners come from the templates' own styling. The same code pasted into GitHub or mermaid.live shows the colors from `classDef` but square corners and plain labels. The connectors have square bends because Mermaid 10.9.1 has no rounded option.

## Writing diagrams that render reliably

- Put node labels in double quotes. Labels with spaces, slashes or brackets break without them.
- Never use the lowercase word `end` as a node id or label. It closes a subgraph.
- Keep labels short. Long labels make wide diagrams that are hard to read in a chat-width widget. Five or six boxes in a row is about the limit.
- Prefer one idea per diagram. Offer a second diagram over a crowded first one.

## If the widget cannot be used

The widget needs the visualizer tools, and its preview needs the browser to reach cdnjs. If the tools are missing, or the user reports that the preview shows a library error, do not keep retrying. Give the code as plain text instead and suggest a place to view it, such as a Markdown file on GitHub (which renders Mermaid natively) or mermaid.live.

## Giving the code as plain text

Chat interfaces often render a Mermaid code fence as a finished diagram and hide the code. When the user needs to copy the code, use a fence tagged `text`, not `mermaid`. If the user wants to paste it into a Markdown file, tell them to change the tag to `mermaid` there.

## Repository conventions

Diagram sources are text and belong in the repository next to the documents they illustrate. Follow the folder layout the repository already uses, and ask the user where a new file should go instead of inventing a folder.
