import datetime
import schedule
import time

from src.newsletter import PyMail
from src.newsletter import make_final_contents
from config import Config

# G메일 계정 정보 초기화
c = Config()
address = c.GMAIL_ACCOUNT['address']
password = c.GMAIL_ACCOUNT['password']

# 뉴스 검색 키워드 정의
search_word_list = ['네이버','카카오','라인','쿠팡','배달의민족']

def send_mail_func():
    """
    컨텐츠 생성 및 이메일 발송 기능 호출 함수
    """
    # 컨텐츠 생성 (sort -> 0: "관련도순", 1: "최신순", 2: "오래된순")
    contents = make_final_contents(search_word_list, sort=0)
    # 타이틀 및 컨텐츠 작성
    date_str = datetime.datetime.strftime(datetime.datetime.now(),'%Y년 %m월 %d일')
    title = f"""📢 정우일 키워드 뉴스레터 ({date_str})"""
    contents=f'''{contents}'''
    # # 첨부파일 경로 설정
    # attachment_path = f"D:/Task.txt"
    # 수신자 정보 설정
    target_email_id = "wooil@kakao.com"
    # 문서 타입 설정 - plain, html 등
    subtype = 'html'
    # 세션 설정
    PM = PyMail(address, password)
    # 메일 발송
    PM.send_mail(target_email_id, title, contents, subtype)
    print("발송 완료")

# 스케줄 등록
schedule.every(1).minutes.do(send_mail_func)
# schedule.every().day.at("09:00").do(send_mail_func)
# schedule.every().day.at("18:00").do(send_mail_func)

while True:
    schedule.run_pending()
    time.sleep(1)