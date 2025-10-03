"""
주석 제거 전후 파일 크기 통계 분석 + 처리 시간 측정
"""
from pathlib import Path
from typing import Dict, List, Tuple
import time


def get_directory_size(directory: Path) -> int:
    """디렉토리의 총 크기 (bytes) 계산"""
    total = 0
    for file in directory.rglob('*.swift'):
        total += file.stat().st_size
    return total


def get_file_stats(directory: Path) -> List[Dict]:
    """디렉토리 내 모든 Swift 파일의 통계"""
    files = []
    for file in sorted(directory.glob('*.swift')):
        size = file.stat().st_size
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.count('\n')

        files.append({
            'name': file.name,
            'size': size,
            'lines': lines
        })
    return files


def format_size(size_bytes: int) -> str:
    """바이트를 읽기 좋은 형식으로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def format_time(seconds: float) -> str:
    """초를 읽기 좋은 형식으로 변환"""
    if seconds < 1:
        return f"{seconds * 1000:.2f} ms"
    elif seconds < 60:
        return f"{seconds:.2f} 초"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}분 {secs:.2f}초"


def analyze_compression():
    """압축률 분석 및 통계 출력"""

    # 전체 시작 시간
    total_start_time = time.time()

    input_root = Path('input')
    output_root = Path('output')

    if not input_root.exists() or not output_root.exists():
        print("❌ 오류: input 또는 output 디렉토리가 없습니다.")
        return

    # 프로젝트 목록
    projects = [d.name for d in input_root.iterdir() if d.is_dir()]

    if not projects:
        print("❌ 오류: 프로젝트가 없습니다.")
        return

    print("=" * 80)
    print("주석 제거 전후 파일 크기 통계 분석")
    print("=" * 80)

    # 전체 통계
    total_input_size = 0
    total_output_size = 0
    total_input_lines = 0
    total_output_lines = 0
    total_files = 0

    project_stats = []

    # 프로젝트별 분석 (시간 측정)
    for project in projects:
        project_start = time.time()

        input_dir = input_root / project
        output_dir = output_root / project

        if not output_dir.exists():
            continue

        input_files = get_file_stats(input_dir)
        output_files = get_file_stats(output_dir)

        # 파일명으로 매칭
        input_dict = {f['name']: f for f in input_files}
        output_dict = {f['name']: f for f in output_files}

        project_input_size = sum(f['size'] for f in input_files)
        project_output_size = sum(f['size'] for f in output_files)
        project_input_lines = sum(f['lines'] for f in input_files)
        project_output_lines = sum(f['lines'] for f in output_files)

        project_time = time.time() - project_start

        project_stats.append({
            'name': project,
            'files': len(input_files),
            'input_size': project_input_size,
            'output_size': project_output_size,
            'input_lines': project_input_lines,
            'output_lines': project_output_lines,
            'time': project_time
        })

        total_input_size += project_input_size
        total_output_size += project_output_size
        total_input_lines += project_input_lines
        total_output_lines += project_output_lines
        total_files += len(input_files)

    # 프로젝트별 통계 출력
    print("\n📊 프로젝트별 통계")
    print("-" * 80)

    for stat in project_stats:
        saved_size = stat['input_size'] - stat['output_size']
        saved_lines = stat['input_lines'] - stat['output_lines']
        reduction_rate = (saved_size / stat['input_size'] * 100) if stat['input_size'] > 0 else 0

        print(f"\n프로젝트: {stat['name']}")
        print(f"  파일 수: {stat['files']}개")
        print(f"  원본 크기: {format_size(stat['input_size'])} ({stat['input_size']:,} bytes)")
        print(f"  정리 후 크기: {format_size(stat['output_size'])} ({stat['output_size']:,} bytes)")
        print(f"  절약된 크기: {format_size(saved_size)} ({saved_size:,} bytes)")
        print(f"  압축률: {reduction_rate:.2f}%")
        print(f"  원본 줄 수: {stat['input_lines']:,}줄")
        print(f"  정리 후 줄 수: {stat['output_lines']:,}줄")
        print(f"  제거된 줄: {saved_lines:,}줄")
        print(f"  분석 시간: {format_time(stat['time'])}")

    # 전체 통계 출력
    total_saved_size = total_input_size - total_output_size
    total_saved_lines = total_input_lines - total_output_lines
    total_reduction_rate = (total_saved_size / total_input_size * 100) if total_input_size > 0 else 0

    # 전체 소요 시간
    total_time = time.time() - total_start_time

    print("\n" + "=" * 80)
    print("📈 전체 통계")
    print("=" * 80)
    print(f"\n총 프로젝트 수: {len(project_stats)}개")
    print(f"총 파일 수: {total_files}개")
    print(f"\n원본 총 크기: {format_size(total_input_size)} ({total_input_size:,} bytes)")
    print(f"정리 후 총 크기: {format_size(total_output_size)} ({total_output_size:,} bytes)")
    print(f"총 절약 크기: {format_size(total_saved_size)} ({total_saved_size:,} bytes)")
    print(f"전체 압축률: {total_reduction_rate:.2f}%")
    print(f"\n원본 총 줄 수: {total_input_lines:,}줄")
    print(f"정리 후 총 줄 수: {total_output_lines:,}줄")
    print(f"총 제거된 줄: {total_saved_lines:,}줄")

    # 평균 통계
    if len(project_stats) > 0:
        avg_reduction = sum(
            (s['input_size'] - s['output_size']) / s['input_size'] * 100
            if s['input_size'] > 0 else 0
            for s in project_stats
        ) / len(project_stats)

        print(f"\n평균 압축률: {avg_reduction:.2f}%")
        print(f"프로젝트당 평균 절약: {format_size(total_saved_size // len(project_stats))}")
        print(f"파일당 평균 절약: {format_size(total_saved_size // total_files)}")

    # 처리 시간 통계
    print("\n" + "=" * 80)
    print("⏱️  처리 시간 통계")
    print("=" * 80)
    print(f"\n총 분석 시간: {format_time(total_time)}")

    if total_files > 0:
        time_per_file = total_time / total_files
        print(f"파일당 평균 시간: {format_time(time_per_file)}")

    if total_input_size > 0:
        # KB당 처리 시간
        kb_processed = total_input_size / 1024
        time_per_kb = total_time / kb_processed

        # MB당 처리 시간 추정
        time_per_mb = time_per_kb * 1024

        print(f"\n처리 속도:")
        print(f"  - {format_size(total_input_size / total_time)}/초")
        print(f"  - 1 KB 처리: {format_time(time_per_kb)}")
        print(f"  - 1 MB 처리 예상: {format_time(time_per_mb)}")

        # 다양한 크기별 예상 시간
        print(f"\n예상 처리 시간:")
        for size_mb in [1, 10, 50, 100, 500]:
            estimated = time_per_mb * size_mb
            print(f"  - {size_mb} MB: {format_time(estimated)}")

    # 상세 파일별 통계 (상위 10개)
    print("\n" + "=" * 80)
    print("🔝 가장 많이 압축된 파일 TOP 10")
    print("=" * 80)

    all_file_stats = []
    for project in projects:
        input_dir = input_root / project
        output_dir = output_root / project

        if not output_dir.exists():
            continue

        input_files = get_file_stats(input_dir)
        output_files = get_file_stats(output_dir)

        input_dict = {f['name']: f for f in input_files}
        output_dict = {f['name']: f for f in output_files}

        for name in input_dict:
            if name in output_dict:
                input_f = input_dict[name]
                output_f = output_dict[name]
                saved = input_f['size'] - output_f['size']
                reduction = (saved / input_f['size'] * 100) if input_f['size'] > 0 else 0

                all_file_stats.append({
                    'project': project,
                    'name': name,
                    'input_size': input_f['size'],
                    'output_size': output_f['size'],
                    'saved': saved,
                    'reduction': reduction
                })

    # 절약 크기 기준 정렬
    top_files = sorted(all_file_stats, key=lambda x: x['saved'], reverse=True)[:10]

    for i, f in enumerate(top_files, 1):
        print(f"\n{i}. {f['name']} ({f['project']})")
        print(f"   원본: {format_size(f['input_size'])} → 정리 후: {format_size(f['output_size'])}")
        print(f"   절약: {format_size(f['saved'])} ({f['reduction']:.1f}%)")

    print("\n" + "=" * 80)
    print(f"\n총 소요 시간: {format_time(total_time)}")
    print("=" * 80)


if __name__ == '__main__':
    analyze_compression()