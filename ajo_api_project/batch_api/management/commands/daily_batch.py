from django.core.management.base import BaseCommand
from batch_api.models import Woo
from datetime import datetime
import time
import requests


class Command(BaseCommand):
    help = 'Daily batch job - Create 5 records and send to AEP'

    def handle(self, *args, **options):
        print("=" * 60)
        print("Daily Batch 시작")
        print("=" * 60)
        
        # 마지막 ID 확인
        last_record = Woo.objects.order_by('-id').first()
        last_id = last_record.id if last_record else 0
        start_id = last_id + 1
        
        print(f"마지막 ID: {last_id}")
        print(f"시작 ID: {start_id}")
        
        # 현재 시간
        now = datetime.now()
        current_timestamp = now.isoformat()
        current_date = now.strftime('%y%m%d')
        
        print(f"현재 시간: {current_timestamp}")
        print(f"현재 날짜: {current_date}")
        
        # 기존 test 계정 개수 확인
        test_count = Woo.objects.filter(email__startswith='test').count()
        print(f"기존 test 계정: {test_count}개\n")
        
        # 5개 데이터 생성
        for i in range(5):
            new_id = start_id + i
            ones_digit = new_id % 10
            
            # 일의 자리가 0 또는 5인 경우 (마지막 데이터)
            if ones_digit == 0 or ones_digit == 5:
                email = 'whi21@naver.com'
                phone = '+821098714077'
            else:
                # test 계정 순차 증가
                test_count += 1
                email = f'test{test_count:05d}@gmail.com'
                phone = f'+8211{test_count:08d}'  # E.164 형식
            
            woo = Woo.objects.create(
                email=email,
                phone=phone,
                name=f'woo{new_id}',
                _id=f'woo{new_id}{current_date}',
                createdby=current_timestamp,
                modifiedby=current_timestamp,
                is_sent=False
            )
            
            print(f"✓ 생성: ID={woo.id}, name={woo.name}, _id={woo._id}")
            print(f"   email: {email}, phone: {phone}")
        
        print(f"\n총 5개 데이터 생성 완료")
        
        # 1분 대기
        wait_time = 60
        print(f'\n1분 대기 중...')
        
        start_time = time.time()
        while time.time() - start_time < wait_time:
            remaining = wait_time - (time.time() - start_time)
            mins, secs = divmod(int(remaining), 60)
            print(f'\r  남은 시간: {mins:02d}:{secs:02d}', end='', flush=True)
            time.sleep(1)
        
        print(f'\n1분 대기 완료!')
        
        # AEP로 전송
        print(f'\nAEP로 데이터 전송 중...')
        
        try:
            response = requests.post(
                'http://127.0.0.1:8000/api/batch/run/',
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ 전송 성공!")
                print(f"  Batch ID: {result.get('batch_id')}")
                print(f"  Total: {result.get('total_records')}")
                print(f"  Success: {result.get('success_count')}")
                print(f"  Failed: {result.get('fail_count')}")
            else:
                print(f"✗ 전송 실패: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"✗ 전송 에러: {e}")
        
        print("=" * 60)
        print("Daily Batch 완료")
        print("=" * 60)
