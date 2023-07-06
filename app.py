from urllib.parse import urlparse
import streamlit as st
import subprocess
import sys
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from streamlit_extras.add_vertical_space import add_vertical_space
import time
import datetime
import threading
import pandas as pd
import plost
from backlinks_analysis import get_backlinks_df
from collections import Counter
from streamlit_extras.no_default_selectbox import selectbox
import re
from check_url import is_url
from delete_website_data import delete_data_in_batches
from urllib.parse import quote, unquote
import pycountry
import requests
import warnings
from bs4 import BeautifulSoup
warnings.filterwarnings("ignore", category=DeprecationWarning)

countries = list(pycountry.countries)
country_names = [country.name for country in countries]
def run_scrapy_script(url, page_amount):
    subprocess.run([sys.executable, 'scrapy_script.py', url, page_amount], env=os.environ.copy())

def get_dict_size(dictionary):
    # Calculate the size of the dictionary in bytes
    size_in_bytes = sys.getsizeof(dictionary)
    
    # Convert bytes to megabytes
    size_in_megabytes = size_in_bytes / (1024 * 1024)
    
    return size_in_megabytes

def format_url(url, filename_friendly = True):
    try:
        # Remove the "http://" or "https://" part
        domain = re.sub(r"https?://", "", url)
        
        # Remove any path or query parameters
        domain = re.sub(r"/.*", "", domain)
        
        if filename_friendly:
            # Replace dots with underscores
            domain = domain.replace(".", "_")
    except:
        domain = url
    return domain

def convert_float_time_to_text(float_time):
    # Create a datetime object using the current time
    datetime_obj = datetime.datetime.fromtimestamp(float_time)

    # Format the datetime object as a string in the desired format
    formatted_time = datetime_obj.strftime("%d %B %Y %H:%M:%S")  # Example format: 23 June 2023 15:30:45

    return formatted_time
    
def get_update_times(site_url, output_float = True):
    parsed_url = urlparse(site_url)
    subdomain = parsed_url.netloc.replace('.','_')
    update_times = db.reference(f'website_data/{subdomain}/update_times').get()
    if update_times:
        if output_float:
            past_update_times = [float(update_time.replace('_', '.')) for update_time in update_times]
        else:
            past_update_times = list(update_times)
    else:
        past_update_times = []
    return past_update_times

def get_data_df(site_url, time):
    parsed_url = urlparse(site_url)
    subdomain = parsed_url.netloc.replace('.','_')
    return pd.DataFrame(db.reference(f'website_data/{subdomain}/webpage_analysis/{str(time).replace(".", "_")}').get())

def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8-sig')

def map_range(value, input_min, input_max, output_min, output_max):
    # Map the value from the input range to the output range
    return ((value - input_min) / (input_max - input_min)) * (output_max - output_min) + output_min

def limit_range(value, minimum, maximum, mode='limit'):
    if mode == 'limit':
        # Limit the value within the minimum and maximum range
        return max(minimum, min(value, maximum))
    elif mode == 'wrap':
        # Wrap around the value if it exceeds the range
        range_size = maximum - minimum + 1
        return ((value - minimum) % range_size) + minimum
    else:
        raise ValueError("Invalid mode. Please choose 'limit' or 'wrap'.")

def format_data_from_SEO_request(text):
    if isinstance(text, list):
        return text[0]
    # Remove leading and trailing whitespace
    text = text.strip()

    # Find the URL using regular expression
    url_match = re.search(r"(?P<url>https?://[^\s]+)", text)

    if url_match:
        url = url_match.group("url")
        formatted_text = f"{url_match.string.split()[0]} → {url}"
        return formatted_text
    else:
        return text

def get_backlinks_analysis_dict(site_url, time):
    parsed_url = urlparse(site_url)
    subdomain = parsed_url.netloc.replace('.','_')
    retrived_data = db.reference(f'website_data/{subdomain}/backlinks_analysis/{str(time).replace(".", "_")}').get()
    if not retrived_data:
        return {'high quality backlinks': {}, 'new backlinks': {}, 'poor backlinks': {}}
    if 'high quality backlinks' not in retrived_data:
        retrived_data['high quality backlinks'] = {}
    if 'new backlinks' not in retrived_data:
        retrived_data['new backlinks'] = {}
    if 'poor backlinks' not in retrived_data:
        retrived_data['poor backlinks'] = {}
    
    # else:
    # print(retrived_data)
    return retrived_data
    
