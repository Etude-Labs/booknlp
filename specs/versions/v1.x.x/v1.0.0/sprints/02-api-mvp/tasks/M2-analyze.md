---
milestone: M2
title: Analyze Endpoint
duration: 2 days
status: pending
---

# M2: Analyze Endpoint

## Tasks

### T2.1: Create Pydantic schemas

**Description**: Create request/response schemas for analyze endpoint.

**Acceptance**: Schemas validate correctly with test data.

**Test Strategy**:
- Unit: Validation passes/fails as expected

### T2.2: Create NLPService wrapper

**Description**: Create service class wrapping BookNLP with model management.

**Acceptance**: Service loads models and runs analysis.

**Test Strategy**:
- Unit: Mock BookNLP, verify calls
- Integration: Real analysis with sample text

### T2.3: Implement POST /v1/analyze

**Description**: Implement analyze endpoint with full response.

**Acceptance**: Returns complete analysis as JSON.

**Test Strategy**:
- Integration: Full request/response cycle

### T2.4: Implement pipeline filtering

**Description**: Allow clients to request specific pipeline components.

**Acceptance**: Only requested components in response.

**Test Strategy**:
- Unit: Verify filtering logic
- Integration: Request with subset of pipeline

### T2.5: Support model selection

**Description**: Allow clients to specify `big` or `small` model.

**Acceptance**: Both models work via API parameter.

**Test Strategy**:
- Integration: Test both model values

## Telemetry

| Metric | Collection Point |
|--------|------------------|
| Request duration | Prometheus histogram |
| Tokens processed | Prometheus counter |
| Model used | Prometheus label |
