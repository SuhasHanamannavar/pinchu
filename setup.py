from setuptools import setup, find_packages

setup(
    name="pinchu",
    version="1.0.0",
    description="AI productivity desktop buddy with Cognee cloud memory",
    author="Suhas Hanamannavar",
    author_email="suhas@example.com",
    url="https://github.com/SuhasHanamannavar/pinchu",
    license="MIT",
    packages=find_packages(),
    py_modules=["cli", "main", "config", "memory", "context_chain", "task_manager", "activity_monitor", "ai_client", "overlay", "tray", "voice"],
    python_requires=">=3.10",
    install_requires=[
        "PyQt5",
        "aiohttp",
        "psutil",
        "speechrecognition",
        "pyttsx3",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "pinchu=cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Office/Business",
        "Topic :: Utilities",
    ],
)
