#!/usr/bin/env python2.7
"""
A small utility to save or delete all of your personally-posted or liked tweets.
John Loeber | contact@johnloeber.com | January 13, 2017 | Python 2.7.6
"""

import dateutil.parser
import twitter
import json
import os
import sys
import logging
import argparse
import ConfigParser
import urllib

from time import time, sleep
from math import ceil

# to enable saving logs, consider e.g. .basicConfig(filename="twitter-tool-x.log")
# where x should be a unique identifier for this log (e.g. timestamp).
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# we will set the twitter api session in main(), this is to instantiate it as a global
api = None

def download_media(folder_path, media_url, fallback_filename):
    """
    Download a media file contained in a tweet.
        - folder_path: string, the name of the folder in which to save the file
        - media_url: string, url to the media file
        - fallback_filename:
    """
    logging.info("Preparing to download media: " + media_url)
    if "/media/" in media_url:
        # I am not entirely sure if all media_urls contain "/media/", hence this conditional
        media_suffix = media_url[media_url.index("/media/")+7:]
    else:
        extension = "." + media_url.split(".")[-1]
        media_suffix = fallback_filename + extension

    file_path = folder_path + "/" + media_suffix
    # often, the media item in 'entities' is also in 'extended_entities'. don't download twice.
    if not media_suffix in os.listdir(folder_path):
        logging.info("Downloading media: " + media_url)
        urllib.urlretrieve(media_url, file_path)
    else:
        logging.info("Skipped duplicate media download: " + media_url)

def archive_single_tweet(tweet, archive_name, id_str, media):
    """
    Archives a single tweet.
        - tweet: twitter.Status, representing the tweet
        - archive_name: string, the folder in which this tweet is to have its archive sub-folder
        - id_str: string, the tweet's unique identifier
        - media: boolean, save attached media if True.
    """
    tweet_as_dict = tweet.AsDict()
    logging.info("Archiving tweet id: " + id_str)
    created_at = dateutil.parser.parse(tweet_as_dict['created_at'])
    folder_name = created_at.strftime("%Y-%m-%d-%H:%M:%S") + "-" + id_str
    folder_path = archive_name + "/" + folder_name

    if os.path.exists(folder_path):
        logging.info("Trying to archive tweet: " + folder_name + "\n\tArchive folder already exists. Proceeding anyway.")
    else:
        os.makedirs(folder_path)

    file_name = "tweet-" + id_str
    file_path = folder_path + "/" + file_name  + ".json"
    tweet_as_json = tweet.__dict__['_json']

    with open(file_path, "w") as f:
        json.dump(tweet_as_json, f, indent=4, sort_keys=True, separators=(',', ':'))

    if media:
        # handle media attachments
        if 'media' in tweet_as_json['entities']:
            tweet_entities_media = tweet_as_json['entities']['media']
            for media_index, media_item in enumerate(tweet_entities_media):
                fallback_file_name = "media_" + str(media_index)
                download_media(folder_path, media_item['media_url'], fallback_file_name)

        if 'extended_entities' in tweet_as_json:
            if 'media' in tweet_as_json['extended_entities']:
                tweet_ee_media = tweet_as_json['extended_entities']['media']
                for media_index, media_item in enumerate(tweet_ee_media):
                    fallback_file_name = "extended_media_" + str(media_index)
                    download_media(folder_path, media_item['media_url'], fallback_file_name)

def handle_single_liked_tweet(tweet, archive, delete, media):
    """
    archives or deletes a single linked tweet.
        - tweet: twitter.Status, representing the tweet
        - archive: boolean, saving the tweet if True
        - delete: boolean, un-liking the tweet if True
        - media: boolean, saving the tweet's media if True (and if archive is True)
    """
    id_str = tweet.__dict__['id_str']
    logging.info("Handling tweet id: " + id_str)

    if archive:
        archive_name = "Archive-Liked-Tweets"
        archive_single_tweet(tweet, archive_name, id_str, media)

    if delete:
        logging.info("Un-liking tweet: " + id_str)
        api.DestroyFavorite(status_id=tweet.__dict__['id'])

def handle_single_personal_tweet(tweet, archive, delete, media):
    """
    archives or deletes a single personal tweet.
        - tweet: twitter.Status, representing the tweet
        - archive: boolean, saving the tweet if True
        - delete: boolean, deleting the tweet if True
        - media: boolean, saving the tweet's media if True (and if archive is True)
    """
    id_str = tweet.__dict__['id_str']
    logging.info("Handling tweet id: " + id_str)

    if archive:
        archive_name = "Archive-Personal-Tweets"
        archive_single_tweet(tweet, archive_name, id_str, media)

    if delete:
        logging.info("Deleting tweet: " + id_str)
        api.DestroyStatus(status_id=tweet.__dict__['id'])

def handle_liked_tweets(archive, delete, media):
    """
    archives or deletes as many liked tweets as possible. (see README for limits.)
        - archive: boolean, saving the tweets if True
        - delete: boolean, un-liking the tweets if True
        - media: boolean, saving each tweet's media if True (and if archive is True)
    """
    if not os.path.exists("Archive-Liked-Tweets"):
        os.makedirs("Archive-Liked-Tweets")

    liked_ratelimit = api.CheckRateLimit("https://api.twitter.com/1.1/favorites/list.json")
    remaining = liked_ratelimit.remaining
    reset_timestamp = liked_ratelimit.reset
    logging.info("Rate Limit Status: " + str(remaining) + " calls to `favorites` remaining in this 15-minute time period.")

    if remaining > 0:
        logging.info("Retrieving a new batch of favorites!")
        favorites = api.GetFavorites(count=200)
        for favorite in favorites:
            handle_single_liked_tweet(favorite, archive, delete, media)
        if len(favorites) == 0:
            logging.info("There are no more liked tweets to handle!")
        else:
            handle_liked_tweets(archive, delete, media)
    else:
        logging.info("Rate limit has been hit! Sleeping until rate limit resets.")
        seconds_until_reset = int(ceil(time() - reset_timestamp))
        sleep(seconds_until_reset)
        handle_liked_tweets(archive, delete, media)


