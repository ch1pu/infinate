<!--
Copyright 2025-2026 Adolfo Lopez (ch1pu)
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Adolfo Lopez (ch1pu) - github.com/ch1pu
Project: INFINATE - Infinite Context Spatial AI (github.com/ch1pu/infinate)

══════════════════════════════════════════════════════════════════════════════
BUILT BY A U.S. NAVY VETERAN | BUILT IN TEXAS | OPEN FOR OPPORTUNITIES
══════════════════════════════════════════════════════════════════════════════
I'm actively seeking software engineering roles. If you're reading this code
and like what you see, let's connect:
  - GitHub: github.com/ch1pu
  - Twitter/X: @2006_adolfo
  - Project: This codebase demonstrates O(k) spatial attention, achieving
    10,317x speedup over MIT's approach with 89.58% test coverage.
══════════════════════════════════════════════════════════════════════════════
-->

# Security Remediation Plan - Infinite Project

**Created:** 2025-11-13
**Priority Order:** CRITICAL → HIGH → MEDIUM → LOW
**Estimated Total Time:** 2-3 hours for all fixes

---

## PHASE 1: CRITICAL FIXES (30 minutes)
**Must complete before ANY git operations**

### 1. Create Root .gitignore File

**Time:** 5 minutes
**Priority:** CRITICAL
**Risk if not fixed:** Secrets exposed on GitHub

**Steps:**

```bash
# 1. Navigate to project root
cd /home/ch1pu/infinate

# 2. Create comprehensive .gitignore
cat > .gitignore << 'EOF'
# SECURITY - NEVER COMMIT THESE
.env
.env.*
!.env.example
*.env
secrets/
credentials/
private/

# Certificates and Keys
*.key
*.pem
*.crt
*.pfx
*.p12
*.cer
*.cert
ssl/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
env/
*.egg-info/
.pytest_cache/
.coverage
.coverage.*
htmlcov/
.tox/
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/
.ruff_cache/

# Jupyter
.ipynb_checkpoints/
*.ipynb

# PyTorch / AI Models
*.pt
*.pth
*.ckpt
*.safetensors
*.bin
*.gguf
*.h5
checkpoints/
models/
saved_models/
runs/
lightning_logs/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*
.pnpm-debug.log*
.next/
out/
dist/
build/

# Database
*.db
*.sqlite
*.sqlite3
postgres-data/
redis-data/
mysql-data/
mongodb-data/

# Docker
docker-compose.override.yml
.dockerignore.local

# IDE and Editors
.vscode/
!.vscode/extensions.json
!.vscode/settings.json.example
.idea/
*.swp
*.swo
*.swn
*.bak
*~
.project
.classpath
.settings/
*.sublime-*

# OS Files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
ehthumbs_vista.db
Thumbs.db
Desktop.ini
$RECYCLE.BIN/

# Logs
*.log
logs/
*.log.*
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

# Temporary files
*.tmp
*.temp
tmp/
temp/
cache/

# Backup files
*.backup
*.bak
*.old
*.orig
*_backup
*_old

# Large data files
datasets/
embeddings/
vectors/
*.csv
*.tsv
*.parquet
data/large/

# Testing
coverage/
.nyc_output/
test-results/
jest-results/
cypress/screenshots/
cypress/videos/

# Documentation builds
docs/_build/
site/
public/

# Terraform
*.tfstate
*.tfstate.*
.terraform/
.terraform.lock.hcl

# Ansible
*.retry
ansible/*.log

# AWS
.aws/
aws_credentials

# Azure
.azure/

# GCP
.gcloud/
gcp-key.json

# Monitoring
.grafana/
.prometheus/

# Custom project specific
research/private/
experiments/results/
benchmarks/output/
EOF

echo "✅ Root .gitignore created successfully"
```

### 2. Fix Documentation Secrets

**Time:** 15 minutes
**Priority:** CRITICAL
**Files to update:** 2 documentation files

**Steps:**

