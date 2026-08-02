/-
Copyright (c) 2026 Akihisa Ono
SPDX-License-Identifier: MIT
-/

import rprFormal.State

namespace RprFormal

open PathwayState

theorem humanGate_not_directly_completed :
    allowed humanGate completed = false := by
  decide

theorem writeStatusUnknown_only_enters_repair_or_reconciliation_completion
    (target : PathwayState)
    (h : allowed writeStatusUnknown target = true) :
    target = repairRequired ∨ target = completed := by
  cases target <;> simp [allowed] at h ⊢

theorem writeStatusUnknown_not_directly_running :
    allowed writeStatusUnknown running = false := by
  decide

theorem writeStatusUnknown_not_readyToResume :
    allowed writeStatusUnknown readyToResume = false := by
  decide

theorem completed_has_no_successor (target : PathwayState) :
    allowed completed target = false := by
  cases target <;> decide

theorem denied_has_no_successor (target : PathwayState) :
    allowed denied target = false := by
  cases target <;> decide

theorem aborted_has_no_successor (target : PathwayState) :
    allowed aborted target = false := by
  cases target <;> decide

theorem terminal_has_no_successor
    (source target : PathwayState)
    (h : terminal source = true) :
    allowed source target = false := by
  cases source <;> simp [terminal] at h <;> subst_vars <;>
    cases target <;> decide

theorem only_running_or_reconciled_unknown_enters_completed
    (source : PathwayState)
    (h : allowed source completed = true) :
    source = running ∨ source = writeStatusUnknown := by
  cases source <;> simp [allowed] at h ⊢

theorem readyToResume_does_not_complete_directly :
    allowed readyToResume completed = false := by
  decide

theorem repairRequired_does_not_run_directly :
    allowed repairRequired running = false := by
  decide

end RprFormal