def handle_personal_tweets(archive, delete, media):
    """
    archives or deletes as many personal tweets as possible. (see README for limits.)
        - archive: boolean, saving the tweets if True
        - delete: boolean, deleting the tweets if True
        - media: boolean, saving each tweet's media if True (and if archive is True)
    """
    if not os.path.exists("Archive-Personal-Tweets"):
        os.makedirs("Archive-Personal-Tweets")

    usertimeline_ratelimit = api.CheckRateLimit("https://api.twitter.com/1.1/statuses/user_timeline.json")
    remaining = usertimeline_ratelimit.remaining
    reset_timestamp = usertimeline_ratelimit.reset
    logging.info("Rate Limit Status: " + str(remaining) + " calls to `user_timeline` remaining in this 15-minute time period.")

    if remaining > 0:
        logging.info("Retrieving a new batch of personal tweets!")
        tweets = api.GetUserTimeline(count=200)
        for tweet in tweets:
            handle_single_personal_tweet(tweet, archive, delete, media)
        if len(tweets) == 0:
            logging.info("There are no more personal tweets to handle!")
        else:
            handle_personal_tweets(archive, delete, media)
    else:
        logging.info("Rate limit has been hit! Sleeping until rate limit resets.")
        seconds_until_reset = int(ceil(time() - reset_timestamp))
        sleep(seconds_until_reset)
        handle_personal_tweets(archive, delete, media)

def arguments_and_confirm():
    """
    handle the user's command-line arguments, ensure input is valid,
    confirm the user's intention.
    """
    parser = argparse.ArgumentParser(description='See README for help with running this program.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--liked", help="use this flag to handle liked/favorited tweets.",
                        action="store_true", default=False)
    group.add_argument("--posted", help="use this flag to handle tweets that you have authored (retweets included).",
                        action="store_true", default=False)
    parser.add_argument("--archive", help="use this flag to archive (save) tweets.",
                        action="store_true", default=False)
    parser.add_argument("--delete", help="use this flag to delete/un-like tweets.",
                        action="store_true", default=False)
    parser.add_argument("--media", help="use this flag to save media files attached to tweets, if archiving.",
                        action="store_true", default=False)

    args = parser.parse_args()

    if not (args.posted or args.liked):
        raise ValueError("You must supply either the --posted or --liked flag to specify whether "
            "you want to handle the tweets that you made/retweeted, or the tweets you liked. "
            "\nPlease see README for instructions.")

    elif (not args.archive) and args.media:
        raise ValueError("You have selected not to archive, but to save media. This is impossible. "
            "You can only save media if you're archiving.\nPlease see README for instructions.")

    elif not (args.archive or args.delete):
        raise ValueError("You must supply at least one of the --archive or --delete flags, to "
            "specify what you want to do with the selected tweets. "
            "\nPlease see README for instructions.")

    else:
        option_string = "You have selected: "
        if args.archive:
            option_string += "to ARCHIVE "
            if args.media:
                option_string += "(and save media files) "
            if args.delete:
                if args.posted:
                    option_string += "and DELETE "
                else:
                    option_string += "and UN-LIKE "
        else:
            if args.posted:
                option_string += "to DELETE "
            else:
                option_string += "to UN-LIKE "

        if args.posted:
            liked_or_personal = 'personal'
            option_string += "ALL tweets you have POSTED (including retweets)."
        else:
            liked_or_personal = 'liked'
            option_string += "ALL tweets you have LIKED."

    print option_string

    while True:
        # loop in case the user does not confirm correctly.
        confirm = raw_input("Please confirm. Yes/No\n").lower()
        if len(confirm) >= 1:
            if confirm[0] == 'y':
                return liked_or_personal, args.archive, args.delete, args.media
            elif confirm[0] == 'n':
                sys.exit(0)

def credentials_and_authenticate():
    """
    parse credentials from credentials.txt and authenticate with Twitter.
    """
    config = ConfigParser.ConfigParser()
    config.read('credentials.txt')
    consumer_key = config.get('TWITTER-TOOL', 'consumer_key')
    consumer_secret = config.get('TWITTER-TOOL', 'consumer_secret')
    access_token_key = config.get('TWITTER-TOOL', 'access_token_key')
    access_token_secret = config.get('TWITTER-TOOL', 'access_token_secret')

    global api
    api = twitter.Api(consumer_key=consumer_key,
                      consumer_secret=consumer_secret,
                      access_token_key=access_token_key,
                      access_token_secret=access_token_secret)

    # returning api instead of None so that it's possible to import and use this from the REPL.
    return api

def main():
    tweet_type, archive, delete, media = arguments_and_confirm()
    credentials_and_authenticate()

    if tweet_type == "personal":
        handle_personal_tweets(archive, delete, media)
    else:
        handle_liked_tweets(archive, delete, media)

if __name__ == '__main__':
    main()