```bash
# 1. Fix DOCKER_ARCHITECTURE.md
cd /home/ch1pu/infinate
sed -i 's/DB_PASSWORD=secure_password_here/DB_PASSWORD=CHANGE_ME_USE_STRONG_PASSWORD_MIN_32_CHARS/g' Documents/DOCKER_ARCHITECTURE.md
sed -i 's/JWT_SECRET=your_jwt_secret_here/JWT_SECRET=CHANGE_ME_GENERATE_WITH_OPENSSL_RAND_BASE64_32/g' Documents/DOCKER_ARCHITECTURE.md
sed -i 's/REDIS_PASSWORD=redis_password_here/REDIS_PASSWORD=CHANGE_ME_USE_DIFFERENT_STRONG_PASSWORD/g' Documents/DOCKER_ARCHITECTURE.md

# 2. Fix INFRASTRUCTURE.md
sed -i 's/echo "strong_password"/echo "CHANGE_ME_STRONG_PASSWORD"/g' Documents/INFRASTRUCTURE.md
sed -i 's/echo "jwt_secret_key"/echo "CHANGE_ME_JWT_SECRET"/g' Documents/INFRASTRUCTURE.md
sed -i 's/echo "redis_password"/echo "CHANGE_ME_REDIS_PASS"/g' Documents/INFRASTRUCTURE.md

# 3. Verify changes
echo "Checking for remaining suspicious patterns..."
grep -n "password_here\|secret_here\|secret_key" Documents/*.md || echo "✅ No suspicious patterns found"
```

**Manual Review Required:**
Check these files for any remaining realistic-looking secrets:
- Documents/DOCKER_ARCHITECTURE.md
- Documents/INFRASTRUCTURE.md
- Documents/SECURITY_PLAN.md

### 3. Initialize Git Safely

**Time:** 10 minutes
**Priority:** CRITICAL
**Purpose:** Ensure git is configured before any commits

```bash
# 1. Initialize git repository
cd /home/ch1pu/infinate
git init

# 2. Configure git for safety
git config core.excludesFile .gitignore
git config core.autocrlf input

# 3. Add security files FIRST
git add .gitignore
git commit -m "security: add comprehensive .gitignore

- Prevents accidental commit of secrets
- Excludes environment files
- Ignores sensitive configurations
- Blocks temporary and backup files"

# 4. Verify gitignore is working
touch .env
echo "TEST_SECRET=this_should_not_be_tracked" > .env
git status
# .env should NOT appear in git status

# 5. Clean up test
rm .env
echo "✅ Git initialized with security configuration"
```

---

## PHASE 2: HIGH PRIORITY FIXES (45 minutes)
**Complete before starting implementation**

### 4. Create .env.example File

**Time:** 10 minutes
**Priority:** HIGH

