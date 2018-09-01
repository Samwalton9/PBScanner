import asyncio
import datetime
import discord
import json
import logging
import praw
import numpy as np
import os

logger = logging.getLogger(__name__)

file_path = os.path.dirname(__file__)

config_path = os.path.join(file_path, 'config.json')
config_data = json.load(open(config_path))

client = discord.Client()
reddit = praw.Reddit(client_id=config_data["prawID"],
                     client_secret=config_data["prawSecret"],
                     user_agent='Project Borealis bot - /u/samwalton9')

@client.event
async def on_ready():

    print('Logged in as', client.user.name)
    print('\nLogged in to the following servers:')
    for server in client.servers:
        print(server.name)
    print('-----')


def load_reddit_logs():
    try:
        reddit_post_log = np.load('reddit_posts.npy')
    except FileNotFoundError:
        logger.info("Couldn't load reddit_posts.npy")
        reddit_post_log = []

    print(reddit_post_log)
    return reddit_post_log


async def reddit_posts():
    """
    Every minute, check /r/dreamsofhalflife3 and search for "Project Borealis"
    across Reddit and post any new threads.
    """
    await client.wait_until_ready()
    while not client.is_closed:
        post_log = load_reddit_logs()

        sub_submissions = reddit.subreddit('dreamsofhalflife3').new(limit=10)
        all_submissions = reddit.subreddit('all').search('"Project Borealis"',
                                                         sort='new',
                                                         limit=10)

        post_list = []
        # Transfer the iterator into a list so it can be reversed.
        # We want to post the oldest first to maintain chronological order.
        for post in all_submissions:
            post_list.append(post)
        for post in sub_submissions:
            post_list.append(post)

        post_ids = []
        for post in reversed(list(set(post_list))):
            post_ids.append(post.id)
            if post.id not in post_log:
                post_embed = discord.Embed(
                    title=post.title,
                    type='rich',
                    description=post.selftext[:1000],
                    url=post.url,
                    color=0xff4500,
                    timestamp=datetime.datetime.utcfromtimestamp(post.created_utc),
                )
                post_embed.set_thumbnail(url='https://www.redditstatic.com/new-icon.png')
                post_embed.set_author(name="/r/{subreddit}".format(
                                        subreddit=post.subreddit),
                                      url="https://reddit.com/r/{subreddit}".format(
                                          subreddit=post.subreddit
                                      ))
                post_embed.set_footer(text="Posted by /u/{username}".format(
                    username=post.author
                ))
                server_channel = client.get_channel(config_data["channelID"])
                await client.send_message(server_channel, embed=post_embed)
                await asyncio.sleep(0.5)

        np.save('reddit_posts', post_ids)
        await asyncio.sleep(5)


async def twitter_posts():
    """
    Scan Twitter and post any new Tweets about the project.
    """
    pass


client.loop.create_task(reddit_posts())
client.run(config_data["botToken"])