def get_keywords_count(site_url, time):
    parsed_url = urlparse(site_url)
    subdomain = parsed_url.netloc.replace('.','_')
    retrived_data = db.reference(f'website_data/{subdomain}/keywords_count/{str(time).replace(".", "_")}').get()
    return retrived_data

def get_web_vitals(site_url, time):
    parsed_url = urlparse(site_url)
    subdomain = parsed_url.netloc.replace('.','_')
    return db.reference(f'website_data/{subdomain}/web_core_vitals/{str(time).replace(".", "_")}').get()

def display_quality(value, must_less, not_more, inverse = False):
    if value > not_more:
        if not inverse:
            return ':red[มากเกินไป]'
        else:
            return ':red[น้อยเกินไป]'
    elif value >= must_less:
        return 'พอใช้'
    else:
        return ':green[ดี]'

def display_keyword_competition_df(keyword, url, location):
    current_time = datetime.datetime.now()
    future_time = current_time + datetime.timedelta(minutes=30)
    timestamp = int(future_time.timestamp())
    parsed_url = urlparse(url)
    formatted_url = parsed_url.netloc

    # print(location)
    if location:
        encoded_url = quote(url, safe='')
        location_aplha_2=str(pycountry.countries.get(name=location).alpha_2)
        competition_url = f"https://seo.esan.app/tools/competition?site={encoded_url}&exp={timestamp}"
        # print(competition_url)
        session = requests.Session()
        response = session.get(competition_url, allow_redirects=True)
        
        payload = {
            "keyword": keyword,
            "country": location_aplha_2
        }
        # Follow the redirection if it occurs
        if response.history:
            redirected_url = response.url
            response = session.post(redirected_url, data=payload)
        # st.markdown(response.content)
        soup = BeautifulSoup(response.content, "html.parser")
        # quote(keyword, safe='')
        
        tables = soup.find_all("table")
        # print(len(tables))
        tables_df_list = []
        
        for table in tables:
            headers = []
            for header in table.find_all("th"):
                headers.append(header.text.strip())
            # print(headers)
            data = []
            for row in table.find_all("tr"):
                row_data = []
                for cell in row.find_all("td"):
                    row_data.append(cell.text.strip())
                if row_data:
                    data.append(row_data)
            keyword_df = pd.DataFrame(data, columns=headers)
            keyword_df['Website'] = keyword_df['Website'].apply(lambda x : format_data_from_SEO_request(x))
            tables_df_list.append(keyword_df)
        if len(tables_df_list) == 1:
            websites_df = tables_df_list[0]
            masked_df = websites_df[websites_df['Website'].apply(lambda x:formatted_url in x)]
            tables_df_list.append(masked_df)
        # print(tables_df_list)
        # print(data)
        # competition_df = pd.DataFrame(data, columns=headers)
        # competition_df['Website'] = competition_df['Website'].apply(lambda x : format_data_from_SEO_request(x))
        st.subheader("เว็บไซต์ของคุณ", anchor=False)
        st.dataframe(tables_df_list[1], use_container_width = True, hide_index = True)
        st.divider()
        st.subheader("คู่แข่ง", anchor=False)
        st.dataframe(tables_df_list[0], use_container_width = True, hide_index = True)
        return tables_df_list
    else:
        st.error("You must select a specific country first.")

