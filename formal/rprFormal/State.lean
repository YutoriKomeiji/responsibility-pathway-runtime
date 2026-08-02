/-
Copyright (c) 2026 Akihisa Ono
SPDX-License-Identifier: MIT
-/

namespace RprFormal

inductive PathwayState where
  | proposed
  | awaitingApproval
  | approved
  | running
  | held
  | humanGate
  | stopped
  | partiallyCompleted
  | writeStatusUnknown
  | repairRequired
  | readyToResume
  | completed
  | denied
  | aborted
  deriving DecidableEq, Repr

open PathwayState

def terminal : PathwayState → Bool
  | completed | denied | aborted => true
  | _ => false

/-- The formal transition relation mirrors the Python runtime table.
    It is intentionally explicit so review sees every authority-bearing edge. -/
def allowed : PathwayState → PathwayState → Bool
  | proposed, awaitingApproval => true
  | proposed, approved => true
  | proposed, denied => true
  | awaitingApproval, approved => true
  | awaitingApproval, denied => true
  | awaitingApproval, humanGate => true
  | approved, running => true
  | approved, held => true
  | approved, aborted => true
  | running, completed => true
  | running, stopped => true
  | running, partiallyCompleted => true
  | running, writeStatusUnknown => true
  | running, repairRequired => true
  | held, humanGate => true
  | held, approved => true
  | held, aborted => true
  | humanGate, approved => true
  | humanGate, denied => true
  | humanGate, aborted => true
  | stopped, repairRequired => true
  | stopped, aborted => true
  | partiallyCompleted, repairRequired => true
  | writeStatusUnknown, completed => true
  | writeStatusUnknown, repairRequired => true
  | repairRequired, readyToResume => true
  | repairRequired, aborted => true
  | readyToResume, running => true
  | readyToResume, aborted => true
  | _, _ => false

end RprFormal
