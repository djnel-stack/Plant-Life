"""
Plant Watering Tracker
======================

A small Drafter website that helps plant owners keep track of when their
plants need water and gives species-specific care tips.

Structure of this file:
    1. Imports and setup
    2. Dataclasses (Plant, State)
    3. Helper functions (no routes in here)
    4. Routes (one function per page)
    5. App setup / run

Concepts used: dataclasses, lists, loops, conditionals, dicts, user input.
"""

from dataclasses import dataclass, field
from datetime import date

from drafter import (
    start_server, route, Page, TextBox, SelectBox, CheckBox, Button,
    Link, Header, HorizontalRule,
)


# ============================================================
# 1) DATACLASSES
# ============================================================

@dataclass
class Plant:
    """
    One plant in the user's garden.

    name:           what the user calls the plant (e.g. "Monstera")
    watering_cycle: how many days between waterings (e.g. 7)
    species:        plant type, used to look up care tips (e.g. "Succulent")
    last_watered:   the date the plant was last watered
    """
    name: str
    watering_cycle: int
    species: str
    last_watered: date


@dataclass
class State:
    """
    Everything that must persist across the whole site.

    plants:    the user's full inventory of Plant objects
    selected:  the plant the user is currently looking at (or None)
    care_tips: species name -> a tip string
    """
    plants: list = field(default_factory=list)
    selected: Plant = None
    care_tips: dict = field(default_factory=lambda: {
        "Succulent": "Water rarely. Let the soil dry out completely between waterings.",
        "Fern": "Keep the soil moist. Loves humidity and indirect light.",
        "Cactus": "Water only once every few weeks. Needs lots of sunlight.",
        "Pothos": "Water when the top inch of soil is dry. Tolerates low light.",
        "Orchid": "Water once a week by soaking the roots. Never leave it in standing water.",
    })


# ============================================================
# 2) HELPER FUNCTIONS
# ============================================================

def days_since_watered(plant: Plant) -> int:
    """Return how many whole days have passed since this plant was watered."""
    return (date.today() - plant.last_watered).days


def needs_water(plant: Plant) -> bool:
    """
    Decide whether a plant is due for water.

    A plant needs water once the days since watering reach its watering cycle.
    """
    if days_since_watered(plant) >= plant.watering_cycle:
        return True
    else:
        return False


def status_label(plant: Plant) -> str:
    """Return a short, human-readable status string for display."""
    if needs_water(plant):
        return "Needs water"
    else:
        return "Okay"


def urgency(plant: Plant) -> int:
    """How many days overdue this plant is. Higher means more urgent."""
    return days_since_watered(plant) - plant.watering_cycle


def sorted_plants(plants: list) -> list:
    """
    Return the plants ordered by urgency (most overdue first).

    The loop below builds a new list by repeatedly pulling out the most
    urgent remaining plant, so the garden view always shows thirsty plants
    at the top.
    """
    remaining = list(plants)
    ordered = []
    while len(remaining) > 0:
        most_urgent = remaining[0]
        for plant in remaining:
            if urgency(plant) > urgency(most_urgent):
                most_urgent = plant
        ordered.append(most_urgent)
        remaining.remove(most_urgent)
    return ordered


def find_plant(state: State, name: str) -> Plant:
    """Look up a plant by name. Returns None if it isn't in the garden."""
    for plant in state.plants:
        if plant.name == name:
            return plant
    return None


def plant_names(state: State) -> list:
    """Return a plain list of every plant name, for use in select boxes."""
    names = []
    for plant in state.plants:
        names.append(plant.name)
    return names


# ============================================================
# 3) ROUTES
# ============================================================

@route
def index(state: State) -> Page:
    """Home page: links to every other part of the site."""
    return Page(state, [
        Header("Plant Watering Tracker"),
        "Welcome! Keep your plants happy and healthy.",
        HorizontalRule(),
        Link("View my garden", garden_view),
        Link("Add a plant", add_plant),
        Link("Water a plant", water_plants),
        Link("Delete a plant", delete_plant),
        Link("View a plant's details", view_plant),
        Link("Filter: needs water", filter_plants),
        Link("Care tips", care_tips),
    ])


@route
def garden_view(state: State) -> Page:
    """
    Garden view: show every plant with its status.

    Plants are ordered by urgency so the ones needing water appear first.
    """
    content = [Header("Your Garden"), Link("Back home", index)]

    if len(state.plants) == 0:
        content.append("You haven't added any plants yet.")
    else:
        for plant in sorted_plants(state.plants):
            content.append(
                plant.name + " (" + plant.species + ") — "
                + status_label(plant) + " — "
                + "watered " + str(days_since_watered(plant)) + " day(s) ago, "
                + "cycle: every " + str(plant.watering_cycle) + " day(s)"
            )

    return Page(state, content)


