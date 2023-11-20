import re
import time
from github import Github
from github.GithubException import RateLimitExceededException, GithubException

def parse_python_imports(file_content):
    """
    Parses Python file content and returns a set of imported modules.
    """
    imports = set()
    for line in file_content.splitlines():
        match = re.match(r'^import (\w+)|^from (\w+) import', line)
        if match:
            imports.add(match.group(1) or match.group(2))
    return imports

def check_rate_limit(github_client):
    """
    Check the remaining rate limit and pause if it's too low.
    """
    rate_limit = github_client.get_rate_limit()
    remaining = rate_limit.core.remaining
    reset_time = rate_limit.core.reset
    if remaining < 10:  # Arbitrary low limit
        pause_duration = (reset_time - datetime.datetime.utcnow()).total_seconds() + 10
        print(f"Pausing for {pause_duration} seconds due to rate limit...")
        time.sleep(pause_duration)

# Replace 'your_token' with your actual GitHub personal access token
token = Github("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")

user = token.get_user()
repos = user.get_repos()

language_stats = {}
python_imports = set()

for repo in repos:
    try:
        print(f"Analyzing repository: {repo.name}")
        check_rate_limit(token)  # Check rate limit before processing each repository

        languages = repo.get_languages()
        for language, lines in languages.items():
            if language in language_stats:
                language_stats[language] += lines
            else:
                language_stats[language] = lines

        if "Python" in languages:
            contents = repo.get_contents("")
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                elif file_content.name.endswith(".py"):
                    raw_data = file_content.decoded_content.decode("utf-8")
                    imports = parse_python_imports(raw_data)
                    python_imports.update(imports)

    except RateLimitExceededException as e:
        print("Rate limit exceeded, waiting to reset...")
        check_rate_limit(token)  # This will pause the script until the rate limit resets

    except GithubException as e:
        print(f"GitHub Exception for repository {repo.name}: {e}")

    except Exception as e:
        print(f"Error processing repository {repo.name}: {e}")

# Calculate total lines of code
total_lines = sum(language_stats.values())

# Calculate percentage usage for each language
for language, lines in language_stats.items():
    percentage = (lines / total_lines) * 100
    print(f"{language}: {lines} lines ({percentage:.2f}%)")

# Print most commonly imported Python modules
print("Most commonly imported Python modules:")
for module in python_imports:
    print(module)
