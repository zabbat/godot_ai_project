---
name: 2d-character-image-modification
description: How to modify an existing 2D character image without redrawing it - cut a figure out with a clean edge (colour-key on a flat background, person-mask fallback), and make expression variants (blink, closed eyes, smile, glowing eyes) by editing only the face so the outline, pose and alpha stay identical. Use when the user asks to cut out or remove the background of a character, make a transparent PNG, add a blinking / closed-eyes / other expression version of a character image, or touch up part of a character picture.
---

# 2D character image modification

Know-how for changing a finished character picture. Two jobs: **cut it out**, and
**make a variant** (blink, expression) of it. The one rule behind both: **change as
little as possible and keep everything else pixel-identical**. Never regenerate the whole
picture for a small change: a new generation moves the outline, hair, folds and colours,
every variant would need its own cut-out, and the figure would jitter when swapped in game.

Scripts (in this skill's `scripts/`; run with a Python that has PIL, numpy and scipy, on
this machine ComfyUI's embedded `python.exe -I`):
- `colorkey_cutout.py`: flat-background colour-key cut-out.
- `face_inpaint.py`: repaint chosen boxes of a face with Flux Fill. Needs ComfyUI running at
  127.0.0.1:8188 with `flux1-fill-dev.safetensors`, `clip_l`, `t5xxl_fp8_e4m3fn_scaled`, `ae`.

The person-mask cut-out (YOLO + SAM) and the take naming/saving conventions are in the
`comfy-ui-images` skill ("cut out"). Output goes where the project says (tower repo: takes in
`tools/comfy-ui/output/images/`, masters in `assets/`).

## 1. Make the base picture cuttable

Cutting is easy or hopeless depending on how the picture was drawn. When generating the base
figure:
- **Plain flat background in a colour the figure does not contain** (lavender purple, dark
  slate blue, ochre). Never white or a colour of clothes/hair; no gradient or vignette.
  Prompt: `plain flat lavender purple background, soft even light`.
- Keep the whole figure inside the frame (nothing touching the border). For a figure that
  will carry expression variants: frontal, looking into the camera, shoulders square.
- Keep the **source on the flat background** (`*_source.png`) next to the cut-out. All later
  edits start from the source, and the cut-out's alpha is reused.

## 2. Cut out

Prefer the **colour key** when the background is flat. It keeps what a person mask drops
(staffs, held flames, glasses, thin strands) and gives soft edges.

```
python.exe -I scripts/colorkey_cutout.py <source.png> <out.png> --tol 14 --soft 8 --holes 25
```
- Background colour = median of the image border. Pixels within `--tol` (RGB distance) that
  connect to the border (flood fill, so same-coloured spots inside the figure stay) become
  transparent; `--soft` is the width of the partial-alpha ramp.
- Edge pixels are **un-mixed from the background colour** (`c = a*f + (1-a)*bg`), so no halo
  of the old colour is left. This is why a colour key beats a hard mask.
- `--holes N`: also clear enclosed background gaps of at least N pixels (between hair and
  arm, inside a handle) that the border flood cannot reach. Pick N below the gap size and
  above any same-coloured detail inside the figure.
- Tuning: `--tol 14 --soft 8` for clean flat art (Lunara); `--tol 38 --soft 14` for
  painterly/noisy backgrounds (Necromancer). Fringe of background colour left: raise `--tol`.
  Parts of the figure eaten (light highlight, similar-coloured sleeve): lower `--tol`, or
  regenerate on a background further from the figure's colours.
- Fallback when the background is not flat or matches the figure: the `comfy-ui-images`
  person-mask cut-out, with `--shrink 2` for a fringe. Thin strands go missing there.

**Always check the edge**: composite the PNG over a bright contrasting colour (red, green)
and zoom on hair, fingers and glasses. Look for a ring of old background, holes that should be
transparent, holes that should be solid, jagged edges. Check at the size the game shows it.

## 3. Make an expression variant (blink, closed eyes, ...)

Edit **only the face patch**, on the **source** (flat background) image, then reuse the
neutral's alpha. Everything outside the patch stays pixel-identical, so the variant swaps in
place with the same outline and needs no new cut-out.

1. **Measure the boxes.** Find pixel boxes around only what changes (blink: one box per eye
   or lens, covering the eye and lids; leave the glasses frame and brows alone unless they
   must change). Draw the boxes on a copy and look before running. Too small leaves the old
   eye showing at the edge; too big repaints skin and shifts the face.
2. **Pick a crop window** around the face (about 600-1000 px, boxes inside with margin). Flux
   Fill works best with the face large in frame and some context.
3. **Prompt for what the patch should show, in positive words** ("no eyes", "without" pull the
   thing in). Repeat the original's style keywords so the lines match: `anime style, anime
   illustration, clean lineart, cel shaded, a young woman with round glasses, both eyes closed
   in a blink, closed eyelids with a curved dark lash line, relaxed face, smooth skin on the
   eyelids`.
4. **Run:**
   ```
   python.exe -I scripts/face_inpaint.py <source.png> <out_source.png> \
       --crop 320 240 960 624 --box 525 328 618 388 --box 685 328 778 388 \
       --prompt "..." --seed 1 --feather 6
   ```
   It crops, inpaints the masked boxes (mask grown 4 px, differential diffusion) and pastes back
   through a feathered mask, so edges blend and the rest is untouched. Defaults: 28 steps,
   guidance 30, euler/normal. Try several seeds (it prints the seed), keep the best, and judge
   the whole face at game size, not zoomed in. Ask before big batches (GPU).
5. **Apply the neutral's alpha** for the cut-out variant: RGB from the result, alpha channel
   from the neutral's cut-out (`Image.putalpha`). The outline is then identical by
   construction. Do not re-run the colour key on the variant.
6. **Compare** neutral and variant (flip between them, or diff): only the face patch may
   change. Lashes sit where the lid line was, glasses do not shift, skin tone in the patch
   matches the skin around it.

Other expressions work the same way (smile, open mouth, brows): new boxes, new prompt.

**Glowing eyes** (casting): do not inpaint, edit pixels. Mask the lit pixels inside a box
around each eye, fill with a pale colour keeping some original shading, add a tight bright
halo plus a wide soft one, keep the alpha from the master. The tower repo's
`tools/comfy-ui/scripts/necromancer_casting_eyes.py` is a worked example.

If inpainting will not give a clean result (wrong lash shape, style mismatch), a hand-drawn
patch is fine: draw the closed-eye lines with PIL in the same boxes, in the line colour
sampled from the original lashes.

## 3b. Other ways to edit (from online research, not yet tried in this project)

Use these when the face-patch recipe above does not fit. Test on a copy and keep the ones that
work; note results here.

**Changing clothes or other large areas**
- *Mask-based (same method as the face patch):* paint a mask over the clothing, inpaint with
  Flux Fill and a positive prompt of the new outfit. Keeps the face and pose pixel-identical,
  but the mask must follow the body outline, and the outline changes if the new clothing is a
  different shape (so the alpha cannot be reused: redo the colour-key cut-out on the result).
- *Instruction-based:* **Flux.1 Kontext Dev** (`flux1-dev-kontext_fp8_scaled.safetensors`,
  native ComfyUI template) or **Qwen Image Edit** take the image plus a text instruction and
  need no mask. Prompt what changes and what stays: `Change the clothes to a red velvet
  cloak, keep the same face, hairstyle, pose and art style`. Keep the flat background in
  the source so the cut-out still works afterwards. These regenerate the whole image, so
  compare to the original: the face and outline may drift. Quality drops over repeated
  edits, so always edit from the original master, not from an earlier edit.
- Find the official templates in ComfyUI's template browser, and docs at
  docs.comfy.org (Flux Kontext Dev tutorial).

**Expressions: tips for the inpaint**
- If "closed eyes" does not show, the change is too weak: raise denoise (when using a
  KSampler with a latent noise mask, start near 0.4-0.5 and go up). Flux Fill with the full
  denoise, as in `face_inpaint.py`, already replaces the patch completely.
- Mask only the part that changes (eyes, or brows, or mouth) and do separate passes,
  instead of one pass over the whole face. A whole-face pass (FaceDetailer) tends to change
  brows and eye shape and is not good for expression changes on anime art.
- Style drift or a "too new" patch: shrink the box, strengthen Differential Diffusion or
  soften the mask (more feather), and repeat the original's style words in the prompt.
- Hard-to-get expressions: an IPAdapter or ControlNet reference of the wanted expression
  can work better than the prompt alone.

**Useful ComfyUI nodes/packs for patch edits**
- *ComfyUI-Inpaint-CropAndStitch* (`✂️ Inpaint Crop` / `Inpaint Stitch`): crops around the
  mask with context, sends only that to the sampler, stitches back without touching unmasked
  pixels, with a blend value to hide seams. Does by node what `face_inpaint.py` does in
  code.
- *comfyui-inpaint-nodes* (Acly): inpaint model helpers; note `VAE Encode (for Inpainting)`
  needs denoise 1.0, use Set Latent Noise Mask / InpaintModelConditioning to keep some of the
  original.
- *Differential Diffusion*: uses the mask as per-pixel denoise strength, so soft mask edges
  blend; a smoother mask gives it more room (grow the mask with blur, e.g. KJNodes
  GrowMaskWithBlur).
- Colour shifts after VAE decode: add a colour-match step to the patch. Seams: grow the mask
  a little more and add blur; edit spilling too far: reduce the growth.

Sources: [Flux.1 Kontext Dev tutorial](https://docs.comfy.org/tutorials/flux/flux-1-kontext-dev),
[Qwen Image Edit character consistency](https://weirdwonderfulai.art/comfyui/qwen-image-edit-can-create-character-consistent-lora-dataset/),
[ComfyUI inpainting tutorial](https://comfyui-wiki.com/en/tutorial/basic/how-to-inpaint-an-image-in-comfyui),
[Inpaint CropAndStitch](https://github.com/lquesada/ComfyUI-Inpaint-CropAndStitch),
[comfyui-inpaint-nodes](https://github.com/Acly/comfyui-inpaint-nodes).

## 4. Record and ship

- Save the result as a master with a `.md` beside it: prompt, model, sampler, steps,
  guidance, seed, crop, boxes, feather/grow, what it was made from and which alpha it uses, so
  it is reproducible (example: `assets/2d/characters/lunara/lunara_blink.md`).
- Three files per variant: the cut-out PNG (goes to the game), the `_source.png` on the flat
  background, and the `.md`.
- In a Godot AI repo the master goes in `assets/`, gets an asset-map entry and is exported
  with the sync script; never put the picture straight into Godot (`godot-ai-architecture`).
- Show the finished picture to the user (`code -r <png>`).

## Gotchas
- Python is not on PATH here: use ComfyUI's embedded `python.exe` with `-I`.
- Edit the flat-background source, never the cut-out.
- Never change the canvas size or crop of the master: the shared alpha only fits an identical
  canvas.
- Flux Fill follows the prompt, not the picture's style, unless you repeat the style words.
