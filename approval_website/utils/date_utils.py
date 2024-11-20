# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import pytz

class DateUtils:
    @staticmethod
    def convert_to_local_time(datetime_str, timezone='Asia/Taipei'):
        """將UTC時間轉換為本地時間"""
        if not datetime_str:
            return False
            
        # 解析時間字串
        utc_dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        utc_dt = pytz.UTC.localize(utc_dt)
        
        # 轉換到本地時區
        local_tz = pytz.timezone(timezone)
        local_dt = utc_dt.astimezone(local_tz)
        
        return local_dt
    
    @staticmethod
    def convert_to_utc(date_str, time_str='00:00:00', timezone='Asia/Taipei'):
        """
        將日期字串和時間字串轉換為UTC的datetime物件
        
        Args:
            date_str: 日期字串 (YYYY-MM-DD)
            time_str: 時間字串 (HH:MM:SS)，默認為 '00:00:00'
            timezone: 時區字串，默認為 'Asia/Taipei'
            
        Returns:
            datetime: UTC timezone的datetime物件
        """
        if not date_str:
            return False
            
        local_tz = pytz.timezone(timezone)
        naive_datetime = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M:%S')
        local_datetime = local_tz.localize(naive_datetime)
        return local_datetime.astimezone(pytz.UTC).replace(tzinfo=None)

    @staticmethod
    def set_end_time(date_str, end_time='18:00:00', timezone='Asia/Taipei'):
        """設置結束時間為指定時間（預設18:00）"""
        if not date_str:
            return False
            
        # 合併日期和時間
        local_tz = pytz.timezone(timezone)
        local_dt = datetime.strptime(f"{date_str} {end_time}", '%Y-%m-%d %H:%M:%S')
        local_dt = local_tz.localize(local_dt)
        
        # 轉換為UTC
        utc_dt = local_dt.astimezone(pytz.UTC)
        return utc_dt.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def set_time_range(date_str, start_time='08:00:00', end_time='18:00:00'):
        """
        設置日期的時間範圍，支援自定義開始和結束時間

        Args:
            date_str: 日期字串 (YYYY-MM-DD)
            start_time: 開始時間字串 (HH:MM:SS)，默認 '08:00:00'
            end_time: 結束時間字串 (HH:MM:SS)，默認 '18:00:00'
            
        Returns:
            tuple: (start_datetime, end_datetime) naive datetime物件
        """
        if not date_str:
            return False, False
            
        # 創建本地時間
        local_tz = pytz.timezone('Asia/Taipei')
        
        # 解析開始時間
        start_naive = datetime.strptime(f"{date_str} {start_time}", '%Y-%m-%d %H:%M:%S')
        start_local = local_tz.localize(start_naive)
        start_utc = start_local.astimezone(pytz.UTC)
        
        # 解析結束時間
        end_naive = datetime.strptime(f"{date_str} {end_time}", '%Y-%m-%d %H:%M:%S')
        end_local = local_tz.localize(end_naive)
        end_utc = end_local.astimezone(pytz.UTC)
        
        # 返回不帶時區信息的 UTC 時間
        return start_utc.replace(tzinfo=None), end_utc.replace(tzinfo=None)
    @staticmethod
    def format_datetime(dt_value):
        """格式化datetime為顯示用字串"""
        if not dt_value:
            return ''
        return dt_value.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def get_work_time_range(date_str, work_time):
        """
        根據作業時段設置時間範圍
        
        Args:
            date_str: 日期字串 (YYYY-MM-DD)
            work_time: 作業時段 ('常日 08:00~18:00' 或 '夜間 18:00~07:00')
            
        Returns:
            tuple: (start_datetime, end_datetime) naive datetime物件
        """
        if not date_str:
            return False, False
            
        if work_time == '常日 08:00~18:00':
            start_dt = datetime.strptime(f"{date_str} 08:00:00", '%Y-%m-%d %H:%M:%S')
            end_dt = datetime.strptime(f"{date_str} 18:00:00", '%Y-%m-%d %H:%M:%S')
        else:  # 夜間 18:00~07:00
            start_dt = datetime.strptime(f"{date_str} 18:00:00", '%Y-%m-%d %H:%M:%S')
            next_day = (datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            end_dt = datetime.strptime(f"{next_day} 07:00:00", '%Y-%m-%d %H:%M:%S')
            
        return start_dt, end_dt

