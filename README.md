# AI Security Labs

Interactive AI security training platform by Prof. Nikolas Behar. 10 workshop products covering OWASP LLM/MCP/Agentic Top 10, Red Teaming, Multimodal Security, Blue Team Defense, and more.

## Spaces

| # | Space | Content | Hardware | Status |
|---|-------|---------|----------|--------|
| 1 | [OWASP Top 10 Workshop](https://huggingface.co/spaces/nikobehar/llm-top-10) | LLM Top 10 (10) + MCP Top 10 (9) + Agentic AI (6) + 5 defenses | CPU | **LIVE** |
| 2 | Red Team Workshop | Red Teaming + Jailbreak Benchmark + Social Engineering | CPU | Planned |
| 3 | Blue Team Workshop | Prompt Hardening + Behavioral Testing + WAF Rules + Defense Pipeline | CPU | Planned |
| 4 | Multimodal Security | Image Injection + Adversarial + Stego + OCR + Deepfake + CAPTCHA | GPU (T4) | Planned |
| 5 | Data Poisoning Lab | RAG Poisoning + Fine-Tuning Poisoning + Synthetic Data | GPU (T4) | Planned |
| 6 | Incident Response Lab | AI Breach Simulation + Containment + Forensics | CPU | Planned |
| 7 | Detection & Monitoring | Log Analysis + Anomaly Detection + Output Sanitization | CPU | Planned |
| 8 | AI Governance Lab | Security Policy Writer + Risk Assessment + Threat Modeling | CPU | Planned |
| 9 | Multi-Agent Security | Multi-Agent Attack + Cascading Failures | CPU | Planned |
| 10 | Model Forensics | Backdoor Detection + Train Your Own Guard + Differential Privacy | GPU (T4) | Planned |

## Repository Structure

```
ai-security-labs/
├── framework/          # Shared code across all Spaces
│   ├── static/         # Common CSS + JS framework
│   ├── scanner.py      # Defense tools (reusable)
│   └── templates/      # Base HTML template
│
├── spaces/
│   ├── owasp-top-10/   # LIVE — 25 attacks, 5 defenses, 3 workshops
│   ├── red-team/       # Planned
│   ├── blue-team/      # Planned
│   ├── multimodal/     # Planned
│   └── ...             # 6 more planned Spaces
│
├── docs/               # Platform documentation
├── scripts/            # Deploy scripts
└── CLAUDE.md           # AI assistant instructions
```

## Stack

- **Backend:** FastAPI + Uvicorn (Python)
- **Frontend:** Vanilla HTML/CSS/JS (no frameworks)
- **Model:** LLaMA 3.3 70B via Groq API
- **Defense Tools:** Meta Prompt Guard 2, LLM Guard, custom guardrail
- **Deploy:** Docker on HuggingFace Spaces

## Deploy

```bash
# Deploy a specific space to HuggingFace
./scripts/deploy.sh owasp-top-10
```

## License

MIT

## Author

Prof. Nikolas Behar
