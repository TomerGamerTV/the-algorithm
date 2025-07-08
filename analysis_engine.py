# analysis_engine.py
import re

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
        # Recommendation moved to engagement potential section if shouting is high
    # Negative sentiment factor also moved to be evaluated alongside negative_feedback_potential

    # 2. Media and Link Analysis
    media_analysis = analyze_media_and_links(tweet_data)
    analysis_results['media_analysis'] = media_analysis
    # Factors for media/links also moved to be evaluated by engagement potential where relevant


    # --- Engagement Potential Simulation & Related Recommendations ---
    text_info_for_engagement = analysis_results.get('text_analysis', {})
    media_info_for_engagement = analysis_results.get('media_analysis', {})
    engagement_potentials = simulate_engagement_potential(
        tweet_data, text_info_for_engagement, media_info_for_engagement
    )
    analysis_results['engagement_potential'] = engagement_potentials

    # Remove the old placeholder note as we are adding the actual section
    if 'engagement_simulation_notes' in analysis_results:
        del analysis_results['engagement_simulation_notes']

    # Refine recommendations based on engagement potentials
    if engagement_potentials.get('reply_potential', {}).get('assessment') in ['low', 'medium']:
        if "?" not in analysis_results['tweet_text']:
             analysis_results['recommendations'].append("To boost replies, try asking a direct question or inviting opinions.")
        if media_info_for_engagement.get("num_mentions", 0) == 0 and not tweet_data.get('is_reply'):
            analysis_results['recommendations'].append("Mentioning relevant users (if appropriate) can sometimes draw them into conversation and increase replies.")

    if engagement_potentials.get('retweet_quote_potential', {}).get('assessment') in ['low', 'medium']:
        if not media_info_for_engagement.get("has_video") and not media_info_for_engagement.get("has_image"):
            analysis_results['recommendations'].append("Adding compelling media (image/video) or a link to unique content can increase retweet/quote potential.")
        if not any(cta in analysis_results['tweet_text'].lower() for cta in ["rt if", "retweet if", "please share"]):
             analysis_results['recommendations'].append("Consider if a call to action for sharing (e.g., 'RT if you agree') is appropriate for your content to boost retweets.")

    if engagement_potentials.get('like_potential', {}).get('assessment') == 'low':
        if text_info_for_engagement.get('basic_sentiment') != 'positive_leaning':
            analysis_results['recommendations'].append("Content with more positive or humorous sentiment often attracts more likes.")
        if not media_info_for_engagement.get("has_video") and not media_info_for_engagement.get("has_image"):
            analysis_results['recommendations'].append("Visually appealing content (images/videos) tends to get more likes.")

    if engagement_potentials.get('negative_feedback_potential', {}).get('assessment') in ['medium', 'high']:
        analysis_results['recommendations'].append("Your tweet has characteristics that might lead to negative feedback. Review for potentially offensive language, excessive capitalization, or spammy elements (too many hashtags/links). Negative feedback is heavily penalized.")
        # Add specific reasons to factors if not already there from text_analysis for shouting
        if text_info_for_engagement.get('shouting_detected') and not any("High proportion of capital letters" in f.get("factor","") for f in analysis_results['factors']):
             analysis_results['factors'].append({
                "factor": "High proportion of capital letters detected.",
                "implication": "This might be perceived as 'shouting' and contribute to negative feedback.",
                "type": "negative_potential_high"
            })
        if text_info_for_engagement.get('basic_sentiment') == 'negative_leaning' and not any("negative leaning" in f.get("factor","") for f in analysis_results['factors']):
             analysis_results['factors'].append({
                "factor": "Tweet has a potentially negative leaning based on keywords.",
                "implication": "Strongly negative content can sometimes lead to 'Negative Feedback' signals.",
                "type": "negative_potential_medium"
            })


    # 4. Author Analysis (Basic) & Deeper Algorithmic Factors
    #    - Link to `tweepcred` concept, `realgraph`, `user_author_aggregate`
    #    - Embeddings, Topic Alignment, Safety Flags, Tweet Age

    # Remove old placeholders for these sections
    if 'author_analysis_notes' in analysis_results:
        del analysis_results['author_analysis_notes']
    if 'algorithm_factors_notes' in analysis_results:
        del analysis_results['algorithm_factors_notes']

    # Author Verified (already covered, but ensure it's in factors)
    if tweet_data.get('author_verified') and not any("Author is Twitter Verified" in f.get("factor","") for f in analysis_results['factors']):
        analysis_results['factors'].append({
            "factor": "Author is Twitter Verified.",
            "implication": "Tweets from verified authors receive a score multiplier (e.g., 2-4x in example configs). This is a direct boost.",
            "type": "positive_signal_strong"
        })

    # Author Reputation (Tweepcred)
    analysis_results['factors'].append({
        "factor": "Author Reputation (e.g., `tweepcred`, `recap.tweetfeature.user_rep`).",
        "implication": "The algorithm considers author reputation. Higher reputation (built over time via positive engagement and network effects) generally improves visibility. This is used in both Light and Heavy Rankers.",
        "type": "general_factor_author"
    })

    # Replies & User-Author Interactions
    if tweet_data.get('is_reply'):
        if not any("This tweet is a reply." in f.get("factor","") for f in analysis_results['factors']): # Avoid duplicate if added earlier
            analysis_results['factors'].append({
                "factor": "This tweet is a reply.",
                "implication": "Replies are a key engagement. Interactions with the original author (e.g., them liking/replying to your reply) are weighted very heavily by the Heavy Ranker (e.g., 'Reply Engaged by Author' ~75.0).",
                "type": "positive_potential_high_value"
            })
        analysis_results['factors'].append({
            "factor": "User-Author Interaction History (e.g., `user_author_aggregate` features).",
            "implication": "If the viewer has a positive interaction history with the replied-to author, this tweet (reply) is more likely to be ranked higher for that viewer. Past likes, replies, profile clicks between a user and an author matter.",
            "type": "contextual_factor_viewer_author"
        })

    # RealGraph (Viewer-Author Connection for In-Network)
    # This is more about how the tweet is ranked for *others* if it's in-network content from this author
    analysis_results['factors'].append({
        "factor": "Viewer-Author Graph Connection (e.g., `realgraph` features).",
        "implication": "For in-network content, the strength of connection (mutual follows, past interactions) between a potential viewer and the tweet's author significantly influences ranking. Tweets from closely connected or frequently interacting authors are prioritized.",
        "type": "contextual_factor_in_network"
    })

    # Topic Alignment
    analysis_results['factors'].append({
        "factor": "Topic Alignment (e.g., `user_topic_aggregate`, `author-topic_aggregate`).",
        "implication": "The algorithm tries to match tweets to users' topic interests and also considers an author's typical topics. Content aligned with these is favored. The Heavy Ranker uses many topic-based aggregate features.",
        "type": "general_factor_content"
    })

    # Embeddings (Semantic Understanding)
    analysis_results['factors'].append({
        "factor": "Semantic Understanding via Embeddings (e.g., TwHIN, SimClusters).",
        "implication": "The algorithm uses embeddings to understand the meaning of your tweet and its similarity to other users/tweets/topics. Clear, coherent language around specific themes helps the algorithm categorize and recommend your content effectively.",
        "type": "general_factor_content_advanced"
    })

    # Tweet Age
    analysis_results['factors'].append({
        "factor": "Tweet Age (e.g., `tweet_age_in_secs`).",
        "implication": "Fresher content is often prioritized, but the algorithm also considers overall engagement and relevance, allowing older tweets to resurface if highly pertinent or engaging.",
        "type": "general_factor_tweet"
    })

    # Safety/Spam Flags Connection
    if tweet_data.get('possibly_sensitive'):
        analysis_results['factors'].append({
            "factor": "Tweet flagged as 'Possibly Sensitive' by Twitter.",
            "implication": "This directly maps to internal safety flags (like `label_nsfw_...`) which can lead to reduced visibility or downranking, and may increase 'Negative Feedback Potential'.",
            "type": "negative_signal_strong"
        })

    current_negative_feedback_assessment = engagement_potentials.get('negative_feedback_potential', {}).get('assessment', 'low')
    if current_negative_feedback_assessment in ['medium', 'high']:
        if media_info_for_engagement.get("num_hashtags", 0) > 5 or \
           (media_info_for_engagement.get("num_mentions", 0) > 3 and not tweet_data.get('is_reply')) or \
           media_info_for_engagement.get("num_links", 0) > 2:
            analysis_results['factors'].append({
                "factor": "Potential Spam-like Characteristics (multiple links/hashtags/mentions).",
                "implication": "These can map to internal spam flags (e.g., `label_spam_flag`) and heavily penalize reach, contributing to 'Negative Feedback Potential'.",
                "type": "negative_signal_strong"
            })

    # Recommendations based on deeper factors
    if any("User-Author Interaction History" in f.get("factor","") for f in analysis_results['factors']) and tweet_data.get('is_reply'):
        analysis_results['recommendations'].append("When replying, aim for interactions that the original author might find valuable enough to like or reply to, as this is a highly positive signal.")

    if any("Topic Alignment" in f.get("factor","") for f in analysis_results['factors']):
        analysis_results['recommendations'].append("Consider the topics your content aligns with. Consistency with your profile's theme and relevance to your target audience's interests can improve algorithmic pairing.")

    if any("Semantic Understanding via Embeddings" in f.get("factor","") for f in analysis_results['factors']):
        analysis_results['recommendations'].append("Use clear and coherent language. This helps the algorithm's embeddings better understand your tweet's meaning and match it to relevant users and topics.")

    if any("Author Reputation" in f.get("factor","") for f in analysis_results['factors']):
        analysis_results['recommendations'].append("Building a positive author reputation over time (through quality content and genuine engagement) is beneficial for overall visibility.")

    if any("Potential Spam-like Characteristics" in f.get("factor","") for f in analysis_results['factors']):
        if not any("Review for potentially offensive language" in r for r in analysis_results['recommendations']): # Avoid duplicate generic advice
            analysis_results['recommendations'].append("Review tweet for elements that might appear spammy (e.g., excessive unrelated hashtags, too many mentions in a non-conversational way, multiple suspicious links) as these can be penalized.")

    if tweet_data.get('possibly_sensitive') and not any("Avoid content that could be flagged as sensitive" in r for r in analysis_results['recommendations']):
         analysis_results['recommendations'].append("Be mindful of content that Twitter might flag as 'possibly sensitive', as this can reduce reach. Ensure it complies with Twitter's rules.")


    # Add a general note about algorithm complexity
    analysis_results['overall_assessment_notes'].append(
        "This analysis is based on the open-sourced components of Twitter's algorithm "
        "and general best practices. The live algorithm is complex, dynamic, and considers "
        "many real-time factors beyond what can be simulated here."
    )
    analysis_results['overall_assessment_notes'].append(
        "Focus on creating authentic, valuable content that resonates with your audience."
    )

    # --- Engagement Potential Simulation (Placeholder for now) ---
    # This will be built out in subsequent steps.
    # For now, just adding the key to the results.
    text_info_for_engagement = analysis_results.get('text_analysis', {})
    media_info_for_engagement = analysis_results.get('media_analysis', {})
    analysis_results['engagement_potential'] = simulate_engagement_potential(
        tweet_data, text_info_for_engagement, media_info_for_engagement
    )
    # Remove the old placeholder note as we are adding the actual section
    if 'engagement_simulation_notes' in analysis_results:
        del analysis_results['engagement_simulation_notes']


    return analysis_results

