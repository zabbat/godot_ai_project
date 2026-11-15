# z-image-turbo-res4lyf

For: the same 2D game art as `z-image-turbo`, with the RES4LYF ClownsharK sampler (an
implicit 2-stage sampler, often cleaner detail at the same step count). No LoRA. Needs the
RES4LYF custom node pack; use `z-image-turbo` where it isn't installed.
Model: `z_image_turbo_bf16.safetensors` (UNETLoader)   Text encoder: `qwen_3_4b.safetensors` (lumina2)
VAE: `ae.safetensors`   LoRA: none
Sampler: ClownsharKSampler_Beta (RES4LYF), `diag_implicit/qin_zhang_2s` / `beta57`, 9 steps, CFG 1, eta 0.5
Size: 480x480

| Role | Node.input | Default |
|---|---|---|
| Prompt | 57:27.text | (filled in per image) |
| Seed | 57:62.seed | random each run |
| Width / Height | 57:13.width / 57:13.height | 480 / 480 |
| Batch | 57:13.batch_size | 1 |
| Steps | 57:62.steps | 9 |
| Output name | 9.filename_prefix | z-image-turbo |

Notes:
- No negative prompt: the negative is `ConditioningZeroOut` of the prompt, so CFG 1 ignores it.
- Node `57:69` is an unconnected text node left in the export; it isn't run.
- Needs on the server: the RES4LYF node pack (`comfy nodes search ClownsharKSampler`) and the
  three model files above.
- To add a style LoRA, save a project template with a `LoraLoaderModelOnly` between the
  UNETLoader (`57:28`) and ModelSamplingAuraFlow (`57:11`).
- No canvas `.json` saved with this template (only the API export).
