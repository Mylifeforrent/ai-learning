from __future__ import annotations

import json
from pathlib import Path

from loop_engineering.config import HarnessStore
from loop_engineering.schemas import ImprovementProposal, utc_now


class HarnessProposalApplier:
    """Human-controlled boundary for applying loop-4 recommendations."""

    def __init__(self, harness_store: HarnessStore) -> None:
        self.harness_store = harness_store

    def apply(self, proposal_path: Path, approved_by: str) -> ImprovementProposal:
        proposal = ImprovementProposal.model_validate_json(
            proposal_path.read_text(encoding="utf-8")
        )
        if proposal.status != "pending_human_review":
            raise ValueError(f"Proposal is not pending review: {proposal.status}")
        if not proposal.prompt_additions:
            raise ValueError("This demo only auto-applies additive prompt rules.")

        harness = self.harness_store.load()
        added_rules = [
            rule for rule in proposal.prompt_additions if rule not in harness.learned_rules
        ]
        harness.learned_rules.extend(added_rules)
        harness.version += 1
        harness.history.append(
            {
                "proposal_id": proposal.proposal_id,
                "approved_by": approved_by,
                "approved_at": utc_now().isoformat(),
                "added_rules": added_rules,
            }
        )
        self.harness_store.save(harness)

        proposal.status = "applied"
        proposal_path.write_text(
            json.dumps(proposal.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return proposal
