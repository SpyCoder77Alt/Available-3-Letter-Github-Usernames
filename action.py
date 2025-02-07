#!/usr/bin/python3
import itertools
import string
import requests
import time
from multiprocessing import Pool
from datetime import datetime
import tqdm

# --- CONFIGURATION ---
ALLOWED_CHARS = string.ascii_lowercase + string.digits  # 36 characters.
MIN_LENGTH = 1
MAX_LENGTH = 3  # Only 3-letter usernames.
MAX_RETRIES = 3
REQUEST_DELAY = 0.1  # Delay (in seconds) between retries
CONCURRENCY = 10    # Lower the concurrency for GitHub Actions

def generate_usernames(min_length, max_length):
    """Generate all possible usernames with the given lengths."""
    for length in range(min_length, max_length + 1):
        for comb in itertools.product(ALLOWED_CHARS, repeat=length):
            yield ''.join(comb)

def request(user):
    """
    Attempt a GET request to https://github.com/<username> with retries.
    Returns the HTTP status code, or 500 if it fails after retries.
    """
    user = user.strip()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(f"https://github.com/{user}", timeout=10)
            return response.status_code
        except Exception as e:
            print(f"[{user}] Attempt {attempt} failed with error: {e}")
            time.sleep(REQUEST_DELAY)
    return 500  # After MAX_RETRIES, give up

def check(username):
    """
    Check the given username on GitHub.
    Returns a dict with its status:
      - "available" if status code is 404,
      - "taken" if status code is 200 (or other valid code),
      - "unchecked" if the request failed.
    """
    code = request(username)
    if code == 500:
        return {"status": "unchecked", "username": username}
    elif code == 404:
        return {"status": "available", "username": username}
    else:
        return {"status": "taken", "username": username}

def main():
    # Generate all 3-letter usernames.
    usernames = list(generate_usernames(MIN_LENGTH, MAX_LENGTH))
    total = len(usernames)
    unchecked = set(usernames)
    available = []
    taken = []

    print(f"Checking {total} usernames...")

    pool = Pool(processes=CONCURRENCY)
    try:
        for result in tqdm.tqdm(pool.imap_unordered(check, usernames), total=total):
            status = result["status"]
            if status != "unchecked":
                unchecked.discard(result["username"])
            if status == "available":
                available.append(result["username"])
            elif status == "taken":
                taken.append(result["username"])
    finally:
        pool.close()
        pool.join()

    # Update the README with the available usernames.
    with open("README.md", "w") as f:
        f.write("# Available 3-Letter GitHub Usernames\n\n")
        f.write("This README is automatically updated daily with the list of available 3-letter GitHub usernames.\n\n")
        if available:
            for user in sorted(available):
                f.write(f"- {user}\n")
        else:
            f.write("No available usernames found.\n")

    print(f"Finished. Available: {len(available)} | Taken: {len(taken)} | Unchecked: {len(unchecked)}.")

if __name__ == "__main__":
    main()
