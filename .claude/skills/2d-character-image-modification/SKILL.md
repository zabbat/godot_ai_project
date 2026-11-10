---
name: 2d-character-image-modification
description: How to modify an existing 2D character image without redrawing it - cut a figure out with a clean edge (colour-key on a flat background, person-mask fallback), make expression variants (blink, closed eyes, smile, angry, embarrassed, frown lines, glowing eyes) by editing only the face so the outline and alpha stay identical, and change a pose or gesture (raise an arm, hand over mouth, hold an item) with small masked passes - plus how to check every edit with a pixel diff, advice for the user on which poses edit cleanly, and a log of lessons learned from earlier edits. Use when the user asks to cut out or remove the background of a character, make a transparent PNG, add a blinking / closed-eyes / other expression version of a character image, change a character's pose or hands, asks why something else changed in an edit ("the necklace changed"), touches up part of a character picture, or wants to record what was learned from an edit.
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
- `face_inpaint.py`: repaint chosen boxes with Flux Fill (despite the name, any area: face,
  arm, background, clothes). Needs ComfyUI running at 127.0.0.1:8188 with
  `flux1-fill-dev.safetensors`, `clip_l`, `t5xxl_fp8_e4m3fn_scaled`, `ae`.
- `draw_boxes.py <src> <out> --box x0 y0 x1 y1 ... [--crop ...] [--grid 64] [--view ...]`:
  draws the boxes (red), the crop window (blue) and a labelled pixel grid on a copy, to check
  boxes before a run. Read coordinates off the grid numbers, not off a scaled preview.
- `diff_check.py <before> <after> <out.png> [--box ...]`: how much changed, where, and whether
  anything changed outside the boxes; writes the original with every changed pixel in magenta
  next to before/after crops. Run it on every chosen take, and show it when the user asks "did
  it change X?" instead of guessing.

**Learning log.** When an edit teaches something new (a trap, a prompt that worked, a box
recipe), add it to [Lessons](#5-lessons) or the worked examples in a line or two, with the take
it came from. Ask the user before changing this file (skills are shared between projects).

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
   must change). Draw the boxes with `draw_boxes.py --grid 64` and look before running.
   Leave out of the mask whatever already works: for anger, repaint the brows and mouth and
   keep the eyes (repainted eyes change colour and open wide). Too small leaves the old
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
5. **Build the cut-out variant from the neutral's cut-out**: copy the neutral cut-out (RGBA)
   and replace only the pixels where the variant's source differs from the neutral's source
   (`m = (variant_src != neutral_src).any(-1)`; face pixels are fully opaque, so assert alpha
   255 there). The outline and the edge colours are then identical by construction. Do not
   re-run the colour key on the variant. Avoid "variant source RGB + neutral alpha"
   (`putalpha`): the soft edge pixels keep the background colour mixed in (a faint fringe the
   colour key had removed from the neutral) and the transparent pixels keep their green RGB.

**When the base changes later** (an edit outside the face, such as removing an ornament), rebase
the face variants instead of redoing them: `m` = pixels where the variant's source differs from
the **old** neutral source (take the old one from git), then new variant source =
`where(m, variant_src, new_neutral_src)` and the cut-out as in step 5 from the new neutral's
cut-out. Exact, no seam, and it works because the variant changed only the face. Check first
that `m`'s bounding box is only the face and that it does not overlap the base edit.
6. **Compare** neutral and variant with `diff_check.py`: only the face patch may change.
   Lashes sit where the lid line was, glasses do not shift, skin tone in the patch matches the
   skin around it.

Other expressions work the same way (smile, open mouth, brows): new boxes, new prompt. Add a
detail later (frown lines, a stronger blush) as a **small second pass on the chosen take**, not
by rerunning the first pass with a longer prompt.

**Glowing eyes** (casting): do not inpaint, edit pixels. Mask the lit pixels inside a box
around each eye, fill with a pale colour keeping some original shading, add a tight bright
halo plus a wide soft one, keep the alpha from the master. The tower repo's
`tools/comfy-ui/scripts/necromancer_casting_eyes.py` is a worked example.

If inpainting will not give a clean result (wrong lash shape, style mismatch), a hand-drawn
patch is fine: draw the closed-eye lines with PIL in the same boxes, in the line colour
sampled from the original lashes.

## 3a. Change a pose (an arm, a hand, a held item)

The same masked inpainting, but the outline changes and more of the figure is at stake.

**Advise the user first**, briefly, when they ask for a pose change:
- **Whatever a box covers is redrawn.** A hand in front of the face, neck or chest means the box
  covers them, and the necklace, hair curls, collar or lips under it come back different, even
  where the hand does not end up. Poses that keep the new part **away from the face and
  jewellery** edit cleanly: a hand on the hip, at the waist, holding the skirt, on the chest
  below the neckline, raised to the side. If the pose must cross the face (hand over mouth,
  finger to lips, hand on cheek), expect small changes around it and use the tightest boxes.
