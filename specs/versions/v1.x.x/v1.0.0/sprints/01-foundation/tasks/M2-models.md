---
milestone: M2
title: Model Pre-download
duration: 1 day
status: pending
---

# M2: Model Pre-download

## Tasks

### T2.1: Download models during Docker build

**Description**: Pre-download both `big` and `small` model variants during image build.

**Acceptance**: Models exist in `/root/booknlp_models/` in final image.

**Test Strategy**:
- Integration: Verify model files exist in container
- Integration: BookNLP initializes without network calls

**Models to download**:
- `entities_google_bert_uncased_L-6_H-768_A-12-v1.0.model` (big)
- `coref_google_bert_uncased_L-12_H-768_A-12-v1.0.model` (big)
- `speaker_google_bert_uncased_L-12_H-768_A-12-v1.0.1.model` (big)
- `entities_google_bert_uncased_L-4_H-256_A-4-v1.0.model` (small)
- `coref_google_bert_uncased_L-2_H-256_A-4-v1.0.model` (small)
- `speaker_google_bert_uncased_L-8_H-256_A-4-v1.0.1.model` (small)

---

### T2.2: Verify offline operation

**Description**: Ensure container works without network access after build.

**Acceptance**: BookNLP processes text with `--network none`.

**Test Strategy**:
- Integration: `docker run --network none booknlp:cpu python -c "..."`

---

### T2.3: Download spacy model

**Description**: Pre-download `en_core_web_sm` spacy model.

**Acceptance**: Spacy model available in image.

**Test Strategy**:
- Integration: `python -m spacy validate` succeeds

---

## Telemetry

| Metric | Collection Point |
|--------|------------------|
| Model download time | Build stage |
| Total model size | Post-build |

## Rollback

N/A (greenfield)
