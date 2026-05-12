---
name: gated-team-dev
description: Use when starting any feature implementation — routes work through Architect → Implementers → DB Reviewer → Code Reviewer → Test Writer with mandatory gate checks before proceeding
---

# Gated Team Development (5-Agent Workflow)

## Overview

5개 전문 에이전트가 게이트 3개를 통과하며 순차+병렬로 작업한다. 아무도 자기 코드를 자기가 리뷰하지 않는다.

```
Gate 1 (설계 완료)          Gate 2 (구현 완료)           Gate 3 (커밋 전)
      │                           │                            │
Architect ──────────────► BE Impl ──► DB Reviewer ─────────► Code Reviewer
                     └──► FE Impl ──► Test Writer ──────────►(all 4 sign off)
```

## Agent Roles

| # | 에이전트 | 모델 | 책임 | 금지사항 |
|---|----------|------|------|----------|
| **1. Architect** | `oh-my-Codex:architect` | opus | API 계약, 파일 구조, DB 스키마+인덱스, 응답 형식 단일화 | 코드 작성 금지 |
| **2. BE Implementer** | `oh-my-Codex:executor` | sonnet | 라우트(얇게) + service 계층 + SQL | 라우트에 SQL 직접 금지, 300줄 초과 금지 |
| **3. FE Implementer** | `oh-my-Codex:executor` | sonnet | 컴포넌트 + hooks + API 모듈 | API 레이어 우회 금지, 파일 300줄 초과 금지 |
| **4. DB Reviewer** | `oh-my-Codex:code-reviewer` | opus | SQL 전담 검토 | 코드 수정 금지 — 리포트만 |
| **5. Test Writer** | `oh-my-Codex:test-engineer` | sonnet | 구현과 동시에 테스트 작성 | Happy path만 금지 |

## Gate 1 — Architect 서명 (구현 시작 전 필수)

Architect가 다음을 모두 정의해야 Gate 1 통과:

- [ ] **파일 목록**: 생성할 파일 경로 전체 + 각 파일 역할 한 줄
- [ ] **API 계약**: 엔드포인트별 request/response shape (TypeScript interface)
- [ ] **응답 형식**: `{ data, total, page }` 또는 `{ data }` — 프로젝트 내 단일 형식
- [ ] **DB 스키마**: 새 컬럼/테이블 + **인덱스 계획** (어떤 컬럼에 왜 인덱스)
- [ ] **Service 계층**: 라우트 → service 분리 경계 명시
- [ ] **파일 크기 한도**: 컴포넌트 300줄, 라우트 200줄, service 400줄

Gate 1 없이 구현 시작 → 해당 구현 전체 폐기 후 재시작.

## Gate 2 — DB Reviewer 서명 (BE 구현 완료 후)

DB Reviewer가 다음을 검토하고 PASS/FAIL 리포트 제출:

- [ ] **N+1 쿼리**: 루프 안 DB 호출 → 단일 GROUP BY로 교체
- [ ] **트랜잭션**: 다중 테이블 수정 → BEGIN/COMMIT 확인
- [ ] **UUID 타입 캐스트**: `$N::uuid`, `$N::date` 일관성
- [ ] **인덱스**: Architect 계획 대비 실제 인덱스 누락 여부
- [ ] **LIMIT**: 무제한 SELECT 없는지 (list API 전체)
- [ ] **WHERE 절 중복**: 동일 필터 SQL이 3회 이상 복붙 → `buildFilterClause()` 헬퍼 요구
- [ ] **타임존**: 날짜 계산이 서버 TZ에 의존하지 않는지

FAIL 항목 있으면 BE Implementer 수정 후 재검토. Gate 2 없이 Gate 3 진입 불가.

## Gate 3 — Code Reviewer + Test Writer (커밋 전)

**Code Reviewer** 체크:
- [ ] 파일 크기 한도 준수 (300/200/400줄)
- [ ] `any` 타입 / 이중 단언 (`as X as Y`) 없음
- [ ] API 레이어 우회 없음 (FE에서 raw `fetch` 직접 호출)
- [ ] Silent catch 없음 (`.catch(() => {})` → 최소 `toast.error`)
- [ ] 하드코딩 도메인 값 없음 (상태/우선순위 문자열 → constants 파일)
- [ ] 응답 형식이 Architect 계약과 일치

**Test Writer** 체크:
- [ ] 권한 매트릭스: user/manager/admin 3가지 역할 모두 테스트
- [ ] Error path: 400/403/404/500 각각 테스트
- [ ] Happy path 외 edge case 1개 이상
- [ ] `it.todo()` 0개

둘 다 PASS해야 커밋 가능.

## Invocation

```bash
# Gate 1: Architect 설계
Agent(subagent_type="oh-my-Codex:architect", model="opus",
  prompt="[기능명] 구현을 위한 Gate 1 설계를 완료하라.
  산출물: 파일 목록, API 계약 TypeScript interface, DB 인덱스 계획, Service 경계.
  작업 디렉토리: /path/to/project")

# Gate 2 병렬 구현
Agent(subagent_type="oh-my-Codex:executor", model="sonnet",
  prompt="BE 구현. Architect 계약: [계약 내용]. 라우트는 얇게, 로직은 service로.")

Agent(subagent_type="oh-my-Codex:executor", model="sonnet",
  prompt="FE 구현. Architect 계약: [계약 내용]. 파일 300줄 초과 금지.")

Agent(subagent_type="oh-my-Codex:test-engineer", model="sonnet",
  prompt="BE 구현과 병렬로 테스트 작성. 권한 매트릭스 + error path 필수.")

# Gate 2: DB 리뷰
Agent(subagent_type="oh-my-Codex:code-reviewer", model="opus",
  prompt="DB Reviewer로서 Gate 2 체크리스트 전체를 검토하고 PASS/FAIL 리포트 작성.")

# Gate 3: 최종 리뷰
Agent(subagent_type="oh-my-Codex:code-reviewer", model="sonnet",
  prompt="Code Reviewer로서 Gate 3 체크리스트 검토. 파일 크기, 타입 안전성, silent catch.")
```

## 절대 규칙

1. **게이트 순서 스킵 불가** — Gate 1 없이 구현, Gate 2 없이 Gate 3 진입 → 해당 작업 전체 폐기
2. **자기 코드 자기 리뷰 불가** — Implementer는 Reviewer 역할 겸직 불가
3. **FAIL 항목 무시 불가** — Reviewer FAIL → 수정 후 재검토, 우회 없음
4. **`it.todo()` 0개로 커밋** — 테스트 나중에 쓰는 것은 테스트 없는 것과 같음

## 이 워크플로우가 막는 문제

| 발견된 문제 | 막는 게이트 |
|-------------|------------|
| AdminPage 1,870줄 | Gate 1 (파일 크기 한도 사전 정의) |
| N+1 쿼리 156회 | Gate 2 (DB Reviewer) |
| 트랜잭션 없는 다중 INSERT | Gate 2 (DB Reviewer) |
| 인덱스 전무 | Gate 1 + Gate 2 |
| API 레이어 우회 raw fetch | Gate 3 (Code Reviewer) |
| 응답 형식 불일치 | Gate 1 (Architect 계약) |
| 테스트 7% 커버리지 | Gate 3 (Test Writer PASS 필수) |
| 권한 매트릭스 `it.todo()` | Gate 3 (0개 조건) |
| VOC 유형 하드코딩 | Gate 3 (Code Reviewer) |
| Silent catch 21건 | Gate 3 (Code Reviewer) |
