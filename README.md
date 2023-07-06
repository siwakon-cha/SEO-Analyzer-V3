# SEO-Analyzer-V3
- [x] Application Streamlit (Webpage เพื่อ access database)
- [ ] Flask application (API ในการ access database)

<br><br>
### Install ⭐
```
pip install -r requirements.txt
```
<br><br>

ใน repo นี้มี File อยู่ 3 File ที่สำคัญ
### 1. seo-luca-firebase.json ⚠️
File นี้มี credential ของ Firebase application เพื่อใช้ในการ access database<br>
ถ้าหากอยากใช้ credential Firebase ของคุณแทน ให้ save ทับ File นี้

<br><br>

### 2. app.py 🟢
File นี้เป็น File ของ Streamlit application สามารถรัน โดยใช้คำสั่ง
```
streamlit run app.py
```
หลังจาก run file นี้ จะมีหน้า webpage ที่ใช้ในการ access database และการ สั่งเก็บข้อมูล SEO ใหม่
<br><br>

ใน File นี้ มีส่วนสำคัญอยู่ดังนี้:
<br><br>
- Initialize Firebase 💾<br><br>
ใช้ในการ access database โดยใช้ credential และ url ของ database
```
try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate("seo-luca-firebase.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://seo-luca-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })
```
<br><br>
- Function run_scrapy_script<br><br>
เป็นการรัน python เพื่อให้ไปเก็บ data จาก website และข้อมูลเก็นใน database (ไม่ return ค่าใดๆ)
มี input 2 ค่า<br>
url - url ของ website ที่ต้องการ scrape เพื่อเก็บคะแนน SEO<br>
page_amount - จำนวน page ที่ต้องการ scrape (ไม่มี limit แต่ตัวเลขยิ่งเยอะก็ยิ่งใช้พื้นที่ในการเก็บ data ใน database มาก)<br>
```
def run_scrapy_script(url, page_amount):
    subprocess.run([sys.executable, 'scrapy_script.py', url, page_amount], env=os.environ.copy())
```
<br><br>
- access Firebase database
<br><br>access ข้อมูล SEO ใน database<br>
โดยจะใช้ 3 Function ดังต่อไปนี้:<br><br>
**get_data_df** - นำข้อมูล Keyword และ error ของ webpage มาจาก database (return เป็น dataframe)<br>
**get_backlinks_analysis_dict** - นำข้อมูล backlinks ของ webpage มาจาก database (return เป็น dict)<br>
**get_web_vitals** - นำข้อมูล web vitals (จาก Google) ของ webpage มาจาก database (return เป็น dict)<br>
```
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
```

<br><br>

### 3. scrapy_script.py 🟡
File ไว้สำหรับ scrape website เพื่อนำมาแปลงเป็นข้อมูล SEO และเก็บ data ใน database<br><br>
File นี้ สามารถรันจาก terminal ใดยใช้คำสั่ง (input: URL, page_amount)
```
scrapy_script.py www.example.com 100
```
เช่นเดียวกับ ใน app.py ใน file นี้มีการ initialize Firebase
```
cred = credentials.Certificate("seo-luca-firebase.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://seo-luca-default-rtdb.asia-southeast1.firebasedatabase.app/'
})
```