- **Moving a limb is two jobs**: draw the new limb, and remove the old one (an arm hanging at
  her side stays unless that area is repainted too). The removal leaves background and clothes
  to fill, where Flux likes to invent things (see Lessons).
- **The outline changes**, so the variant needs its own cut-out and will not swap in place in
  the game like a face expression (the arm and the clothes next to it jump). Fine for a pose;
  say so if the user means to use it as an "expression".
- More than about a third of the figure masked (a whole new pose, turning the body) is a new
  generation, not an edit: offer that instead.
- **Offer to try it small first** (see below) when the edit is new or uncertain: a pose, a
  removal, a prompt not tried before.

**Try it on a 480x480 copy first.** Scale the source down to 480x480 (Lanczos; from a 1280
source the factor is 0.375) and scale the boxes and crop by the same factor, rounded. Runs are
several times faster and the previews are smaller, so trying prompts, box placement and the
order of passes costs little GPU time and few tokens. Use the small runs to settle **what works**
(the prompt, the boxes, which passes, what goes wrong), then redo the chosen recipe at full
size. The full run is not a copy of the small one: the same seed gives a different picture at
another size, so run a few seeds at full size too. Fine detail (frown lines, lashes, a blush)
is too small to judge at 480; for those, test at full size. Keep the small takes in their own
folder (or named `-small`) so they never end up as masters.

**Recipe:**
1. Work on the flat-background source (or its 480x480 copy for a first try). Measure on a
   labelled grid (`draw_boxes.py`).
2. **Several narrow boxes along the limb's path** (hand, wrist, forearm, elbow), not one
   rectangle around the whole path: a rectangle from the mouth to the elbow covers the chest,
   necklace and hair.
