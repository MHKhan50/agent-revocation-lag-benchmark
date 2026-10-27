# Research scan and topic-selection rationale

**Checked:** 27 October 2026
**Selected topic:** Temporal authorization / permission revocation in multi-step agent workflows
**Programme relationship:** Adjacent to, but distinct from, the existing static tool-policy benchmark. The earlier benchmark compared policy choices for synthetic tool actions; this package isolates the time dimension—a permission is valid at workflow start and revoked while the plan continues.

## Current official UK evidence
1. **University of Surrey — 15 October 2026.** Surrey announced an ARIA-backed project worth more than £3.2 million to develop a secure sandbox for AI agents. The announcement explicitly mentions permissions that can be changed or removed while agents operate and testing against agent-escape scenarios.
2. **The Alan Turing Institute / CETaS — 23 September 2026.** Its behavioural-assurance paper emphasises deployment context, trajectory-level evaluation, continuous monitoring, and reassessment of permissions.
3. **University of Glasgow — 30 March 2026.** The university announced a four-year partnership with Lloyds Banking Group to empirically study agentic AI in software and data engineering, measuring quality, speed, workflow, and efficiency.
4. **Ulster University — funded PhD theme, deadline listed as 8 January 2027.** “Agentic AI for Complex Environments” spans trust-aware digital twins, multi-agent process intelligence, explainable model recommendation, and safe/explainable decisions in dynamic settings.
5. **Lancaster University — PhD opportunities page, checked 27 October 2026.** The page lists eight AI Agent Security positions, including runtime detection and guardrails, but explicitly says the listing is for UK Home students only. This is a research-interest signal, not a statement about any individual's eligibility.
6. **Queen's University Belfast — Cyber AI MSc, 2026 entry.** The module list includes Agentic AI with tool use, autonomous planning, agent vulnerabilities, evaluation, and hardening.
7. **Newcastle University — Artificial Intelligence BSc.** Its official undergraduate page describes final-year project options including generative AI, reinforcement learning, autonomous systems, and intelligent decision-making.

## What this scan does and does not establish
These sources show current activity across a funded research project, research-policy report, industry research partnership, funded PhD theme, security PhD listing, taught MSc module, and undergraduate project pathway. They do **not** prove global novelty or that the topic is universally “hot.” A scoping/systematic literature review is required before making a novelty claim.

## Why this question is useful
A deterministic benchmark lets students reason about a temporal failure mode that static policy comparisons can miss: a permission check can be correct at the beginning yet stale later. The contribution here is a transparent, reproducible baseline; the simulator is not a formal-verification proof or a deployment-ready control.

## Official sources
- Surrey: https://www.surrey.ac.uk/news/surrey-leads-ps32m-project-collaboration-sheffield-and-melbourne-develop-provably-secure-sandbox-ai
- CETaS / Alan Turing Institute: https://cetas.turing.ac.uk/publications/behavioural-assurance-agentic-ai-sensitive-and-high-stakes-organisations
- Glasgow: https://www.gla.ac.uk/news/headline_1256583_en.html
- Ulster University: https://www.ulster.ac.uk/doctoralcollege/find-a-phd/11a-computing/1903114
- Lancaster University: https://www.lancaster.ac.uk/scc/study/phd/phd-opportunities/
- Queen's University Belfast: https://www.qub.ac.uk/courses/postgraduate-taught/2026/cyber-ai-msc-jan/
- Newcastle University: https://www.ncl.ac.uk/undergraduate/degrees/g407/