@route
def add_plant(state: State, name: str = "", cycle: str = "", species: str = "") -> Page:
    """
    Add plant page.

    Three text boxes collect the name, watering cycle, and species.
    The cycle arrives as text, so we convert it to an int and validate it.
    """
    error = ""

    if name != "" and cycle != "" and species != "":
        if not cycle.isdigit():
            error = "Watering cycle must be a whole number of days."
        elif find_plant(state, name) is not None:
            error = "You already have a plant with that name."
        else:
            new_plant = Plant(
                name=name,
                watering_cycle=int(cycle),
                species=species,
                last_watered=date.today(),
            )
            state.plants.append(new_plant)
            return garden_view(state)

    content = [Header("Add a Plant"), Link("Back home", index)]
    if error != "":
        content.append(error)

    content.append(TextBox("name", name))
    content.append("Watering cycle (days):")
    content.append(TextBox("cycle", cycle))
    content.append("Species:")
    content.append(TextBox("species", species))
    content.append(Button("Add plant", add_plant))
    return Page(state, content)


@route
def delete_plant(state: State, plant_name: str = "") -> Page:
    """
    Delete plant page.

    A select box lists every plant; choosing one and pressing the button
    removes it from the inventory.
    """
    if len(state.plants) == 0:
        return Page(state, [
            Header("Delete a Plant"),
            "There are no plants to delete.",
            Link("Back home", index),
        ])

    if plant_name != "":
        plant = find_plant(state, plant_name)
        if plant is not None:
            state.plants.remove(plant)
        return garden_view(state)

    return Page(state, [
        Header("Delete a Plant"),
        Link("Back home", index),
        SelectBox("plant_name", plant_names(state)),
        Button("Delete plant", delete_plant),
    ])


@route
def water_plants(state: State, plant_name: str = "", confirm: bool = False) -> Page:
    """
    Water plant page.

    A select box picks the plant and a checkbox confirms the watering.
    When confirmed, the plant's last_watered date is reset to today.
    """
    if len(state.plants) == 0:
        return Page(state, [
            Header("Water a Plant"),
            "You haven't added any plants yet.",
            Link("Add a plant", add_plant),
        ])

    if plant_name != "" and confirm:
        plant = find_plant(state, plant_name)
        if plant is not None:
            plant.last_watered = date.today()
        return garden_view(state)

    return Page(state, [
        Header("Water a Plant"),
        Link("Back home", index),
        SelectBox("plant_name", plant_names(state)),
        CheckBox("confirm", False),
        "I watered this plant today",
        Button("Mark as watered", water_plants),
    ])


@route
def view_plant(state: State, plant_name: str = "") -> Page:
    """
    View plant page.

    Shows every attribute of the selected plant. The chosen plant is also
    stored in state.selected so other pages could reuse it.
    """
    if len(state.plants) == 0:
        return Page(state, [
            Header("View a Plant"),
            "You haven't added any plants yet.",
            Link("Add a plant", add_plant),
        ])

    if plant_name != "":
        plant = find_plant(state, plant_name)
        if plant is not None:
            state.selected = plant
            return Page(state, [
                Header(plant.name),
                Link("Back home", index),
                "Species: " + plant.species,
                "Watering cycle: every " + str(plant.watering_cycle) + " day(s)",
                "Last watered: " + str(plant.last_watered),
                "Days since watering: " + str(days_since_watered(plant)),
                "Status: " + status_label(plant),
            ])

    return Page(state, [
        Header("View a Plant"),
        Link("Back home", index),
        SelectBox("plant_name", plant_names(state)),
        Button("View plant", view_plant),
    ])


@route
def filter_plants(state: State) -> Page:
    """
    Filter page: show only the plants that need water, most urgent first.
    """
    thirsty = []
    for plant in sorted_plants(state.plants):
        if needs_water(plant):
            thirsty.append(plant)

    content = [Header("Plants That Need Water"), Link("Back home", index)]

    if len(thirsty) == 0:
        content.append("Nothing needs water right now. Nice work!")
    else:
        for plant in thirsty:
            content.append(
                plant.name + " — " + str(urgency(plant)) + " day(s) overdue"
            )

    return Page(state, content)


@route
def care_tips(state: State, species: str = "") -> Page:
    """
    Care tips page.

    A select box lists the species the site knows about. The matching tip
    is pulled from the state.care_tips dictionary.
    """
    if species != "":
        tip = state.care_tips.get(species, "No tips available for that species yet.")
        return Page(state, [
            Header("Care Tips: " + species),
            Link("Back home", index),
            tip,
        ])

    return Page(state, [
        Header("Care Tips"),
        Link("Back home", index),
        SelectBox("species", list(state.care_tips.keys())),
        Button("Show tips", care_tips),
    ])


# ============================================================
# 4) RUN THE APP
# ============================================================

start_server(State())