```bash
cd /home/ch1pu/infinate

cat > .env.example << 'EOF'
# ============================================================
# Infinite Spatial AI - Environment Configuration Template
# ============================================================
# SECURITY WARNING: Never commit real values to version control!
#
# Instructions:
# 1. Copy this file to .env
# 2. Replace all CHANGE_ME values with secure values
# 3. Use strong, unique passwords (min 32 characters)
# 4. Generate secrets with: openssl rand -base64 32
# ============================================================

# === Database Configuration ===
DB_HOST=localhost
DB_PORT=5432
DB_NAME=infinite_db
DB_USER=infinite_user
DB_PASSWORD=CHANGE_ME_USE_STRONG_PASSWORD_MIN_32_CHARS
DB_SSL_MODE=require

# === Redis Configuration ===
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=CHANGE_ME_USE_DIFFERENT_STRONG_PASSWORD
REDIS_DB=0
REDIS_SSL=false

# === PostgreSQL pgvector Extension ===
PGVECTOR_HOST=localhost
PGVECTOR_PORT=5432
PGVECTOR_DB=vectors_db
PGVECTOR_USER=vector_user
PGVECTOR_PASSWORD=CHANGE_ME_ANOTHER_STRONG_PASSWORD

# === Qdrant Vector Store ===
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_API_KEY=CHANGE_ME_IF_USING_QDRANT_CLOUD
QDRANT_COLLECTION=spatial_memories

# === Authentication & Security ===
JWT_SECRET=CHANGE_ME_GENERATE_WITH_OPENSSL_RAND_BASE64_32
JWT_EXPIRY=24h
JWT_REFRESH_SECRET=CHANGE_ME_DIFFERENT_FROM_JWT_SECRET
JWT_REFRESH_EXPIRY=7d
SESSION_SECRET=CHANGE_ME_ANOTHER_RANDOM_SECRET
ENCRYPTION_KEY=CHANGE_ME_32_BYTE_KEY_FOR_AES256

# === API Configuration ===
NODE_ENV=development
API_PORT=4000
API_HOST=0.0.0.0
API_PREFIX=/api/v1
API_DOCS_ENABLED=true

# === Python Spatial Engine ===
SPATIAL_ENGINE_PORT=5000
SPATIAL_ENGINE_HOST=0.0.0.0
SPATIAL_ENGINE_WORKERS=4
SPATIAL_ENGINE_DEBUG=false

# === AI Model Configuration ===
MODEL_PATH=/models/llama-2-7b.gguf
MODEL_TYPE=llama
MODEL_CONTEXT_SIZE=4096
MODEL_BATCH_SIZE=512
MODEL_THREADS=8

# === Hardware Acceleration ===
CUDA_VISIBLE_DEVICES=0
USE_GPU=true
USE_NPU=false
NPU_DEVICE=xdna2
GPU_MEMORY_FRACTION=0.9

# === Frontend Configuration ===
REACT_APP_API_URL=http://localhost:4000
REACT_APP_WS_URL=ws://localhost:4000
REACT_APP_PUBLIC_URL=http://localhost:3000
REACT_APP_ENABLE_DEBUG=false

# === CORS Configuration ===
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_CREDENTIALS=true

# === Rate Limiting ===
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_SKIP_SUCCESSFUL_REQUESTS=false

# === Logging Configuration ===
LOG_LEVEL=info
LOG_FORMAT=json
LOG_FILE=logs/app.log
LOG_MAX_SIZE=10m
LOG_MAX_FILES=30
LOG_COMPRESSION=true

# === Monitoring & Metrics ===
METRICS_ENABLED=true
METRICS_PORT=9090
PROMETHEUS_PUSHGATEWAY=localhost:9091
JAEGER_ENDPOINT=http://localhost:14268/api/traces

# === Email Configuration (Optional) ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=CHANGE_ME_YOUR_EMAIL
SMTP_PASSWORD=CHANGE_ME_APP_SPECIFIC_PASSWORD
SMTP_FROM=noreply@infinite-ai.local
SMTP_SECURE=false

# === AWS Configuration (Optional) ===
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=CHANGE_ME_IF_USING_AWS
AWS_SECRET_ACCESS_KEY=CHANGE_ME_IF_USING_AWS
S3_BUCKET=infinite-storage

# === Feature Flags ===
ENABLE_SPATIAL_INDEX=true
ENABLE_VECTOR_CACHE=true
ENABLE_AUTH=true
ENABLE_RATE_LIMITING=true
ENABLE_METRICS=true
ENABLE_SWAGGER_DOCS=false

# === Debug Settings (Development Only) ===
DEBUG=false
VERBOSE_ERRORS=false
PRETTY_LOGS=true

# ============================================================
# Security Checklist:
# [ ] All CHANGE_ME values have been replaced
# [ ] Passwords are at least 32 characters
# [ ] JWT secrets are cryptographically random
# [ ] Different passwords for each service
# [ ] File permissions: chmod 600 .env
# [ ] .env is in .gitignore
# [ ] No spaces around = signs
# ============================================================
EOF

echo "✅ .env.example created with secure defaults"
```

### 5. Create Security Headers Configuration

**Time:** 15 minutes
**Priority:** HIGH

