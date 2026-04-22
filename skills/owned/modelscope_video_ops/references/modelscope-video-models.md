# ModelScope Video Model Notes

Checked date: `2026-04-22`

Primary source endpoints:

- `GET https://www.modelscope.cn/api/v1/tasks`
- `PUT https://www.modelscope.cn/api/v1/models/`
- `GET https://www.modelscope.cn/api/v1/models/{model_id}`

## Task Signals

Relevant task names confirmed from `/api/v1/tasks`:

- `video-captioning`
- `video-question-answering`
- `auto-speech-recognition`
- `speech-language-recognition`

## Star-Ranked Defaults Used by This Skill

The helper script selects the highest-star candidate from keyword queries, then applies task filtering when possible.

Fallback defaults:

- video understanding:
  - `Qwen/Qwen2.5-Omni-7B` (high-star multimodal any-to-any)
- video caption:
  - `iic/multi-modal_hitea_video-captioning_base_en`
- subtitle ASR:
  - `iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch`
- speech language id:
  - `iic/speech_whisper-large_lid_multilingual_pytorch`

## Notes

- ModelScope model cards can expose rich README usage examples even when `SupportApiInference` is false.
- Subtitle generation requires timestamps; not all ASR outputs include them by default.
- Language-ID task availability is narrower than ASR; keep explicit LID model fallback.
