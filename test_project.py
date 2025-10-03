"""
프로젝트 단위 Swift 주석 제거 테스트 스크립트
"""
from pathlib import Path
from remove_swift_comments import SwiftCommentRemover
import time


def test_project(project_path: str):
    """
    Swift 프로젝트의 모든 파일을 처리하고 input/output 폴더에 평탄화하여 정리합니다.

    Args:
        project_path: Swift 프로젝트 경로
    """
    print("=" * 70)
    print("Swift 프로젝트 주석 제거 테스트")
    print("=" * 70)

    # 프로젝트 경로 확인
    project = Path(project_path)
    if not project.exists():
        print(f"❌ 오류: 경로를 찾을 수 없습니다 - {project_path}")
        return

    # 프로젝트 이름 추출
    project_name = project.name

    # input/output 디렉토리 생성
    input_dir = Path('input') / project_name
    output_dir = Path('output') / project_name

    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Swift 파일 찾기
    swift_files = list(project.glob('**/*.swift'))

    if not swift_files:
        print(f"❌ 오류: .swift 파일을 찾을 수 없습니다 - {project_path}")
        return

    print(f"\n프로젝트: {project.absolute()}")
    print(f"프로젝트 이름: {project_name}")
    print(f"Swift 파일: {len(swift_files)}개 발견")
    print(f"\n📂 입력 복사: {input_dir.absolute()}")
    print(f"📂 출력 저장: {output_dir.absolute()}")

    print("\n" + "-" * 70)
    print("처리 시작...")
    print("-" * 70)

    # 통계 초기화
    stats = {
        'total': len(swift_files),
        'success': 0,
        'failed': 0,
        'total_original_size': 0,
        'total_cleaned_size': 0,
        'total_original_lines': 0,
        'total_cleaned_lines': 0,
    }

    failed_files = []
    start_time = time.time()

    # 파일별 처리
    remover = SwiftCommentRemover()

    for i, swift_file in enumerate(swift_files, 1):
        try:
            # 진행 상황 출력
            relative_path = swift_file.relative_to(project)

            # 평탄화된 파일명 생성 (경로를 _로 구분)
            # 예: Models/User.swift -> Models_User.swift
            flat_name = str(relative_path).replace('/', '_').replace('\\', '_')

            print(f"[{i}/{stats['total']}] {relative_path} -> {flat_name}", end=" ... ")

            # 원본 읽기
            with open(swift_file, 'r', encoding='utf-8') as f:
                source = f.read()

            # input 폴더에 원본 복사 (평탄화된 이름)
            input_file = input_dir / flat_name
            with open(input_file, 'w', encoding='utf-8') as f:
                f.write(source)

            # 주석 제거
            cleaned = remover.remove_comments(source)

            # output 폴더에 저장 (평탄화된 이름)
            output_file = output_dir / flat_name
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(cleaned)

            # 통계 업데이트
            stats['success'] += 1
            stats['total_original_size'] += len(source)
            stats['total_cleaned_size'] += len(cleaned)
            stats['total_original_lines'] += source.count('\n')
            stats['total_cleaned_lines'] += cleaned.count('\n')

            # 압축률 계산
            reduction = (1 - len(cleaned) / len(source)) * 100 if len(source) > 0 else 0
            print(f"✅ ({reduction:.1f}% 감소)")

        except Exception as e:
            stats['failed'] += 1
            failed_files.append((relative_path, str(e)))
            print(f"❌ 실패: {e}")

    # 처리 시간
    elapsed_time = time.time() - start_time

    # 결과 출력
    print("\n" + "=" * 70)
    print("처리 완료")
    print("=" * 70)

    print(f"\n📊 총 파일 수: {stats['total']}개")
    print(f"   ✅ 성공: {stats['success']}개")
    print(f"   ❌ 실패: {stats['failed']}개")

    if stats['success'] > 0:
        print(f"\n📦 원본 크기: {stats['total_original_size']:,} bytes")
        print(f"   정리 후 크기: {stats['total_cleaned_size']:,} bytes")

        total_reduction = (1 - stats['total_cleaned_size'] / stats['total_original_size']) * 100
        print(f"   전체 감소율: {total_reduction:.2f}%")

        print(f"\n📝 원본 줄 수: {stats['total_original_lines']:,}줄")
        print(f"   정리 후 줄 수: {stats['total_cleaned_lines']:,}줄")

        lines_removed = stats['total_original_lines'] - stats['total_cleaned_lines']
        print(f"   제거된 줄: {lines_removed:,}줄")

    print(f"\n⏱️  처리 시간: {elapsed_time:.2f}초")

    if failed_files:
        print(f"\n❌ 실패한 파일 목록:")
        for file_path, error in failed_files:
            print(f"   - {file_path}: {error}")

    print("\n" + "=" * 70)
    print(f"📂 결과 확인:")
    print(f"   입력: {input_dir.absolute()}")
    print(f"   출력: {output_dir.absolute()}")
    print("=" * 70)

    print("\n" + "=" * 70)


def quick_test():
    """빠른 테스트 - 현재 디렉토리의 realistic_source.swift"""
    print("빠른 테스트 모드\n")

    if Path('realistic_source.swift').exists():
        test_project('.', 'test_output')
    else:
        print("realistic_source.swift 파일을 찾을 수 없습니다.")
        print("프로젝트 경로를 직접 지정해주세요:")
        print("\npython test_project.py")


if __name__ == '__main__':
    # ========================================
    # 여기에 프로젝트 경로를 직접 입력하세요
    # ========================================

    PROJECT_PATH = './project/test_project9'  # 테스트할 프로젝트 경로

    # ========================================

    test_project(PROJECT_PATH)