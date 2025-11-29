# 002 - RAPIDS cuDF Excel Acceleration

## 개요

RAGFlow Excel 파서에 NVIDIA RAPIDS cuDF를 적용하여 GPU 가속을 구현하는 패치 패키지.

## 목표

- **Linux 프로덕션**: cuDF GPU 가속으로 10-150x 성능 향상
- **Windows 개발**: CPU 폴백으로 동일 로직 테스트 가능
- **코드 변경 최소화**: `cudf.pandas` 모드로 기존 코드 수정 없이 가속

## 기술 스택

| 구성 요소 | 버전/사양 |
|-----------|-----------|
| RAPIDS cuDF | 25.10+ |
| CUDA | 12.x |
| Python | 3.10+ |
| pandas | 2.2.x |
| 지원 GPU | NVIDIA Compute Capability 7.0+ |

## 파일 구조

```
patches/rapids-cudf/
├── README.md                    # 사용 문서
├── excel_parser_cudf.py         # GPU 가속 파서 (원본 교체)
├── scripts/
│   ├── install_rapids.sh        # Linux: cuDF 설치 + 패치 적용
│   ├── rollback_rapids.sh       # Linux: 원본 복원
│   └── test_parser_windows.py   # Windows: 로직 검증 테스트
└── backup/                      # 설치 시 자동 생성
```

## 작동 방식

```
┌─────────────────────────────────────────────────────┐
│              excel_parser_cudf.py                   │
├─────────────────────────────────────────────────────┤
│  import check:                                      │
│  ├─ Linux + cuDF installed → GPU acceleration ON   │
│  └─ Windows / no cuDF     → CPU fallback (pandas)  │
│                                                     │
│  Result: Same API, same output, different speed    │
└─────────────────────────────────────────────────────┘
```

## 설치 방법

### 1. Windows 테스트 (CPU)

```powershell
cd patches/rapids-cudf
python scripts/test_parser_windows.py
```

예상 결과:
```
===================================
ALL TESTS PASSED!
===================================
The cuDF parser produces identical results to the original.
```

### 2. Linux 프로덕션 (GPU)

```bash
# RAGFlow 실행 확인
docker compose up -d

# 설치 스크립트 실행
chmod +x patches/rapids-cudf/scripts/install_rapids.sh
./patches/rapids-cudf/scripts/install_rapids.sh

# 서비스 재시작
docker compose restart ragflow-server
```

### 3. 가속 상태 확인

```bash
docker exec ragflow-server python3 -c "
from deepdoc.parser.excel_parser import get_acceleration_status
import json
print(json.dumps(get_acceleration_status(), indent=2))
"
```

예상 출력:
```json
{
  "cudf_available": true,
  "gpu_accelerated": true,
  "platform": "Linux",
  "pandas_version": "2.2.3"
}
```

## 롤백 방법

```bash
./patches/rapids-cudf/scripts/rollback_rapids.sh
docker compose restart ragflow-server
```

## 성능 비교

| 작업 | CPU (pandas) | GPU (cuDF) | 배속 |
|------|--------------|------------|------|
| CSV 읽기 | ~2.5s | ~0.1s | 25x |
| DataFrame 연산 | ~1.0s | ~0.05s | 20x |
| 전체 파싱 | ~135s | ~15s | 9x |

*6000행, 10열 한국어 영업보고서 기준*

## 테스트 결과

### Windows 테스트 (2024-11-30)

- **테스트 파일**: 49,000행 한국어 Excel
- **결과**: PASS
  - Row count: 일치
  - Chunk count: 일치
  - Total rows: 일치
- **소요 시간**: ~35초 (CPU)

### Docker 테스트 (2024-11-30)

- **환경**: Ubuntu 22.04, CUDA 12.8, RTX 2070
- **cuDF 버전**: 25.10.00
- **GPU 가속**: 활성화 확인
- **롤백 테스트**: 성공

## 제한사항

1. **Linux 전용 GPU**: RAPIDS cuDF는 Linux만 지원
2. **openpyxl 미가속**: `load_workbook`은 CPU 전용, DataFrame 연산만 가속
3. **VRAM 사용**: 일반 작업 기준 1-2GB 추가 VRAM 필요

## API 호환성

원본 `RAGFlowExcelParser`와 100% 호환:

```python
from deepdoc.parser.excel_parser import RAGFlowExcelParser, get_acceleration_status

# 기존 사용법 그대로
parser = RAGFlowExcelParser()
rows = parser(content)
html_chunks = parser.html(content)
row_count = RAGFlowExcelParser.row_number(filename, content)

# 추가된 API
status = get_acceleration_status()  # 가속 상태 확인
parser.is_gpu_accelerated()         # GPU 활성화 여부
```

## 관련 이슈

- 001-ragflow-korean-optimization에서 Excel 파싱 성능 개선 필요성 도출
- Naive + HTML4Excel 최적 조합 확인 후 GPU 가속 패치 개발

## 브랜치

- `002-rapids-cudf-excel-acceleration`
- 커밋: `cf3bffc0`