3. Crop window about 1024 px, so the model sees the shoulder and the body.
4. Prompt the new limb **and the things in the boxes that must stay** (`a gold necklace with
   green gems`, `puffed sleeves`), with the style words. Never describe what must go away ("the
   other arm resting at her side" kept the old arm).
5. Pick the best of 4 seeds (the new pass keeps the old limb, that is expected), then **remove
   the old limb** on that take. Split it by what lies behind it:
   - **Over the background** (the gap between arm and waist): open the original source to see
     what was behind it, and if it was background, **paint it by hand** with the background
     colour (median of nearby background pixels, a little noise, blur the polygon edge ~0.8 px).
     Follow the new limb's underside and the body's edge with the polygon. No inpainting, so
     nothing gets invented, and the colour key removes it anyway.
   - **Over the clothes** (skirt, bodice): inpaint a small box over the rest of the old limb
     (cuff, wrist), prompting the clothes and background:
     `the top of a full golden satin ball gown skirt flaring out from the waist, smooth satin
     folds, plain flat smooth green background above the skirt`.
   - If you inpaint instead of painting, the box must cover **all** of the old limb down to
     the cuff (half an arm in the box is redrawn as an arm).
   Then zoom in (4x, nearest) on the elbow and the old limb's path: stray outline spikes and
   leftover strips are easy to miss at 1x. Paint small spikes away by hand too.
6. `diff_check.py` against the original: nothing important (jewellery, hair, eyes, crown)
   changed that should not have. Pass every box and painted area to `--box`.
7. Cut out with `colorkey_cutout.py` and the original's settings (in its record), not the
   original's alpha; check the edge over red.

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

## 5. Lessons

From Queen Charlotte (tower repo, takes 053-059 in `tools/comfy-ui/output/images/`):

- **Repainting the eyes changes their colour and size.** Angry face: boxes over brows and eyes
  recoloured the eyes (olive, red; 054-2, 054-3) or opened them wide, which reads surprised
  (054-5..8). Keeping her own half-lidded eyes and repainting only the brows plus the mouth gave
  a cold angry glare (054-11). The brows and mouth carry anger; leave the eyes alone.
- **One box over both brows** (with the bridge of the nose) lets them pull together into a V;
  two separate brow boxes keep them apart and barely lowered.
- **Details as a second pass work well**: frown lines came from a 58x52 px box between the
  brows on the chosen take (054-15); a stronger blush from a cheeks-only pass (053-5).
- **Too big a box changes what is under it.** Hand over mouth: one rectangle from the mouth to
  below the neckline (430 420 760 860) redrew the necklace (heavier, different), the hair curls
  by the neck, the collar and the lips (055-14). The diff showed 22 % of the picture changed,
  all inside the boxes. Use narrow boxes along the arm.
- **Flux Fill invents things in big empty fills.** Asking a large area to become plain
  background gave tiny queens, line sketches of figures and a signature (055-9..11, 13, 15,
  16). Describe the clothes and body that share the box, avoid the word "empty", keep the box
  no bigger than the old part, run more seeds; if it still happens, paint the pure-background
  part with the background colour by hand (the colour key removes it anyway) and inpaint only
  the part touching the body.
- **Hand on chest below the necklace edits cleanly** (057, 480 test). Three narrow boxes (hand
  on the breastbone just below the pendant, forearm, elbow) left the necklace, collar and face
  untouched (0 px changed outside the boxes). The prompt `her right arm bent at the elbow with
  her right hand pressed flat on her upper chest in shock, slender fingers spread over her
  breastbone` gave spread fingers with red nails; 1 of 4 seeds had a believable elbow. One seed
  added a bracelet: name the bare arm if that matters.
- **The 480 test paid off** (057): 12 Flux runs plus checks in a few minutes, and it showed the
  leftover-arm problem and its fix before any full-size run.
- **A removal box that stops short leaves a strip of the old limb** (057-small-final-3): the
  box 84 364 150 480 started below the new elbow, so the old forearm between the elbow and the
  waist stayed, with its gold cuff on the skirt. It looked clean on a 1x sheet of 4 seeds; the
  user saw it at once. Always zoom on the removal area. Fix: paint the background gap by hand,
  inpaint only the cuff on the skirt, then paint away the stray outline spike under the elbow
  (057-small-shocked-final).
- **Hand-painting the background beats inpainting it.** A filled polygon in the background
  colour (plus noise 1.5 and a slight blur) was clean on the first try; inpainting the same
  area risks invented figures (see above).
- **A pose change does not change the face.** The hand on the chest read as "how dare you",
  not shock, with her cold neutral face: offer a face pass (raised brows, open mouth) with it.
- **Small boxes invent things too.** Removing an ornament from the elbow (058, 1280, boxes
  about 76x116 on the arm's edge, half background): 2 of 4 seeds on the left drew a tiny queen
  and a hand in the background part; the other side was clean in all 4. Run 4 seeds even for a
  small fix, and pick the one whose outline continues the arm smoothly (some seeds put a kink in
  it). Prompt: `a slender bare arm with smooth fair skin and a clean dark outline, the golden
  satin ball gown skirt behind it, plain flat smooth green background`.
- **Fixing the base does not mean redoing the expressions** (059): blink, embarrassed and
  grumpy were rebased on the new neutral by copying exactly their changed face pixels (see
  "When the base changes later"); the faces are bit-identical to before. The old variants
  turned out to use "source RGB + neutral alpha", with green-mixed edge colours; the rebase
  fixed that too.
- **Half-covered parts come back.** A removal box over half the old forearm got the arm redrawn
  (055-9..12); covering all of it worked (055-14).
- **"Shh" instead of a covered mouth**: "covers her mouth with her fingers" gave a finger on the
  lips; "her palm pressed flat over her mouth hiding her lips, fingers together" got closer.
- **Measure on a labelled grid.** Reading coordinates off a scaled, offset preview put a box
  100 px off.
- **A face edit can be skipped on export** (tower repo, `tools/godot-sync/export_assets.py`):
  the image profile compares with `ImageChops.difference(...).getbbox()`, which on RGBA looks
  only at alpha, so a variant sharing the original's alpha looks unchanged and is not written.
  Until the script is fixed, delete the old exported file before exporting a changed face, and
  compare the export with the master (resize the master, compare RGB).

**Worked examples** (Charlotte, 1280x1280 source):

| Edit | Passes (boxes; crop 320 160 960 640 unless noted) | Result |
|---|---|---|
| Embarrassed (053-5) | brows 528 312 626 344 + 660 310 760 342, cheeks 536 384 620 428 + 676 382 760 426, mouth 598 440 690 484; then cheeks only for a stronger blush | good |
| Angry (054-15) | both brows in one box 524 300 764 346 + mouth 596 438 692 486; then 614 304 672 356 for frown lines | good |
| Hand over mouth (055-14) | crop 128 256 1152 1280: arm 270 600 500 1140 + hand path 430 420 760 860 (too big); then crop 0 256 1024 1280: old forearm 160 790 488 1280 | pose good; necklace and hair changed: redo with narrow boxes |
| Hand on chest, shocked (057, **480x480 test**, crop 0 0 480 480, feather 4) | hand 186 258 262 318 + forearm 140 296 204 362 + elbow 100 300 156 392 (seed 4); old forearm 84 364 150 480 (seed 3, left a strip); painted green polygon (132,388) (178,343) (166,398) (140,404) (128,398); skirt box 112 392 172 432 (seed 2); painted spike (126,387) (139,386) (137,397) (126,397) | good; x2.667 for 1280 |
| Elbow ornaments removed (058, 1280, feather 6) | left: crop 0 640 640 1280, box 272 1012 348 1128 (seed 4); right: crop 640 640 1280 1280, box 936 1014 1008 1146 (seed 1) | good; 1.4 % changed |

## Gotchas
- Python is not on PATH here: use ComfyUI's embedded `python.exe` with `-I`.
- Edit the flat-background source, never the cut-out.
- Never change the canvas size or crop of the master: the shared alpha only fits an identical
  canvas.
- Flux Fill follows the prompt, not the picture's style, unless you repeat the style words.
