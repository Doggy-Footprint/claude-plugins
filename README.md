# claude-plugins

## Claude Code

```bash
claude plugin marketplace add Doggy-Footprint/claude-plugins
claude plugin install scored-web-search@doggy-footprint
claude plugin install learn-to-tell@doggy-footprint
claude plugin install llm-wiki@doggy-footprint
```

자동 업데이트: `/plugin` → Marketplaces → `doggy-footprint` → Enable auto-update. Claude Code는 각 플러그인 `plugin.json`의 `version`이 바뀌어야 새 버전으로 인식한다.

## claude.ai (웹·데스크톱·모바일)

1. PC 웹 claude.ai의 Customize → Plugins → Add → Add marketplace에 `Doggy-Footprint/claude-plugins`를 넣는다.
2. 마켓플레이스 화면에서 **Sync automatically**를 켠다. 이 저장소의 `main`에 push가 있을 때마다 claude.ai가 다시 동기화한다.
3. 쓰려는 플러그인을 설치한다. 예전에 Customize → Skills에 zip으로 올린 같은 skill은 지운다 (같은 요청에 둘 다 반응한다).
4. 코드 실행을 켠다. 플러그인 skill의 스크립트는 코드 실행 환경에서 돈다.

claude.ai에 설치한 플러그인은 모바일 앱에도 보이고, 같은 계정으로 로그인한 Claude Code에도 `<이름>@synced`로 들어온다.

## 플러그인 갱신이 claude.ai까지 가는 길

`marketplace.json`은 플러그인마다 `ref`(브랜치)와 그 브랜치의 커밋 `sha`를 함께 적는다. claude.ai는 이 저장소에 push가 있어야 동기화하므로, 플러그인 저장소만 바뀌면 claude.ai는 모른다. 그래서 `pin-sources` workflow가 매시 17분에 각 `ref`의 최신 커밋을 `git ls-remote`로 확인하고, 바뀐 `sha`를 커밋해 push한다. 그 push가 claude.ai 동기화를 부른다.

- 바로 반영하려면 Actions → pin-sources → Run workflow.
- 로컬에서: `python3 scripts/pin_sources.py` (바뀐 플러그인을 출력하고 `marketplace.json`을 고친다), 테스트는 `python3 -m unittest discover tests`.
- GitHub은 60일 동안 저장소 활동이 없으면 공개 저장소의 schedule workflow를 끈다. 꺼지면 Actions에서 다시 켠다.
- learn-to-tell은 claude.ai에 zip으로 올린 경우를 위해 새 릴리스가 있으면 zip을 다시 올리라고 알린다. 플러그인으로 설치했다면 그 알림은 무시해도 된다 (다음 동기화 때 받는다).

각 플러그인의 claude.ai 사용법: [llm-wiki](https://github.com/Doggy-Footprint/llm-wiki-plugin#claudeai-채팅-웹모바일), [learn-to-tell](https://github.com/Doggy-Footprint/learn-to-tell#claudeai-웹모바일-앱).
