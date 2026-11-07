# stable-audio-3-sfx

For: game sound effects and one-shots. Stable Audio 3 medium, with an LLM prompt enhancer
(Qwen 3.5 2B) that expands a short description for the chosen category.
Model: `stable_audio_3_medium_base.safetensors`   Text encoder: `t5gemma_b_b_ul2.safetensors` (stable_audio)
Enhancer LLM: `qwen3.5_2b_bf16.safetensors`
Sampler: KSampler `res_multistep` / `simple`, 50 steps, CFG 7
Output: SaveAudioMP3 (V0) → `.mp3`

| Role | Node.input | Default |
|---|---|---|
| Description | 52:31.value | (filled in per sound) |
| Length (s) | 52:36.value | 1.5 |
| Category | 52:43.choice | SFX (`SFX` / `One-shot`; `Music` / `Instrument` are out of scope) |
| Enhancer on/off | 52:35.value | true |
| Enhancer (capture with PreviewAny) | 52:28 output 0 | - |
| Enhancer seed | 52:28.sampling_mode.seed | 0 (fixed: same description → same enhanced prompt) |
| Negative | 52:7.text | "" |
| Seed | 52:3.seed | random each run |
| Steps / CFG | 52:3.steps / 52:3.cfg | 50 / 7 |
| Output name | 19.filename_prefix | audio/stable_audio_3 |

Notes:
- `52:42` is an existing PreviewAny (it shows the length); use another id (e.g. `900`) for
  the enhancer preview.
- No canvas `.json` saved with this template (only the API export).
