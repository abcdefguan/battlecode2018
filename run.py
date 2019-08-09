import battlecode as bc
import sys
import traceback
import time
from astronaut import Astronaut
from astronomer import Astronomer
from commander import Commander
from intel_map import IntelMap
from mover import Mover
from engineer import Engineer
from researcher import Researcher
import random
import gc as garbage




# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.

knight_use_dist = 20;

gcc = bc.GameController()

if (gcc.team() == bc.Team.Red):
    random.seed(1337);
else:
    random.seed(2631);


# It's a good idea to try to keep your bots deterministic, to make debugging easier.
# determinism isn't required, but it means that the same things will happen in every thing you run,
# aside from turns taking slightly different amounts of time due to noise.

#initiate a new intel map from the game controller
intel_map = IntelMap(gcc)

#initiate a new mover => to help units move
mov = Mover(gcc, intel_map)

mov.precomp();

furthest_dist = -100;
knight_rush = False;
if (gcc.planet() == bc.Planet.Earth):
    for start_pt in intel_map.earth_friendly_starting_points:
        furthest_dist = max(furthest_dist, mov.unit_bfs[start_pt.x][start_pt.y]);
    print("Furthest dist is: " + str(furthest_dist));
    if (furthest_dist < knight_use_dist and furthest_dist > 0):
        Engineer.unit_ratio_early_game = [0, 1, 0, 0, 0]; #All knights
        Engineer.knight_override = True;

#initiate an astronomer to perform astronomy stuff
astro = Astronomer(gcc, intel_map)

#initiate other crucial modules
chief_engineer = Engineer(gcc, intel_map, mov, astro)
general = Commander(gcc, intel_map, mov, astro)
chief_researcher = Researcher(gcc, intel_map)

#A quick fix to some rocket panic bug for Mars
if (gcc.planet() == bc.Planet.Mars):
    Astronomer.rocket_panic_round = 1500;

def get_short_form(dir):
    if (dir == bc.Direction.North):
        return "N ";
    elif (dir == bc.Direction.South):
        return "S ";
    elif (dir == bc.Direction.West):
        return "W ";
    elif (dir == bc.Direction.East):
        return "E ";
    elif (dir == bc.Direction.Northeast):
        return "NE";
    elif (dir == bc.Direction.Northwest):
        return "NW";
    elif (dir == bc.Direction.Southeast):
        return "SE";
    elif (dir == bc.Direction.Southwest):
        return "SW";
    else:
        return "??";


