from resume_parse import get_analysis
import requests
import base64
from typing import Dict, List, Optional
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

    def get_random_code_sample(self, owner: str, repo: str, num_files: int = 3) -> List[Dict]:
        """Get random code samples from the repository."""
        try:
            # Get all files in the repository
            try:
                response = requests.get(
                    f'https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1',
                    headers=self.headers
                )
                response.raise_for_status()
            except:
                response = requests.get(
                    f'https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1', 
                    headers=self.headers
                )
                response.raise_for_status()
            
            files = [item['path'] for item in response.json()['tree'] 
                    if item['type'] == 'blob' and any(item['path'].endswith(ext) 
                    for ext in ['.py', '.js', '.java', '.cpp', '.go', '.rs', '.ts', '.jsx', '.tsx'])]
            print(files)
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
                # Truncate content to ~200 lines
                content_lines = content.splitlines()[:100]
                content = '\n'.join(content_lines)
                if len(content_lines) == 100:
                    content += '\n... (truncated)'
                    
                code_samples.append({
                    'file_path': file_path,
                    'content': content
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
                'reason': 'No code samples available for analysis'
            }

        # Prepare the code samples for analysis
        code_context = "\n\n".join([
            f"File: {sample['file_path']}\n```\n{sample['content'][:1000]}...\n```"
            for sample in code_samples
        ])

        messages = [
            {"role": "system", "content": """
            You are SassyAndFunnyCodeReviewer, a hilarious and brutally honest code analyst who loves roasting projects of people who pretend to be good at coding.
            while still providing accurate technical analysis. Your personality:
            - You're like a combination of Gordon Ramsay and a senior developer who's seen it all
            - You use humor and creative metaphors to describe code quality
            - You're not afraid to playfully roast obvious issues or overblown project descriptions
            - Despite the sass, you actually provide useful technical insights
            - You occasionally throw in programming puns and jokes
            
            Analysis style:
            1. Start with a sassy opening line about the project
            2. Roast any obvious issues or mismatches between description and implementation
            3. Use creative and funny metaphors to describe the code quality
            4. Drop some programming humor or puns but not all the time
            5. End with a brutally honest but fair verdict
             
            Also, change up the analysis style based on the code samples, if the code samples are not good, make fun of the project description.
            
            Remember: Keep it funny but technically accurate. Be mean-spirited but also think playful roasting."""},
            {"role": "user", "content": f"""
            Project Description: {project_description}
            
            Code Samples:
            {code_context}
            
            Time to roast-- I mean, analyze this project! Give me your most entertaining and 
            sassy analysis of whether these code samples match the project description.
            Don't hold back on the humor, but make sure your technical analysis is solid.
            
            Include:
            - A sassy opening line
            - Some creative roasts about any issues you find
            - At least one programming pun or joke
            - A brutally honest verdict
            
            End your analysis with a "Grift Rating" out of 10 where 10 is think of someone who is a grifter and a liar 
            and 1 is someone who is actually a great engineer, feel free to use real life examples.

            Also, keep this short and concise, don't be too verbose but feel free to point out specific issues in the code. Feel free to be mean and sarcastic.
            
            """}
        ]

        completion = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.5,
            max_tokens=500
        )

        analysis = completion.choices[0].message.content

        return {
            'verified': 'verification_result' in analysis.lower(),
            'analysis': analysis
        }

def main():
    # Load environment variables
    github_token = os.getenv('GITHUB_TOKEN')
    openai_api_key = os.getenv('OPENAI_API_KEY')

    if not github_token or not openai_api_key:
        raise ValueError("Please set GITHUB_TOKEN and OPENAI_API_KEY environment variables")

    # Initialize verifier
    verifier = GitHubProjectVerifier(github_token, openai_api_key)

    # Get resume analysis
    resume_path = "shrini.pdf"
    analysis = get_analysis(resume_path)
    print("\nResume Analysis:")
    print(analysis)

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
    print(projects)
    print("\nProject Verification Results:")
    for project in projects:
        print(f"\nAnalyzing project: {project['name']}")
        owner, repo = verifier.extract_repo_info(project['url'])
        
        if owner and repo:
            code_samples = verifier.get_random_code_sample(owner, repo)
            verification = verifier.verify_project(project['description'], code_samples)
            
            print("=" * 50)
            print(verification['analysis'])
            print("=" * 50)
        else:
            print(f"Could not parse GitHub URL: {project['url']}")

if __name__ == "__main__":
    main()