# Roster Generator

![Python version](https://img.shields.io/badge/python-3.14-blue.svg)
![GitHub release](https://img.shields.io/github/v/release/GreenMachine582/RosterGenerator?include_prereleases)
![GitHub deployments](https://img.shields.io/github/deployments/GreenMachine582/RosterGenerator/Production)

---

A Python-based roster generation engine designed to automatically assign employees to operational lines/shifts while respecting hard constraints, soft preferences, and scoring heuristics. The system supports iterative optimisation, transparent scoring, and detailed logging to enable continuous refinement of roster quality.

---

## 🚀 Project Objectives

- Automatically generate valid rosters from structured employee inputs
- Enforce **hard rules** (must / can’t work together, role requirements)
- Optimise against **soft rules** (synergy, experience balance, preferences)
- Produce **scored rosters** with traceable decision logic
- Support **open-ended iterations** to progressively find better solutions
- Export results in a **business-friendly Excel format**

---

## 🧠 Core Concepts

### Employees
Each employee is defined by:
- Unique identifier
- Role (e.g. Paramedic, Manager)
- Years of experience (experience level)
- Specialist flags (e.g. ECP)
- Compatibility rules:
  - `can_work_with`
  - `should_work_with`
  - `cannot_work_with`

### Lines / Shifts
- A roster consists of **N lines**
- Each line can have **multiple employees**
- Lines are scored independently and contribute to an overall roster score

---

## ⚖️ Rules & Constraints

### Hard Rules (Non-Negotiable)
- Employees marked as **cannot work together** are never assigned to the same line
- Line capacity limits are respected
- Role coverage constraints (if configured)

### Soft Rules (Scored)
- Team synergy (role mix, experience spread)
- Preference alignment (`should_work_with`)
- Experience balance across lines
- Specialist distribution (e.g. ECP coverage)

Hard rule violations invalidate a roster.  
Soft rules influence scoring only.

---

## 📊 Scoring System

Each roster receives:
- **Per-line score**
- **Aggregate roster score**

Scoring inputs include:
- Experience variance
- Role synergy
- Specialist presence
- Preference satisfaction
- Penalty deductions for suboptimal pairings

All scoring is logged for transparency and tuning.

---

## 🔁 Optimisation Strategy

The generator uses an **iterative minimax-style search**:
1. Generate a valid initial roster
2. Mutate assignments
3. Re-score the roster
4. Retain the best candidates
5. Repeat for configurable iterations

This avoids premature convergence while remaining computationally practical.

## License
GreenTechHub is licensed under the MIT License, see [LICENSE](LICENSE) for more information.
