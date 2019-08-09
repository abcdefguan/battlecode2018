
import battlecode as bc
from soldier import Soldier
from helper import Helper
from astronomer import Astronomer

class Mage(Soldier):
	mage_sense_dist = 100;
	mage_avoid_buffer = 10;
	mage_knight_avoid_buffer = 5;

	def __init__(self, gc, intel_map, mov, astro, role, unit): #GameController, IntelMap, Mover, Astronomer, Role, Unit
		super().__init__(gc, intel_map, mov, astro, role, unit);

	def micro_move(self): # => void
		if (self.unit.movement_heat() >= 10 or self.unit.location.is_in_garrison() or self.unit.location.is_in_space()):
			return;
		nearby_enemies = self.gc.sense_nearby_units_by_team(self.unit.location.map_location(), Mage.mage_sense_dist, Helper.get_opposing_team(self.gc.team()));
		best_score = -1000000000;
		best_move = None;
		if (len(nearby_enemies) > 0):
			for direc in Soldier.directions:
				if (self.gc.can_move(self.unit.id, direc)):
					new_loc = self.unit.location.map_location().add(direc);
					score = self.get_move_score(new_loc, nearby_enemies);
					if (score > best_score):
						best_score = score;
						best_move = direc;
			if (not(best_move is None)):
				if (self.gc.can_move(self.unit.id, best_move)):
					self.gc.move_robot(self.unit.id, best_move);
				else:
					print("Mage: Can't actually take micro move !!");
		else:
			self.make_move();
			return;

	def get_move_score(self, new_loc, nearby_enemies): #MapLocation, VecUnit => double
		# Objectives:
		# Keep as far as possible away from any knight, but within attack range
		# Keep as close as possible to any rangers, huge reward when within cannot attack range

		score = 100000;
		has_non_ranger = False;
		for enemy in nearby_enemies:
			dist_squared_to_enemy = enemy.location.map_location().distance_squared_to(new_loc);
			if (enemy.unit_type == bc.UnitType.Worker or enemy.unit_type == bc.UnitType.Factory or enemy.unit_type == bc.UnitType.Rocket):
				score += 1000000;
				score -= 1000 * dist_squared_to_enemy;
				continue;
			if (enemy.unit_type == bc.UnitType.Knight):
				if (dist_squared_to_enemy <= enemy.attack_range() + Mage.mage_knight_avoid_buffer):
					print("Knight close to me");
					score -= 10000000;
					score += dist_squared_to_enemy * 100000;
			elif (dist_squared_to_enemy <= enemy.attack_range() + Mage.mage_avoid_buffer):
				score += 10000;
				score -= 100 * dist_squared_to_enemy;
			else:
				if (dist_squared_to_enemy <= self.unit.attack_range()):
					score += 100;
		return score;

	def get_attack_score(self, enemy): #Unit => double
		#	Objectives:
		#	Attack mages first
		#	Then attack healers
		#	Then attack factories
		#	Then attack rangers
		#	Then attack knights
		#	Then attack workers, rockets
		#	Attack enemies that are closer first => Top order most impt
		#Get nearby attacked units
		nearby_units = self.gc.sense_nearby_units(enemy.location.map_location(), 3);
		score = 0;
		for attacked_unit in nearby_units:
			allegiance_multiplier = 1.0
			if (attacked_unit.team == self.gc.team()):
				allegiance_multiplier = -1.0;
			dist_squared = attacked_unit.location.map_location().distance_squared_to(self.unit.location.map_location());
			if (attacked_unit.unit_type == bc.UnitType.Mage):
				score += allegiance_multiplier * 1000000;
			elif (attacked_unit.unit_type == bc.UnitType.Ranger):
				score += allegiance_multiplier * 800000;
			elif (attacked_unit.unit_type == bc.UnitType.Healer):
				score += allegiance_multiplier * 600000;
			elif (attacked_unit.unit_type == bc.UnitType.Knight):
				score += allegiance_multiplier * 400000;
			elif (attacked_unit.unit_type == bc.UnitType.Factory):
				score += allegiance_multiplier * 1200000;
			else:
				score += allegiance_multiplier * 200000;
			if (attacked_unit.team == self.gc.team()):
				score += attacked_unit.health * 100;
			else:
				score -= dist_squared * 100;
				score -= attacked_unit.health * 100;
		return score;

	def attack(self): # => void
		#Can't do anything if garrisoned or in space
		if (self.unit.location.is_in_garrison() or self.unit.location.is_in_space()):
			return;
		if (self.unit.attack_heat() >= 10):
			return;
		enemies_within_range = self.gc.sense_nearby_units_by_team(self.unit.location.map_location(), self.unit.attack_range(), Helper.get_opposing_team(self.gc.team()));
		best_score = 0;
		best_enemy = None;
		for enemy in enemies_within_range:
			if (self.gc.can_attack(self.unit.id, enemy.id)):
				score = self.get_attack_score(enemy);
				if (score > best_score):
					best_score = score;
					best_enemy = enemy;
		if (not(best_enemy is None)):
			if (self.gc.can_attack(self.unit.id, best_enemy.id)):
				self.gc.attack(self.unit.id, best_enemy.id);
			else:
				print("Mage: Unexpectedly cannot attack enemy");
		else:
			0
			#print("Healer: Can't find units to heal");

	def move_and_attack(self): # => void
		#Can't do anything if garrisoned or in space
		if (self.unit.location.is_in_garrison() or self.unit.location.is_in_space()):
			return;
		if (self.should_use_micro()):
			if (self.gc.round() >= Astronomer.rocket_panic_round):
				self.escape_move();
			else:
				self.micro_move();
		else:
			if (self.gc.round() >= Astronomer.rocket_panic_round):
				self.escape_move();
			else:
				self.make_move();
		if (self.gc.can_sense_unit(self.unit.id)):
			self.unit = self.gc.unit(self.unit.id);
		self.attack();
