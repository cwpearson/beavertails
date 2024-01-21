from enum import Enum
from pathlib import Path
import json

from pulp import LpProblem, LpMinimize, lpSum, LpVariable, value
from pulp.apis import PULP_CBC_CMD

from beavertails import mypulp

THIS_DIR = Path(__file__).parent.absolute()
STATIC_DIR = THIS_DIR / "static"

# create Items enum
with open(STATIC_DIR / "items.json") as f:
    data = json.load(f)
    Item = Enum("Items", data)


class Rates:
    def __init__(self, rates):
        self.rates = rates

    def __getitem__(self, key):
        return self.rates.get(key, 0)

    def items(self):
        return self.rates.items()

    def __repr__(self):
        return repr(self.rates)

    def get(self, key, default):
        return self.rates.get(key, default)

    def __setitem___(self, key, value):
        self.rates[key] = value


class Settings:
    def __init__(self):
        self.working_hours = 16
        self.efficiency = 0.9
        self.lumberjack_period = 0.75
        self.tapper_period = 0.75
        self.gatherer_period = 0.75
        self.forester_period = 0.75
        self.farmhouse_period = 0.75


class Recipe:
    def __init__(
        self,
        name,
        tiles,
        period,
        inputs=Rates({}),
        outputs=Rates({}),
        input_workers=0,
        output_workers=0,
    ):
        self.name = name
        self.tiles = tiles
        self.period = period
        self.inputs = inputs
        self.outputs = outputs
        self.input_workers = input_workers
        self.output_workers = output_workers

    def __repr__(self):
        return self.name


RECIPES = []

# load additional recipes
with open(STATIC_DIR / "recipes.json") as f:
    RECIPES = json.load(f)

ITEM_IDS = dict((item, i) for i, item in enumerate(Item))


def recipe_with_settings(raw_recipe: dict, settings: Settings) -> Recipe:
    """convert a dict to a Recipe.
    BED and POWER are already a rate, so don't divide by time"""

    # numeric() is running eval, and the json
    # recipe definitions are looking for specific variables to be
    # set in this scope.
    scope = locals()

    def numeric(o):
        if isinstance(o, str):
            return eval(
                o,
                None,  # globals
                scope,  # locals
            )
        elif isinstance(o, float):
            return o
        elif isinstance(o, int):
            return o
        else:
            raise RuntimeError(f"can't make {o} numeric!")

    input_workers = raw_recipe.get("input_workers", 0)
    output_workers = raw_recipe.get("output_workers", 0)

    r_inputs = {}
    for k, v in raw_recipe.get("inputs", {}).items():
        if k in ("BED", "POWER"):
            r_inputs[Item[k]] = numeric(v)
        else:
            active_hours = numeric(raw_recipe["working_hours"])
            input_rate = numeric(v) * active_hours / 24 / numeric(raw_recipe["period"])
            if input_workers > 0:
                input_rate *= settings.efficiency
            r_inputs[Item[k]] = input_rate
    r_outputs = {}
    for k, v in raw_recipe.get("outputs", {}).items():
        if k in ("BED", "POWER"):
            r_outputs[Item[k]] = numeric(v)
        else:
            active_hours = numeric(raw_recipe["working_hours"])
            output_rate = numeric(v) * active_hours / 24 / numeric(raw_recipe["period"])
            if input_workers > 0:
                output_rate *= settings.efficiency
            r_outputs[Item[k]] = output_rate

    return Recipe(
        raw_recipe["name"],
        int(raw_recipe["tiles"]),
        numeric(raw_recipe["period"]),
        inputs=Rates(r_inputs),
        outputs=Rates(r_outputs),
        input_workers=input_workers,
        output_workers=output_workers,
    )


def recipes_with_settings(settings: Settings):
    return [recipe_with_settings(raw_recipe, settings) for raw_recipe in RECIPES]