```bash
# Create security config for Node.js
mkdir -p /home/ch1pu/infinate/api/config
cat > /home/ch1pu/infinate/api/config/security.js << 'EOF'
/**
 * Security Configuration for Infinite Spatial AI
 * Implements OWASP security best practices
 */

module.exports = {
  // Helmet.js configuration
  helmet: {
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'"], // Remove unsafe in production
        styleSrc: ["'self'", "'unsafe-inline'"],
        imgSrc: ["'self'", "data:", "https:", "blob:"],
        connectSrc: ["'self'", "ws://localhost:*", "wss://localhost:*"],
        fontSrc: ["'self'", "data:"],
        objectSrc: ["'none'"],
        mediaSrc: ["'self'"],
        frameSrc: ["'none'"],
        workerSrc: ["'self'", "blob:"],
        childSrc: ["'self'", "blob:"],
        formAction: ["'self'"],
        frameAncestors: ["'none'"],
        baseUri: ["'self'"],
        manifestSrc: ["'self'"],
        upgradeInsecureRequests: process.env.NODE_ENV === 'production' ? [] : null,
      },
    },
    strictTransportSecurity: {
      maxAge: 31536000,
      includeSubDomains: true,
      preload: true,
    },
    xContentTypeOptions: 'nosniff',
    xFrameOptions: 'DENY',
    xXssProtection: '1; mode=block',
    referrerPolicy: 'strict-origin-when-cross-origin',
    crossOriginEmbedderPolicy: false, // May need for Three.js
    crossOriginOpenerPolicy: { policy: 'same-origin' },
    crossOriginResourcePolicy: { policy: 'cross-origin' },
    originAgentCluster: true,
    xDnsPrefetchControl: { allow: false },
    xDownloadOptions: 'noopen',
    xPermittedCrossDomainPolicies: false,
    hsts: {
      maxAge: 31536000,
      includeSubDomains: true,
      preload: true,
    },
  },

  // CORS configuration
  cors: {
    origin: function (origin, callback) {
      const allowedOrigins = (process.env.CORS_ORIGINS || 'http://localhost:3000').split(',');
      if (!origin || allowedOrigins.indexOf(origin) !== -1) {
        callback(null, true);
      } else {
        callback(new Error('Not allowed by CORS'));
      }
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With', 'X-CSRF-Token'],
    exposedHeaders: ['X-Total-Count', 'X-Page', 'X-Per-Page'],
    maxAge: 86400, // 24 hours
    preflightContinue: false,
    optionsSuccessStatus: 204,
  },

  // Rate limiting
  rateLimit: {
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '60000'),
    max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100'),
    message: 'Too many requests from this IP, please try again later.',
    standardHeaders: true,
    legacyHeaders: false,
    skipSuccessfulRequests: false,
    skipFailedRequests: false,
    handler: (req, res) => {
      res.status(429).json({
        error: 'Rate limit exceeded',
        message: 'Too many requests, please try again later.',
        retryAfter: Math.ceil(req.rateLimit.resetTime / 1000),
      });
    },
  },

  // Session configuration
  session: {
    secret: process.env.SESSION_SECRET || 'CHANGE_ME_IN_PRODUCTION',
    name: 'infinite.sid',
    resave: false,
    saveUninitialized: false,
    rolling: true,
    cookie: {
      secure: process.env.NODE_ENV === 'production',
      httpOnly: true,
      maxAge: 24 * 60 * 60 * 1000, // 24 hours
      sameSite: 'strict',
      domain: process.env.COOKIE_DOMAIN || undefined,
      path: '/',
    },
    store: null, // Configure Redis store in production
  },

  // Password policy
  passwordPolicy: {
    minLength: 12,
    maxLength: 128,
    requireUppercase: true,
    requireLowercase: true,
    requireNumbers: true,
    requireSymbols: true,
    preventCommonPasswords: true,
    preventUserInfo: true,
    bcryptRounds: 12,
  },

  // API Security
  api: {
    maxRequestSize: '10mb',
    maxUploadSize: '100mb',
    allowedFileTypes: ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'],
    apiKeyHeader: 'X-API-Key',
    apiVersionHeader: 'X-API-Version',
    requestIdHeader: 'X-Request-ID',
  },

  // Security monitoring
  monitoring: {
    enableAuditLog: true,
    logFailedLogins: true,
    logSensitiveActions: true,
    alertOnSuspiciousActivity: true,
    maxFailedLoginAttempts: 5,
    lockoutDuration: 30 * 60 * 1000, // 30 minutes
  },
};
EOF

echo "✅ Security headers configuration created"
```

