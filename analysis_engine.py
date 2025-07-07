# analysis_engine.py

# --- Constants for Analysis (Examples, can be expanded) ---

# Keywords that might suggest positive sentiment (very basic)
POSITIVE_KEYWORDS = [
    "great", "awesome", "love", "excellent", "good", "amazing", "happy", "thanks", "congrats"
]
# Keywords that might suggest negative sentiment (very basic)
NEGATIVE_KEYWORDS = [
    "bad", "terrible", "hate", "awful", "sucks", "problem", "issue", "stop", "annoying"
]

# Thresholds (examples)
MAX_TEXT_LENGTH_IDEAL = 280  # Standard tweet limit
MIN_TEXT_LENGTH_FOR_SUBSTANCE = 20 # Arbitrary minimum for some substance
SHOUTING_THRESHOLD_CAPS_PERCENTAGE = 0.5 # More than 50% caps might be shouting

# --- Helper Functions ---

def basic_sentiment_analysis(text):
    """
    Performs a very basic sentiment analysis based on keyword matching.
    Returns 'positive', 'negative', or 'neutral'.
    """
    text_lower = text.lower()
    positive_score = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in text_lower)
    negative_score = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in text_lower)

    if positive_score > negative_score:
        return "positive_leaning"
    elif negative_score > positive_score:
        return "negative_leaning"
    else:
        return "neutral"

def analyze_text_characteristics(text):
    """
    Analyzes basic text characteristics.
    """
    analysis = {}
    text_len = len(text)
    analysis['length'] = text_len
    analysis['length_assessment'] = "good"
    if text_len == 0:
        analysis['length_assessment'] = "empty"
    elif text_len < MIN_TEXT_LENGTH_FOR_SUBSTANCE:
        analysis['length_assessment'] = "very_short"
    elif text_len > MAX_TEXT_LENGTH_IDEAL: # Should not happen with Twitter API data
        analysis['length_assessment'] = "too_long_for_twitter"

    num_caps = sum(1 for char in text if char.isupper())
    if text_len > 0 :
        caps_percentage = num_caps / text_len
        analysis['caps_percentage'] = round(caps_percentage, 2)
        if caps_percentage > SHOUTING_THRESHOLD_CAPS_PERCENTAGE and text_len > 10: # Avoid flagging short acronyms
             analysis['shouting_detected'] = True
        else:
            analysis['shouting_detected'] = False
    else:
        analysis['caps_percentage'] = 0
        analysis['shouting_detected'] = False

    analysis['basic_sentiment'] = basic_sentiment_analysis(text)

    # Placeholder for more advanced text scores (like Light Ranker's text_score)
    # This would involve checking for offensiveness, entropy, readability etc.
    # For now, we'll just note its importance.
    analysis['notes_on_text_score'] = "Light Ranker uses a 'text_score' considering offensiveness, entropy, length, readability. Advanced analysis needed here."

    return analysis

def analyze_media_and_links(tweet_data):
    """
    Analyzes media and link presence in the tweet.
    """
    analysis = {}
    entities = tweet_data.get('entities', {})

    analysis['has_image'] = any(media_item.get('type') == 'photo' for media_item in tweet_data.get('media', []))
    analysis['has_video'] = any(media_item.get('type') == 'video' or media_item.get('type') == 'animated_gif' for media_item in tweet_data.get('media', []))
    analysis['num_media_items'] = len(tweet_data.get('media', []))

    analysis['has_card'] = False # Harder to detect reliably from basic entities, often part of URLs.
                                # True card detection might need more specific entity parsing or link analysis.
                                # The Heavy Ranker feature `recap.tweetfeature.has_card` suggests it's known.

    analysis['has_links'] = bool(entities.get('urls'))
    analysis['num_links'] = len(entities.get('urls', []))

    analysis['num_hashtags'] = len(entities.get('hashtags', []))
    analysis['num_mentions'] = len(entities.get('mentions', []))

    analysis['notes_on_media'] = "Presence of media (especially video) can be positive. Specific media features (resolution, duration) are used by Heavy Ranker."
    return analysis

# --- Main Analysis Function ---

