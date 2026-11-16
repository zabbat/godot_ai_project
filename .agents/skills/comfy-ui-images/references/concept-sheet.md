# Character concept sheet

One tall image (720x1280) with **the same character in four full-body views in a two by two
grid**: front, back, side, and a dynamic pose in three-quarter view. It fixes the look of a
character in one picture: outfit, hair, colours and how it looks from every side. Later resources
are made from it (an image-to-3D model, the portraits, the in-game figure). Every new character
gets one first, before its portraits.

```
+-----------+-----------+
|   front   |   back    |
+-----------+-----------+
|   side    |  dynamic  |
|           | 3/4 view  |
+-----------+-----------+
```

Made with the normal `comfy-ui-images` commands ("generate new image" into one asset folder);
this file only holds the recipe that worked.

## Recipe

Use the project's default template and the style LoRA its style doc names for characters (the
first game used `z-image-turbo-res4lyf` + an anime LoRA at 0.8). Positive prompt only.

1. **Concept at 480x480, a single figure.** Put the design brief into the prompt (see "Prompt")
   and render 2 takes per outfit idea (a dress and a skirt, for example), full body, frontal,
   figure small in the frame with space around it, flat background. Fast; the user picks the
   outfits to continue with. Describe a reference image (a game sprite) in words: the model has
   no image input in this graph, so name its hair, headband, colours; change what the user wants
   changed ("light blue instead of green").
2. **The sheet at 720x1280**: start from the picked take's graph, replace the framing part of the
   prompt with the layout sentence below, keep the character part word for word, set 720x1280,
   new seed. Make 2 takes per outfit, then more versions of the best one (a new seed each time).
3. Display the takes (the skill's display step) and let the user choose. Save each take with its
   `.md` and `.api.json` as always, in the same asset folder (the concept asset, e.g.
   `084-asset-<character>-concept/`).
4. **Loose parts go on their own sheet.** For a body that will become a 3D model, leave a cape,
   cloak or similar flowing part out of the body sheet (describe the bare shoulders and a collar
   instead; never write "no cape"), and design it separately. A cape fused to the body can't
   swing, clips through the arms, and leaves holes when removed from a generated mesh.

## Prompt

Style keywords from the style doc, then the layout, then the character, then the background:

```
<style keywords>, tall character turnaround sheet of the same <girl/man/creature> with exactly
four full body views in a two by two grid, top left front view standing upright facing the viewer
with her arms relaxed slightly away from her body in a neutral A-pose, top right back view, a
perfectly straight symmetrical rear view from directly behind, shoulders and hips square to the
viewer, her head turned straight away from the viewer, showing her long ponytail and her bare
shoulders and upper back, arms relaxed away from her body in the same neutral A-pose as the front
view, bottom left side view in profile with her long high ponytail hanging down her back and her
arms relaxed at her sides, and bottom right a dynamic pose seen in three-quarter side view, her
face slightly turned to the camera, <expression>, <the character: age, hair, eyes, skin,
accessories, clothes, colours, trim, belt, boots>, every figure shown in full from the top of the
head down to the white boots, each figure small within its own quarter of the picture with empty
space above and below it, solid uniform flat dark slate grey background with no texture, soft even
light
```

- **Name each view once** and give each a corner (top left, top right...). Two layout ideas in one
  prompt ("a portrait in the corner" and "a back view on the left") made the model fall back to a
  standard sheet. "Exactly four" stopped it drawing a fifth (a repeated back view).
- **The dynamic pose**: "a dynamic pose seen in three-quarter side view" alone gives a gentle
  walk with a swinging skirt, because the model does the minimum. Adding "her face slightly turned
  to the camera" makes it face the viewer. To get a real action (a mage casting, an archer
  drawing, a knight lunging) the prompt has to name what the body does: feet, weight, arms, gaze.
  Ask the user whether to describe an action or leave it plain, and put the action in the bible
  if there is one. A vague "mid-step striding" gave a skipping leg, and "one hand raised and
  glowing" gave a wave.
- **The back view twists** when the prompt says "head facing forward" (it is ambiguous: toward the
  viewer?). Use "a perfectly straight symmetrical rear view from directly behind, shoulders and
  hips square to the viewer, her head turned straight away from the viewer", and ask for the same
  A-pose as the front.
- **Neutral A-pose** for front, back and side ("arms relaxed slightly away from her body"): the
  input an image-to-3D tool and a rig want. The dynamic pose is only an art reference.
- **Flat background in a colour the character does not have** (dark slate grey for white and light
  blue clothes), so the views can be cut out by colour.
- **Say the hair in every view** if it matters: the side view lost the ponytail (a bun) until the
  prompt said "her long high ponytail hanging down her back" there.
- **Every figure from head to boots** ("each figure small within its own quarter of the picture
  with empty space above and below it"). Without it the top row was cut at the knees.
- **Positive words only** (see "Writing the prompt" in the skill).
- **When editing a prompt from an earlier take**, check that the old layout phrase is really gone
  (leftover fragments stayed in twice). Print the final text before sending.

## Sizes that were tried

| Size and layout | Result |
|---|---|
| 480x480, one figure | good for choosing outfits quickly |
| 1280x1280 with an inset (circle or waist-up portrait) | the inset works, the body gets stiff, small details drift |
| 720x1280, two figures and a portrait stacked | cramped |
| 1280x720, four views in a row | works, but the model sometimes adds a fifth view; the figures are small |
| 1280x1280, 2x2 grid | the front and back were cut at the knees |
| **720x1280, 2x2 grid** | **the format: tall cells fit full-length figures** |

## Using the sheet

- It is a **reference for an image-to-3D tool** (Tripo, for example) and for the portraits and
  in-game figures: they use the same prompt keywords and the colours from it. To feed the tool one
  view at a time, cut the views out: a colour key on the flat background
  (`colorkey_cutout.py`-style), then split the grid by its cells (the figures do not touch), keep
  the largest piece of each crop and trim. The front, back and side views are the 3D input.
- Keep the chosen sheet in `assets/` with its record (the character's resource sheet has a
  "Concept sheet" row, see the `game-character` skill); the takes stay in the tool's `output/`.
- If ComfyUI's command line is blocked on the machine, the running server's HTTP API does the same
  (`POST /prompt` with the API graph as `{"prompt": ...}`, then `/history/<id>` and `/view`).
