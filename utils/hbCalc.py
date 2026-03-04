# This file is part of owo-dusk.
#
# Copyright (c) 2024-present EchoQuill
#
# Portions of this file are based on code by EchoQuill, licensed under the
# GNU General Public License v3.0 (GPL-3.0).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.


"""
The approach here is simple (if we count out the coding part).
We are using greedy approach here, invest in the trait with possiblity to level up the highest,
counting out the best solution to invest in duration, cost etc first...
but hey this also works fine, users can disable the trait they dont want to invest in
to prevent the code from investing essense in those.

If in-case essense we have is not enough to level up any traits to next level,
then it will focus on priorities that I have set instead.

Whatever this is:
https://www.geeksforgeeks.org/introduction-to-greedy-algorithm-data-structures-and-algorithm-tutorials/
"""


def allocate_essence(input_data, prio_obj):
    """
    inc:  The base multiplier for the level cost calculation.
    pow:  The exponent applied to (level+1) to compute cost.
    base: The starting value for the stat.
    upg:  The change in the stat per level (can be negative for improvements like cost reduction).
    max:  The maximum level the trait can reach.
    prio: The priority (set by me) according to what I believe needs to be upgraded first!
    """
    traits = {
        "efficiency": {
            "inc": 10,
            "pow": 1.748,
            "base": 25,
            "upg": 1,
            "max": 215,
            "prio": 4,
        },
        "duration": {
            "inc": 10,
            "pow": 1.7,
            "base": 0.5,
            "upg": 0.1,
            "max": 235,
            "prio": 2,
        },
        "cost": {"inc": 1000, "pow": 3.4, "base": 10, "upg": -1, "max": 5, "prio": 5},
        "gain": {"inc": 10, "pow": 1.8, "base": 0, "upg": 25, "max": 200, "prio": 4},
        "exp": {"inc": 10, "pow": 1.8, "base": 0, "upg": 35, "max": 200, "prio": 3},
        "radar": {
            "inc": 50,
            "pow": 2.5,
            "base": 0,
            "upg": 0.00000004,
            "max": 999,
            "prio": 1,
        },
    }

    for trait in traits.keys():
        prio = getattr(prio_obj, trait, 0)
        traits[trait]["prio"] = prio

    """Total essense"""
    available_essence = input_data.get("essence", 0)

    """Fetch enabled traits"""
    enabled_traits = {
        t: data
        for t, data in input_data.items()
        if t in traits and data.get("enabled", False)
    }

    """
    allocation: future result,
    initialising with 0, will contain how much essence to allocate for all traits
    """
    allocation = {t: 0 for t in enabled_traits}

    """Contains a dict of current level of each enabled traits"""
    current_levels = {
        t: enabled_traits[t].get("current_level", 0) for t in enabled_traits
    }

    """Contains a dict of currently invested essense for each trait"""
    current_invested = {t: enabled_traits[t].get("invested", 0) for t in enabled_traits}

    """Essence from total available essence, which has yet to be distributed."""
    remaining = available_essence

    while remaining > 0:
        best_trait = None  # Trait selected for a full upgrade (if any).
        best_ratio = -1  # Highest benefit-to-required ratio found.
        cost_for_best = None  # The cost required for the best trait's full upgrade.

        for t in allocation:
            lvl = current_levels[t]
            trait_data = traits[t]

            if lvl >= trait_data["max"]:
                """Trait already maxed out!"""
                continue

            next_level = lvl + 1

            """Total cost for next level is calculated with this equation"""
            full_cost = int(trait_data["inc"] * (next_level ** trait_data["pow"]))
            invested = current_invested.get(t, 0)

            """cost for next level"""
            required = max(0, full_cost - invested)
            # max() prevents the value of `full_cost - invested` from going less than 0 (this should never happen!)

            if required == 0:
                """
                If 0 essence is required for next level,
                This shouldn't be executed but letting it stay.
                """
                current_levels[t] += 1
                current_invested[t] = 0
                continue

            """Get priority for the trait"""
            benefit = trait_data["prio"]
            ratio = benefit / required if required > 0 else 0

            if required <= remaining and ratio > best_ratio:
                best_ratio = ratio
                best_trait = t
                cost_for_best = required

        if best_trait is not None:
            """trait found that can be fully upgraded"""
            allocation[best_trait] += cost_for_best
            remaining -= cost_for_best
            """move the trait up by a level"""
            current_levels[best_trait] += 1
            """reset already invested amount to 0 (since we are at next level now)"""
            current_invested[best_trait] = 0
        else:
            """Invest in best trait if upgrade is not possible"""
            best_trait = None
            best_ratio = -1

            for t in allocation:
                lvl = current_levels[t]
                trait_data = traits[t]

                if lvl >= trait_data["max"]:
                    """Skip if already maxed out."""
                    continue

                next_level = lvl + 1
                # ** == ^
                full_cost = int(trait_data["inc"] * (next_level ** trait_data["pow"]))
                invested = current_invested.get(t, 0)
                required = max(0, full_cost - invested)

                if required <= 0:
                    continue

                benefit = trait_data["prio"]
                ratio = benefit / required if required > 0 else 0

                # Select the trait with best ratio.
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_trait = t

            if best_trait is not None:
                allocation[best_trait] += remaining
                current_invested[best_trait] += remaining
                remaining = 0  # All essence has now been allocated.
            else:
                """Break out of loop if no trait is eligible"""
                break

    return allocation
