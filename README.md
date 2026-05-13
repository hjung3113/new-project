# Roo 프로젝트 하네스 템플릿

이 저장소는 **특정 기술 스택에 묶이지 않은** Roo/Codex 에이전트 하네스 템플릿입니다.  
목표는 어떤 새 프로젝트에서도 바로 재사용할 수 있도록, 계획 문서/phase gate/에이전트 규칙을 일관되게 제공하는 것입니다.

## 이 템플릿이 제공하는 것

- `.planning/` 기반의 영속적인 프로젝트 상태 문서
- `.scratch/phase-state.json` 기반의 live phase gate
- `.roo/` 모드/룰/커맨드 스캐폴딩
- `AGENTS.md` 중심의 세션 재시작 절차

## 새 프로젝트에 적용하는 최소 절차

1. `AGENTS.md`를 프로젝트 컨텍스트에 맞게 업데이트합니다.
2. `.planning/PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`를 새 프로젝트 기준으로 교체/작성합니다.
3. 첫 active phase 폴더를 `.planning/phases/` 아래 생성합니다.
4. `.scratch/phase-state.json`의 `plan_id`, `allowed_paths`, `verification`을 현재 작업 기준으로 갱신합니다.
5. 구현 전에는 `phase=discuss|plan`, 구현 승인 후에만 `phase=execute`를 사용합니다.

## 세션 시작 순서

새 세션에서는 아래 순서를 고정합니다.

1. `AGENTS.md`
2. `.planning/STATE.md`
3. `.planning/ROADMAP.md`
4. active phase의 `*-CHECKPOINTS.md`
5. `.scratch/phase-state.json`

## 참고 문서

- `docs/phase-gate-harness.md`: phase gate 규칙
- `docs/agents/issue-tracker.md`: 이슈/PRD 파일 운영
- `docs/agents/domain.md`: 도메인 문서 구조
- `docs/agents/triage-labels.md`: triage 라벨
- `docs/codex-cloud-setup.md`: Codex Cloud 환경 연결
