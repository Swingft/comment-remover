# Swift Comment Remover

Swift 소스코드에서 모든 주석을 제거하는 Python 도구입니다. Swift 문법의 복잡한 엣지 케이스를 모두 처리합니다.

## 목차

- [특징](#특징)
- [지원하는 Swift 문법](#지원하는-swift-문법)
- [설치 및 요구사항](#설치-및-요구사항)
- [사용 방법](#사용-방법)
- [작동 원리](#작동-원리)
- [테스트](#테스트)
- [주의사항](#주의사항)

---

## 특징

### 제거하는 주석
- `//` 단일 라인 주석
- `/* */` 다중 라인 블록 주석
- `/* /* */ */` 중첩된 블록 주석 (무한 깊이 지원)
- `///` 문서화 주석
- `/** */` 블록 문서화 주석
- 확장 정규식 내부의 `#` 주석

### 보존하는 내용
- 일반 문자열 내부의 `//`, `/* */` 기호
- 원시 문자열 `#"..."#` 내부의 모든 내용
- 다중 라인 문자열 `"""..."""` 내부의 주석 형태 문자
- **문자열 보간 `\(...)`**: 보간 내부의 주석은 제거하되 보간 자체는 보존
- 정규식 리터럴 `/pattern/`
- 확장 정규식 `#/.../# ` (주석만 제거, 패턴 보존)

---

## 지원하는 Swift 문법

### 1. 기본 주석
```swift
// 단일 라인 주석
let value = 42 // 코드 뒤 주석

/* 블록 주석 */
/*
  여러 줄
  블록 주석
*/

/* 중첩된 /* 주석도 */ 지원 */
```

### 2. 문자열 내 주석 형태 보존
```swift
let str = "문자열 안의 // 주석은 내용"
let raw = #"원시 문자열 /* 이것도 */ 내용"#
```

### 3. 문자열 보간 (String Interpolation) ⭐ 핵심
```swift
// 원본
let msg = "User \(user.name /* 주석 */ + suffix) end"

// 결과
let msg = "User \(user.name  + suffix) end"
```
보간 내부의 주석만 제거하고 `\(...)`는 보존합니다.

### 4. 원시 문자열 (Raw Strings)
```swift
let s1 = #"문자열 "내부" // 주석 형태"#
let s2 = ##"다중 해시 /* 주석 */ 형태"##
```
`#` 개수를 정확히 매칭하여 종료 지점을 찾습니다.

### 5. 확장 정규식 (Extended Regex)
```swift
// 원본
let regex = #/
  \d+     # 숫자 1개 이상
  \s+     # 공백 1개 이상
/#

// 결과
let regex = #/
  \d+
  \s+
/#
```
`#` 주석만 제거하고 정규식 패턴은 보존합니다.

### 6. 정규식 vs 나누기 연산자 구분
```swift
let division = 10 / 5        // 나누기 연산자
let regex = /\d+/            // 정규식 리터럴
let array = values.map { $0 / 2 }  // 나누기
```
문맥을 분석하여 정확히 구분합니다.

---

## 설치 및 요구사항

### 요구사항
- Python 3.7 이상
- 표준 라이브러리만 사용 (외부 의존성 없음)

### 파일 구조
```
project/
├── remove_swift_comments.py    # 메인 파서 코드
├── test_runner.py               # 통합 테스트
├── realistic_source.swift       # 테스트용 Swift 파일
├── expected_result.swift        # 기대 결과
└── .gitignore                   # Git 무시 파일
```

---

## 사용 방법

### 1. 기본 사용법

```python
from remove_swift_comments import SwiftCommentRemover

# 파서 인스턴스 생성
remover = SwiftCommentRemover()

# 문자열에서 주석 제거
source_code = '''
// 주석
let value = 42
'''
result = remover.remove_comments(source_code)
print(result)
```

### 2. 단일 파일 처리

```python
remover = SwiftCommentRemover()

# 파일 읽어서 주석 제거 후 저장
remover.process_and_save(
    input_path='MyFile.swift',
    output_path='MyFile_cleaned.swift'
)
```

### 3. 디렉토리 전체 처리

```python
remover = SwiftCommentRemover()

# 프로젝트 디렉토리의 모든 .swift 파일 처리 (재귀적)
remover.process_directory(
    directory='./MySwiftProject',
    output_dir='./MySwiftProject_cleaned',
    recursive=True
)
```

### 4. 실전 예제

```python
from pathlib import Path
from remove_swift_comments import SwiftCommentRemover

def clean_project(project_path: str, output_path: str = None):
    """Swift 프로젝트의 모든 주석 제거"""
    remover = SwiftCommentRemover()
    
    # 파일 개수 확인
    project = Path(project_path)
    swift_files = list(project.glob('**/*.swift'))
    print(f"처리할 파일: {len(swift_files)}개")
    
    # 처리
    if output_path:
        remover.process_directory(project_path, output_path, recursive=True)
    else:
        # 원본 디렉토리에 .cleaned.swift로 저장
        remover.process_directory(project_path, recursive=True)
    
    print("완료!")

# 사용
clean_project('./MyApp', './MyApp_NoComments')
```

---

## 작동 원리

### 상태 머신 기반 파서

이 도구는 **유한 상태 머신(Finite State Machine)** 기반으로 작동합니다.

#### 1. 상태(State) 정의

```python
class ParseState(Enum):
    NORMAL = 1                    # 일반 코드
    SINGLE_LINE_COMMENT = 2       # // 주석
    MULTI_LINE_COMMENT = 3        # /* */ 주석
    STRING = 4                    # "..." 문자열
    MULTILINE_STRING = 5          # """...""" 문자열
    STRING_ESCAPE = 6             # 문자열 이스케이프 \
    MULTILINE_STRING_ESCAPE = 7   # 다중 라인 문자열 이스케이프
    REGEX_LITERAL = 8             # /.../  정규식
    EXTENDED_REGEX = 9            # #/.../#  확장 정규식
    IN_INTERPOLATION = 10         # \(...) 문자열 보간 내부
```

#### 2. 상태 전환 예시

```
"Hello \(name /* 주석 */ + "!")"

1. " → STRING 상태
2. \( → IN_INTERPOLATION 상태 (스택에 STRING 저장)
3. /* → MULTI_LINE_COMMENT 상태
4. */ → IN_INTERPOLATION 복귀
5. ) → STRING 복귀 (스택에서 꺼냄)
6. " → NORMAL 상태
```

#### 3. 핵심 메커니즘

**스택 기반 상태 관리:**
```python
# 문자열 보간 진입 시
context = StateContext(state=STRING, hash_count=0, quote_count=1)
state_stack.append(context)
current_state = IN_INTERPOLATION

# 보간 종료 시 (괄호가 모두 닫힘)
context = state_stack.pop()
current_state = context.state  # STRING으로 복귀
```

**괄호 깊이 추적:**
```python
# 보간 내부에서
if char == '(':
    interpolation_depth += 1
elif char == ')':
    interpolation_depth -= 1
    if interpolation_depth == 0:
        # 보간 종료, 문자열로 복귀
```

**원시 문자열 해시 카운팅:**
```python
# #"..."# 또는 ##"..."## 처리
if char == '#':
    hash_count = count_consecutive_hashes()
    if next_char == '"':
        # 종료 시 동일한 개수의 #" 확인
        if closing_hash_count >= hash_count:
            # 문자열 종료
```

### 주요 알고리즘

#### 1. 확장 정규식 주석 제거
```python
def _handle_extended_regex(self):
    if char == '#':
        # 주석 앞의 공백 제거
        remove_trailing_spaces_from_result()
        
        # 줄 끝까지 스킵
        while source[i] != '\n':
            i += 1
        
        # 개행은 메인 루프가 처리하도록
        i -= 1
```

#### 2. 정규식 vs 나누기 연산자 판단
```python
def _is_regex_context(self):
    # 뒤로 거슬러 올라가며 의미있는 문자 찾기
    pos = i - 1
    skip_whitespace()
    
    # 정규식이 올 수 있는 문자
    if char in ['=', '(', ',', '[', ':', '{', ...]:
        return True
    
    # return, where 키워드 뒤
    if is_keyword_before():
        return True
    
    return False
```

---

## 테스트

### 단위 테스트 실행

```bash
python remove_swift_comments.py
```

7개의 테스트 케이스가 실행됩니다:
1. 문자열 보간
2. 원시 문자열
3. 확장 정규식
4. 복합 시나리오
5. 나누기 연산자 vs 정규식
6. 복잡한 중첩 문자열 보간
7. 문자열 보간 내 블록 주석

### 통합 테스트 실행

```bash
python test_file.py
```

실제 Swift 소스 파일(`realistic_source.swift`)을 처리하여 결과를 검증합니다.

### 테스트 케이스 예시

```python
# 1. 문자열 보간
입력: let msg = "Hello, \(world.uppercased())" // 주석
출력: let msg = "Hello, \(world.uppercased())" 

# 2. 원시 문자열
입력: let raw = #"문자열 "내부" // 이것도 내용"#
출력: let raw = #"문자열 "내부" // 이것도 내용"#

# 3. 확장 정규식
입력:
let regex = #/
  \d+     # 숫자
  \s+     # 공백
/#
출력:
let regex = #/
  \d+
  \s+
/#

# 4. 중첩 주석
입력: /* 외부 /* 내부 */ 주석 */
출력: (모두 제거)
```

---

## 주의사항

### 1. 처음엔 테스트 출력
원본을 수정하지 말고 별도 디렉토리로 출력하여 결과를 확인하세요.

```python
remover.process_directory(
    './MyProject',
    './MyProject_test',  # 테스트 출력
    recursive=True
)
```

### 2. 알려진 제한사항

#### 2.1 복잡한 매크로
Swift 매크로나 컴파일러 지시문은 테스트되지 않았습니다.

```swift
#if DEBUG
// 이런 조건부 컴파일은 신중하게 사용
#endif
```

#### 2.2 인코딩 문제
UTF-8이 아닌 인코딩은 지원하지 않습니다. 파일을 UTF-8로 변환하세요.

#### 2.3 손상된 구문
구문이 잘못된 Swift 파일은 예상치 못한 결과를 낼 수 있습니다. 먼저 컴파일이 되는 파일인지 확인하세요.

### 3. 성능 고려사항
대규모 프로젝트(1000+ 파일)는 처리에 시간이 걸릴 수 있습니다. 진행 상황을 확인하려면:

```python
from pathlib import Path

project = Path('./LargeProject')
files = list(project.glob('**/*.swift'))
total = len(files)

for i, file in enumerate(files, 1):
    print(f"처리 중: {i}/{total} - {file.name}")
    remover.process_and_save(str(file), str(file.with_suffix('.cleaned.swift')))
```

---

## 문제 해결

### Q: 주석이 제거되지 않습니다
**A:** 문자열이나 원시 문자열 내부에 있는지 확인하세요. 이들은 의도적으로 보존됩니다.

### Q: 코드가 깨집니다
**A:** 다음을 확인하세요:
1. 원본 파일이 컴파일 가능한가?
2. UTF-8 인코딩인가?
3. 백슬래시 `\`가 올바르게 사용되었는가?

### Q: 문자열 보간이 작동하지 않습니다
**A:** 파일에 `\\(`가 아닌 `\(`로 저장되어 있는지 확인하세요.

```swift
// 올바름
let msg = "Hello \(name)"

// 잘못됨 (리터럴 백슬래시)
let msg = "Hello \\(name)"
```

### Q: 특정 파일만 처리하고 싶습니다
**A:**
```python
from pathlib import Path

files_to_process = [
    'Models/User.swift',
    'ViewModels/MainViewModel.swift'
]

for file in files_to_process:
    remover.process_and_save(file, f"{file}.cleaned")
```

---

## 라이선스

MIT License - 자유롭게 사용, 수정, 배포할 수 있습니다.

---

## 요약

Swift Comment Remover는 Swift 문법의 복잡한 엣지 케이스를 모두 고려한 견고한 주석 제거 도구입니다. 문자열 보간, 원시 문자열, 확장 정규식 등 Swift의 고급 기능을 완벽히 지원하며, 상태 머신 기반의 정확한 파싱으로 코드를 손상시키지 않습니다.

**핵심 강점:**
- 문자열 보간 내 주석 정확히 제거
- 원시 문자열 완벽 지원
- 중첩 주석 무한 깊이 지원
- 정규식 vs 나누기 연산자 정확한 구분
- 외부 의존성 없음

**사용 권장:**
- 코드 난독화
- 배포용 코드 정리
- 코드 크기 최적화
- 주석 제거 후 재분석

실제 프로덕션 코드에 사용하기 전 반드시 백업하고 테스트하세요!