from apify_scraper import ApifyScraper
from playwright.sync_api import TimeoutError
from nicegui import ui
import csv
import asyncio
import time

### Initialize Scraper ###

scraper = ApifyScraper()


### UI Functions ###
async def update_logs():
    # Check if there are new messages in the queue
    while not scraper.log_queue.empty():
        message = scraper.log_queue.get()
        # Push message to the UI component
        log_view.push(message)


def on_mode_change():
    mode = mode_selector.value
    if mode == "Single Post":
        post_mode.set_visibility(True)
        profile_mode.set_visibility(False)
    elif mode == "Entire Profile":
        post_mode.set_visibility(False)
        profile_mode.set_visibility(True)


def add_row(post_number, post_url, vip_rank, username, followers, location, profile_url):
    new_row = {
        'post_number': post_number,
        'post_url': post_url, # hidden
        'vip_rank': vip_rank,
        'username': username,
        'followers': followers,
        'location': location,
        'profile_url': profile_url,
    }
    table.rows.append(new_row)
    table.update()


### GUI ###
def show_csv(path):
    with open(path, 'r') as file:
        reader = csv.reader(file)
        next(reader) # skip header
        for row in reader:
            add_row(row[0], row[1], row[2], row[3], row[4], row[5], row[6])


### Scraping Functions ###
async def start_scraping():
    mode_selector.set_enabled(False)
    if mode_selector.value == "Single Post":
        scrape_button_post.set_enabled(False)
    elif mode_selector.value == "Entire Profile":
        scrape_button_profile.set_enabled(False)
    ui.notify('Starting scrape...', type='info')
    try:
        if mode_selector.value == "Single Post":
            data = await asyncio.to_thread(
                scraper.scrape_single_post,
                link_input.value,
                int(number_of_vips_input.value)
            )
        elif mode_selector.value == "Entire Profile":
            data = await asyncio.to_thread(
                scraper.scrape_profile_posts,
                profile_input.value,
                int(number_of_posts_input.value),
                int(number_of_vips_input.value)
            )
        ui.notify('Done!', type='positive')
        # create csv and auto download
        csv_path = scraper.create_csv(data)
        show_csv(csv_path)
        ui.download(csv_path)
        # additional download button
        download_button.props('csv_path=' + csv_path)
        download_button.set_visibility(True)
        download_button.on('click', lambda: ui.download(csv_path))
    finally:
        if mode_selector.value == "Single Post":
            scrape_button_post.set_enabled(True)
        elif mode_selector.value == "Entire Profile":
            scrape_button_profile.set_enabled(True)
        mode_selector.set_enabled(True)


### Initialize UI ###
# title
ui.label('Collaborator Scraper').classes('text-h2').style('''
    position: absolute; 
    top: 40px; 
    left: 50%; 
    transform: translateX(-50%); 
    z-index: 0; 
    font-weight: bold;
    background: linear-gradient(to bottom, #333333 10%, #333333 30%, #dddddd 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: transparent;
''')

# main body container
with ui.column().classes('q-mt-xl w-full').style('position: relative; z-index: 1; margin-top: 120px;'):

    mode_selector = ui.toggle(["Single Post", "Entire Profile"], value="Single Post", on_change=on_mode_change)

    with ui.row().classes('items-center') as post_mode:
        link_input = ui.input(
            label="Enter Post Link", 
            placeholder="e.g. https://www.instagram.com/p/1234567890/",
            validation={'Post Link must be a valid Instagram post link': lambda value: value.startswith('https://www.instagram.com/p/') or value == ""}
            ).on('keydown.enter', lambda: link_input.run_method('blur'))
        scrape_button_post = ui.button('Scrape', on_click=start_scraping)   

    with ui.row().classes('items-center') as profile_mode:
        profile_input = ui.input(
            label="Enter Profile Name", 
            placeholder="e.g. larshinrichs",
            validation={'Profile Name must be a valid Instagram username': lambda value: value.isalpha() or value == ""}
            ).on('keydown.enter', lambda: number_of_posts_input.run_method('blur'))
        number_of_posts_input = ui.input(
            label="Number of Posts", 
            placeholder="e.g. 2", 
            validation={'Number of Posts must be an integer': lambda value: value.isdigit() or value == ""}
            ).on('keydown.enter', lambda: number_of_posts_input.run_method('blur'))
        number_of_vips_input = ui.input(
            label="Number of VIPs", 
            placeholder="e.g. 5", 
            validation={'Number of VIPs must be an integer': lambda value: value.isdigit() or value == ""}
            ).on('keydown.enter', lambda: number_of_vips_input.run_method('blur'))
        scrape_button_profile = ui.button('Scrape', on_click=start_scraping)

    profile_mode.set_visibility(False)


    columns = [
        {'name': 'post_number', 'label': 'Post Number', 'field': 'post_number', 'sortable': True},
        {'name': 'vip_rank', 'label': 'VIP Rank', 'field': 'vip_rank', 'sortable': True},
        {'name': 'username', 'label': 'Username', 'field': 'username', 'sortable': True},
        {'name': 'followers', 'label': 'Followers Count', 'field': 'followers', 'sortable': True},
        {'name': 'location', 'label': 'Location', 'field': 'location', 'sortable': True},
        {'name': 'profile_url', 'label': 'Profile URL', 'field': 'profile_url'},
    ]
    table = ui.table(columns=columns, rows=[]).classes('w-full')

    table.add_slot('body-cell-post_number', '''
        <q-td :props="props">
            <a :href="props.row.post_url" target="_blank" style="color: #1976d2; text-decoration: none;">
                {{ props.value }}
            </a>
        </q-td>
    ''')


    ui.label('Scraper Logs').classes('text-h6 q-mt-md')
    log_view = ui.log(max_lines=100).classes('w-full h-64')
    ui.timer(0.1, update_logs) 


    download_button = ui.button('Download CSV', icon='download', on_click=lambda: ui.download(csv_path))
    download_button.set_visibility(False)


### CLI ###
def main():
    while True:
        print("Type Ctrl+C to exit")
        try:
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
            else:
                print("Invalid mode. Please try again.")
                continue
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

if __name__ in {"__main__", "__mp_main__"}:
    #main()
    ui.run()
    scraper.log("UI Initialized")
    #add_row(1, 1, "John Doe", 1000, "New York", "https://www.example.com")
    show_csv("data/last_scrape.csv")