from data_fetcher import get_tweet_details
from analysis_engine import analyze_tweet_against_algorithm
import json # For pretty printing the raw dictionary if needed, but we'll do custom print

def display_analysis_report(analysis_results):
    """
    Displays the analysis results in a user-friendly format.
    """
    if not analysis_results or analysis_results.get("error"):
        print("\n--- Analysis Error ---")
        print(analysis_results.get("error", "Unknown error during analysis."))
        return

    print("\n--- Twitter Post Analysis Report ---")
    print(f"Tweet ID: {analysis_results.get('tweet_id', 'N/A')}")
    print(f"Tweet Text: \"{analysis_results.get('tweet_text', '')}\"")
    print("-" * 30)

    if 'text_analysis' in analysis_results:
        print("\n[Text Analysis]")
        ta = analysis_results['text_analysis']
        print(f"  Length: {ta.get('length')} characters ({ta.get('length_assessment', '')})")
        print(f"  Capitalization: {ta.get('caps_percentage')*100:.0f}% uppercase")
        if ta.get('shouting_detected'):
            print("    Warning: High proportion of capital letters (potential 'shouting').")
        print(f"  Basic Sentiment: {ta.get('basic_sentiment', 'N/A')}")

        if 'readability' in ta:
            readability = ta['readability']
            print(f"  Readability Assessment: {readability.get('qualitative_assessment', 'N/A')}")
            print(f"    Avg. Sentence Length: {readability.get('average_sentence_length', 0.0):.1f} words")
            print(f"    Avg. Word Length: {readability.get('average_word_length', 0.0):.2f} chars")
            if "notes" in readability and readability["notes"]: # Optional: display notes if needed for debugging, or specific advice from readability
                 # print(f"    Readability Notes: {readability['notes']}")
                 pass

        if 'notes_on_text_score' in ta: # Keep this general note
            print(f"  Note on Text Score: {ta['notes_on_text_score']}")

    if 'media_analysis' in analysis_results:
        print("\n[Media & Entities Analysis]")
        ma = analysis_results['media_analysis']
        if ma.get('has_image'):
            print("  Contains Image(s)")
        if ma.get('has_video'):
            print("  Contains Video/GIF")
        if not ma.get('has_image') and not ma.get('has_video'):
            print("  No direct images or videos detected in this tweet object.")
        print(f"  Number of Media Items: {ma.get('num_media_items', 0)}")
        print(f"  Has Links: {'Yes' if ma.get('has_links') else 'No'} (Count: {ma.get('num_links', 0)})")
        print(f"  Hashtags: {ma.get('num_hashtags', 0)}")
        print(f"  Mentions: {ma.get('num_mentions', 0)}")
        if 'notes_on_media' in ma:
            print(f"  Note: {ma['notes_on_media']}")

    if analysis_results.get('factors'):
        print("\n[Key Algorithmic Factors Noted]")
        for factor_info in analysis_results['factors']:
            factor_type = factor_info.get('type', 'neutral').upper()
            print(f"  - ({factor_type}) {factor_info.get('factor', '')}")
            print(f"    Implication: {factor_info.get('implication', '')}")

    # Placeholders for future analysis sections
    if 'engagement_potential' in analysis_results:
        print("\n[Engagement Potential Simulation]")
        ep = analysis_results['engagement_potential']
        for potential_type, details in ep.items():
            assessment = details.get('assessment', 'N/A').capitalize()
            score_info = f" (Score: {details.get('score', 'N/A')})" if 'score' in details else "" # Optional: display score if useful
            # For this report, we'll focus on assessment and reasons
            print(f"  {potential_type.replace('_', ' ').capitalize()}: {assessment}")
            if details.get('reasons'):
                for reason in details['reasons']:
                    print(f"    - {reason}")
            else:
                print("    - No specific reasons provided.")

    if 'author_analysis_notes' in analysis_results: # Keep other placeholders
         print(f"\n[Author Analysis Notes]\n  {analysis_results['author_analysis_notes']}")
    if 'algorithm_factors_notes' in analysis_results:
        print(f"\n[Algorithm Factors Notes]\n  {analysis_results['algorithm_factors_notes']}")


    if analysis_results.get('recommendations'):
        print("\n[Suggestions for Improvement]")
        for rec in analysis_results['recommendations']:
            print(f"  - {rec}")

    if analysis_results.get('overall_assessment_notes'):
        print("\n[Overall Assessment Notes]")
        for note in analysis_results['overall_assessment_notes']:
            print(f"  - {note}")

    print("\n--- End of Report ---")


def run_analyzer_cli():
    """
    Runs a simple command-line interface for the Twitter Post Analyzer.
    """
    print("--- Twitter Post Analyzer ---")
    print("Enter a Twitter post URL or Tweet ID to analyze.")
    print("Type 'quit' or 'exit' to stop.")

    while True:
        user_input = input("\nEnter Tweet URL/ID: ").strip()

        if user_input.lower() in ["quit", "exit"]:
            print("Exiting analyzer.")
            break

        if not user_input:
            print("Please enter a URL or ID.")
            continue

        print(f"\nFetching details for: {user_input} ...")
        tweet_data = get_tweet_details(user_input)

        if tweet_data:
            # print("\n--- Raw Tweet Data Fetched (for debugging) ---")
            # print(json.dumps(tweet_data, indent=2, ensure_ascii=False))
            # print("-" * 30)

            print("Analyzing tweet against algorithm factors...")
            analysis_results = analyze_tweet_against_algorithm(tweet_data)
            display_analysis_report(analysis_results)
        else:
            print("Could not retrieve tweet data. Please check the URL/ID or your API credentials.")

        print("\n" + "=" * 40 + "\n")


if __name__ == "__main__":
    # Before running, ensure you have your BEARER_TOKEN set in config.py
    try:
        from config import BEARER_TOKEN
        if "YOUR_BEARER_TOKEN" in BEARER_TOKEN: # Check if it's still the placeholder
            print("***********************************************************************************")
            print("REMINDER: Please replace 'YOUR_BEARER_TOKEN' in config.py with your actual token.")
            print("The tool will likely fail to fetch live tweet data until this is done.")
            print("***********************************************************************************\n")
    except ImportError:
        print("ERROR: config.py not found. Please ensure it exists with your API credentials.")
        # Optionally exit here if config is critical for any operation
    except AttributeError:
        print("ERROR: BEARER_TOKEN not found in config.py. Please ensure it is set.")
        # Optionally exit

    run_analyzer_cli()