def show_data(site_url):
    if status_message_placeholder.button('เปลี่ยน website', type = 'primary'):
        st.session_state.clear()
        st.experimental_rerun()
    st.session_state['loaded_website'] = site_url
    past_update_times = get_update_times(site_url)
    formatted_past_update_times = []
    for time in past_update_times:
        formatted_past_update_times.append(convert_float_time_to_text(time))
    add_vertical_space(4)
    st.subheader(f'ข้อมูลของ {site_url}', anchor=False)
    selected_time_analyzation = past_update_times[formatted_past_update_times.index(st.selectbox('วิเคราะห์เมื่อ', list(reversed(formatted_past_update_times)), 0))]
    
    with st.spinner('กำลังโหลดข้อมูล'):
    
        if 'website_df' not in st.session_state:
            website_df = get_data_df(site_url, selected_time_analyzation)
            st.session_state['website_df'] = website_df
        else:
            website_df = st.session_state['website_df']
            
        if 'backlinks_analysis' not in st.session_state:
            backlinks_analysis = get_backlinks_analysis_dict(site_url, selected_time_analyzation)
            st.session_state['backlinks_analysis'] = backlinks_analysis
        else:
            backlinks_analysis = st.session_state['backlinks_analysis']
            
        if 'web_vitals' not in st.session_state:
            web_vitals = get_web_vitals(site_url, selected_time_analyzation)
            st.session_state['web_vitals'] = web_vitals
        else:
            web_vitals = st.session_state['web_vitals']
            
        warnings_df = website_df[['url', 'warnings']]
        downloaded_size = get_dict_size(warnings_df)
        count_no_warnings = warnings_df[warnings_df['warnings'].apply(lambda x: len(x) == 0)].shape[0]
        warnings_df.loc[:, 'warnings group'] = warnings_df['warnings'].apply(lambda x: [warning.split(':')[0] for warning in x])
        warnings_df.loc[:, 'warnings count'] = warnings_df['warnings'].apply(lambda x: len(x))
        total_website_errors = warnings_df['warnings count'].sum()
        keyword_counter = Counter()
        for keywords in website_df['keywords']:
            keyword_counter.update(Counter(keywords))
        keywords_df = pd.DataFrame.from_dict(keyword_counter, orient='index', columns=['Count']).sort_values('Count', ascending=False).reset_index(drop=False).rename(columns={'index': 'Keyword'})
    st.caption(f'ความจุของข้อมูล: {downloaded_size} MB')
    
    overview_tab, error_tab, backlinks_tab, keywords_tab, settings_tab = st.tabs(['Overview', 'Error', 'Backlinks', 'Keywords', 'Settings'])
    with overview_tab:
        add_vertical_space(2)
        st.header('SEO score ⭐', anchor=False)
        st.subheader(f'{round(web_vitals["score"]*100)}/100', anchor=False)
        st.caption(display_quality(1 - web_vitals['score'], 0.2, 0.7, True))
        add_vertical_space(2)
        st.subheader('Connections 🌎', anchor=False)
        add_vertical_space(2)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('**Error**')
            error_text_placeholder = st.empty()
            flatten_errors = [error for sublist in warnings_df['warnings group'] for error in sublist]
            error_counter = Counter(flatten_errors)
            select_error_analysis = selectbox('เลือก Error', error_counter.keys(), label_visibility='collapsed')
            error_text_placeholder.subheader(f'**{total_website_errors}**', anchor=False)
            if not select_error_analysis:
                error_text_placeholder.subheader(f'**{total_website_errors}**', anchor=False)
            else:
                error_text_placeholder.subheader(f"**{error_counter[select_error_analysis]}**", anchor=False)
        with col2:
            st.markdown('**Backlinks**')
            backlink_text_placeholder = st.empty()
            select_backlinks_analysis = st.selectbox('เลือก Backlinks', backlinks_analysis.keys(), label_visibility='collapsed')
            selected_backlinks_df = pd.DataFrame(backlinks_analysis[select_backlinks_analysis])
            backlink_text_placeholder.subheader(f'**{selected_backlinks_df.shape[0]}**', anchor=False)
            
        with col3:
            st.markdown('**Keywords**')
            keyword_text_placeholder = st.empty()
            select_keyword_analysis = selectbox('เลือก Keyword', keywords_df['Keyword'].to_list(), label_visibility='collapsed')
            if not select_keyword_analysis:
                keyword_text_placeholder.subheader(f"**{get_keywords_count(site_url, selected_time_analyzation)}**", anchor=False)
            else:
                filtered_df = keywords_df[keywords_df['Keyword'] == select_keyword_analysis]
                keyword_text_placeholder.subheader(f"**{filtered_df['Count'].values[0]}**", anchor=False)
        add_vertical_space(2)
        st.divider()
        add_vertical_space(2)
        st.image("https://tehnoblog.org/wp-content/uploads/2019/01/Google-Chrome-Lighthouse-Logo.png", width = 220)
        st.subheader('Google Lighthouse 🔎', anchor=False)
        add_vertical_space(2)
        col1, col2, col3 = st.columns(3)
            
        with col1:
            st.markdown('**First Contentful Paint**', help='First Contentful Paint หมายถึงเวลาที่ใช้ไปในการโหลดข้อความหรือรูปภาพรูปแรก')
            st.subheader(f"**{web_vitals['fcp']}** วินาที", anchor=False)
            st.caption(display_quality(web_vitals['fcp'], 1.8, 3))
            add_vertical_space(2)
            st.markdown('**Cumulative Layout Shift**', help='Cumulative Layout Shift วัดการเคลื่อนไหวขององค์ประกอบของหน้าเว็บ')
            st.subheader(f"**{web_vitals['cls']}**", anchor=False)
            st.caption(display_quality(web_vitals['cls'], 0.1, 0.25))
        with col2:
            st.markdown('**Largest Contentful Paint**', help='Largest Contentful Paint หมายถึงเวลาที่ใช้ไปในการโหลดข้อความหรือรูปภาพที่มีขนาดใหญ่ที่สุด')
            st.subheader(f"**{web_vitals['lcp']}** วินาที", anchor=False)
            st.caption(display_quality(web_vitals['lcp'], 2.5, 4))
            add_vertical_space(2)
            st.markdown('**Speed Index**', help='Speed Index แสดงให้เห็นว่าเนื้อหาของหน้าถูกโหลดอย่างรวดเร็วเพียงใด')
            st.subheader(f"**{web_vitals['si']}** วินาที", anchor=False)
            st.caption(display_quality(web_vitals['si'], 3.4, 5.8))
        with col3:
            st.markdown('**Time to Interactive**', help='Time to Interactive วัดเวลาที่ใช้ไปที่หน้าเว็บจะโต้ตอบได้อย่างสมบูรณ์')
            st.subheader(f"**{web_vitals['tti']}** วินาที", anchor=False)
            st.caption(display_quality(web_vitals['tti'], 3.9, 7.3))
            add_vertical_space(2)
            st.markdown('**Total Blocking Time**', help='Total Blocking Time คือผลรวมของช่วงเวลาทั้งหมดระหว่าง FCP และ Time to Interactive')
            st.subheader(f"**{web_vitals['tbt']}** มิลลิวินาที", anchor=False)
            st.caption(display_quality(web_vitals['tbt'], 200, 600))
    with error_tab:
        csv = convert_df(warnings_df[['url', 'warnings']])
        add_vertical_space(2)
        st.download_button(
            label="Download CSV :arrow_down:",
            data=csv,
            file_name=f'{format_url(site_url)}.csv',
            mime='text/csv',
        )
        st.subheader('Search for errors')
        filter_warnings = st.selectbox('', error_counter.keys(), label_visibility='collapsed')
        filtered_warnings_df = warnings_df[warnings_df['warnings group'].apply(lambda x:filter_warnings in x)]
        st.markdown(f'**พบ :red[{len(filtered_warnings_df)}] เพจที่มี error นี้**')
        st.dataframe(filtered_warnings_df[['url', 'warnings']], hide_index=True)
        
    with backlinks_tab:
        add_vertical_space(2)
        quality_backlinks, new_backlinks, poor_backlinks = st.tabs(['Backlinks คุณภาพ', 'Backlinks ใหม่', 'Backlinks ไม่ดี'])
        with quality_backlinks:
            if backlinks_analysis['high quality backlinks']:
                quality_backlinks_df = pd.DataFrame(backlinks_analysis['high quality backlinks'])
                quality_backlinks_df['Page title & location'] = quality_backlinks_df['Page title & location'].apply(lambda x:format_data_from_SEO_request(x))
                quality_backlinks_df['Anchor text & destination'] = quality_backlinks_df['Anchor text & destination'].apply(format_data_from_SEO_request)
                st.markdown(f'**พบ {len(quality_backlinks_df)} backlinks**')
                st.dataframe(quality_backlinks_df.reindex(columns=['Page title & location', 'Anchor text & destination', 'DA', 'PA', 'Found']), hide_index=True)
            else:
                st.info("ไม่มีข้อมูล")
        with new_backlinks:
            if backlinks_analysis['new backlinks']:
                new_backlinks_df = pd.DataFrame(backlinks_analysis['new backlinks'])
                new_backlinks_df['Page title & location'] = new_backlinks_df['Page title & location'].apply(format_data_from_SEO_request)
                new_backlinks_df['Anchor text & destination'] = new_backlinks_df['Anchor text & destination'].apply(format_data_from_SEO_request)
                st.markdown(f'**พบ {len(new_backlinks_df)} backlinks**')
                st.dataframe(new_backlinks_df.reindex(columns=['Page title & location', 'Anchor text & destination', 'DA', 'PA', 'Found']), hide_index=True)
            else:
                st.info("ไม่มีข้อมูล")
        with poor_backlinks:
            if backlinks_analysis['poor backlinks']:
                poor_backlinks_df = pd.DataFrame(backlinks_analysis['poor backlinks'])
                poor_backlinks_df['Page title & location'] = poor_backlinks_df['Page title & location'].apply(format_data_from_SEO_request)
                poor_backlinks_df['Anchor text & destination'] = poor_backlinks_df['Anchor text & destination'].apply(format_data_from_SEO_request)
                st.markdown(f'**พบ {len(poor_backlinks_df)} backlinks**')
                st.dataframe(poor_backlinks_df.reindex(columns=['Page title & location', 'Anchor text & destination', 'DA', 'PA', 'Found']), hide_index=True)
            else:
                st.info("ไม่มีข้อมูล")
    with keywords_tab:
        add_vertical_space(2)
        select_keyword_filter = selectbox('เลือก Keyword', keywords_df['Keyword'].to_list(), key='select keywords')
        location = st.selectbox('เลือกประเทศ', country_names, country_names.index('Thailand'))
        if not select_keyword_filter:
            st.info('โปรดเลือก Keyword')
            add_vertical_space(20)
        else:
            with st.spinner('กำลังโหลดข้อมูล'):
                display_keyword_competition_df(select_keyword_filter, site_url, location)
    
    with settings_tab:
        st.button('Delete all data', type = 'primary', on_click=delete_website_data)
        
        add_vertical_space(30)
    
