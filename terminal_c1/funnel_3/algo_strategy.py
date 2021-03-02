import gamelib
import random
import math
import warnings
from sys import maxsize
import json

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)

        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  # Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # First, place basic defenses
        self.build_defences(game_state)

        if game_state.turn_number % 7 == 1:
            if game_state.turn_number > 25:
                game_state.attempt_spawn(SCOUT, [8, 5], 12)
            if game_state.turn_number:
                game_state.attempt_spawn(SCOUT, [4, 9], 1000)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """

        turret_locations_0 = [[2, 12], [25, 12], [6, 10], [21, 10], [11, 9], [16, 9]]
        turret_locations_1 = [[1, 12], [26, 12], [3, 11], [24, 11], [5, 10], [22, 10], [8, 9], [10, 9], [17, 9],
                              [19, 9], [12, 8], [15, 8], [11,8], [11,7], [11,6]]
        wall_locations_0 = [[11, 10], [16, 10], [0, 13], [1, 13], [2, 13], [25, 13], [26, 13], [27, 13], [6, 11],
                            [21, 11], [3, 12], [24, 12], [4, 11], [5, 11], [22, 11], [23, 11], [7, 10], [8, 10],
                            [9, 10], [10, 10], [12, 10], [15, 10], [17, 10], [18, 10], [19, 10], [20, 10], [12, 9],
                            [15, 9], [7, 11], [8, 11]]
        wall_locations_1 = [[3, 13], [24, 13]]

        game_state.attempt_spawn(TURRET, turret_locations_0)
        game_state.attempt_spawn(WALL, wall_locations_0)
        game_state.attempt_upgrade(turret_locations_0)
        game_state.attempt_upgrade(wall_locations_0)

        if game_state.turn_number % 7 > 1 or 2 < game_state.turn_number < 20:
            game_state.attempt_spawn(WALL, [[13, 9], [14, 9]])
            game_state.attempt_upgrade([[13, 9], [14, 9]])

        if game_state.turn_number % 7 < 1 and game_state.turn_number > 1:
            game_state.attempt_remove([[13, 9], [14, 9]])

        if game_state.turn_number > 30:
            game_state.attempt_spawn(SUPPORT, [[3, 10], [4, 10], [6, 9], [7, 9]], 1)
            game_state.attempt_upgrade([[3, 10], [4, 10], [6, 9], [7, 9]])

        if game_state.turn_number > 25 and game_state.turn_number % 7 == 1:
            game_state.attempt_spawn(INTERCEPTOR, [7, 6], 2)

        if game_state.turn_number > 15:
            game_state.attempt_spawn(SUPPORT, [6, 7], 1)
            game_state.attempt_upgrade([6, 7])
            game_state.attempt_spawn(SUPPORT, [7, 7], 1)
            game_state.attempt_upgrade([7, 7])
            game_state.attempt_spawn(SUPPORT, [8, 7], 1)
            game_state.attempt_upgrade([8, 7])
            game_state.attempt_spawn(SUPPORT, [9, 7], 1)
            game_state.attempt_upgrade([9, 7])
            game_state.attempt_spawn(SUPPORT, [7, 6], 1)
            game_state.attempt_upgrade([7, 6])
            game_state.attempt_spawn(SUPPORT, [8, 6], 1)
            game_state.attempt_upgrade([8, 6])
            game_state.attempt_spawn(SUPPORT, [9, 6], 1)
            game_state.attempt_upgrade([9, 6])

        if game_state.turn_number > 20:
            game_state.attempt_spawn(TURRET, turret_locations_1)
            game_state.attempt_spawn(WALL, wall_locations_1)
            game_state.attempt_upgrade(turret_locations_1)
            game_state.attempt_upgrade(wall_locations_1)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames
        as shown in the on_action_frame function
        """
        if game_state.turn_number > 5:
            locs = self.scored_on_locations[::-1]

            spawn_cnt = 0
            for location in locs:
                # Build turret 1-3 spaces above so that it doesn't block our own edge spawn locations
                build_location1 = [location[0], location[1] + 1]
                bad = [[11, 3], [16, 3], [17, 4]]
                if build_location1 not in bad:
                    game_state.attempt_upgrade(build_location1)
                    game_state.attempt_spawn(TURRET, build_location1)

    def stall_with_interceptors(self, game_state):
        pass
        # use these frugally in late game
        # if game_state.turn_number > 12:
        #     loc = self.scored_on_locations[0]
        #     game_state.attempt_spawn(INTERCEPTOR, loc, 1)

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """

        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET,
                                                                                             game_state.config).damage_i
            damages.append(damage)

        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (
                            valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
