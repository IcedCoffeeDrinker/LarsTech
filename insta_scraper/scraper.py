from playwright.sync_api import sync_playwright
from apify_client import ApifyClient
import asyncio
import random
import requests
import os
from dotenv import load_dotenv
import csv

load_dotenv()

class Scraper:
    def __init__(self):
        self.username = os.getenv("INSTA_USERNAME")
        self.password = os.getenv("INSTA_PASSWORD")
        self.client = ApifyClient(os.getenv("APIFY_API_TOKEN"))
    
    def setup_browser(self, playwright):
        self.chrome = playwright.chromium
        self.browser = self.chrome.launch(
            headless=False,
            args=[
                # Essential for servers without display
                '--no-sandbox',
                '--disable-setuid-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--single-process',  # Helps on limited resources
                '--disable-gpu',
                
                # Anti-detection measures
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"',
                
                # Window size to look more natural
                '--window-size=1920,1080',
            ]
        )
        self.context = self.browser.new_context(
            viewport={'width': 1920/2, 'height': 1080/2},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            # Add more realistic browser fingerprinting
            permissions=['geolocation'],
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # NYC coordinates
        )
        self.page = self.context.new_page()
        self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

    def run(self, username, number_of_posts, top_n_vips):
        with sync_playwright() as playwright:
            self.setup_browser(playwright)
            self.page.goto("https://www.instagram.com")
            self.page.wait_for_timeout(random.randint(1000, 2000))
            self.human_behaviour()
            self.accept_cookies()
            self.human_behaviour()
            self.login()
            self.human_behaviour()
            vip_interested_profiles = self.scrape_profile_posts(username, number_of_posts, top_n_vips)
            self.create_csv(vip_interested_profiles)
            self.page.screenshot(path="screenshot.png")
            self.page.wait_for_timeout(99999999)
            self.browser.close()

    def human_behaviour(self, page=None):
        if page is None:
            page = self.page
        for _ in range(random.randint(3, 7)):
            page.mouse.move(random.randint(100, 1800), random.randint(100, 900))
            page.wait_for_timeout(random.randint(100, 500))
        
        if random.random() < 0.6:
            page.evaluate(f"window.scrollTo(0, {random.randint(200, 600)});")
            page.wait_for_timeout(random.randint(500, 1500))

    def accept_cookies(self):
        self.page.wait_for_selector("text='Allow all cookies'", timeout=5000)
        button = self.page.locator("text='Allow all cookies'")
        if button.is_visible():
            self.page.wait_for_timeout(random.randint(500, 1000))
            self.click_human_like(button)
            print("Cookies accepted")
            return

    def type_human_like(self, locator, text):
        locator.click()
        self.page.wait_for_timeout(random.randint(200, 500))    
        for char in text:
            locator.type(char)
            delay = random.randint(100, 250)
            if random.random() < 0.1:
                delay += random.randint(300, 800)
            self.page.wait_for_timeout(delay)
        if random.random() < 0.15:
            self.page.wait_for_timeout(random.randint(500, 1000))
    
    def click_human_like(self, locator):
        self.page.wait_for_timeout(random.randint(200, 500))
        box = locator.bounding_box()
        if box:
            self.page.mouse.move(
                box['x'] + random.randint(-50, 50),
            box['y'] + random.randint(-30, 30)
            )
        self.page.wait_for_timeout(random.randint(300, 700))
        locator.click()
        
    def login(self):
        self.page.wait_for_timeout(random.randint(1000, 3000))
        selector = self.page.locator("input[name='username']")
        self.type_human_like(selector, self.username)
        self.page.wait_for_timeout(random.randint(1000, 3000))
        selector = self.page.locator("input[name='password']")
        self.type_human_like(selector, self.password)
        self.page.wait_for_timeout(random.randint(1000, 3000))
        selector = self.page.locator("button[type='submit']")
        self.click_human_like(selector)
        self.page.wait_for_timeout(random.randint(5000, 6000))
    
    def navigate_to_profile(self, username):
        self.page.wait_for_timeout(random.randint(1000, 3000))
        self.page.goto(f"https://www.instagram.com/{username}")

    def scrape_profile_posts(self, username, number_of_posts, top_n_vips):
        self.navigate_to_profile(username)
        self.page.wait_for_timeout(random.randint(1000, 3000))
        first_post_link = self.page.locator("a[href*='/p/']").first
        self.click_human_like(first_post_link)

        vip_interested_profiles = []
        
        for i in range(number_of_posts):
            try:
                liked_by_url = self.page.locator("a[href*='/liked_by/']")
                liked_by_users = self.get_profile_likes(liked_by_url)
                vip_users = self.fetch_user_info(liked_by_users, top_n_vips)
                vip_interested_profiles.append([i+1] + vip_users)
                self.open_next_post()
            except Error as e:
                print(e)
        return vip_interested_profiles

    def open_next_post(self):
        try:
            selector = self.page.locator("button[class='_abl-']")
            self.click_human_like(selector)
        except Error as e:
            print(e)
    
    def fetch_user_info(self, usernames, top_n):
        run_input = {
            "usernames": usernames,
            "includeAboutSection": False,
        }
        run = self.client.actor("dSCLg0C3YEZ83HzYX").call(run_input=run_input)
        dataset = self.client.dataset(run["defaultDatasetId"])
        filtered_data = []
        for item in dataset.iterate_items():
            filtered_item = {
                'url': item.get('url'),
                'followersCount': item.get('followersCount'),
                'location': item.get('locationName')  # might be None
            }
            filtered_data.append(filtered_item)
        # identify top_n users with most likes
        sorted_data = sorted(filtered_data, key=lambda x: x['followersCount'], reverse=True)
        top_users = sorted_data[:top_n]
        return top_users
    
    def create_csv(self, vip_interested_profiles):
        # Create CSV with the necessary headers
        with open('vip_profiles.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write the header
            header = ['Post Number', 'Username', 'Followers Count', 'Location', 'Profile URL']
            writer.writerow(header)

            # Write data for each post
            for post in vip_interested_profiles:
                post_number = post[0]
                for vip in post[1:]:
                    writer.writerow([
                        f'Post #{post_number}',
                        vip.get('username'),
                        vip.get('followersCount', 'N/A'),
                        vip.get('location', 'N/A'),
                        vip.get('url')
                    ])
        
    def get_profile_likes(self, url):
        liked_by_page = self.context.new_page()
        href = url.get_attribute("href")
        liked_by_page.goto(f"https://instagram.com{href}", timeout=20000)
        liked_by_page.wait_for_timeout(random.randint(1000, 3000))
        self.human_behaviour(liked_by_page)

        username_elements = liked_by_page.locator("._ap3a._aaco._aacw._aacx._aad7._aade")
        usernames = []
        count = username_elements.count()
        for i in range(count):
            element = username_elements.nth(i)
            username = element.inner_text().strip()
            if username:  # Only add non-empty usernames
                usernames.append(username)
        print(usernames)
        liked_by_page.wait_for_timeout(random.randint(1000, 3000))
        liked_by_page.close()
        return usernames

if __name__ == "__main__":
    scraper = Scraper()
    #username = input("Account to be scraped (username): ")
    #number_of_posts = int(input("Number of most recent posts to be scraped: "))
    #number_of_vips = int(input("Number of VIPs listed per post: "))
    #scraper.run(username, number_of_posts, number_of_vips)
    scraper.run("digitalartmuseum", 2, 3)