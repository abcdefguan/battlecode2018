
import battlecode as bc
from dice_roller import DiceRoller
from astronaut import Astronaut

class Astronomer:
	overcrowding_limit = 25; #I'll launch rockets if I have more than this no. of units
	rocket_panic_round = 550; #Note that there's another one of this variable in astronaut
	rocket_resource_requirement = 400; #Need this much resources to launch rocket
	can_reach_enemy = True; #Can I reach the enemy base from all of my start points?
	directions = [bc.Direction.East, bc.Direction.North, bc.Direction.Northeast,
	bc.Direction.Northwest, bc.Direction.South, bc.Direction.Southeast,
	bc.Direction.Southwest, bc.Direction.West];
	dirx = [0, 0, 1, -1, 1, 1, -1, -1];
	diry = [1, -1, 0, 0, 1, -1, 1, -1];

	def __init__(self, gc, intel_map):
		self.gc = gc;
		self.intel_map = intel_map;
		self.astronauts = {}; #dict (int => astronaut)
		self.all_rockets = None; #vecunit
		self.bfs = [[]];
		if (self.gc.planet() == bc.Planet.Earth):
			self.rocket_launches = []; #tuple[]
			self.has_rocket_landing = [[False for col in range(self.intel_map.mars_map_height)] for row in range(self.intel_map.mars_map_width)];
			self.bfs = [[1000000 for col in range(self.intel_map.mars_map_height)] for row in range(self.intel_map.mars_map_width)];
		#print("Mars has " + str(len(self.contiguous_value)) + " contiguous areas");

	def take_turn(self, rockets): #[unit] => void
		pattern = self.gc.asteroid_pattern();
		if (pattern.has_asteroid(self.gc.round())):
			strike = pattern.asteroid(self.gc.round())
			#print("Has Asteroid of size " + str(strike.karbonite) + " at " + str((strike.location.x, strike.location.y)));
			self.intel_map.increase_karbonite_at(strike.location, strike.karbonite);
		#Allow rockets to act
		for rocket in rockets:
			if (rocket.location.is_in_space()):
				continue;
			astro = self.astronauts.get(rocket.id);
			if astro is None:
				astro = Astronaut(self.gc, self.intel_map, self, rocket);
				self.astronauts[rocket.id] = astro;
				#print("Created Astronaut ID: " + str(rocket.id))
			if rocket.structure_is_built():
				#print("Astronaut taking turn");
				astro.take_turn(rocket)
		self.all_rockets = self.gc.sense_nearby_units_by_type(bc.MapLocation(self.gc.planet(), 0, 0), 1000000, bc.UnitType.Rocket);

	def should_build_rocket(self): # => bool
		#Should I build a rocket based on the game state?
		if self.gc.round() > Astronomer.rocket_panic_round:
			return True;
		else:
			if self.has_too_many_units(True):
				return True;
			return False;

	def has_too_many_units(self, compensate_rockets): #bool => bool
		my_units = self.gc.my_units();
		unit_cnt = 0;
		rocket_cnt = 0;
		rocket_capacity = 8;
		for unit in my_units:
			if (unit.unit_type != bc.UnitType.Factory and unit.unit_type != bc.UnitType.Rocket and unit.unit_type != bc.UnitType.Worker):
				unit_cnt += 1;
			if (unit.unit_type == bc.UnitType.Rocket and not(unit.location.is_in_space())):
				rocket_cnt += 1;
				rocket_capacity = unit.structure_max_capacity();

		if compensate_rockets:
			if (unit_cnt - rocket_cnt * rocket_capacity >= Astronomer.overcrowding_limit):
				return True;
		else:
			if (unit_cnt >= Astronomer.overcrowding_limit):
				return True;
		return False;

	def get_rocket_cnt(self): # => int
		my_units = self.gc.my_units();
		rocket_cnt = 0;
		for unit in my_units:
			if (unit.unit_type == bc.UnitType.Rocket and not(unit.location.is_in_space())):
				rocket_cnt += 1;
		return rocket_cnt;

	def should_do_resourcing(self): # => boolean
		if self.has_too_many_units(False):
			return False;
		elif self.gc.round() > Astronomer.rocket_panic_round:
			return False;
		#return True;
		return False;

	def nearest_rocket_requesting_unit(self, unit): # Unit => Unit
		best_rocket = None;
		least_dist_squared = 1000000;
		for rocket in self.all_rockets:
			if (rocket.team == self.gc.team()):
				astro = self.astronauts.get(rocket.id);
				if not(astro is None):
					if astro.is_requesting_unit_type(unit.unit_type):
						dist_squared = unit.location.map_location().distance_squared_to(rocket.location.map_location());
						if (dist_squared < least_dist_squared):
							least_dist_squared = dist_squared;
							best_rocket = rocket;
		return best_rocket;

	def get_salvation_rocket_land_location(self): # => MapLocation, shouldn't return None
		return self.get_random_rocket_land_location();
		if (self.gc.planet() == bc.Planet.Earth):
			if (len(self.rocket_launches) == 0):
				for i in range(self.intel_map.mars_map_width):
					for j in range(self.intel_map.mars_map_height):
						if (self.intel_map.mars_map[i][j] != -1):
							#ideally should be one of the corners
							return bc.MapLocation(bc.Planet.Mars, i, j);
				return None;
			else:
				for i in range(self.intel_map.mars_map_width):
					for j in range(self.intel_map.mars_map_height):
						self.bfs[i][j] = 1000000;
				queue = [];
				for launch_site in self.rocket_launches:
					queue.append(launch_site);
					self.bfs[launch_site[0]][launch_site[1]] = 0;
				print(queue);
				while (len(queue) > 0):
					launch_site = queue.pop(0);
					for i in range(len(Astronomer.dirx)):
						nx = launch_site[0] + Astronomer.dirx[i];
						ny = launch_site[1] + Astronomer.diry[i];
						#print("nx: " + str(nx) + " ny: " + str(ny));
						if (nx < 0 or nx >= self.intel_map.mars_map_width or ny < 0 or
							ny >= self.intel_map.mars_map_height or self.bfs[nx][ny] != 1000000):
							continue;
						#print("Passed: nx: " + str(nx) + " ny: " + str(ny));
						self.bfs[nx][ny] = self.bfs[launch_site[0]][launch_site[1]] + 1;
						if (self.bfs[nx][ny] >= 3 and self.intel_map.mars_map[nx][ny] != -1):
							del queue[:];
							return bc.MapLocation(bc.Planet.Mars, nx, ny);
						queue.append((nx, ny));
				return self.get_random_rocket_land_location();
		else:
			#print("Astronomer: Rockets shouldn't be launching from Mars !!");
			return None;

	def get_random_rocket_land_location(self): # => MapLocation, shouldn't return None
		all_landing_spots = [];
		if (self.gc.planet() == bc.Planet.Earth):
			for i in range(self.intel_map.mars_map_width):
				for j in range(self.intel_map.mars_map_height):
					if (not(self.has_rocket_landing[i][j]) and not(self.intel_map.mars_map[i][j] == -1)):
						all_landing_spots.append((i, j));
			if (len(all_landing_spots) > 0):
				landing_spot = all_landing_spots[DiceRoller.get_int(len(all_landing_spots))];
				return bc.MapLocation(bc.Planet.Mars, landing_spot[0], landing_spot[1]);
			return None;
		else:
			return None;


	def launch_rocket(self, landing_zone): #MapLocation, boolean => void
		if (self.gc.planet() == bc.Planet.Earth):
			self.rocket_launches.append((landing_zone.x, landing_zone.y));
			self.has_rocket_landing[landing_zone.x][landing_zone.y] = True;
		else:
			#print("Astronomer: Rockets shouldn't be launching from Mars !!");
			return;

	def no_connected_mode(): #Change the mode to a non connected mode
		Astronomer.can_reach_enemy = False;
		Astronaut.max_wait_time = 50;