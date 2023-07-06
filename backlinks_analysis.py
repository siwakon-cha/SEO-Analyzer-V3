from urllib.parse import quote, unquote
import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def format_data_from_SEO_request(text):
    try:
        # Define the pattern to match the anchor text and link
        pattern = r"(.*?)\s+(https?://\S+)"

        # Find all matches in the text
        matches = re.findall(pattern, text)
            
        return unquote(matches[0][1])
    except IndexError:
        return [text, text, text]

def get_backlinks_df(url):
    # url = "https://www.thaiprintshop.com/"
    current_time = datetime.datetime.now()
    future_time = current_time + datetime.timedelta(minutes=30)
    timestamp = int(future_time.timestamp())
    encoded_url = quote(url, safe='')
    checks_urls = [f"https://seo.esan.app/tools/high-quality-backlinks?site={encoded_url}&exp={timestamp}", f"https://seo.esan.app/tools/new-backlinks?site={encoded_url}&exp={timestamp}", f"https://seo.esan.app/tools/poor-backlinks?site={encoded_url}&exp={timestamp}"]
    checks = ['high quality backlinks', 'new backlinks', 'poor backlinks']
    output_dataframes = []
    output_dict_data = {}

    for idex, url in enumerate(checks_urls):
        session = requests.Session()
        response = session.get(url, allow_redirects=True)

        # Follow the redirection if it occurs
        if response.history:
            redirected_url = response.url
            response = session.get(redirected_url)

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table", attrs={"id": "backlinks"})

        headers = []
        for header in table.find_all("th"):
            headers.append(header.text.strip())

        data = []
        for row in table.find_all("tr"):
            row_data = []
            for cell in row.find_all("td"):
                row_data.append(cell.text.strip())
            if row_data:
                data.append(row_data)
        try:
            df = pd.DataFrame(data, columns=headers)
            df['Page title & location'] = df['Page title & location'].apply(lambda x : format_data_from_SEO_request(x))
        except:            
            df = pd.DataFrame(columns=headers)
        df.drop('#', axis=1, inplace=True)
        output_dataframes.append(df)
        output_dict_data.update({checks[idex]: df.to_dict()})
    return output_dataframes, output_dict_data