def make_problem_constraints(name: str, needs: Rates, settings: Settings):
    prob = LpProblem(name, LpMinimize)
    recipes = recipes_with_settings(settings)

    var_names = {}

    # two separate numbers of each recipe
    # a "real" version (non-integer)
    # an integer version (real rounded up)
    recipe_counts_real = []
    recipe_counts_int = []
    for recipe in recipes:
        var_real = LpVariable(f"{recipe.name}_real", 0, cat="Continuous")
        var_names[var_real] = recipe.name
        var_int = LpVariable(f"{recipe.name}_int", 0, cat="Integer")
        var_names[var_int] = recipe.name
        prob += var_real <= var_int
        # really we want var_int < var_real + 1
        # since we're minimizing things, the integer value will be as small as possible anyway
        # prob += var_int <= (var_real + 0.9999)
        recipe_counts_real += [var_real]
        recipe_counts_int += [var_int]

    # how much each item is being produced
    # require that the net rate of production for each item is at least 0 (no negative items)
    item_rates = []
    for item in Item:
        item_rate = 0
        for ri, recipe in enumerate(recipes):
            item_rate += (
                recipe.outputs[item] * recipe_counts_real[ri]
                - recipe.inputs[item] * recipe_counts_real[ri]
            )
        prob += item_rate >= 0
        item_rates += [item_rate]

    # require that particular item rates meet our needs
    for item, per_hour in needs.items():
        prob += item_rates[ITEM_IDS[item]] >= per_hour

    # require output workers at least match input workers
    input_workers = lpSum(
        r.input_workers * recipe_counts_int[ri] for ri, r in enumerate(recipes)
    )

    # "Beaver" pseudo-recipe is the only thing that produces workers
    # Might seem reasonable to use the integer number here, but
    # the number of inputs consumed by the recipe is computed from the
    # "real" variable, which can drift down below the integer by nearly 1
    # according to the rules that rounded partial recipes up
    # so, for e.g. 6 beavers -> consume resources according to ~5 beavers
    output_workers = lpSum(
        r.output_workers * recipe_counts_real[ri] for ri, r in enumerate(recipes)
    )
    prob += output_workers >= input_workers

    return prob, var_names, recipes, recipe_counts_int


def construct_phase1(needs: Rates, settings: Settings):
    prob, var_names, recipes, recipe_counts = make_problem_constraints(
        "phase1", needs, settings
    )

    # want to minimize the number of work beavers required
    beaver_count = 0
    for ri, count in enumerate(recipe_counts):
        beaver_count += recipes[ri].input_workers * count
    prob += beaver_count

    # print(prob)
    # raise RuntimeError(prob)
    return prob, var_names


def construct_phase2(needs: Rates, settings: Settings, workers: int):
    prob, var_names, recipes, recipe_counts = make_problem_constraints(
        "phase2", needs, settings
    )

    # require that we're using a previously-discovered optimal number of beavers
    beaver_count = 0
    for ri, count in enumerate(recipe_counts):
        beaver_count += recipes[ri].input_workers * count
    prob += beaver_count <= workers

    # minimize tiles used
    counts = []
    for ri, count in enumerate(recipe_counts):
        counts += [recipes[ri].tiles * count]
    prob += lpSum(counts)

    # raise RuntimeError(prob)
    return prob, var_names


def solve(needs: Rates, settings: Settings):
    prob1, var_names1 = construct_phase1(needs, settings)
    status1, log1 = mypulp.solve(prob1)
    prob2, var_names2 = construct_phase2(needs, settings, value(prob1.objective))
    status2, log2 = mypulp.solve(prob2)

    vars = {
        var_names2[var]: value(var) for var in prob2.variables() if "_int" in str(var)
    }
    result = {
        "beavers": value(prob1.objective),
        "tiles": value(prob2.objective),
        "log": log1 + log2,
        "vars": vars,
    }
    # raise RuntimeError(result)
    return result


if __name__ == "__main__":
    needs = Rates({Item.BOT: 1 / 24})

    prob1 = construct_phase1(needs)

    print("==== PHASE 1 (optimal beavers) ====")
    status1 = prob1.solve()
    # for var in prob1.variables():
    #     print(var, value(var))
    print("beavers:", value(prob1.objective))

    print("==== PHASE 2 (minimum tiles) ====")
    prob2 = construct_phase2(needs, value(prob1.objective))

    status2 = prob2.solve()
    for var in prob1.variables():
        print(var, value(var))
    for var in prob2.variables():
        print(var, value(var))

    print("beavers:", value(prob1.objective))
    print("tiles:  ", value(prob2.objective))