while True:
    # We only support Python 3, which means brackets around print()
    #print('pyround:', gcc.round(), 'time left:', gcc.get_time_left_ms(), 'ms')
    # frequent try/catches are a good idea
    try:
        intel_map.update_map()
        my_factories = []
        my_rockets = []
        my_workers = []
        my_offensive_units = []
        unit_cnt = [0,0,0,0,0]
        my_units = gcc.my_units();
        all_units = gcc.units();

        # walk through our units:
        for unit in my_units:
            if unit.unit_type == bc.UnitType.Worker:
                unit_cnt[0] += 1;
            elif unit.unit_type == bc.UnitType.Knight:
                unit_cnt[1] += 1;
            elif unit.unit_type == bc.UnitType.Ranger:
                unit_cnt[2] += 1;
            elif unit.unit_type == bc.UnitType.Mage:
                unit_cnt[3] += 1;
            elif unit.unit_type == bc.UnitType.Healer:
                unit_cnt[4] += 1;

            if unit.location.is_in_garrison() or unit.location.is_in_space():
                continue;

            if unit.unit_type == bc.UnitType.Worker:
                my_workers.append(unit);
            elif unit.unit_type == bc.UnitType.Factory:
                my_factories.append(unit);
            elif unit.unit_type == bc.UnitType.Rocket:
                my_rockets.append(unit);
            else:
                my_offensive_units.append(unit);

            intel_map.set_unit_at(unit.location.map_location(), unit)

        if (gcc.round() < Engineer.early_game_end and Engineer.knight_override):
            mage_counter = False;
            cannot_mage_counter = False;
            for unit in all_units:
                if (unit.unit_type == bc.UnitType.Knight and unit.team != gcc.team()):
                    mage_counter = True;
                elif (unit.unit_type == bc.UnitType.Ranger and unit.team != gcc.team()):
                    cannot_mage_counter = True;
                    break;
            if (mage_counter and not(cannot_mage_counter)):
                Engineer.mage_override = True;
                Engineer.unit_ratio_early_game = [0, 0, 0, 2, 0];
            else:
                Engineer.mage_override = False;
                Engineer.unit_ratio_early_game = [0, 0, 2, 0, 1];

        def cmp_unit(unit):
            if (unit.unit_type == bc.UnitType.Healer):
                return 1;
            else:
                return 0;

        #print("My unit count is: ");

        #for i in range(0, 5):
        #    print(str(unit_cnt[i]) + " ", end='');
        #print("");
        #Only precomp when it's my turn
        #if (not(mov.is_precomp_resources_complete())):
        #    mov.do_actual_precomp_resources();
        mov.precomp_resources();

        chief_engineer.take_turn(my_workers, my_factories, unit_cnt);
        astro.take_turn(my_rockets);
        #if (not(mov.is_precomp_complete())):
        #    mov.do_actual_precomp();
        #debug the astronomer
        #if (gcc.planet() == bc.Planet.Earth and gcc.round() == 1):
        #    for i in range(5):
        #        landing_site = astro.get_salvation_rocket_land_location();
        #        print("Recommended landing site at: (" + str(landing_site.x) + " , " + str(landing_site.y) + ")");
        #        astro.launch_rocket(landing_site);
        #        for i in range(intel_map.mars_map_width):
        #            for j in range(intel_map.mars_map_height):
        #                print(astro.bfs[i][j], end=' ');
        #            print("");
        mov.precomp();

        #Astronomer.no_connected_mode();
        #can_reach = True;
        #if (gcc.round() == 1):
        #    if (gcc.planet() == bc.Planet.Earth):
        #        for i in range(len(intel_map.earth_friendly_starting_points)):
        #            starting_pt = intel_map.earth_friendly_starting_points[i];
        #            if (mov.prev_move[starting_pt.x][starting_pt.y] is None):
        #                Astronomer.no_connected_mode();
        #                print("Cannot reach enemy");
        #                can_reach = False;

        #    if (can_reach):
        #        print("Can reach enemy");

        #debug the precomp
        #if (gcc.round() == 250 or gcc.round() == 150):
        #    for i in range(intel_map.mars_map_width):
        #        for j in range(intel_map.mars_map_height):
        #            print(intel_map.mars_map[i][j], end=' ');
        #        print("");
        #for i in range(intel_map.earth_map_width):
        #    for j in range(intel_map.earth_map_height):
        #        print(get_short_form(mov.prev_move[i][j]), end=' ');
        #    print("");
        general.take_turn(sorted(my_offensive_units, key=cmp_unit)); #will put other units first, healers last
        chief_researcher.take_turn();
        del my_factories[:]
        del my_rockets[:]
        del my_workers[:]
        del my_offensive_units[:]
        
        for unit in my_units:
            del unit;

        if (gcc.round() % 3 == 0):
            #start_time = time.time();
            garbage.collect();
            #print("time taken to garbage collect: " + str((time.time() - start_time) * 1000));

    except Exception as e:
        print('Error:', e)
        # use this to show where the error was
        traceback.print_exc()


    # send the actions we've performed, and wait for our next turn.
    gcc.next_turn()

    # these lines are not strictly necessary, but it helps make the logs make more sense.
    # it forces everything we've written this turn to be written to the manager.
    sys.stdout.flush()
    sys.stderr.flush()

