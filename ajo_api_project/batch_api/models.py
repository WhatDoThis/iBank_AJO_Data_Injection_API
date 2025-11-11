from django.db import models

class BatchLog(models.Model):
    """배치 실행 로그"""
    batch_id = models.CharField(max_length=100, unique=True)
    total_records = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    fail_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20)
    error_message = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'batch_log'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.batch_id} - {self.status}"


class Woo(models.Model):
    """테스트 데이터"""
    email = models.EmailField(max_length=255)
    phone = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    _id = models.CharField(max_length=100, db_column='_id')
    createdby = models.CharField(max_length=100)
    modifiedby = models.CharField(max_length=100)
    
    # 전송 여부 플래그 추가
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'woo'
    
    def __str__(self):
        return f"{self.name} ({self.email})"
