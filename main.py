import requests
from googlesearch import search
from bs4 import BeautifulSoup
import json
from youtube_transcript_api import YouTubeTranscriptApi
import smtplib
import ssl
import csv
import random
from email.message import EmailMessage

OPENAI_API_KEY = '**************************************************'


def chat_gpt4(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are ChatGPT-4, a large language model trained by OpenAI."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4096,
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        message = response_data["choices"][0]["message"]["content"]
        return message
    else:
        raise Exception(
            f"Request failed with status code {response.status_code}: {response.text}"
        )


# Function to search and scrape Medium content
def search_and_scrape_medium(title):
    # Perform a Google search using the provided title
    search_query = f"medium innerscore {title}"
    # Perform a Google search using the provided title
    search_results = search(search_query, lang='en')

    # Fetch the first search result URL
    first_result_url = next(search_results, None)

    if first_result_url:
        # Send a GET request to the search result URL
        response = requests.get(first_result_url)
        response.raise_for_status()  # Raise an exception if the request fails

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract the content from the first search result
        content = soup.get_text()

        # Write the content to a text file
        with open("medium.txt", "w", encoding="utf-8") as file:
            file.write(content)

        print("Content saved to medium.txt file.")
    else:
        print("No results found for Medium.")


# Function to download YouTube transcript
def download_youtube_transcript(video_url, output_file):
    try:
        video_id = video_url.split("=")[1]  # Extract the video ID from the URL
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

        with open(output_file, 'w', encoding='utf-8') as file:
            for line in transcript:
                text = line['text']
                file.write(text + '\n')

        print(f'Transcript downloaded successfully and saved to "{output_file}".')

    except Exception as e:
        print(f'An error occurred while downloading the transcript: {e}')


# Define the URL of your channel's journal page
medium_url = 'https://medium.com/@innerscore'

# Send a GET request to the Medium URL and fetch the HTML content
response = requests.get(medium_url)
html_content = response.text

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Find the list of journals on the page
journals = soup.find_all('h2', {
    'class': 'be jt ju do jv jw jx jy dq jz ka kb kc kd ke kf kg kh ki kj kk kl km kn ko kp kq hn ho hp hr ht bj'})

# Check if any journals are found
if journals:
    # Get the latest journal
    latest_journal = journals[0]

    # Extract the title of the latest journal
    title = latest_journal.text.strip()

    # Call the function to search and scrape Medium using the extracted title
    search_and_scrape_medium(title)
else:
    print('Unable to find any journals on the Medium page.')

# Set your YouTube API key here
API_KEY = "AIzaSyCQrrS4QoM6ZSxsUWHBeOrINF2CeOgbBPc"

# Set the YouTube channel ID
channel_id = "UConeitW_F4Ak13codN_FE8w"

# Get the latest video ID from the channel
channel_url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={channel_id}&key={API_KEY}"
response = requests.get(channel_url)
channel_data = json.loads(response.text)
uploads_playlist_id = channel_data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

playlist_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=1&playlistId={uploads_playlist_id}&key={API_KEY}"
response = requests.get(playlist_url)
playlist_data = json.loads(response.text)
video_id = playlist_data["items"][0]["snippet"]["resourceId"]["videoId"]
video_title = playlist_data["items"][0]["snippet"]["title"]
video_url = f"https://www.youtube.com/watch?v={video_id}"

# Define the output file name for the YouTube transcript
transcript_output_file = "transcript.txt"

# Call the function to download YouTube transcript
download_youtube_transcript(video_url, transcript_output_file)

# Read the contents of medium.txt and transcript.txt
with open('medium.txt', 'r', encoding='utf-8') as file:
    medium_content = file.read()

with open('transcript.txt', 'r', encoding='utf-8') as file:
    transcript_content = file.read()

# Combine the contents
combined_content = medium_content + '\n' + transcript_content

# Generate the summary using ChatGPT-4.0-turbo
summary = chat_gpt4(combined_content)

# Write the summary to a text file
with open('summary.txt', 'w', encoding='utf-8') as file:
    file.write(summary)

print("Summary saved to summary.txt file.")

# Prepare the email with the summary
replyto = 'Your Reply to Email Id'
subject = 'Summary Email'
name = 'Your Name'

# Read the user credentials from CSV file
with open("user.csv") as f:
    data = [row for row in csv.reader(f) if row]

# Prepare the email body
email_body = f"Hello,\n\nHere is the summary for you:\n\n{summary}"

counter = {}


# Loop over the recipient email addresses from the CSV file
with open('mails.csv', 'r') as csvfile:
    datareader = csv.reader(csvfile)
    for row in datareader:
        random_user = random.choice(data)
        sender = random_user[0]
        password = random_user[1]

        if sender not in counter:
            counter[sender] = 0

        if counter[sender] >= 500:
            continue

        try:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context)
            server.login(sender, password)
            msg = EmailMessage()
            msg['From'] = f'{name} <{sender}>'
            msg['Reply-To'] = replyto
            msg['To'] = row
            msg['Subject'] = subject
            msg.set_content(email_body)
            server.send_message(msg)
            counter[sender] += 1
            print(f"{counter[sender]} emails sent from {sender} to {row}")
            with open("mails.csv", "r") as file:
                reader = csv.reader(file)
                rows = list(reader)
                rows = rows[1:]
            if rows:
                with open("mails.csv", "w", newline='') as file:
                    writer = csv.writer(file)
                    writer.writerows(rows)
            server.close()
        except Exception as e:
            print(f"Error sending email from {sender} to {row}: {e}")
            with open("mails.csv", "r") as file:
                reader = csv.reader(file)
                rows = list(reader)
                rows = rows[1:]
            if rows:
                with open("mails.csv", "w", newline='') as file:
                    writer = csv.writer(file)
                    writer.writerows(rows)

print("Emails Sent")
for sender, count in counter.items():
    print(f"{sender}: {count}")
