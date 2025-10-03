"""
검증용 텍스트 파일 생성 스크립트
input/output 폴더의 파일들을 비교하여 검증용 .txt 파일 생성
"""
from pathlib import Path
from typing import List, Tuple


def get_file_size_kb(file_path: Path) -> float:
    """파일 크기를 KB 단위로 반환"""
    return file_path.stat().st_size / 1024


def group_files_by_size(files: List[Path], max_size_kb: float = 50.0) -> List[List[Path]]:
    """
    파일들을 크기 제한에 맞춰 그룹으로 나눔

    Args:
        files: 파일 경로 리스트
        max_size_kb: 그룹당 최대 크기 (KB)

    Returns:
        파일 그룹 리스트
    """
    groups = []
    current_group = []
    current_size = 0.0

    for file in files:
        file_size = get_file_size_kb(file)

        # 현재 그룹에 추가하면 제한 초과 시 새 그룹 시작
        if current_size + file_size > max_size_kb and current_group:
            groups.append(current_group)
            current_group = []
            current_size = 0.0

        current_group.append(file)
        current_size += file_size

    # 마지막 그룹 추가
    if current_group:
        groups.append(current_group)

    return groups


def create_validation_file_for_project(project_name: str, max_size_kb: float = 50.0):
    """
    단일 프로젝트의 검증 파일 생성

    Args:
        project_name: 프로젝트 이름
        max_size_kb: 검증 파일당 최대 크기 (KB)
    """
    input_dir = Path('input') / project_name
    output_dir = Path('output') / project_name
    validation_dir = Path('model_validation')

    # 디렉토리 확인
    if not input_dir.exists():
        print(f"  ⚠️  건너뜀: input 디렉토리 없음 - {project_name}")
        return 0

    if not output_dir.exists():
        print(f"  ⚠️  건너뜀: output 디렉토리 없음 - {project_name}")
        return 0

    # 검증 디렉토리 생성
    validation_dir.mkdir(parents=True, exist_ok=True)

    # Swift 파일 찾기
    input_files = sorted(list(input_dir.glob('*.swift')))

    if not input_files:
        print(f"  ⚠️  건너뜀: Swift 파일 없음 - {project_name}")
        return 0

    # 파일들을 크기 기준으로 그룹화
    file_groups = group_files_by_size(input_files, max_size_kb)

    print(f"\n  프로젝트: {project_name}")
    print(f"  Swift 파일: {len(input_files)}개")
    print(f"  검증 파일 수: {len(file_groups)}개 (그룹당 최대 {max_size_kb}KB)")

    # 각 그룹별로 검증 파일 생성
    for group_idx, file_group in enumerate(file_groups, 1):
        validation_filename = f"validation_{project_name}_{group_idx:02d}.txt"
        validation_path = validation_dir / validation_filename

        with open(validation_path, 'w', encoding='utf-8') as f:
            # 헤더
            f.write("=" * 70 + "\n")
            f.write(f"검증 파일 #{group_idx} - {project_name}\n")
            f.write("=" * 70 + "\n\n")
            f.write("다음 Swift 파일들의 주석 제거가 올바르게 되었는지 검증해주세요.\n")
            f.write("각 파일마다 원본(BEFORE)과 주석 제거 후(AFTER)를 비교해서\n")
            f.write("1. 주석이 모두 제거되었는지\n")
            f.write("2. 코드 로직이 손상되지 않았는지\n")
            f.write("3. 문자열 내용이 보존되었는지\n")
            f.write("확인해주세요.\n\n")

            # 각 파일 처리
            for file_idx, input_file in enumerate(file_group, 1):
                filename = input_file.name
                output_file = output_dir / filename

                if not output_file.exists():
                    print(f"    ⚠️  경고: 출력 파일 없음 - {filename}")
                    continue

                # 파일 읽기
                with open(input_file, 'r', encoding='utf-8') as inf:
                    original_content = inf.read()

                with open(output_file, 'r', encoding='utf-8') as outf:
                    cleaned_content = outf.read()

                # 파일 정보
                f.write("\n" + "=" * 70 + "\n")
                f.write(f"파일 #{file_idx}: {filename}\n")
                f.write("=" * 70 + "\n\n")

                # 통계
                original_lines = original_content.count('\n')
                cleaned_lines = cleaned_content.count('\n')
                removed_lines = original_lines - cleaned_lines
                reduction = (removed_lines / original_lines * 100) if original_lines > 0 else 0
                file_size = get_file_size_kb(input_file)

                f.write(f"📊 통계:\n")
                f.write(f"   파일 크기: {file_size:.1f} KB\n")
                f.write(f"   원본 줄 수: {original_lines}줄\n")
                f.write(f"   정리 후 줄 수: {cleaned_lines}줄\n")
                f.write(f"   제거된 줄: {removed_lines}줄 ({reduction:.1f}%)\n\n")

                # BEFORE
                f.write("-" * 70 + "\n")
                f.write("BEFORE (원본 코드):\n")
                f.write("-" * 70 + "\n")
                f.write(original_content)
                f.write("\n\n")

                # AFTER
                f.write("-" * 70 + "\n")
                f.write("AFTER (주석 제거 후):\n")
                f.write("-" * 70 + "\n")
                f.write(cleaned_content)
                f.write("\n\n")

                # 구분선
                if file_idx < len(file_group):
                    f.write("\n" + "▼" * 70 + "\n")
                    f.write("다음 파일로 이동\n")
                    f.write("▼" * 70 + "\n")

            # 푸터
            f.write("\n" + "=" * 70 + "\n")
            f.write(f"검증 파일 #{group_idx} 끝\n")
            f.write("=" * 70 + "\n")

        print(f"    ✅ {validation_filename} ({len(file_group)}개 파일)")

    return len(file_groups)


