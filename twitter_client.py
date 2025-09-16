import tweepy
import config # Assuming config.py is in the same directory or accessible via PYTHONPATH

def get_twitter_api_client_v2():
    """
    Authenticates with the Twitter API v2 using a Bearer Token and returns a Tweepy Client.

    This client is suitable for app-only authentication and read-only access
    to public information (e.g., fetching public tweets).

    Returns:
        tweepy.Client: An authenticated Tweepy Client object if successful.
        None: If authentication fails or credentials are not found.
    """
    if not config.BEARER_TOKEN or config.BEARER_TOKEN == "YOUR_BEARER_TOKEN":
        print("Error: BEARER_TOKEN not found or not set in config.py.")
        print("Please ensure your Twitter API v2 Bearer Token is correctly set in config.py.")
        return None

    try:
        client = tweepy.Client(bearer_token=config.BEARER_TOKEN)
        # You can test authentication by making a simple call, e.g., to get client user's info
        # Note: For app-only auth with just bearer token, you can't get "me";
        # this kind of call would require user context auth (OAuth 2.0 PKCE or OAuth 1.1a).
        # So, we'll rely on Tweepy to raise an exception during Client creation if the token is invalid format,
        # or on subsequent API calls if the token is invalid/revoked.
        print("Successfully authenticated with Twitter API v2 (App-only Bearer Token).")
        return client
    except Exception as e:
        print(f"Error during Twitter API v2 authentication: {e}")
        return None

# Example usage (optional, for testing this module directly)
if __name__ == "__main__":
    print("Attempting to authenticate Twitter API v2 client...")
    client = get_twitter_api_client_v2()
    if client:
        print("Twitter API v2 Client obtained successfully.")
        # As a simple test, you could try fetching a public tweet if you know its ID,
        # but that requires the tweet fetching function which will be built next.
        # For now, just obtaining the client is the goal.
    else:
        print("Failed to obtain Twitter API v2 Client.")

    # Note: For fetching a specific tweet, you'd typically use a function that takes a tweet ID
    # and uses this client, e.g.:
    # tweet_id = "some_tweet_id"
    # if client:
    #     try:
    #         response = client.get_tweet(tweet_id)
    #         if response.data:
    #             print(f"\nSuccessfully fetched tweet {tweet_id}:")
    #             print(response.data.text)
    #         else:
    #             print(f"Could not find tweet {tweet_id} or an error occurred: {response.errors}")
    #     except Exception as e:
    #         print(f"Error fetching tweet {tweet_id}: {e}")
