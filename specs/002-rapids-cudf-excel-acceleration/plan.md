# 002 - RAPIDS cuDF Excel Acceleration Plan

## 목표

RAGFlow Excel 파서에 NVIDIA RAPIDS cuDF GPU 가속을 적용하여 대용량 Excel 파일 처리 성능을 10-150배 향상시킨다.

## 접근 방식

### 핵심 전략: cudf.pandas 모드

기존 pandas 코드를 수정하지 않고 `cudf.pandas.install()`을 통해 투명하게 GPU 가속 적용.

```python
# 적용 전
import pandas as pd
df = pd.read_excel(file)  # CPU

# 적용 후
import cudf.pandas
cudf.pandas.install()
import pandas as pd
df = pd.read_excel(file)  # GPU (자동)
```

### 플랫폼 전략

| 환경 | 동작 | 용도 |
|------|------|------|
| Windows | CPU pandas 폴백 | 개발/로직 테스트 |
| Linux + GPU | cuDF GPU 가속 | 프로덕션 |
| Linux - GPU | CPU pandas 폴백 | 폴백 |

## 설계 결정

### 1. 패치 패키지 구조

**선택**: 독립 패치 디렉토리 (`patches/rapids-cudf/`)

**이유**:
- 원본 RAGFlow 코드와 분리
- 쉬운 적용/롤백
- GitHub 업로드 용이
- 버전 관리 독립적

### 2. 테스트 전략

**선택**: 임베디드 원본 파서 복사

**이유**:
- `deepdoc` 의존성 (beartype 등) 회피
- Windows에서 독립 실행 가능
- 결과 비교 정확성 보장

### 3. 설치 방식

**선택**: Shell 스크립트 + Docker exec

**이유**:
- 컨테이너 내부 직접 수정
- 백업 자동 생성
- 롤백 스크립트 제공

## 구현 단계

### Phase 1: 파서 개발 ✅

1. ~~cudf.pandas 통합 파서 작성~~
2. ~~플랫폼 감지 로직 구현~~
3. ~~폴백 메커니즘 구현~~
4. ~~get_acceleration_status() API 추가~~

### Phase 2: 스크립트 개발 ✅

1. ~~install_rapids.sh 작성~~
2. ~~rollback_rapids.sh 작성~~
3. ~~test_parser_windows.py 작성~~

### Phase 3: 테스트 ✅

1. ~~Windows CPU 테스트 (49,000행)~~
2. ~~Docker GPU 테스트~~
3. ~~결과 일치성 검증~~
4. ~~롤백 테스트~~

### Phase 4: 문서화 ✅

1. ~~README.md 작성~~
2. ~~spec.md 작성~~
3. ~~plan.md 작성~~
4. ~~tasks.md 작성~~

## 기술 상세

### GPU 가속 대상

| 함수 | 가속 여부 | 설명 |
|------|----------|------|
| `pd.read_excel()` | ✅ | 대용량 파일 읽기 |
| `pd.read_csv()` | ✅ | CSV 폴백 읽기 |
| `df.apply()` | ✅ | 문자열 정리 연산 |
| `df.replace()` | ✅ | 정규식 치환 |
| `load_workbook()` | ❌ | openpyxl CPU 전용 |

### 메모리 요구사항

- 기본 VRAM: 1-2GB (일반 워크로드)
- 대용량 파일: 파일 크기의 2-3배 VRAM

### 호환성 매트릭스

| CUDA | cuDF | Python | 상태 |
|------|------|--------|------|
| 12.x | 25.10+ | 3.10+ | ✅ 검증됨 |
| 11.x | 25.10+ | 3.10+ | ⚠️ 미검증 |

## 리스크 및 대응

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| cuDF 설치 실패 | 중 | 중 | CPU 폴백 자동 적용 |
| VRAM 부족 | 저 | 중 | 대용량 파일 분할 처리 |
| 버전 충돌 | 저 | 저 | pip 경고만, 기능 정상 |

## 성공 기준

1. ✅ Windows 테스트 통과 (결과 일치)
2. ✅ Docker GPU 가속 활성화 확인
3. ✅ 롤백 정상 동작
4. ✅ 문서화 완료

## 향후 개선

1. **벤치마크 자동화**: 다양한 파일 크기별 성능 측정
2. **메모리 최적화**: 청크 단위 처리로 VRAM 사용 최적화
3. **다중 GPU**: 대규모 배치 처리 시 GPU 분산
