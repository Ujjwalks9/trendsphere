from flask import Flask, render_template, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from zoneinfo import ZoneInfo
from pymongo import MongoClient
import uuid
import datetime
import time
import random
import requests

# Configuration
MONGO_URI = "mongodb://localhost:27017/"
# PROXY_URL = "http://Ujjwalks9:Anjudk92@proxy.proxymesh.com:31280"  # Replace with your ProxyMesh credentials
SCRAPERAPI_KEY = "b0a43224a1f8eb33cc78790586d0ba95"
CHROME_DRIVER_PATH = r"C:\Drivers\chromedriver.exe"  # Update with the correct path

# Initialize Flask App
app = Flask(__name__, template_folder="templates", static_folder="static")

# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client.get_database("stir_tech")
collection = db["trending_topics"]

# Helper Function to Get External IP Address
def get_ip_address():
    """Fetches the external IP address using an API."""
    try:
        response = requests.get("https://api.ipify.org?format=json")
        return response.json().get("ip")
    except Exception as e:
        print(f"Error fetching IP address: {e}")
        return None



def login_to_twitter(driver):
    """Log in to Twitter using Selenium."""
    try:
        # Wait for the username field to appear
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="text"]'))
        )
        username_field.send_keys("Ujjwalks9")

        # Click the "Next" button if required
        # next_button = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="LoginForm_Login_Button"]')
        # next_button.click()
        next_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//button[.//span[text()="Next"]]'))
        )
        next_button.click()

        # Wait for the password field to appear
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
        )
        password_field.send_keys("Anjudk92")

        # Click the login button
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="LoginForm_Login_Button"]'))
        )
        login_button.click()

    except Exception as e:
        print(f"Error during login: {e}")
        driver.save_screenshot("login_error.png")
        with open("login_error_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        raise

    # Wait for the "Trending now" section
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Timeline: Trending now"]'))
        )
    except Exception as e:
        print(f"Error locating 'Trending now': {e}")
        driver.save_screenshot("trending_error.png")
        with open("trending_error_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        raise



def scrape_trending_topics():
    """Scrapes the top 5 trending topics from Twitter."""
    # Selenium WebDriver with Proxy
    # Generate a random session ID for ScraperAPI to force IP rotation
    # session_id = str(random.randint(1, 100000))
    SCRAPERAPI_PROXY_URL = f"http://scraperapi.proxy/api_key={SCRAPERAPI_KEY}&render=true&session={random.randint(1, 100000)}"
    # SCRAPERAPI_PROXY_URL = f"http://scraperapi.proxy/api_key={SCRAPERAPI_KEY}&render=true"
    options = webdriver.ChromeOptions()
    # options.add_argument(f"--proxy-server={PROXY_URL}")
    options.add_argument(f"--proxy-server={SCRAPERAPI_PROXY_URL}")
    options.add_argument("--headless")  # Run browser in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Access Twitter
        driver.get("https://twitter.com/login")
        time.sleep(5)  

       
        login_to_twitter(driver)

        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Timeline: Trending now"]'))
        )

        # trends_section = driver.find_elements(By.CSS_SELECTOR, '[aria-label="Timeline: Trending now"] span:not([aria-hidden="true"])') 
        # top_trends = [] 
        # for trend in trends_section: 
        #     trend_text = trend.text.strip() 
        #     # Filter out trends and their associated post counts 
        #     if trend_text and "posts" not in trend_text and "Trending" not in trend_text and trend_text != "Show more": 
        #         top_trends.append(trend_text) 

        # top_trends = list(dict.fromkeys(top_trends))[:5]

        # Retry logic to ensure valid trending topics are retrieved 
        for _ in range(3): # Retry up to 3 times # Change 1 
            trends_section = driver.find_elements(By.CSS_SELECTOR, '[aria-label="Timeline: Trending now"] span:not([aria-hidden="true"])') 
            top_trends = [trend.text.strip() for trend in trends_section if trend.text.strip() and "posts" not in trend.text and "Trending" not in trend.text and trend.text != "Show more"] 
            if "What\'s happening" not in top_trends: 
                break 
            time.sleep(2) # Wait before retrying 

        top_trends = top_trends[:5]
        print("Top Trends:", top_trends)

        # Generate unique ID and timezone-aware timestamp
        unique_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        # timestamp = datetime.datetime.now(datetime.timezone.utc).astimezone(ZoneInfo("Asia/Kolkata"))

        # Get external IP address
        ip_address = get_ip_address()
        print(f"IP Address Used: {ip_address}")


        #Prepare and store data in MongoDB
        # data = {
        #     "_id": unique_id,
        #     "trends": top_trends,
        #     "timestamp": timestamp,
        #     "ip_address": ip_address,
        # }
        data = {
            "_id": unique_id,
            "trend1": top_trends[0] if len(top_trends) > 0 else None,
            "trend2": top_trends[1] if len(top_trends) > 1 else None,
            "trend3": top_trends[2] if len(top_trends) > 2 else None,
            "trend4": top_trends[3] if len(top_trends) > 3 else None,
            "trend5": top_trends[4] if len(top_trends) > 4 else None,
            "timestamp": timestamp,
            "ip_address": ip_address,
        }
        collection.insert_one(data)
        return data

    finally:
        driver.quit()

# Flask Routes
@app.route("/")
def home():
    """Renders the main HTML page."""
    return render_template("index.html")

@app.route("/run-script", methods=["POST"])
def run_script():
    """Runs the scraper and returns the data."""
    try:
        data = scrape_trending_topics()
        return jsonify(data)
    except Exception as e:
        print(f"Error running script: {e}")
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
