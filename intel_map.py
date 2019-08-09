
import battlecode as bc;

class IntelMap:
	directions = [bc.Direction.East, bc.Direction.North, bc.Direction.Northeast,
	bc.Direction.Northwest, bc.Direction.South, bc.Direction.Southeast,
	bc.Direction.Southwest, bc.Direction.West];

	def __init__ (self, gc):
		#Initate teh variables
		self.earth_map = [[]];
		self.earth_unit_map = [[]];
		self.mars_map = [[]];
		self.mars_unit_map = [[]];
		self.earth_map_width = 0;
		self.earth_map_height = 0;
		self.mars_map_width = 0;
		self.mars_map_height = 0;
		self.my_team = None;
		self.gc = gc;
		self.earth_friendly_starting_points = []; #MapLocation[]
		self.earth_enemy_starting_points = []; #MapLocation[]
		self.mars_friendly_starting_points = []; #MapLocation[]
		self.cached_earth_karbonite = 0;
		self.cached_mars_karbonite = 0;

		#Construct an intel map from each of the starting planet maps
		earth_start_map = self.gc.starting_map(bc.Planet.Earth);
		init_units = earth_start_map.initial_units;
		#print("Init units: " + str(len(init_units)));
		self.earth_friendly_starting_points = [None for row in range(int(len(init_units) / 2))];
		self.earth_enemy_starting_points = [None for row in range(int(len(init_units) / 2))];

		friendly_cnt = 0;
		enemy_cnt = 0;
		for init_unit in init_units:
			if (init_unit.team == self.gc.team()):
				self.earth_friendly_starting_points[friendly_cnt] = init_unit.location.map_location();
				friendly_cnt += 1;
			else:
				self.earth_enemy_starting_points[enemy_cnt] = init_unit.location.map_location();
				enemy_cnt += 1;
		self.earth_map_width = earth_start_map.width;
		self.earth_map_height = earth_start_map.height;

		self.earth_map = [[0 for col in range(self.earth_map_height)] for row in range(self.earth_map_width)];
		self.earth_unit_map = [[0 for col in range(self.earth_map_height)] for row in range(self.earth_map_width)];

		for i in range(self.earth_map_width):
			for j in range(self.earth_map_height):
				loc = bc.MapLocation(bc.Planet.Earth, i, j);

				if (earth_start_map.is_passable_terrain_at(loc)):
					self.earth_map[i][j] = earth_start_map.initial_karbonite_at(loc);
				else:
					self.earth_map[i][j] = -1;

		mars_start_map = self.gc.starting_map(bc.Planet.Mars);
		self.mars_map_width = mars_start_map.width;
		self.mars_map_height = mars_start_map.height;

		self.mars_map = [[0 for col in range(self.mars_map_height)] for row in range(self.mars_map_width)];
		self.mars_unit_map = [[0 for col in range(self.mars_map_height)] for row in range(self.mars_map_width)];

		for i in range(self.mars_map_width):
			for j in range(self.mars_map_height):
				loc = bc.MapLocation(bc.Planet.Mars, i, j);

				if (mars_start_map.is_passable_terrain_at(loc)):
					self.mars_map[i][j] = mars_start_map.initial_karbonite_at(loc);
				else:
					self.mars_map[i][j] = -1;
		self.my_team = self.gc.team();

	def update_map(self): # => void, to be run every turn to refresh unit maps
		for i in range(self.earth_map_width):
			for j in range(self.earth_map_height):
				self.earth_unit_map[i][j] = 0;
		for i in range(self.mars_map_width):
			for j in range(self.mars_map_height):
				self.mars_unit_map[i][j] = 0;
		all_units = self.gc.sense_nearby_units(bc.MapLocation(self.gc.planet(), 0, 0), 1000000);
		for unit in all_units:
			self.set_unit_at(unit.location.map_location(), unit);
		self.cached_earth_karbonite = self.calc_map_karbonite(bc.Planet.Earth);
		self.cached_mars_karbonite = self.calc_map_karbonite(bc.Planet.Mars);

	def set_karbonite_at(self, loc, val): #MapLocation, int => void
		if (loc.planet == bc.Planet.Earth):
			if (self.earth_map[loc.x][loc.y] != -1):
				self.earth_map[loc.x][loc.y] = val;
		else:
			if (self.mars_map[loc.x][loc.y] != -1):
				self.mars_map[loc.x][loc.y] = val;

	def is_valid_loc(self, loc): #MapLocation => bool
		if (loc.planet == bc.Planet.Earth):
			if (loc.x < 0 or loc.x >= self.earth_map_width or loc.y < 0 or loc.y >= self.earth_map_height):
				return False;
			return True;
		else:
			if (loc.x < 0 or loc.x >= self.mars_map_width or loc.y < 0 or loc.y >= self.mars_map_height):
				return False;
			return True;

	def is_passable(self, loc): #MapLocation => bool
		if (not(self.is_valid_loc(loc))):
			return False;
		if (loc.planet == bc.Planet.Earth):
			if (self.earth_map[loc.x][loc.y] != -1):
				return True;
			else:
				return False;
		else:
			if (self.mars_map[loc.x][loc.y] != -1):
				return True;
			else:
				return False;

	def increase_karbonite_at(self, loc, delta): #MapLocation, long => void
		#print(loc);
		if (loc.planet == bc.Planet.Earth):
			if (self.earth_map[loc.x][loc.y] != -1):
				self.earth_map[loc.x][loc.y] += delta;
		else:
			if (self.mars_map[loc.x][loc.y] != -1):
				self.mars_map[loc.x][loc.y] += delta;

	def set_unit_at(self, loc, unit): #MapLocation, Unit
		computedId = 0;
		if (unit.team == self.my_team):
			if (unit.unit_type == bc.UnitType.Factory):
				computedId = 1000000000 + unit.id;
			elif (unit.unit_type == bc.UnitType.Worker):
				computedId = 1250000000 + unit.id;
			elif (unit.unit_type == bc.UnitType.Rocket):
				computedId = 1500000000 + unit.id;
			else:
				computedId = unit.id + 1;
		else:
			computedId = -(unit.id + 1);
		if loc.planet == bc.Planet.Earth:
			self.earth_unit_map[loc.x][loc.y] = computedId;
		else:
			self.mars_unit_map[loc.x][loc.y] = computedId;

	def get_unit_at(self, loc): #MapLocation => int, returns -1 if no unit, unitID if got unit
		#Note: Any changes to this will require changes to mover.py at earth precomp resources
		computedId = 0;
		if (loc.planet == bc.Planet.Earth):
			computedId = self.earth_unit_map[loc.x][loc.y];
		else:
			computedId = self.mars_unit_map[loc.x][loc.y];
		if (computedId == 0):
			return -1;
		else:
			if (computedId >= 1500000000):
				return computedId - 1500000000;
			elif (computedId >= 1250000000):
				return computedId - 1250000000;
			elif (computedId >= 1000000000):
				return computedId - 1000000000;
			if (computedId > 0):
				return computedId - 1;
			else:
				return -(computedId) - 1;

	def remove_unit_from(self, loc): #MapLocation => void
		if (loc.planet == bc.Planet.Earth):
			self.earth_unit_map[loc.x][loc.y] = 0;
		else:
			self.mars_unit_map[loc.x][loc.y] = 0;

	def move_unit(self, unit, direc): #Unit, Direction => void
		self.remove_unit_from(unit.location.map_location());
		loc = unit.location.map_location().add(direc);
		self.set_unit_at(loc, unit);

	def calc_map_karbonite(self, planet): #Planet => int
		ans = 0;
		if (planet == bc.Planet.Earth):
			for i in range(self.earth_map_width):
				for j in range(self.earth_map_height):
					if (self.earth_map[i][j] >= 0):
						ans += self.earth_map[i][j];
		else:
			for i in range(self.mars_map_width):
				for j in range(self.mars_map_height):
					if (self.mars_map[i][j] >= 0):
						ans += self.mars_map[i][j];
		return ans;

	def get_map_karbonite(self, planet): #Planet => int
		if (planet == bc.Planet.Earth):
			return self.cached_earth_karbonite;
		else:
			return self.cached_mars_karbonite;

	def is_on_map(self, loc):
		if (loc.planet == bc.Planet.Earth):
			if (loc.x < 0 or loc.x >= self.earth_map_width or loc.y < 0 or loc.y >= self.earth_map_height):
				return False;
			return True;
		else:
			if (loc.x <0 or loc.x >= self.mars_map_width or loc.y < 0 or loc.y >= self.mars_map_height):
				return False;
			return True;

	def dist_squared_to_starting_point(self, loc): #MapLocation => long
		if (loc.planet == bc.Planet.Earth):
			ans = 1000000000;
			for i in range(len(self.earth_friendly_starting_points)):
				dist_squared = self.earth_friendly_starting_points[i].distance_squared_to(loc);
				if (dist_squared < ans):
					ans = dist_squared;
			return ans;
		else:
			ans = 1000000000;
			for i in range(len(self.mars_friendly_starting_points)):
				dist_squared = self.mars_friendly_starting_points[i].distance_squared_to(loc);
				if (dist_squared < ans):
					ans = dist_squared;
			return ans;

	def update_karbonite_info(self, unit): #Unit => void
		for direc in IntelMap.directions:
			new_loc = unit.location.map_location().add(direc);
			if (self.gc.can_sense_location(new_loc)):
				self.set_karbonite_at(new_loc, self.gc.karbonite_at(new_loc));
		if self.gc.can_sense_location(unit.location.map_location()):
			self.set_karbonite_at(unit.location.map_location(), self.gc.karbonite_at(unit.location.map_location()));

	def get_default_rally_point(self, p): #Planet => MapLocation
		if (p == bc.Planet.Earth):
			enemy_pos = self.earth_enemy_starting_points[0];
			return enemy_pos;
		else:
			return bc.MapLocation(bc.Planet.Mars, 10, 10);