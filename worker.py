
import battlecode as bc
from helper import Helper

class Worker:
	worker_avoid_range = 70;
	worker_avoid_buffer = 10;
	worker_knight_avoid_buffer = 5;
	building_sense_range = 20;
	rocket_sense_range = 50;
	factory_resource_limit = 75;
	factory_karbonite_ratio = 25;
	worker_factory_sense_dist = 4;
	worker_karbonite_ratio = 300; #Amt of karbonite on map per worker
	max_earth_worker_num = 30; #Maximum number of workers on earth map
	workers_per_rocket = 4
	workers_per_factory = 4
	max_factory_num = 8; #Shouldn't build more than this no of factories
	max_rocket_num = 3; #Shouldn't build more than this no of rockets in one spot
	mars_worker_cap = 50; #Cap of no of workers on mars
	directions = [bc.Direction.East, bc.Direction.North, bc.Direction.Northeast,
	bc.Direction.Northwest, bc.Direction.South, bc.Direction.Southeast,
	bc.Direction.Southwest, bc.Direction.West];

	def __init__(self, gc, intel_map, mov, astro): #GameController, IntelMap, Mover, Astronomer
		self.gc = gc;
		self.intel_map = intel_map;
		self.mov = mov;
		self.astro = astro;
		self.prev_locs = [];
		self.worker = None;
		self.factories = [];
		self.workers = [];

	def take_turn(self, unit, factories, workers): #Unit, Unit[], Unit[]
		self.worker = unit;
		self.factories = factories;
		self.workers = workers;
		if (self.should_use_micro()):
			self.micro_move();
		else:
			self.perform_general_turn(True);

	def should_use_micro(self): # => boolean
		#Can't do anything if garrisoned or in space
		if (self.worker.location.is_in_garrison() or self.worker.location.is_in_space()):
			return False;
		#If there's a nearby factory
		nearby_factories = self.gc.sense_nearby_units_by_type(self.worker.location.map_location(), Worker.worker_factory_sense_dist, bc.UnitType.Factory);
		for factory in nearby_factories:
			if (factory.team == self.gc.team()):
				return False;
		#Sense nearby enemy units
		nearby_enemies = self.gc.sense_nearby_units_by_team(self.worker.location.map_location(), Worker.worker_avoid_range, Helper.get_opposing_team(self.gc.team()));
		for enemy in nearby_enemies:
			if (enemy.unit_type == bc.UnitType.Ranger or enemy.unit_type == bc.UnitType.Knight or enemy.unit_type == bc.UnitType.Mage):
				return True;
		return False;

	def micro_move(self): # => void
		if (self.worker.movement_heat() >= 10 or self.worker.location.is_in_garrison() or self.worker.location.is_in_space()):
			return;
		nearby_enemies = self.gc.sense_nearby_units_by_team(self.worker.location.map_location(), Worker.worker_avoid_range, Helper.get_opposing_team(self.gc.team()));
		best_score = -1000000000;
		best_move = None;
		if (len(nearby_enemies) > 0):
			for direc in Worker.directions:
				new_loc = self.worker.location.map_location().add(direc);
				score = self.get_move_score(new_loc, nearby_enemies);
				if (score > best_score):
					best_score = score;
					best_move = direc;
			#Sometimes the best move is not to move
			score = self.get_move_score(self.worker.location.map_location(), nearby_enemies);
			if (score > best_score):
				best_score = score;
				best_move = None;
			if (not(best_move is None)):
				if (self.gc.can_move(self.worker.id, best_move)):
					self.gc.move_robot(self.worker.id, best_move);
			self.perform_general_turn(False);
		else:
			self.perform_general_turn(True);
			return;

	def get_move_score(self, new_loc, nearby_enemies): #MapLocation, VecUnit
		#	Objectives:
		#	Keep out of enemy attack range for knight, ranger, mage (More impt)
		#	Run away from enemies if within their attack range

		score = 0;
		for enemy in nearby_enemies:
			dist_squared_to_enemy = enemy.location.map_location().distance_squared_to(new_loc);
			if (enemy.unit_type == bc.UnitType.Ranger or enemy.unit_type == bc.UnitType.Mage):
				if (dist_squared_to_enemy <= enemy.attack_range() + Worker.worker_avoid_buffer):
					score -= 1000000;
					score += dist_squared_to_enemy * 10000;
			elif (enemy.unit_type == bc.UnitType.Knight):
				if (dist_squared_to_enemy <= enemy.attack_range() + Worker.worker_knight_avoid_buffer):
					score -= 1000000;
					score += dist_squared_to_enemy * 100000;
		return score;

	def perform_general_turn(self, can_move): # => void
		#If can't harvest, then move to nearest resource
		if (can_move):
			self.mov.move_to_nearest_karbonite(self.worker);

		self.intel_map.update_karbonite_info(self.worker);

		turn_done = False;

		nearby_factories = self.gc.sense_nearby_units_by_type(self.worker.location.map_location(), Worker.building_sense_range, bc.UnitType.Factory)
		nearby_rockets = self.gc.sense_nearby_units_by_type(self.worker.location.map_location(), Worker.building_sense_range, bc.UnitType.Rocket)

		nearby_workers = self.gc.sense_nearby_units_by_type(self.worker.location.map_location(), Worker.building_sense_range, bc.UnitType.Worker);

		nearby_unbuilt_factories = 0;
		for factory in nearby_factories:
			if (not(factory.structure_is_built()) and factory.team == self.gc.team() ):
				nearby_unbuilt_factories += 1;
		if (self.gc.planet() == bc.Planet.Earth):
			if (len(nearby_workers) <= Worker.workers_per_factory * nearby_unbuilt_factories and len(nearby_factories) > 0):
				#Attempt to replicate worker
				if (bc.UnitType.Worker.replicate_cost() <= self.gc.karbonite() and self.worker.ability_heat() < 10):
					for direc in Worker.directions:
						if (self.gc.can_replicate(self.worker.id, direc)):
							self.gc.replicate(self.worker.id, direc);
							turn_done = True;
							break;
		if (turn_done):
			return;
		for factory in nearby_factories:
			if (not(factory.structure_is_built()) and factory.team == self.gc.team()):
				#If within range, build factory
				if (factory.location.map_location().distance_squared_to(self.worker.location.map_location()) <= 2):
					if (self.gc.can_build(self.worker.id, factory.id)):
						self.gc.build(self.worker.id, factory.id);
						turn_done = True;
						break;
		if (turn_done):
			return;
		#print("I'm here");
		#Spawn new worker if there's no workers nearby and there's rockets to be built
		if (self.gc.planet() == bc.Planet.Earth):
			if (len(nearby_workers) <= Worker.workers_per_rocket and len(nearby_rockets) > 0):
				#Attempt to replicate worker
				if (bc.UnitType.Worker.replicate_cost() <= self.gc.karbonite() and self.worker.ability_heat() < 10):
					for direc in Worker.directions:
						if (self.gc.can_replicate(self.worker.id, direc)):
							self.gc.replicate(self.worker.id, direc);
							turn_done = True;
							break;
		if (turn_done):
			return;
		#This shouldn't trigger for mars
		for rocket in nearby_rockets:
			if (not(rocket.structure_is_built()) and rocket.team == self.gc.team()):
				#If within range, build factory
				if (rocket.location.map_location().distance_squared_to(self.worker.location.map_location()) <= 2):
					if (self.gc.can_build(self.worker.id, rocket.id)):
						#Build factory
						self.gc.build(self.worker.id, rocket.id);
						turn_done = True;
						break;
		if (turn_done):
			return;
		#print("Yo I'm here");
		#If factory ratio not enough, build a new factory
		if (len(self.factories) == 0 or self.gc.karbonite() > len(self.factories) * Worker.factory_karbonite_ratio + Worker.factory_resource_limit
			and len(self.factories) < Worker.max_factory_num):
			if (bc.UnitType.Factory.blueprint_cost() <= self.gc.karbonite()):
				best_factory_direction = None;
				most_clear = 0;
				for direc in Worker.directions:
					if (self.gc.can_blueprint(self.worker.id, bc.UnitType.Factory, direc)):
						factory_loc = self.worker.location.map_location().add(direc);
						clarity = 0;
						for direc2 in Worker.directions:
							test_loc = factory_loc.add(direc2);
							if (self.intel_map.is_passable(test_loc)):
								clarity += 1;
						if (clarity > most_clear):
							most_clear = clarity
							best_factory_direction = direc;
				if (not(best_factory_direction is None)):
					if (self.gc.can_blueprint(self.worker.id, bc.UnitType.Factory, best_factory_direction)):
						self.gc.blueprint(self.worker.id, bc.UnitType.Factory, best_factory_direction);
						turn_done = True;
						return;
		if (turn_done):
			return;
		#print("Ooh I'm here");
		#Repair stuff if I can repair
		for factory in nearby_factories:
			if (factory.health < factory.max_health and factory.team == self.gc.team()):
				if (self.gc.can_repair(self.worker.id, factory.id)):
					#Build factory
					self.gc.repair(self.worker.id, factory.id);
					turn_done = True;
					break;
		if (turn_done):
			return;
		nearby_rockets = self.gc.sense_nearby_units_by_type(self.worker.location.map_location(), Worker.rocket_sense_range, bc.UnitType.Rocket)
		num_friendly_rockets = 0;
		for rocket in nearby_rockets:
			if (rocket.team == self.gc.team() and not(rocket.structure_is_built())):
				num_friendly_rockets += 1;
		#print("Helloo");
		#Todo: Blueprint and build rockets => replicate a few workers when there's a rocket to be built and no workers nearby
		#Only allow rockets to be built on Earth
		if (self.gc.planet() == bc.Planet.Earth and self.gc.research_info().get_level(bc.UnitType.Rocket) >= 1):
			if (self.astro.should_build_rocket() and can_move):
				if (bc.UnitType.Rocket.blueprint_cost() <= self.gc.karbonite() and num_friendly_rockets < Worker.max_rocket_num):
					has_place_for_rocket = False;
					for direc in Worker.directions:
						if (self.gc.can_blueprint(self.worker.id, bc.UnitType.Rocket, direc)):
							self.gc.blueprint(self.worker.id, bc.UnitType.Rocket, direc);
							turn_done = True;
							has_place_for_rocket = True;
							break;
					if (not(has_place_for_rocket) and num_friendly_rockets == 0):
						for direc in Worker.directions:
							new_loc = self.worker.location.map_location().add(direc);
							if (self.gc.can_sense_location(new_loc) and self.gc.has_unit_at_location(new_loc)):
								unit = self.gc.sense_unit_at_location(new_loc);
								if (unit.team == self.gc.team()):
									self.gc.disintegrate_unit(unit.id);
									if (self.gc.can_blueprint(self.worker.id, bc.UnitType.Rocket, direc)):
										self.gc.blueprint(self.worker.id, bc.UnitType.Rocket, direc);
										turn_done = True;
										break;
		if (turn_done):
			return;
		#Spawn new worker if there's too much karbonite to harvest only on Earth
		if (self.gc.planet() == bc.Planet.Earth):
			if (self.intel_map.get_map_karbonite(bc.Planet.Earth) > len(self.workers) * Worker.worker_karbonite_ratio and 
				len(self.workers) < Worker.max_earth_worker_num):
				#Attempt to replicate worker
				if (bc.UnitType.Worker.replicate_cost() <= self.gc.karbonite() and self.worker.ability_heat() < 10):
					move_dir = self.mov.move_dir_to_karbonite(self.worker);
					if (not(move_dir is None)):
						if (self.gc.can_replicate(self.worker.id, move_dir)):
							self.gc.replicate(self.worker.id, move_dir);
							turn_done = True;
					if (not(turn_done)):
						for direc in Worker.directions:
							if (self.gc.can_replicate(self.worker.id, direc)):
								self.gc.replicate(self.worker.id, direc);
								turn_done = True;
								break;
		else:
			#Attempt to replicate worker
			if (bc.UnitType.Worker.replicate_cost() <= self.gc.karbonite() and self.worker.ability_heat() < 10 and len(self.workers) < Worker.mars_worker_cap and self.gc.round() > 750):
				for direc in Worker.directions:
					if (self.gc.can_replicate(self.worker.id, direc)):
						self.gc.replicate(self.worker.id, direc);
						#print("Rep rep => fill up Mars yay")
						turn_done = True;
						break;
		if (turn_done):
			return;
		#print("Haihai");
		#If not, run harvest algorithm to begin harvesting stuff
		if (self.gc.can_harvest(self.worker.id, bc.Direction.Center)):
			self.gc.harvest(self.worker.id, bc.Direction.Center);
			self.intel_map.set_karbonite_at(self.worker.location.map_location(), self.gc.karbonite_at(self.worker.location.map_location()));
			turn_done = True;
			return;
		if (turn_done):
			return;
		for direc in Worker.directions:
			if (self.gc.can_harvest(self.worker.id, direc)):
				self.gc.harvest(self.worker.id, direc);
				new_loc = self.worker.location.map_location().add(direc);
				if (self.intel_map.is_on_map(new_loc)):
					self.intel_map.set_karbonite_at(new_loc, self.gc.karbonite_at(new_loc));
				turn_done = True;
				break;
		if (turn_done):
			return;
		#print("hai");
		



