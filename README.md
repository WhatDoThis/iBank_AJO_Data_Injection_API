# iBank AJO Data Injection API

Adobe Journey Optimizer (AJO) 데이터 자동 주입 API

## 📋 프로젝트 개요

Django 기반 배치 API로 매일 자동으로 테스트 데이터를 생성하고 Adobe Experience Platform(AEP)으로 전송합니다.

## 🚀 주요 기능

- **자동 배치 처리**: 매일 오전 2시 자동 실행
- **데이터 생성**: 5개씩 증가하는 테스트 데이터
- **AEP 전송**: Streaming Ingestion API를 통한 실시간 전송
- **전송 추적**: is_sent 플래그로 전송 상태 관리
- **배치 이력**: 모든 배치 실행 기록 저장

## 🛠️ 기술 스택

- **Backend**: Django 4.2 LTS
- **Database**: SQLite3
- **Scheduler**: Cron
- **Python**: 3.6+

## 📦 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/WhatDoThis/iBank_AJO_Data_Injection_API.git
cd iBank_AJO_Data_Injection_API
```

### 2. 가상환경 설정
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정

`.env` 파일 생성:
```bash
DJANGO_SECRET_KEY=your-secret-key-here
AEP_STREAMING_ENDPOINT=https://dcs.adobedc.net/collection/...
AEP_IMS_ORG_ID=your-org-id@AdobeOrg
AEP_DATASET_ID=your-dataset-id
AEP_SCHEMA_ID=https://ns.adobe.com/...
AEP_TENANT_ID=_your_tenant
AEP_MOCK_MODE=True
```

### 5. 데이터베이스 마이그레이션
```bash
cd ajo_api_project
python manage.py migrate
```

### 6. 서버 실행
```bash
python manage.py runserver 0.0.0.0:8000
```

## ⚙️ 배치 설정

### Cron 설정 (매일 오전 2시 실행)
```bash
crontab -e
```

추가:
```bash
0 2 * * * cd /path/to/ajo_api_project && /path/to/venv/bin/python manage.py daily_batch >> /var/log/daily_batch.log 2>&1
```

### Systemd 서비스 (선택사항)

`/etc/systemd/system/django-batch-api.service`:
```ini
[Unit]
Description=Django Batch API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/woo_test/ajo-api-test/ajo_api_project
Environment="DJANGO_SECRET_KEY=..."
ExecStart=/root/woo_test/ajo-api-test/venv/bin/python manage.py runserver 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📡 API 엔드포인트

### 1. 배치 수동 실행
```bash
POST /api/batch/run/
```

### 2. 배치 상태 조회
```bash
GET /api/batch/status/<batch_id>/
```

### 3. 배치 목록 조회
```bash
GET /api/batch/list/
```

### 4. 헬스 체크
```bash
GET /api/batch/health/
```

## 📊 데이터 구조

### Woo 모델
- `id`: Primary Key (자동 증가)
- `email`: 이메일
- `phone`: 전화번호
- `name`: 이름 (woo + id)
- `_id`: 고유 ID (woo + id + yymmdd)
- `is_sent`: 전송 여부
- `sent_at`: 전송 시간
- `createdby`: 생성 시간
- `modifiedby`: 수정 시간

### XDM 페이로드 구조
```json
{
  "body": {
    "xdmEntity": {
      "_id": "woo1251024",
      "identityMap": {
        "id": [{"id": "woo1251024"}]
      },
      "_aeppsemea": {
        "TEST_ID": 1,
        "TEST_NAME": "woo1",
        "identification": {
          "core": {
            "email": "whi21@naver.com",
            "phoneNumber": "+821098714077",
            "crmId": "woo1251024"
          }
        }
      }
    }
  }
}
```

## 🔧 Management Commands

### daily_batch
매일 자동 실행되는 배치 작업:
- 5개 데이터 생성
- 1분 대기
- AEP 전송
- is_sent 업데이트
```bash
python manage.py daily_batch
```

### batch_history
배치 실행 이력 조회:
```bash
# 오늘 실행 이력
python manage.py batch_history --today

# 최근 10개
python manage.py batch_history --limit 10
```

## 📝 로그

배치 실행 로그는 `/var/log/daily_batch.log`에 저장됩니다.
```bash
tail -f /var/log/daily_batch.log
```

## 🔍 트러블슈팅

### 배치가 실행 안 됨
```bash
# Cron 서비스 확인
sudo systemctl status crond

# Cron 설정 확인
crontab -l

# 수동 실행 테스트
python manage.py daily_batch
```

### 데이터 전송 실패
```bash
# 미전송 데이터 확인
python manage.py shell -c "from batch_api.models import Woo; print(Woo.objects.filter(is_sent=False).count())"

# 재전송
curl -X POST http://localhost:8000/api/batch/run/
```

## 📜 라이선스

MIT License

## 👤 Author

iBank Dev Team
