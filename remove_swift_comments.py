import re
from enum import Enum
from pathlib import Path
from typing import Optional, List, Tuple


class ParseState(Enum):
    NORMAL = 1
    SINGLE_LINE_COMMENT = 2
    MULTI_LINE_COMMENT = 3
    STRING = 4
    MULTILINE_STRING = 5
    STRING_ESCAPE = 6
    MULTILINE_STRING_ESCAPE = 7
    REGEX_LITERAL = 8
    EXTENDED_REGEX = 9
    IN_INTERPOLATION = 10


class StateContext:
    """A class to store the context of a state, used for the state stack."""

    def __init__(self, state: ParseState, hash_count: int = 0, quote_count: int = 0):
        self.state = state
        self.hash_count = hash_count
        self.quote_count = quote_count


class SwiftCommentRemover:
    def __init__(self):
        self.source = ""
        self.result: List[str] = []
        self.i = 0
        self.length = 0

        self.current_state = ParseState.NORMAL
        self.state_stack: List[StateContext] = []

        self.nesting_level = 0
        self.current_hash_count = 0
        self.current_quote_count = 0

        # Depths for balanced pairs inside interpolation
        self.interpolation_depth = 0
        self.brace_depth = 0
        self.bracket_depth = 0

    def remove_comments(self, source: str) -> str:
        """Removes all comments from a Swift source code string."""
        self.source = source
        self.result = []
        self.i = 0
        self.length = len(source)
        self.state_stack = []
        self.current_state = ParseState.NORMAL
        self.nesting_level = 0
        self.current_hash_count = 0
        self.current_quote_count = 0
        self.interpolation_depth = 0
        self.brace_depth = 0
        self.bracket_depth = 0

        while self.i < self.length:
            self._process_current_char()
            self.i += 1

        return ''.join(self.result)

    def _process_current_char(self):
        """Dispatches the current character to the appropriate handler based on the current state."""
        handlers = {
            ParseState.NORMAL: self._handle_normal,
            ParseState.SINGLE_LINE_COMMENT: self._handle_single_comment,
            ParseState.MULTI_LINE_COMMENT: self._handle_multi_comment,
            ParseState.STRING: self._handle_string,
            ParseState.STRING_ESCAPE: self._handle_string_escape,
            ParseState.MULTILINE_STRING: self._handle_multiline_string,
            ParseState.MULTILINE_STRING_ESCAPE: self._handle_multiline_string_escape,
            ParseState.REGEX_LITERAL: self._handle_regex,
            ParseState.EXTENDED_REGEX: self._handle_extended_regex,
            ParseState.IN_INTERPOLATION: self._handle_in_interpolation,
        }
        handler = handlers.get(self.current_state)
        if handler:
            handler()

    def _peek(self, offset: int = 1) -> Optional[str]:
        """Looks at the character at the given offset from the current position."""
        pos = self.i + offset
        return self.source[pos] if pos < self.length else None

    def _count_char(self, char: str, start_offset: int = 0) -> int:
        """Counts consecutive occurrences of a character from a starting offset."""
        count = 0
        pos = self.i + start_offset
        while pos < self.length and self.source[pos] == char:
            count += 1
            pos += 1
        return count

    def _is_regex_context(self) -> bool:
        """Heuristically determines if a '/' character is likely the start of a regex literal."""
        pos = self.i - 1
        while pos >= 0 and self.source[pos].isspace():
            pos -= 1
        if pos < 0: return True

        char = self.source[pos]
        # Common characters that can precede a regex literal.
        regex_preceding = {'=', '(', ',', '[', ':', '{', '!', '&', '|', '^', '+', '-', '*', '%', '<', '>', '~', ';'}
        if char in regex_preceding: return True

        # Check for keywords like 'return' or 'where'
        for keyword in ['return', 'where']:
            keyword_len = len(keyword)
            if pos >= keyword_len - 1:
                start = pos - keyword_len + 1
                if self.source[start:pos + 1] == keyword:
                    # Ensure it's not part of a larger word
                    if start == 0 or not self.source[start - 1].isalnum():
                        return True
        return False

    def _append(self, text: str):
        self.result.append(text)

    def _current_char(self) -> str:
        return self.source[self.i]

    def _revert_to_previous_state(self):
        """Reverts to the correct previous state (NORMAL or IN_INTERPOLATION) after a temporary state ends."""
        self.current_hash_count = 0
        self.current_quote_count = 0
        if self.interpolation_depth > 0:
            self.current_state = ParseState.IN_INTERPOLATION
        else:
            self.current_state = ParseState.NORMAL

    def _handle_normal_or_interpolation(self):
        """Handles characters in NORMAL or IN_INTERPOLATION states by first checking for state transitions."""
        char = self._current_char()
        next_char = self._peek()

        # --- Part 1: Check for transitions to other states (comments, strings, etc.) ---
        if char == '/' and next_char == '/':
            self.current_state = ParseState.SINGLE_LINE_COMMENT
            self.i += 1
            return
        if char == '/' and next_char == '*':
            self.current_state = ParseState.MULTI_LINE_COMMENT
            self.nesting_level = 1
            self.i += 1
            return

        if char == '#':
            hash_count = self._count_char('#')
            next_after_hash = self._peek(hash_count)
            if next_after_hash == '"':
                quote_count = self._count_char('"', hash_count)
                state = ParseState.MULTILINE_STRING if quote_count >= 3 else ParseState.STRING
                self._enter_string_state(state, hash_count, quote_count)
                return
            if next_after_hash == '/' and self._is_regex_context():
                self.current_state = ParseState.EXTENDED_REGEX
                self.current_hash_count = hash_count
                self._append('#' * hash_count + '/')
                self.i += hash_count
                return

        if char == '"':
            quote_count = self._count_char('"')
            state = ParseState.MULTILINE_STRING if quote_count >= 3 else ParseState.STRING
            self._enter_string_state(state, 0, quote_count)
            return

        if char == '/' and self._is_regex_context():
            self.current_state = ParseState.REGEX_LITERAL
            self._append(char)
            return

        # --- Part 2: If no state change, append character and handle interpolation logic ---
        self._append(char)

        if self.current_state == ParseState.IN_INTERPOLATION:
            if char == '(':
                self.interpolation_depth += 1
            elif char == '{':
                self.brace_depth += 1
            elif char == '[':
                self.bracket_depth += 1
            elif char == ')':
                self.interpolation_depth -= 1
            elif char == '}':
                self.brace_depth -= 1
            elif char == ']':
                self.bracket_depth -= 1

            # Check if the interpolation has ended
            if self.interpolation_depth == 0 and self.brace_depth == 0 and self.bracket_depth == 0:
                context = self.state_stack.pop()
                self.current_state = context.state
                self.current_hash_count = context.hash_count
                self.current_quote_count = context.quote_count

    def _handle_normal(self):
        self._handle_normal_or_interpolation()

    def _handle_in_interpolation(self):
        self._handle_normal_or_interpolation()

    def _enter_string_state(self, state: ParseState, hash_count: int, quote_count: int):
        """Helper to enter a string state."""
        self.current_state = state
        self.current_hash_count = hash_count
        self.current_quote_count = quote_count if state == ParseState.MULTILINE_STRING else 1

        delimiters = '#' * hash_count + '"' * self.current_quote_count
        self._append(delimiters)
        self.i += len(delimiters) - 1

    def _handle_comment_end(self):
        """Handles the end of a comment, reverting to the correct state."""
        if self.interpolation_depth > 0:
            self.current_state = ParseState.IN_INTERPOLATION
        else:
            self.current_state = ParseState.NORMAL

    def _handle_single_comment(self):
        if self._current_char() == '\n':
            self._handle_comment_end()
            self._append('\n')

    def _handle_multi_comment(self):
        char, next_char = self._current_char(), self._peek()
        if char == '/' and next_char == '*':
            self.nesting_level += 1
            self.i += 1
        elif char == '*' and next_char == '/':
            self.nesting_level -= 1
            self.i += 1
            if self.nesting_level == 0:
                self._handle_comment_end()

    def _handle_any_string(self, escape_state: ParseState):
        """Handles logic common to both single and multi-line strings."""
        char, next_char = self._current_char(), self._peek()
        if char == '\\':
            if next_char == '(':
                self._append('\\(')
                self.i += 1
                context = StateContext(self.current_state, self.current_hash_count, self.current_quote_count)
                self.state_stack.append(context)
                self.current_state = ParseState.IN_INTERPOLATION
                self.interpolation_depth = 1
                self.brace_depth = 0
                self.bracket_depth = 0
            else:
                self.current_state = escape_state
                self._append(char)
            return

        is_closing_quote = False
        if char == '"':
            end_quote_count = self._count_char('"')
            if end_quote_count >= self.current_quote_count:
                if self.current_hash_count > 0:
                    if self._count_char('#', end_quote_count) >= self.current_hash_count:
                        is_closing_quote = True
                else:
                    is_closing_quote = True

        if is_closing_quote:
            delimiters = '"' * self.current_quote_count + '#' * self.current_hash_count
            self._append(delimiters)
            self.i += len(delimiters) - 1
            self._revert_to_previous_state()
        else:
            self._append(char)

    def _handle_string(self):
        self._handle_any_string(ParseState.STRING_ESCAPE)

    def _handle_multiline_string(self):
        self._handle_any_string(ParseState.MULTILINE_STRING_ESCAPE)

    def _handle_string_escape(self):
        self._append(self._current_char())
        self.current_state = ParseState.STRING

    def _handle_multiline_string_escape(self):
        self._append(self._current_char())
        self.current_state = ParseState.MULTILINE_STRING

    def _handle_regex(self):
        char, next_char = self._current_char(), self._peek()
        if char == '\\' and next_char:
            self._append(char + next_char)
            self.i += 1
        elif char == '/':
            self._append(char)
            self._revert_to_previous_state()
        else:
            self._append(char)

    def _handle_extended_regex(self):
        char = self._current_char()
        if char == '/':
            if self._count_char('#', 1) >= self.current_hash_count:
                delimiters = '/' + '#' * self.current_hash_count
                self._append(delimiters)
                self.i += self.current_hash_count
                self._revert_to_previous_state()
                return

        if char == '#':
            # This is a comment. Skip until the newline, but don't consume the newline.
            # The main loop will process the newline in the next iteration.
            while self.i < self.length and self.source[self.i] != '\n':
                self.i += 1
            if self.i < self.length:  # To handle file ending without newline
                self.i -= 1  # Rewind so the main loop can process the \n
            return

        if char == '\\' and self._peek():
            self._append(char + self._peek())
            self.i += 1
            return

        self._append(char)

    def process_file(self, input_path: str) -> str:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.remove_comments(content)

    def process_and_save(self, input_path: str, output_path: str):
        result = self.process_file(input_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"✓ 주석 제거 완료: {output_path}")


