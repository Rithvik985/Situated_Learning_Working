#!/usr/bin/env python3
"""
Minimal AI Detection Test - Run this to quickly test AI detection
Usage: python quick_test_ai.py
"""

import requests
import json
from colorama import init, Fore, Back, Style

init(autoreset=True)

def main():
    print(f"\n{Fore.CYAN}{Back.BLACK}{'='*60}")
    print(f"  AI DETECTION QUICK TEST")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    backend_url = "http://localhost:8000"
    
    # Step 1: Get submissions
    print(f"{Fore.YELLOW}[1/3]{Style.RESET_ALL} Fetching submissions...")
    try:
        resp = requests.get(f"{backend_url}/api/faculty/pending-submissions", timeout=5)
        resp.raise_for_status()
        submissions = resp.json()
    except Exception as e:
        print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}Hint: Is backend running? Try: python start_evaluation_server.py{Style.RESET_ALL}")
        return False
    
    if not submissions:
        print(f"{Fore.RED}✗ No pending submissions{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}Hint: Go to Student Workflow and submit an assignment first{Style.RESET_ALL}")
        return False
    
    print(f"{Fore.GREEN}✓{Style.RESET_ALL} Found {len(submissions)} submission(s)")
    
    # Step 2: Run AI detection
    sub_id = submissions[0]['id']
    print(f"\n{Fore.YELLOW}[2/3]{Style.RESET_ALL} Running AI detection on: {sub_id}")
    try:
        resp = requests.post(f"{backend_url}/api/faculty/submissions/{sub_id}/detect-ai", json={}, timeout=120)
        resp.raise_for_status()
        results = resp.json()
    except Exception as e:
        print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
        return False
    
    print(f"{Fore.GREEN}✓{Style.RESET_ALL} Analysis complete")
    
    # Step 3: Display results
    print(f"\n{Fore.YELLOW}[3/3]{Style.RESET_ALL} Results:")
    print()
    
    ai_prob = results['ai_detection_results']['ai_probability']
    risk = results['risk_assessment']['risk_level']
    
    # Color-code risk level
    if risk == "High":
        risk_color = Fore.RED
    elif risk == "Medium":
        risk_color = Fore.YELLOW
    else:
        risk_color = Fore.GREEN
    
    print(f"  AI Probability:  {ai_prob:.1%}")
    print(f"  Risk Level:      {risk_color}{risk}{Style.RESET_ALL}")
    print(f"  Text Length:     {results['submission_stats']['text_length']:,} chars")
    print(f"  Word Count:      {results['submission_stats']['word_count']:,} words")
    
    print(f"\n  Recommendation:")
    for rec in results['recommendations'][:2]:
        print(f"    • {rec}")
    
    print(f"\n{Fore.CYAN}{Back.BLACK}{'='*60}")
    print(f"  SUCCESS - Results saved to ai_detection_results.json")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    # Save results
    with open("ai_detection_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
        exit(1)