def analyze_tweet_against_algorithm(tweet_data):
    """
    Analyzes a fetched tweet against known factors of the Twitter algorithm.

    Args:
        tweet_data (dict): The dictionary of tweet details from data_fetcher.get_tweet_details.

    Returns:
        dict: A dictionary containing analysis results and actionable insights.
    """
    if not tweet_data or not isinstance(tweet_data, dict):
        return {"error": "Invalid or empty tweet_data provided."}

    analysis_results = {
        "tweet_id": tweet_data.get("id"),
        "tweet_text": tweet_data.get("text", ""),
        "factors": [], # List of observations/factors
        "recommendations": [], # List of actionable recommendations
        "overall_assessment_notes": [] # General notes
    }

    # 1. Text Analysis
    text_analysis = analyze_text_characteristics(tweet_data.get("text", ""))
    analysis_results['text_analysis'] = text_analysis
    if text_analysis.get('shouting_detected'):
        analysis_results['factors'].append({
            "factor": "High proportion of capital letters detected.",
            "implication": "This might be perceived as 'shouting' and could negatively impact readability or user perception.",
            "type": "negative_potential"
        })
        analysis_results['recommendations'].append("Consider using fewer capital letters for better readability.")
    if text_analysis.get('basic_sentiment') == 'negative_leaning':
         analysis_results['factors'].append({
            "factor": "Tweet has a potentially negative leaning based on keywords.",
            "implication": "While not always bad, strongly negative content can sometimes lead to 'Negative Feedback' signals (which are heavily penalized).",
            "type": "neutral_to_negative_potential"
        })

    # 2. Media and Link Analysis
    media_analysis = analyze_media_and_links(tweet_data)
    analysis_results['media_analysis'] = media_analysis
    if media_analysis.get('has_video'):
        analysis_results['factors'].append({
            "factor": "Tweet contains video.",
            "implication": "Video content can be highly engaging. The algorithm has specific predictions for video playback (e.g., >50% view time).",
            "type": "positive_potential"
        })
    elif media_analysis.get('has_image'):
        analysis_results['factors'].append({
            "factor": "Tweet contains image(s).",
            "implication": "Images generally increase engagement over plain text.",
            "type": "positive_potential"
        })
    if media_analysis.get('has_links') and media_analysis.get('num_links', 0) > 1:
         analysis_results['factors'].append({
            "factor": f"Tweet contains {media_analysis['num_links']} links.",
            "implication": "Multiple links might make the tweet look spammy or dilute focus, unless it's a curated list.",
            "type": "neutral_to_negative_potential"
        })
        analysis_results['recommendations'].append("If not essential, consider reducing the number of links to maintain focus.")


    # --- Placeholder for more advanced analysis modules ---

    # 3. Engagement Potential Simulation (Qualitative) - Iteration 2+
    #    - Analyze for reply-worthiness, RT-worthiness, fav-worthiness etc.
    #    - Consider if it asks questions, is controversial, provides high value etc.
    analysis_results['engagement_simulation_notes'] = "TODO: Simulate potential for different engagement types based on content heuristics."

    # 4. Author Analysis (Basic) - Iteration 2+
    #    - Check verified status (already in tweet_data if fetched correctly)
    #    - Link to `tweepcred` concept
    analysis_results['author_analysis_notes'] = "TODO: Analyze author details (e.g., verified status from tweet_data)."
    if tweet_data.get('author_verified'):
        analysis_results['factors'].append({
            "factor": "Author is Twitter Verified.",
            "implication": "Tweets from verified authors receive a score multiplier in the algorithm.",
            "type": "positive_signal"
        })


    # 5. Identify Key Algorithm Factors / Scoring - Iteration 2+
    #    - Explicitly mention how tweet characteristics map to known positive/negative weights
    #      (e.g., "This is a reply. Replies that get author engagement are very highly weighted.")
    analysis_results['algorithm_factors_notes'] = "TODO: Map tweet features directly to known high/low algorithm weights."
    if tweet_data.get('is_reply'):
        analysis_results['factors'].append({
            "factor": "This tweet is a reply.",
            "implication": "Replies are a key engagement type. Replies that get engagement *from the original author* are weighted very heavily by the Heavy Ranker. Make your reply insightful, valuable, or engaging to the original poster.",
            "type": "positive_potential_high_value"
        })
        analysis_results['recommendations'].append("If this is a reply, aim to add substantial value or ask a pertinent question to encourage author interaction.")


    # Add a general note about algorithm complexity
    analysis_results['overall_assessment_notes'].append(
        "This analysis is based on the open-sourced components of Twitter's algorithm "
        "and general best practices. The live algorithm is complex, dynamic, and considers "
        "many real-time factors beyond what can be simulated here."
    )
    analysis_results['overall_assessment_notes'].append(
        "Focus on creating authentic, valuable content that resonates with your audience."
    )

    return analysis_results

# Example Usage (for testing this module directly)
if __name__ == '__main__':
    sample_tweet_data_reply_verified = {
        "id": "123",
        "text": "This is a GREAT reply to an interesting topic! What do you think, @original_poster?",
        "author_id": "456",
        "author_username": "testuser",
        "author_verified": True,
        "created_at": "2023-10-26T10:00:00Z",
        "lang": "en",
        "possibly_sensitive": False,
        "public_metrics": {"retweet_count": 5, "reply_count": 2, "like_count": 20, "quote_count": 1},
        "entities": {
            "hashtags": [{"tag": "discussion"}],
            "mentions": [{"username": "original_poster"}]
        },
        "media": [],
        "is_reply": True,
        "replied_to_tweet_id": "789"
    }

    sample_tweet_data_shouting_links = {
        "id": "124",
        "text": "URGENT NEWS CLICK HERE http://example.com AND ALSO HERE http://another.example.com YOU WONT BELIEVE IT!!!",
        "author_id": "789",
        "author_username": "news_guy",
        "author_verified": False,
        "public_metrics": {},
        "entities": {
            "urls": [
                {"url": "t.co/1", "expanded_url": "http://example.com", "display_url": "example.com"},
                {"url": "t.co/2", "expanded_url": "http://another.example.com", "display_url": "another.example.com"}
            ]
        },
        "media": [],
        "is_reply": False,
    }

    import json

    print("--- Analyzing Reply from Verified User ---")
    analysis1 = analyze_tweet_against_algorithm(sample_tweet_data_reply_verified)
    print(json.dumps(analysis1, indent=2))

    print("\n--- Analyzing Shouting Tweet with Multiple Links ---")
    analysis2 = analyze_tweet_against_algorithm(sample_tweet_data_shouting_links)
    print(json.dumps(analysis2, indent=2))

    print("\n--- Analyzing Empty Tweet Data ---")
    analysis3 = analyze_tweet_against_algorithm({})
    print(json.dumps(analysis3, indent=2))

    print("\n--- Analyzing None Tweet Data ---")
    analysis4 = analyze_tweet_against_algorithm(None)
    print(json.dumps(analysis4, indent=2))
