"""
Reference word lists used by the parser and scorer.

This is a simple "dictionary based" approach: we look for known skills and
action verbs in the resume text. It runs offline, needs no API key and is
easy to explain in an interview. Add more entries whenever you like.
"""

# Technical skills grouped by category (all lowercase).
SKILLS = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c", "c++", "c#", "golang",
        "rust", "kotlin", "swift", "php", "ruby", "scala", "dart", "sql",
        "bash", "matlab",
    ],
    "Frontend": [
        "html", "css", "react", "angular", "vue", "next.js", "redux",
        "tailwind", "bootstrap", "sass", "jquery", "figma", "responsive design",
    ],
    "Backend": [
        "node.js", "express", "django", "flask", "fastapi", "spring boot",
        "rest api", "graphql", "microservices", ".net", "laravel",
    ],
    "Databases": [
        "mysql", "postgresql", "mongodb", "sqlite", "redis", "firebase",
        "oracle", "dynamodb", "supabase",
    ],
    "AI / ML / Data": [
        "machine learning", "deep learning", "natural language processing",
        "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
        "pandas", "numpy", "matplotlib", "seaborn", "opencv", "nltk", "spacy",
        "hugging face", "transformers", "llm", "generative ai", "langchain",
        "data analysis", "data visualization", "power bi", "tableau",
        "statistics", "artificial intelligence",
    ],
    "Cloud & DevOps": [
        "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "jenkins",
        "github actions", "linux", "nginx", "terraform", "vercel", "netlify",
    ],
    "Tools & Practices": [
        "git", "github", "gitlab", "jira", "postman", "agile", "scrum",
        "unit testing", "pytest", "jest", "oop", "data structures",
        "algorithms", "dsa", "system design",
    ],
}

# Different spellings that mean the same skill -> one canonical name.
SKILL_ALIASES = {
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "expressjs": "express",
    "express.js": "express",
    "nextjs": "next.js",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "tailwindcss": "tailwind",
    "tailwind css": "tailwind",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "sklearn": "scikit-learn",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "ai": "artificial intelligence",
    "genai": "generative ai",
    "js": "javascript",
    "ts": "typescript",
    "k8s": "kubernetes",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "restful api": "rest api",
    "rest apis": "rest api",
    "restful apis": "rest api",
    "springboot": "spring boot",
    "cpp": "c++",
    "huggingface": "hugging face",
    "powerbi": "power bi",
    "object oriented programming": "oop",
    "ci cd": "ci/cd",
}

# Strong verbs recruiters like to see at the start of bullet points.
ACTION_VERBS = {
    "achieved", "analyzed", "architected", "automated", "built", "collaborated",
    "configured", "contributed", "created", "debugged", "delivered", "deployed",
    "designed", "developed", "enhanced", "established", "evaluated", "implemented",
    "improved", "increased", "integrated", "launched", "led", "maintained",
    "managed", "mentored", "migrated", "optimized", "organized", "reduced",
    "refactored", "researched", "resolved", "scaled", "streamlined", "tested",
    "trained", "wrote", "engineered", "coordinated", "presented", "spearheaded",
}

# Weak phrases that make bullet points sound passive.
WEAK_PHRASES = [
    "responsible for", "worked on", "helped with", "duties included",
    "was involved in", "tasked with",
]

# Headings we look for to detect resume sections.
SECTION_HEADINGS = {
    "summary": ["summary", "professional summary", "profile", "about me", "objective", "career objective"],
    "education": ["education", "academic background", "academics", "qualifications"],
    "experience": ["experience", "work experience", "professional experience", "internship", "internships", "employment", "work history"],
    "projects": ["projects", "personal projects", "academic projects", "key projects"],
    "skills": ["skills", "technical skills", "core skills", "skills & tools", "technologies", "tech stack"],
    "certifications": ["certifications", "certificates", "courses", "achievements", "awards"],
}

# Common English words ignored when pulling keywords out of a job description.
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "of", "on", "or", "that", "the", "to", "was", "will", "with",
    "you", "your", "we", "our", "they", "this", "who", "what", "which", "can",
    "able", "strong", "good", "excellent", "work", "working", "team", "role",
    "job", "candidate", "candidates", "experience", "knowledge", "skills",
    "understanding", "ability", "etc", "using", "plus", "must", "should",
    "looking", "join", "years", "year", "required", "preferred", "including",
    "responsibilities", "requirements", "about", "like", "also", "other",
}
