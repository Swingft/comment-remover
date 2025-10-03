import os
import difflib
from remove_swift_comments import SwiftCommentRemover


def run_realistic_test():
    """
    Runs a test on a realistic Swift source file and compares it to an expected result.
    """
    SOURCE_FILE = 'realistic_source.swift'
    EXPECTED_FILE = 'expected_result.swift'

    print("현실적인 Swift 코드에 대한 최종 검증을 실행합니다...")
    print("=" * 60)
    print(f"입력 파일: '{SOURCE_FILE}'")
    print(f"기대 결과 파일: '{EXPECTED_FILE}'")
    print("-" * 60)

    try:
        # 1. Read source and expected files
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            source_code = f.read()

        with open(EXPECTED_FILE, 'r', encoding='utf-8') as f:
            expected_cleaned_code = f.read()

        # 2. Run the comment remover
        remover = SwiftCommentRemover()
        actual_cleaned_code = remover.remove_comments(source_code)

        # 디버깅: 문제가 되는 라인만 출력
        print("\n=== 디버깅: 문제 라인 확인 ===")
        for i, line in enumerate(source_code.split('\n'), 1):
            if 'New score calculation' in line:
                print(f"원본 라인 {i}: {repr(line)}")

        for i, line in enumerate(actual_cleaned_code.split('\n'), 1):
            if 'New score' in line:
                print(f"결과 라인 {i}: {repr(line)}")

        # 3. Compare and report
        if actual_cleaned_code.strip() == expected_cleaned_code.strip():
            print("✅ 성공: 주석이 제거된 코드가 기대 결과와 정확히 일치합니다.")
        else:
            print("❌ 실패: 주석이 제거된 코드가 기대 결과와 다릅니다.")

            # Generate and print a diff for easy comparison
            diff = difflib.unified_diff(
                expected_cleaned_code.strip().splitlines(keepends=True),
                actual_cleaned_code.strip().splitlines(keepends=True),
                fromfile='expected_result.swift',
                tofile='actual_result (from remover)',
            )
            print("\n--- 차이점 (Diff) ---")
            print(''.join(diff))

    except FileNotFoundError as e:
        print(f"오류: 테스트 파일을 찾을 수 없습니다 - {e.filename}")
        print("스크립트가 realistic_source.swift와 expected_result.swift 파일과 동일한 디렉토리에 있는지 확인하세요.")
    except Exception as e:
        print(f"테스트 중 예기치 않은 오류가 발생했습니다: {e}")


if __name__ == '__main__':
    run_realistic_test()
