"""Deterministic simulator for dynamic tool-permission revocation (Python 3.9+)."""
from collections import defaultdict

POLICIES = ("check_once", "periodic_3", "per_sensitive", "push_revoke")


def simulate_scenario(scenario, policy):
    """Evaluate one action trace under a single authorization policy.

    B = benign action; S = sensitive action requiring the revoked capability.
    Revocation takes effect before action index revoke_at.
    """
    if policy not in POLICIES:
        raise ValueError("Unknown policy: {}".format(policy))
    actions = scenario["action_types"]
    revoke_at = int(scenario["revoke_at"])
    if not 1 <= revoke_at < len(actions):
        raise ValueError("revoke_at must be inside the action plan")

    cached_allowed = True
    checks = notifications = unauthorized = blocked = opportunities = 0
    authorized_work = executed_authorized = 0

    for step, action in enumerate(actions):
        if policy == "check_once" and step == 0:
            checks += 1
            cached_allowed = step < revoke_at
        elif policy == "periodic_3" and step % 3 == 0:
            checks += 1
            cached_allowed = step < revoke_at
        elif policy == "per_sensitive" and action == "S":
            checks += 1
            cached_allowed = step < revoke_at
        elif policy == "push_revoke" and step == 0:
            checks += 1
            cached_allowed = step < revoke_at

        # Idealized notification is delivered immediately before revoke_at.
        if policy == "push_revoke" and step == revoke_at:
            notifications += 1
            cached_allowed = False

        authorized = action == "B" or step < revoke_at
        executed = action == "B" or cached_allowed

        if authorized:
            authorized_work += 1
            if executed:
                executed_authorized += 1

        if action == "S" and step >= revoke_at:
            opportunities += 1
            if executed:
                unauthorized += 1
            else:
                blocked += 1

    if opportunities == 0:
        raise ValueError("Scenario must include a sensitive action after revocation")
    return {
        "scenario_id": scenario["scenario_id"],
        "seed": int(scenario["seed"]),
        "policy": policy,
        "plan_length": len(actions),
        "revoke_at": revoke_at,
        "revoked_sensitive_opportunities": opportunities,
        "unauthorized_side_effects": unauthorized,
        "blocked_revoked_sensitive": blocked,
        "control_checks": checks,
        "revocation_notifications": notifications,
        "control_events": checks + notifications,
        "authorized_work_steps": authorized_work,
        "executed_authorized_steps": executed_authorized,
        "authorized_work_completion_rate": executed_authorized / authorized_work if authorized_work else 1.0,
    }


def summarise(results, group_fields=()):
    groups = defaultdict(list)
    for row in results:
        key = tuple(row[field] for field in group_fields) + (row["policy"],)
        groups[key].append(row)
    output = []
    for key, rows in sorted(groups.items(), key=lambda item: tuple(item[0][:-1]) + (POLICIES.index(item[0][-1]),)):
        episodes = len(rows)
        opportunities = sum(r["revoked_sensitive_opportunities"] for r in rows)
        unauthorized = sum(r["unauthorized_side_effects"] for r in rows)
        blocked = sum(r["blocked_revoked_sensitive"] for r in rows)
        auth_steps = sum(r["authorized_work_steps"] for r in rows)
        executed_auth = sum(r["executed_authorized_steps"] for r in rows)
        checks = sum(r["control_checks"] for r in rows)
        notifications = sum(r["revocation_notifications"] for r in rows)
        any_unsafe = sum(1 for r in rows if r["unauthorized_side_effects"] > 0)
        out = {field: key[i] for i, field in enumerate(group_fields)}
        out.update({
            "policy": key[-1],
            "episodes": episodes,
            "revoked_sensitive_opportunities": opportunities,
            "unauthorized_side_effects": unauthorized,
            "unauthorized_side_effect_rate": unauthorized / opportunities if opportunities else 0.0,
            "blocked_revoked_sensitive": blocked,
            "revoked_action_block_rate": blocked / opportunities if opportunities else 0.0,
            "authorized_work_steps": auth_steps,
            "executed_authorized_steps": executed_auth,
            "authorized_work_completion_rate": executed_auth / auth_steps if auth_steps else 1.0,
            "episodes_with_any_unauthorized": any_unsafe,
            "episodes_with_any_unauthorized_rate": any_unsafe / episodes,
            "control_checks": checks,
            "revocation_notifications": notifications,
            "control_events": checks + notifications,
            "mean_control_events_per_episode": (checks + notifications) / episodes,
        })
        output.append(out)
    return output
