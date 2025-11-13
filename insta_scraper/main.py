from scraper import Scraper
from playwright.sync_api import TimeoutError

### Initialize Scraper ###
scraper = Scraper()

### CLI ###
while True:
    try:
        print("Type Ctrl+C to exit")
        scraper_mode = input("Do you want to scrape a profile or a single post? (profile/post): ")
        if scraper_mode == "profile":
            username = input("Enter the username of the profile to scrape: ")
            number_of_posts = int(input("Enter the number of posts to scrape: "))
            number_of_vips = int(input("Enter the number of VIPs to scrape: "))
            data = scraper.scrape_profile_posts(username, number_of_posts, number_of_vips)
        elif scraper_mode == "post":
            post_link = input("Enter the link of the post to scrape: ")
            number_of_vips = int(input("Enter the number of VIPs to scrape: "))
            data = scraper.scrape_single_post(post_link, number_of_vips)
        
        scraper.create_csv(data)
    except KeyboardInterrupt:
        print("Exiting...")
        break
    except TimeoutError:
        print("Timeout error. Please try again.")
        continue
    except Exception as e:
        print(f"Failed due to Error: {e}")
    
scraper.shutdown()