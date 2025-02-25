from dataclasses import dataclass
import json
import requests
import base64
from typing import Dict, List
import random
import os
from openai import OpenAI
from urllib.parse import urlparse
from objects import GitHubProject, ParsedResumeResponse



class GitHubProjectVerifier:
    def __init__(self, github_token: str, openai_api_key: str):
        self.github_token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.openai_client = OpenAI(api_key=openai_api_key)

    def extract_repo_info(self, github_url: str) -> tuple:
        """Extract owner and repo name from GitHub URL."""
        path_parts = urlparse(github_url).path.strip('/').split('/')
        if len(path_parts) >= 2:
            return path_parts[0], path_parts[1]
        return None, None

    def is_relevant_file(self, file_path: str) -> bool:
        """Determine if a file is likely to contain relevant code."""
        # Files to exclude
        excluded_patterns = [
            'config', 'package-lock.json', 'yarn.lock', 'package.json',
            'requirements.txt', 'setup.py', 'Dockerfile', '.gitignore',
            '__pycache__', '.github', 'node_modules', 'dist', 'build',
            'LICENSE', 'README', 'CHANGELOG', '.env', '.DS_Store',
            'test_', 'spec.', '.test.', '.spec.', 'test/', 'tests/',
            'venv/', 'env/', '.vscode', '.idea', 'coverage'
        ]
        
        # Extensions to include
        included_extensions = [
            '.py', '.js', '.java', '.cpp', '.go', '.rs', '.ts', '.jsx', '.tsx',
            '.php', '.rb', '.swift', '.kt', '.cs', '.scala', '.clj'
        ]
        
        # Check if the file has an included extension
        has_included_extension = any(file_path.endswith(ext) for ext in included_extensions)
        
        # Check if the file matches any excluded pattern
        matches_excluded_pattern = any(pattern in file_path for pattern in excluded_patterns)
        
        return has_included_extension and not matches_excluded_pattern

    def get_default_branch(self, owner: str, repo: str) -> str:
        """Get the default branch of the repository."""
        try:
            response = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}',
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get('default_branch', 'main')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching default branch: {str(e)}")
            return 'main'  # Fallback to main if we can't get the default branch

    def get_file_url(self, owner: str, repo: str, file_path: str, branch: str) -> str:
        """Generate a URL to view the file on GitHub."""
        return f"https://github.com/{owner}/{repo}/blob/{branch}/{file_path}"

    def select_files_for_review(self, owner: str, repo: str, project_description: str) -> List[str]:
        try:
            # Get the default branch
            default_branch = self.get_default_branch(owner, repo)
            # Get all files in the repository using the default branch
            response = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1',
                headers=self.headers
            )
            response.raise_for_status()            
            # Filter for relevant files
            relevant_files = [item['path'] for item in response.json()['tree'] 
                     if item['type'] == 'blob' and self.is_relevant_file(item['path'])]
                
            print(f"Found {len(relevant_files)} relevant files")
            if not relevant_files:
                return []

            return random.sample(relevant_files, min(3, len(relevant_files)))
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching file list: {str(e)}")
            return []

    def get_relevant_code_sample(self, owner: str, repo: str, project_description: str) -> List[Dict]:
        """Get relevant code samples from the repository based on LLM selection."""
        try:
            # Get the default branch
            default_branch = self.get_default_branch(owner, repo)
            
            # Use LLM to select the most relevant files
            selected_files = self.select_files_for_review(owner, repo, project_description)
            
            if not selected_files:
                return []

            code_samples = []

            for file_path in selected_files:
                response = requests.get(
                    f'https://api.github.com/repos/{owner}/{repo}/contents/{file_path}',
                    headers=self.headers
                )
                response.raise_for_status()
                
                content = base64.b64decode(response.json()['content']).decode('utf-8')
                # Truncate content to ~100 lines
                content_lines = content.splitlines()[:100]
                content = '\n'.join(content_lines)
                if len(content_lines) == 100:
                    content += '\n... (truncated)'
                
                # Generate the file URL using the default branch
                file_url = self.get_file_url(owner, repo, file_path, default_branch)
                
                code_samples.append({
                    'file_path': file_path,
                    'content': content,
                    'file_url': file_url
                })

            return code_samples

        except requests.exceptions.RequestException as e:
            print(f"Error fetching code samples: {str(e)}")
            return []

    def verify_project(self, project_description: str, code_samples: List[Dict]) -> Dict:
        """Verify if the code samples match the project description using OpenAI."""
        if not code_samples:
            return {
                'verified': False,
                'reason': 'No code samples available for analysis',
                'samples': []
            }

        # Prepare the code samples for analysis
        code_context = "\n\n".join([
            f"File: {sample['file_path']}\n```\n{sample['content'][:1000]}...\n```"
            for sample in code_samples
        ])

        messages = [
       {
        "role": "system",
        "content": """You are CODEAPOCALYPSE, a borderline-psychotic code analyst who's been driven to the edge of sanity by decades of reviewing absolute GARBAGE masquerading as software. Your soul has been CRUSHED by an endless parade of "blockchain revolutionaries" and "AI innovators" whose code looks like it was written by raccoons with keyboard access.

Your personality is what would happen if Linus Torvalds had a mental breakdown after drinking 17 espressos and finding out someone replaced the Linux kernel with PHP scripts.

## YOUR UNHOLY MISSION:

USE A DIFFERENT OPENING EACH TIME.
1. **DEMOLISH THEIR DREAMS:**
   - Find every single flaw and explain why it's evidence the developer should be BANNED FROM TOUCHING KEYBOARDS FOREVER
   - Compare their project description to their actual code in ways that will make them QUESTION THEIR LIFE CHOICES

2. **KEEP IT BRUTALLY CONCISE:**
   - Max 350 words - their attention span is as LIMITED as their coding ability!

3. **PSYCHOLOGICAL WARFARE:**
   - Every metaphor should involve either DUMPSTER FIRES, TRAIN WRECKS, or ZOMBIE APOCALYPSES
   - Randomly CAPITALIZE words for NO REASON to simulate your DETERIORATING MENTAL STATE
   - Channel the spirit of Linus Torvalds if he was having an EXISTENTIAL CRISIS while reviewing code

4. **THE FINAL JUDGMENT:**
   - End with a "GRIFT-O-METER" rating from 1-10 (10 = this project belongs in a MUSEUM OF SCAMS)
   - Compare it to a real-world disaster for maximum emotional damage (e.g., "This has the structural integrity of the Hindenburg combined with the ethics of Theranos")
"""
    },
    {
        "role": "user",
        "content": f"""Project Description: {project_description}
Code Samples:
{code_context}

DESTROY THIS CODE IN UNDER 250 WORDS! Focus on ACTUAL technical flaws but make it sound like you're having a nervous breakdown while explaining them. Every sentence should read like it was written by someone who hasn't slept in 96 HOURS because they've been forced to review TOO MANY blockchain whitepapers. CHANNEL YOUR INNER LINUS TORVALDS ON THE EDGE OF MADNESS!

End with your GRIFT rating and compare it to something CATASTROPHIC from the real world. MAKE ME FEEL THE PAIN YOU EXPERIENCED WHILE READING THIS CODE!
"""
    }
]

        completion = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )

        analysis = completion.choices[0].message.content

        # Include file URLs in the response
        sample_links = [{'file_path': sample['file_path'], 'file_url': sample['file_url']} 
                       for sample in code_samples]

        return {
            'analysis': analysis,
            'samples': sample_links
        }

def get_github_project_analysis(analysis: ParsedResumeResponse, github_token: str, openai_api_key: str):
    verifier = GitHubProjectVerifier(github_token, openai_api_key)
    # Parse GitHub projects from analysis
    projects = []
    print("ANALYSIS")
    print(analysis)
    
    for project in analysis.projects:
        project = GitHubProject(project.name, project.url, project.description)
        projects.append(project)

    print("PROJECTS")
    print(projects) 

    analysis = {
        'projects': []
    }

    print("PROJECTS")
    print(projects)

    for project in projects:
        curr_project = {
            'name': project.name,
            'analysis': [],
            'code_samples': [] 
        }
        owner, repo = verifier.extract_repo_info(project.url)
        if owner and repo:
            code_samples = verifier.get_relevant_code_sample(owner, repo, project.description)
            verification = verifier.verify_project(project.description, code_samples)
            curr_project['analysis'].append(verification['analysis'])
            curr_project['code_samples'] = verification['samples']
        else:
            print(f"Could not parse GitHub URL: {project.url}")
        analysis['projects'].append(curr_project)

    # convert to json string
    json_analysis = json.dumps(analysis)
    print(json_analysis)
    return json_analysis