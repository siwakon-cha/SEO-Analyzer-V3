from firebase_admin import db
from urllib.parse import urlparse

# Function to delete data in batches
def delete_data_in_batches(website_url):
    parsed_url = urlparse(website_url)
    subdomain = parsed_url.netloc.replace('.','_')
    # Get the root reference of the Realtime Database
    root_ref = db.reference(f'website_data/{subdomain}/update_times')
    snapshot = list(root_ref.get())

    for time in snapshot:
        db.reference(f'website_data/{subdomain}/webpage_analysis/{time}').delete()
        db.reference(f'website_data/{subdomain}/backlinks_analysis/{time}').delete()
        print(f"Deleted {time}")
    root_ref.delete()