### 6. Update Network Documentation

**Time:** 10 minutes
**Priority:** HIGH

```bash
# Replace specific IPs with generic examples
cd /home/ch1pu/infinate

# Update SECURITY_PLAN.md
sed -i 's/172\.20\.0\.0\/24/10.0.1.0\/24 # Example frontend network/g' Documents/SECURITY_PLAN.md
sed -i 's/172\.21\.0\.0\/24/10.0.2.0\/24 # Example backend network/g' Documents/SECURITY_PLAN.md
sed -i 's/172\.22\.0\.0\/24/10.0.3.0\/24 # Example database network/g' Documents/SECURITY_PLAN.md

# Update localhost references to be generic
find Documents -name "*.md" -exec sed -i 's/http:\/\/localhost:[0-9]\+/http:\/\/<your-host>:<port>/g' {} \;
find Documents -name "*.md" -exec sed -i 's/ws:\/\/localhost:[0-9]\+/ws:\/\/<your-host>:<port>/g' {} \;

echo "✅ Network documentation sanitized"
```

### 7. Create SECURITY.md

**Time:** 10 minutes
**Priority:** HIGH

```bash
cat > /home/ch1pu/infinate/SECURITY.md << 'EOF'
# Security Policy

## 🔒 Security First

The Infinite Spatial AI project takes security seriously. This document outlines our security policies and procedures.

## Supported Versions

Currently in pre-release development. Security updates will be provided for:

| Version | Supported          | Status      |
| ------- | ------------------ | ----------- |
| 0.1.x   | :white_check_mark: | Development |
| < 0.1   | :x:                | Unsupported |

## Reporting Security Vulnerabilities

**⚠️ IMPORTANT: Do NOT report security vulnerabilities through public GitHub issues.**

### How to Report

1. **Email:** Send details to `security@[your-domain].com`
2. **Encrypted Communication:** Use our PGP key (available at [link])
3. **Response Time:** We aim to respond within 48 hours

### What to Include

- Type of vulnerability
- Full path to source file(s)
- Location of affected code (tag/branch/commit or line numbers)
- Step-by-step reproduction instructions
- Proof-of-concept or exploit code (if possible)
- Impact assessment
- Suggested fix (if you have one)

### What to Expect

1. **Acknowledgment:** Within 48 hours
2. **Initial Assessment:** Within 1 week
3. **Resolution Timeline:** Depends on severity
4. **Credit:** Security researchers will be credited (unless anonymity requested)

## Security Measures

### Current Implementation

- ✅ Environment-based configuration (no hardcoded secrets)
- ✅ Comprehensive .gitignore preventing secret exposure
- ✅ Type checking with mypy (strict mode)
- ✅ 90% minimum test coverage requirement
- ✅ Modern dependencies with security updates
- ✅ Input validation using Pydantic
- ✅ SQL injection prevention via ORMs
- ✅ XSS prevention in frontend

### Planned Enhancements

- [ ] Container vulnerability scanning (Trivy)
- [ ] Dependency vulnerability scanning (Safety, npm audit)
- [ ] Pre-commit hooks for secret detection
- [ ] Rate limiting on all API endpoints
- [ ] Web Application Firewall (WAF)
- [ ] Intrusion Detection System (IDS)
- [ ] Regular security audits
- [ ] Penetration testing

## Security Best Practices

### For Contributors

1. **Never commit secrets** - Use environment variables
2. **Validate all input** - Never trust user input
3. **Use parameterized queries** - Prevent SQL injection
4. **Implement proper authentication** - Use JWT with short expiry
5. **Enable HTTPS everywhere** - No plain HTTP in production
6. **Keep dependencies updated** - Regular security patches
7. **Follow least privilege principle** - Minimal permissions
8. **Log security events** - But never log sensitive data

### Development Guidelines

```bash
# Before committing
git diff --cached  # Review changes
git secrets --scan  # Scan for secrets (if installed)

# Check dependencies
poetry check
npm audit