# --- Engagement Potential Simulation Sub-Functions (to be built out) ---

def _assess_reply_potential(tweet_data, text_info, media_info):
    """
    Assesses the potential for a tweet to receive replies based on heuristics.
    """
    reasons = []
    score = 0 # Simple scoring: 0=low, 1=medium, 2+=high

    text = tweet_data.get("text", "").lower()

    # 1. Question marks
    if "?" in text:
        reasons.append("Contains question mark(s), inviting answers.")
        score += 1

    # 2. Call to action for opinions
    opinion_phrases = ["what do you think", "thoughts?", "your opinion", "share your views", "let me know"]
    if any(phrase in text for phrase in opinion_phrases):
        reasons.append("Contains phrases asking for opinions.")
        score += 1

    # 3. Mentions
    if media_info.get("num_mentions", 0) > 0:
        reasons.append(f"Mentions {media_info['num_mentions']} user(s), potentially drawing them into conversation.")
        # Higher score if it's not just a self-mention in a reply chain (harder to check simply)
        score += 0.5 # Mentions are good but not as strong as a direct question for general replies

    # 4. Reply settings (if available and not 'mentioned_users' or 'followed_users' only)
    reply_settings = tweet_data.get("reply_settings")
    if reply_settings and reply_settings != "everyone":
        reasons.append(f"Reply settings are restricted to '{reply_settings}', limiting who can reply.")
        score -= 1 # Penalize if replies are restricted
    else:
        reasons.append("Reply settings likely allow everyone to reply (default or explicitly set).")
        # No direct score change for 'everyone', it's the baseline.

    # 5. Is it already a reply? (Replies to replies can continue chains)
    if tweet_data.get('is_reply'):
        reasons.append("Tweet is itself a reply, which can encourage further discussion in the thread.")
        score += 0.5

    # Determine qualitative assessment
    assessment = "low"
    if score >= 2:
        assessment = "high"
    elif score >= 1:
        assessment = "medium"

    if not reasons:
        reasons.append("Tweet does not have obvious characteristics that strongly invite replies (e.g., questions, direct calls for opinion).")

    return {"assessment": assessment, "reasons": reasons, "score": score}

