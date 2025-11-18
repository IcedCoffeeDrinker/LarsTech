import os
import csv
import random
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError
from apify_client import ApifyClient
from queue import Queue

load_dotenv()

class Scraper:
    def __init__(self):
        self.log_queue = Queue()
        # initialize credentials
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        self.client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

        # initialize playwright
        self.log("Initializing Scraper...")
        self.playwright = sync_playwright().start()
        self.setup_browser(self.playwright)
        self.page.goto("https://www.instagram.com")
        self.accept_cookies()
        self.login()
        self.log("Scraper initialized")
    

    ### Humanification Helper Functions ###

    def human_behaviour(self, page=None):
        if page is None:
            page = self.page
        for _ in range(random.randint(3, 7)):
            page.mouse.move(random.randint(100, 1800), random.randint(100, 900))
            page.wait_for_timeout(random.randint(100, 500))
        if random.random() < 0.6:
            page.evaluate(f"window.scrollTo(0, {random.randint(200, 600)});")
            page.wait_for_timeout(random.randint(500, 1500))


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

    
    def type_human_like(self, locator, text):
        self.click_human_like(locator)
        self.page.wait_for_timeout(random.randint(200, 500))    
        for char in text:
            locator.type(char)
            delay = random.randint(100, 250)
            if random.random() < 0.1:
                delay += random.randint(300, 800)
            self.page.wait_for_timeout(delay)
        if random.random() < 0.15:
            self.page.wait_for_timeout(random.randint(500, 1000))


    def sleep(self, page=None):
        if page is None: 
            page = self.page
        page.wait_for_timeout(random.randint(1000, 3000))

    
    ### Initialization Helpers ###

    def setup_browser(self, playwright):
        """Initizes a browser that is difficult to detect by Instagram's anti-bot measures.
        Additionally creates the main navigation page."""
        self.chrome = playwright.chromium
        self.browser = self.chrome.launch(
            headless=False, # set to True for deployment
            # anti bot-detection measures
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--single-process',  
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"',
                '--window-size=1920,1080',
            ]
        )
        # anti-bot fingerprinting
        self.context = self.browser.new_context(
            viewport={'width': 1920/2, 'height': 1080/2},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # NYC coordinates
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(120000)
        self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")


    def accept_cookies(self):
        self.page.wait_for_load_state('load')
        self.log("Page loaded")
        try:
            self.page.wait_for_selector("text='Allow all cookies'", timeout=random.randint(700, 1300))
        except TimeoutError:
            self.log("Cookies button does not exist")
            return
        button = self.page.locator("text='Allow all cookies'")
        if button.is_visible():
            self.page.wait_for_timeout(random.randint(500, 1000))
            self.click_human_like(button)
            self.log("Cookies accepted")


    def login(self):
        self.sleep()
        try:
            selector = self.page.locator("input[name='username']")
        except TimeoutError:
            selector = self.page.locator("input[name='email']")
        self.type_human_like(selector, self.username)

        self.sleep()
        selector = self.page.locator("input[name='password']")
        self.type_human_like(selector, self.password)

        self.sleep()
        selector = self.page.locator("button[type='submit']")
        self.click_human_like(selector)
        
        self.page.wait_for_selector("div[class='x1n2onr6']")
        self.log("Logged in successfully")
    

    ### scraping tooling ###

    def navigate_to_profile(self, username):
        self.sleep()
        self.page.goto(f"https://www.instagram.com/{username}")

    
    def navigate_to_post(self, post_link):
        self.sleep()
        self.page.goto(post_link)
    

    def get_profile_likes(self, post_url):
        # create second page listing all accounts that liked
        liked_by_page = self.context.new_page()
        liked_by_page.goto(f"{post_url}liked_by/")

        self.human_behaviour(liked_by_page)
        self.sleep(liked_by_page)
        
        usernames = []
        while True:
            username_elements = liked_by_page.locator("._ap3a._aaco._aacw._aacx._aad7._aade")
            count = username_elements.count()
            new_usernames = []

            for i in range(count):
                element = username_elements.nth(i)
                username = element.inner_text().strip()
                if username and username not in usernames:  # Avoid duplicates
                    new_usernames.append(username)

            if not new_usernames:
                break  # Exit loop if no new usernames are found

            usernames.extend(new_usernames)
            self.log(f"Found {len(new_usernames)} new usernames")
            liked_by_page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        self.log(f"Found {len(usernames)} usernames in total")
        return usernames


    def get_profile_likes_Apify(self, post_url): # only for <1000 likes
        run_input = {
            "posts": [post_url],
            #"resultsType": "likes",  # This handles pagination automatically
            "max_count": 1_000,
        }
        run = self.client.actor("datadoping/instagram-likes-scraper").call(run_input=run_input)
        dataset = self.client.dataset(run["defaultDatasetId"])
        usernames = []
        for item in dataset.iterate_items():
            usernames.append(item.get('username'))
        self.log(f"Found {len(usernames)} usernames in total")
        return usernames


    def open_next_post(self):
            try:
                selector = self.page.locator("button[class='_abl-']").filter(has_text="Next")
                self.click_human_like(selector)
                self.log("next post selected")
            except Exception as e:
                self.log(e)
    

    def identify_VIPs(self, usernames, top_n):
        run_input = {
            "usernames": usernames,
            "includeAboutSection": False,
        }
        run = self.client.actor("dSCLg0C3YEZ83HzYX").call(run_input=run_input)
        dataset = self.client.dataset(run["defaultDatasetId"])
        filtered_data = []

        for item in dataset.iterate_items():
            url = item.get('url')
            username = url.rstrip('/').split('/')[-1] if url else None
            filtered_item = {
                'url': url,
                'username': username,
                'followersCount': item.get('followersCount'),
                'location': item.get('locationName')  # might be None
            }
            filtered_data.append(filtered_item)

        # identify top_n users with most likes #! assuming n <= like count
        sorted_data = sorted(
            (item for item in filtered_data if item['followersCount'] is not None),
            key=lambda x: x['followersCount'],
            reverse=True
        )
        top_users = sorted_data[:top_n]
        self.log(f"Identified {len(top_users)} VIPs")
        return top_users


    ### Main Scraping Function ###

    def scrape_profile_posts(self, username, number_of_posts, top_n_vips):
        # navigate to profile
        self.navigate_to_profile(username)
        self.sleep()

        # navigate to most recent post
        self.page.wait_for_selector("a[href*='/p/']")
        first_post_link = self.page.locator("a[href*='/p/']").first
        self.click_human_like(first_post_link)

        vip_interested_profiles = []
        
        for i in range(number_of_posts):
            try:
                # fetch people who liked the post
                self.sleep()
                post_url = self.page.url
                liked_by_users = self.get_profile_likes(post_url)

                # extract users with most followers
                vip_users = self.identify_VIPs(liked_by_users, top_n_vips)
                vip_interested_profiles.append([i+1] + vip_users)
                self.log(liked_by_users)
                # move to the next less-recent post 
                self.open_next_post()
            except Exception as e:
                self.log(e)
        return vip_interested_profiles

    def scrape_single_post(self, post_link, top_n_vips):
        liked_by_users = self.get_profile_likes_Apify(post_link)
        vip_users = self.identify_VIPs(liked_by_users, top_n_vips)
        return [[1] + vip_users]

    
    ### Post-Processing ###

    def create_csv(self, vip_interested_profiles):
        # Create CSV with the necessary headers
        with open('vip_profiles.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write the header
            header = ['Post Number', 'VIP Rank', 'Username', 'Followers Count', 'Location', 'Profile URL']
            writer.writerow(header)

            # Write data for each post
            for post in vip_interested_profiles:
                post_number = post[0]
                vip_count = 1
                for vip in post[1:]:
                    location = vip.get('location', 'N/A')
                    if location == None or location == '' or location == 'None':
                        location = 'N/A'
                    writer.writerow([
                        f'Post #{post_number}',
                        f'VIP #{vip_count}',
                        vip.get('username'),
                        vip.get('followersCount', 'N/A'),
                        location,
                        vip.get('url')
                    ])
                    vip_count += 1


    ### Logging ###
    def log(self, message):
        self.log_queue.put(message)
        print(message)
       
    ### Clean-Up ###

    def shutdown(self):
        #self.page.wait_for_timeout(99999999)
        self.browser.close()
        self.playwright.stop()




def get_input():
    username = input("Account to be scraped (username): ")
    number_of_posts = int(input("Number of most recent posts to be scraped: "))
    number_of_vips = int(input("Number of VIPs listed per post: "))
    return username, number_of_posts, number_of_vips

if __name__ == "__main__":
    scraper = Scraper()
    try:
        #username, number_of_posts, number_of_vips = get_input()
        #scraper.scrape(username, number_of_posts, number_of_vips)
        data = scraper.scrape("bormannrene", 2, 3)
        scraper.create_csv(data)
        scraper.shutdown()
    except TimeoutError:
        scraper.log("TimeoutError: Bad internet connection")