# Run security tests
pytest -m security
```

## Security Headers

Production deployments must include:

- Content-Security-Policy
- Strict-Transport-Security
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin

## Dependency Management

- Python: Dependencies managed with Poetry, locked versions
- Node.js: npm with package-lock.json
- Docker: Regular base image updates
- All: Automated vulnerability scanning in CI/CD

## Data Protection

- Passwords: Argon2 hashing (never bcrypt for new systems)
- API Keys: Stored encrypted, rotated regularly
- PII: Encrypted at rest and in transit
- Logs: No sensitive data logged
- Backups: Encrypted with separate keys

## Incident Response

1. **Detect:** Monitoring and alerting
2. **Assess:** Determine severity and scope
3. **Contain:** Isolate affected systems
4. **Eradicate:** Remove threat
5. **Recover:** Restore normal operations
6. **Review:** Post-incident analysis

## Compliance

While not yet certified, we aim to comply with:

- OWASP Top 10 mitigation
- GDPR (data privacy)
- SOC 2 Type II (future)
- ISO 27001 (future)

## Security Tools

### Recommended Tools

- **Secret Scanning:** GitGuardian, TruffleHog
- **SAST:** Semgrep, Bandit (Python)
- **DAST:** OWASP ZAP
- **Dependency Scanning:** Snyk, Dependabot
- **Container Scanning:** Trivy, Clair
- **IDE Plugins:** GitLens, Security linters

## Security Training

Team members should be familiar with:

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [SANS Top 25](https://www.sans.org/top25-software-errors/)
- [CWE Database](https://cwe.mitre.org/)
- Security-focused code reviews

## Contact

- Security Team: `security@[your-domain].com`
- Bug Bounty Program: (Coming Soon)
- Security Updates: Subscribe to security-announce@[your-domain].com

## Acknowledgments

We thank the security researchers who help keep Infinite secure:

- (Your name could be here!)

---

**Last Updated:** 2025-11-13
**Next Review:** 2025-12-13

Remember: Security is everyone's responsibility! 🛡️
EOF

echo "✅ SECURITY.md created"
```

---

## PHASE 3: MEDIUM PRIORITY (45 minutes)
**Address during implementation**

### 8. Pin Python Dependencies

**Time:** 10 minutes

```bash
cd /home/ch1pu/infinate/backend

# Update pyproject.toml to pin versions
cat > pyproject.toml.new << 'EOF'
[tool.poetry]
name = "spatial-engine"
version = "0.1.0"
description = "Spatial AI Engine with O(k) Constant Complexity for Unlimited Context"
authors = ["Infinite Project Team"]
readme = "README.md"
license = "Apache-2.0"

[tool.poetry.dependencies]
python = "3.11.9"  # Pinned version
torch = "2.1.0"    # Pinned version
numpy = "1.26.0"   # Pinned version
pydantic = "2.5.0" # Pinned version
python-dotenv = "0.21.0"  # Pinned version

# ... rest of file remains the same ...
EOF

# Apply changes
mv pyproject.toml.new pyproject.toml
poetry lock --no-update
echo "✅ Dependencies pinned to exact versions"
```

### 9. Add Pre-commit Hooks

**Time:** 15 minutes

```bash
cd /home/ch1pu/infinate

cat > .pre-commit-config.yaml << 'EOF'
# Pre-commit hooks for security and code quality
repos:
  # Security: Detect secrets
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: .*\.lock|package-lock\.json

  # Security: Check for common security issues
  - repo: https://github.com/PyCQA/bandit
    rev: '1.7.5'
    hooks:
      - id: bandit
        args: ['-r', 'backend/spatial_engine']
        exclude: tests/

  # Python: Black formatter
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  # Python: Ruff linter
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  # Python: Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict, --ignore-missing-imports]

  # General: File checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-case-conflict
      - id: check-merge-conflict
      - id: mixed-line-ending
      - id: detect-private-key

  # Docker: Lint Dockerfiles
  - repo: https://github.com/hadolint/hadolint
    rev: v2.12.0
    hooks:
      - id: hadolint-docker

  # Markdown: Lint markdown files
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.37.0
    hooks:
      - id: markdownlint
        args: ['--fix']

  # YAML: Lint YAML files
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.33.0
    hooks:
      - id: yamllint
        args: ['-c', '.yamllint.yml']

# Configuration for yamllint
default_language_version:
  python: python3.11
EOF

# Create yamllint config
cat > .yamllint.yml << 'EOF'
extends: default
rules:
  line-length:
    max: 120
  comments:
    min-spaces-from-content: 2
  truthy:
    allowed-values: ['true', 'false', 'yes', 'no', 'on', 'off']
EOF

# Initialize secret detection baseline
cd /home/ch1pu/infinate
pip install detect-secrets
detect-secrets scan --baseline .secrets.baseline

echo "✅ Pre-commit hooks configured"
```