# --- Test Suite ---
def run_tests():
    test_cases: List[Tuple[str, str, str]] = [
        (
            '문자열 보간',
            '''let world = "World"
let message = "Hello, \\(world.uppercased())" // 이 주석은 제거되어야 합니다.
print(message) /* 이 주석도 제거되어야 합니다. */''',
            '''let world = "World"
let message = "Hello, \\(world.uppercased())" 
print(message) '''
        ),
        (
            '원시 문자열',
            '''let rawString = #"이것은 "원시 문자열"입니다. // 이 부분은 문자열입니다."#
let anotherRaw = ##"이 안에서는 /* 이것도 */ 주석이 아닙니다."##''',
            '''let rawString = #"이것은 "원시 문자열"입니다. // 이 부분은 문자열입니다."#
let anotherRaw = ##"이 안에서는 /* 이것도 */ 주석이 아닙니다."##'''
        ),
        (
            '확장 정규식',
            '''let regex = #/
  \\d+     # 숫자 1개 이상
  \\s+     # 공백 1개 이상
  [a-z]+  # 소문자 1개 이상
/#''',
            '''let regex = #/
  \\d+     
  \\s+     
  [a-z]+  
/#'''
        ),
        (
            '복합 시나리오',
            '''// 단일 주석
let value = 42 // 뒤 주석
/* 블록 주석 */
let str = "문자열 // 안의 주석"
let interp = "값: \\(value /* 보간 내 주석 */ + 1)"
let raw = #"원시: "test" // 주석 아님"#
let multiRaw = ##"다중 원시 /* 주석 아님 */ "##
let regex = /\\d+/ // 정규식 뒤 주석
/* /* 중첩 */ 주석 */
let result = value''',
            '''
let value = 42 

let str = "문자열 // 안의 주석"
let interp = "값: \\(value  + 1)"
let raw = #"원시: "test" // 주석 아님"#
let multiRaw = ##"다중 원시 /* 주석 아님 */ "##
let regex = /\\d+/ 

let result = value'''
        ),
        (
            '나누기 연산자',
            '''let value = dictionary["key"] / 2 // 나누기 연산자입니다.
let division = 10 / 5
let regexVar = /\\d+/''',
            '''let value = dictionary["key"] / 2 
let division = 10 / 5
let regexVar = /\\d+/'''
        ),
        (
            '복잡한 문자열 보간',
            '''let nested = "outer \\(a + b /* 주석1 */ + c) middle \\("inner \\(x /* 주석2 */ + y)") end"
let arr = "values: \\(array.map { "item: \\($0)" /* 주석3 */ }.joined())"''',
            '''let nested = "outer \\(a + b  + c) middle \\("inner \\(x  + y)") end"
let arr = "values: \\(array.map { "item: \\($0)"  }.joined())"'''
        ),
    ]

    remover = SwiftCommentRemover()
    all_passed = True

    print("Swift 주석 제거 도구 - 전체 테스트")
    print("=" * 70)

    for name, code, expected in test_cases:
        result = remover.remove_comments(code).strip()
        expected = expected.strip()

        print(f"\n테스트: {name}")
        print("-" * 70)

        if result == expected:
            print("✅ 통과")
        else:
            all_passed = False
            print("❌ 실패")
            print("\n[입력 코드]")
            print(code)
            print("\n[기대 결과]")
            print(expected)
            print("\n[실제 결과]")
            print(result)
            print("-" * 20)

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 모든 테스트를 통과했습니다!")
    else:
        print("🔥 일부 테스트에 실패했습니다.")


if __name__ == '__main__':
    run_tests()