def _assess_retweet_potential(tweet_data, text_info, media_info):
    """
    Assesses the potential for a tweet to be retweeted or quoted based on heuristics.
    """
    reasons = []
    score = 0 # Simple scoring: 0=low, 1=medium, 2+=high

    text = tweet_data.get("text", "").lower()
    text_actual_case = tweet_data.get("text", "") # For checking things like "BREAKING"

    # 1. Strong Call to Action for sharing
    share_ctas = ["rt if", "retweet if", "please share", "spread the word", "share this"]
    if any(phrase in text for phrase in share_ctas):
        reasons.append("Contains a direct call to action for sharing/retweeting.")
        score += 1.5 # Strong indicator

    # 2. Links to External Content
    if media_info.get("has_links"):
        reasons.append(f"Contains {media_info.get('num_links', 0)} link(s) to external content, which can be shareable.")
        score += 0.5

    # 3. Media Presence (especially video or informative images)
    if media_info.get("has_video"):
        reasons.append("Contains video, which can be highly shareable.")
        score += 1
    elif media_info.get("has_image"):
        reasons.append("Contains image(s), which can increase shareability.")
        score += 0.5

    # 4. Strong Sentiment (can be polarizing but often shareable)
    #    Using text_info which contains basic_sentiment
    sentiment = text_info.get('basic_sentiment', 'neutral')
    if sentiment == 'positive_leaning' or sentiment == 'negative_leaning':
        reasons.append(f"Text has a {sentiment} sentiment, which can sometimes drive shares.")
        score += 0.5
        # Note: Very negative might also lead to "negative feedback" later.

    # 5. Information Value / Uniqueness Indicators
    news_keywords = ["breaking", "study finds", "reveals", "exclusive", "announcement", "new report"]
    if any(keyword in text for keyword in news_keywords) or "BREAKING" in text_actual_case:
        reasons.append("Suggests news value or unique information, increasing shareability.")
        score += 1

    # Check for numbers/statistics (simple proxy for data)
    if any(char.isdigit() for char in text):
        # Check if it's part of a common pattern like "Top 10" or a year, or a percentage
        if re.search(r'\d+%', text) or re.search(r'\b\d[\d,.]*\b', text): # find standalone numbers
             if not re.search(r'\b(19|20)\d{2}\b', text): # Avoid simple years
                reasons.append("Contains numbers/statistics, which can indicate informative content.")
                score += 0.5


    # 6. Hashtag Usage (for visibility within interested communities)
    num_hashtags = media_info.get("num_hashtags", 0)
    if num_hashtags > 0 and num_hashtags <= 3: # Optimal range, more can look spammy
        reasons.append(f"Uses {num_hashtags} hashtag(s), potentially increasing visibility for sharing.")
        score += 0.5
    elif num_hashtags > 3:
        reasons.append(f"Uses {num_hashtags} hashtags. While good for visibility, too many can sometimes reduce perceived quality for shares.")
        score += 0.2 # Still some benefit

    # Determine qualitative assessment
    assessment = "low"
    if score >= 2.5: # Higher threshold for "high" RT potential
        assessment = "high"
    elif score >= 1.0:
        assessment = "medium"

    if not reasons:
        reasons.append("Tweet does not have strong characteristics typically associated with high retweet/quote rates (e.g., strong CTAs, unique info, highly engaging media).")

    return {"assessment": assessment, "reasons": reasons, "score": score}

