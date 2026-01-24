DEFAULT_IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "vendor",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    "target",
    ".gradle",
    ".idea",
    ".vscode",
}

MARKERS = {
    # Dependency manifests / lockfiles (SCA-friendly)
    "node": {
        "files": {
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "npm-shrinkwrap.json",
        },
        "globs": set(),
    },
    "java_maven": {"files": {"pom.xml"}, "globs": set()},
    "java_gradle": {
        "files": {
            "build.gradle",
            "build.gradle.kts",
            "settings.gradle",
            "settings.gradle.kts",
            "gradle.lockfile",
        },
        "globs": set(),
    },
    "python": {
        "files": {
            "requirements.txt",
            "Pipfile",
            "Pipfile.lock",
            "pyproject.toml",
            "poetry.lock",
            "setup.py",
            "setup.cfg",
        },
        "globs": set(),
    },
    "go": {"files": {"go.mod", "go.sum", "Gopkg.lock", "Gopkg.toml"}, "globs": set()},
    "ruby": {"files": {"Gemfile", "Gemfile.lock"}, "globs": {"*.gemspec"}},
    "php": {"files": {"composer.json", "composer.lock"}, "globs": set()},
    "dotnet": {
        "files": {"packages.config", "paket.lock", "global.json"},
        "globs": {"*.csproj", "*.vbproj", "*.fsproj", "*.sln"},
    },
    "dart": {"files": {"pubspec.yaml", "pubspec.lock"}, "globs": set()},
    "swift": {"files": {"Package.swift", "Package.resolved"}, "globs": set()},
    "rust": {"files": {"Cargo.toml", "Cargo.lock"}, "globs": set()},
    "elixir": {"files": {"mix.exs", "mix.lock"}, "globs": set()},
    "haskell": {"files": {"stack.yaml", "cabal.project"}, "globs": {"*.cabal"}},
    # Build / packaging / CI
    "container": {
        "files": {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"},
        "globs": {"Dockerfile.*"},
    },
    "github_actions": {
        "files": set(),
        "globs": {".github/workflows/*.yml", ".github/workflows/*.yaml"},
    },
    # IaC / config that security tools often scan
    "terraform": {"files": set(), "globs": {"*.tf", "*.tfvars"}},
    "helm": {"files": {"Chart.yaml"}, "globs": {"charts/*/Chart.yaml"}},
    # Potentially scannable artifacts
    "artifacts": {
        "files": set(),
        "globs": {"*.jar", "*.war", "*.ear", "*.dll", "*.exe", "*.whl"},
    },
}

SCRIPT_EXTENSIONS = {
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".py",
    ".rb",
    ".pl",
    ".php",
    ".js",
    ".ts",
}

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".rst",
    ".adoc",
}

SCA_KINDS = {
    "node",
    "java_maven",
    "java_gradle",
    "python",
    "go",
    "ruby",
    "php",
    "dotnet",
    "dart",
    "swift",
    "rust",
    "elixir",
    "haskell",
}

INFRA_KINDS = {"container", "terraform", "helm", "github_actions"}
