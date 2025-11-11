import json
import uuid
import requests
from datetime import datetime
from functools import wraps
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import BatchLog, Woo
from django.utils import timezone


def fetch_data_from_db():
    """전송되지 않은 데이터만 조회"""
    results = Woo.objects.filter(is_sent=False).values(
        'id', 'email', 'phone', 'name', '_id', 'createdby', 'modifiedby'
    )
    return list(results)


def transform_to_aep_format(db_record):
    """DB 레코드를 AEP 포맷으로 변환 - header/body 구조"""
    tenant_key = settings.AEP_TENANT_ID.strip('_')
    
    return {
        "header": {
            "schemaRef": {
                "id": settings.AEP_SCHEMA_ID,
                "contentType": "application/vnd.adobe.xed-full+json;version=1"
            },
            "imsOrgId": settings.AEP_IMS_ORG_ID,
            "datasetId": settings.AEP_DATASET_ID,
            "source": {
                "name": "Batch API Source"
            }
        },
        "body": {
            "xdmMeta": {
                "schemaRef": {
                    "id": settings.AEP_SCHEMA_ID,
                    "contentType": "application/vnd.adobe.xed-full+json;version=1"
                }
            },
            "xdmEntity": {
                "_id": db_record.get('_id'),
                "identityMap": {
                    "crmId": [
                        {
                            "id": db_record.get('_id')
                        }
                    ],
                    "id": [
                        {
                            "id": db_record.get('_id')
                        }
                    ]
                },
                f"_{tenant_key}": {
                    "TEST_ID": db_record.get('id'),
                    "TEST_NAME": db_record.get('name'),
                    "identification": {
                        "core": {
                            "email": db_record.get('email'),
                            "phoneNumber": db_record.get('phone'),
                            "crmId": db_record.get('_id')
                        }
                    }
                }
            }
        }
    }


