
import battlecode as bc
from soldier import Soldier
from helper import Helper
from astronomer import Astronomer

class Healer(Soldier):
	healer_sense_dist = 60;
	healer_avoid_dist = 30; #Buffer distance to avoid enemies
	healer_knight_avoid_dist = 4; #Buffer distance to avoid enemies

	def __init__(self, gc, intel_map, mov, astro, role, unit, com): #GameController, IntelMap, Mover, Astronomer, Role, Unit, Commander
		super().__init__(gc, intel_map, mov, astro, role, unit);
		self.com = com;

	def micro_move(self): # => void
		if (self.unit.movement_heat() >= 10 or self.unit.location.is_in_garrison() or self.unit.location.is_in_space()):
			return;
		nearby_enemies = self.gc.sense_nearby_units_by_team(self.unit.location.map_location(), Healer.healer_sense_dist, Helper.get_opposing_team(self.gc.team()));
		nearby_allies = self.gc.sense_nearby_units_by_team(self.unit.location.map_location(), Healer.healer_sense_dist, self.gc.team());
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
					print("Healer: Can't actually take micro move !!");
		else:
			for enemy in nearby_enemies:
				del enemy;
			for ally in nearby_allies:
				del ally;
			self.make_move();
			return;
		for enemy in nearby_enemies:
			del enemy;
		for ally in nearby_allies:
			del ally;

	def get_move_score(self, new_loc, nearby_enemies, nearby_allies): #MapLocation, VecUnit, VecUnit => double
		# Objectives:
		# Keep out of enemy attack range for knight, range, mage (More impt)
		# Run away from enemies if within their attack range
		# Go closer to allied units that are low on health (less impt)

		score = 0;
		for enemy in nearby_enemies:
			dist_squared_to_enemy = enemy.location.map_location().distance_squared_to(new_loc);
			if (enemy.unit_type == bc.UnitType.Ranger or enemy.unit_type == bc.UnitType.Mage):
				if (dist_squared_to_enemy <= enemy.attack_range() + Healer.healer_avoid_dist ):
					score -= 1000000;
					score += dist_squared_to_enemy * 10000;
			elif (enemy.unit_type == bc.UnitType.Knight):
				if (dist_squared_to_enemy <= enemy.attack_range() + Healer.healer_knight_avoid_dist):
					score -= 1000000;
					score += dist_squared_to_enemy * 100000;
		for ally in nearby_allies:
			dist_squared_to_ally = ally.location.map_location().distance_squared_to(new_loc);
			if (dist_squared_to_ally <= self.unit.attack_range()):
				score += 1000;
				#score -= dist_squared_to_ally * 10; # Get closer to allies
				ally_damage = ally.max_health - ally.health;
				score += ally_damage * 100;
		return score;

	def get_attack_score(self, ally): #Unit => double
		#	Objectives:
		#	Heal units that have the least health first
		#Get nearby attacked units
		score = 100000;
		score -= ally.health * 100; #max 250
		return score;

	def attack(self, allies_within_range): # => void
		#Can't do anything if garrisoned or in space
		if (self.unit.location.is_in_garrison() or self.unit.location.is_in_space()):
			return;
		if (self.unit.attack_heat() >= 10):
			return;
		best_score = 0;
		best_ally = None;
		for ally in allies_within_range:
			if (ally.health < ally.max_health and self.gc.can_heal(self.unit.id, ally.id)):
				score = self.get_attack_score(ally);
				if (score > best_score):
					best_score = score;
					best_ally = ally;
		if (not(best_ally is None)):
			if (self.gc.can_heal(self.unit.id, best_ally.id)):
				self.gc.heal(self.unit.id, best_ally.id);
				#print("Healer healed ally");
			else:
				print("Healer: Unexpectedly cannot heal ally");
		else:
			0
			#print("Healer: Can't find units to heal");

	def overcharge(self, allies_within_range): # => void
		#Can't overcharge if garrisoned or in space
		if (self.unit.location.is_in_garrison() or self.unit.location.is_in_space() or self.unit.ability_heat() >= 10 or
			self.unit.research_level < 3):
			return;
		#Overcharge furthest unit that's not a healer
		best_ally = None;
		max_dist_squared = -100;
		least_health = 300;
		for ally in allies_within_range:
			if (Helper.is_offensive_robot(ally) and (ally.attack_heat() >= 10 or ally.ability_heat() >= 10)):
				if (ally.health < least_health):
					best_ally = ally;
					least_health = ally.health;
					max_dist_squared = -100;
				elif (ally.health == least_health):
					dist_squared = ally.location.map_location().distance_squared_to(self.unit.location.map_location());
					if (dist_squared > max_dist_squared):
						best_ally = ally;
						max_dist_squared = dist_squared;
		if (not(best_ally is None)):
			if (self.gc.can_overcharge(self.unit.id, best_ally.id)):
				self.gc.overcharge(self.unit.id, best_ally.id);
				self.com.take_extra_turn(best_ally);
			else:
				print("Healer: Unexpectedly cannot overcharge");

	def should_use_micro(self): # => bool
		if (self.unit.location.is_in_garrison() or self.unit.location.is_in_space()):
			return False;
		nearby_enemies = self.gc.sense_nearby_units_by_team(self.unit.location.map_location(), Healer.healer_sense_dist, Helper.get_opposing_team(self.gc.team()));
		nearby_allies = self.gc.sense_nearby_units_by_team(self.unit.location.map_location(), Healer.healer_sense_dist, self.gc.team());
		for enemy in nearby_enemies:
			del enemy;
		for ally in nearby_allies:
			del ally;
		if (len(nearby_enemies) > 0):
			return True;
		return False;

	def move_and_attack(self): # => void
		#Can't do anything if garrisoned or in space
		if (self.gc.can_sense_unit(self.unit.id)):
			self.unit = self.gc.unit(self.unit.id);
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
		if (self.unit.location.is_in_garrison() or self.unit.location.is_in_space()):
			return;
		allies_within_range = self.gc.sense_nearby_units_by_team(self.unit.location.map_location(), self.unit.attack_range(), self.gc.team());
		self.attack(allies_within_range);
		self.overcharge(allies_within_range);
		for ally in allies_within_range:
			del ally;
