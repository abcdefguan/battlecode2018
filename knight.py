
import battlecode as bc
from soldier import Soldier
from helper import Helper
from astronomer import Astronomer

class Knight(Soldier):
	knight_sense_dist = 100;

	def __init__(self, gc, intel_map, mov, astro, role, unit): #GameController, IntelMap, Mover, Astronomer, Role, Unit
		super().__init__(gc, intel_map, mov, astro, role, unit);

	def micro_move(self): # => void
		if (self.unit.movement_heat() >= 10 or self.unit.location.is_in_garrison() or self.unit.location.is_in_space()):
			return;
		nearby_enemies = self.gc.sense_nearby_units_by_team(self.unit.location.map_location(), Knight.knight_sense_dist, Helper.get_opposing_team(self.gc.team()));
		best_score = 0;
		best_loc = None;
		for enemy in nearby_enemies:
			score = self.get_attack_score(enemy);
			if (score > best_score):
				best_score = score;
				best_loc = enemy.location.map_location();
		if (not(best_loc is None)):
			self.mov.expensive_move_to(self.unit, best_loc);
		else:
			self.make_move();
			return;

	def get_move_score(self, new_loc, nearby_enemies): #MapLocation, VecUnit => double
		# Objectives:
		# Dummy function

		score = 100000;
		least_dist_squared = 1000000000;
		for enemy in nearby_enemies:
			dist_squared_to_enemy = enemy.location.map_location().distance_squared_to(new_loc);
			if (dist_squared_to_enemy < least_dist_squared):
				least_dist_squared = dist_squared_to_enemy;
		score -= least_dist_squared * 1000;
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
		score = 0;
		dist_squared = enemy.location.map_location().distance_squared_to(self.unit.location.map_location());
		if (enemy.unit_type == bc.UnitType.Mage):
			score += 1000000;
		elif (enemy.unit_type == bc.UnitType.Healer):
			score += 800000;
		elif (enemy.unit_type == bc.UnitType.Factory):
			score += 1200000;
		elif (enemy.unit_type == bc.UnitType.Ranger):
			score += 400000;
		elif (enemy.unit_type == bc.UnitType.Knight):
			score += 900000;
		else:
			if (self.gc.round() < 150):
				score -= 1000000;
			else:
				score += 10000;
		score += 100000;
		score -= dist_squared * 100;
		score -= enemy.health * 100;
		return score;

	def attack(self): # => void
		#Can't do anything if garrisoned or in space
		if (self.unit.location.is_in_garrison() or self.unit.location.is_in_space()):
			return;
		if (self.unit.attack_heat() >= 10):
			return;
		enemies_within_range = self.gc.sense_nearby_units_by_team(self.unit.location.map_location(), self.unit.attack_range(), Helper.get_opposing_team(self.gc.team()));
		best_score = -100000000;
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
				print("Knight: Unexpectedly cannot attack enemy");
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