def create_all_validation_files(project_names: List[str] = None, max_size_kb: float = 50.0):
    """
    여러 프로젝트의 검증 파일을 한 번에 생성

    Args:
        project_names: 프로젝트 이름 리스트 (None이면 input 폴더의 모든 프로젝트)
        max_size_kb: 검증 파일당 최대 크기 (KB)
    """
    print("=" * 70)
    print("검증용 텍스트 파일 생성")
    print("=" * 70)

    validation_dir = Path('model_validation')
    validation_dir.mkdir(parents=True, exist_ok=True)

    # 프로젝트 목록 결정
    if project_names is None:
        # input 폴더의 모든 하위 디렉토리
        input_root = Path('input')
        if not input_root.exists():
            print("❌ 오류: input 디렉토리가 없습니다.")
            return

        project_names = [d.name for d in input_root.iterdir() if d.is_dir()]

        if not project_names:
            print("❌ 오류: input 디렉토리에 프로젝트가 없습니다.")
            return

        print(f"\ninput 폴더의 모든 프로젝트 처리: {len(project_names)}개")
    else:
        print(f"\n지정된 프로젝트 처리: {len(project_names)}개")

    print(f"검증 파일당 최대 크기: {max_size_kb} KB")
    print("-" * 70)

    # 각 프로젝트 처리
    total_validation_files = 0
    processed_projects = []

    for project_name in project_names:
        num_files = create_validation_file_for_project(project_name, max_size_kb)
        if num_files > 0:
            total_validation_files += num_files
            processed_projects.append(project_name)

    if not processed_projects:
        print("\n❌ 처리된 프로젝트가 없습니다.")
        return

    # 전체 요약 파일 생성
    summary_path = validation_dir / "_summary_all.txt"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("전체 검증 요약\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"총 프로젝트 수: {len(processed_projects)}개\n")
        f.write(f"총 검증 파일 수: {total_validation_files}개\n")
        f.write(f"검증 파일당 최대 크기: {max_size_kb} KB\n\n")

        f.write("프로젝트 목록:\n")
        for project in processed_projects:
            project_files = list(validation_dir.glob(f"validation_{project}_*.txt"))
            f.write(f"  - {project} ({len(project_files)}개 검증 파일)\n")

        f.write("\n사용 방법:\n")
        f.write("1. 각 validation_*.txt 파일을 Claude에게 업로드\n")
        f.write("2. '이 파일들의 주석 제거가 올바른지 검증해주세요' 요청\n")
        f.write("3. Claude가 각 파일을 분석하여 문제점 보고\n")

    # 결과 출력
    print("\n" + "=" * 70)
    print("완료!")
    print("=" * 70)
    print(f"\n처리된 프로젝트: {len(processed_projects)}개")
    for project in processed_projects:
        project_files = list(validation_dir.glob(f"validation_{project}_*.txt"))
        print(f"  - {project}: {len(project_files)}개 검증 파일")

    print(f"\n📂 생성 위치: {validation_dir.absolute()}")
    print(f"   - 검증 파일: validation_*.txt ({total_validation_files}개)")
    print(f"   - 요약 파일: _summary_all.txt")

    print("\n💡 사용법:")
    print("   1. validation_*.txt 파일을 Claude 채팅에 업로드")
    print("   2. '주석 제거가 올바른지 검증해주세요' 요청")
    print("=" * 70)


if __name__ == '__main__':
    # ========================================
    # 설정 1: 특정 프로젝트만 처리
    # ========================================

    # 방법 1: 단일 프로젝트
    # PROJECT_NAMES = ['MySwiftProject']

    # 방법 2: 여러 프로젝트
    # PROJECT_NAMES = ['Project1', 'Project2', 'Project3']

    # 방법 3: input 폴더의 모든 프로젝트 (None으로 설정)
    PROJECT_NAMES = None

    # ========================================
    # 설정 2: 검증 파일당 최대 크기 (KB)
    # ========================================

    MAX_SIZE_KB = 200.0  # 50KB (적절한 크기)
    # MAX_SIZE_KB = 30.0  # 30KB (더 작은 단위)
    # MAX_SIZE_KB = 100.0 # 100KB (더 큰 단위)

    # ========================================

    create_all_validation_files(PROJECT_NAMES, MAX_SIZE_KB)