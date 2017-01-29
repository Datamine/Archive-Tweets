def argument()
    """
    handle the user's command-line argument to decide whether to generate
    a display of personal or liked tweets.
    """
    parser = argparse.ArgumentParser(description='See README for help with running this program.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--liked", help="use this flag to handle liked/favorited tweets.",
                        action="store_true", default=False)
    group.add_argument("--posted", help="use this flag to handle tweets that you have authored (retweets included).",
                        action="store_true", default=False)
    args = parser.parse_args()
    if args.liked:
        return 'liked'
    else:
        return 'personal'

def main():
    tweet_type = argument()


if __name__ == '__main__':
    main()
