---
name: modelscope_video_ops
description: |
  基于 ModelScope 做视频理解、视频描述、字幕提取（ASR）和语种识别（LID），并支持按点赞数自动选择默认模型。
  当用户提到 ModelScope 视频理解、视频描述、字幕提取、语音转字幕、语种识别、video captioning、ASR、LID 时必须触发。
compatibility:
  tools: [bash, python]
  requires: Python 3；若需从视频抽音频，建议安装 ffmpeg
---

# ModelScope Video Ops

This skill provides a practical video analysis workflow on top of ModelScope:

1. pick default models by star ranking
2. video caption / understanding
3. ASR transcription to subtitle
4. speech language identification (LID)

## Model Defaults (Star-Ranked)

Use helper script to resolve defaults from live ModelScope metadata:

```bash
python ~/.codex/skills/modelscope_video_ops/scripts/modelscope_video_helper.py defaults
```

As of this skill version, fallback defaults are:

- video understanding: `Qwen/Qwen2.5-Omni-7B`
- video caption: `iic/multi-modal_hitea_video-captioning_base_en`
- subtitle ASR: `iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch`
- speech language id: `iic/speech_whisper-large_lid_multilingual_pytorch`

Read details in:

- [modelscope-video-models.md](./references/modelscope-video-models.md)

## Discover Candidate Models

Example: top video-captioning candidates:

```bash
python ~/.codex/skills/modelscope_video_ops/scripts/modelscope_video_helper.py recommend \
  --keyword video-caption \
  --task video-captioning \
  --top 10
```

Example: top speech-language-recognition candidates:

```bash
python ~/.codex/skills/modelscope_video_ops/scripts/modelscope_video_helper.py recommend \
  --keyword lid \
  --task speech-language-recognition \
  --top 10
```

## Video Description (Caption)

```python
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

captioner = pipeline(
    task=Tasks.video_captioning,
    model="iic/multi-modal_hitea_video-captioning_base_en",
)
result = captioner("input.mp4")
print(result)
```

If your installed SDK does not expose `Tasks.video_captioning`, use string task name:

```python
captioner = pipeline(task="video-captioning", model="iic/multi-modal_hitea_video-captioning_base_en")
```

## Subtitle Extraction Workflow

1. Extract audio from video:

```bash
python ~/.codex/skills/modelscope_video_ops/scripts/modelscope_video_helper.py extract-audio \
  --video ./input.mp4 \
  --output ./tmp/audio.wav
```

2. Run ASR pipeline with your selected ModelScope ASR model.
3. Save ASR raw JSON segments (must contain `start/end/text` or equivalent fields).
4. Convert to `.srt`:

```bash
python ~/.codex/skills/modelscope_video_ops/scripts/modelscope_video_helper.py build-srt \
  --segments ./tmp/asr_result.json \
  --output ./tmp/output.srt
```

## Speech Language Recognition (LID)

```python
from modelscope.pipelines import pipeline

lid = pipeline(
    task="speech-language-recognition",
    model="iic/speech_whisper-large_lid_multilingual_pytorch",
)
result = lid("tmp/audio.wav")
print(result)
```

## Practical Rules

- 如果用户只要“一句视频描述”，优先 `video-captioning` 任务。
- 如果用户要“详细理解 + 问答”，优先多模态大模型（如 `Qwen/Qwen2.5-Omni-7B`）。
- 如果用户要字幕，先做 ASR，再转 SRT，不要把“描述”当作“字幕”。
- 语种识别应先于多语 ASR 策略选择，避免错误语言配置导致识别质量下降。

## Failure Handling

- `ffmpeg` 不存在：先提示安装，或跳过抽音频步骤。
- ASR 输出无时间戳：无法直接生成 SRT，需切换支持时间戳的 ASR 模型或输出格式。
- 模型查询为空：用 helper 的 fallback 模型继续执行。
