from django.core.management.base import BaseCommand
from batch_api.models import BatchLog
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = '배치 실행 이력 조회'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='최근 N일 이력 조회 (기본: 7일)',
        )
        parser.add_argument(
            '--today',
            action='store_true',
            help='오늘 실행된 배치만 조회',
        )

    def handle(self, *args, **options):
        self.stdout.write('=' * 100)
        self.stdout.write(self.style.SUCCESS('배치 실행 이력'))
        self.stdout.write('=' * 100)
        
        if options['today']:
            from datetime import date
            logs = BatchLog.objects.filter(started_at__date=date.today())
            self.stdout.write(f"\n오늘 ({date.today()}) 실행된 배치\n")
        else:
            days = options['days']
            since = datetime.now() - timedelta(days=days)
            logs = BatchLog.objects.filter(started_at__gte=since)
            self.stdout.write(f"\n최근 {days}일 배치 이력\n")
        
        if logs.count() == 0:
            self.stdout.write(self.style.WARNING('실행된 배치가 없습니다.'))
            return
        
        # 헤더
        self.stdout.write(
            f"{'Batch ID':<20} "
            f"{'Status':<10} "
            f"{'Records':<8} "
            f"{'Success':<8} "
            f"{'Failed':<8} "
            f"{'Started At':<20}"
        )
        self.stdout.write('-' * 100)
        
        # 데이터
        for log in logs.order_by('-started_at'):
            started = log.started_at.strftime('%Y-%m-%d %H:%M:%S')
            
            # 상태별 색상
            if log.status == 'SUCCESS':
                status = self.style.SUCCESS(f"{log.status:<10}")
            elif log.status == 'FAILED':
                status = self.style.ERROR(f"{log.status:<10}")
            else:
                status = self.style.WARNING(f"{log.status:<10}")
            
            self.stdout.write(
                f"{log.batch_id:<20} "
                f"{status} "
                f"{log.total_records:<8} "
                f"{log.success_count:<8} "
                f"{log.fail_count:<8} "
                f"{started:<20}"
            )
            
            # 에러 메시지가 있으면 표시
            if log.error_message:
                self.stdout.write(
                    self.style.ERROR(f"  └─ Error: {log.error_message[:80]}...")
                )
        
        self.stdout.write('-' * 100)
        self.stdout.write(f"\n총 {logs.count()}개 배치 실행")
        
        # 통계
        success = logs.filter(status='SUCCESS').count()
        failed = logs.filter(status='FAILED').count()
        partial = logs.filter(status='PARTIAL').count()
        
        self.stdout.write(f"  성공: {success}, 실패: {failed}, 부분성공: {partial}\n")
