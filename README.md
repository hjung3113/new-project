# Roo C# ETL 오케스트레이션 템플릿

이 저장소는 C#/.NET 10 + Microsoft SQL Server 기반 ETL 프로젝트를 Roo Code로 운영하기 위한 에이전트 하네스입니다. 애플리케이션 구현체가 아니라, Roo 모드, slash command, workflow skill, 라우팅 규칙, phase gate, 문서 중심 계획 체계를 제공하는 템플릿입니다.

목표는 단순합니다. 작업이 커져도 에이전트가 즉흥적으로 코드를 만지지 않고, 설계 문서와 phase/checkpoint를 기준으로 계획, 승인, 구현, 검증, 종료까지 이어가게 만드는 것입니다. 세션을 초기화해도 [.planning/STATE.md](.planning/STATE.md)에서 현재 위치와 다음 행동을 복구할 수 있어야 합니다.

## 핵심 원칙

- 모든 요청은 하나의 소유 workflow로 라우팅합니다.
- 질문, 작은 문서 수정, 오타, 무해한 명령 실행, 기계적 정리, 즉시 검증 가능한 작은 변경은 `/simple`로 처리할 수 있습니다.
- 구현은 반드시 `discuss -> plan -> execute -> done` phase gate를 통과합니다.
- 동작 변경은 TDD로 진행합니다. 먼저 실패 증거를 만들고, 최소 변경으로 green을 만든 뒤 refactor합니다.
- SQL, migration, writer, transaction, restart, idempotency는 mock이나 SQLite가 아니라 `testcontainers-dotnet` + 실제 MSSQL 컨테이너로 검증합니다.
- `.planning/`은 영속적인 프로젝트 기억입니다. `.scratch/phase-state.json`은 현재 phase에서 허용된 작업을 나타내는 live gate일 뿐입니다.
- planning 문서, Roo 설정, tracker, application code의 소유권을 mode별로 분리합니다.
- [AGENTS.md](AGENTS.md)에는 [andrej-karpathy-skills의 CLAUDE.md](https://github.com/forrestchang/andrej-karpathy-skills/blob/main/CLAUDE.md)를 참고한 coding conduct 규칙을 추가했습니다.

## 새 세션 시작 순서

새 Roo 세션, 새 에이전트, 또는 대화 컨텍스트가 초기화된 경우 반드시 아래 순서로 읽습니다.

1. [AGENTS.md](AGENTS.md)
2. [.planning/STATE.md](.planning/STATE.md)
3. [.planning/ROADMAP.md](.planning/ROADMAP.md)
4. 현재 phase의 `.planning/phases/**/**-CHECKPOINTS.md`
5. [.scratch/phase-state.json](.scratch/phase-state.json)
6. 현재 phase의 context, plan, summary, verification 문서

이 순서를 지키면 이전 대화 기록 없이도 현재 phase, checkpoint, blocker, next action, 승인된 plan, 허용 경로를 복구할 수 있습니다.

## 큰 작업 흐름

아래 흐름은 “아무것도 없는 0부터 시작하는 경우”와 “이미 설계 문서가 있는 경우” 모두에 적용됩니다.

단, 작업이 작고 되돌리기 쉬우며 검증 방법이 명확한 경우에는 `/simple` + `workflow-simple-task`를 사용할 수 있습니다. 이 경로는 phase gate를 무시하는 통로가 아니라, 질문 답변, 오타 수정, 짧은 README 문구 추가, 무해한 스크립트 실행, 기계적 코드 정리, focused test로 즉시 증명되는 작은 변경을 가볍게 처리하는 통로입니다. DB, ETL, ops, 보안, 배포, 아키텍처, public contract, 원인 불명 버그, 넓은 리팩토링이 걸리면 즉시 일반 workflow로 되돌립니다.

### 1. 0부터 시작할 때

사용자가 아이디어만 가지고 있다면 먼저 구현하지 않습니다. `orchestrator`가 요청을 분류하고, 보통 `/adr` 또는 `/issues` 계열 planning workflow로 보냅니다.

1. 문제, 사용자, 목표, 비목표, 제약을 정리합니다.
2. 기존 문서가 없으면 `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`를 만듭니다.
3. milestone을 phase로 나눕니다.
4. 각 phase에 성공 기준, 의존성, gate, 예상 verification을 씁니다.
5. 첫 phase 폴더를 만듭니다.
6. phase 안에 `NN-CONTEXT.md`, `NN-01-PLAN.md`, `NN-CHECKPOINTS.md`, `NN-REVIEW.md`, `NN-VERIFICATION.md`, `NN-01-SUMMARY.md` 형태의 문서를 둡니다.
7. `.scratch/phase-state.json`은 아직 구현 승인 전이면 `discuss` 또는 `plan` 상태로 둡니다.

이 단계의 산출물은 코드가 아니라 결정과 계획입니다. 구현은 사용자가 `execute`를 승인한 뒤에만 시작합니다.

### 2. 설계 문서가 이미 있을 때

요구사항 문서, 설계 문서, ADR, PRD, 또는 외부 명세가 있다면 `/issues` 또는 `/adr`로 시작합니다.

1. 원본 문서를 읽고 고정 요구사항과 열린 질문을 분리합니다.
2. 결정이 필요한 부분은 `/adr` + `workflow-architecture-decision`으로 보냅니다.
3. 구현 가능한 단위는 `/issues` + `workflow-docs-to-issues`로 vertical slice issue로 쪼갭니다.
4. 각 slice에 추천 owner mode를 붙입니다.
5. DB, ETL, ops, 일반 feature가 섞여 있으면 한 issue에 몰아넣지 않고 workflow별로 나눕니다.
6. `.planning/ROADMAP.md`와 active phase checkpoint에 현재 위치를 반영합니다.

설계 문서가 있다고 해서 바로 구현하지 않습니다. 설계 문서는 plan의 입력이고, 구현 권한은 `.scratch/phase-state.json`의 `phase=execute`, `approved=true`, `plan_id`, `allowed_paths`, `verification`이 맞을 때만 열립니다.

### 3. Discuss phase

`discuss`는 읽기 전용입니다.

허용되는 작업:

- 파일 검색과 코드 탐색
- 기존 문서, ADR, issue, 테스트 읽기
- 위험, 선택지, 모르는 점 정리
- 가장 작은 blocking question 질문

금지되는 작업:

- 파일 수정
- 테스트나 generator처럼 파일을 바꿀 수 있는 명령 실행
- 구현 시작

이 phase의 목적은 “무엇을 해야 하는지”와 “무엇을 아직 모르는지”를 밝히는 것입니다.

### 4. Plan phase

`plan`은 문서화와 실행 계획 작성 단계입니다.

허용되는 작업:

- PRD, ADR, checklist, issue plan 작성
- `.planning/STATE.md`, `.planning/ROADMAP.md`, phase context/checkpoint 갱신
- acceptance criteria 작성
- verification command 작성
- 구현 범위와 소유 mode 결정
- `allowed_paths` 후보 정의

금지되는 작업:

- application behavior 변경
- source, migration, generated artifact, test implementation 수정
- dependency 설치나 code generator 실행

plan이 끝나면 에이전트는 멈추고 승인을 기다립니다. 승인 전에는 execute로 넘어가지 않습니다.

### 5. Execute phase

`execute`는 승인된 구현 단계입니다. 이 phase에서는 매 응답 또는 작업 단위가 다음 조건을 만족해야 합니다.

- `phase=execute`
- `approved=true`
- 승인된 `plan_id`
- 비어 있지 않은 `allowed_paths`
- 비어 있지 않은 `verification`
- 현재 요청이 승인된 plan 범위 안에 있음

일반 구현 흐름:

1. `workflow-phase-gate`로 live gate를 확인합니다.
2. owner workflow를 하나 선택합니다.
3. 실패 테스트 또는 재현 증거를 먼저 만듭니다.
4. red evidence를 기록합니다.
5. 최소 구현을 합니다.
6. focused test를 통과시킵니다.
7. green evidence를 기록합니다.
8. 필요할 때만 refactor합니다.
9. verification command를 실행합니다.
10. 결과를 active phase의 `*-VERIFICATION.md`와 `*-SUMMARY.md`에 남깁니다.

작업이 plan 밖으로 커지면 즉시 멈추고 `plan`으로 돌아갑니다.

### 6. Review phase 또는 review pass

리뷰는 구현과 분리합니다. `/review`와 `workflow-code-review`는 read-only가 기본입니다.

리뷰에서 보는 것:

- 동작 회귀
- 누락된 테스트
- SQL injection, transaction, index, MERGE 위험
- ETL stage 순서와 idempotency
- restart safety
- cancellation, retry, shutdown
- logging, metrics, processing event
- 실제 MSSQL 검증 누락

리뷰 결과는 수정하지 않고 findings로 남깁니다. 수정이 필요하면 다시 해당 owner workflow로 라우팅합니다.

### 7. Done phase

`done`은 구현을 더 하는 단계가 아닙니다.

해야 할 일:

- 변경 파일 요약
- acceptance criteria 충족 여부 기록
- verification 결과 기록
- 남은 risk와 follow-up 후보 기록
- `.planning/STATE.md`에 다음 action 하나를 명확히 남김
- `.scratch/phase-state.json`을 완료 상태 또는 다음 phase 진입 상태로 갱신

이 상태가 되어야 세션을 종료하거나 새 세션으로 넘겨도 작업이 끊기지 않습니다.

## Slash command와 workflow skill 매핑

| Command | Roo mode | Workflow skill | 사용 시점 |
| --- | --- | --- | --- |
| `/simple` | `orchestrator` | `workflow-simple-task` | 질문, 작은 문서 수정, 오타, 무해한 명령 실행, 기계적 정리, 즉시 검증 가능한 작은 변경을 처리합니다. |
| `/feature` | `orchestrator` | `workflow-feature-tdd` | 일반 application feature 또는 refactor. 더 좁은 owner가 없을 때 사용합니다. |
| `/bugfix` | `orchestrator` | `workflow-bug-diagnosis` | 버그, 실패 테스트, 잘못된 출력, 성능 회귀, 원인 불명 장애를 다룹니다. |
| `/etl` | `orchestrator` | `workflow-etl-pipeline` | parser, normalize, state, merge, buffer, write orchestration, replay, restart-safety를 다룹니다. |
| `/db` | `orchestrator` | `workflow-db-change` | MSSQL schema, EF migration, SQL, index, transaction, Dapper 예외, `SqlBulkCopy`, staging, `MERGE`를 다룹니다. |
| `/ops` | `orchestrator` | `workflow-ops-observability` | log, metric, processing event, retry, worker polling, graceful shutdown, dashboard, runbook을 다룹니다. |
| `/adr` | `architect` | `workflow-architecture-decision` | 설계 결정, 경계, 상태 모델, tradeoff, ADR, 구현 계획을 다룹니다. |
| `/review` | `review` | `workflow-code-review` | 코드, SQL, ETL, 테스트, 성능, 운영 리스크를 read-only로 리뷰합니다. |
| `/issues` | `docs-issues` | `workflow-docs-to-issues` | 요구사항과 설계 문서를 PRD, issue, acceptance criteria로 쪼갭니다. |

Slash command는 얇은 진입점입니다. 실제 라우팅 판단은 [.roo/rules-orchestrator/rules.md](.roo/rules-orchestrator/rules.md)에 있고, 상세 작업 절차는 [.roo/skills/](.roo/skills/)의 workflow skill에 있습니다.

## Workflow skill 설명

### `workflow-phase-gate`

모든 구현 workflow 앞에서 실행되는 gate입니다. `.planning/STATE.md`, `.planning/ROADMAP.md`, active checkpoint, `.scratch/phase-state.json`을 읽고 현재 허용 작업을 판정합니다.

이 skill은 구현을 막는 핵심 조건을 확인합니다.

- `phase`
- `plan_id`
- `approved`
- `state_path`
- `plan_path`
- `checkpoint_path`
- `current_checkpoint`
- `allowed_paths`
- `verification`

`execute` 조건이 부족하면 구현하지 않고 `discuss` 또는 `plan`으로 되돌립니다.

### `workflow-simple-task`

간단하고 낮은 위험의 작업을 위한 lightweight workflow입니다. `answer-only`, `docs-only`, `command-only`, `mechanical-code`, `tiny-behavior` 유형으로 분류하고, 각 유형에 맞는 최소 검증을 수행합니다. 작은 동작 변경은 기대 동작이 명확하고 focused test 또는 명령으로 즉시 증명될 때만 허용합니다. DB, ETL, ops, 보안, 배포, 아키텍처, public contract, 원인 불명 버그, 넓은 리팩토링이 걸리면 `/feature`, `/bugfix`, `/db`, `/etl`, `/ops`, `/adr` 중 맞는 경로로 라우팅합니다.

### `workflow-architecture-decision`

설계 결정 workflow입니다. 문제, 제약, 비목표, 선택지, tradeoff를 정리하고 durable decision이 필요하면 ADR로 남깁니다. 구현은 하지 않습니다. 구현이 필요하면 `/feature`, `/etl`, `/db`, `/ops` 중 적절한 workflow로 slice를 넘깁니다.

### `workflow-docs-to-issues`

요구사항, 설계 노트, 계획 문서를 PRD와 issue로 바꾸는 workflow입니다. 각 issue는 독립 구현 가능한 vertical slice여야 합니다. slice마다 owner mode, acceptance criteria, test expectation, dependency를 적습니다.

### `workflow-feature-tdd`

일반 application behavior 변경 workflow입니다. xUnit 실패 테스트를 먼저 만들고, FluentAssertions로 의도를 명확히 검증한 뒤 최소 구현을 합니다. SQL, ETL, ops 성격이 강해지면 해당 workflow로 넘깁니다.

### `workflow-bug-diagnosis`

버그를 재현, 축소, 가설 수립, 증거 확보, regression test 작성, 수정, 검증 순서로 처리합니다. 원인이 증거로 확인되기 전에는 증상 패치를 하지 않습니다.

### `workflow-etl-pipeline`

ETL 내부 동작을 다룹니다. stage 순서는 고정입니다.

```text
source -> parse -> normalize -> state -> merge -> buffer -> write -> observe
```

각 작업은 어떤 stage를 바꾸는지 명시해야 합니다. idempotency, restart safety, source traceability, bounded buffer, backpressure, replay behavior를 계획 단계에서 드러냅니다.

### `workflow-db-change`

MSSQL schema, migration, query, index, transaction, bulk write를 다룹니다. EF Core가 기본이고, Dapper는 문서화된 복잡/성능 read-query 예외에만 사용합니다. ETL write는 기본적으로 `SqlBulkCopy` to staging + set-based `MERGE`/upsert입니다.

### `workflow-ops-observability`

운영 신호를 다룹니다. structured log, metric, processing event, retry boundary, worker lifecycle, graceful shutdown, dashboard, runbook이 대상입니다. persistence와 연결된 운영 동작은 실제 MSSQL 검증을 요구합니다.

### `workflow-code-review`

read-only 리뷰 workflow입니다. findings를 심각도순으로 제시하고, 파일/라인 근거를 붙입니다. 수정이 필요하면 직접 고치지 않고 올바른 owner workflow로 넘깁니다.

## Mode 소유권

| Mode | 수정 가능 | 수정 금지 |
| --- | --- | --- |
| `orchestrator` | 읽기와 라우팅 | 구현 코드, agent-control 파일 |
| `architect` | `docs/`, `.planning/`, `.scratch/` tracker 파일 | `.roomodes`, `.roo/**`, `AGENTS.md`, `CLAUDE.md`, `.scratch/phase-state*.json` |
| `docs-issues` | `docs/`, `.planning/`, `.scratch/` tracker 파일 | agent-control 파일, phase approval JSON |
| `tdd-code` | 승인된 plan의 application code | docs, `.planning/`, `.scratch/`, Roo harness 파일 |
| `etl-pipeline` | 승인된 plan의 ETL/application code | docs, `.planning/`, `.scratch/`, Roo harness 파일 |
| `db-migration` | 승인된 plan의 DB/application code | docs, `.planning/`, `.scratch/`, Roo harness 파일 |
| `diagnose` | 승인된 plan의 bugfix code | docs, `.planning/`, `.scratch/`, Roo harness 파일 |
| `ops-observability` | 승인된 plan의 ops/application code | docs, `.planning/`, `.scratch/`, Roo harness 파일 |
| `review` | 읽기 전용 | 수정, mutation-capable command |
| `harness-maintainer` | `.roomodes`, `.roo/**`, phase approval JSON, `AGENTS.md`, `CLAUDE.md` | application 구현 |

중요한 점은 planning mode가 `.planning/`을 유지하고, implementation mode는 `.planning/`을 건드리지 않는다는 것입니다.

## Phase gate 상세

| Phase | 허용 작업 | 종료 조건 |
| --- | --- | --- |
| `discuss` | 읽기, 탐색, 질문, risk 정리 | 충분히 알게 되면 `plan`으로 이동 |
| `plan` | 문서, ADR, PRD, issue plan, acceptance criteria, verification 계획 | 사용자 또는 승인자가 `execute` 승인 |
| `execute` | 승인된 `plan_id`와 `allowed_paths` 안의 구현 및 검증 | verification 통과 후 `done` |
| `done` | 요약, 검증 증거, follow-up 정리 | 새 작업은 새 `discuss`로 시작 |

관련 문서:

- [docs/phase-gate-harness.md](docs/phase-gate-harness.md)
- [.roo/rules/phase-gate.md](.roo/rules/phase-gate.md)
- [.scratch/phase-state.example.json](.scratch/phase-state.example.json)

## 문서 중심 관리 구조

| Path | 역할 |
| --- | --- |
| [.planning/STATE.md](.planning/STATE.md) | 현재 phase, checkpoint, blocker, next action |
| [.planning/ROADMAP.md](.planning/ROADMAP.md) | phase 경계, 의존성, success criteria |
| [.planning/REQUIREMENTS.md](.planning/REQUIREMENTS.md) | durable requirement |
| [.planning/DECISIONS.md](.planning/DECISIONS.md) | phase를 가로지르는 결정 |
| `.planning/phases/<phase>/` | phase context, plan, checkpoint, review, verification, summary |
| [.planning/VERIFICATION.md](.planning/VERIFICATION.md) | 전역 검증 evidence ledger |
| [.scratch/phase-state.json](.scratch/phase-state.json) | live phase gate |

Phase 폴더 기본 패턴:

```text
.planning/phases/<NN-phase-slug>/
  NN-CONTEXT.md
  NN-01-PLAN.md
  NN-CHECKPOINTS.md
  NN-REVIEW.md
  NN-VERIFICATION.md
  NN-01-SUMMARY.md
```

큰 phase는 `NN-02-PLAN.md`, `NN-02-SUMMARY.md`처럼 plan을 여러 개로 나눕니다.

## 구현 workflow 예시

예를 들어 “새 ETL parser 기능을 추가해줘”라는 요청이 들어오면 흐름은 다음과 같습니다.

1. `orchestrator`가 `/etl`로 라우팅합니다.
2. `workflow-phase-gate`가 현재 phase를 확인합니다.
3. `discuss`라면 source format, output contract, existing parser, risk를 읽기만 합니다.
4. `plan`이라면 `.planning/phases/.../NN-01-PLAN.md`에 stage, acceptance criteria, allowed paths, verification을 씁니다.
5. 승인자가 `.scratch/phase-state.json`을 `phase=execute`, `approved=true`로 맞춥니다.
6. `execute`에서 `workflow-etl-pipeline`이 red test를 먼저 만듭니다.
7. parser/normalize/state 중 어느 stage가 바뀌는지 명시합니다.
8. 최소 구현 후 focused test를 통과시킵니다.
9. DB writer까지 영향을 주면 `/db` slice로 분리합니다.
10. 운영 신호가 필요하면 `/ops` slice로 분리합니다.
11. verification 결과를 phase 문서에 기록합니다.
12. `/review`로 read-only 리뷰를 수행합니다.
13. 모든 기준을 만족하면 `done`으로 닫고 `.planning/STATE.md`의 next action을 갱신합니다.

## 검증 명령

```bash
jq . .roomodes >/dev/null
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.json
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.example.json
```

README와 실제 Roo 설정이 어긋나는지 확인하려면 command, mode, skill 이름을 함께 검색합니다.

```bash
rg -n "workflow-simple-task|workflow-feature-tdd|workflow-etl-pipeline|workflow-db-change|workflow-phase-gate" README.md .roo
```

현재 상태와 다음 작업은 항상 [.planning/STATE.md](.planning/STATE.md)에서 시작합니다.
