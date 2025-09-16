import re
import tweepy # Although client is obtained from twitter_client, tweepy might be needed for error types
from twitter_client import get_twitter_api_client_v2

def parse_tweet_id_from_url(tweet_url):
    """
    Parses the tweet ID from a Twitter status URL.
    Example URL: https://twitter.com/user/status/1234567890
    """
    match = re.search(r"status/(\d+)", tweet_url)
    if match:
        return match.group(1)
    return None

def get_tweet_details(tweet_url_or_id):
    """
    Fetches details for a specific tweet using its URL or ID.

    Args:
        tweet_url_or_id (str): The full URL of the tweet or the tweet ID itself.

    Returns:
        dict: A dictionary containing tweet details if successful,
              e.g., {'id': str, 'text': str, 'author_id': str,
                     'public_metrics': {'like_count': int, ...}}
        None: If the tweet cannot be fetched or an error occurs.
    """
    tweet_id = None
    if "twitter.com" in tweet_url_or_id and "/status/" in tweet_url_or_id:
        tweet_id = parse_tweet_id_from_url(tweet_url_or_id)
        if not tweet_id:
            print(f"Error: Could not parse tweet ID from URL: {tweet_url_or_id}")
            return None
    elif tweet_url_or_id.isdigit():
        tweet_id = tweet_url_or_id
    else:
        print(f"Error: Invalid tweet URL or ID format: {tweet_url_or_id}")
        return None

    print(f"Attempting to fetch details for tweet ID: {tweet_id}")

    client = get_twitter_api_client_v2()
    if not client:
        print("Error: Failed to get Twitter API client.")
        return None

    try:
        # Reference for tweet_fields and expansions:
        # https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets-id
        # https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/tweet
        response = client.get_tweet(
            id=tweet_id,
            tweet_fields=[
                "created_at",
                "text",
                "author_id",
                "public_metrics",
                "conversation_id",
                "entities",  # For hashtags, mentions, URLs
                "lang",
                "possibly_sensitive",
                "reply_settings",
                "source", # Device/app used to post
                "context_annotations"
            ],
            expansions=["author_id", "attachments.media_keys", "referenced_tweets.id"],
            media_fields=["type", "url", "public_metrics", "alt_text"],
            user_fields=["username", "verified"]
        )

        if response.data:
            tweet_data = response.data
            # You can structure the output as needed. Here's an example:
            metrics = tweet_data.public_metrics if tweet_data.public_metrics else {}
            entities = tweet_data.entities if tweet_data.entities else {}

            # Basic info
            tweet_info = {
                "id": str(tweet_data.id),
                "text": tweet_data.text,
                "author_id": str(tweet_data.author_id) if tweet_data.author_id else None,
                "created_at": str(tweet_data.created_at) if tweet_data.created_at else None,
                "lang": tweet_data.lang,
                "conversation_id": str(tweet_data.conversation_id) if tweet_data.conversation_id else None,
                "possibly_sensitive": tweet_data.possibly_sensitive,
                "reply_settings": tweet_data.reply_settings,
                "source": tweet_data.source,
                "public_metrics": {
                    "retweet_count": metrics.get("retweet_count", 0),
                    "reply_count": metrics.get("reply_count", 0),
                    "like_count": metrics.get("like_count", 0),
                    "quote_count": metrics.get("quote_count", 0),
                    "impression_count": metrics.get("impression_count", 0) # Varies by access level
                },
                "entities": {
                    "hashtags": [tag['tag'] for tag in entities.get('hashtags', [])],
                    "mentions": [mention['username'] for mention in entities.get('mentions', [])],
                    "urls": [{'url': url['url'], 'expanded_url': url['expanded_url'], 'display_url': url['display_url']} for url in entities.get('urls', [])]
                }
            }

            # Add author username if available in includes
            if response.includes and 'users' in response.includes:
                for user in response.includes['users']:
                    if user.id == tweet_data.author_id:
                        tweet_info['author_username'] = user.username
                        tweet_info['author_verified'] = user.verified
                        break

            # Add referenced tweets (is_reply, is_quote)
            tweet_info['is_reply'] = False
            tweet_info['is_quote'] = False
            if tweet_data.referenced_tweets:
                for ref_tweet in tweet_data.referenced_tweets:
                    if ref_tweet.type == 'replied_to':
                        tweet_info['is_reply'] = True
                        tweet_info['replied_to_tweet_id'] = str(ref_tweet.id)
                    elif ref_tweet.type == 'quoted':
                        tweet_info['is_quote'] = True
                        tweet_info['quoted_tweet_id'] = str(ref_tweet.id)

            # Add media info if available
            tweet_info['media'] = []
            if response.includes and 'media' in response.includes:
                for media_item in response.includes['media']:
                    media_details = {
                        'media_key': media_item.media_key,
                        'type': media_item.type,
                        'url': media_item.url if hasattr(media_item, 'url') else None,
                        'alt_text': media_item.alt_text if hasattr(media_item, 'alt_text') else None,
                        'public_metrics': media_item.public_metrics if hasattr(media_item, 'public_metrics') else {}
                    }
                    tweet_info['media'].append(media_details)

            return tweet_info
        elif response.errors:
            print(f"Error fetching tweet {tweet_id}: {response.errors}")
            return None
        else:
            print(f"No data found for tweet {tweet_id}, and no errors reported.")
            return None

    except tweepy.TweepyException as e:
        # More specific Tweepy exception
        print(f"Tweepy error while fetching tweet {tweet_id}: {e}")
        if e.response:
            print(f"Twitter API Response Error Details: {e.response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching tweet {tweet_id}: {e}")
        return None

# Example Usage (for testing this module directly)
if __name__ == "__main__":
    # Replace with a real tweet URL or ID for testing
    # Ensure your BEARER_TOKEN in config.py is valid
    sample_tweet_url = "https://twitter.com/TwitterDev/status/1549130366508552194" # Example public tweet
    sample_tweet_id = "1549130366508552194"

    print(f"\n--- Testing with URL: {sample_tweet_url} ---")
    details_from_url = get_tweet_details(sample_tweet_url)
    if details_from_url:
        print("Tweet details fetched successfully (from URL):")
        for key, value in details_from_url.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            elif isinstance(value, list) and key == 'media':
                 print(f"  {key}:")
                 for item in value:
                     print(f"    {item}")
            else:
                print(f"  {key}: {value}")
    else:
        print("Failed to fetch tweet details (from URL).")

    print(f"\n--- Testing with ID: {sample_tweet_id} ---")
    details_from_id = get_tweet_details(sample_tweet_id)
    if details_from_id:
        print("Tweet details fetched successfully (from ID):")
        # (Similar print logic as above for brevity)
        print(details_from_id['text'][:100] + "...") # Print first 100 chars of text
    else:
        print("Failed to fetch tweet details (from ID).")

    print(f"\n--- Testing with invalid ID: ---")
    invalid_tweet_id = "000"
    details_invalid = get_tweet_details(invalid_tweet_id)
    if not details_invalid:
        print("Correctly failed to fetch non-existent tweet.")
    else:
        print("Something went wrong, fetched details for an invalid ID.")

    print(f"\n--- Testing with invalid URL format: ---")
    invalid_url = "https://example.com/foo/bar"
    details_invalid_url = get_tweet_details(invalid_url)
    if not details_invalid_url:
        print("Correctly failed with invalid URL format.")
    else:
        print("Something went wrong, processed an invalid URL format.")
