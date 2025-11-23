import os
import json
import csv
from queue import Queue
from apify_client import ApifyClient
from dotenv import load_dotenv
from datetime import datetime
import shutil

load_dotenv()


class ApifyScraper:
    def __init__(self):
        self.log_queue = Queue()
        self.client = ApifyClient(os.getenv("APIFY_API_TOKEN"))
    
    
    def scrape_single_post(self, post_url, top_n_vips):
        self.log(f"Scraping single post: {post_url}")
        usernames = self.get_profile_likes_Apify(post_url)
        vip_users = self.identify_VIPs(usernames, top_n_vips)
        return [[1, post_url] + vip_users]

    
    def scrape_profile_posts(self, username, number_of_posts, top_n_vips):
        self.log(f"Scraping profile posts for {username}")
        posts = self.get_profile_posts(username, number_of_posts)
        cleaned_posts = self.clean_post_data(posts, number_of_posts)
        vip_interested_profiles = []
        for i, post in enumerate(cleaned_posts):
            post_url = post.get('url')
            usernames = self.get_profile_likes_Apify(post_url)
            vip_users = self.identify_VIPs(usernames, top_n_vips)
            vip_interested_profiles.append([i+1, post_url] + vip_users)
        return vip_interested_profiles

    def log(self, message):
        timestamped_message = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        self.log_queue.put(timestamped_message)
        print(timestamped_message)


    def get_profile_posts(self, username, number_of_posts):
        self.log(f"Requesting {number_of_posts} posts for {username} (takes up to 2 minutes)")
        run_input = {
            "username": [
                username,
            ],
            "resultsLimit": number_of_posts + 2, # extra posts to compensate for duplicates
            #"onlyPostsNewerThan": None,
            #"skipPinnedPosts": None,
        }

        run = self.client.actor("nH2AHrwxeTRJoN5hX").call(run_input=run_input)

        posts = []
        for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
            posts.append(item)
        
        self.log(f"-> Found {len(posts)} posts (+2 to compensate for duplicates)")
        return posts


    def clean_post_data(self, posts, number_of_posts):
        self.log(f"Cleaning post data for {number_of_posts} posts")
        # remove duplicates
        unique_posts = {}
        for post in posts:
            url = post.get('url')
            if url and url not in unique_posts:
                unique_posts[url] = post
        unique_posts = list(unique_posts.values())

        # sort by timestamp
        unique_posts.sort(key=lambda x: x.get('timestamp'), reverse=True)

        self.log(f"-> Cleaned {len(unique_posts)} posts")
        return unique_posts[:number_of_posts]


    def get_profile_likes_Apify(self, post_url): # gets first 1000 likes
        self.log(f"Requesting likes for {post_url} (takes up to 5 minutes)")
        run_input = {
            "posts": [post_url],
            "max_count": 1_000,
        }
        run = self.client.actor("datadoping/instagram-likes-scraper").call(run_input=run_input)
        dataset = self.client.dataset(run["defaultDatasetId"])
        usernames = []
        for item in dataset.iterate_items():
            usernames.append(item.get('username'))
        self.log(f"-> Found {len(usernames)} users that liked the post")
        return usernames


    def identify_VIPs(self, usernames, top_n):
        self.log(f"Requesting follower counts and identifying VIPs for {len(usernames)} users")
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
        self.log(f"-> Data for {len(filtered_data)} users received")
        # identify top_n users with most likes #! assuming n <= like count
        sorted_data = sorted(
            (item for item in filtered_data if item['followersCount'] is not None),
            key=lambda x: x['followersCount'],
            reverse=True
        )
        top_users = sorted_data[:top_n]
        self.log(f"-> Identified {len(top_users)} VIPs")
        return top_users
    

    def create_csv(self, vip_interested_profiles):
        self.log(f"Creating CSV...")
        # Create CSV with the necessary headers
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = f'data/vip_profiles_{timestamp}.csv'
        with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write the header
            header = ['Post Number', 'Post URL', 'VIP Rank', 'Username', 'Followers Count', 'Location', 'Profile URL']
            writer.writerow(header)

            # Write data for each post
            for post in vip_interested_profiles:
                post_number = post[0]
                post_url = post[1]
                for vip_count, vip in enumerate(post[2:], start=1):
                    location = vip.get('location', 'N/A')
                    if location == None or location == '' or location == 'None':
                        location = 'N/A'
                    writer.writerow([
                        f'Post #{post_number}',
                        post_url,
                        f'VIP #{vip_count}',
                        vip.get('username'),
                        vip.get('followersCount', 'N/A'),
                        location,
                        vip.get('url')
                    ])

        shutil.copy(csv_path, 'data/last_scrape.csv')
        self.log(f"-> CSV ready to download")
        return csv_path


if __name__ == "__main__":
    scraper = ApifyScraper()
    vip_interested_profiles = scraper.scrape_profile_posts("bormannrene", 2, 3)
    scraper.create_csv(vip_interested_profiles)