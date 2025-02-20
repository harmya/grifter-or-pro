### Grifter or Pro?

Ever wondered if the stuff people put on their resume is actually true?

Especially when they put coding projects that they say they made with grandiose descriptions?

Well, lets find out.

### Work in progress

This is a work in progress and I will be adding more features to it.

For now, I have implemented a basic resume parser that can parse the resume and extract the information.
I have also implemented a basic GitHub repo verifier that can verify the GitHub repos and check if the projects are actually real.
After that, I randomly sample files from the GitHub repos and use a LLM to analyze the code and the project description and give a "grift" rating.

Example:

I put this on my resume: "Created a self-driving car system that learns to navigate through traffic using a neural network to process sensory input and make decisions using JavaScript, HTML and CSS"

Now, after running the verifier, my review is:
"Oh, sweet code of mine, what have we here? A self-driving car system that sounds like it was designed by someone who thinks "neural network" is just a fancy term for a group chat!

Let’s dive into the code, shall we? First off, your project description is like a toddler claiming they can cook a five-course meal because they microwaved a Hot Pocket. You’re not exactly building Skynet here; you’re just trying to avoid a fender bender with some polygons."

Kinda funny, hopefully I don't lose interest in this before I finish the web app.
