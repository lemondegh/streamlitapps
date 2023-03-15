import streamlit as st
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from urllib.parse import urlencode, unquote
import requests
import json
import math

from config import *

today = date.today()

# print(today)
today_str = str(today)
year = int(today_str.split('-')[0])
month = int(today_str.split('-')[1])
day = int(today_str.split('-')[2])
# print(year, month, day)

prev_month_today = today - relativedelta(months=1)
prev_month_today = str(prev_month_today)
# print(prev_month_today)
year_s = int(prev_month_today.split('-')[0])
month_s = int(prev_month_today.split('-')[1])
day_s = int(prev_month_today.split('-')[2])
# print(year, month, day)

ROWS = 20
date_option = ['공고일', '개찰일']
duration_option = ['From/To 지정', '최근 1개월', '최근 3개월']
work_option = ['전체', '물품', '공사', '용역', '리스', '외자', '비축', '기타', '민간']

org_option = ['공고기관', '수요기관']    
        
with st.form('기관 검색'):
    col1, col2 = st.columns([2, 8])
    with col1:
        org_str = st.selectbox('기관명', org_option)
    with col2:
        org_input = st.text_input('기관명 검색')

    col1, col2 = st.columns([9, 1])
    with col1:
        st.empty()
    with col2:
        search = st.form_submit_button("검색", use_container_width=True)
    
with st.form('Prompt'):
    col1, col2 = st.columns([2, 8])
    with col1:
        work_type_str = st.selectbox('업무구분', work_option)
    with col2:
        title = st.text_input('공고명 검색', placeholder='공고명에 포함되는 문자열') 

    col1, col2, col3, col4 = st.columns([2,2,2,4])
    with col1:
        date_type_str = st.selectbox('기준 일자 :', date_option)
    with col2:
        date_s = str(st.date_input('From', datetime.date(year_s, month_s, day_s))).replace('-', '')
    with col3:
        date_e = str(st.date_input('To', datetime.date(year, month, day))).replace('-', '')
    with col4:
        duration_str = st.selectbox('기간', duration_option, label_visibility='hidden')  

    disp_rows = st.number_input('샘플 미리보기 라인 수', min_value=1, max_value=10000, value=10)
    
    submitted = st.form_submit_button("검 색", use_container_width=True)
    
if submitted:
    error = False
    
    title_len = len(title.strip())
    if title_len == 0:
        st.warning('검색어가 입력되지 않았습니다.', icon="⚠️")
    else:
        url = 'https://apis.data.go.kr/1230000/BidPublicInfoService04/getBidPblancListEvaluationIndstrytyMfrcInfo01'
        url = URL + SERVICE
        
        if date_type_str == date_option[0]:
            date_type = 1
        else:
            date_type = 2
            
        queryString = "?" + urlencode(
            { 
            "ServiceKey": unquote(API_KEY), 
            "pageNo": 1,
            "numOfRows": ROWS,
            "inqryDiv": str(date_type),
            "inqryBgnDt":date_s + '0000',
            "inqryEndDt":date_e + '2359',
            "bidNtceNm": title,
            "type": "json"
            }
        )
        queryUrl = url + queryString
        print('Date type : ', date_type)
        print('Full URL : \n', queryUrl)
        
        response = requests.get(queryUrl)

        # json_str = response.read().decode("utf-8")
        try:
            r_dict = json.loads(response.text)
        except:
            print('Error : \n', response.text)
            
            
        # json_object = json.loads(json_str)

        print(r_dict)

        import pandas as pd
        from pandas.io.json import json_normalize

        # body = [json_object['body']['data']]
        print('Data ================================')
        # count = r_dict['totalCount']
        count = r_dict['response']['body']['totalCount']
        print('Count : ', count)
        
        if count == 0:
            st.info('검색 조건에 해당하는 데이터가 검색되지 않습니다.', icon='❗')
        loopCount = math.ceil(count / ROWS)
        print('Loop count : ', loopCount)
        
        finalTotalData = pd.DataFrame()
        for ind in range(loopCount):
                queryString = "?" + urlencode(
                    { 
                    "ServiceKey": unquote(API_KEY), 
                    "pageNo": 1,
                    "numOfRows": ROWS,
                    "inqryDiv": str(date_type),
                    "inqryBgnDt":date_s + '0000',
                    "inqryEndDt":date_e + '2359',
                    "bidNtceNm": title,
                    "type": "json"
                    }
                )

                queryURL = url + queryString
                response = requests.get(queryURL)
                r_dict = json.loads(response.text)
                
                # data = r_dict['data']
                data = r_dict['response']['body']['items']

                jnormal = json_normalize(data)
                # print(jnormal)
                finalTotalData = pd.concat([finalTotalData, pd.DataFrame(jnormal)], axis = 0, ignore_index = True)

        print(finalTotalData)
        # finalTotalData.rename(columns={'bidNtceNo':'NO'}, inplace=True)
        finalTotalData.to_csv('result_tmp.csv', encoding='utf-8-sig', index=False)

        import pandas as pd

        # Load the original DataFrame
        df = pd.read_csv('result_tmp.csv')

        # Load the mapping file
        mapping = pd.read_csv("col_map.csv", index_col="org")

        # Create a dictionary mapping the old column names to the new ones
        new_names = mapping["new"].to_dict()

        # Rename the columns using the dictionary
        df = df.rename(columns=new_names)

        # Save the renamed DataFrame
        # df.to_csv(r'.\Result\result.csv', index=False, encoding='utf-8-sig')
        print(df)
        len = len(df)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text('Total rows :' + str(len))
        with col2:
            file = title + '_' + date_e + '.csv'
            file_name = st.text_input('File name', file, label_visibility="collapsed")
        with col3:
            csv = df.to_csv().encode('utf-8-sig')
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=file_name,
                mime='text/csv',
            )   
            
        st.dataframe(df.head(disp_rows))        