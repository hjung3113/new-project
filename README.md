# Roo C# ETL 오케스트레이션 템플릿

이 저장소는 C#/.NET 10 + Microsoft SQL Server 기반 ETL 프로젝트를 Roo Code로 운영하기 위한 에이전트 하네스입니다. 애플리케이션 구현체가 아니라, Roo 모드, slash command, workflow skill, 라우팅 규칙, phase gate, 문서 중심 계획 체계를 제공하는 템플릿입니다.

목표는 단순합니다. 작업이 커져도 에이전트가 즉흥적으로 코드를 만지지 않고, 설계 문서와 phase/checkpoint를 기준으로 계획, 승인, 구현, 검증, 종료까지 이어가게 만드는 것입니다. 세션을 초기화해도 [.planning/STATE.md](.planning/STATE.md)에서 현재 위치와 다음 행동을 복구할 수 있어야 합니다.

## 목차

- [핵심 원칙](#핵심-원칙)
- [오케스트레이터/서브태스크 실행 모델](#오케스트레이터서브태스크-실행-모델)
- [새 세션 시작 순서](#새-세션-시작-순서)
- [하네스 배포와 업데이트](#하네스-배포와-업데이트)
- [큰 작업 흐름](#큰-작업-흐름)
- [자동 진행 플래그](#자동-진행-플래그)
- [Slash command와 workflow skill 매핑](#slash-command와-workflow-skill-매핑)
- [Workflow skill 설명](#workflow-skill-설명)
- [DB context snapshot](#db-context-snapshot)
- [Mode 소유권](#mode-소유권)
- [Phase gate 상세](#phase-gate-상세)
- [문서 중심 관리 구조](#문서-중심-관리-구조)
- [구현 workflow 예시](#구현-workflow-예시)
- [검증 명령](#검증-명령)

## 핵심 원칙

- 모든 요청은 하나의 소유 workflow로 라우팅합니다.
- 질문, 작은 문서 수정, 오타, 무해한 명령 실행, 기계적 정리, 즉시 검증 가능한 작은 변경은 `/simple`로 처리할 수 있습니다.
- 구현은 반드시 phase별 `discuss -> plan -> execute -> done` gate를 통과합니다.
- 동작 변경은 TDD로 진행합니다. 먼저 실패 증거를 만들고, 최소 변경으로 green을 만든 뒤 refactor합니다.
- SQL, migration, writer, transaction, restart, idempotency는 mock이나 SQLite가 아니라 `testcontainers-dotnet` + 실제 MSSQL 컨테이너로 검증합니다.
- `.planning/`은 영속적인 프로젝트 기억입니다. `.scratch/phase-state.json`은 현재 phase에서 허용된 작업을 나타내는 live gate일 뿐입니다.
- planning 문서, Roo 설정, tracker, application code의 소유권을 mode별로 분리합니다.
- [AGENTS.md](AGENTS.md)에는 [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)를 참고한 coding conduct 규칙을 추가했습니다.

## 오케스트레이터/서브태스크 실행 모델

메인 orchestrator 세션은 의도적으로 작게 유지합니다. 요청을 분류하고, workflow를 고르고, owning mode에 집중된 subtask를 만들고, 구조화된 결과를 수집한 뒤 최종 상태를 보고합니다.

즉 planning, review, implementation, debugging, verification 같은 실제 작업은 specialist mode가 수행하고, orchestrator는 non-trivial step을 inline으로 실행하지 않습니다.

## 새 세션 시작 순서

새 Roo 세션, 새 에이전트, 또는 대화 컨텍스트가 초기화된 경우 반드시 아래 순서로 읽습니다.

1. [AGENTS.md](AGENTS.md)
2. [.planning/STATE.md](.planning/STATE.md)
3. [.planning/ROADMAP.md](.planning/ROADMAP.md)
4. `.planning/codebase/ARCHITECTURE.md`, `STACK.md`, `STRUCTURE.md`, `CONVENTIONS.md`, `TESTING.md`, `INTEGRATIONS.md`, `CONCERNS.md`
5. 현재 phase의 `.planning/phases/**/**-CHECKPOINTS.md`
6. 현재 phase의 context, plan, review, verification, summary 문서
7. [.scratch/phase-state.json](.scratch/phase-state.json)

이 순서를 지키면 이전 대화 기록 없이도 현재 phase, checkpoint, blocker, next action, 승인된 plan, 허용 경로를 복구할 수 있습니다.

## 하네스 배포와 업데이트

이 저장소는 하네스 개발 repo이고, 타겟 프로젝트는 이 repo의 `.git` 이력을 포함하지 않아도 됩니다. 배포는 `harness/manifest.json`과 `harness/skeleton/clean/`을 기준으로 합니다.

```bash
python3 scripts/harness.py init --target /path/to/project
python3 scripts/harness.py upgrade --target /path/to/project
python3 scripts/harness.py check
python3 scripts/harness.py doctor
```

현재 작업 현황을 사람이 빠르게 훑어보려면 정적 HTML 대시보드를 생성합니다.

```bash
python3 scripts/project_dashboard.py
```

이 명령은 `.planning/**`, `.scratch/**`, `docs/**`, `README.md`, `AGENTS.md`를 읽고 [.scratch/reports/project-dashboard.html](.scratch/reports/project-dashboard.html)을 만듭니다. 생성된 HTML은 커밋하지 않는 로컬 산출물이며, roadmap은 `Done / In Progress / Remaining` 칸반으로 표시됩니다.

대시보드는 특히 “지금이 discuss, plan, execute, done 중 어디인가?”를 빠르게 확인하는 용도입니다. `Gate Details`에는 `.scratch/phase-state.json`의 `phase`, `plan_id`, 승인 여부, 승인자, 승인 시각, `current_checkpoint`, `automation_mode`, durable 문서 포인터, next action이 표시됩니다. `Live Gate`에는 acceptance criteria, verification commands, allowed paths, blocked paths, notes가 표시됩니다. `.planning/STATE.md`와 `.scratch/phase-state.json`이 서로 다른 checkpoint를 가리키거나 roadmap progress가 어긋나면 warning으로 노출됩니다.

현재 이 하네스 개발 repo의 durable state는 Phase 5 `discuss`입니다. PR #21까지 merge되어 Phase 4의 roadmap/state sync, Windows-compatible DB snapshot controls, harness doctor, phase command distribution/routing이 적용되었습니다. 다음 큰 작업은 Phase 5 alignment를 진행하는 것이고, 작은 README/dashboard 정리는 명시적으로 요청된 경우 `/simple` 경로로 처리할 수 있습니다.

`init`은 깨끗한 project-owned planning skeleton을 타겟에 설치합니다. 기존 파일이 있으면 덮어쓰지 않고 중단합니다.
설치되는 `AGENTS.md`에는 `Think Before Coding`, `Simplicity First`, `Surgical Changes`, `Goal-Driven Execution` 기본 지침이 포함됩니다.

`upgrade`는 새 하네스 소스에서 타겟을 지정해 실행합니다. manifest에서 `harness-owned` 또는 `managed`로 분류된 파일만 갱신하고, `.planning/STATE.md`, `.planning/phases/**`, `.scratch/phase-state.json`처럼 프로젝트 진행 상태가 담기는 파일은 보존합니다. 하네스 소유 파일을 타겟에서 수정한 경우에는 `.harness/conflicts/**/*.new`에 새 버전을 남기고 충돌을 보고합니다.

`check`는 JSON 구문, phase-state automation semantics, Roo command/mode 일치, clean skeleton 오염, stale phase 번호, roadmap/state 동기화, 선택적 changed-path enforcement를 검증합니다. changed-path 검증은 `phase=execute` 또는 `phase=done`, `approved=true`, `allowed_paths`가 있는 상태에서 사용합니다.

`doctor`는 read-only 진단 리포트입니다. 주요 planning 문서, Roo command/mode, DB context 설정, diff-before-mutation 흐름을 점검하고 각 항목을 severity, cause, impact, fix, evidence로 보여줍니다. 수정은 자동 적용하지 않습니다.

파일 소유권은 다음 기준을 따릅니다.

| 분류 | 예시 | upgrade 동작 |
| --- | --- | --- |
| `harness-owned` | `.roo/**`, `.roomodes`, `.scratch/phase-state.schema.json`, `.scratch/phase-state.example.json`, `scripts/harness.py` | 설치된 hash와 다르면 충돌 보고, 아니면 갱신 |
| `managed` | `AGENTS.md`, `README.md` | 정책상 managed-block merge 대상입니다. 현재 구현은 파일 단위 충돌 보고이며, block marker/merge/dry-run/rollback 검증이 추가되기 전까지 자동 block 병합을 수행하지 않습니다. |
| `project-owned` | `.planning/**`, `.scratch/phase-state.json` | init 때만 생성, upgrade는 보존 |
| `exclude` | `.git`, `.db-context/**`, generated artifacts | 설치/업그레이드 대상 아님 |

clean skeleton에는 특정 프로젝트명, 완료된 phase 기록, PR 번호, live DB snapshot 진행 상태가 들어가면 안 됩니다. 그런 정보는 하네스 개발 repo의 `.planning/**` 또는 타겟 프로젝트의 project-owned 문서에만 둡니다.

## 큰 작업 흐름

아래 흐름은 “아무것도 없는 0부터 시작하는 경우”, “이미 코드와 문서가 있는 기존 프로젝트에 하네스를 적용하는 경우”, “이미 설계 문서가 있는 경우”를 구분합니다.

단, 작업이 작고 되돌리기 쉬우며 검증 방법이 명확한 경우에는 `/simple` + `workflow-simple-task`를 사용할 수 있습니다. 이 경로는 phase gate를 무시하는 통로가 아니라, 질문 답변, 오타 수정, 짧은 README 문구 추가, 무해한 스크립트 실행, 기계적 코드 정리, focused test로 즉시 증명되는 작은 변경을 가볍게 처리하는 통로입니다. DB, ETL, ops, 보안, 배포, 아키텍처, public contract, 원인 불명 버그, 넓은 리팩토링이 걸리면 즉시 일반 workflow로 되돌립니다.

### 1. 0부터 시작할 때

사용자가 아이디어만 가지고 있다면 먼저 구현하지 않습니다. `orchestrator`가 요청을 분류하고, 보통 `/adr` 또는 `/issues` 계열 planning workflow로 보냅니다.

1. 먼저 `grill-me` 방식으로 한 번에 하나씩 묻습니다. 각 질문에는 모델의 추천 답과 이유를 같이 제시합니다.
2. repo나 문서에서 답할 수 있는 질문은 사용자에게 묻지 말고 직접 확인합니다.
3. 문제, 사용자, 목표, 비목표, 제약, tradeoff, phase granularity, 첫 usable slice, 성공 기준, verification evidence를 맞춥니다.
4. alignment summary를 남깁니다: 확인된 사실, repo에서 추론한 사실, 사용자 선호, 추천 default, 열린 질문, 열린 질문 때문에 막힌 결정.
5. 기존 문서가 없으면 `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`를 만듭니다.
6. 사용자가 확인했거나 repo evidence로 증명된 내용만 milestone과 phase로 나눕니다. 추론만 있는 선호는 phase 성공 기준으로 굳히지 않습니다.
7. 초안 phase를 확정하기 전에 적대적 전문가 2명과 각 3개 관점으로 리뷰합니다.
8. 필수 리뷰 관점으로 “저추론 모델도 align될 만큼 질문이 구체적인가?”를 포함합니다.
9. 각 phase에 phase-local `discuss -> plan -> execute -> done` 흐름, 성공 기준, 의존성, gate, 예상 verification을 씁니다.
10. 첫 phase 폴더를 만들고 `NN-CONTEXT.md`, `NN-01-PLAN.md`, `NN-CHECKPOINTS.md`, `NN-REVIEW.md`, `NN-VERIFICATION.md`, `NN-01-SUMMARY.md` 형태의 문서를 둡니다.
11. `.scratch/phase-state.json`은 아직 구현 승인 전이면 `discuss` 또는 `plan` 상태로 둡니다.

이 단계의 산출물은 코드가 아니라 결정과 계획입니다. 구현은 사용자가 `execute`를 승인한 뒤에만 시작합니다.

### 2. 기존 프로젝트에 하네스를 적용할 때

이미 코드, README, 테스트, ADR, 이슈, 또는 이전 planning 문서가 있는 저장소라면 일반적인 `project init`처럼 템플릿을 덮어쓰지 않습니다. 먼저 `workflow-planning-hydration`으로 현재 저장소를 읽고 `.planning/`을 채웁니다.

1. README, build/test 파일, source/test 폴더, docs, ADR, 기존 `.planning/**`, `.scratch/**`를 inventory합니다.
2. repo가 답할 수 없는 제품 의도와 phase 경계는 `grill-me` 방식으로 한 번에 하나씩 묻고, 추천 답과 이유를 같이 제시합니다.
3. alignment summary를 active phase context나 `.planning/PROJECT.md`에 남깁니다.
4. phase 초안을 만들기 전에 적대적 전문가 2명과 각 3개 관점으로 리뷰하고 보강 포인트를 반영합니다.
5. 기존 planning 상태를 `absent`, `template-only`, `stale`, `partial`, `usable` 중 하나로 분류합니다.
6. `.planning/codebase/**`를 실제 저장소 기준으로 채웁니다.
7. active `.planning/phases/**` 문서 세트를 만들거나 현재 프로젝트 기준으로 보정합니다. 새 phase는 항상 phase-local `discuss`부터 시작합니다.
8. 이전 프로젝트나 템플릿 잔여 planning 문서를 `keep`, `archive`, `delete candidate`, `needs-human`으로 분류합니다.
9. `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/DECISIONS.md`, `.planning/VERIFICATION.md`를 현재 프로젝트 기준으로 동기화합니다.
10. `.scratch/phase-state.json`은 명시적으로 phase-state 수정을 요청받았거나 phase-state repair가 범위일 때만 갱신합니다.

이 단계가 끝나기 전에는 `/adr`, `/issues`, `/feature`, `/bugfix`, `/etl`, `/db`, `/ops`가 `.planning/`을 신뢰하면 안 됩니다.

#### 기존 프로젝트 적용 프롬프트 예시

기존 프로젝트에 하네스를 적용할 때는 “분석 범위”, “건드려도 되는 파일”, “산출물”, “멈춰야 하는 조건”을 프롬프트에 명시합니다. 아래 예시는 그대로 붙여 넣고 프로젝트 상황만 바꿔 쓰는 용도입니다.

**전체 repo를 처음 분석할 때**

```text
이 저장소에 Roo/Codex 하네스를 적용하려고 한다.
먼저 구현하지 말고 workflow-planning-hydration으로 현재 repo를 inventory해라.
README, build/test 설정, src/tests, docs, ADR, 기존 .planning/.scratch 상태를 읽고
.planning/codebase/**와 active phase 문서를 현재 repo 기준으로 채우는 계획을 세워라.
repo가 답할 수 있는 내용은 직접 확인하고, 제품 의도나 phase 경계처럼 repo가 답할 수 없는 질문만 한 번에 하나씩 물어라.
stale/template/previous-project planning 문서는 keep/archive/delete candidate/needs-human으로 분류하고 삭제하지 마라.
```

**일부 범위만 분석하면 될 때**

```text
하네스를 이 repo 전체가 아니라 <범위>에 먼저 적용하고 싶다.
분석 범위는 <예: ingestion pipeline, billing module, docs/adr only, src/Foo + tests/FooTests>로 제한해라.
범위 밖 파일은 ownership, dependency, risk 파악에 필요한 경우에만 읽고 수정하지 마라.
.planning/codebase/**에는 전체 repo를 아는 척하지 말고, 확인된 범위와 확인하지 않은 범위를 분리해서 기록해라.
첫 phase도 이 범위 안의 smallest usable slice로만 제안해라.
```

**기존 `.planning/`이 있는데 신뢰하기 어려울 때**

```text
이 repo에는 이미 .planning/과 .scratch/phase-state.json이 있지만 최신 상태인지 모르겠다.
구현하지 말고 planning hydration/reconciliation만 수행해라.
현재 문서를 absent/template-only/stale/partial/usable로 판정하고,
repo evidence와 충돌하는 문장을 파일별로 찾아라.
고칠 수 있는 문서 보정안과 사람 확인이 필요한 결정은 분리해라.
phase-state는 내가 명시적으로 승인하기 전까지 execute로 바꾸지 마라.
```

**이미 PRD/ADR/설계 문서가 있을 때**

```text
<문서 경로>를 기준으로 하네스 planning을 맞춰라.
문서를 요구사항, 결정, 열린 질문, 구현 slice 후보로 분해해라.
.planning/codebase/**가 없거나 stale이면 먼저 현재 repo 분석으로 되돌아가라.
바로 구현하지 말고 /issues 또는 /adr에 넘길 수 있는 phase-local discuss summary와 첫 plan 후보를 작성해라.
각 slice에는 owner workflow, allowed_paths 후보, verification 후보를 붙여라.
```

**DB/ETL 의존 코드가 있는 프로젝트일 때**

```text
이 repo는 DB/ETL 동작이 중요하다.
하네스 적용 전 .db-context/latest.json이 있는지 확인하고, 없거나 부족하면 needs-db-context를 반환해라.
DB schema, migration, stored procedure, SQL Agent job, writer/restart/idempotency 판단은 추측하지 마라.
planning에는 어떤 판단이 repo 파일만으로 가능하고 어떤 판단이 DB snapshot을 요구하는지 분리해서 기록해라.
```

**작은 문서/설정 변경만 필요할 때**

```text
이번 요청은 application behavior가 아니라 작은 docs-only 하네스 변경이다.
/simple로 처리하되 AGENTS.md, .planning/STATE.md, active checkpoint, .scratch/phase-state.json을 읽고
allowed_paths 안에서만 수정해라.
변경 후 README/AGENTS/planning 간 restart order나 workflow 이름이 어긋나지 않는지 rg로 확인하고,
필요한 최소 harness check만 실행해라.
```

**하네스 설치 후 첫 feature를 시작할 때**

```text
이제 하네스가 설치된 기존 프로젝트에서 첫 feature phase를 시작하려고 한다.
바로 구현하지 말고 이 feature 전용 discuss pass부터 시작해라.
현재 .planning/codebase/**가 이 repo를 정확히 설명하는지 확인하고,
첫 usable slice, 비목표, allowed_paths 후보, verification 후보를 정리해라.
phase plan을 쓰기 전 적대적 전문가 2명과 각 3개 관점으로 리뷰하고,
저추론 모델도 실행할 수 있을 만큼 질문과 acceptance criteria가 구체적인지 확인해라.
```

**리뷰 또는 점검만 하고 싶을 때**

```text
이 요청은 read-only review다.
파일을 수정하지 말고 하네스 적용 상태를 점검해라.
AGENTS.md, README.md, .planning/STATE.md, .planning/ROADMAP.md,
.planning/codebase/**, active phase docs, .scratch/phase-state.json이 서로 같은 현재 위치를 가리키는지 확인해라.
문제는 severity 순으로 파일/라인 근거와 함께 보고하고, 수정은 별도 요청 전까지 하지 마라.
```

#### 기존 프로젝트 적용 체크리스트

- 먼저 `python3 scripts/harness.py init --target /path/to/project`로 하네스를 설치하되, 기존 파일 충돌이 있으면 멈추고 diff를 검토합니다.
- 설치 직후에는 target repo 안에서 `python3 scripts/harness.py check`를 실행합니다.
- `.planning/codebase/**`가 template placeholder라면 어떤 workflow도 구현을 시작하지 않습니다.
- 분석 범위를 전체 repo로 할지, 특정 subsystem으로 할지 먼저 정합니다.
- 이전 프로젝트 이름, 완료된 phase, PR 번호, 다른 stack의 테스트 명령이 남아 있으면 stale planning으로 분류합니다.
- `.scratch/phase-state.json`은 full planning memory가 아니라 현재 허용 작업의 gate입니다. planning hydration만 하는 동안에는 execute 승인을 만들지 않습니다.
- application code 변경은 `phase=execute`, `approved=true`, 같은 `plan_id`, `allowed_paths`, `verification`이 모두 맞을 때만 시작합니다.

### 3. 설계 문서가 이미 있을 때

요구사항 문서, 설계 문서, ADR, PRD, 또는 외부 명세가 있다면 `/issues` 또는 `/adr`로 시작합니다.

1. 원본 문서를 읽고 고정 요구사항과 열린 질문을 분리합니다.
2. `.planning/codebase/**`와 active `.planning/phases/**`가 없거나 stale이면 먼저 `workflow-planning-hydration`으로 되돌립니다.
3. 결정이 필요한 부분은 `/adr` + `workflow-architecture-decision`으로 보냅니다.
4. ADR이나 phase plan을 쓰기 전에 사용자 의도, tradeoff, 비목표, 성공 기준, verification을 alignment summary로 확정합니다.
5. 확정 전 적대적 전문가 2명과 각 3개 관점으로 리뷰하고 보강 포인트를 반영합니다.
6. 구현 가능한 단위는 `/issues` + `workflow-docs-to-issues`로 vertical slice issue로 쪼갭니다.
7. 각 slice에 추천 owner mode를 붙입니다.
8. DB, ETL, ops, 일반 feature가 섞여 있으면 한 issue에 몰아넣지 않고 workflow별로 나눕니다.
9. `.planning/ROADMAP.md`와 active phase checkpoint에 현재 위치를 반영합니다.

설계 문서가 있다고 해서 바로 구현하지 않습니다. 설계 문서는 plan의 입력이고, 구현 권한은 `.scratch/phase-state.json`의 `phase=execute`, `approved=true`, `plan_id`, `allowed_paths`, `verification`이 맞을 때만 열립니다.

### 4. Discuss phase

`discuss`는 읽기 전용입니다. 모든 roadmap phase는 phase-local `discuss`부터 시작합니다. 이전 phase가 `done`이어도 다음 phase로 바로 `plan`을 쓰지 않습니다.

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

phase-local `discuss` 산출물:

- 이 phase가 풀 문제
- target user 또는 operator
- 비목표와 명시적으로 원하지 않는 작업
- 첫 usable slice
- repo evidence로 답할 수 있는 질문
- 사용자 선호가 필요한 질문
- 추천 default
- verification evidence 후보

### 5. Plan phase

`plan`은 문서화와 실행 계획 작성 단계입니다.

허용되는 작업:

- PRD, ADR, checklist, issue plan 작성
- 기존 프로젝트 planning hydration과 stale planning reconciliation
- `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/codebase/**`, phase context/checkpoint 갱신
- acceptance criteria 작성
- verification command 작성
- 구현 범위와 소유 mode 결정
- `allowed_paths` 후보 정의

금지되는 작업:

- application behavior 변경
- source, migration, generated artifact, test implementation 수정
- dependency 설치나 code generator 실행

plan이 끝나면 에이전트는 멈추고 승인을 기다립니다. 승인 전에는 execute로 넘어가지 않습니다.

단, 사용자가 `--chain`을 명시한 경우에는 plan이 concrete하고 `allowed_paths`, `verification`, durable planning pointer가 모두 있으며 적대적 리뷰의 P1 blocker가 없을 때 같은 phase 안에서 execute까지 진행할 수 있습니다.

### 6. Execute phase

`execute`는 승인된 구현 단계입니다. 이 phase에서는 매 응답 또는 작업 단위가 다음 조건을 만족해야 합니다.

- `phase=execute`
- `approved=true`
- 승인된 `plan_id`
- 비어 있지 않은 `allowed_paths`
- 비어 있지 않은 `verification`
- 현재 요청이 승인된 plan 범위 안에 있음
- `.planning/codebase/**`와 active phase 문서가 승인된 plan 기준으로 stale하지 않음

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

### 7. Review phase 또는 review pass

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
- `.planning/**`과 `.scratch/phase-state.json`이 변경 내용과 맞는지

리뷰 결과는 수정하지 않고 findings로 남깁니다. 수정이 필요하면 다시 해당 owner workflow로 라우팅합니다.

### 8. Done phase

`done`은 구현을 더 하는 단계가 아닙니다.

해야 할 일:

- 변경 파일 요약
- acceptance criteria 충족 여부 기록
- verification 결과 기록
- 남은 risk와 follow-up 후보 기록
- `.planning/STATE.md`에 다음 action 하나를 명확히 남김
- active phase checkpoint, verification, summary 문서 갱신
- `.scratch/phase-state.json`을 완료 상태 또는 다음 phase 진입 상태로 갱신

이 상태가 되어야 세션을 종료하거나 새 세션으로 넘겨도 작업이 끊기지 않습니다.

## 자동 진행 플래그

Roo slash command 인자나 task prompt에 아래 플래그를 붙일 수 있습니다. 플래그는 phase gate를 약화하지 않고 선택 처리 방식만 바꿉니다.

### `--auto`

`--auto`는 blocking이 아닌 선택을 모델의 recommended answer로 자동 채택합니다.

규칙:

- repo evidence로 답할 수 있으면 사용자에게 묻지 않고 직접 확인합니다.
- documentation wording, ordering, naming, repo-proven default처럼 되돌릴 수 있고 낮은 위험이며 현재 허용 작업 안에 있는 선택만 자동 채택합니다.
- product scope, user audience, phase boundary, external integration, auth/security, deployment, data deletion, dependency addition, verification removal은 자동 채택하지 않습니다.
- 자동 채택한 항목은 `.scratch/phase-state.json`의 `auto_selected` 또는 active phase context에 `choice`, `selected_value`, `reason`, `evidence_path`, `risk_level`, `reversible`, `inside_allowed_paths`, `stop_conditions_checked`로 기록합니다.
- destructive action, 외부 시스템, secret, 배포, 구매, 삭제, 넓은 scope, 여러 제품 방향이 가능한 phase boundary, verification이 없는 작업은 멈추고 질문합니다.

### `--chain`

`--chain`은 추천값으로 같은 phase의 `discuss -> plan -> execute`를 이어서 진행합니다.

조건:

- phase-local `discuss` summary가 있어야 합니다.
- plan에는 `plan_id`, `allowed_paths`, acceptance criteria, verification, durable planning pointer가 있어야 합니다.
- 적대적 리뷰에서 unresolved P1 blocker가 없어야 합니다.
- execute 전 `.scratch/phase-state.json`이 `phase=execute`, 같은 `plan_id`, `approved=true`, `automation_mode=chain`, 비어 있지 않은 `allowed_paths`, 비어 있지 않은 `verification`을 가진 상태로 기록되거나 검증되어야 합니다.
- execute는 생성된 하나의 plan 안에서만 진행합니다.
- 새 follow-up phase나 범위 확장은 새 phase-local `discuss`로 돌아갑니다.

`--chain`도 destructive/external/security-sensitive/irreversible 작업은 자동으로 넘기지 않습니다.

## Slash command와 workflow skill 매핑

| Command | Roo mode | Workflow skill | 사용 시점 |
| --- | --- | --- | --- |
| `/simple` | `orchestrator` | `workflow-simple-task` | 질문, 작은 문서 수정, 오타, 무해한 명령 실행, 기계적 정리, 즉시 검증 가능한 작은 변경을 처리합니다. |
| 기존 프로젝트 planning 채우기 | `orchestrator` | `workflow-planning-hydration` | 기존 프로젝트에 하네스를 적용했거나 `.planning/codebase/**`, `.planning/phases/**`가 없거나 stale일 때 사용합니다. |
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

모든 구현 workflow 앞에서 실행되는 gate입니다. `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/codebase/**`, active checkpoint, active phase docs, `.scratch/phase-state.json`을 읽고 현재 허용 작업을 판정합니다.

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
- planning context freshness
- `automation_mode`
- `auto_selected`

`execute` 조건이 부족하거나 planning context가 stale이면 구현하지 않고 `discuss` 또는 `plan`으로 되돌립니다.

### `workflow-planning-hydration`

기존 프로젝트에 이 하네스를 적용할 때 사용하는 planning 전용 workflow입니다. 일반적인 `project init`처럼 템플릿을 덮어쓰지 않고, 실제 저장소를 inventory한 뒤 사용자와 phase 경계 및 첫 usable slice를 맞춥니다. phase 초안은 적대적 전문가 2명과 각 3개 관점으로 리뷰하고, 저추론 모델도 따라갈 수 있는 질문 구체성을 확인합니다. 그 다음 `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/codebase/**`, active `.planning/phases/**`를 현재 프로젝트 기준으로 채웁니다. stale planning 파일은 `keep`, `archive`, `delete candidate`, `needs-human`으로 분류하고, 모호한 파일은 삭제하지 않습니다.

### `workflow-simple-task`

간단하고 낮은 위험의 작업을 위한 lightweight workflow입니다. `answer-only`, `docs-only`, `command-only`, `mechanical-code`, `tiny-behavior` 유형으로 분류하고, 각 유형에 맞는 최소 검증을 수행합니다. 작은 동작 변경은 기대 동작이 명확하고 focused test 또는 명령으로 즉시 증명될 때만 허용합니다. DB, ETL, ops, 보안, 배포, 아키텍처, public contract, 원인 불명 버그, 넓은 리팩토링이 걸리면 `/feature`, `/bugfix`, `/db`, `/etl`, `/ops`, `/adr` 중 맞는 경로로 라우팅합니다.

### `workflow-architecture-decision`

설계 결정 workflow입니다. 문제, 제약, 비목표, 선택지, tradeoff를 정리하고 durable decision이 필요하면 ADR로 남깁니다. ADR이나 phase 성공 기준을 쓰기 전에는 `grill-me` 방식으로 사용자 의도를 맞추고 alignment summary를 남긴 뒤, 적대적 전문가 2명과 각 3개 관점으로 초안을 리뷰합니다. 필수 관점은 “저추론 모델도 align될 만큼 질문이 구체적인가?”입니다. `.planning/codebase/**` 또는 active `.planning/phases/**`가 없거나 stale이면 먼저 `workflow-planning-hydration`으로 되돌립니다. 구현은 하지 않습니다. 구현이 필요하면 `/feature`, `/etl`, `/db`, `/ops` 중 적절한 workflow로 slice를 넘깁니다.

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

## DB context snapshot

DB, ETL, review, ops workflow가 실제 MSSQL schema, index, stored procedure, function, view, trigger, SQL Agent job에 의존하는 판단을 해야 할 때는 먼저 `.db-context/` snapshot을 봅니다.

기본 동작은 cache-first입니다. snapshot이 있으면 agent는 DB에 접속하지 않고 `.db-context/latest.json`을 읽습니다. 필요한 snapshot이 없거나 오래되었거나 부족하면 추측하지 않고 `needs-db-context`를 반환합니다.

명시적으로 DB context refresh가 필요할 때만 아래 명령을 실행합니다.

```bash
python3 scripts/db_context_snapshot.py --refresh
```

SQL Agent job schedule이나 job step까지 필요하면 `--include-agent-jobs`를 함께 사용합니다.

```bash
python3 scripts/db_context_snapshot.py --refresh --include-agent-jobs
```

연결 문자열은 commit하지 않습니다. 환경 변수나 CLI 인자로만 전달합니다.

```bash
export DB_CONTEXT_MASTER_CONNECTION="Driver={ODBC Driver 18 for SQL Server};Server=...;Database=MasterDb;..."
export DB_CONTEXT_PROCESS_CONNECTIONS='{
  "process-a": "Driver={ODBC Driver 18 for SQL Server};Server=...;Database=ProcessA;...",
  "process-b": "Driver={ODBC Driver 18 for SQL Server};Server=...;Database=ProcessB;..."
}'
```

snapshot 파일은 민감할 수 있으므로 `.db-context/`와 생성된 SQL/job artifact는 gitignore 대상입니다. Stored procedure 본문이나 job command에는 secret, server name, file path, 업무상 민감한 object name이 들어갈 수 있습니다.

자세한 설계와 threat model은 [docs/db-context-snapshot.md](docs/db-context-snapshot.md)를 봅니다.

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
| `harness-maintainer` | `.roomodes`, `.roo/**`, `harness/**`, `scripts/harness.py`, `scripts/test_harness.py`, phase approval JSON, `AGENTS.md`, `CLAUDE.md`, 하네스 문서 | application 구현 |

중요한 점은 planning mode가 `.planning/`을 유지하고, implementation mode는 `.planning/`을 건드리지 않는다는 것입니다.

## Phase gate 상세

| Phase | 허용 작업 | 종료 조건 |
| --- | --- | --- |
| `discuss` | 읽기, 탐색, 질문, risk 정리, phase-local 첫 usable slice와 추천 default 정리 | 충분히 알게 되면 `plan`으로 이동 |
| `plan` | 문서, ADR, PRD, issue plan, planning hydration, acceptance criteria, verification 계획 | 사용자 또는 승인자가 `execute` 승인 |
| `execute` | 승인된 `plan_id`와 `allowed_paths` 안의 구현 및 검증 | verification 통과 후 `done` |
| `done` | 요약, 검증 증거, follow-up 정리 | 새 작업은 새 `discuss`로 시작 |

각 phase는 자체 `discuss`를 가져야 합니다. `done` 이후 다음 phase가 필요하면 그 phase의 `discuss`로 시작합니다.

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
| `.planning/codebase/` | 현재 저장소의 architecture, stack, structure, conventions, testing, integrations, concerns |
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
3. `.planning/codebase/**` 또는 active phase docs가 stale이면 `workflow-planning-hydration`으로 되돌립니다.
4. `discuss`라면 source format, output contract, existing parser, risk를 읽기만 합니다.
5. phase-local discuss summary에 첫 usable slice, 비목표, 추천 default, verification 후보를 남깁니다.
6. `plan`이라면 `.planning/phases/.../NN-01-PLAN.md`에 stage, acceptance criteria, allowed paths, verification을 씁니다.
7. 적대적 전문가 2명과 각 3개 관점으로 plan 초안을 리뷰하고 보강합니다.
8. 승인자가 `.scratch/phase-state.json`을 `phase=execute`, `approved=true`로 맞춥니다. `--chain`이면 조건 충족 시 같은 phase 안에서 자동 진행할 수 있습니다.
9. `execute`에서 `workflow-etl-pipeline`이 red test를 먼저 만듭니다.
10. parser/normalize/state 중 어느 stage가 바뀌는지 명시합니다.
11. 최소 구현 후 focused test를 통과시킵니다.
12. DB writer까지 영향을 주면 `/db` slice로 분리합니다.
13. 운영 신호가 필요하면 `/ops` slice로 분리합니다.
14. verification 결과를 phase 문서에 기록합니다.
15. `/review`로 read-only 리뷰를 수행합니다.
16. 모든 기준을 만족하면 `done`으로 닫고 `.planning/STATE.md`의 next action을 갱신합니다.

## 검증 명령

```bash
python3 scripts/harness.py check
python3 scripts/harness.py doctor
python3 scripts/harness.py check --worktree
python3 -m unittest scripts/test_harness.py
python3 -m py_compile scripts/harness.py scripts/test_harness.py
jq . .roomodes >/dev/null
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.json
npx --yes ajv-cli validate --spec=draft2020 -s .scratch/phase-state.schema.json -d .scratch/phase-state.example.json
```

Windows PowerShell에서는 `jq`와 `/dev/null` 대신 Python JSON tooling을 사용할 수 있습니다.

```powershell
python scripts/harness.py check
python scripts/harness.py doctor
python scripts/harness.py check --worktree
python -m unittest scripts/test_harness.py
python -m py_compile scripts/harness.py scripts/test_harness.py
python -m json.tool .roomodes > $null
```

README와 실제 Roo 설정이 어긋나는지 확인하려면 command, mode, skill 이름을 함께 검색합니다.

```bash
rg -n "workflow-planning-hydration|workflow-simple-task|workflow-feature-tdd|workflow-etl-pipeline|workflow-db-change|workflow-phase-gate|db-context-snapshot|needs-db-context" README.md .roo docs
```

PR 전에는 아래 검증도 함께 실행합니다.

```bash
python3 -m unittest scripts/test_db_context_snapshot.py
tmp="$(mktemp -d)"
python3 scripts/harness.py init --target "$tmp/target"
python3 scripts/harness.py check --target "$tmp/target"
(cd "$tmp/target" && python3 scripts/harness.py check && python3 scripts/harness.py doctor)
```

PowerShell 예시:

```powershell
python -m unittest scripts/test_db_context_snapshot.py
$tmp = New-Item -ItemType Directory -Path ([System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), [System.Guid]::NewGuid().ToString()))
python scripts/harness.py init --target "$($tmp.FullName)\target"
python scripts/harness.py check --target "$($tmp.FullName)\target"
Push-Location "$($tmp.FullName)\target"
python scripts/harness.py check
python scripts/harness.py doctor
Pop-Location
```

현재 상태와 다음 작업은 항상 [.planning/STATE.md](.planning/STATE.md)에서 시작합니다.
