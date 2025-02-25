from dataclasses import dataclass

@dataclass
class GitHubProject:
    name: str
    url: str
    description: str

@dataclass
class Project:
    name: str
    description: str
    url: str

@dataclass
class ParsedResumeResponse:
    found_all_links: bool
    github_username: str
    projects: list[Project]