def _assess_like_potential(tweet_data, text_info, media_info):
    """
    Assesses the potential for a tweet to receive likes based on heuristics.
    """
    reasons = []
    score = 0 # Simple scoring

    text_lower = tweet_data.get("text", "").lower()

    # 1. Positive Sentiment
    if text_info.get('basic_sentiment') == 'positive_leaning':
        reasons.append("Tweet has a positive sentiment, which generally encourages likes.")
        score += 1
    elif text_info.get('basic_sentiment') == 'neutral':
        reasons.append("Tweet sentiment is neutral.")
        score += 0.5 # Neutral is still generally fine for likes

    # 2. Media Presence
    if media_info.get("has_video"):
        reasons.append("Contains video, which can be engaging and likable.")
        score += 1
    elif media_info.get("has_image"):
        reasons.append("Contains image(s), often increasing likability.")
        score += 0.75

    # 3. Informative Content Keywords
    informative_keywords = ["guide", "tutorial", "learn", "discover", "tip", "facts", "interesting", "insight"]
    if any(keyword in text_lower for keyword in informative_keywords):
        reasons.append("Suggests informative content, which users often appreciate with a like.")
        score += 1

    # 4. Lack of Negativity/Controversy (already partially covered by sentiment)
    #    If sentiment is strongly negative, it might deter some likes, even if it drives other engagement.
    if text_info.get('basic_sentiment') == 'negative_leaning':
        reasons.append("Strongly negative sentiment might deter some casual likes, even if it provokes discussion.")
        score -= 0.5 # Slight negative impact on general 'likability'

    # 5. Readability & Clarity (not shouting, reasonable length)
    if text_info.get('shouting_detected'):
        reasons.append("Excessive capitalization ('shouting') can reduce likability.")
        score -= 0.5
    if text_info.get('length_assessment') == 'very_short' and not (media_info.get("has_video") or media_info.get("has_image")):
        reasons.append("Very short text without media might lack substance for a like unless very witty/impactful.")
        score -= 0.25

    # 6. Relatability/Humor Keywords (very basic)
    humor_keywords = ["funny", "lol", "haha", "so true", "mood", "hilarious", "joke"]
    if any(keyword in text_lower for keyword in humor_keywords):
        reasons.append("Contains keywords suggesting humor or relatability, often liked.")
        score += 1

    # 7. Not Overly Demanding (e.g. few strong CTAs for other actions)
    #    This is implicitly handled by not having strong CTAs for RTs/replies if those scores are low.

    assessment = "low"
    if score >= 2.0:
        assessment = "high"
    elif score >= 1.0:
        assessment = "medium"

    if not reasons:
        reasons.append("Tweet content does not strongly align with common drivers for likes (e.g., overt positive sentiment, highly engaging media, humor, direct informational value).")

    return {"assessment": assessment, "reasons": reasons, "score": score}


