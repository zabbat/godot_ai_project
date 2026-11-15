# z-image-turbo

For: general 2D game art (icons, portraits, figures). ComfyUI's own Z-Image Turbo template:
built-in nodes only (no custom node packs), no LoRA, fast (8 steps). The style comes from the
prompt (and the project's style doc, if any).
Model: `z_image_turbo_bf16.safetensors` (UNETLoader)   Text encoder: `qwen_3_4b.safetensors` (lumina2)
VAE: `ae.safetensors`   LoRA: none
Sampler: KSampler `res_multistep` / `simple`, 8 steps, CFG 1   ModelSamplingAuraFlow shift 3
Size: 480x480

| Role | Node.input | Default |
|---|---|---|
| Prompt | 57:27.text | (filled in per image) |
| Seed | 57:3.seed | random each run |
| Width / Height | 57:13.width / 57:13.height | 480 / 480 |
| Batch | 57:13.batch_size | 1 |
| Steps | 57:3.steps | 8 |
| Output name | 9.filename_prefix | z-image-turbo |

Notes:
- No negative prompt: the negative is `ConditioningZeroOut` of the prompt, so CFG 1 ignores it.
- Needs on the server only the three model files above (ComfyUI's template browser offers to
  download them). `comfy workflow validate` names whatever is missing.
- To add a style LoRA, save a project template with a `LoraLoaderModelOnly` between the
  UNETLoader (`57:28`) and ModelSamplingAuraFlow (`57:11`).
- No canvas `.json` saved with this template (only the API export).
