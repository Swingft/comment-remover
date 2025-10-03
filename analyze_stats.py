import os
import time
from pathlib import Path
from remove_swift_comments import SwiftCommentRemover


def get_file_size(filepath):
    """파일 크기를 바이트 단위로 반환"""
    return os.path.getsize(filepath)


def format_size(bytes_size):
    """바이트를 읽기 좋은 형식으로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def analyze_project(project_path):
    """단일 프로젝트 분석"""
    project_name = os.path.basename(project_path)
    swift_files = list(Path(project_path).rglob('*.swift'))

    if not swift_files:
        return None

    print(f"\n{'=' * 70}")
    print(f"프로젝트: {project_name}")
    print(f"{'=' * 70}")
    print(f"Swift 파일 개수: {len(swift_files)}개")

    remover = SwiftCommentRemover()

    total_original_size = 0
    total_cleaned_size = 0
    total_files = len(swift_files)

    start_time = time.time()

    for swift_file in swift_files:
        try:
            # 원본 파일 읽기
            with open(swift_file, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # 주석 제거
            cleaned_content = remover.remove_comments(original_content)

            # 크기 계산 (UTF-8 인코딩 기준)
            original_size = len(original_content.encode('utf-8'))
            cleaned_size = len(cleaned_content.encode('utf-8'))

            total_original_size += original_size
            total_cleaned_size += cleaned_size

        except Exception as e:
            print(f"  ⚠️  오류 ({swift_file.name}): {e}")
            total_files -= 1

    end_time = time.time()
    processing_time = end_time - start_time

    if total_files == 0:
        print("처리 가능한 파일이 없습니다.")
        return None

    # 압축률 계산
    compression_ratio = ((
                                     total_original_size - total_cleaned_size) / total_original_size * 100) if total_original_size > 0 else 0

    # 처리 속도 계산 (MB/s)
    processing_speed = (total_original_size / (1024 * 1024)) / processing_time if processing_time > 0 else 0

    # 결과 출력
    print(f"\n처리 결과:")
    print(f"  • 처리 시간: {processing_time:.3f}초")
    print(f"  • 처리된 파일: {total_files}개")
    print(f"  • 원본 크기: {format_size(total_original_size)}")
    print(f"  • 처리 후 크기: {format_size(total_cleaned_size)}")
    print(f"  • 절감 크기: {format_size(total_original_size - total_cleaned_size)}")
    print(f"  • 압축률: {compression_ratio:.2f}%")
    print(f"  • 처리 속도: {processing_speed:.2f} MB/s")

    return {
        'name': project_name,
        'files': total_files,
        'time': processing_time,
        'original_size': total_original_size,
        'cleaned_size': total_cleaned_size,
        'compression_ratio': compression_ratio,
        'speed': processing_speed
    }


def analyze_all_projects():
    """./project 디렉토리의 모든 프로젝트 분석"""
    project_dir = Path('./project')

    if not project_dir.exists():
        print("❌ './project' 디렉토리를 찾을 수 없습니다.")
        return

    # project 디렉토리 내의 모든 서브디렉토리 찾기
    projects = [d for d in project_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]

    if not projects:
        print("❌ './project' 디렉토리에 프로젝트가 없습니다.")
        return

    print("Swift 주석 제거 도구 - 프로젝트 분석")
    print(f"총 {len(projects)}개의 프로젝트를 분석합니다...\n")

    results = []

    for project_path in sorted(projects):
        result = analyze_project(project_path)
        if result:
            results.append(result)

    # 전체 통계
    if results:
        print(f"\n{'=' * 70}")
        print("전체 통계")
        print(f"{'=' * 70}")

        total_files = sum(r['files'] for r in results)
        total_time = sum(r['time'] for r in results)
        total_original = sum(r['original_size'] for r in results)
        total_cleaned = sum(r['cleaned_size'] for r in results)
        avg_compression = sum(r['compression_ratio'] for r in results) / len(results)
        overall_speed = (total_original / (1024 * 1024)) / total_time if total_time > 0 else 0

        print(f"  • 분석된 프로젝트: {len(results)}개")
        print(f"  • 총 파일 수: {total_files}개")
        print(f"  • 총 처리 시간: {total_time:.3f}초")
        print(f"  • 총 원본 크기: {format_size(total_original)}")
        print(f"  • 총 처리 후 크기: {format_size(total_cleaned)}")
        print(f"  • 총 절감 크기: {format_size(total_original - total_cleaned)}")
        print(f"  • 평균 압축률: {avg_compression:.2f}%")
        print(f"  • 전체 처리 속도: {overall_speed:.2f} MB/s")

        # 프로젝트별 요약
        print(f"\n{'=' * 70}")
        print("프로젝트별 요약")
        print(f"{'=' * 70}")
        print(f"{'프로젝트명':<20} {'파일':<8} {'시간(초)':<10} {'압축률':<10} {'속도(MB/s)':<12}")
        print(f"{'-' * 70}")
        for r in results:
            print(
                f"{r['name']:<20} {r['files']:<8} {r['time']:<10.3f} {r['compression_ratio']:<9.2f}% {r['speed']:<12.2f}")


if __name__ == '__main__':
    analyze_all_projects()