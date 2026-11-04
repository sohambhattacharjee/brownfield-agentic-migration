# Literature map for manuscript planning

This is a reading and positioning aid, not manuscript text. Confirm the target IEEE Software call's live requirements before submission; calls, length limits, and reference rules can change.

## Practice-facing framing

- [IEEE Software: Call for Papers](https://www.computer.org/digital-library/magazines/so/cfp-ieee-software) describes the magazine as connecting software research and practice and encourages sharing related data through IEEE DataPort. Use this to shape a concise experience report with actionable lessons and an inspectable evidence package. Recheck the selected call's current format and limits at submission.

## Evaluation of coding agents

- [SWE-bench](https://arxiv.org/abs/2310.06770) evaluates issue resolution on real repositories with tests. It provides a useful contrast: this project has a tiny, synthetic, controlled brownfield application and evaluates staged onboarding/proposal profiles rather than broad repository-solving capability.
- [SWE-agent](https://arxiv.org/abs/2405.15793) studies how an agent-computer interface affects software engineering task performance. Relevant to interpreting the factory's task interface and tool workflow as part of the treatment, rather than treating the model alone as the system.
- [Agentless](https://arxiv.org/abs/2407.01489) presents a simpler localization, repair, and validation pipeline. It cautions against assuming that more agentic orchestration is inherently better; the manuscript should report what the staged process does and avoid superiority claims unsupported by these cohorts.
- [AgentLens](https://arxiv.org/abs/2605.12925) argues that binary test outcomes can hide differences in trajectory quality, including passing patches that do not reflect intended solutions. This directly motivates retaining proposal patches, metadata, and review records. Our current cohorts reached a binary pass ceiling, and same-model reviews are not independent validation, so process evidence remains descriptive.

## Human productivity and field validity

- [METR's randomized study of experienced open-source developers](https://metr.org/Early_2025_AI_Experienced_OS_Devs_Study-paper.pdf) used 16 developers and 246 tasks in mature repositories. Its real-world setting differs substantially from this one-person synthetic case; use it to emphasize that our results cannot support claims about professional productivity or general effectiveness.

## Positioning boundary for this project

- A bounded, independently authored synthetic case study of staged brownfield onboarding, task execution, and evidence capture.
- Three completed task cohorts, each tied to its own pinned target revision. They are not a pooled experiment and have no randomized human/control comparison.
- Corrected suites reached a pass ceiling. Compare token use, latency, patch size, changed files, review outcomes, and protocol events descriptively only; do not infer profile superiority from these small cohorts.
- Generated proposals were evaluated in isolated copies and were not transferred into the application. The independently authored application implementation is a separate artifact.
- Same-model review is a second pass, not an independent reviewer. The evidence does not establish production readiness, maintainability over time, or legal/IP conclusions.
