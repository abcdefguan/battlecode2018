
import battlecode as bc
from soldier import Soldier
from helper import Helper
from astronomer import Astronomer

class Ranger(Soldier):
	ranger_sense_dist = 60;
	ranger_avoid_buffer = 10; #Buffer distance to avoid enemies
	ranger_mage_avoid_buffer = 5; #Buffer distance to avoid magi
	ranger_healer_buffer = 5; #Buffer distance for following healers
	ranger_knight_avoid_buffer = 3; #Buffer distance to avoid knights
	max_damage_allowed = 70; #Maximum amt of damage that this unit would like to take in 1 turn

	def __init__(self, gc, intel_map, mov, astro, role, unit): #GameController, IntelMap, Mover, Astronomer, Role, Unit
		super().__init__(gc, intel_map, mov, astro, role, unit);

	def micro_move(self): # => void
		if (self.unit.movement_heat() >= 10 or self.unit.location.is_in_garrison() or self.unit.location.is_in_space()):
			return;
		nearby_enemies = self.gc.sense_nearby_units_by_team(self.unit.location.map_location(), Ranger.ranger_sense_dist, Helper.get_opposing_team(self.gc.team()));
		nearby_allies = self.gc.sense_nearby_units_by_team(self.unit.location.map_location(), Ranger.ranger_sense_dist, self.gc.team());
		best_score = -1000000000;
		best_move = None;
		if (len(nearby_enemies) > 0):
			for direc in Soldier.directions:
				if (self.gc.can_move(self.unit.id, direc)):
					new_loc = self.unit.location.map_location().add(direc);
					score = self.get_move_score(new_loc, nearby_enemies, nearby_allies);
					if (score > best_score):
						best_score = score;
						best_move = direc;
			score = self.get_move_score(self.unit.location.map_location(), nearby_enemies, nearby_allies);
			if (score > best_score):
				best_score = score;
				best_move = None;
			if (not(best_move is None)):
				if (self.gc.can_move(self.unit.id, best_move)):
					self.gc.move_robot(self.unit.id, best_move);
				else:
					print("Ranger: Can't actually take micro move !!");
		else:
			self.make_move();
			return;

	def get_move_score(self, new_loc, nearby_enemies, nearby_allies): #MapLocation, VecUnit => double
		# Objectives:
		# Big penalty for any unit that's too close (within squared dist 10)
		# Small reward for being within enemy units
		# Bigger reward for being next to healers
		# Tiny reward for being next to other allied units

		score = 0;
		damage_taken = 0;
		for enemy in nearby_enemies:
			dist_squared_to_enemy = enemy.location.map_location().distance_squared_to(new_loc);
			if (dist_squared_to_enemy <= (self.unit.ranger_cannot_attack_range() + Ranger.ranger_avoid_buffer)):
				score -= 1000000;
				score += 10000 * dist_squared_to_enemy;
			elif (dist_squared_to_enemy <= self.unit.attack_range()):
				score += 100 * dist_squared_to_enemy;
			if (enemy.unit_type == bc.UnitType.Ranger):
				if (dist_squared_to_enemy <= (enemy.attack_range())):
					damage_taken += enemy.damage();
			if (enemy.unit_type == bc.UnitType.Mage):
				if (dist_squared_to_enemy <= (enemy.attack_range() + Ranger.ranger_mage_avoid_buffer)):
					score -= 1000000;
					score += 10000 * dist_squared_to_enemy;
					damage_taken += enemy.damage();
			elif (enemy.unit_type == bc.UnitType.Knight):
				if (dist_squared_to_enemy <= enemy.attack_range() + Ranger.ranger_knight_avoid_buffer):
					score -= 1000000;
					score += 100000 * dist_squared_to_enemy;
					damage_taken += enemy.damage();
		for ally in nearby_allies:
			dist_squared_to_ally = ally.location.map_location().distance_squared_to(new_loc);
			if (ally.unit_type == bc.UnitType.Healer):
				if (dist_squared_to_ally - Ranger.ranger_healer_buffer < ally.attack_range()):
					score += 10000;
					score -= 100 * dist_squared_to_ally; #get closer to healer
			else:
				score += 1000;
				score -= 10 * dist_squared_to_ally;
		if (damage_taken > self.unit.health):
			score -= 100000000;
		elif (damage_taken > Ranger.max_damage_allowed):
			score -= 1000000;
		else:
			score -= 100 * damage_taken;
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
		if (dist_squared <= self.unit.ranger_cannot_attack_range()):
			return -1000000;
		if (enemy.unit_type == bc.UnitType.Mage):
			score += 1000000;
		elif (enemy.unit_type == bc.UnitType.Healer):
			score += 800000;
		elif (enemy.unit_type == bc.UnitType.Factory):
			score += 1200000;
		elif (enemy.unit_type == bc.UnitType.Ranger):
			score += 400000;
		elif (enemy.unit_type == bc.UnitType.Knight):
			if (dist_squared <= enemy.attack_range()):
				score += 1200000;
			else:
				score += 200000;
		else:
			score += 0;
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
				#print("Enemy distance is: " + str(self.unit.location.map_location().distance_squared_to(best_enemy.location.map_location())));
				print("Ranger: Unexpectedly cannot attack enemy");
		else:
			0
			#print("Healer: Can't find units to heal");

	def move_and_attack(self): # => void
		#Can't do anything if garrisoned or in space
		if (self.unit.location.is_in_garrison() or self.unit.location.is_in_space()):
			return;
		if (self.should_use_micro()):
			if (self.gc.round() >= Astronomer.rocket_panic_round and self.gc.planet() == bc.Planet.Earth):
				self.escape_move();
			else:
				#if (self.gc.planet() == bc.Planet.Mars):
				#	print("Micro move")
				self.micro_move();
		else:
			if (self.gc.round() >= Astronomer.rocket_panic_round and self.gc.planet() == bc.Planet.Earth):
				self.escape_move();
			else:
				self.make_move();
		if (self.gc.can_sense_unit(self.unit.id)):
			self.unit = self.gc.unit(self.unit.id);
		self.attack();