def format_time(seconds):
    if seconds == 0:
        return f"Unknown"
    elif seconds < 60:
        return f"{seconds:.2f} วินาที"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} นาที"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} ชั่วโมง"
    else:
        days = seconds // 86400
        return f"{days} วัน"
    
if 'disable_inputs' not in st.session_state:
    st.session_state['disable_inputs'] = False
    
def disable_inputs():
    st.session_state['disable_inputs'] = True

def enable_inputs():
    st.session_state['disable_inputs'] = False
    
if 'loaded_website' not in st.session_state:
    st.session_state['loaded_website'] = ''

try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate("seo-luca-firebase.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://seo-luca-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })

st.header('SEO in one click!', anchor=False)
add_vertical_space(3)
site_url = st.text_input("Link เว็บไซต์ของคุณ", placeholder='http://www.example.com/', disabled=st.session_state['disable_inputs'])

def delete_website_data():
    delete_data_in_batches(site_url)
    st.session_state.clear()

with st.expander('ตั้งค่าเพิ่มเติม'):
    add_vertical_space(2)
    page_amount = st.slider('จำนวน page ของ website ที่ต้องการวิเคราะห์', 1, 100, 100, disabled=st.session_state['disable_inputs'])
    estimated_wait_time = 0.3 * int(page_amount) + 27
    st.caption(f'รอประมาณ {format_time(estimated_wait_time)}')
    add_vertical_space(2)

disable_analyze = True
past_update_times = []
status_message_placeholder = st.empty()
if site_url:
    if is_url(site_url):
        disable_analyze = False
        status_message_placeholder.success('👍 Link ถูกต้อง')
        past_update_times = get_update_times(site_url)
    else:
        status_message_placeholder.error('Link ไม่ถูกต้อง')
else:
    status_message_placeholder.info('โปรดใส่ Link เว็บไซต์ของคุณ')

st.caption('โหลดข้อมูลการวิเคราะห์ของ website ครั้งที่ผ่านมา')
load_existing_data = st.button('โหลดข้อมูล', key = 'load_existing_data', disabled= not past_update_times or st.session_state['disable_inputs'], on_click=disable_inputs)
st.caption('เริ่มวิเคราะห์ได้ครั้งละ 1 ชั่วโมงเท่านั้น')
start_analyze = st.button('เริ่มการวิเคราะห์ใหม่', key = 'start_analyze', type = 'primary', disabled=disable_analyze or st.session_state['disable_inputs'], on_click=disable_inputs)
if load_existing_data or st.session_state['loaded_website']:
    show_data(site_url)

if start_analyze:
    with st.spinner('กำลังวิเคราะห์ Website...'):
        start_time = time.time()
        progress_placeholder = st.empty()
        if page_amount!= 0:
            progress_placeholder.progress(0.0, text="")
        thread = threading.Thread(target=run_scrapy_script, args=(site_url, str(page_amount)))
        thread.start()
        while thread.is_alive():
            elapsed_time = time.time() - start_time
            if page_amount!= 0:
                progress_placeholder.progress(max(min(elapsed_time/estimated_wait_time, 0.95),0.0), text=f"โปรดรอซักครู่ ( เวลาใช้ไป : {format_time(elapsed_time)} )")
            time.sleep(0.1)  # Adjust the interval as needed
        if page_amount!= 0:
            progress_placeholder.progress(1.0 ,text="สำเร็จ!")
        thread.join()
    show_data(site_url)
    