def _assess_video_view_potential(tweet_data, text_info, media_info):
    if not media_info.get('has_video'):
        return {"assessment": "n_a", "reasons": ["Tweet does not contain video."]}
    # TODO: Implement heuristics for video engagement
    # For now, if there's a video, we can give it a baseline 'medium' if text is not too short or negative.
    reasons = ["Video present."]
    score = 0.5
    if text_info.get('length_assessment') == 'very_short':
        reasons.append("Video accompanied by very short text, might lack context for views.")
        score -= 0.25
    if text_info.get('basic_sentiment') == 'negative_leaning':
        reasons.append("Video has negative leaning text, may deter some views depending on topic.")
        score -= 0.25

    assessment = "low"
    if score >= 0.5:
        assessment = "medium" # Hard to assess 'high' without knowing video content appeal

    return {"assessment": assessment, "reasons": reasons, "score": score}

def _assess_negative_feedback_potential(tweet_data, text_info, media_info):
    """
    Assesses the potential for a tweet to receive negative feedback based on heuristics.
    """
    reasons = []
    score = 0 # Higher score means higher negative feedback potential

    text_lower = tweet_data.get("text", "").lower()

    # 1. Strong Negative Sentiment
    if text_info.get('basic_sentiment') == 'negative_leaning':
        reasons.append("Tweet has a strong negative sentiment, which can sometimes lead to negative feedback if perceived as overly aggressive or offensive.")
        score += 1

    # 2. Offensive/Controversial Keywords (very basic example list)
    # In a real system, this would be far more sophisticated.
    offensive_controversial_keywords = ["idiot", "stupid", "moron", "garbage", "lies", "scam", "fake news"] # Add more with caution
    # Be careful with generic words that can be used in non-offensive contexts.
    # This list should be context-aware and possibly weighted in a real system.
    found_keywords = [kw for kw in offensive_controversial_keywords if kw in text_lower]
    if found_keywords:
        reasons.append(f"Contains potentially offensive/controversial keywords: {', '.join(found_keywords)}.")
        score += 1.5 * len(found_keywords) # Each keyword adds significantly

    # 3. "Shouting" / Aggressive Tone
    if text_info.get('shouting_detected'):
        reasons.append("Excessive capitalization ('shouting') can be perceived as aggressive and attract negative feedback.")
        score += 1

    # 4. Spammy Characteristics
    if media_info.get("num_hashtags", 0) > 5: # Arbitrary threshold for "too many"
        reasons.append(f"Uses {media_info['num_hashtags']} hashtags, which might appear spammy to some users.")
        score += 0.5
    if media_info.get("num_mentions", 0) > 3 and not tweet_data.get('is_reply'): # Many mentions in a non-reply might be spammy
        reasons.append(f"Uses {media_info['num_mentions']} mentions in a non-reply context, potentially perceived as spammy.")
        score += 0.5
    if media_info.get("num_links", 0) > 2:
        reasons.append(f"Contains {media_info['num_links']} links, which could be seen as spammy or overly promotional.")
        score += 0.5

    # 5. Directly Antagonistic Phrases (very basic)
    antagonistic_phrases = ["you are wrong", "shut up", "i hate you", "this is dumb"]
    if any(phrase in text_lower for phrase in antagonistic_phrases):
        reasons.append("Contains directly antagonistic phrases.")
        score += 2

    # 6. Sensitive Content Flag (from Twitter)
    if tweet_data.get('possibly_sensitive'):
        reasons.append("Tweet is flagged by Twitter as 'possibly sensitive', which might lead to negative feedback if users disagree with the content or flag.")
        score += 1

    assessment = "low"
    if score >= 3: # Higher score means higher negative feedback potential
        assessment = "high"
    elif score >= 1.5:
        assessment = "medium"

    if not reasons:
        reasons.append("Tweet does not exhibit strong indicators typically associated with high negative feedback.")

    return {"assessment": assessment, "reasons": reasons, "score": score}


