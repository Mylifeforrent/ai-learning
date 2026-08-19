---
name: learning-path-architect
description: Design systematic learning paths for technical topics. Use when asked to create a learning roadmap, design a course structure, plan a study path, or organize knowledge from beginner to mastery. Analyzes topics through three perspectives (foundation, advanced cases, project practice) and produces sequenced learning plans with checkpoints and resources.
---

# Learning Path Architect

## Goal
Design complete, executable learning paths for any technical topic using a three-perspective analysis framework (foundation, advanced cases, project practice) that produces sequenced roadmaps with clear dependencies, checkpoints, and resources.

## Workflow
1. Confirm knowledge boundary and learning goals.
2. Classify request type: quick-start, systematic-mastery, or project-driven.
3. Route to three-perspective analysis framework.
4. Sequence knowledge points with dependency mapping.
5. Design validation checkpoints for each stage.
6. Recommend stage-specific resources.
7. Generate complete learning path document.
8. Run automated validation: `python3 scripts/validate_learning_path.py <output_file>`
9. If validation fails, fix issues and re-validate.
10. Declare completion only after validation passes.

## Decision Tree
- If user provides clear boundary → proceed to three-perspective analysis
- If boundary is fuzzy → run boundary clarification protocol (see `references/boundary-clarification.md`)
- If request is quick-start focused → emphasize foundation perspective, compress advanced/project sections
- If request is mastery-focused → full three-perspective treatment with extended project phase
- If request is project-driven → start with project selection, backfill foundation/advanced as dependencies

## Constraints
- Must define learning boundary before generating content
- Must use three-perspective framework (foundation, advanced cases, project practice)
- Must include dependency mapping and time estimates
- Must provide validation checkpoints for each stage
- Must recommend only publicly accessible resources
- Output must be executable without additional clarification

## Validation
Before declaring completion, verify:
- ✓ Learning boundary is explicitly stated
- ✓ All three perspectives are covered (or justified omission)
- ✓ Knowledge points have clear dependencies and sequencing
- ✓ Each stage has validation checkpoints
- ✓ Time estimates are provided for each phase
- ✓ Resources are stage-specific and accessible
- ✓ Output follows template structure in `assets/learning-path-template.md`

## Resources
- `references/foundation-perspective.md`: detailed analysis dimensions for foundation phase
- `references/advanced-cases-perspective.md`: case selection and analysis methodology
- `references/project-practice-perspective.md`: project selection and module breakdown
- `references/sequencing-methodology.md`: dependency mapping and time estimation
- `references/checkpoint-design.md`: validation checkpoint design principles
- `references/resource-recommendation.md`: resource selection and categorization
- `references/boundary-clarification.md`: protocol for clarifying fuzzy learning goals
- `references/content-richness-and-logic-coherence.md`: **[NEW]** strategies for enhancing content richness and logic coherence in courseware generation and editing
- `references/output-examples.md`: complete examples for Agent Skills, RAG, Transformer
- `assets/learning-path-template.md`: output structure template
- `scripts/validate_learning_path.py`: automated quality validation script
- `scripts/README.md`: scripts usage guide and validation criteria
