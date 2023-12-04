import re
import time
from github import Github
from github.GithubException import RateLimitExceededException, GithubException

class CodeGrimoire:
    def __init__(self, auth):
        self.total_lines = None
        self.github = Github(auth)
        self.user = self.github.get_user()
        self.language_stats = {}
        self.init_language_counters()
        self.extension_to_language = self.create_extension_to_language_map()

    @staticmethod
    def create_extension_to_language_map():
        return {
            "py": "Python",
            "js": "JavaScript",
            "jsx": "JavaScript",
            "ts": "TypeScript",
            "tsx": "TypeScript",
            "rb": "Ruby",
            "c": "C",
            "h": "C",
            "cpp": "C++",
            "cxx": "C++",
            "cc": "C++",
            "hpp": "C++",
            "hxx": "C++",
            "hh": "C++",
            "html": "HTML",
            "css": "CSS",
            "rs": "Rust",
            "go": "Go",
            "pl": "Perl",
            "sh": "Shell",
            "php": "PHP",
            "swift": "Swift",
            "r": "R",
            "sql": "SQL",
            "lua": "Lua",
            "java": "Java", # Add other mappings as necessary
        }
    def init_language_counters(self):
        self.total_lines = {
            "Python": {"code": 0, "comments": 0},
            "JavaScript": {"code": 0, "comments": 0},
            "TypeScript": {"code": 0, "comments": 0},
            "HTML": {"code": 0, "comments": 0},
            "CSS": {"code": 0, "comments": 0},
            "C": {"code": 0, "comments": 0},
            "C++": {"code": 0, "comments": 0},
            "C#": {"code": 0, "comments": 0},
            "Java": {"code": 0, "comments": 0},
            "Ruby": {"code": 0, "comments": 0},
            "Rust": {"code": 0, "comments": 0},
            "Go": {"code": 0, "comments": 0},
            "Perl": {"code": 0, "comments": 0},
            "Shell": {"code": 0, "comments": 0},
            "PHP": {"code": 0, "comments": 0},
            "Swift": {"code": 0, "comments": 0},
            "R": {"code": 0, "comments": 0},
            "SQL": {"code": 0, "comments": 0},
            "Lua": {"code": 0, "comments": 0},
        }

    def analyze_repos(self):
        for repo in self.fetch_relevant_repos():
            try:
                self.process_repository(repo)
            except RateLimitExceededException:
                print("Rate limit exceeded, waiting to reset...")
                self.check_rate_limit()
            except GithubException as e:
                print(f"GitHub Exception for repository {repo.name}: {e}")
            except Exception as e:
                print(f"Error processing repository {repo.name}: {e}")
        self.display_results()

    def fetch_relevant_repos(self):
        owned_repos = self.user.get_repos(type='owner')
        collaborated_repos = self.user.get_repos(type='collaborator')
        return set(owned_repos).union(set(collaborated_repos))

    def process_repository(self, repo):
        start_time = time.time()
        print(f"Analyzing repository: {repo.name}")
        self.check_rate_limit()
        try:
            contents = repo.get_contents("")
            self.process_contents(contents, repo, start_time)
        except Exception as e:
            print(f"Error processing repository {repo.name}: {e}")

    def process_contents(self, contents, repo, start_time):
        for file_content in contents:
            if time.time() - start_time > 60:
                print(f"Skipping repository {repo.name} due to timeout after 60 seconds")
                break

            if file_content.type == "dir":
                self.process_contents(repo.get_contents(file_content.path), repo, start_time)
            elif file_content.type == "file":
                code_lines, comment_lines = self.parse_file(file_content)
                file_extension = file_content.name.split('.')[-1].lower()

                language = self.extension_to_language.get(file_extension)
                if language and language in self.total_lines:
                    self.total_lines[language]["code"] += code_lines
                    self.total_lines[language]["comments"] += comment_lines
                else:
                    print(f"Unknown file type or language mapping missing for: {file_extension}")

    def parse_file(self, file_content):
        file_type = file_content.name.split('.')[-1]
        parsers = {
            "py": self.parse_python_file, # python files
            "js": self.parse_javascript_file, # javascript files
            "jsx": self.parse_javascript_file, # javascript react files
            "ts": self.parse_typescript_file, # typescript files
            "tsx": self.parse_typescript_file, # typescript react files
            "rb": self.parse_ruby_file, # ruby files
            "c": self.parse_c_file, # c source files
            "h": self.parse_c_file,  # C header files
            "cpp": self.parse_cpp_file, # c++ files
            "cxx": self.parse_cpp_file, # c++ files
            "cc": self.parse_cpp_file, # c++ files
            "hpp": self.parse_cpp_file,  # C++ header files
            "hxx": self.parse_cpp_file, # c++ files
            "hh": self.parse_cpp_file, # c++ files
            "html": self.parse_html_file, # html files
            "css": self.parse_css_file, # css files
            "rs": self.parse_rust_file,  # Rust parser
            "go": self.parse_go_file,  # Go parser
            "pl": self.parse_perl_file,  # Perl parser
            "sh": self.parse_shell_file,  # script parser
            "php": self.parse_php_file,  # PHP parser
            "swift": self.parse_swift_file,  # Swift parser
            "r": self.parse_r_file,  # R parser
            "sql": self.parse_sql_file,  # SQL parser
            "lua": self.parse_lua_file,  # Lua parser
        }
        if file_type in parsers:
            result = parsers[file_type](file_content.decoded_content.decode("utf-8"))
            if file_type == 'py':
                return result[1], result[2]  # Return only code lines and comment lines for Python
            elif isinstance(result, tuple) and len(result) == 2:
                return result
            else:
                raise ValueError(f"Parser for {file_type} did not return a valid tuple")
        return 0, 0

    @staticmethod
    def parse_python_file(file_content):
        imports = set()
        code_lines = 0
        comment_lines = 0
        inside_multiline_comment = False

        for line in file_content.splitlines():
            stripped_line = line.strip()

            # Skip blank lines
            if not stripped_line:
                continue

            # Detect and handle multi-line comment blocks
            if stripped_line.startswith("'''") or stripped_line.startswith('"""'):
                inside_multiline_comment = not inside_multiline_comment
                comment_lines += 1
                continue

            if inside_multiline_comment or stripped_line.startswith("#"):
                comment_lines += 1
                continue

            # Count as a code line if it's not a comment or blank
            code_lines += 1

            # Parsing for import statements
            if re.match(r'^import (\w+)|^from (\w+) import', stripped_line):
                imports.add(re.match(r'^import (\w+)|^from (\w+) import', stripped_line).group(1) or re.match(
                    r'^import (\w+)|^from (\w+) import', stripped_line).group(2))

        return (imports, code_lines, comment_lines)

    @staticmethod
    def parse_c_file(file_content):
        code_lines = 0
        comment_lines = 0
        inside_block_comment = False

        for line in file_content.splitlines():
            stripped_line = line.strip()

            # Skip blank lines
            if not stripped_line:
                continue

            # Handle block comments
            if stripped_line.startswith("/*") or inside_block_comment:
                inside_block_comment = True
                comment_lines += 1
                if "*/" in stripped_line:
                    inside_block_comment = False
                continue

            # Handle single-line comments
            if stripped_line.startswith("//"):
                comment_lines += 1
                continue

            # Count as a code line if it's not a comment
            code_lines += 1

        return code_lines, comment_lines

    @staticmethod
    def parse_rust_file(file_content):
        code_lines = 0
        comment_lines = 0
        inside_block_comment = False

        for line in file_content.splitlines():
            stripped_line = line.strip()

            # Handle block comments
            if stripped_line.startswith("/*") or inside_block_comment:
                inside_block_comment = True
                comment_lines += 1
                if "*/" in stripped_line:
                    inside_block_comment = False
                continue

            # Handle single-line comments
            if stripped_line.startswith("//"):
                comment_lines += 1
                continue

            # Non-empty and non-comment line is considered as a code line
            if stripped_line and not inside_block_comment:
                code_lines += 1

        return code_lines, comment_lines

    @staticmethod
    def parse_go_file(file_content):
        code_lines = 0
        comment_lines = 0
        inside_block_comment = False

        for line in file_content.splitlines():
            stripped_line = line.strip()

            # Handle block comments
            if stripped_line.startswith("/*") or inside_block_comment:
                inside_block_comment = True
                comment_lines += 1
                if "*/" in stripped_line:
                    inside_block_comment = False
                continue

            # Handle single-line comments
            if stripped_line.startswith("//"):
                comment_lines += 1
                continue

            # Non-empty and non-comment line is considered as a code line
            if stripped_line and not inside_block_comment:
                code_lines += 1

        return code_lines, comment_lines

    @staticmethod
    def parse_shell_file(file_content):
        code_lines = 0
        comment_lines = 0

        for line in file_content.splitlines():
            stripped_line = line.strip()

            # Handle single-line comments
            if stripped_line.startswith("#"):
                comment_lines += 1
                continue

            # Non-empty line is considered as a code line
            if stripped_line:
                code_lines += 1

        return code_lines, comment_lines

    @staticmethod
    def parse_swift_file(file_content):
        code_lines = 0
        comment_lines = 0
        inside_block_comment = False

        for line in file_content.splitlines():
            stripped_line = line.strip()

            # Handle block comments
            if stripped_line.startswith("/*") or inside_block_comment:
                inside_block_comment = True
                comment_lines += 1
                if "*/" in stripped_line:
                    inside_block_comment = False
                continue

            # Handle single-line and documentation comments
            if stripped_line.startswith("//"):
                comment_lines += 1
                continue

            # Non-empty and non-comment line is considered as a code line
            if stripped_line and not inside_block_comment:
                code_lines += 1

        return code_lines, comment_lines

    @staticmethod
    def parse_lua_file(file_content):
        code_lines = 0
        comment_lines = 0
        inside_block_comment = False

        for line in file_content.splitlines():
            stripped_line = line.strip()

            # Handle block comments
            if stripped_line.startswith("--[[") or inside_block_comment:
                inside_block_comment = True
                comment_lines += 1
                if stripped_line.endswith("--]]"):
                    inside_block_comment = False
                continue

            # Handle single-line comments
            if stripped_line.startswith("--") and not stripped_line.startswith("--[["):
                comment_lines += 1
                continue

            # Non-empty and non-comment line is considered as a code line
            if stripped_line and not inside_block_comment:
                code_lines += 1

        return code_lines, comment_lines

    @staticmethod
    def parse_r_file(file_content):
        code_lines = 0
        comment_lines = 0

        for line in file_content.splitlines():
            stripped_line = line.strip()

            # Handle single-line comments
            if stripped_line.startswith("#"):
                comment_lines += 1
                continue

            # Non-empty line is considered as a code line
            if stripped_line:
                code_lines += 1

        return code_lines, comment_lines

    @staticmethod
    def parse_sql_file(file_content):
        code_lines = 0
        comment_lines = 0
        inside_block_comment = False

        for line in file_content.splitlines():
            stripped_line = line.strip()

            # Handle block comments
            if stripped_line.startswith("/*") or inside_block_comment:
                inside_block_comment = True
                comment_lines += 1
                if "*/" in stripped_line:
                    inside_block_comment = False
                continue

            # Handle single-line comments
            if stripped_line.startswith("--"):
                comment_lines += 1
                continue

            # Non-empty and non-comment line is considered as a code line
            if stripped_line and not inside_block_comment:
                code_lines += 1

        return code_lines, comment_lines

    @staticmethod
    def parse_php_file(file_content):
        code_lines = 0
        comment_lines = 0
        inside_block_comment = False

        for line in file_content.splitlines():
            stripped_line = line.strip()

            # Handle block comments
            if stripped_line.startswith("/*") or inside_block_comment:
                inside_block_comment = True
                comment_lines += 1
                if "*/" in stripped_line:
                    inside_block_comment = False
                continue

            # Handle single-line comments
            if stripped_line.startswith("//") or stripped_line.startswith("#"):
                comment_lines += 1
                continue

            # Non-empty and non-comment line is considered as a code line
            if stripped_line and not inside_block_comment:
                code_lines += 1

        return code_lines, comment_lines

    @staticmethod
    def parse_perl_file(file_content):
        code_lines = 0
        comment_lines = 0

        for line in file_content.splitlines():
            stripped_line = line.strip()

            # Handle single-line comments
            if stripped_line.startswith("#"):
                comment_lines += 1
                continue

            # Non-empty line is considered as a code line
            if stripped_line:
                code_lines += 1

        return code_lines, comment_lines

    @staticmethod
    def parse_javascript_file(file_content):
        code_lines = 0
        comment_lines = 0
        inside_block_comment = False

        for line in file_content.splitlines():
            stripped_line = line.strip()

            # Skip blank lines
            if not stripped_line:
                continue

            # Handle block comments
            if stripped_line.startswith("/*") or inside_block_comment:
                inside_block_comment = True
                comment_lines += 1
                if "*/" in stripped_line:
                    inside_block_comment = False
                continue

            # Handle single-line comments
            if stripped_line.startswith("//"):
                comment_lines += 1
                continue

            # Count as a code line if it's not a comment
            code_lines += 1

        return code_lines, comment_lines

    def parse_typescript_file(self, file_content):
        return self.parse_javascript_file(file_content)

    def parse_cpp_file(self, file_content):
        return self.parse_c_file(file_content)

    def parse_java_file(self, file_content):
        return self.parse_c_file(file_content)  # or parse_cpp_file, if they share the same logic

    def parse_csharp_file(self, file_content):
        return self.parse_c_file(file_content)  # reusing the C parser logic

    @staticmethod
    def parse_html_file(file_content):
        code_lines = 0
        comment_lines = 0
        inside_comment = False

        for line in file_content.splitlines():
            stripped_line = line.strip()

            if stripped_line.startswith("<!--"):
                inside_comment = True

            if inside_comment:
                comment_lines += 1
                if stripped_line.endswith("-->"):
                    inside_comment = False
                continue

            if stripped_line and not inside_comment:
                code_lines += 1

        return code_lines, comment_lines

    @staticmethod
    def parse_css_file(file_content):
        code_lines = 0
        comment_lines = 0
        inside_comment = False

        for line in file_content.splitlines():
            stripped_line = line.strip()

            if stripped_line.startswith("/*"):
                inside_comment = True

            if inside_comment:
                comment_lines += 1
                if stripped_line.endswith("*/"):
                    inside_comment = False
                continue

            if stripped_line and not inside_comment:
                code_lines += 1

        return code_lines, comment_lines

    @staticmethod
    def parse_ruby_file(file_content):
        code_lines = 0
        comment_lines = 0
        inside_multiline_comment = False

        for line in file_content.splitlines():
            stripped_line = line.strip()

            if stripped_line.startswith("=begin"):
                inside_multiline_comment = True
                comment_lines += 1
                continue

            if stripped_line.startswith("=end"):
                inside_multiline_comment = False
                comment_lines += 1
                continue

            if inside_multiline_comment or stripped_line.startswith("#"):
                comment_lines += 1
                continue

            if stripped_line:  # Non-empty line
                code_lines += 1

        return code_lines, comment_lines


    def check_rate_limit(self):
        rate_limit = self.github.get_rate_limit()
        remaining = rate_limit.core.remaining
        reset_time = rate_limit.core.reset
        if remaining < 10:
            pause_duration = (reset_time - time.time()).total_seconds() + 10
            print(f"Pausing for {pause_duration} seconds due to rate limit...")
            time.sleep(pause_duration)

    def display_results(self):
        total_lines = sum(sum(lang.values()) for lang in self.total_lines.values())
        for lang, counts in self.total_lines.items():
            code_lines = counts["code"]
            comment_lines = counts["comments"]
            percentage = (code_lines / total_lines) * 100 if total_lines > 0 else 0
            print(f"{lang}: Code lines - {code_lines}, Comment lines - {comment_lines} ({percentage:.2f}%)")

# Usage
auth = "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"
analyzer = CodeGrimoire(auth)
analyzer.analyze_repos()