# import pandas as pd
import os.path
import urllib.parse
from flask import Flask, request, render_template, redirect
import requests
# import pandas as pd
from scrape import *
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import re

app = Flask(__name__, template_folder='template')


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/result', methods=['GET', 'POST'])
def result():
    id = request.form.get('url')
    video_id = get_video_id(id)
    fileName = request.form.get("file_name")

    api_url = f'https://www.googleapis.com/youtube/v3/videos'
    params = {
        'id': video_id,
        'part': 'snippet',
        'key': api_key,
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses

        data = response.json()

        if 'items' in data and data['items']:
            flag = 1
        else:
            flag = 0
    except requests.exceptions.HTTPError:
        flag = 2
    except Exception:
        flag = 3

    if flag == 1:
        df = video_comments(video_id)
        lst = get_video_stats(video_id)

        try:
            if isinstance(df, pd.DataFrame):
                res, file_path = sentiment_analyzer(df, fileName)
                dataFrame = pd.read_csv(file_path)
                dataFrame1 = dataFrame[dataFrame['Label'] == "Positive"]
                dataFrame2 = dataFrame[dataFrame['Label'] == "Neutral"]
                dataFrame3 = dataFrame[dataFrame['Label'] == "Negative"]
                l1 = len(res[res['Label'] == 'Positive'])
                l2 = len(res[res['Label'] == 'Neutral'])
                l3 = len(res[res['Label'] == 'Negative'])
                values = [l1, l2, l3]
                labels = ['Positive', 'Neutral', 'Negative']
                colors = ['Limegreen', 'silver', 'red']

                explode = (0, 0, 0.1)
                fig, ax = plt.subplots(figsize=(4.3, 4.3))

                ax.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, explode=explode)
                ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle

                plt.title('Sentiment Distribution')

                # Save the chart as an image
                img_buffer = BytesIO()
                plt.savefig(img_buffer, format='png')
                img_buffer.seek(0)
                img_str = base64.b64encode(img_buffer.read()).decode('utf-8')
                plt.close()

                plt.figure(figsize=(5, 4))
                plt.bar(labels, values, color=colors)
                plt.title('Sentiment Distribution in YouTube Comments')
                plt.xlabel('Sentiment')
                plt.ylabel('Number of Comments')
                bar_buffer = BytesIO()
                plt.savefig(bar_buffer, format='png')
                bar_buffer.seek(0)
                bar_str = base64.b64encode(bar_buffer.read()).decode('utf-8')
                plt.close()

                wordcloud = generate_cloud(dataFrame.Comment)
                fig1, ax1 = plt.subplots(figsize=(8, 8))
                ax1.imshow(wordcloud, interpolation='bilinear')
                ax1.axis('off')
                save_folder = 'static'
                file_extension = 'png'
                saveFileName = f"{save_folder}/{fileName}.{file_extension}"
                plt.savefig(saveFileName, bbox_inches='tight', pad_inches=0.1)

                return render_template('result.html',
                                       pie_chart=img_str,
                                       frequent_words=saveFileName,
                                       emojis=bar_str,
                                       data=dataFrame,
                                       scraped=dataFrame.shape[0],
                                       df1=dataFrame1.to_dict(
                                           orient='records'),
                                       df2=dataFrame2.to_dict(
                                           orient='records'),
                                       df3=dataFrame3.to_dict(
                                           orient='records'),
                                       value=True,
                                       Title=lst[0],
                                       ChannelName=lst[1],
                                       Views=lst[2],
                                       Likes=lst[3],
                                       TotalComments=lst[4],
                                       PublishedAt=lst[5],
                                       urls=video_id,
                                       flag=1,
                                       downloads=file_path,
                                       fileName=fileName
                                       )
        except ValueError:
            return render_template('result.html', titles=[''],
                                   value=False,
                                   Title=lst[0],
                                   ChannelName=lst[1],
                                   Views=lst[2],
                                   Likes=lst[3],
                                   TotalComments=lst[4],
                                   PublishedAt=lst[5],
                                   urls=video_id,
                                   flag=1
                                   )
        else:
            return render_template('result.html', titles=[''],
                                   value=False,
                                   Title=lst[0],
                                   ChannelName=lst[1],
                                   Views=lst[2],
                                   Likes=lst[3],
                                   TotalComments=lst[4],
                                   PublishedAt=lst[5],
                                   urls=video_id,
                                   flag=1
                                   )

    elif flag == 0:
        return render_template("result.html", flag=0)
    elif flag == 2:
        return render_template("result.html", flag=2)
    else:
        return render_template("result.html", flag=3)


def get_video_id(video_id):
    # Regular video ID pattern
    regular_pattern = re.compile(
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?['
        r'?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})')

    # Shorts video ID pattern
    shorts_pattern = re.compile(
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})')

    # Check for regular video ID match
    regular_match = regular_pattern.search(video_id)
    if regular_match:
        return regular_match.group(1)

    # Check for Shorts video ID match
    shorts_match = shorts_pattern.search(video_id)
    if shorts_match:
        return shorts_match.group(1)

    # If no match found
    return None


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/gotowhatsapp', methods=['Get', 'POST'])
def gotowhatsapp():
    phone_number = '917230860415'

    # Get form data
    name = request.form.get('Name')
    email = request.form.get('Mail')
    query = request.form.get('Subject')
    Message = request.form.get('Message')

    # Construct the message based on form input
    message = f"New query received:\nName: {name}\nEmail: {email}\nQuery: {query}\n\nMessage: {Message}"

    # Construct the WhatsApp URL
    whatsapp_url = f"https://wa.me/{phone_number}?text={urllib.parse.quote(message)}"

    # Redirect the user to WhatsApp URL
    return redirect(whatsapp_url)


#if __name__ == '__main__':
 #   app.run(debug=True)