### 10. Create Rate Limiting Configuration

**Time:** 10 minutes

```javascript
// Create rate limiting middleware
mkdir -p /home/ch1pu/infinate/api/middleware
cat > /home/ch1pu/infinate/api/middleware/rateLimiter.js << 'EOF'
const rateLimit = require('express-rate-limit');
const RedisStore = require('rate-limit-redis');
const Redis = require('ioredis');

// Create Redis client
const redisClient = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT || 6379,
  password: process.env.REDIS_PASSWORD,
  enableOfflineQueue: false,
});

// Rate limiting configurations for different endpoints
const rateLimiters = {
  // General API rate limit
  api: rateLimit({
    store: new RedisStore({
      client: redisClient,
      prefix: 'rl:api:',
    }),
    windowMs: 60 * 1000, // 1 minute
    max: 100, // 100 requests per minute
    message: 'Too many requests from this IP, please try again later.',
    standardHeaders: true,
    legacyHeaders: false,
  }),

  // Strict limit for authentication endpoints
  auth: rateLimit({
    store: new RedisStore({
      client: redisClient,
      prefix: 'rl:auth:',
    }),
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 5, // 5 attempts per 15 minutes
    message: 'Too many authentication attempts, please try again later.',
    skipSuccessfulRequests: true, // Only count failed attempts
  }),

  // Relaxed limit for search endpoints
  search: rateLimit({
    store: new RedisStore({
      client: redisClient,
      prefix: 'rl:search:',
    }),
    windowMs: 60 * 1000, // 1 minute
    max: 30, // 30 searches per minute
    message: 'Search rate limit exceeded, please slow down.',
  }),

  // Strict limit for file uploads
  upload: rateLimit({
    store: new RedisStore({
      client: redisClient,
      prefix: 'rl:upload:',
    }),
    windowMs: 60 * 60 * 1000, // 1 hour
    max: 10, // 10 uploads per hour
    message: 'Upload limit exceeded, please try again later.',
  }),
};

module.exports = rateLimiters;
EOF

echo "✅ Rate limiting configuration created"
```

### 11. Add Docker Security Scanning

**Time:** 10 minutes

```bash
# Create GitHub Actions workflow for security scanning
mkdir -p /home/ch1pu/infinate/.github/workflows
cat > /home/ch1pu/infinate/.github/workflows/security.yml << 'EOF'
name: Security Scanning

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  # Scan Docker images for vulnerabilities
  trivy-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t infinite-app:${{ github.sha }} .

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'infinite-app:${{ github.sha }}'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH,MEDIUM'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  # Python dependency scanning
  python-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Poetry
        run: pip install poetry

      - name: Install dependencies
        working-directory: ./backend
        run: poetry install

      - name: Run Safety check
        working-directory: ./backend
        run: poetry run safety check --json

      - name: Run Bandit security linter
        working-directory: ./backend
        run: poetry run bandit -r spatial_engine/ -f json -o bandit-report.json

  # Node.js dependency scanning
  nodejs-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Run npm audit
        working-directory: ./frontend
        run: npm audit --audit-level=moderate

  # Secret scanning
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run TruffleHog
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD
EOF

echo "✅ Docker security scanning configured"
```

---

## PHASE 4: LOW PRIORITY (30 minutes)
**Nice to have improvements**

### 12-14. Additional Security Enhancements

