#!/usr/bin/python3
import itertools
import string
import requests
from multiprocessing import Pool
from datetime import datetime
import tqdm

# --- CONFIGURATION ---
ALLOWED_CHARS = string.ascii_lowercase + string.digits  # 36 characters.
MIN_LENGTH = 3
MAX_LENGTH = 3  # Only 3-letter usernames.

def generate_usernames(min_length, max_length):
    """
    Generate all possible usernames with the given lengths.
    For 3-letter usernames with 36 characters, there will be 36^3 combinations.
    """
    for length in range(min_length, max_length + 1):
        for comb in itertools.product(ALLOWED_CHARS, repeat=length):
            yield ''.join(comb)

def request(user):
    """
    Return the status code for https://github.com/<username>.
    404 indicates the username is available.
    """
    user = user.strip()
    try:
        response = requests.get(f"https://github.com/{user}", timeout=10)
        return response.status_code
    except Exception:
        return 500  # Mark as 'unchecked' in case of error.

def check(username):
    """
    Check a username and return a dict with its status.
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

    # Use a multiprocessing pool to check usernames concurrently.
    pool = Pool(processes=50)  # Adjust concurrency if needed.
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

    # Update the README file with the available usernames.
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
