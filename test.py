import sys
import requests
from time import time
from difflib import SequenceMatcher
from bs4 import BeautifulSoup

def load_url_multiple_times(url, num_trials=3, timeout_param=120, set_name="", name=""):
    """
    Load a URL multiple times to calculate the average loading time and display progress.
    Includes set and name information in the output for clarity.
    """
    total_time = 0
    successful_trials = 0
    print(f"\n[{set_name} | {name}] Loading URL {url} with {num_trials} trials...")
    for trial in range(1, num_trials+1):
        try:
            start_time = time()
            response = requests.get(url, timeout=timeout_param)
            elapsed_time = time() - start_time
            response.raise_for_status()
            total_time += elapsed_time
            successful_trials += 1
            print(f"[{set_name} | {name}] Trial {trial}: Success, Time = {elapsed_time:.2f} seconds")
        except requests.exceptions.RequestException as e:
            print(f"[{set_name} | {name}] Trial {trial}: Failed to load {url}, Error: {e}")
    if successful_trials > 0:
        average_time = total_time / successful_trials
        return response.text, average_time
    else:
        return "", 0

def compare_pages(content1, content2, set_name="", name1="", name2=""):
    """
    Compare the text content of two web pages, compute the similarity ratio, and include set and name information in output.
    """
    soup1 = BeautifulSoup(content1, 'html.parser')
    text1 = soup1.get_text()
    soup2 = BeautifulSoup(content2, 'html.parser')
    text2 = soup2.get_text()
    
    similarity = SequenceMatcher(None, text1, text2).ratio()
    print(f"[{set_name}] Comparing {name1} vs {name2}, Similarity = {similarity:.2%}")
    return similarity

def read_urls(filename):
    """
    Read URLs, names, and descriptions from a file, skipping lines starting with '#'.
    """
    with open(filename, 'r') as file:
        lines = [line.strip() for line in file if not line.strip().startswith('#')]
    
    urls = []
    names = []
    sets = []
    current_set = ""
    current_name = ""
    for line in lines:
        if line.startswith("Set="):
            current_set = line.split("=", 1)[1].strip()
        elif line.startswith("Name="):
            current_name = line.split("=", 1)[1].strip()
        elif line.startswith("Url="):
            urls.append(line.split("=", 1)[1].strip())
            names.append(current_name)
            sets.append(current_set)
    return sets, names, urls

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]  # Input file is specified on the command line
    sets, names, urls = read_urls(input_file)

    print("\n===============================================================")
    results = []
    for url, set_name, name in zip(urls, sets, names):
        content, avg_load_time = load_url_multiple_times(url, set_name=set_name, name=name)
        results.append((content, avg_load_time, set_name, name))

    print("\n===============================================================")
    for i, (content, avg_load_time, set_name, name) in enumerate(results):
        if content:
            print(f"[{set_name} | {name}] Average time to load: {avg_load_time:.2f} seconds")
        else:
            print(f"[{set_name} | {name}] Failed to load")

    # Example: Comparing first two URLs in the same set
    print("\n===============================================================")
    for set_name in set(sets):
        indices = [i for i, s in enumerate(sets) if s == set_name]
        if len(indices) > 1:
            sim = compare_pages(results[indices[0]][0], results[indices[1]][0], set_name, names[indices[0]], names[indices[1]])
            print(f"[{set_name}] Similarity between {names[indices[0]]} and {names[indices[1]]}: {sim:.2%}")
