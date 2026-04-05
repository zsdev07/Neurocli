from setuptools import setup, find_packages

setup(
    name="neurocli",
    version="1.0.0",
    description="Lightweight AI terminal assistant — multi-provider, RAG, git, search",
    author="NeuroCLI",
    python_requires=">=3.8",
    packages=find_packages(),
    py_modules=["main"],
    install_requires=[
        "rich>=13.0",
    ],
    extras_require={
        "openai":      ["openai>=1.0"],
        "anthropic":   ["anthropic>=0.30"],
        "groq":        ["groq>=0.9"],
        "gemini":      ["google-generativeai>=0.7"],
        "search":      ["duckduckgo-search>=5.0"],
        "all": [
            "openai>=1.0",
            "anthropic>=0.30",
            "groq>=0.9",
            "google-generativeai>=0.7",
            "duckduckgo-search>=5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "neurocli=main:main",
        ],
    },
)