def send_to_aep(payload):
    """AEP로 데이터 전송"""
    if getattr(settings, 'AEP_MOCK_MODE', True):
        print("⚠️ MOCK MODE 활성화됨!")
        return {
            'success': True,
            'status_code': 200,
            'response': 'MOCK MODE: Data not actually sent to AEP',
            'mock': True
        }
    
    aep_endpoint = settings.AEP_STREAMING_ENDPOINT
    
    headers = {
        'Content-Type': 'application/json',
        'x-gw-ims-org-id': settings.AEP_IMS_ORG_ID,
    }
    
    print("=" * 80)
    print("🚀 AEP로 전송 시작")
    print(f"Endpoint: {aep_endpoint}")
    print(f"Headers: {headers}")
    print(f"Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("=" * 80)
    
    try:
        response = requests.post(
            aep_endpoint,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"✅ 응답 코드: {response.status_code}")
        print(f"📄 응답 내용: {response.text}")
        print("=" * 80)
        
        if response.status_code in [200, 201, 202]:
            return {
                'success': True,
                'status_code': response.status_code,
                'response': response.text
            }
        else:
            print(f"❌ 에러 발생!")
            return {
                'success': False,
                'status_code': response.status_code,
                'error': response.text
            }
    except requests.exceptions.RequestException as e:
        print(f"🔥 예외 발생: {str(e)}")
        print("=" * 80)
        return {
            'success': False,
            'error': str(e)
        }


@require_http_methods(["GET"])
def health_check(request):
    """헬스 체크 엔드포인트"""
    return JsonResponse({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "Batch API",
        "database": {
            "total_records": Woo.objects.count(),
            "unsent_records": Woo.objects.filter(is_sent=False).count()
        }
    })



ALLOWED_IPS = ['127.0.0.1', 'localhost', '::1']

def require_local_ip(view_func):
    """로컬 IP만 허용"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        client_ip = request.META.get('REMOTE_ADDR')
        
        if client_ip not in ALLOWED_IPS:
            return JsonResponse({
                'error': 'Access denied'
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


@require_local_ip
@csrf_exempt
@require_http_methods(["POST"])
def run_batch(request):
    """배치 실행 - 전송되지 않은 데이터만"""
    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    
    # 배치 로그 생성
    batch_log = BatchLog.objects.create(
        batch_id=batch_id,
        status='RUNNING'
    )
    
    try:
        # 1. 전송되지 않은 데이터 조회
        db_records = fetch_data_from_db()
        batch_log.total_records = len(db_records)
        batch_log.save()
        
        if len(db_records) == 0:
            batch_log.status = 'SUCCESS'
            batch_log.completed_at = timezone.now()
            batch_log.save()
            
            return JsonResponse({
                'status': 'completed',
                'batch_id': batch_id,
                'total_records': 0,
                'success_count': 0,
                'fail_count': 0,
                'batch_status': 'SUCCESS',
                'message': 'No unsent records to process'
            })
        
        success_count = 0
        fail_count = 0
        errors = []
        success_ids = []
        
        # 2. 각 레코드를 AEP로 전송
        for record in db_records:
            try:
                # AEP 포맷으로 변환
                aep_payload = transform_to_aep_format(record)
                
                # AEP로 전송
                result = send_to_aep(aep_payload)
                
                if result.get('success'):
                    success_count += 1
                    success_ids.append(record.get('id'))
                else:
                    fail_count += 1
                    errors.append({
                        'record_id': record.get('id'),
                        'error': result.get('error', 'Unknown error')
                    })
            except Exception as e:
                fail_count += 1
                errors.append({
                    'record_id': record.get('id'),
                    'error': str(e)
                })
        
        # 3. 성공한 레코드 플래그 업데이트
        if success_ids:
            Woo.objects.filter(id__in=success_ids).update(
                is_sent=True,
                sent_at=timezone.now()
            )
        
        # 4. 배치 로그 업데이트
        batch_log.success_count = success_count
        batch_log.fail_count = fail_count
        batch_log.completed_at = timezone.now()
        
        if fail_count == 0:
            batch_log.status = 'SUCCESS'
        elif success_count == 0:
            batch_log.status = 'FAILED'
            batch_log.error_message = json.dumps(errors)
        else:
            batch_log.status = 'PARTIAL'
            batch_log.error_message = json.dumps(errors)
        
        batch_log.save()
        
        return JsonResponse({
            'status': 'completed',
            'batch_id': batch_id,
            'total_records': batch_log.total_records,
            'success_count': success_count,
            'fail_count': fail_count,
            'batch_status': batch_log.status,
            'errors': errors if errors else None
        })
        
    except Exception as e:
        batch_log.status = 'FAILED'
        batch_log.error_message = str(e)
        batch_log.completed_at = timezone.now()
        batch_log.save()
        
        return JsonResponse({
            'status': 'failed',
            'batch_id': batch_id,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def batch_status(request, batch_id):
    """배치 상태 조회"""
    try:
        batch_log = BatchLog.objects.get(batch_id=batch_id)
        return JsonResponse({
            'batch_id': batch_log.batch_id,
            'status': batch_log.status,
            'total_records': batch_log.total_records,
            'success_count': batch_log.success_count,
            'fail_count': batch_log.fail_count,
            'started_at': batch_log.started_at.isoformat() if batch_log.started_at else None,
            'completed_at': batch_log.completed_at.isoformat() if batch_log.completed_at else None,
            'error_message': batch_log.error_message
        })
    except BatchLog.DoesNotExist:
        return JsonResponse({
            'error': 'Batch not found'
        }, status=404)


@require_http_methods(["GET"])
def batch_list(request):
    """배치 목록 조회"""
    batches = BatchLog.objects.all()[:20]
    
    batch_list = []
    for batch in batches:
        batch_list.append({
            'batch_id': batch.batch_id,
            'status': batch.status,
            'total_records': batch.total_records,
            'success_count': batch.success_count,
            'fail_count': batch.fail_count,
            'started_at': batch.started_at.isoformat(),
            'completed_at': batch.completed_at.isoformat() if batch.completed_at else None
        })
    
    return JsonResponse({
        'total': BatchLog.objects.count(),
        'batches': batch_list
    })


@csrf_exempt
@require_http_methods(["POST"])
def test_payload(request):
    """테스트용 페이로드 생성"""
    try:
        # 샘플 레코드
        sample_record = {
            'id': 999,
            'email': 'test@example.com',
            'phone': '+821012345678',
            'name': 'test_user',
            '_id': 'test999251017',
            'createdby': datetime.utcnow().isoformat(),
            'modifiedby': datetime.utcnow().isoformat()
        }
        
        # AEP 포맷으로 변환
        aep_payload = transform_to_aep_format(sample_record)
        
        return JsonResponse({
            'status': 'success',
            'sample_record': sample_record,
            'aep_payload': aep_payload
        }, json_dumps_params={'indent': 2})
        
    except Exception as e:
        return JsonResponse({
            'status': 'failed',
            'error': str(e)
        }, status=500)


