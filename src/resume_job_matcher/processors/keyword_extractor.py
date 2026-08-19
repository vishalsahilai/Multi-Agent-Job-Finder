import re
from typing import Optional


"""
Stage 2: Python Resume Keyword Extractor
Extracts skills, experience years, location, job title, email, phone from resume text.
No LLM calls — pure Python regex + dictionary matching.
"""
 
import re
from typing import Optional
 
 
#  Skill Dictionaries
 
SKILLS = {
    "languages": [
        "python", "javascript", "typescript", "java", "c++", "c#", "c",
        "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
        "r", "matlab", "perl", "bash", "shell", "powershell", "dart", "lua",
        "haskell", "elixir", "clojure", "groovy", "cobol", "fortran",
    ],
    "web_frameworks": [
        "django", "flask", "fastapi", "express", "nestjs", "nextjs", "nuxtjs",
        "react", "angular", "vue", "svelte", "spring", "spring boot", "laravel",
        "rails", "ruby on rails", "asp.net", "blazor", "gatsby", "remix",
        "fiber", "gin", "echo", "tornado", "aiohttp", "starlette", "hapi",
    ],
    "databases": [
        "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis",
        "elasticsearch", "cassandra", "dynamodb", "firebase", "supabase",
        "oracle", "sql server", "mssql", "mariadb", "cockroachdb", "neo4j",
        "influxdb", "clickhouse", "snowflake", "bigquery", "redshift",
    ],
    "cloud": [
        "aws", "azure", "gcp", "google cloud", "heroku", "digitalocean",
        "vercel", "netlify", "cloudflare", "linode", "vultr", "railway",
        "ec2", "s3", "lambda", "rds", "ecs", "eks", "cloud run", "app engine",
    ],
    "devops": [
        "docker", "kubernetes", "k8s", "jenkins", "github actions", "gitlab ci",
        "circleci", "travis ci", "ansible", "terraform", "helm", "prometheus",
        "grafana", "nginx", "apache", "linux", "ubuntu", "centos", "debian",
        "ci/cd", "devops", "sre", "gitops", "argocd",
    ],
    "data_ml": [
        "pandas", "numpy", "scikit-learn", "sklearn", "tensorflow", "keras",
        "pytorch", "xgboost", "lightgbm", "spark", "hadoop", "airflow",
        "dbt", "mlflow", "huggingface", "langchain", "openai", "gemini",
        "machine learning", "deep learning", "nlp", "computer vision",
        "data science", "data engineering", "etl", "data pipeline",
        "tableau", "power bi", "looker", "matplotlib", "seaborn", "plotly",
    ],
    "mobile": [
        "react native", "flutter", "android", "ios", "swift", "kotlin",
        "xamarin", "ionic", "capacitor", "expo",
    ],
    "tools": [
        "git", "github", "gitlab", "bitbucket", "jira", "confluence",
        "figma", "postman", "swagger", "graphql", "rest", "rest api",
        "grpc", "websocket", "kafka", "rabbitmq", "celery", "redis",
        "webpack", "vite", "babel", "eslint", "pytest", "jest", "selenium",
        "playwright", "cypress", "linux", "vim", "vs code", "intellij",
    ],
    "concepts": [
        "agile", "scrum", "kanban", "tdd", "bdd", "microservices",
        "monolith", "serverless", "event-driven", "oop", "functional programming",
        "design patterns", "system design", "api design", "data structures",
        "algorithms", "distributed systems", "cloud native", "devsecops",
    ],
}
 
# Flatten for fast lookup
ALL_SKILLS_FLAT = {skill for category in SKILLS.values() for skill in category}

#  Job Title Patterns
 
TITLE_KEYWORDS = [
    "software engineer", "software developer", "web developer", "backend developer",
    "frontend developer", "full stack developer", "fullstack developer",
    "mobile developer", "android developer", "ios developer",
    "data scientist", "data engineer", "data analyst", "ml engineer",
    "machine learning engineer", "ai engineer", "nlp engineer",
    "devops engineer", "cloud engineer", "sre", "site reliability engineer",
    "security engineer", "cybersecurity", "network engineer",
    "product manager", "project manager", "scrum master",
    "ui/ux designer", "ux designer", "ui designer",
    "qa engineer", "test engineer", "automation engineer",
    "tech lead", "technical lead", "engineering manager",
    "solutions architect", "cloud architect", "system architect",
    "python developer", "java developer", "javascript developer",
    "node.js developer", "react developer", "django developer",
    "intern", "junior developer", "senior developer",
    "associate engineer", "graduate trainee",
]
 