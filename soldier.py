
import battlecode as bc
from role import Role
from helper import Helper

class Soldier:

	target_accept_dist = 16; #Distance squared
	enemy_sense_dist = 100; #Range at which to detect enemies
	move_target_reset_round = 50; #Rounds after which move target will reset
	healer_sense_range = 50; #Range at which healers are sensed
	percentage_critical_health = 40; #Percentage of health considered critical
	percentage_recovered_health = 80; #Percentage of health which will run unit out of critical
	directions = [bc.Direction.East, bc.Direction.North, bc.Direction.Northeast,
	bc.Direction.Northwest, bc.Direction.South, bc.Direction.Southeast,
	bc.Direction.Southwest, bc.Direction.West];

	def __init__(self, gc, intel_map, mov, astro, role, unit): #GameController, IntelMap, Mover, Astronomer, Role, Unit
		self.gc = gc;
		self.intel_map = intel_map;
		self.mov = mov;
		self.astro = astro;
		self.role = role;
		self.unit = unit;
		critical_health = self.unit.max_health * Soldier.percentage_critical_health // 100;
		recovered_health = self.unit.max_health * Soldier.percentage_recovered_health // 100;

		self.move_target = None; #MapLocation
		self.prev_move_target = None; #MapLocation
		self.rally_point = None; #MapLocation
		self.prev_locs = []; #MapLocation[]
		self.move_target_round_set = 0;
		self.is_in_critical_mode = False;

	def take_turn(self, unit, alert): #Unit, boolean => void Need to run this to update the unit every turn
		self.unit = unit;
		#print("Soldier: Unit ID " + str(self.unit.id) + " has heat " + str(self.unit.movement_heat()))
		self.intel_map.update_karbonite_info(self.unit);

	def set_role(self, new_role): #Role => void
		self.role = new_role;

	def get_role(self):
		return self.role;

	def set_move_target(self, tgt): #MapLocation => void
		self.move_target = tgt;
		self.move_target_round_set = self.gc.round();

	def set_rally_point(self, new_pt): #MapLocation => void
		self.rally_point = new_pt;

	def is_within_target(self, curr_loc): #MapLocation => boolean
		if (self.move_target is None):
			return False;
		else:
			return curr_loc.distance_squared_to(self.move_target) <= Soldier.target_accept_dist;

	def should_use_micro(self): # => boolean
		if (self.unit.location.is_in_garrison() or self.unit.location.is_in_space()):
			return False;
		#Sense nearby enemy units
		nearby_enemies = self.gc.sense_nearby_units_by_team(self.unit.location.map_location(), Soldier.enemy_sense_dist, Helper.get_opposing_team(self.gc.team()));
		for enemy in nearby_enemies:
			del enemy;
		if (len(nearby_enemies) > 0):
			return True;
		return False;

	def make_move(self): # => void
		if (self.unit.location.is_in_garrison() or self.unit.location.is_in_space() or self.unit.movement_heat() >= 10):
			return;

		if (not(self.prev_move_target is None) and not(self.move_target is None) and (self.prev_move_target.x != self.move_target.x or self.prev_move_target.y != self.move_target.y)):
			self.prev_locs.clear();
		#nearest_rocket = self.astro.nearest_rocket_requesting_unit(self.unit);
		#rocket_move_loc = None;
		#if (not(nearest_rocket is None)):
		#	rocket_move_loc = nearest_rocket.location.map_location();
		#if (not(rocket_move_loc is None)):
		#	self.mov.non_blocking_move_to(self.unit, rocket_move_loc, self.prev_locs);
		if (not(self.move_target is None) and not(self.mov.can_move_to_nearest_enemy(self.unit))):
			self.mov.non_blocking_move_to(self.unit, self.move_target, self.prev_locs);
			#if (self.gc.planet() == bc.Planet.Mars):
			#			print("scout move")
		else:
			if (self.role == Role.Scout):
				if (self.mov.can_move_to_nearest_enemy(self.unit)):
					self.mov.move_to_nearest_enemy(self.unit, self);
				else:
					scout_loc = self.mov.scout_move(self.unit);
					if (not(scout_loc is None)):
						self.move_target = scout_loc;
						self.mov.non_blocking_move_to(self.unit, self.move_target, self.prev_locs);
					else:
						self.mov.move_to_nearest_enemy(self.unit, self);
			elif (self.role == Role.Attack):
				if (not(self.mov.can_move_to_nearest_enemy(self.unit))):
					self.role = Role.Scout
				else:
					self.mov.move_to_nearest_enemy(self.unit, self);
				#print("Moving towards nearest enemy");
		if (self.gc.can_sense_unit(self.unit.id)):
			self.unit = self.gc.unit(self.unit.id);
		if (self.is_within_target(self.move_target)):
			self.move_target = None;
			self.prev_locs.clear();
		self.prev_move_target = self.move_target;

	def escape_move(self): # => void
		self.mov.move_to_nearest_enemy(self.unit, self);
		#if (self.unit.location.is_in_garrison() or self.unit.location.is_in_space() or self.unit.movement_heat() >= 10):
		#	return;

		#nearest_rocket = self.astro.nearest_rocket_requesting_unit(self.unit);
		#rocket_move_loc = None;
		#if (not(nearest_rocket is None)):
		#	rocket_move_loc = nearest_rocket.location.map_location();
		#if (not(rocket_move_loc is None)):
		#	self.prev_locs.clear();
		#	self.mov.non_blocking_move_to(self.unit, rocket_move_loc, self.prev_locs);

	def should_use_evade_move(self): # => boolean
		nearby_healers = self.gc.sense_nearby_units_by_type(self.unit.location.map_location(), Soldier.healer_sense_range, bc.UnitType.Healer);
		
		has_allied_healer = False;
		for healer in nearby_healers:
			if (healer.team == self.gc.team()):
				has_allied_healer = True;
				break;
		for healer in nearby_healers:
			del healer;
		if (not(self.is_in_critical_mode)):
			if (self.unit.health <= critical_health and has_allied_healer):
				self.is_in_critical_mode = True;
				return True;
			return False;
		else:
			if (self.has_allied_healer and self.unit.health <= recovered_health):
				return True;
			self.is_in_critical_mode = False;
			return False;

	def evade_move(self): # => void
		nearby_healers = self.gc.sense_nearby_units_by_type(self.unit.location.map_location(), Soldier.healer_sense_range, bc.UnitType.Healer);
		nearest_healer = None;
		least_dist_squared = 1000000000;
		for healer in nearby_healers:
			if (healer.team == self.gc.team()):
				dist_squared = healer.location.map_location().distance_squared_to(self.unit.location.map_location());
				if (dist_squared < least_dist_squared):
					least_dist_squared = dist_squared;
					nearest_healer = healer;
		for healer in nearby_healers:
			del healer;
		self.mov.non_blocking_move_to(self.unit, nearest_healer.location.map_location(), self.prev_locs);