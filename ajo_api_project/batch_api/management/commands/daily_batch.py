import time
from datetime import datetime
from django.core.management.base import BaseCommand
from batch_api.models import Woo
import requests


class Command(BaseCommand):
    help = '매일 자동으로 새 데이터 5개 생성 후 AEP로 전송'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('Daily Batch 시작'))
        self.stdout.write('=' * 60)
        
        # 1. 마지막 ID 확인
        last_woo = Woo.objects.order_by('-id').first()
        start_id = (last_woo.id + 1) if last_woo else 1
        
        self.stdout.write(f'마지막 ID: {last_woo.id if last_woo else 0}')
        self.stdout.write(f'시작 ID: {start_id}')
        
        # 2. 현재 시간 및 날짜
        now = datetime.now()
        current_timestamp = now.isoformat()
        current_date = now.strftime('%y%m%d')  # yymmdd
        
        self.stdout.write(f'현재 시간: {current_timestamp}')
        self.stdout.write(f'현재 날짜: {current_date}')
        
        # 3. 새 데이터 5개 생성
        created_count = 0
        for i in range(5):
            new_id = start_id + i
            woo = Woo.objects.create(
                email='whi21@naver.com',
                phone='+821098714077',
                name=f'woo{new_id}',
                _id=f'woo{new_id}{current_date}',
                createdby=current_timestamp,
                modifiedby=current_timestamp
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'✓ 생성: ID={woo.id}, name={woo.name}, _id={woo._id}')
            )
        
        self.stdout.write(f'\n총 {created_count}개 데이터 생성 완료')
        
        # 4. 5분 대기
        self.stdout.write('\n5분 대기 중...')
        for remaining in range(300, 0, -30):
            mins, secs = divmod(remaining, 60)
            self.stdout.write(f'  남은 시간: {mins:02d}:{secs:02d}', ending='\r')
            time.sleep(30)
        
        self.stdout.write('\n\n5분 대기 완료!')
        
        # 5. API 호출하여 AEP로 전송
        self.stdout.write('\nAEP로 데이터 전송 중...')
        
        try:
            response = requests.post(
                'http://127.0.0.1:8000/api/batch/run/',
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                self.stdout.write(self.style.SUCCESS('\n✓ 전송 성공!'))
                self.stdout.write(f"  Batch ID: {result.get('batch_id')}")
                self.stdout.write(f"  Total: {result.get('total_records')}")
                self.stdout.write(f"  Success: {result.get('success_count')}")
                self.stdout.write(f"  Failed: {result.get('fail_count')}")
            else:
                self.stdout.write(
                    self.style.ERROR(f'\n✗ 전송 실패: {response.status_code}')
                )
                self.stdout.write(response.text)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ 에러: {str(e)}'))
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Daily Batch 완료'))
        self.stdout.write('=' * 60)
