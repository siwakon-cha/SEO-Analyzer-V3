import requests
import datetime
def webcorevitals(url_list,device = 'mobile',category = 'performance',today = None):
    if not today:
        today = datetime.date.today().strftime("%Y-%m-%d")
    result_list = []
    for url in url_list:
        # print(url)
        
           
        #making api call for URL
        response = requests.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url="+url+"&strategy="+device+"&category="+category)
        
        
        #saving response as json
        data = response.json()
        
        # print('Running URL #',url)
        
        test = url
        date = today
        
# =============================================================================
#         #Getting Metrics
#         
# =============================================================================
        
        try:   
            data = data['lighthouseResult']
        except KeyError:
            print('no Values')
            data = 'No Values.'
        pass
        #First Contentful Paint
        try:
            #First Contentful Paint
            fcp  = float(data['audits']['first-contentful-paint']['displayValue'].replace(',', '').replace('\xa0s', ''))
        except KeyError:
            print('no Values')
            fcp = 0
        pass
        
        #Largest Contentful Paint
        try:
             
            lcp = float(data['audits']['largest-contentful-paint']['displayValue'].replace(',', '').replace('\xa0s', ''))
        except KeyError:
            print('no Values')
            lcp = 0
        pass
        
        #Cumulative layout shift
        try:
            
            cls = float(data['audits']['cumulative-layout-shift']['displayValue'].replace(',', '').replace('\xa0s', ''))
        except KeyError:
            print('no Values')
            cls = 0
        pass
        
        try: 
            #Speed Index
            si = float(data['audits']['speed-index']['displayValue'].replace(',', '').replace('\xa0s', ''))
        except KeyError:
            print('no Values')
            si = 0
        pass
        try:
            
            #Time to Interactive
            tti = float(data['audits']['interactive']['displayValue'].replace(',', '').replace('\xa0s', ''))
        except KeyError:
            print('no Values')
            tti = 0
        try: 
            #Total Blocking Time
            tbt= float(data['audits']['total-blocking-time']['displayValue'].replace(',', '').replace('\xa0ms', ''))
        except KeyError:
            print('no Values')
            tbt = 0
        pass
        
        try:
            #score
            score = data['categories']['performance']['score']
        except KeyError:
            print('no Values')
        pass
            
        #list with all values
        values = [test, score,fcp,si,lcp,tti,tbt,cls,date]
        
        result_list.append(values)
        
    return result_list

# print(webcorevitals(['https://www.thaiprintshop.com/'])[0])