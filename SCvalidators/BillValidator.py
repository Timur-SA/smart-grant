import time
import requests
import base64
import re
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from config import NVIDIA_API_BILL

BASE_URL = "https://kkt-online.nalog.ru"
NVIDIA_API_KEY = NVIDIA_API_BILL

def extract_receipt_data_from_image(image):
    image_b64 = base64.b64encode(image.getvalue()).decode()

    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    
    
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "application/json"
    }

    payload = {
        "model": "meta/llama-4-maverick-17b-128e-instruct",
        "messages": [
            {
                "role": "user",
                "content": f"""Extract these data:
ФП
ФН
ФД
Дата
Время
Сумма

Create json in this format:

{{
    "type": "request",
    "fp": "ФП",
    "fn": "ФН",
    "fd": "ФД",
    "date": "Дата в формате 11.11.1111",
    "time": "Время",
    "operationtype": "1",
    "summ": "Сумма, разделитель - запятая"
}}

Некоторые значения статичны. Если значения не найдены, укажи нули во всех пунктах
<img src="data:image/png;base64,{image_b64}" />"""
            }
        ],
        "max_tokens": 512,
        "temperature": 1.00,
        "top_p": 1.00,
        "frequency_penalty": 0.00,
        "presence_penalty": 0.00,
        "stream": False
    }

    try:
        response = requests.post(invoke_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            receipt_data = json.loads(json_str)
            return receipt_data
        else:
            raise ValueError("JSON not found in API response")
            
    except Exception as e:
        print(f"Error extracting data from image: {e}")
        return None

def get_cookies_via_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-javascript")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--safebrowsing-disable-auto-update")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--dns-prefetch-disable")
    chrome_options.add_argument("--no-proxy-server")
    chrome_options.add_argument("--memory-efficient-offscreen")
    chrome_options.add_argument("--max-old-space-size=1024")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.set_capability("pageLoadStrategy", "eager")
    chrome_options.add_argument("--disable-application-cache")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.set_page_load_timeout(10)
        driver.set_script_timeout(5)
        
        driver.get(BASE_URL)
        
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception:
            pass
        
        cookies = driver.get_cookies()
        cookies_dict = {}
        for cookie in cookies:
            cookies_dict[cookie['name']] = cookie['value']

        driver.quit()
        return cookies_dict

    except Exception:
        try:
            cookies = driver.get_cookies()
            cookies_dict = {}
            for cookie in cookies:
                cookies_dict[cookie['name']] = cookie['value']
            driver.quit()
            return cookies_dict
        except:
            driver.quit()
            return {}

def get_cookies_via_browser_fast():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-javascript")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-extensions")
    
    prefs = {
        'profile.default_content_setting_values': {
            'images': 2,
            'plugins': 2,
            'popups': 2,
            'geolocation': 2,
            'notifications': 2,
            'auto_select_certificate': 2,
            'fullscreen': 2,
            'mouselock': 2,
            'mixed_script': 2,
            'media_stream': 2,
            'media_stream_mic': 2,
            'media_stream_camera': 2,
            'protocol_handlers': 2,
            'ppapi_broker': 2,
            'automatic_downloads': 2,
            'midi_sysex': 2,
            'push_messaging': 2,
            'ssl_cert_decisions': 2,
            'metro_switch_to_desktop': 2,
            'protected_media_identifier': 2,
            'app_banner': 2,
            'site_engagement': 2,
            'durable_storage': 2
        }
    }
    chrome_options.add_experimental_option('prefs', prefs)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.set_page_load_timeout(8)
        
        driver.execute_cdp_cmd('Network.setBlockedURLs', {
            "urls": [
                "*.gif", "*.jpg", "*.jpeg", "*.png", "*.webp",
                "*.css", "*.woff", "*.woff2", "*.ttf",
                "*.mp4", "*.avi", "*.mov",
                "*.mp3", "*.wav",
                "*.json", "*.xml"
            ]
        })
        driver.execute_cdp_cmd('Network.enable', {})
        
        driver.get(BASE_URL)
        time.sleep(2)
        
        cookies = driver.get_cookies()
        cookies_dict = {}
        for cookie in cookies:
            cookies_dict[cookie['name']] = cookie['value']
            
        driver.quit()
        return cookies_dict
        
    except Exception:
        try:
            cookies = driver.get_cookies()
            driver.quit()
            return {cookie['name']: cookie['value'] for cookie in cookies}
        except:
            if 'driver' in locals():
                driver.quit()
            return {}

def post_receipt(data, cookies):
    session = requests.Session()

    for name, value in cookies.items():
        session.cookies.set(name, value)

    headers = {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": BASE_URL,
        "referer": BASE_URL + "/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    post_url = BASE_URL + "/openapikkt.html"
    
    try:
        resp = session.post(post_url, data=data, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            try:
                js = resp.json()
                return js.get("success", False), js
            except:
                return False, {"error": "Invalid JSON response", "text": resp.text}
        else:
            return False, {"error": f"HTTP {resp.status_code}", "text": resp.text}
            
    except Exception as e:
        return False, {"error": str(e)}

def fetch_receipt(data):
    cookies = get_cookies_via_browser_fast()
    
    if not cookies:
        cookies = get_cookies_via_browser()
    
    if not cookies:
        return False, {"error": "Failed to get cookies"}
    
    success, details = post_receipt(data, cookies)
    return success, details

if __name__ == "__main__":
    image_path = "image.jpg"
    
    print("Extracting data from image...")
    start_extract = time.time()
    receipt_data = extract_receipt_data_from_image(image_path)
    end_extract = time.time()
    
    if not receipt_data:
        print("Failed to extract data from image")
        exit(1)
    
    print(f"Data extraction took: {end_extract - start_extract:.2f} seconds")
    print("Extracted data:", receipt_data)
    
    print("\nSending data to server...")
    start_fetch = time.time()
    success, details = fetch_receipt(receipt_data)
    end_fetch = time.time()
    
    print(f"Data sending took: {end_fetch - start_fetch:.2f} seconds")
    print("Success:", success)
    print("Details:", details)
    
    total_time = (end_extract - start_extract) + (end_fetch - start_fetch)
    print(f"\nTotal execution time: {total_time:.2f} seconds")