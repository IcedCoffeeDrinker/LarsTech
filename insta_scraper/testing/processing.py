import json
import csv

# Read the JSONL file
data = []
with open('data.jsonl', 'r') as f:
    for line in f:
        item = json.loads(line.strip())
        data.append(item)

print(f"Loaded {len(data)} profiles")

# Sort by follower count (descending)
sorted_data = sorted(data, key=lambda x: x.get('followersCount', 0), reverse=True)

# Get top 50
top_50 = sorted_data[:50]

print(f"Top follower count: {top_50[0]['followersCount']}")
print(f"50th follower count: {top_50[-1]['followersCount']}")

# Create CSV matching scraper.py format
with open('vip_profiles_top50.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    
    # Write header (matching scraper.py format)
    header = ['Post Number', 'VIP Rank', 'Username', 'Followers Count', 'Location', 'Profile URL']
    writer.writerow(header)
    
    # Write top 50 VIPs
    for rank, vip in enumerate(top_50, start=1):
        location = vip.get('location', 'N/A')
        if location is None or location == '' or location == 'None':
            location = 'N/A'
            
        writer.writerow([
            'Post #1',
            f'VIP #{rank}',
            vip.get('username', 'N/A'),
            vip.get('followersCount', 'N/A'),
            location,
            vip.get('url', 'N/A')
        ])

print(f"✅ Created vip_profiles_top50.csv with {len(top_50)} VIPs")