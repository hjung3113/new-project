# Upcoming Issues Brainstorm

요청하신 "앞으로 올라올 이슈" 관점에서, 현재 프로젝트 상태 문서를 기준으로 우선 검토가 필요한 이슈 후보를 정리했습니다.

## 기준으로 확인한 문서

- `.planning/STATE.md`
- `.planning/ROADMAP.md`
- `.scratch/phase-state.json`

## 이슈 후보 (우선순위 순)

### 1) Phase 2 강제 범위 확정 (pre-commit / CI / 둘 다)
- **배경**: STATE의 open question에 강제 방식 선택이 미결로 남아 있음.
- **왜 지금 필요한가**: 선택이 없으면 Phase 2 문서 작성과 구현 범위를 고정할 수 없음.
- **이슈 초안**:
  - 제목: `Decide enforcement channel for phase gate (pre-commit, CI, or both)`
  - 완료조건: 선택 근거 + 운영 정책(우회 허용 여부) + 검증 커맨드 확정

### 2) allowed_paths 매칭 규칙 확정 (exact / prefix / glob)
- **배경**: 경로 허용 규칙은 체크 정확도와 운영 난이도를 직접 좌우함.
- **왜 지금 필요한가**: 구현 전에 규칙이 모호하면 false positive/negative가 크게 발생할 수 있음.
- **이슈 초안**:
  - 제목: `Define allowed_paths matching semantics`
  - 완료조건: 규칙 1안 확정 + 예시 케이스(허용/차단) 문서화

### 3) README vs 전용 문서 분리 정책
- **배경**: 템플릿 소비자 온보딩 문서 위치가 미정.
- **왜 지금 필요한가**: Phase 3 산출물의 구조가 달라질 수 있음.
- **이슈 초안**:
  - 제목: `Choose onboarding doc location (README or dedicated docs file)`
  - 완료조건: 위치 선택 + 유지보수 책임/업데이트 규칙 정의

### 4) phase-state 검증 자동화 최소 스택 확정
- **배경**: ROADMAP의 Phase 2 성공 조건에 schema 검증 자동화가 포함됨.
- **왜 지금 필요한가**: 로컬/CI에서 동일하게 재현 가능한 커맨드가 필요함.
- **이슈 초안**:
  - 제목: `Standardize phase-state schema validation command`
  - 완료조건: 단일 표준 커맨드 + 실패 예시 + 문서 반영

## 제안하는 처리 순서

1. 이슈 1(강제 채널) 결정
2. 이슈 2(경로 규칙) 결정
3. 이슈 4(검증 커맨드) 확정
4. 이슈 3(온보딩 문서 위치) 결정

## 메모

- 현재 `.scratch/phase-state.json`의 `phase` 값은 `done`이며, 다음 액션은 Phase 2 시작 준비로 명시되어 있습니다.
- 따라서 위 이슈들은 "새 기능 구현"보다 "Phase 2 설계 고정"을 위한 선행 의사결정 성격이 강합니다.

---

## PR 확인 메모

- 이 저장소의 Codex 에이전트 작업은 **로컬 커밋과 PR 메시지 초안 생성**까지는 수행할 수 있으나,
  GitHub 원격으로의 실제 PR 생성 여부는 브랜치 푸시 상태에 따라 달라질 수 있습니다.
- 확인 순서: `git status` -> `git log --oneline -n 3` -> `git remote -v` -> GitHub PR 페이지.
