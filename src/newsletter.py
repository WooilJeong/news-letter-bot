import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta
import codecs
import logging

import requests
from bs4 import BeautifulSoup
from pretty_html_table import build_table


class PyMail:
    """
    Python Email 전송 클래스
    """
    
    def __init__(self, my_email_id, my_email_pw):
        """
        G메일 계정, SMTP 정보 및 세션 초기화
        """
        # 계정 정보 초기화
        self.my_email_id = my_email_id
        self.my_email_pw = my_email_pw
        # G메일 SMTP 호스트, 포트 정보 초기화
        self.smtp_host = 'smtp.gmail.com'
        self.smtp_port = 587
        # 세션 정의
        self.session = smtplib.SMTP(self.smtp_host, self.smtp_port)

    
    def send_mail(self, target_email_id, title, contents, subtype=None, attachment_path=None):
        """
        이메일 전송 메서드
        - 수신자 이메일, 제목, 내용, 문서타입, 첨부 파일 경로
        """
        # 세션 보안 TLS 시작
        self.session.starttls()
        # 세션 계정 로그인
        self.session.login(self.my_email_id, self.my_email_pw)
        # 제목, 본문 작성
        msg = MIMEMultipart()
        msg['Subject'] = title
        if not subtype:
            msg.attach(MIMEText(contents, 'plain'))
        else:
            msg.attach(MIMEText(contents, subtype))
        # 파일첨부 (파일 미첨부시 생략가능)
        if attachment_path:
            fileName = attachment_path.split("/")[-1]
            attachment = open(attachment_path, 'rb')
            part = MIMEBase('application', 'octet-stream')
            part.set_payload((attachment).read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= " + fileName)
            msg.attach(part)
        # 메일 전송
        try:
            self.session.sendmail(self.my_email_id, target_email_id, msg.as_string())
            self.session.quit()
        except:
            self.session.quit()

def df_to_html_table(df, index=False):
    """
    Pandas DataFrame을 HTML 테이블 태그로 변환
    """
    return build_table(df, 'blue_light')

def make_contents(search_word_list, sort):
    """
    컨텐츠 생성 함수
    """
    df = pd.DataFrame()
    for search_word in search_word_list:

        # 해당 url의 html문서를 soup 객체로 저장
        url = f'https://m.search.naver.com/search.naver?where=m_news&sm=mtb_jum&query={search_word}&sort={sort}'

        req = requests.get(url)
        html = req.text
        soup = BeautifulSoup(html, 'html.parser')

        search_result = soup.select_one('#news_result_list')
        news_links = search_result.select('.bx > .news_wrap > a')
        times = search_result.select("#news_result_list > li > div > div.news_info > div.info_group > span:nth-child(2)")
        source = search_result.select("#news_result_list > li > div.news_wrap > div.news_info > div.info_group > a")

        title_list = list(map(lambda x: x.text, news_links))
        link_list = list(map(lambda x: x.attrs['href'], news_links))
        times_list = list(map(lambda x: x.text, times))
        source_list = list(map(lambda x: x.text, source))
        source_link_list = list(map(lambda x: x.attrs['href'], source))

        tmp = pd.DataFrame({"Title": title_list, "Times": times_list, "Source": source_list, "Link": link_list, "SourceLink": source_link_list})
        tmp['Keyword'] = search_word

        df = df.append(tmp.head(3))

    df = df[['Keyword', 'Title', 'Times', 'Source', 'Link', 'SourceLink']]
    df.index = range(len(df))
    
    return df

def preprocessing(df):
    """
    전처리 함수
    """
    new_title_list = []
    new_source_list = []
    for idx, row in df.iterrows():
        title = row['Title']
        link = row['Link']

        source = row['Source']
        source_link = row['SourceLink']

        new_title = f"""<a href="{link}">{title}</a>"""
        new_source = f"""<a href="{source_link}">{source}</a>"""

        new_title_list.append(new_title)
        new_source_list.append(new_source)

    df['Title_Link'] = new_title_list
    df['Source_Link'] = new_source_list

    # 시점 계산
    now = datetime.datetime.now()
    df.loc[df['Times'].str.contains("일 전"), 'Times_'] = df.loc[df['Times'].str.contains("일 전")]['Times'].apply(lambda x: now-relativedelta(days=int(x.split("일")[0])))
    df.loc[df['Times'].str.contains("시간 전"), 'Times_'] = df.loc[df['Times'].str.contains("시간 전")]['Times'].apply(lambda x: now-relativedelta(hours=int(x.split("시간")[0])))
    df.loc[df['Times'].str.contains("분 전"), 'Times_'] = df.loc[df['Times'].str.contains("분 전")]['Times'].apply(lambda x: now-relativedelta(minutes=int(x.split("분")[0])))
    df.loc[df['Times'].str.contains("\."), 'Times_'] = df.loc[df['Times'].str.contains("\.")]['Times'].apply(lambda x: datetime.datetime.strptime(x, "%Y.%m.%d."))
    df['Times_'] = pd.to_datetime(df['Times_']).apply(lambda x: datetime.datetime.strftime(x, "%Y-%m-%d"))

    # 결과
    df_cls = df[['Keyword','Title_Link','Times_','Source_Link']]
    colDict = {"Keyword": "주제",
               "Title_Link": "제목",
               "Times_": "날짜",
               "Source_Link": "채널"}
    df_cls = df_cls.rename(columns=colDict)
    return df_cls


def merge_with_html_template(contents, sort):
    """
    HTML 뉴스레터 템플릿 적용
    """
    sort_dict = {0: "관련도순", 1: "최신순", 2: "오래된순"}
    sort_selected = sort_dict[sort]
    f=codecs.open("./template/newsletter.html", 'r', 'utf-8')
    html = f.read().format(sort_selected=sort_selected, contents=contents)
    return html


def make_final_contents(search_word_list, sort=1):
    """
    컨텐츠 만들기
    sort: 정렬 기준 - 0: 관련도순, 1: 최신순, 2: 오래된순
    """
    # 컨텐츠 생성
    df = make_contents(search_word_list, sort)
    # 전처리
    df_cls = preprocessing(df)
    # HTML로 변환하기
    html = df_to_html_table(df_cls)
    # HTML Contents
    contents_ = html.replace("&lt;","<").replace("&gt;",">")
    # 뉴스레터 HTML 템플릿 적용
    contents = merge_with_html_template(contents_, sort)
    return contents


