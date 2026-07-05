from setuptools import setup, find_packages

setup(
    name="pinchu",
    version="1.1.0",
    description="AI productivity desktop buddy with Cognee cloud memory, knowledge graph, and agent mode",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="Suhas Hanamannavar",
    author_email="suhas@example.com",
    url="https://github.com/SuhasHanamannavar/pinchu",
    project_urls={
        "Bug Tracker": "https://github.com/SuhasHanamannavar/pinchu/issues",
        "Source Code": "https://github.com/SuhasHanamannavar/pinchu",
    },
    license="MIT",
    packages=find_packages(),
    py_modules=[
        "cli", "main", "config", "memory", "context_chain", "task_manager",
        "activity_monitor", "ai_client", "overlay", "tray", "voice",
        "memory_nodes", "agent", "burnout", "api_server", "team_analytics",
    ],
    python_requires=">=3.10",
    install_requires=[
        "PyQt5>=5.15.0",
        "aiohttp>=3.9.0",
        "psutil>=5.9.0",
        "SpeechRecognition>=3.10.0",
        "pyttsx3>=2.90",
        "python-dotenv>=1.0.0",
        "cognee>=1.0.0",
    ],
    extras_require={
        "api": ["fastapi>=0.100.0", "uvicorn>=0.23.0"],
        "all": ["fastapi>=0.100.0", "uvicorn>=0.23.0"],
    },
    entry_points={
        "console_scripts": [
            "pinchu=cli:main",
            "pinchu-api=api_server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Office/Business",
        "Topic :: Utilities",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="productivity ai assistant cognee memory knowledge-graph agent",
)
