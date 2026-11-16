# Character concept sheet

One landscape image with **the same character in four full-body views**: front, back, side and a
dynamic three-quarter pose. It fixes the look of a character in one picture: outfit, hair, colours
and how it looks from every side. Later resources are made from it (an image-to-3D model, the
portraits, the in-game figure). A character that has a design reference (a sprite, a sketch, a
photo of a pose) gets the sheet first, before its portraits.

Made with the normal `comfy-ui-images` commands ("generate new image" into one asset folder);
this file only holds the recipe that worked.

## Recipe

Use the project's default template and the style LoRA its style doc names for characters (the
first game used `z-image-turbo-res4lyf` + an anime LoRA at 0.8). Positive prompt only.

1. **Concept at 480x480, a single figure.** Put the design brief into the prompt (see "Prompt")
   and render 2 takes per outfit idea (a dress and a skirt, for example), full body, frontal,
   figure small in the frame with space around it, flat background. Fast; the user picks the
   outfits to continue with. Describe a reference image (a game sprite) in words: the model has
   no image input in this graph, so name its hair, headband, cape, colours; change what the user
   wants changed ("light blue instead of green").
2. **Same prompt at 1280x1280 for detail** (optional, 4 takes). Use the picked takes' graphs
   (`<xxx>-asset-<nr>-<desc>.api.json`), change only width/height and the seed. Check that the
   hair and outfit survive the bigger size; the details drift (a ponytail turned into a bun in
   some takes), so look at every take.
3. **The sheet at 1280x720**: start from the picked take's graph, replace the framing part of the
   prompt with the layout sentence below, keep the character part word for word, set 1280x720,
   new seed. 2 takes per outfit; the user picks.
4. Display the takes (the skill's display step) and let the user choose. Save each take with its
   `.md` and `.api.json` as always, in the same asset folder (the concept asset, e.g.
   `084-asset-<character>-concept/`).

## Prompt

Style keywords from the style doc, then the layout, then the character, then the background:

```
<style keywords>, wide landscape character turnaround sheet of the same <girl/man/creature> in
four full body views in a row from left to right: front view standing upright facing the viewer,
back view seen from behind showing her long ponytail and the back of her white cape, side view in
profile, and a dynamic three-quarter view mid-step striding forward with one hand raised and
glowing with soft golden light, her white cape and ponytail swinging behind her, <expression>,
<the character: age, hair, eyes, skin, accessories, clothes, colours, trim, belt, cape, boots>,
the whole figure from head to feet small in the frame with empty space around her, solid uniform
flat dark slate grey background with no texture, soft even light
```

- **The fourth view is the character's own pose**: what fits who they are (a mage casting, an
  archer drawing, a knight with the sword raised, a mob lunging). Ask the user, or take it from
  the bible; it shows personality, not only a stance.
- **One layout sentence.** Two layout ideas in one prompt ("a portrait in the corner" and "a back
  view on the left") made the model fall back to a standard sheet. Say "four full body views in a
  row" and name each view once.
- **Flat background in a colour the character does not have** (dark slate grey for white and
  light blue clothes), so the sheet can be cut out later.
- **Say the hair in every view** if it matters: in two takes the side view lost the ponytail and
  showed a bun. Name it in the side-view text too ("side view in profile, her high ponytail
  visible") when it drifts.
- **Positive words only** (see "Writing the prompt" in the skill). "Facing away" worked for the
  back view in landscape; at 720x1280 the back view came out three-quarter from behind.
- **When editing a prompt from an earlier take**, check that the old layout phrase is really gone
  (a leftover "waist-up portrait" fragment stayed in once). Print the final text before sending.

## Sizes that were tried

| Size | Result |
|---|---|
| 480x480 | one figure, good for choosing outfits quickly |
| 1280x1280 | one figure plus an inset (circle or waist-up portrait): the inset works, the body gets stiff, small details drift |
| 720x1280 (portrait) | two figures and a portrait stack: cramped |
| **1280x720** | **four views side by side: the sheet** |

## Using the sheet

- It is a **reference for an image-to-3D tool** (Tripo, for example) and for the portraits and
  in-game figures: they use the same prompt keywords and the colours from it.
- Keep the chosen sheet in `assets/` with its record (the character's resource sheet has a
  "Concept sheet" row, see the `game-character` skill); the takes stay in the tool's `output/`.
- If ComfyUI's command line is blocked on the machine, the running server's HTTP API does the same
  (`POST /prompt` with the API graph as `{"prompt": ...}`, then `/history/<id>` and `/view`).
