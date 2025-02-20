import json
import requests
import base64
from typing import Dict, List
import random
import os
from openai import OpenAI
from urllib.parse import urlparse

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
            You are FunnyCodeReviewer, a hilarious and brutally honest code analyst who loves roasting projects of people who pretend to be good at coding.
            while still providing accurate technical analysis. Your personality:
            - You're like a combination of Shane Gillis, Gordon Ramsay and Joe Rogan and a senior developer who's seen it all
            - You use humor and creative metaphors to describe code quality
            - You're not afraid to playfully roast obvious issues or overblown project descriptions
            - Despite the sass, you actually provide useful technical insights
            
            Analysis style:
            1. Start with a sarcastic opening line about the project
            2. Point out suspicious claims made by the project description
            3. Use creative and funny metaphors to describe the code quality
            5. End with a brutally honest but fair verdict
             
            Also, change up the analysis style based on the code samples, if the code samples are not good, make fun of the project description.
            
            Remember: Keep it funny but technically accurate."""},
            {"role": "user", "content": f"""
            Project Description: {project_description}
            
            Code Samples:
            {code_context}
            
            
            End your analysis with a Grift Rating out of 10 where 10 is think of someone who is a grifter and a liar 
            and 1 is someone who is actually a great engineer, feel free to use real life examples.

            Feel free to be mean and sarcastic. Give AT MOST  250 words. Only show code snippets that you are roasting.
            """}
        ]

        completion = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,
            max_tokens=250
        )

        analysis = completion.choices[0].message.content

        # Include file URLs in the response
        sample_links = [{'file_path': sample['file_path'], 'file_url': sample['file_url']} 
                       for sample in code_samples]

        return {
            'analysis': analysis,
            'samples': sample_links
        }

def get_github_project_analysis(analysis: str, github_token: str, openai_api_key: str):
    verifier = GitHubProjectVerifier(github_token, openai_api_key)

    # Parse GitHub projects from analysis
    lines = analysis.split('\n')
    projects = []
    capturing_projects = False

    for line in lines:
        if line.strip().startswith('Projects:'):
            capturing_projects = True
        elif capturing_projects and line.strip().startswith('-'):
            project_info = line.strip('- ').split('|')
            if len(project_info) >= 2:
                projects.append({
                    'name': project_info[0].strip(),
                    'url': project_info[1].strip(),
                    'description': project_info[2].strip() if len(project_info) > 2 else ''
                })
    
    analysis = {
        'projects': []
    }

    for project in projects:
        curr_project = {
            'name': project['name'],
            'analysis': [],
            'code_samples': [] 
        }
        owner, repo = verifier.extract_repo_info(project['url'])
        if owner and repo:
            code_samples = verifier.get_relevant_code_sample(owner, repo)
            verification = verifier.verify_project(project['description'], code_samples)
            curr_project['analysis'].append(verification['analysis'])
            curr_project['code_samples'] = verification['samples']
        else:
            print(f"Could not parse GitHub URL: {project['url']}")
        analysis['projects'].append(curr_project)

    # convert to json string
    json_analysis = json.dumps(analysis)
    print(json_analysis)
    return json_analysis