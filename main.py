from dataclasses import dataclass, field
from drafter import *

@dataclass
class Plant:
    name: str
    watering_cycle: int          # days between waterings
    species: str
    last_watered: int = 0        # day count when last watered
    def needs_water(self, today: int) -> bool:
        return (today - self.last_watered) >= self.watering_cycle

@dataclass
class State:
    plants: list[Plant] = field(default_factory=list)
    selected_plant: Plant | None = None
    care_tips: dict[str, str] = field(default_factory=dict)
    today: int = 0

set_website_title("Plant Care Tracker")
set_site_information(
    author="Your Name",
    description="Track watering schedules and care tips for all your houseplants.",
    sources="Thanks to the Drafter docs and my study group.",
    planning=["CS1 Final Project 1_ Design.pdf"],
    links=["https://github.com/your-username/your-repository"]
)
hide_debug_information()
set_website_framed(False)


@route
def index(state: State) -> Page:
    return Page([
        Text("Plant Care Tracker"),
        Button("Garden View", garden_view),
        Button("Add Plant", add_plant_page),
        Button("Delete Plant", delete_plant_page),
        Button("Filter by Needs Watering", filter_plants),
    ])

@route
def garden_view(state: State) -> Page:
    widgets = [Text("Your Garden")]
    for plant in state.plants:                 # loop over the list of instances
        status = "Needs water" if plant.needs_water(state.today) else "Happy"
        widgets.append(Text(f"{plant.name} ({plant.species}) - {status}"))
        widgets.append(Button(f"View {plant.name}", view_plant, plant.name))
        widgets.append(Button(f"Water {plant.name}", water_plant_page, plant.name))
        widgets.append(Button("Next Day", next_day))
    widgets.append(Button("Home", index))
    return Page(widgets)

@route
def plant_detail(state: State) -> Page:
    plant = state.selected_plant
    if plant is None:                          # if #4
        return garden_view(state)
    return Page([
        Text(f"{plant.name} - {plant.species}"),
        Text(f"Water every {plant.watering_cycle} days"),
        Text(f"Last watered on day {plant.last_watered}"),
        Button("Care Tips", care_tips_page, plant.species),
        Button("Back to Garden", garden_view),
    ])

@route
def tips_view(state: State) -> Page:
    widgets = [Text("Care Tips")]
    for species, tip in state.care_tips.items():   # loop over the dict
        widgets.append(Text(f"{species}: {tip}"))
    widgets.append(Button("Home", index))
    return Page(widgets)

@route
def delete_plant(state: State, name: str) -> Page:
    state.plants = [p for p in state.plants if p.name != name]
    return garden_view(state)

@route
def add_plant(state: State, name: str, cycle: str, species: str) -> Page:
    if name and cycle.isdigit() and int(cycle) > 0:
        state.plants.append(Plant(name, int(cycle), species, state.today))
    return garden_view(state)

@route
def next_day(state: State) -> Page:
    state.today += 1
    return garden_view(state)

@route
def water_plant(state: State, name: str, confirm: bool) -> Page:
    for plant in state.plants:
        if plant.name == name and confirm:     # if #2, now meaningful
            plant.last_watered = state.today
    return garden_view(state)

@route
def water_plant_page(state: State, name: str) -> Page:
    return Page([
        Text(f"Mark {name} as watered?"),
        CheckBox("confirm", "Yes, I watered it"),
        Button("Confirm", water_plant, name, "confirm"),
    ])

@route
def filter_plants(state: State) -> Page:
    state.plants.sort(key=lambda p: not p.needs_water(state.today))
    return garden_view(state)

@route
def view_plant(state: State, name: str) -> Page:
    for plant in state.plants:
        if plant.name == name:
            state.selected_plant = plant
    return plant_detail(state)

@route
def care_tips_page(state: State, species: str) -> Page:
    if species not in state.care_tips:
        state.care_tips[species] = "Water every few days; bright indirect light."
    return tips_view(state)

@route
def add_plant_page(state: State) -> Page:
    return Page([
        Text("Add a Plant"),
        TextBox("name", "Plant name"),
        TextBox("cycle", "Water every N days"),
        TextBox("species", "Species"),
        Button("Add", add_plant),
    ])

@route
def delete_plant_page(state: State) -> Page:
    options = [plant.name for plant in state.plants]
    return Page([
        Text("Delete a Plant"),
        SelectBox("name", "Choose a plant", options),
        Button("Delete", delete_plant),
    ])

start_server(State())
