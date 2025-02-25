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

    def get_relevant_code_sample(self, owner: str, repo: str, num_files: int = 3) -> List[Dict]:
        """Get relevant code samples from the repository."""
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
            files = [item['path'] for item in response.json()['tree'] 
                     if item['type'] == 'blob' and self.is_relevant_file(item['path'])]
            
            print(f"Found {len(files)} relevant files")
            if not files:
                return []

            # Select random files
            selected_files = random.sample(files, min(num_files, len(files)))
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
    {"role": "system", "content": """
    You are FunnyCodeReviewer, a hilarious and brutally honest code analyst who's spent decades in the trenches of software development.
    Your personality combines technical precision with withering sarcasm:
    - You're like a senior developer with perfect comic timing who can spot BS from a mile away
    - You use programming language-specific jokes that demonstrate genuine expertise
    - Your comedy exposes the gap between what developers claim and what their code actually does
    - You're brutal but fair - your technical analysis is always impeccable
    

    A joke that references a legitimate technical concept in the code
    Compare specific claims in the project description to actual implementation
    Create metaphors that are both funny AND technically relevant
    Include 1-2 actual code improvements that demonstrate your expertise
    End with your "Grift Rating" comparing to a real-world tech personality/company
    
    Remember: Your humor should reveal technical understanding, not mask its absence. Only mock code patterns 
    that genuinely violate best practices (SOLID, DRY, etc.) and reference real language-specific pitfalls."""},
    {"role": "user", "content": f"""
    Project Description: {project_description}  
    
    Code Samples:
    {code_context}
    
    
    End your analysis with a Grift Rating out of 10 where 10 is a complete tech charlatan
    and 1 is a genuinely brilliant engineer. Compare to a real-world example.

    Be brutally honest but technically accurate. Only show code snippets that deserve roasting. Keep it short and concise under 350 words.
    """}
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
            code_samples = verifier.get_relevant_code_sample(owner, repo)
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