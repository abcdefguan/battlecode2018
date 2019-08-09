
import battlecode as bc
from dice_roller import DiceRoller
from helper import Helper
from role import Role
from astronomer import Astronomer
import time

class Mover:
	search_depth_delta = 1
	past_locations_remembered = 10
	max_random_tries = 20
	max_bfs_depth = 12
	max_precomp_time = 0.030; #max 30 milliseconds
	dirx = [0, 0, 1, 1, 1, -1, -1, -1];
	diry = [-1, 1, -1, 0, 1, -1, 0, 1];
	directions = [bc.Direction.South, bc.Direction.North, bc.Direction.Southeast,
	bc.Direction.East, bc.Direction.Northeast, bc.Direction.Southwest,
	bc.Direction.West, bc.Direction.Northwest]

	def __init__(self, gc, intel_map): #GameController, IntelMap
		self.gc = gc;
		self.intel_map = intel_map;
		if (self.gc.planet() == bc.Planet.Earth):
			self.bfs = [[0 for col in range(self.intel_map.earth_map_height)] for row in range(self.intel_map.earth_map_width)];
			self.prev_move = [[None for col in range(self.intel_map.earth_map_height)] for row in range(self.intel_map.earth_map_width)];
			self.unit_bfs = [[0 for col in range(self.intel_map.earth_map_height)] for row in range(self.intel_map.earth_map_width)];
			self.unit_prev_move = [[None for col in range(self.intel_map.earth_map_height)] for row in range(self.intel_map.earth_map_width)];
		else:
			self.bfs = [[0 for col in range(self.intel_map.mars_map_height)] for row in range(self.intel_map.mars_map_width)];
			self.prev_move = [[None for col in range(self.intel_map.mars_map_height)] for row in range(self.intel_map.mars_map_width)];
			self.unit_bfs = [[0 for col in range(self.intel_map.mars_map_height)] for row in range(self.intel_map.mars_map_width)];
			self.unit_prev_move = [[None for col in range(self.intel_map.mars_map_height)] for row in range(self.intel_map.mars_map_width)];
		self.q = [];
		self.resource_q = [];

	def precomp(self):
		if (self.gc.planet() == bc.Planet.Earth):
			self.q.clear();
			e_cnt = 0;
			for i in range(self.intel_map.earth_map_width):
				for j in range(self.intel_map.earth_map_height):
					if (self.intel_map.earth_map[i][j] == -1):
						self.unit_bfs[i][j] = -1; #cannot move here
					elif (self.intel_map.earth_unit_map[i][j] >= 1500000000):
						self.unit_bfs[i][j] = -1; #rocket
						if self.gc.can_sense_unit(self.intel_map.earth_unit_map[i][j] - 1500000000):
							unit = self.gc.unit(self.intel_map.earth_unit_map[i][j] - 1500000000);
							if (unit.structure_is_built() and len(unit.structure_garrison()) != unit.structure_max_capacity()):
								self.q.append((i, j));
					elif (self.intel_map.earth_unit_map[i][j] >= 1000000000):
						self.unit_bfs[i][j] = -1; #factory or worker => obstruction
					elif (self.intel_map.earth_unit_map[i][j] < 0):
						e_cnt += 1;
						self.unit_bfs[i][j] = 1000000000;
						if (self.gc.round() < Astronomer.rocket_panic_round):
							self.q.append((i, j));
					else:
						self.unit_bfs[i][j] = 1000000000;
					self.unit_prev_move[i][j] = None;
			#Mark enemy starting locations as enemy
			if (e_cnt == 0 and self.gc.round() < Astronomer.rocket_panic_round):
				for start_pt in self.intel_map.earth_enemy_starting_points:
					self.q.append((start_pt.x, start_pt.y));
					self.unit_bfs[start_pt.x][start_pt.y] = 0;
			self.do_actual_precomp();
		else:
			self.q.clear();
			for i in range(self.intel_map.mars_map_width):
				for j in range(self.intel_map.mars_map_height):
					if (self.intel_map.mars_map[i][j] == -1):
						self.unit_bfs[i][j] = -1; #cannot move here
					elif (self.intel_map.mars_unit_map[i][j] >= 1500000000):
						self.unit_bfs[i][j] = -1; #rocket
					elif (self.intel_map.mars_unit_map[i][j] >= 1000000000):
						self.unit_bfs[i][j] = -1; #factory or worker => obstruction
					elif (self.intel_map.mars_unit_map[i][j] < 0):
						self.unit_bfs[i][j] = 1000000000;
						self.q.append((i , j))
					else:
						self.unit_bfs[i][j] = 1000000000;
					self.unit_prev_move[i][j] = None;
			self.do_actual_precomp();

	def expensive_move_to(self, unit, target):
		#print("Target: " + str(target));
		if (unit.movement_heat() >= 10 or unit.location.is_in_garrison() or unit.location.is_in_space()):
			return;
		start_time = time.time();
		queue = [];
		if (self.gc.planet() == bc.Planet.Earth):
			search = [[0 for col in range(self.intel_map.earth_map_height)] for row in range(self.intel_map.earth_map_width)];
			last_move = [[None for col in range(self.intel_map.earth_map_height)] for row in range(self.intel_map.earth_map_width)];
			for i in range(self.intel_map.earth_map_width):
				for j in range(self.intel_map.earth_map_height):
					if (self.intel_map.earth_map[i][j] == -1):
						search[i][j] = -1;
					elif (self.intel_map.earth_unit_map[i][j] >= 1000000000):
						search[i][j] = -1;
					else:
						search[i][j] = 1000000000;
					last_move[i][j] = None;
			search[target.x][target.y] = 0;
			queue.append((target.x, target.y))
			unit_loc = unit.location.map_location();
			while (len(queue) > 0):
				loc = queue.pop(0);
				for i in range(len(Mover.dirx)):
					nx = loc[0] + Mover.dirx[i];
					ny = loc[1] + Mover.diry[i];
					if (nx < 0 or nx >= self.intel_map.earth_map_width or ny < 0 or ny >= self.intel_map.earth_map_height
						or search[nx][ny] != 1000000000):
						continue;
					search[nx][ny] = search[loc[0]][loc[1]] + 1;
					last_move[nx][ny] = Mover.directions[i];
					if (nx == unit_loc.x and ny == unit_loc.y):
						ans = Helper.get_inverse(last_move[nx][ny]);
						print(ans);
						if (not(ans is None)):
							if (self.gc.can_move(unit.id, ans)):
								self.gc.move_robot(unit.id, ans);
								break;
					queue.append((nx, ny));
			del search;
			del last_move;
			del queue;
			#print("computation took " + str((time.time() - start_time) * 1000) + " ms" ) 
		else:
			print("Mover: Can't do expensive move to on Mars !!");
			return;

	def do_actual_precomp(self):
		start_time = time.time();
		if (self.gc.planet() == bc.Planet.Earth):
			op_num = 0;
			while (not(len(self.q) == 0)):
				loc = self.q.pop(0);
				op_num += 1;
				if (op_num % 400 == 0):
					if (time.time() - start_time >= Mover.max_precomp_time):
						break;
					#else:
					#	print(str(op_num) + " precomp operations took " + str((time.time() - start_time) * 1000) + " ms" ) 
				for i in range(len(Mover.dirx)):
					nx = loc[0] + Mover.dirx[i];
					ny = loc[1] + Mover.diry[i];
					if (nx < 0 or nx >= self.intel_map.earth_map_width or ny < 0 or 
						ny >= self.intel_map.earth_map_height or self.unit_bfs[nx][ny] != 1000000000):
						continue;
					self.unit_bfs[nx][ny] = self.unit_bfs[loc[0]][loc[1]] + 1; #No need to track actual distance
					self.unit_prev_move[nx][ny] = Mover.directions[i];
					self.q.append((nx, ny));
		else:
			op_num = 0;
			while (not(len(self.q) == 0)):
				loc = self.q.pop(0);
				op_num += 1;
				if (op_num % 400 == 0):
					if (time.time() - start_time >= Mover.max_precomp_time):
						break;
					#else:
					#	print(str(op_num) + " precomp operations took " + str((time.time() - start_time) * 1000) + " ms" ) 
				for i in range(len(Mover.dirx)):
					nx = loc[0] + Mover.dirx[i];
					ny = loc[1] + Mover.diry[i];
					if (nx < 0 or nx >= self.intel_map.mars_map_width or ny < 0 or 
						ny >= self.intel_map.mars_map_height or self.unit_bfs[nx][ny] != 1000000000):
						continue;
					self.unit_bfs[nx][ny] = self.unit_bfs[loc[0]][loc[1]] + 1; #No need to track actual distance
					self.unit_prev_move[nx][ny] = Mover.directions[i];
					self.q.append((nx, ny));

	def is_precomp_complete(self): # => boolean
		if (len(self.q) == 0):
			return True;
		else:
			return False;

	def precomp_resources(self): # => void
		start_time = time.time();
		if (self.gc.planet() == bc.Planet.Earth):
			self.resource_q.clear();
			for i in range(self.intel_map.earth_map_width):
				for j in range(self.intel_map.earth_map_height):
					if (self.intel_map.earth_map[i][j] == -1):
						self.bfs[i][j] = -1;
					elif (self.intel_map.earth_unit_map[i][j] >= 1500000000):
						self.bfs[i][j] = -1; #factory or rocket => obstruction
						if self.gc.can_sense_unit(self.intel_map.earth_unit_map[i][j] - 1500000000):
							unit = self.gc.unit(self.intel_map.earth_unit_map[i][j] - 1500000000);
							if (not(unit.structure_is_built())):
								self.resource_q.append((i, j));
					elif (self.intel_map.earth_unit_map[i][j] >= 1250000000):
						self.bfs[i][j] = 1000000; # treat workers as obstructions
					elif (self.intel_map.earth_unit_map[i][j] >= 1000000000):
						self.bfs[i][j] = -1;
						if self.gc.can_sense_unit(self.intel_map.earth_unit_map[i][j] - 1000000000):
							unit = self.gc.unit(self.intel_map.earth_unit_map[i][j] - 1000000000);
							if (not(unit.structure_is_built())):
								self.resource_q.append((i, j));
					elif (self.intel_map.earth_map[i][j] > 0): #karbonite
						self.bfs[i][j] = 1000000000;
						self.resource_q.append((i, j));
					else:
						self.bfs[i][j] = 1000000000;
					self.prev_move[i][j] = None;
			self.do_actual_precomp_resources();
		else:
			self.resource_q.clear();
			for i in range(self.intel_map.mars_map_width):
				for j in range(self.intel_map.mars_map_height):
					if (self.intel_map.mars_map[i][j] == -1):
						self.bfs[i][j] = -1;
					elif (self.intel_map.mars_unit_map[i][j] >= 1500000000):
						self.bfs[i][j] = -1; #factory or rocket => obstruction
					elif (self.intel_map.mars_unit_map[i][j] >= 1250000000):
						self.bfs[i][j] = 1000000000;
					elif (self.intel_map.mars_unit_map[i][j] >= 1000000000):
						self.bfs[i][j] = -1;
					elif (self.intel_map.mars_map[i][j] > 0): #karbonite
						self.bfs[i][j] = 1000000000;
						self.resource_q.append((i, j));
					else:
						self.bfs[i][j] = 1000000000;
					self.prev_move[i][j] = None;
			self.do_actual_precomp_resources();

	def do_actual_precomp_resources(self): # => void
		start_time = time.time();
		if (self.gc.planet() == bc.Planet.Earth):
			op_num = 0;
			while (not(len(self.resource_q) == 0)):
				loc = self.resource_q.pop(0);
				op_num += 1;
				if (op_num % 400 == 0):
					if (time.time() - start_time >= Mover.max_precomp_time):
						break;
					#else:
						#print(str(op_num) + " resource operations took " + str((time.time() - start_time) * 1000) + " ms" )
				for i in range(len(Mover.dirx)):
					nx = loc[0] + Mover.dirx[i];
					ny = loc[1] + Mover.diry[i];
					if (nx < 0 or nx >= self.intel_map.earth_map_width or ny < 0
						or ny >= self.intel_map.earth_map_height or (self.bfs[nx][ny] != 1000000000
						and self.bfs[nx][ny] != 1000000)):
						continue;
					if (self.bfs[nx][ny] != 1000000): #treat workers as impassable
						self.resource_q.append((nx, ny));
					self.bfs[nx][ny] = 1;
					self.prev_move[nx][ny] = Mover.directions[i];
		else:
			op_num = 0;
			while (not(len(self.resource_q) == 0)):
				loc = self.resource_q.pop(0);
				op_num += 1;
				if (op_num % 400 == 0):
					if (time.time() - start_time >= Mover.max_precomp_time):
						break;
					#else:
						#print(str(op_num) + " resource operations took " + str((time.time() - start_time) * 1000) + " ms" )
				for i in range(len(Mover.dirx)):
					nx = loc[0] + Mover.dirx[i];
					ny = loc[1] + Mover.diry[i];
					if (nx < 0 or nx >= self.intel_map.mars_map_width or ny < 0
						or ny >= self.intel_map.mars_map_height or self.bfs[nx][ny] != 1000000000):
						continue;
					self.bfs[nx][ny] = 1;
					self.prev_move[nx][ny] = Mover.directions[i];
					self.resource_q.append((nx, ny));

	def is_precomp_resources_complete(self): # => bool
		if (len(self.resource_q) == 0):
			return True;
		else:
			return False;

	def move_to_nearest_enemy(self, unit, s): #Unit, Soldier => void
		if (unit.movement_heat() >= 10 or unit.location.is_in_garrison() or unit.location.is_in_space()):
			return;
		unit_loc = unit.location.map_location();
		direc = Helper.get_inverse(self.unit_prev_move[unit_loc.x][unit_loc.y]);
		if (not(direc is None)):
			if (self.gc.can_move(unit.id, direc)):
				self.gc.move_robot(unit.id, direc);
				self.intel_map.move_unit(unit, direc);
				return;
		else:
			#No way to get to enemy => become scout
			0
			#print("Couldn't get to enemy, becoming scout !!")
			#s.set_role(Role.Scout);

	def can_move_to_nearest_enemy(self, unit): # Unit => bool
		unit_loc = unit.location.map_location();
		if (self.unit_prev_move[unit_loc.x][unit_loc.y] is None):
			return False;
		else:
			return True;

	def move_dir_to_karbonite(self, worker): # Unit => bool
		unit_loc = worker.location.map_location();
		return Helper.get_inverse(self.prev_move[unit_loc.x][unit_loc.y]);

	def cheap_move_to(self, unit, target): #Unit, MapLocation => void
		if (unit.movement_heat() >= 10 or unit.location.is_in_garrison() or unit.location.is_in_space()):
			return;
		lowest_squared_dist = 1000000;
		move_dir = bc.Direction.Center;
		curr_loc = unit.location.map_location();
		for direc in Mover.directions:
			if (self.gc.can_move(unit.id, direc)):
				new_loc = curr_loc.add(direc);
				squared_dist = new_loc.distance_squared_to(target);
				if (lowest_squared_dist > squared_dist):
					lowest_squared_dist = squared_dist;
					move_dir = direc;
		if (move_dir != bc.Direction.Center):
			self.intel_map.move_unit(unit, move_dir);
			self.gc.move_robot(unit.id, move_dir);

	def non_blocking_move_to(self, unit, target, prev_locs): #Unit, MapLocation, MapLocation[] => None
		#Can't move if there's no possible movement
		if (unit.movement_heat() >= 10 or unit.location.is_in_garrison() or unit.location.is_in_space()):
			return;
		lowest_squared_dist = 1000000000;
		move_dir = None;
		curr_loc = unit.location.map_location();
		for direc in Mover.directions:
			if (self.gc.can_move(unit.id, direc)):
				new_loc = curr_loc.add(direc);
				has_been_visited = False;
				for prev_loc in prev_locs:
					if (prev_loc.x == new_loc.x and prev_loc.y == new_loc.y):
						has_been_visited = True;
						break;
				if (has_been_visited):
					continue;
				squared_dist = new_loc.distance_squared_to(target);
				if (lowest_squared_dist > squared_dist):
					lowest_squared_dist = squared_dist;
					move_dir = direc;
		if (not(move_dir is None)):
			if (len(prev_locs) >= Mover.past_locations_remembered):
				prev_locs.pop();
			prev_locs.append(curr_loc.add(move_dir));
			self.intel_map.move_unit(unit, move_dir);
			self.gc.move_robot(unit.id, move_dir);

	def scout_move(self, unit): #Unit => MapLocation
		try_cnt = 0;
		while (try_cnt < Mover.max_random_tries):
			scout_loc = None;
			if (self.gc.planet() == bc.Planet.Earth):
				scout_loc = DiceRoller.get_random_map_location(bc.Planet.Earth, self.intel_map.earth_map_width, self.intel_map.earth_map_height);
			else:
				scout_loc = DiceRoller.get_random_map_location(bc.Planet.Mars, self.intel_map.mars_map_width, self.intel_map.mars_map_height);
			if (not(self.gc.can_sense_location(scout_loc))):
				return scout_loc;
			try_cnt += 1;
		return None;

	#Todo: Use bfs to compute karbonite and update this
	def move_to_nearest_karbonite(self, unit): #Unit => void
		if (unit.movement_heat() >= 10 or unit.location.is_in_garrison() or unit.location.is_in_space()):
			return;
		unit_loc = unit.location.map_location();
		direc = Helper.get_inverse(self.prev_move[unit_loc.x][unit_loc.y]);
		if (not(direc is None)):
			if (self.gc.can_move(unit.id, direc)):
				self.gc.move_robot(unit.id, direc);
				self.intel_map.move_unit(unit, direc);
				return;
		else:
			#No way to get to resources => return to base or sth
			0

	def move_away_from_nearest_karbonite(self, unit): #Unit => void
		if (unit.movement_heat() >= 10 or unit.location.is_in_garrison() or unit.location.is_in_space()):
			return;
		unit_loc = unit.location.map_location();
		direc = self.prev_move[unit_loc.x][unit_loc.y];
		if (not(direc is None)):
			if (self.gc.can_move(unit.id, direc)):
				self.gc.move_robot(unit.id, direc);
				self.intel_map.move_unit(unit, direc);
				return;
		else:
			#No way to get to resources => return to base or sth
			0