```bash
# Quick setup for remaining items
cd /home/ch1pu/infinate

# Create security scripts directory
mkdir -p scripts/security

# Secret rotation script
cat > scripts/security/rotate-secrets.sh << 'EOF'
#!/bin/bash
# Script to rotate secrets
echo "Generating new JWT secret..."
NEW_JWT_SECRET=$(openssl rand -base64 32)
echo "New JWT secret: $NEW_JWT_SECRET"
echo "Update your .env file with this value"

echo "Generating new session secret..."
NEW_SESSION_SECRET=$(openssl rand -base64 32)
echo "New session secret: $NEW_SESSION_SECRET"
EOF

chmod +x scripts/security/rotate-secrets.sh

# Audit logging configuration
cat > backend/spatial_engine/utils/audit_logger.py << 'EOF'
"""Security audit logging for Infinite project."""
import json
import logging
from datetime import datetime
from typing import Any, Dict

class SecurityAuditLogger:
    """Log security-relevant events."""

    def __init__(self):
        self.logger = logging.getLogger('security.audit')
        handler = logging.FileHandler('logs/security-audit.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_event(
        self,
        event_type: str,
        user_id: str = None,
        ip_address: str = None,
        details: Dict[str, Any] = None
    ):
        """Log a security event."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': ip_address,
            'details': details or {}
        }
        self.logger.info(json.dumps(event))

# Usage:
# audit = SecurityAuditLogger()
# audit.log_event('login_failed', ip_address='192.168.1.1')
EOF

echo "✅ Additional security enhancements configured"
```

---

## Verification Checklist

After completing all fixes, verify:

```bash
# Run verification script
cd /home/ch1pu/infinate

echo "=== Security Verification Checklist ==="

# Check .gitignore exists
if [ -f ".gitignore" ]; then
    echo "✅ Root .gitignore exists"
else
    echo "❌ Root .gitignore missing!"
fi

# Check .env.example exists
if [ -f ".env.example" ]; then
    echo "✅ .env.example exists"
else
    echo "❌ .env.example missing!"
fi

# Check for .env files (should not exist or be gitignored)
if [ -f ".env" ]; then
    if git check-ignore .env > /dev/null 2>&1; then
        echo "✅ .env is gitignored"
    else
        echo "❌ .env exists and is NOT gitignored!"
    fi
else
    echo "✅ No .env file exists yet"
fi

# Check SECURITY.md exists
if [ -f "SECURITY.md" ]; then
    echo "✅ SECURITY.md exists"
else
    echo "❌ SECURITY.md missing!"
fi

# Check for suspicious patterns in docs
echo "Checking for suspicious patterns in documentation..."
if grep -q "password_here\|secret_key\|your_jwt" Documents/*.md 2>/dev/null; then
    echo "⚠️  Found suspicious patterns in documentation"
else
    echo "✅ No suspicious patterns in documentation"
fi

# Check git status
echo ""
echo "Git status (no sensitive files should appear):"
git status --short

echo ""
echo "=== Verification Complete ==="
```

---

## Estimated Time Summary

| Phase | Time | Priority |
|-------|------|----------|
| CRITICAL fixes | 30 min | Must do before git |
| HIGH fixes | 45 min | Before implementation |
| MEDIUM fixes | 45 min | During implementation |
| LOW fixes | 30 min | Nice to have |
| **TOTAL** | **2.5 hours** | |

## Priority Order for Implementation

1. ⚠️ **IMMEDIATE (Before ANY git operations):**
   - Create root .gitignore
   - Fix documentation secrets
   - Initialize git safely

2. 🔴 **URGENT (Before starting code):**
   - Create .env.example
   - Configure security headers
   - Create SECURITY.md

3. 🟡 **IMPORTANT (During Milestone 1.1):**
   - Pin dependencies
   - Add pre-commit hooks
   - Configure rate limiting

4. 🟢 **RECOMMENDED (Before production):**
   - Docker scanning
   - Audit logging
   - Secret rotation

---

**Security First!** Complete at least CRITICAL and HIGH priority fixes before proceeding with implementation. 🛡️