def simulate_engagement_potential(tweet_data, text_info, media_info):
    """
    Simulates the potential for different types of engagement based on tweet characteristics.
    This is a heuristic-based qualitative assessment.
    """
    potential = {
        "reply_potential": _assess_reply_potential(tweet_data, text_info, media_info),
        "retweet_quote_potential": _assess_retweet_potential(tweet_data, text_info, media_info),
        "like_potential": _assess_like_potential(tweet_data, text_info, media_info),
        "video_view_potential": _assess_video_view_potential(tweet_data, text_info, media_info),
        "negative_feedback_potential": _assess_negative_feedback_potential(tweet_data, text_info, media_info),
    }
    return potential

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

    sample_tweet_data_shouting_links_video = {
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
        "media": [{"type": "video", "media_key": "v1"}], # Added video
        "is_reply": False,
    }

    import json

    print("--- Analyzing Reply from Verified User ---")
    analysis1 = analyze_tweet_against_algorithm(sample_tweet_data_reply_verified)
    print(json.dumps(analysis1, indent=2))

    print("\n--- Analyzing Shouting Tweet with Multiple Links & Video ---")
    analysis2 = analyze_tweet_against_algorithm(sample_tweet_data_shouting_links_video)
    print(json.dumps(analysis2, indent=2))

    print("\n--- Analyzing Empty Tweet Data ---")
    analysis3 = analyze_tweet_against_algorithm({})
    print(json.dumps(analysis3, indent=2))

    print("\n--- Analyzing None Tweet Data ---")
    analysis4 = analyze_tweet_against_algorithm(None)
    print(json.dumps(analysis4, indent=2))
