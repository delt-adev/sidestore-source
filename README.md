# SideStore 자동 Source (GitHub Pages)

GitHub Releases에 IPA를 올리면 GitHub Actions가 IPA 내부 정보를 읽어 SideStore 호환 `apps.json`을 자동 생성하고 GitHub Pages에 배포합니다.

## 최초 설정

1. GitHub에서 **Public** 저장소를 만듭니다.
2. 이 ZIP의 파일과 폴더를 저장소 루트에 업로드합니다.
3. `metadata/apps.json`에서 Source 이름과 고유 identifier, 기본 개발자 이름/설명을 수정합니다.
4. `source.identifier`는 배포 후 바꾸지 않는 것을 권장합니다.
5. GitHub 저장소의 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 선택합니다.
6. 앱을 배포할 때 **Releases → Draft a new release**에서 태그를 만들고 `.ipa` 파일을 Release asset으로 올린 뒤 Publish release를 누릅니다.
7. 자동 실행된 **Actions → Build and publish SideStore source**가 성공했는지 확인합니다.

## 앱 등록 및 업데이트 방식

- IPA를 Release asset으로 업로드하면 새 앱도 자동으로 목록에 추가됩니다.
- 스크립트가 IPA 내부 `Payload/*.app/Info.plist`에서 `CFBundleIdentifier`, `CFBundleShortVersionString`, `CFBundleDisplayName` 등을 읽습니다.
- 앱 이름은 `CFBundleDisplayName` → `CFBundleName` → Bundle ID 순서로 가져옵니다.
- 앱별 이름/개발자/설명/아이콘 등을 직접 지정하고 싶으면 `metadata/apps.json`의 `apps` 배열에 Bundle ID별 override 항목을 추가하면 됩니다. 필수 절차는 아닙니다.
- 앱별 override가 없으면 기본 개발자 이름/설명과 `assets/default-icon.png`를 사용합니다.
- 새 버전은 `versions` 배열에 자동 추가되며 기존 공개 Release 버전도 유지됩니다.
- 한 Release에 여러 IPA를 올릴 수 있고, 여러 앱을 같은 Source에서 관리할 수 있습니다.
- Release에 `.ipa` 파일을 올려야 하며, 일반 저장소 파일 업로드만으로는 트리거되지 않습니다.

## SideStore에 추가할 주소

`https://USERNAME.github.io/REPOSITORY/apps.json`

추가 링크:

`sidestore://source?url=https://USERNAME.github.io/REPOSITORY/apps.json`

## 참고

- GitHub Pages 주소는 저장소의 소유자/이름에 따라 달라집니다.
- Public 저장소에서는 Source JSON과 Release IPA가 공개됩니다.
- IPA의 버전은 `CFBundleShortVersionString`에서 가져옵니다.
- 워크플로는 공개 GitHub Release의 IPA를 대상으로 합니다.
- GitHub Actions의 `GITHUB_TOKEN`은 자동 제공되므로 별도 Personal Access Token은 필요하지 않습니다.
- SideStore source는 AltStore Source 호환 형식입니다.
